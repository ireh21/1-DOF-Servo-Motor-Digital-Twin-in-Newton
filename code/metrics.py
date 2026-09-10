"""Evaluation metrics for the 1-DOF Newton motor fitting project.

This module is intentionally independent from Newton/Warp. It only consumes
NumPy arrays or the ``data`` / ``simulation`` dictionaries produced in the
project notebooks and helper scripts.
"""

from __future__ import annotations

from typing import Any

import numpy as np


TRAJECTORY_KEYS = {
    "position": "feedback_position",
    "velocity": "feedback_velocity",
    "torque": "feedback_torque",
}


def _as_1d_float_array(values: Any, name: str) -> np.ndarray:
    array = np.asarray(values, dtype=np.float64)
    if array.ndim != 1:
        raise ValueError(f"{name} must be a 1D array.")
    if array.size == 0:
        raise ValueError(f"{name} must not be empty.")
    if not np.all(np.isfinite(array)):
        raise ValueError(f"{name} contains NaN or inf.")
    return array


def _require_same_shape(reference: np.ndarray, estimate: np.ndarray, prefix: str) -> None:
    if reference.shape != estimate.shape:
        raise ValueError(
            f"{prefix} shape mismatch: reference={reference.shape}, "
            f"estimate={estimate.shape}"
        )


def rmse(reference: Any, estimate: Any) -> float:
    """Return root-mean-square error."""
    reference_array = _as_1d_float_array(reference, "reference")
    estimate_array = _as_1d_float_array(estimate, "estimate")
    _require_same_shape(reference_array, estimate_array, "rmse")
    return float(np.sqrt(np.mean((estimate_array - reference_array) ** 2)))


def nrmse(reference: Any, estimate: Any, scale: float | None = None) -> float:
    """Return normalized RMSE.

    If ``scale`` is not supplied, the reference standard deviation is used.
    When the scale is numerically too small, a small epsilon is added to avoid
    division by zero.
    """
    reference_array = _as_1d_float_array(reference, "reference")
    estimate_array = _as_1d_float_array(estimate, "estimate")
    _require_same_shape(reference_array, estimate_array, "nrmse")
    if scale is None:
        scale_value = float(np.std(reference_array))
    else:
        scale_value = float(scale)
    return rmse(reference_array, estimate_array) / max(scale_value, 1.0e-12)


def following_error(command: Any, feedback: Any) -> np.ndarray:
    """Return command minus feedback."""
    command_array = _as_1d_float_array(command, "command")
    feedback_array = _as_1d_float_array(feedback, "feedback")
    _require_same_shape(command_array, feedback_array, "following_error")
    return command_array - feedback_array


def following_error_metrics(command: Any, feedback: Any) -> dict[str, float]:
    """Return summary metrics for following error."""
    error = following_error(command, feedback)
    abs_error = np.abs(error)
    return {
        "mean_abs": float(np.mean(abs_error)),
        "p95_abs": float(np.percentile(abs_error, 95.0)),
        "max_abs": float(np.max(abs_error)),
        "rms": float(np.sqrt(np.mean(error ** 2))),
    }


def _step_levels(command: np.ndarray, initial_window: int = 5) -> tuple[float, float, float, float]:
    window = min(command.size, max(1, int(initial_window)))
    initial = float(np.median(command[:window]))
    target = float(np.median(command[-window:]))
    amplitude = target - initial
    direction = float(np.sign(amplitude)) if abs(amplitude) > 0.0 else 0.0
    return initial, target, amplitude, direction


def overshoot(response: Any, command: Any) -> float:
    """Return normalized overshoot ratio for a step-like response.

    The value is expressed as a fraction of the step amplitude. For example,
    0.10 means 10% overshoot.
    """
    response_array = _as_1d_float_array(response, "response")
    command_array = _as_1d_float_array(command, "command")
    _require_same_shape(command_array, response_array, "overshoot")
    initial, target, amplitude, direction = _step_levels(command_array)
    if abs(amplitude) <= 1.0e-12 or direction == 0.0:
        return 0.0
    if direction > 0.0:
        peak = float(np.max(response_array))
        excess = max(0.0, peak - target)
    else:
        peak = float(np.min(response_array))
        excess = max(0.0, target - peak)
    return excess / abs(amplitude)


def overshoot_error(
    measured_response: Any,
    simulated_response: Any,
    command: Any,
) -> dict[str, float]:
    """Return measured/simulated overshoot and their absolute difference."""
    measured_value = overshoot(measured_response, command)
    simulated_value = overshoot(simulated_response, command)
    return {
        "measured": measured_value,
        "simulated": simulated_value,
        "abs_error": abs(simulated_value - measured_value),
    }


