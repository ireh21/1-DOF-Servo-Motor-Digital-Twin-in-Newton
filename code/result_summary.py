"""Helpers for notebook result summaries backed by saved JSON outputs."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

import numpy as np

from metrics import (
    ramp_response_metrics,
    sine_response_metrics,
    step_response_metrics,
    trajectory_metrics,
)
from single_motor_twin import MotorParams, simulate_motor
from wmx_log_utils import load_wmx_log


DEG_TO_RAD = np.pi / 180.0
RATED_TORQUE_NM = 0.16
LOG_OPTIONS = {
    "cycle_period_s": 1.0e-3,
    "position_scale": DEG_TO_RAD,
    "velocity_scale": DEG_TO_RAD,
    "torque_scale": RATED_TORQUE_NM / 100.0,
}
SIGNAL_KEYS = (
    "command_position",
    "feedback_position",
    "feedback_velocity",
    "feedback_torque",
)
INITIAL_WINDOW_S = 0.02


def load_result_payload(result_path: str | Path) -> dict[str, Any]:
    path = Path(result_path)
    return json.loads(path.read_text(encoding="utf-8"))


def align_log(data: dict[str, Any], profile: str) -> dict[str, Any]:
    raw_time = np.asarray(data["time"], dtype=np.float64)
    dt = float(np.median(np.diff(raw_time)))
    count = int(np.floor((raw_time[-1] - raw_time[0]) / dt + 1.0e-9)) + 1
    time_axis = np.arange(count, dtype=np.float64) * dt
    result = {
        key: np.interp(time_axis, raw_time - raw_time[0], data[key])
        for key in SIGNAL_KEYS
    }
    initial_count = min(count, max(3, int(round(INITIAL_WINDOW_S / dt))))
    position_origin = float(np.median(result["feedback_position"][:initial_count]))
    initial_velocity = float(np.median(result["feedback_velocity"][:initial_count]))
    result["command_position"] -= position_origin
    result["feedback_position"] -= position_origin
    result.update(
        {
            "profile": profile,
            "source": data["source"],
            "time": time_axis,
            "dt": dt,
            "source_dt": dt,
            "position_origin": position_origin,
            "initial_position": float(result["feedback_position"][0]),
            "initial_velocity": initial_velocity,
        }
    )
    return result


def slice_log(data: dict[str, Any], start: int, stop: int) -> dict[str, Any]:
    result = {key: np.asarray(data[key])[start:stop] for key in SIGNAL_KEYS}
    result.update(
        {
            "profile": data["profile"],
            "source": data["source"],
            "time": np.arange(stop - start) * data["dt"],
            "dt": data["dt"],
            "source_dt": data["source_dt"],
            "position_origin": data["position_origin"],
            "initial_position": float(result["feedback_position"][0]),
            "initial_velocity": float(result["feedback_velocity"][0]),
        }
    )
    return result


def decimate_log(data: dict[str, Any], max_samples: int) -> dict[str, Any]:
    stride = max(1, int(np.ceil(len(data["time"]) / max_samples)))
    if stride == 1:
        return {key: value.copy() if isinstance(value, np.ndarray) else value for key, value in data.items()}
    result = {key: np.asarray(data[key])[::stride] for key in SIGNAL_KEYS}
    result.update(
        {
            "profile": data["profile"],
            "source": data["source"],
            "time": np.arange(len(result["command_position"])) * data["dt"] * stride,
            "dt": data["dt"] * stride,
            "source_dt": data["source_dt"],
            "position_origin": data["position_origin"],
            "initial_position": float(result["feedback_position"][0]),
            "initial_velocity": float(result["feedback_velocity"][0]),
        }
    )
    return result


def infer_frequency_hz(name: str) -> float | None:
    match = re.search(r"sine_(\d+(?:\.\d+)?)hz", name.lower())
    return float(match.group(1)) if match else None


def evaluate_items(
    items: list[dict[str, Any]],
    params: MotorParams,
) -> list[dict[str, Any]]:
    simulations = []
    for data in items:
        simulations.append(
            simulate_motor(
                data["command_position"],
                data["dt"],
                params,
                use_viewer=False,
                initial_position=data["initial_position"],
                initial_velocity=data["initial_velocity"],
            )
        )
    return simulations


def build_step_items(step_data: dict[str, Any], mode: str) -> list[dict[str, Any]]:
    command_jump = np.abs(
        np.diff(step_data["command_position"], prepend=step_data["command_position"][0])
    )
    jump_threshold = 0.25 * float(np.max(command_jump))
    jump_indices = np.flatnonzero(command_jump >= jump_threshold)
    jump_indices = jump_indices[np.r_[True, np.diff(jump_indices) > 10]]
    if len(jump_indices) == 0:
        raise RuntimeError("Step 로그에서 jump를 찾지 못했습니다.")

    step_windows = []
    for index, jump in enumerate(jump_indices, 1):
        segment = slice_log(
            step_data,
            max(0, int(jump) - int(round(0.10 / step_data["dt"]))),
            min(len(step_data["time"]), int(jump) + int(round(0.50 / step_data["dt"]))),
        )
        segment["profile"] = f"step_transient_{index}"
        step_windows.append(segment)

    if mode == "04_3":
        return [step_windows[0]]
    return step_windows


def build_ramp_items(ramp_data: dict[str, Any], mode: str) -> list[dict[str, Any]]:
    if mode == "04_3":
        return [decimate_log(ramp_data, 1200)]
    return [ramp_data]


def build_sine_items(
    datasets: dict[str, dict[str, Any]],
    fit_names: list[str],
) -> tuple[list[dict[str, Any]], list[float]]:
    sine_names = [name for name in fit_names if "sine" in name.lower()]
    frequencies = [infer_frequency_hz(name) for name in sine_names]
    if any(frequency is None for frequency in frequencies):
        raise RuntimeError("Sine dataset 이름에서 frequency를 읽지 못했습니다.")
    return [datasets[name] for name in sine_names], [float(value) for value in frequencies]


def mean_metric(rows: list[dict[str, Any]], *keys: str) -> float:
    values = []
    for row in rows:
        value = float("nan")
        for key in keys:
            if key in row:
                value = float(row[key])
                break
        if np.isfinite(value):
            values.append(value)
    return float(np.mean(values)) if values else float("nan")


def summarize_result_bundle(result_path: str | Path, mode: str) -> dict[str, dict[str, float]]:
    payload = load_result_payload(result_path)
    params = MotorParams(**payload["motor_params"])

    all_logs = {**payload["fit_logs"], **payload["validation_logs"]}
    datasets = {
        name: align_log(load_wmx_log(path, **LOG_OPTIONS), name)
        for name, path in all_logs.items()
    }

    fit_names = list(payload["fit_logs"])
    validation_names = list(payload["validation_logs"])
    validation_items = [datasets[name] for name in validation_names]
    validation_simulations = evaluate_items(validation_items, params)
    validation_rows = [
        trajectory_metrics(data, simulation)
        for data, simulation in zip(validation_items, validation_simulations)
    ]

    step_name = next((name for name in fit_names if "step" in name.lower()), None)
    if step_name is None:
        raise RuntimeError("result JSON에 step 로그가 없습니다.")
    step_items = build_step_items(datasets[step_name], mode)
    step_simulations = evaluate_items(step_items, params)
    step_rows = [
        step_response_metrics(data, simulation)
        for data, simulation in zip(step_items, step_simulations)
    ]

    ramp_name = next((name for name in fit_names if "ramp" in name.lower()), None)
    if ramp_name is None:
        raise RuntimeError("result JSON에 ramp 로그가 없습니다.")
    ramp_items = build_ramp_items(datasets[ramp_name], mode)
    ramp_simulations = evaluate_items(ramp_items, params)
    ramp_rows = [
        ramp_response_metrics(data, simulation)
        for data, simulation in zip(ramp_items, ramp_simulations)
    ]

    sine_items, sine_frequencies = build_sine_items(datasets, fit_names)
    sine_simulations = evaluate_items(sine_items, params)
    sine_rows = [
        sine_response_metrics(data, simulation, frequency_hz=frequency_hz)
        for frequency_hz, data, simulation in zip(
            sine_frequencies, sine_items, sine_simulations
        )
    ]

    return {
        "validation": {
            "position_nrmse": mean_metric(validation_rows, "position_nrmse"),
            "velocity_nrmse": mean_metric(validation_rows, "velocity_nrmse"),
            "torque_nrmse": mean_metric(validation_rows, "torque_nrmse"),
        },
        "step": {
            "rise_error_s": mean_metric(step_rows, "rise_abs_error_s", "rise_error_s"),
            "settling_error_s": mean_metric(
                step_rows, "settling_abs_error_s", "settling_error_s"
            ),
            "overshoot_error": mean_metric(
                step_rows, "overshoot_abs_error", "overshoot_error"
            ),
        },
        "ramp": {
            "torque_bias_abs": mean_metric(ramp_rows, "torque_bias_abs", "torque_bias"),
        },
        "sine": {
            "gain_abs_error": mean_metric(sine_rows, "gain_abs_error"),
            "phase_abs_error_deg": mean_metric(
                sine_rows, "phase_abs_error_deg", "phase_error_deg"
            ),
        },
    }


def format_summary(summary: dict[str, dict[str, float]]) -> str:
    return "\n".join(
        [
            "VALIDATION",
            f"  position_nrmse: {summary['validation']['position_nrmse']:.6g}",
            f"  velocity_nrmse: {summary['validation']['velocity_nrmse']:.6g}",
            f"  torque_nrmse: {summary['validation']['torque_nrmse']:.6g}",
            "",
            "STEP",
            f"  rise_error_s: {summary['step']['rise_error_s']:.6g}",
            f"  settling_error_s: {summary['step']['settling_error_s']:.6g}",
            f"  overshoot_error: {summary['step']['overshoot_error']:.6g}",
            "",
            "RAMP",
            f"  torque_bias_abs: {summary['ramp']['torque_bias_abs']:.6g}",
            "",
            "SINE",
            f"  gain_abs_error: {summary['sine']['gain_abs_error']:.6g}",
            f"  phase_abs_error_deg: {summary['sine']['phase_abs_error_deg']:.6g}",
        ]
    )


def print_summary(summary: dict[str, dict[str, float]]) -> None:
    print(format_summary(summary))


__all__ = [
    "format_summary",
    "print_summary",
    "summarize_result_bundle",
]
