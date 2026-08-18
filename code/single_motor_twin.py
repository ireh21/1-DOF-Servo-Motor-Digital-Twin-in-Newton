"""Newton 기반 1축 서보 모터 디지털 트윈.

WMX Command Position을 입력으로 받아 PID 제어기와 회전축의 관성/마찰을
계산한다. Newton은 시뮬레이션을 시작할 때만 import하므로 프로파일 함수는
Newton이 없는 환경에서도 사용할 수 있다.
"""
from __future__ import annotations

import argparse
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable

import numpy as np


@dataclass(frozen=True)
class MotorParams:
    """1축 서보 제어기와 기계 플랜트 파라미터(SI 단위)."""

    kp: float = 8.0                 # [N m/rad]
    ki: float = 0.0                 # [N m/(rad s)]
    kd: float = 0.6                 # [N m s/rad]
    integral_max: float = 5.0       # [rad s]
    effort_limit: float = 5.0       # [N m]
    inertia: float = 0.02           # [kg m^2]
    viscous: float = 0.01           # [N m s/rad]
    coulomb: float = 0.0            # [N m]
    delay_steps: int = 1            # [cycle]

    def validate(self) -> None:
        for name in ("kp", "ki", "kd", "integral_max", "effort_limit",
                     "inertia", "viscous", "coulomb"):
            if not np.isfinite(getattr(self, name)):
                raise ValueError(f"{name}은 유한한 값이어야 합니다.")
        for name in ("integral_max", "effort_limit", "viscous", "coulomb"):
            if getattr(self, name) < 0.0:
                raise ValueError(f"{name}은 0 이상이어야 합니다.")
        if self.inertia <= 0.0:
            raise ValueError("inertia는 0보다 커야 합니다.")
        if (isinstance(self.delay_steps, bool)
                or not isinstance(self.delay_steps, (int, np.integer))
                or self.delay_steps < 0):
            raise ValueError("delay_steps는 0 이상의 정수여야 합니다.")


def _newton_modules():
    try:
        import newton
        import warp as wp
    except ImportError as exc:
        raise RuntimeError(
            "Newton/Warp를 불러오지 못했습니다. 두 패키지가 설치된 프로젝트 "
            "가상환경을 활성화한 뒤 실행하세요."
        ) from exc
    return newton, wp


def build_motor_model(params: MotorParams, *, device: str = "cpu"):
    """Viewer 형상을 포함한 무부하 1-DOF revolute-joint 모델을 만든다."""
    params.validate()
    newton, wp = _newton_modules()
    builder = newton.ModelBuilder(gravity=0.0)
    inertia = float(params.inertia)
    rotor = builder.add_link(
        mass=1.0e-3,
        inertia=wp.mat33(inertia, 0.0, 0.0,
                         0.0, inertia, 0.0,
                         0.0, 0.0, inertia),
        lock_inertia=True,
        label="motor_rotor",
    )
    # as_site 형상은 관성이나 충돌에 영향을 주지 않는 Viewer 전용 형상이다.
    builder.add_shape_cylinder(
        rotor, radius=0.05, half_height=0.015, as_site=True,
        label="rotor_visual",
    )
    builder.add_shape_box(
        rotor,
        xform=wp.transform(wp.vec3(0.04, 0.0, 0.025), wp.quat_identity()),
        hx=0.035, hy=0.006, hz=0.006, as_site=True,
        label="rotor_marker",
    )
    joint = builder.add_joint_revolute(
        parent=-1, child=rotor, axis=wp.vec3(0.0, 0.0, 1.0),
        target_ke=0.0, target_kd=0.0,
        damping=0.0, armature=0.0, friction=0.0,
        effort_limit=1.0e9, velocity_limit=1.0e9,
        label="motor_joint",
    )
    builder.add_articulation([joint], label="single_servo_motor")
    return builder.finalize(device=device)


def _make_viewer(newton: Any, model: Any, record_path):
    kwargs: dict[str, Any] = {
        "label": "Single Servo Motor Digital Twin",
        "plot_history_size": 500,
    }
    if record_path is not None:
        kwargs["record_to_viser"] = str(record_path)
    viewer = newton.viewer.ViewerViser(**kwargs)
    viewer.set_model(model)
    try:
        _, wp = _newton_modules()
        viewer.set_camera(wp.vec3(0.25, -0.30, 0.18), -20, 130)
    except (AttributeError, TypeError):
        pass
    return viewer