def settling_time(
    time: Any,
    response: Any,
    command: Any,
    *,
    tolerance_ratio: float = 0.02,
    hold_time_s: float = 0.05,
) -> float:
    """Return settling time for a step-like response.

    The response is considered settled at the first time index after which it
    remains within ``tolerance_ratio * abs(step_amplitude)`` until the end.
    ``hold_time_s`` defines a minimum continuous in-band duration.
    """
    time_array = _as_1d_float_array(time, "time")
    response_array = _as_1d_float_array(response, "response")
    command_array = _as_1d_float_array(command, "command")
    _require_same_shape(time_array, response_array, "settling_time")
    _require_same_shape(time_array, command_array, "settling_time")
    if time_array.size < 2:
        raise ValueError("time must contain at least two samples.")
    dt = float(np.median(np.diff(time_array)))
    if dt <= 0.0:
        raise ValueError("time must be strictly increasing.")

    _, target, amplitude, _ = _step_levels(command_array)
    tolerance = max(abs(amplitude) * float(tolerance_ratio), 1.0e-12)
    in_band = np.abs(response_array - target) <= tolerance
    min_hold_count = max(1, int(round(float(hold_time_s) / dt)))

    for start in range(response_array.size):
        if not in_band[start]:
            continue
        stop = min(response_array.size, start + min_hold_count)
        if not np.all(in_band[start:stop]):
            continue
        if np.all(in_band[start:]):
            return float(time_array[start] - time_array[0])
    return float(time_array[-1] - time_array[0])


def settling_time_error(
    time: Any,
    measured_response: Any,
    simulated_response: Any,
    command: Any,
    *,
    tolerance_ratio: float = 0.02,
    hold_time_s: float = 0.05,
) -> dict[str, float]:
    """Return measured/simulated settling time and their absolute difference."""
    measured_value = settling_time(
        time,
        measured_response,
        command,
        tolerance_ratio=tolerance_ratio,
        hold_time_s=hold_time_s,
    )
    simulated_value = settling_time(
        time,
        simulated_response,
        command,
        tolerance_ratio=tolerance_ratio,
        hold_time_s=hold_time_s,
    )
    return {
        "measured_s": measured_value,
        "simulated_s": simulated_value,
        "abs_error_s": abs(simulated_value - measured_value),
    }


def rise_time(
    time: Any,
    response: Any,
    command: Any,
    *,
    low_ratio: float = 0.10,
    high_ratio: float = 0.90,
) -> float:
    """Return 10%-90% rise time for a step-like response."""
    time_array = _as_1d_float_array(time, "time")
    response_array = _as_1d_float_array(response, "response")
    command_array = _as_1d_float_array(command, "command")
    _require_same_shape(time_array, response_array, "rise_time")
    _require_same_shape(time_array, command_array, "rise_time")

    initial, _, amplitude, direction = _step_levels(command_array)
    if abs(amplitude) <= 1.0e-12 or direction == 0.0:
        return 0.0

    low_level = initial + low_ratio * amplitude
    high_level = initial + high_ratio * amplitude
    if direction > 0.0:
        low_hits = np.flatnonzero(response_array >= low_level)
        high_hits = np.flatnonzero(response_array >= high_level)
    else:
        low_hits = np.flatnonzero(response_array <= low_level)
        high_hits = np.flatnonzero(response_array <= high_level)
    if len(low_hits) == 0 or len(high_hits) == 0:
        return float(time_array[-1] - time_array[0])
    return float(time_array[high_hits[0]] - time_array[low_hits[0]])


def rise_time_error(
    time: Any,
    measured_response: Any,
    simulated_response: Any,
    command: Any,
    *,
    low_ratio: float = 0.10,
    high_ratio: float = 0.90,
) -> dict[str, float]:
    """Return measured/simulated rise time and their absolute difference."""
    measured_value = rise_time(
        time, measured_response, command, low_ratio=low_ratio, high_ratio=high_ratio
    )
    simulated_value = rise_time(
        time, simulated_response, command, low_ratio=low_ratio, high_ratio=high_ratio
    )
    return {
        "measured_s": measured_value,
        "simulated_s": simulated_value,
        "abs_error_s": abs(simulated_value - measured_value),
    }


