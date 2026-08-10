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
TIME
SYSTEM_TIME
CMDPOS0
FBKPOS0
FBKVEL0
FBKTRQ0
```
### 2.1 시간 관련 데이터
- `CYCLE` : 데이터가 취득된 제어 주기의 순번
- `TIME` : 로그 시작 이후의 경과 시간을 나타내는 값
- `SYSTEM_TIME` : 시스템 기준 시간 정보이다.

### 2.2 제어 및 피드백 신호
- `CMDPOS0` : 0번 축에 전달된 Command Position  
  (Newton 시뮬레이션에 동일한 위치 지령을 입력하기 위한 기준 신호)
- `FBKPOS0` : 실제 모터의 Feedback Position  
  (Newton의 관절 위치와 비교)
- `FBKVEL0` : 실제 모터의 Feedback Velocity  
  (Newton의 관절 속도와 비교)
- `FBKTRQ0` : 실제 모터 또는 드라이브에서 제공하는 Feedback Torque  
  (Newton의 토크 응답과 비교)





## 3. 단일 모터 데모기 구성 파악 (추후 완성)
여기서 말하는 단일 모터 데모기는
실제 WMX3에 연결되어 실험에 사용할 하나의 서보 모터 시험 장치를 의미한다.

WMX3 자체의 사양과 별개로 다음 항목을 실제 데모기에서 확인해야 한다.

| 확인 항목       | 확인 내용                      | 현재 상태 |
| ----------- | -------------------------- | ----- |
| 모터 모델       | 제조사 및 모델명                  | TBD   |
| 정격 토크       | Torque 변환에 필요한 정격 토크 [N·m] | TBD   |
| 드라이브 모델     | EtherCAT 서보 드라이브 모델        | TBD   |
| 엔코더 분해능     | Position 단위 변환에 필요한 분해능    | TBD   |
| 기어비         | 모터측과 부하측 변환 비율             | TBD   |
| 기계 구성       | 무부하 여부, 커플링 등              | TBD   |
| 제어 축 번호     | WMX3에서 사용하는 Axis 번호        | TBD   |
| 운전 모드       | CSP 사용 여부                  | TBD   |
| Position 단위 | count / user unit 등        | TBD   |
| Velocity 단위 | count/s / rpm 등            | TBD   |
| Torque 단위   | ‰ / % / N·m 등              | TBD   |
| 회전 방향       | 실제 장비와 Newton의 부호 규약       | TBD   |





## 4. 단위 정합
WMX/EtherCAT의 신호 단위와 Newton에서 사용하는 SI 단위가 다를 수 있으므로,
피팅 전에 각 신호의 변환 기준을 확정해야 한다.

WMX3 축을 rad 기준의 User Unit으로 설정하여 Newton과 맞춘다는 가정하에 작성한다.
추가로, 단일 모터는 감속기 없는 23-bit absolute encoder 사용한다고 가정한다.

- Encoder Resolution: 8,388,608 pulse/rev
- Reduction Gear: 없음 (1:1)
- Position Control Resolution: 1 U = 1 μrad = 0.000001 rad

### 4.1 Position
Master Gear Ratio의 분자는 1회전 펄스 수, 즉 [모터 엔코더 분해능 x 감속비] 인데, 감속기는 없기 때문에 모터 엔코터 분해능은 **8388608 pulse/rev**이다. 여기서 rev는 1회전이다.   
모터가 1회전을 하기위해 8388608의 pulse가 필요한 것이다.  

Master Gear Ratio의 분모는 [1회전 이동량 / 제어 사양] 이다.  
1회전 이동량 = 2π rad/rev
제어 사양 = 1 U = 1 μrad = 0.000001 rad  
분모 = 6,283,185 U/rev

따라서 WMX의 숫자는 이렇게 해석된다
```
WMX Position = 1        → 0.000001 rad
WMX Position = 1000     → 0.001 rad
WMX Position = 1,000,000 → 1 rad
WMX Position ≈ 6,283,185 → 2π rad = 1회전
```
```
Newton Position [rad] = WMX Position [U] × 0.000001
```
만약 1U = 1rad 라면 이때는 동일하다. 

### 4.2 Velocity
Velocity는 Position의 시간에 따른 변화량이므로,
Position에서 설정한 User Unit의 변환 비율을 동일하게 사용한다.
```
Newton Velocity [rad/s] = WMX Velocity [U/s] × 0.000001
```



### 4.3 Torque (추후 작성)





## 5. 