def simulate_motor(
    command_position: Iterable[float],
    dt: float,
    params: MotorParams | None = None,
    *,
    device: str = "cpu",
    use_viewer: bool = False,
    viewer_fps: float = 60.0,
    viewer_record_path: str | Path | None = "single_motor.viser",
    initial_position: float = 0.0,
    initial_velocity: float = 0.0,
) -> dict[str, Any]:
    """Command Position에 대한 위치/속도/토크 응답을 계산한다.

    피드백 위치와 속도의 k번째 값은 k번째 제어 주기 시작 상태이고,
    피드백 토크는 그 주기에 PID가 계산한 모터 토크이다.
    """
    params = params or MotorParams()
    params.validate()
    command = np.asarray(command_position, dtype=np.float32)
    if command.ndim != 1 or command.size == 0:
        raise ValueError("command_position은 비어 있지 않은 1차원 배열이어야 합니다.")
    if not np.all(np.isfinite(command)):
        raise ValueError("command_position에 NaN 또는 inf가 있습니다.")
    if not np.isfinite(dt) or dt <= 0.0:
        raise ValueError("dt는 0보다 큰 유한한 값이어야 합니다.")
    if not np.isfinite(viewer_fps) or viewer_fps <= 0.0:
        raise ValueError("viewer_fps는 0보다 큰 유한한 값이어야 합니다.")

    newton, _ = _newton_modules()
    model = build_motor_model(params, device=device)
    model.joint_q.assign(np.array([initial_position], dtype=np.float32))
    model.joint_qd.assign(np.array([initial_velocity], dtype=np.float32))
    state_0, state_1 = model.state(), model.state()
    control = model.control()
    newton.eval_fk(model, model.joint_q, model.joint_qd, state_0)
    newton.eval_fk(model, model.joint_q, model.joint_qd, state_1)
    # Newton 기본 damping과 식별할 viscous 계수가 섞이지 않게 한다.
    solver = newton.solvers.SolverFeatherstone(model, angular_damping=0.0)

    count = command.size
    time = np.arange(count, dtype=np.float64) * dt
    fb_pos = np.zeros(count, dtype=np.float64)
    fb_vel = np.zeros(count, dtype=np.float64)
    fb_trq = np.zeros(count, dtype=np.float64)
    net_trq = np.zeros(count, dtype=np.float64)
    errors = np.zeros(count, dtype=np.float64)
    delayed_command = np.zeros(count, dtype=np.float64)
    integral = 0.0
    joint_force = np.zeros(model.joint_dof_count, dtype=np.float32)
    viewer = _make_viewer(newton, model, viewer_record_path) if use_viewer else None
    render_stride = max(1, int(round(1.0 / (viewer_fps * dt))))

    for k in range(count):
        q = float(state_0.joint_q.numpy()[0])
        qd = float(state_0.joint_qd.numpy()[0])
        fb_pos[k], fb_vel[k] = q, qd

        cmd = float(command[max(0, k - int(params.delay_steps))])
        error = cmd - q
        integral = float(np.clip(
            integral + error * dt, -params.integral_max, params.integral_max,
        ))
        tau_motor = float(np.clip(
            params.kp * error + params.ki * integral - params.kd * qd,
            -params.effort_limit, params.effort_limit,
        ))
        tau_net = float(
            tau_motor - params.viscous * qd - params.coulomb * np.sign(qd)
        )
        fb_trq[k], net_trq[k] = tau_motor, tau_net
        errors[k], delayed_command[k] = error, cmd

        joint_force[0] = tau_net
        control.joint_f.assign(joint_force)
        state_0.clear_forces()
        solver.step(state_0, state_1, control, None, dt)
        state_0, state_1 = state_1, state_0

        if viewer is not None and k % render_stride == 0:
            viewer.begin_frame((k + 1) * dt)
            viewer.log_state(state_0)
            viewer.log_scalar("Motor/Command Position", float(command[k]))
            viewer.log_scalar("Motor/Feedback Position", float(state_0.joint_q.numpy()[0]))
            viewer.log_scalar("Motor/Feedback Velocity", float(state_0.joint_qd.numpy()[0]))
            viewer.log_scalar("Motor/Motor Torque", tau_motor)
            viewer.end_frame()

    result = {
        "time": time,
        "command_position": command,
        "delayed_command_position": delayed_command,
        "feedback_position": fb_pos,
        "feedback_velocity": fb_vel,
        "feedback_torque": fb_trq,
        "net_torque": net_trq,
        "position_error": errors,
        "viewer": viewer,
        "model": model,
    }
    # 기존 스크립트에서 사용하던 짧은 key도 유지한다.
    result.update({"feedback_pos": fb_pos, "feedback_vel": fb_vel})
    return result


