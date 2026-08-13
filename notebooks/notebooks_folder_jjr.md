## feedback_torque와 net_torque의 차이 (01 notebook)

우리가 WMX3에서 얻어올 수 있는 토크값은, 실제 물리적인 특성이 포함된 최종, 그러니까 현재 모터가 돌아가는 정도를 나타내는 토크값이 아닌!
모터야 너가 이만큼의 토크로 돌리거라~ 라고 하는 주는 값의 토크값을 feedback torque로 얻어온다

물론, 돌아가는 모터에 최종 토크값을 얻기위해 엔코더를 달면 그것도 알 수는 있겠지만 일단 그건 아니고...  


하여튼 그래서 우리가 wmx3에서 얻어오는 feedback torque값은

내가 작성한 저 single_motor_twin.ipynb의 `tau_motor` (Motor Torque)랑 비교해야함. 
`tau_net` (Net Torque)는 점성마찰과 쿨롱마찰로 인해 토크마찰이 생기는데 Motor Torque에서 토크마찰을 뺀 값이 Net이다.

그럼 비교도 안하는데 net은 왜 계산하냐?  
Newton의 물리 엔진에게 "모터토크와 마찰토크를 모두 고려했을 때 실제 회전축에 남는 최종 토크"를 전달하기 위해 만든 내부 계산값임.  
현재 Newton 물리 엔진 내부에 자체로 있는 내부 마찰을 끄고 연산중이기에, 우리가 직접 마찰토크를 빼주고 넣어야하는거임.  
그럼 뉴턴 자체의 내부 마찰은 왜 껐냐?    
점성마찰, 쿨롱 마찰을 우리가 parameter로 지정해서 나중에 바꾸기 위해서 꺼놓음.

---

## Parameter가 모터의 응답에 끼치는 영향

- P gain (Kp) 변화  
kp가 커지면? 응답이 빨라지고, 정상상태 오차가 감소, overshoot 증가 시스템 불안정해질 수도.

- I gain (Ki) 변화  
ki가 크면? 정상상태 오차가 빠르게 제거. Overshoot, Ts가 증가한다. 너무 커지면 적분 포화(windup)로 시스템이 불안정해짐.

- D gain (kd) 변화
kd가 크면? 오차 변화율에 미리 반응해 overshoot, Ts 감소. 안정성 개선. 정상상태 오차에는 영향 X. 너무 크면 느려진다... 

| 파라미터 증가           | 위치 Position                 | 속도 Velocity    | Motor Torque     | 핵심 역할         |
| ---------------- | --------------------------- | -------------- | ---------------- | ------------- |
| `kp` ↑           | 더 빨리 목표 접근, 과하면 overshoot ↑ | peak ↑         | 오차에 대한 토크 ↑      | 강하게 따라감       |
| `ki` ↑           | 누적오차 보정, 과하면 overshoot/진동 ↑ | 진동·peak 증가 가능  | 토크가 오래 남음        | 남은 오차 제거      |
| `integral_max` ↑ | I항 영향 허용 범위 ↑               | overshoot 가능 ↑ | I 토크 최대량 ↑       | windup 제한     |
| `kd` ↑           | overshoot ↓, 너무 크면 느림       | peak ↓         | 움직일 때 제동 토크 ↑    | damping       |
| `delay_steps` ↑  | 반응 시작 늦음                    | 반응 늦음          | 토크 발생도 늦음        | 시간 지연         |
| `effort_limit` ↑ | 더 빠르게 움직일 수 있음              | peak ↑         | 허용 최대 토크 ↑       | 토크 saturation |
| `inertia` ↑      | 느려짐, 경우에 따라 overshoot ↑     | 가속/peak ↓      | 큰 토크가 더 오래 필요    | 회전하기 어려움      |
| `viscous` ↑      | 감쇠 ↑, overshoot ↓           | peak ↓         | 움직이는 동안 보상 토크 필요 | 속도 비례 마찰      |
| `coulomb` ↑      | 이동 저항/추종오차 ↑                | 속도 ↓           | 마찰 극복 토크 필요      | 방향 반대 일정 마찰   |

---


WMX 로그를 읽고
모터 파라미터를 추정하고
시뮬레이션 결과를 실제 log와 비교하고
적절한 오차를 계산하고
결과를 문서화하는 흐름
이 전체를 하나의 체계로 정리해야 합니다.

WMX 실측 로그를 입력으로 받아, Newton 기반 단일 모터 디지털 트윈의 파라미터를 자동으로 추정하고, 실측 응답을 재현할 수 있는 가이드와 실행 파이프라인을 만든다.



지금 당장 할 일: 가장 현실적인 작업 목록

현재 노트북 내용을 기반으로 “프로젝트 개요 문서” 작성
01/02/03의 역할 정리
단일 모터 디지털 트윈 목표 정리

실측 WMX 로그 여러 개로 테스트
파라미터가 잘 안 맞는 경우 원인 분석
kp, kd, inertia, delay 우선순위 조정

docs 정리
프로젝트 가이드 초안 작성
“what/why/how/limitations” 형식으로 정리






추천 방식
가장 현실적인 방식은 이 3단계입니다.

03의 실측 로그를 기준으로 objective function 정의
범위를 정한 뒤 전역 탐색으로 초기값 추정
그값을 L-BFGS-B로 정밀 최적화
다른 로그로 validation

가장 추천하는 피팅 방법
이건 지금 구조에 제일 잘 맞습니다.

1차: coarse global search
differential_evolution
2차: local refinement
minimize(..., method="L-BFGS-B")
3차: validation
다른 WMX 로그로 최종 확인
이 조합이 “디지털 트윈”에 가장 적합합니다.

Step response log
예: +90 deg 또는 -90 deg 계단 입력
목적:
kp, kd, delay_steps
overshoot, rise time, settling time
inertia의 영향 확인
꼭 필요한 이유:
가장 기본적이고 식별성이 좋음
Reverse-direction step or zero-crossing log
예: 0 → +45 → 0 → -45 → 0
목적:
coulomb
direction change 시 마찰
static friction / dead-zone 확인
꼭 필요한 이유:
Coulomb friction은 방향 전환 구간에서만 드러남
Sine or low-frequency periodic log
예: 0.2 ~ 1 Hz, amplitude 10~30 deg
목적:
phase lag
gain attenuation
damping
viscous와 kp,kd의 분리
꼭 필요한 이유:
step만으로는 속도 지연과 damping을 분리하기 어려움
Chirp log
예: 0.2 Hz → 5 Hz
목적:
bandwidth
고주파에서의 지연
inertia와 delay 분리
실제 주파수 응답 특성
꼭 필요한 이유:
모터가 “어떤 대역폭까지 잘 추종하는지”를 보기에 좋음