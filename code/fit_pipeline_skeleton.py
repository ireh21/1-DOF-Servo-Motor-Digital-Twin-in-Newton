"""
fit_pipeline_skeleton.py — WMX 로그 기반 파라미터 피팅 파이프라인 스켈레톤
==========================================================================
흐름: WMX 로그 로드 → 시뮬 입력 정합 → 트윈 실행 → 오차 지표 계산 → (예시) 1-파라미터 스윕 → 시각화

인턴이 확장할 부분(TODO):
  - 시간축 정합(리샘플/동기) 정교화, 단위 변환(user unit ↔ rad)
  - 다중 파라미터 동시 최적화(scipy.optimize / 베이지안 등)로 확장
  - held-out 궤적 교차검증, 주파수 응답(gain/phase) 비교(선택)
"""
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from single_motor_twin import simulate, MotorParams

DT = 1e-3

# === 단위 정합 (실측 WMX 로그를 쓸 때 반드시 설정) =========================
# WMX/EtherCAT 신호는 Newton의 SI 단위와 다르다. 아래 배율로 변환한다.
#   위치: 카운트(또는 user unit) → rad
#   속도: 카운트/s(또는 rpm) → rad/s
#   토크: CiA402 0x6077은 보통 '정격토크 대비 ‰' → N·m = (raw/1000)*정격토크
# 합성 샘플(sample_wmx_log.txt)은 이미 rad/N·m 이므로 아래 값은 1.0.
# 실측 로그로 교체할 때 데모기 스펙에 맞춰 반드시 수정할 것.  (TODO)
POS_SCALE = 1.0   # 예) 2*pi / encoder_counts_per_rev
VEL_SCALE = 1.0   # 예) (2*pi/60) if rpm
TRQ_SCALE = 1.0   # 예) rated_torque_Nm / 1000.0  (‰ → N·m)
# ==========================================================================

def load_wmx_log(path):
    """WMX CoreMotion Data Log(텍스트) → dict (SI 단위로 변환). 숫자로 시작하지 않는 줄은 헤더로 skip."""
    rows = []
    cols = None
    for line in open(path):
        s = line.strip()
        if not s or s.startswith("#"):
            continue
        parts = s.split()
        try:
            float(parts[0])
        except ValueError:
            cols = parts   # 컬럼명 줄
            continue
        rows.append([float(x) for x in parts])
    arr = np.array(rows)
    idx = {c: i for i, c in enumerate(cols)}
    return {
        "cmd_pos": arr[:, idx["CMDPOS0"]] * POS_SCALE,
        "fb_pos":  arr[:, idx["FBKPOS0"]] * POS_SCALE,
        "fb_vel":  arr[:, idx["FBKVEL0"]] * VEL_SCALE,
        "fb_trq":  arr[:, idx["FBKTRQ0"]] * TRQ_SCALE,
    }

def error_metric(sim, meas):
    """정규화 RMSE 합 (위치/속도/토크). 인턴이 가중치·지표 조정 가능."""
    def nrmse(a, b):
        return np.sqrt(np.mean((a - b) ** 2)) / (np.std(b) + 1e-9)
    return (nrmse(sim["feedback_pos"], meas["fb_pos"])
            + nrmse(sim["feedback_vel"], meas["fb_vel"])
            + nrmse(sim["feedback_torque"], meas["fb_trq"]))

def run(params, meas):
    return simulate(meas["cmd_pos"], DT, params)

if __name__ == "__main__":
    meas = load_wmx_log("sample_wmx_log.txt")
    print("loaded %d samples" % len(meas["cmd_pos"]))

    # 초기 추정(정답 모름) → 오차
    guess = MotorParams(kp=8.0, ki=0.0, kd=0.6, inertia=0.02, viscous=0.01, delay_steps=1)
    e0 = error_metric(run(guess, meas), meas)
    print("initial guess error = %.4f" % e0)

    # --- 예시: inertia 1-파라미터 스윕으로 최소 오차 지점 찾기 ---
    Js = np.linspace(0.01, 0.06, 11)
    errs = []
    for J in Js:
        p = MotorParams(kp=12.0, ki=2.0, kd=0.9, integral_max=4.0,
                        continuous_torque_limit=6.0, peak_torque_limit=6.0,
                        inertia=float(J), viscous=0.02, delay_steps=2)
        errs.append(error_metric(run(p, meas), meas))
    errs = np.array(errs); Jbest = Js[errs.argmin()]
    print("sweep inertia: best J = %.4f (true≈0.03)  err=%.4f" % (Jbest, errs.min()))

    # --- 시각화 ---
    best = MotorParams(kp=12.0, ki=2.0, kd=0.9, integral_max=4.0,
                       continuous_torque_limit=6.0, peak_torque_limit=6.0,
                       inertia=float(Jbest), viscous=0.02, delay_steps=2)
    sim = run(best, meas)
    t = np.arange(len(meas["cmd_pos"])) * DT
    fig, ax = plt.subplots(2, 1, figsize=(10, 6))
    ax[0].plot(t, meas["fb_pos"], label="measured (fb_pos)", lw=1)
    ax[0].plot(t, sim["feedback_pos"], "--", label="twin (best J)", lw=1)
    ax[0].plot(t, meas["cmd_pos"], ":", color="gray", label="command", lw=0.8)
    ax[0].set_ylabel("position [rad]"); ax[0].legend(loc="upper right"); ax[0].set_title("Twin vs Measured")
    ax[1].plot(Js, errs, "o-"); ax[1].axvline(0.03, color="r", ls=":", label="true J")
    ax[1].set_xlabel("inertia J"); ax[1].set_ylabel("error"); ax[1].legend()
    fig.tight_layout(); fig.savefig("fit_result.png", dpi=110)
    print("saved fit_result.png")
