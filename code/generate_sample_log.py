"""
generate_sample_log.py — 합성(SYNTHETIC) WMX3 로그 샘플 생성기
================================================================
실제 데모기 하드웨어가 준비되기 전, 인턴이 피팅 파이프라인을 개발/검증할 수 있도록
WMX3 CoreMotion Data Log 형식과 유사한 4신호 텍스트 로그를 생성한다.

⚠️  이 파일이 만드는 데이터는 '가짜(합성)'다. 실제 캘리브레이션에는 반드시 실측
    WMX3 로그로 대체할 것. (컬럼/형식만 실제와 맞춰 둠)

형식: 헤더줄(#) → 컬럼명줄 → 매 사이클 데이터
      CYCLE  TIME  SYSTEM_TIME  CMDPOS0  FBKPOS0  FBKVEL0  FBKTRQ0
"""
import numpy as np
from single_motor_twin import simulate, MotorParams, profile_chirp, profile_point_to_point

dt = 1e-3
# "정답" 파라미터 (인턴은 이 값을 모른다고 가정하고 피팅으로 복원)
TRUE = MotorParams(kp=12.0, ki=2.0, kd=0.9, integral_max=4.0,
                   effort_limit=6.0, inertia=0.03, viscous=0.02,
                   coulomb=0.0, delay_steps=2)

# 시험 지령 프로파일(합성 sim용): 주파수 스윕 + 점대점 이어붙이기
cmd = np.concatenate([
    profile_chirp(3000, dt, amp=0.5, f0=0.5, f1=20.0),
    profile_point_to_point(1000, dt, dist=1.0, move_time=0.4) + profile_chirp(3000, dt, 0.5, 0.5, 20.0)[-1],
])
N = len(cmd)
out = simulate(cmd, dt, TRUE)

# 측정 잡음 (실측 유사)
rng = np.random.default_rng(0)
pos = out["feedback_pos"] + rng.normal(0, 2e-4, N)
vel = out["feedback_vel"] + rng.normal(0, 5e-3, N)
trq = out["feedback_torque"] + rng.normal(0, 2e-2, N)

with open("sample_wmx_log.txt", "w") as f:
    f.write("# SYNTHETIC PLACEHOLDER — replace with real WMX3 CoreMotion Data Log\n")
    f.write("CYCLE TIME SYSTEM_TIME CMDPOS0 FBKPOS0 FBKVEL0 FBKTRQ0\n")
    for k in range(N):
        f.write("%d %.6f %d %.9f %.9f %.9f %.9f\n"
                % (10000 + k, k * dt * 1000.0, 17758100000000000 + k * 1000,
                   cmd[k], pos[k], vel[k], trq[k]))
print("wrote sample_wmx_log.txt  (%d rows)" % N)
