"""여러 시험 프로파일의 합성 WMX3 텍스트 로그를 생성한다.

실제 하드웨어 로그가 준비되기 전에 피팅 파이프라인을 검증하기 위한 데이터다.
모든 출력 파일은 아래에 명시된 동일한 MotorParams를 사용한다.
"""
from __future__ import annotations

import argparse
from dataclasses import asdict
from pathlib import Path

import numpy as np

from single_motor_twin import (
    MotorParams,
    profile_scurve,
    profile_sine,
    profile_step,
    simulate,
)


DT = 1.0e-3
DEFAULT_OUTPUT_DIR = Path(__file__).resolve().parent.parent / "synthetic_wmx_logs2"

# 합성 로그의 "정답" 파라미터. 새 데이터를 만들 때 원하는 값을 직접 수정한다.
MOTOR_PARAMS = MotorParams(
    kp=10.996398718882114,
    ki=1.1930162194347773,
    kd=0.8556416451823275,
    integral_max=4.437985730220815,
    continuous_torque_limit=5.193511737418461,
    peak_torque_limit=5.193511737418461,
    inertia=0.028188008953187953,
    viscous=0.024485211102482668,
    coulomb=0.0006373491469474279,
    delay_steps=2,
)


def _ramp_profile() -> np.ndarray:
    """양/음 방향을 모두 포함하는 연속 ramp 프로파일."""
    count = 8000
    time = np.arange(count) * DT
    return np.interp(
        time,
        [0.0, 0.5, 2.0, 4.0, 6.0, 7.5, 8.0],
        [0.0, 0.0, 0.75, 0.0, -0.75, 0.0, 0.0],
    ).astype(np.float32)


def _step_profile() -> np.ndarray:
    command = profile_step(5000, DT, 0.0, 0.7, 0.5)
    command[2000:3500] = -0.4
    command[3500:] = 0.2
    return command


def _profiles() -> list[tuple[str, np.ndarray, str]]:
    sine_specs = (
        (1, 0.5, 8000),
        (2, 0.3, 6000),
        (5, 0.12, 4000),
        (10, 0.04, 3000),
        (20, 0.01, 2000),
    )
    profiles = [
        ("wmx_ramp_log.txt", _ramp_profile(), "profile=ramp"),
        (
            "wmx_scurve_log.txt",
            profile_scurve(
                5000, DT, -0.3, 0.9,
                max_velocity=1.2,
                max_acceleration=3.0,
                max_jerk=15.0,
            ),
            "profile=scurve",
        ),
        ("wmx_step_log.txt", _step_profile(), "profile=step"),
    ]
    profiles.extend(
        (
            f"wmx_sine_{frequency}hz_log.txt",
            profile_sine(count, DT, amplitude, frequency, center=0.1),
            f"profile=sine frequency={frequency}Hz amplitude={amplitude}rad",
        )
        for frequency, amplitude, count in sine_specs
    )
    return profiles


def _write_log(
    path: Path,
    command: np.ndarray,
    profile_description: str,
    params: MotorParams,
    seed: int,
    rng: np.random.Generator,
    cycle_start: int,
) -> None:
    output = simulate(
        command,
        DT,
        params,
        initial_position=float(command[0]),
    )
    count = len(command)
    position = output["feedback_pos"] + rng.normal(0.0, 2.0e-4, count)
    velocity = output["feedback_vel"] + rng.normal(0.0, 5.0e-3, count)
    torque = output["feedback_torque"] + rng.normal(0.0, 2.0e-2, count)
    params_text = " ".join(f"{key}={value}" for key, value in asdict(params).items())

    with path.open("w", encoding="utf-8") as file:
        file.write("# SYNTHETIC PLACEHOLDER — replace with real WMX3 CoreMotion Data Log\n")
        file.write(f"# {profile_description} backend=newton dt={DT}s seed={seed}\n")
        file.write(f"# MotorParams {params_text}\n")
        file.write("CYCLE TIME SYSTEM_TIME CMDPOS0 FBKPOS0 FBKVEL0 FBKTRQ0\n")
        for index in range(count):
            file.write(
                "%d %.6f %d %.9f %.9f %.9f %.9f\n"
                % (
                    cycle_start + index,
                    index * DT * 1000.0,
                    17758100000000000 + index * 1000,
                    command[index],
                    position[index],
                    velocity[index],
                    torque[index],
                )
            )


def generate_logs(output_dir: Path, seed: int) -> MotorParams:
    params = MOTOR_PARAMS
    rng = np.random.default_rng(seed)
    output_dir.mkdir(parents=True, exist_ok=True)

    for profile_index, (filename, command, description) in enumerate(_profiles()):
        _write_log(
            output_dir / filename,
            command,
            description,
            params,
            seed,
            rng,
            cycle_start=100000 + profile_index * 100000,
        )
        print(f"wrote {output_dir / filename} ({len(command)} rows)")
    return params


def main() -> int:
    parser = argparse.ArgumentParser(description="합성 WMX3 시험 로그 8개 생성")
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument(
        "--seed", type=int, default=20260820,
        help="측정 잡음 재현용 난수 seed (MotorParams에는 영향 없음)",
    )
    args = parser.parse_args()
    params = generate_logs(args.output_dir, args.seed)
    print(f"MotorParams: {params}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
