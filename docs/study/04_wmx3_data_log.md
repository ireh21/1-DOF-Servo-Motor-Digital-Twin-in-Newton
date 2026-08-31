# WMX3 실측 데이터 준비와 입력 파형 설계

> **참고**
>
> 이 문서는 WMX3의 Data Log를 통해 단일 모터 데모기의 실측 데이터를 취득하고,
> 이를 Newton 시뮬레이션 결과와 비교 가능한 형태로 정리하기 위한 기준을 다룬다.  
> 구체적으로는 어떤 신호를 취득해야 하는지, 단위 정합을 위해 어떤 하드웨어 정보를 확인해야 하는지,
> 그리고 피팅을 위해 어떤 입력 파형을 준비하고 어떻게 구분할지에 초점을 둔다.
>
> 이 문서에서 `WMX 로그`는 Data Log로 저장한 원본 로그 파일을 뜻하고,
> `실측 데이터`는 해당 로그를 불러와 단위 변환과 시간축 정렬을 거친 뒤 분석에 사용하는 신호를 뜻한다.

## 1. 데이터 취득 목적

본 프로젝트에서는 실제 단일 서보 모터의 응답과 Newton 기반 디지털 트윈의 응답을 비교하여
제어기 및 물리 파라미터를 조정한다.

이를 위해 실제 장비에 동일한 Command Position을 입력하고,
WMX3 Data Log를 이용하여 다음 신호를 취득한다.

- Command Position
- Feedback Position
- Feedback Velocity
- Feedback Torque

취득한 데이터는 단위 변환과 시간축 정렬을 거친 뒤,
Newton의 입력 및 출력 신호와 비교한다.


## 2. WMX3 Data Log 형식과 신호

제공된 샘플 Data Log는 다음과 같은 컬럼으로 구성되어 있다.

```text
CYCLE
CommandPos-0
FeedbackPos-0
FeedbackVelocity-0
FeedbackTrq-0
```

현재 코드의 `wmx_log_utils.py`는 CSV 헤더를 읽을 때 대소문자와 `-` 같은 구분 문자를 무시하고 정규화한다.  
따라서 실제 파일에서 `FeedbackTrq-0`, `feedbacktrq0`, `FeedbackTrq`처럼 표기가 조금 달라도
동일한 torque 채널로 인식할 수 있다.

### 2.1 시간 관련 데이터

- `CYCLE`
  데이터가 취득된 제어 주기의 순번이다.  
  현재 기준은 1ms 주기이다.

### 2.2 제어 및 피드백 신호

- `CommandPos-0`  
  0번 축에 전달된 Command Position이다.
  Newton 시뮬레이션에 동일한 위치 지령을 넣기 위한 기준 신호로 사용한다.
- `FeedbackPos-0`  
  실제 모터의 Feedback Position이다.
  Newton의 관절 위치와 비교한다.
- `FeedbackVelocity-0`  
  실제 모터의 Feedback Velocity이다.
  Newton의 관절 속도와 비교한다.
- `FeedbackTrq-0`  
  실제 드라이브에서 제공하는 Feedback Torque이다. 
  Newton의 토크 응답과 비교한다.


## 3. 단일 모터 데모기와 단위 정합에 필요한 정보

WMX 로그를 Newton과 비교하려면,
로그의 숫자만 보는 것이 아니라 그 숫자가 어떤 하드웨어와 어떤 설정에서 나온 값인지 먼저 확인해야 한다.

| 확인 항목 | 확인 내용 | 현재 상태 |
|---|---|---|
| 모터 모델 | Panasonic `MSMF5AZL1S2` | 확인 |
| 정격 토크 | Torque 변환 기준 | `0.16 N·m` |
| 드라이브 모델 | Panasonic `MADLN05BE` | 확인 |
| 전원 | 드라이브 입력 전원 | `AC 220 V` |
| 엔코더 분해능 | Position 단위 변환 기준 | `8,388,608 pulse/rev` |
| 기어비 | 모터측과 부하측 변환 비율 | `1:1` |
| 연속 토크 제한 | 장시간 출력 기준 | `0.16 N·m` |
| 순간 피크 토크 제한 | 단시간 출력 상한 | `0.48 N·m` |
| 기계 구성 | 무부하 여부, 커플링 등 | TBD |
| 제어 축 번호 | WMX3에서 사용하는 Axis 번호 | TBD |
| 운전 모드 | CSP 사용 여부 | TBD |
| Position 단위 | count / user unit 등 | `1 U = 1 deg` |
| Velocity 단위 | count/s / rpm 등 | `deg/s` |
| Torque 단위 | ‰ / % / N·m 등 | `%` |
| 회전 방향 | 실제 장비와 Newton의 부호 규약 | TBD |

현재는 Position User Unit을 `deg` 기준으로 설정해 사용한다.


## 4. 단위 정합

WMX3 Position 및 Velocity는 `deg` 기준 User Unit으로 설정한다.

- Encoder Resolution: `8,388,608 pulse/rev`
- Reduction Gear: 없음 (1:1)
- Position Control Resolution: `1 U = 1 deg`

### 4.1 Position

Master Gear Ratio:

- 분자: `8,388,608 pulse/rev`
- 분모: `360 U/rev`

따라서:

```text
WMX Position = 1   → 1 deg
WMX Position = 90  → 90 deg
WMX Position = 360 → 360 deg = 1회전
```

변환식:

```text
Newton Position [rad] = WMX Position [deg] × π / 180
```

### 4.2 Velocity

Velocity는 `deg/s` 단위이며, Position과 동일한 비율로 변환한다.