def estimate_gain_phase(
    command: Any,
    response: Any,
    dt: float,
    frequency_hz: float,
) -> dict[str, float]:
    """Estimate sine gain and phase using single-frequency projection."""
    command_array = _as_1d_float_array(command, "command")
    response_array = _as_1d_float_array(response, "response")
    _require_same_shape(command_array, response_array, "estimate_gain_phase")
    dt_value = float(dt)
    frequency = float(frequency_hz)
    if dt_value <= 0.0:
        raise ValueError("dt must be positive.")
    if frequency <= 0.0:
        raise ValueError("frequency_hz must be positive.")

    time_array = np.arange(command_array.size, dtype=np.float64) * dt_value
    omega = 2.0 * np.pi * frequency
    sin_basis = np.sin(omega * time_array)
    cos_basis = np.cos(omega * time_array)

    def fit_components(signal: np.ndarray) -> tuple[float, float]:
        sin_coeff = 2.0 * np.mean(signal * sin_basis)
        cos_coeff = 2.0 * np.mean(signal * cos_basis)
        return float(sin_coeff), float(cos_coeff)

    cmd_sin, cmd_cos = fit_components(command_array - np.mean(command_array))
    res_sin, res_cos = fit_components(response_array - np.mean(response_array))

    cmd_amp = float(np.hypot(cmd_sin, cmd_cos))
    res_amp = float(np.hypot(res_sin, res_cos))
    cmd_phase = float(np.arctan2(cmd_cos, cmd_sin))
    res_phase = float(np.arctan2(res_cos, res_sin))

    gain = res_amp / max(cmd_amp, 1.0e-12)
    phase_rad = res_phase - cmd_phase
    phase_rad = float((phase_rad + np.pi) % (2.0 * np.pi) - np.pi)
    return {
        "gain": gain,
        "phase_rad": phase_rad,
        "phase_deg": float(np.rad2deg(phase_rad)),
        "command_amplitude": cmd_amp,
        "response_amplitude": res_amp,
    }


def gain_phase_metrics(
    measured_response: Any,
    simulated_response: Any,
    command: Any,
    dt: float,
    frequency_hz: float,
) -> dict[str, float]:
    """Compare sine gain/phase between measurement and simulation."""
    measured = estimate_gain_phase(command, measured_response, dt, frequency_hz)
    simulated = estimate_gain_phase(command, simulated_response, dt, frequency_hz)
    return {
        "measured_gain": measured["gain"],
        "simulated_gain": simulated["gain"],
        "gain_abs_error": abs(simulated["gain"] - measured["gain"]),
        "measured_phase_deg": measured["phase_deg"],
        "simulated_phase_deg": simulated["phase_deg"],
        "phase_abs_error_deg": abs(simulated["phase_deg"] - measured["phase_deg"]),
    }


def trajectory_metrics(
    data: dict[str, Any],
    simulation: dict[str, Any],
    *,
    scales: dict[str, float] | None = None,
) -> dict[str, float]:
    """Return per-signal NRMSE metrics for position/velocity/torque."""
    metrics: dict[str, float] = {}
    for signal, key in TRAJECTORY_KEYS.items():
        scale = None if scales is None else scales.get(signal)
        metrics[f"{signal}_nrmse"] = nrmse(data[key], simulation[key], scale=scale)
        metrics[f"{signal}_rmse"] = rmse(data[key], simulation[key])
    return metrics


def step_response_metrics(
    data: dict[str, Any],
    simulation: dict[str, Any],
    *,
    tolerance_ratio: float = 0.02,
    hold_time_s: float = 0.05,
) -> dict[str, float]:
    """Return step-oriented metrics using position response."""
    time = data["time"]
    command = data["command_position"]
    measured = data["feedback_position"]
    simulated = simulation["feedback_position"]

    overshoot_result = overshoot_error(measured, simulated, command)
    settling_result = settling_time_error(
        time,
        measured,
        simulated,
        command,
        tolerance_ratio=tolerance_ratio,
        hold_time_s=hold_time_s,
    )
    rise_result = rise_time_error(time, measured, simulated, command)
    following_measured = following_error_metrics(command, measured)
    following_simulated = following_error_metrics(command, simulated)

    return {
        "overshoot_measured": overshoot_result["measured"],
        "overshoot_simulated": overshoot_result["simulated"],
        "overshoot_abs_error": overshoot_result["abs_error"],
        "settling_measured_s": settling_result["measured_s"],
        "settling_simulated_s": settling_result["simulated_s"],
        "settling_abs_error_s": settling_result["abs_error_s"],
        "rise_measured_s": rise_result["measured_s"],
        "rise_simulated_s": rise_result["simulated_s"],
        "rise_abs_error_s": rise_result["abs_error_s"],
        "measured_following_rms": following_measured["rms"],
        "simulated_following_rms": following_simulated["rms"],
        "following_rms_abs_error": abs(
            following_simulated["rms"] - following_measured["rms"]
        ),
        "measured_following_max_abs": following_measured["max_abs"],
        "simulated_following_max_abs": following_simulated["max_abs"],
        "following_max_abs_error": abs(
            following_simulated["max_abs"] - following_measured["max_abs"]
        ),
    }