def simulate(command_position, dt, params: MotorParams | None = None, **kwargs):
    """기존 코드 호환용 ``simulate_motor`` 별칭."""
    return simulate_motor(command_position, dt, params, **kwargs)


def simulate_wmx_log(
    file_path: str | Path,
    params: MotorParams | None = None,
    *,
    time_unit: str = "ms",
    position_scale: float = 1.0,
    velocity_scale: float = 1.0,
    torque_scale: float = 1.0,
    **simulation_kwargs,
):
    """WMX 로그를 읽어 시뮬레이션하고 ``(simulation, measurement)``를 반환한다."""
    from wmx_log_utils import load_wmx_log

    measurement = load_wmx_log(
        file_path, time_unit=time_unit, position_scale=position_scale,
        velocity_scale=velocity_scale, torque_scale=torque_scale,
    )
    simulation = simulate_motor(
        measurement["command_position"], measurement["dt"], params,
        **simulation_kwargs,
    )
    return simulation, measurement


def _validate_profile_common(N, dt):
    if isinstance(N, bool) or not isinstance(N, (int, np.integer)) or N <= 0:
        raise ValueError("N은 0보다 큰 정수여야 합니다.")
    if not np.isfinite(dt) or dt <= 0.0:
        raise ValueError("dt는 0보다 큰 유한한 값이어야 합니다.")


def profile_step(N, dt, start_pos=0.0, target_pos=1.0, start_time=0.2):
    _validate_profile_common(N, dt)
    if start_time < 0.0:
        raise ValueError("start_time은 0 이상이어야 합니다.")
    time = np.arange(N) * dt
    command = np.full(N, start_pos, dtype=np.float32)
    command[time >= start_time] = target_pos
    return command


def profile_sine(N, dt, amp, freq_hz, center=0.0):
    _validate_profile_common(N, dt)
    if freq_hz < 0.0:
        raise ValueError("freq_hz는 0 이상이어야 합니다.")
    time = np.arange(N) * dt
    return (center + amp * np.sin(2.0 * np.pi * freq_hz * time)).astype(np.float32)


def profile_chirp(N, dt, amp, f0, f1, center=0.0):
    _validate_profile_common(N, dt)
    if f0 < 0.0 or f1 < 0.0:
        raise ValueError("f0와 f1은 0 이상이어야 합니다.")
    time = np.arange(N) * dt
    sweep_rate = (f1 - f0) / (N * dt)
    phase = 2.0 * np.pi * (f0 * time + 0.5 * sweep_rate * time**2)
    return (center + amp * np.sin(phase)).astype(np.float32)


def profile_point_to_point(N, dt, dist, move_time, start_pos=0.0):
    _validate_profile_common(N, dt)
    if move_time <= 0.0:
        raise ValueError("move_time은 0보다 커야 합니다.")
    time = np.arange(N) * dt
    return (start_pos + np.clip(time / move_time, 0.0, 1.0) * dist).astype(np.float32)