```text
Newton Velocity [rad/s] = WMX Velocity [deg/s] × π / 180
```

### 4.3 Torque

`FeedbackTrq`는 `%` 단위이며, 모터 정격 토크는 `0.16 N·m`이다.

```text
Newton Torque [N·m]
= FeedbackTrq × 0.01 × 0.16
= FeedbackTrq × 0.0016
```


## 5. WMX 로그 취득 방법과 입력 파형 생성

WMX3 API의 `ClosedLoop` 기반 시험 기능으로 입력 파형을 생성하고,
축 응답 데이터를 로그로 저장해 취득하였다.

입력 파형은 step, ramp, sine, s-curve를 생성하였다.

- step
  `StartClosedLoop()`의 setpoint 변경 사용
- ramp
  `opts.SetRampRate()`를 통한 setpoint 변화율 제어 사용
- sine
  `StartSineGenerator()` 사용
- s-curve
  `Motion::PosCommand`의 profile, velocity, acc, dec 사용

s-curve는 `/opt/wmx3/sample/1_BasicMotion/03_MotorControl.cpp`,
그 외는 `/opt/wmx3/sample/2_DerivedMotion/08_CyclicBufferMotion.cpp`
기반으로 API에 맞게 수정하여 입력 파형을 생성하였다.


### @ 입력 파형을 왜 준비해야 하는가

피팅에서는 단순히 "실측 데이터를 많이 모은다"보다,
**어떤 파형이 어떤 특성을 드러내는지**를 구분해서 준비하는 것이 중요하다.

하나의 입력 파형만으로는 지연, 관성, 제어 게인, 마찰, 일반화 성능을 모두 안정적으로 구분하기 어렵다.  
따라서 서로 다른 성격의 입력 파형을 준비하고,
각 파형이 잘 드러내는 특성을 기준으로 로그를 해석한다.


## 7. 입력 파형별 역할

### Stop 파형

사용 목적: 토크 바이어스와 노이즈 확인  
피팅 대상: 직접적인 피팅 파라미터는 아님

Stop 로그는 정지 상태에서의 토크 noise floor를 확인하는 데 사용한다.
이 값은 이후 토크 loss 계산에서 작은 오차를 무시하는 deadband 또는 tolerance 기준으로 활용할 수 있다.

### Step 파형

사용 목적: Command Position 변화에 대한 응답지연과 과도응답 확인  
주로 드러나는 특성: `delay_steps`, `kp`, `kd`, `inertia`

Step 파형은 지령이 바뀐 직후 응답이 언제 시작되는지,
오버슈트와 정정시간이 어떻게 나타나는지를 보기 좋다.
따라서 지연과 과도응답 형상을 먼저 살펴보는 데 적합하다.

### Ramp 파형

사용 목적: 일정 속도 구간에서의 마찰 성분 확인  
주로 드러나는 특성: `viscous`, `coulomb`

Ramp 로그의 정상속도 구간에서는 속도와 토크의 관계를 이용해
점성 마찰과 쿨롱 마찰의 영향을 보기 쉽다.

사용하는 기본 모델은 아래와 같다.

```text
τ_friction = bq̇ + τ_c·sign(q̇)
```

- `b`
  점성 마찰 계수
- `τ_c`
  쿨롱 마찰 계수
- `q̇`
  회전 속도

### Multi-sine 파형

사용 목적: 여러 주파수에서의 동특성 확인  
주로 드러나는 특성: `kp`, `kd`, `inertia`

Multi-sine은 하나의 주파수만 보는 대신,
여러 단일 사인파 응답을 통해 주파수에 따른 추종 특성 변화를 확인하는 데 적합하다.

### S-Curve 파형

사용 목적: 피팅에 직접 사용하지 않은 응답에서 일반화 성능 확인  
주로 드러나는 특성: held-out 검증 성격의 응답

S-Curve는 학습용 로그와 별도로 두었을 때,
특정 파형에만 과도하게 맞춘 모델인지 아닌지를 확인하기 좋다.




---

### @ 학습용 로그와 검증용 로그의 구분

피팅에서는 학습에 사용하는 로그와 검증에 사용하는 로그를 구분하는 것이 좋다.

- Step, Ramp, Multi-sine  
  파라미터 추정에 직접 활용하는 학습용 로그
- S-Curve 같은 held-out 로그  
  피팅에 직접 사용하지 않고 일반화 성능을 확인하는 검증용 로그

피팅에 사용하지 않은 새로운 응답에도 비슷하게 맞는가를 확인하기 위함이다.


### @ 입력 파형 선택 기준

입력 파형을 선택할 때는,
실측 데이터가 많이 쌓이는 것보다 **해석 가능한 특성이 분리되어 드러나는가**를 우선 본다.

단일 모터 모델링 기준은 아래와 같다.

- 지연과 과도응답을 보고 싶으면 Step 파형을 사용한다.
- 일정 속도 구간의 마찰 특성을 보고 싶으면 Ramp 파형을 사용한다.
- 관성과 제어 게인의 주파수별 영향을 보고 싶으면 여러 주파수의 Sine 파형을 사용한다.
- 일반화 성능을 확인하고 싶으면 학습에 쓰지 않은 held-out 파형을 남겨 둔다.

고주파 응답은 추가 정보를 줄 수 있지만,
초기 피팅 단계에서는 저주파~중간 주파수 대역을 먼저 보는 편이 안정적이다.  
높은 주파수 구간에서는 샘플링 주기, 지연, 노이즈, 미모델링 동특성의 영향이 더 크게 섞일 수 있기 때문이다.
