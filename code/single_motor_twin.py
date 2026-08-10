"""
single_motor_twin.py  —  NVIDIA Newton 기반 무부하 단일 서보 모터 디지털 트윈 (1-DOF) 스켈레톤
================================================================================================
[프로젝트 A] 인턴 시작용 골격 코드.

목적:
  WMX3가 CSP로 내보내는 "Command Position 시계열"을 입력으로 받아, 드라이브+모터의
  응답(Feedback Position / Velocity / Torque)을 시뮬레이션한다. 이 출력 시계열을 WMX
  실측 로그와 비교(피팅)하여 파라미터를 캘리브레이션한다.

모델:
  - 단일 회전 관절(1-DOF), 무부하(중력 0). 링크 관성 J를 유효(반사) 관성으로 사용.
  - 액추에이터: PID(+anti-windup) → 토크 포화(effort_limit) → 지령 지연(delay_steps).
    (Newton actuators의 ControllerPID / Delay / Clamping 개념을 파이썬으로 명시 구현.)
  - 마찰: 점성(viscous b) + 쿨롱(coulomb)을 플랜트에 명시 적용.

인턴이 채울 부분(TODO):
  - 실제 드라이브 구조에 맞게 제어식 정교화(속도루프 분리 등)
  - Newton 내장 actuator 클래스(ControllerPID/ClampingDCMotor)로 치환 실험
  - 파라미터 초기값을 실측 데모기 스펙에 맞게 조정
"""
from dataclasses import dataclass, field
import numpy as np
import warp as wp
import newton


@dataclass
class MotorParams:
    # ---- 피팅 대상 파라미터 (초기값은 자리표시자) ----
    kp: float = 8.0            # 위치 비례 게인
    ki: float = 0.0            # 적분 게인
    kd: float = 0.6            # 미분(속도) 게인
    integral_max: float = 5.0  # anti-windup 적분 한계
    effort_limit: float = 5.0  # 토크 포화 [N·m]
    inertia: float = 0.02      # 유효(반사) 관성 J [kg·m^2]
    viscous: float = 0.01      # 점성 마찰 b [N·m·s/rad]
    coulomb: float = 0.0       # 쿨롱 마찰 [N·m]
    delay_steps: int = 1       # 지령 전송·연산 지연 [사이클]


def _build_model(p: MotorParams):
    b = newton.ModelBuilder(gravity=0.0)  # 무부하: 중력 영향 배제
    J = max(p.inertia, 1e-6)
    inertia = wp.mat33(J, 0.0, 0.0, 0.0, J, 0.0, 0.0, 0.0, J)
    link = b.add_link(mass=1e-3, inertia=inertia)     # 회전 관성 J를 갖는 로터
    j = b.add_joint_revolute(
        parent=-1, child=link, axis=wp.vec3(0.0, 0.0, 1.0),
        target_ke=0.0, target_kd=0.0,                 # 내장 드라이브 미사용(토크 직접 인가)
        effort_limit=1e9, velocity_limit=1e9, friction=0.0,
    )
    b.add_articulation([j])
    return b.finalize()


def simulate(cmd_pos, dt, p: MotorParams):
    """
    cmd_pos : (N,) ndarray  — CSP Command Position 시계열 [rad] (또는 user unit)
    dt      : float         — 통신 사이클 [s] (예: 1e-3 → 1 kHz)
    p       : MotorParams
    returns : dict(feedback_pos, feedback_vel, feedback_torque)  각 (N,)
    """
    model = _build_model(p)
    s0, s1 = model.state(), model.state()
    control = model.control()
    newton.eval_fk(model, model.joint_q, model.joint_qd, s0)
    solver = newton.solvers.SolverFeatherstone(model)

    N = len(cmd_pos)
    fb_pos = np.zeros(N); fb_vel = np.zeros(N); fb_trq = np.zeros(N)
    jf = np.zeros(model.joint_dof_count, dtype=np.float32)
    integ = 0.0
    for k in range(N):
        q = float(s0.joint_q.numpy()[0]); qd = float(s0.joint_qd.numpy()[0])
        # --- 지령 지연 (transport/compute latency) ---
        cmd = cmd_pos[max(0, k - p.delay_steps)]
        # --- PID + anti-windup ---
        err = cmd - q
        integ = float(np.clip(integ + err * dt, -p.integral_max, p.integral_max))
        tau_motor = p.kp * err + p.ki * integ - p.kd * qd
        # --- 토크 포화 (모터/드라이브 한계) ---
        tau_motor = float(np.clip(tau_motor, -p.effort_limit, p.effort_limit))
        # --- 플랜트: 마찰 반영 후 적분 ---
        tau_net = tau_motor - p.viscous * qd - p.coulomb * np.sign(qd)
        jf[0] = tau_net; control.joint_f.assign(jf)
        s0.clear_forces()
        solver.step(s0, s1, control, None, dt)
        s0, s1 = s1, s0
        fb_pos[k] = q; fb_vel[k] = qd; fb_trq[k] = tau_motor  # feedbackTrq ≈ 모터 지령 토크
    return {"feedback_pos": fb_pos, "feedback_vel": fb_vel, "feedback_torque": fb_trq}


# ------- 시험 지령 프로파일 생성 헬퍼 (점대점/사인/주파수 스윕[sim용]) -------
def profile_sine(N, dt, amp, freq_hz, center=0.0):
    t = np.arange(N) * dt
    return center + amp * np.sin(2 * np.pi * freq_hz * t)

def profile_chirp(N, dt, amp, f0, f1, center=0.0):
    t = np.arange(N) * dt; T = N * dt
    inst = f0 + (f1 - f0) * t / T
    phase = 2 * np.pi * np.cumsum(inst) * dt
    return center + amp * np.sin(phase)

def profile_point_to_point(N, dt, dist, move_time):
    # 사다리꼴 근사(간이) — 인턴이 S-curve로 정교화 가능
    t = np.arange(N) * dt
    y = np.clip(t / move_time, 0, 1) * dist
    return y


if __name__ == "__main__":
    dt = 1e-3
    N = 2000
    cmd = profile_chirp(N, dt, amp=0.5, f0=0.5, f1=15.0)
    out = simulate(cmd, dt, MotorParams())
    print("chirp run OK  | pos rms=%.4f vel rms=%.4f trq rms=%.4f"
          % (np.sqrt((out['feedback_pos']**2).mean()),
             np.sqrt((out['feedback_vel']**2).mean()),
             np.sqrt((out['feedback_torque']**2).mean())))