def profile_scurve(
    N, dt, start_pos, target_pos,
    max_velocity, max_acceleration, max_jerk,
):
    """속도/가속도/저크 제한을 갖는 대칭 7구간 S-curve Command."""
    _validate_profile_common(N, dt)
    signed_distance = float(target_pos - start_pos)
    if abs(signed_distance) < 1.0e-12:
        return np.full(N, start_pos, dtype=np.float32)
    velocity, acceleration, jerk_max = map(
        abs, (float(max_velocity), float(max_acceleration), float(max_jerk))
    )
    if min(velocity, acceleration, jerk_max) <= 0.0:
        raise ValueError("속도, 가속도, 저크 제한은 0보다 커야 합니다.")

    direction, distance = np.sign(signed_distance), abs(signed_distance)
    tj_acc, tj_vel = acceleration / jerk_max, np.sqrt(velocity / jerk_max)
    if tj_vel < tj_acc:
        tj, ta = tj_vel, 0.0
        d_to_v = 2.0 * velocity * tj
        if distance >= d_to_v:
            tv = (distance - d_to_v) / velocity
        else:
            tj, tv = (distance / (2.0 * jerk_max)) ** (1.0 / 3.0), 0.0
    else:
        tj = tj_acc
        ta_to_v = velocity / acceleration - tj
        d_to_v = velocity * (2.0 * tj + ta_to_v)
        if distance >= d_to_v:
            ta, tv = ta_to_v, (distance - d_to_v) / velocity
        else:
            ta = (-3.0 * tj + np.sqrt(tj**2 + 4.0 * distance / acceleration)) / 2.0
            if ta < 0.0:
                tj, ta = (distance / (2.0 * jerk_max)) ** (1.0 / 3.0), 0.0
            tv = 0.0

    durations = np.array([tj, ta, tj, tv, tj, ta, tj])
    jerks = direction * np.array([
        jerk_max, 0.0, -jerk_max, 0.0, -jerk_max, 0.0, jerk_max,
    ])
    move_time = float(durations.sum())
    available_time = (N - 1) * dt
    if available_time + 1.0e-12 < move_time:
        raise ValueError(
            f"사용 가능한 시간 {available_time:.3f}s가 S-curve 이동시간 "
            f"{move_time:.3f}s보다 짧습니다."
        )

    starts = []
    q, qd, qdd = float(start_pos), 0.0, 0.0
    for duration, jerk in zip(durations, jerks):
        starts.append((q, qd, qdd, jerk))
        q += qd * duration + 0.5 * qdd * duration**2 + jerk * duration**3 / 6.0
        qd += qdd * duration + 0.5 * jerk * duration**2
        qdd += jerk * duration

    segment_ends = np.cumsum(durations)
    segment_begins = np.concatenate(([0.0], segment_ends[:-1]))
    command = np.empty(N, dtype=np.float32)
    for k, time in enumerate(np.arange(N) * dt):
        if time >= move_time:
            command[k] = target_pos
            continue
        segment = int(np.searchsorted(segment_ends, time, side="right"))
        q0, qd0, qdd0, jerk = starts[segment]
        local_time = time - segment_begins[segment]
        command[k] = (
            q0 + qd0 * local_time + 0.5 * qdd0 * local_time**2
            + jerk * local_time**3 / 6.0
        )
    return command


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="Newton 1축 모터 디지털 트윈")
    parser.add_argument("--profile", choices=("step", "sine", "chirp", "scurve"), default="scurve")
    parser.add_argument("--duration", type=float, default=5.0)
    parser.add_argument("--dt", type=float, default=1.0e-3)
    parser.add_argument("--amplitude-deg", type=float, default=90.0)
    parser.add_argument("--viewer", action="store_true")
    parser.add_argument("--device", default="cpu")
    args = parser.parse_args(argv)
    count, amplitude = int(round(args.duration / args.dt)), np.deg2rad(args.amplitude_deg)
    profiles = {
        "step": lambda: profile_step(count, args.dt, 0.0, amplitude, 0.5),
        "sine": lambda: profile_sine(count, args.dt, amplitude, 0.5),
        "chirp": lambda: profile_chirp(count, args.dt, amplitude, 0.2, 3.0),
        "scurve": lambda: profile_scurve(
            count, args.dt, 0.0, amplitude,
            np.deg2rad(60), np.deg2rad(180), np.deg2rad(900),
        ),
    }
    command = profiles[args.profile]()
    result = simulate_motor(command, args.dt, device=args.device, use_viewer=args.viewer)
    print("simulation OK | samples=%d pos_rms=%.5f vel_rms=%.5f torque_rms=%.5f" % (
        count,
        np.sqrt(np.mean(result["feedback_position"] ** 2)),
        np.sqrt(np.mean(result["feedback_velocity"] ** 2)),
        np.sqrt(np.mean(result["feedback_torque"] ** 2)),
    ))
    if result["viewer"] is not None:
        print(f"Viewer 기록: {Path('single_motor.viser').resolve()}")
    return 0


__all__ = [
    "MotorParams", "build_motor_model", "simulate_motor", "simulate",
    "simulate_wmx_log", "profile_step", "profile_sine", "profile_chirp",
    "profile_point_to_point", "profile_scurve",
]


if __name__ == "__main__":
    raise SystemExit(main())