def sine_response_metrics(
    data: dict[str, Any],
    simulation: dict[str, Any],
    frequency_hz: float,
) -> dict[str, float]:
    """Return gain/phase and following-error metrics for a sine dataset."""
    command = data["command_position"]
    measured = data["feedback_position"]
    simulated = simulation["feedback_position"]
    gain_phase = gain_phase_metrics(
        measured, simulated, command, data["dt"], frequency_hz
    )
    following_measured = following_error_metrics(command, measured)
    following_simulated = following_error_metrics(command, simulated)
    return {
        **gain_phase,
        "measured_following_rms": following_measured["rms"],
        "simulated_following_rms": following_simulated["rms"],
        "following_rms_abs_error": abs(
            following_simulated["rms"] - following_measured["rms"]
        ),
        "measured_following_p95_abs": following_measured["p95_abs"],
        "simulated_following_p95_abs": following_simulated["p95_abs"],
        "following_p95_abs_error": abs(
            following_simulated["p95_abs"] - following_measured["p95_abs"]
        ),
    }


def steady_speed_torque_bias(
    velocity: Any,
    measured_torque: Any,
    simulated_torque: Any,
    *,
    moving_threshold: float | None = None,
) -> dict[str, float]:
    """Return steady-speed torque bias over moving samples.

    The bias is defined as mean(simulated_torque - measured_torque) over
    samples where the absolute velocity is above ``moving_threshold``.
    If the threshold is not supplied, it is set to 10% of the 95th percentile
    of the absolute velocity with a small minimum floor.
    """
    velocity_array = _as_1d_float_array(velocity, "velocity")
    measured_array = _as_1d_float_array(measured_torque, "measured_torque")
    simulated_array = _as_1d_float_array(simulated_torque, "simulated_torque")
    _require_same_shape(velocity_array, measured_array, "steady_speed_torque_bias")
    _require_same_shape(velocity_array, simulated_array, "steady_speed_torque_bias")

    if moving_threshold is None:
        threshold = max(
            1.0e-12,
            0.10 * float(np.percentile(np.abs(velocity_array), 95.0)),
        )
    else:
        threshold = max(float(moving_threshold), 1.0e-12)

    moving_mask = np.abs(velocity_array) >= threshold
    if not np.any(moving_mask):
        return {
            "moving_threshold": threshold,
            "moving_sample_count": 0.0,
            "measured_mean_torque": 0.0,
            "simulated_mean_torque": 0.0,
            "torque_bias": 0.0,
            "torque_bias_abs": 0.0,
        }

    measured_mean = float(np.mean(measured_array[moving_mask]))
    simulated_mean = float(np.mean(simulated_array[moving_mask]))
    bias = simulated_mean - measured_mean
    return {
        "moving_threshold": threshold,
        "moving_sample_count": float(np.sum(moving_mask)),
        "measured_mean_torque": measured_mean,
        "simulated_mean_torque": simulated_mean,
        "torque_bias": bias,
        "torque_bias_abs": abs(bias),
    }


def ramp_response_metrics(
    data: dict[str, Any],
    simulation: dict[str, Any],
    *,
    moving_threshold: float | None = None,
) -> dict[str, float]:
    """Return ramp-oriented torque-bias and following-error metrics."""
    command = data["command_position"]
    measured_position = data["feedback_position"]
    simulated_position = simulation["feedback_position"]
    torque_bias = steady_speed_torque_bias(
        data["feedback_velocity"],
        data["feedback_torque"],
        simulation["feedback_torque"],
        moving_threshold=moving_threshold,
    )
    following_measured = following_error_metrics(command, measured_position)
    following_simulated = following_error_metrics(command, simulated_position)
    return {
        **torque_bias,
        "measured_following_rms": following_measured["rms"],
        "simulated_following_rms": following_simulated["rms"],
        "following_rms_abs_error": abs(
            following_simulated["rms"] - following_measured["rms"]
        ),
        "measured_following_p95_abs": following_measured["p95_abs"],
        "simulated_following_p95_abs": following_simulated["p95_abs"],
        "following_p95_abs_error": abs(
            following_simulated["p95_abs"] - following_measured["p95_abs"]
        ),
    }


__all__ = [
    "TRAJECTORY_KEYS",
    "estimate_gain_phase",
    "following_error",
    "following_error_metrics",
    "gain_phase_metrics",
    "nrmse",
    "overshoot",
    "overshoot_error",
    "rise_time",
    "rise_time_error",
    "ramp_response_metrics",
    "rmse",
    "settling_time",
    "settling_time_error",
    "sine_response_metrics",
    "steady_speed_torque_bias",
    "step_response_metrics",
    "trajectory_metrics",
]
