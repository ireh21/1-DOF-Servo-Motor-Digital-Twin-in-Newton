# WMX3 Data Log 및 실측 데이터 취득

> **참고**
>
> 이 문서는 본 프로젝트에서 사용할 **WMX3 CoreMotion Data Log의 형식과 신호를 확인하고, 단일 모터 데모기의 실측 데이터를 Newton과 비교 가능한 형태로 취득하기 위한 기준**을 정리한다.
>
> 모터 정격 토크, 엔코더 분해능, 기어비, 실제 WMX3 로그의 신호 단위 등은
> 단일 모터 데모기의 하드웨어 및 드라이브 설정을 확인한 후 확정한다.


## 1. 데이터 취득 목적

본 프로젝트에서는 실제 단일 서보 모터의 응답과 Newton 기반 디지털 트윈의 응답을 비교하여 Actuator 및 물리 파라미터를 조정한다.

이를 위해 실제 장비에 동일한 Command Position을 입력하고,  
WMX3 Data Log를 이용하여 다음 신호를 취득한다.

- Command Position
- Feedback Position
- Feedback Velocity
- Feedback Torque

취득한 데이터는 단위 변환 및 시간축 정합을 거친 후 Newton의 입력 및 출력 신호와 비교한다.




## 2. WMX3 Data Log 형식

제공된 샘플 Data Log는 다음과 같은 컬럼으로 구성되어 있다.

```
CYCLE
CommandPos-0
FeedbackPos-0
FeedbackVelocity-0
FeedbackTrq-0
```
### 2.1 시간 관련 데이터
- `CYCLE` : 데이터가 취득된 제어 주기의 순번 (1ms로 설정)

### 2.2 제어 및 피드백 신호
- `CommandPos-0` : 0번 축에 전달된 Command Position  
  (Newton 시뮬레이션에 동일한 위치 지령을 입력하기 위한 기준 신호)
- `FeedbackPos-0` : 실제 모터의 Feedback Position  
  (Newton의 관절 위치와 비교)
- `FeedbackVelocity-0` : 실제 모터의 Feedback Velocity  
(Newton의 관절 속도와 비교)
- `FeedbackTrq-0` : 실제 드라이브에서 제공하는 Feedback Torque  
  (Newton의 토크 응답과 비교)





## 3. 단일 모터 데모기 구성

| 확인 항목       | 확인 내용                      | 현재 상태 |
|---|---|---|
| 모터 모델       | Panasonic `MSMF5AZL1S2` | 확인 |
| 정격 토크       | Torque 변환 기준             | `0.16 N·m` |
| 드라이브 모델   | Panasonic `MADLN05BE`       | 확인 |
| 전원            | 드라이브 입력 전원           | `AC 220 V` |
| 엔코더 분해능   | Position 단위 변환 기준      | `8,388,608 pulse/rev` |
| 기어비          | 모터측과 부하측 변환 비율     | `1:1` |
| 기계 구성       | 무부하 여부, 커플링 등        | TBD |
| 제어 축 번호    | WMX3에서 사용하는 Axis 번호   | TBD |
| 운전 모드       | CSP 사용 여부                | TBD |
| Position 단위   | count / user unit 등         | `1 U = 1 deg` |
| Velocity 단위   | count/s / rpm 등             | `deg/s` |
| Torque 단위     | ‰ / % / N·m 등               | `%` |
| 회전 방향       | 실제 장비와 Newton의 부호 규약 | TBD |





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

### 4.4 Motor torque limits

Panasonic `MSMF5AZL1S2`의 토크 제한은 서로 다른 시간 척도로 적용한다.

- 연속 토크 제한: `0.16 N·m` (장시간 열 한계)
- 순간 피크 토크 제한: `0.48 N·m` (즉시 출력 상한)

Newton 모델은 피크 제한을 매 제어 주기의 하드 클램프로 적용하고, 연속
제한은 지수 RMS 토크로 누적하여 적용한다. 열 시정수 `10 s`는 단순화한
근사값이며 실제 과부하 차단 시간을 재현하려면 드라이브의 과부하 보호
특성에 맞춰 보정해야 한다.

## 5. 데이터 취득 방법
WMX3 API의 `ClosedLoop` 기반 시험 기능으로 입력 파형을 생성하고, 축 응답 데이터를 로그로 저장해 취득하였다. step은 `StartClosedLoop()`의 `setpoint` 변경, ramp는 `opts.SetRampRate()`를 통한 setpoint 변화율 제어, sine은 `StartSineGenerator()`를 사용하였다.

