# EtherCAT·CoE·CiA 402·CSP 구조
> **참고**
>
> 이 문서는 EtherCAT과 CiA 402의 전체 사양을 일반적으로 설명하는 문서가 아니라,
> 본 프로젝트에서 사용하는 **WMX3 EtherCAT 마스터와 단일 서보 드라이브의 CSP 운전 구조**를
> 이해하는 데 필요한 개념을 중심으로 정리한다.
>
> 따라서 마스터와 드라이브의 역할 경계, Command Position 전달 과정,
> Position·Velocity·Torque 피드백 및 WMX3 Data Log와 관련된 내용을 중점적으로 다룬다.

## 1. 전체 관계

본 프로젝트에서 WMX3와 서보 드라이브 사이의 통신 및 제어 구조는
다음과 같이 구분할 수 있다.

```text
WMX3
- 이동 궤적 생성
- EtherCAT 마스터
        ↓
EtherCAT
- 주기적 지령 및 피드백 전달
- 장치 간 시간 동기화
        ↓
CoE
- CANopen의 객체 사전과 장치 프로파일 사용
        ↓
CiA 402
- 서보 드라이브의 상태와 운전 모드 정의
        ↓
CSP
- 주기적으로 목표 위치를 전달하는 위치 제어 모드
        ↓
서보 드라이브
- 내부 위치·속도·전류 제어
        ↓
서보 모터
```

각 기술의 역할은 다음과 같다.

| 구분 | 역할 |
|---|---|
| EtherCAT | WMX3와 서보 드라이브 사이의 실시간 통신 |
| CoE | EtherCAT에서 CANopen의 객체 사전과 장치 제어 방식을 사용 |
| CiA 402 | 서보 드라이브의 상태, 제어 명령 및 운전 모드를 표준화 |
| CSP | 목표 위치를 통신 주기마다 전달하는 위치 제어 모드 |

## 2. EtherCAT

EtherCAT은 산업용 장치 사이에서 지령과 피드백 데이터를
짧고 일정한 주기로 전달하기 위한 실시간 EtherNET 통신 방식이다.

본 프로젝트에서는 WMX3가 EtherCAT 마스터로 동작하고,
서보 드라이브가 EtherCAT 슬레이브로 동작한다.

```text
WMX3 EtherCAT Master
        ↓
Command Position 전송
        ↓
서보 드라이브
        ↓
Position·Velocity·Torque 피드백
        ↓
WMX3 EtherCAT Master
```


### 2.1 마스터와 드라이브의 역할

| 구성 요소 | 역할 |
|---|---|
| WMX3 마스터 | 이동 궤적 생성, 주기적 지령 전송, 피드백 수신 |
| EtherCAT | 지령과 피드백을 정해진 통신 주기에 맞추어 전달 |
| 서보 드라이브 | 지령을 실제 모터 제어에 사용하고 피드백 생성 |
| 서보 모터 | 드라이브가 발생시킨 토크에 따라 회전 |

EtherCAT은 데이터를 전달하는 통신 계층이며,
모터의 위치 제어 연산을 직접 수행하는 제어기는 아니다.

실제 위치·속도·전류 제어 루프는 서보 드라이브 내부에서 수행된다.

### 2.2 주기적 프로세스 데이터

모터 제어에 필요한 지령과 피드백은
EtherCAT의 주기적 프로세스 데이터로 교환된다.

```text
한 통신 주기

WMX3
→ 목표 위치 및 제어 명령 전송

서보 드라이브
→ 실제 위치·속도·토크 및 상태 전송
```

예를 들어 통신 주기가 1 ms이면,
WMX3와 드라이브 사이의 데이터 교환이 1 ms마다 반복된다.

## 3. CoE와 객체 사전

CoE는 `CANopen over EtherCAT`의 약자로,
CANopen에서 정의한 객체 사전과 장치 제어 구조를
EtherCAT 통신에서 사용할 수 있게 하는 방식이다.

CoE를 사용한다고 해서 실제 통신선이 CAN으로 바뀌는 것은 아니다.

```text
물리적 데이터 전송
→ EtherCAT

장치 파라미터와 제어 데이터의 구성 방식
→ CANopen 객체 사전 및 CiA 402
```

객체 사전은 드라이브에서 사용하는 지령, 상태 및 설정값을
인덱스와 서브인덱스로 구분하여 정리한 데이터 목록이다.

객체 사전에는 다음과 같은 정보가 포함될 수 있다.

- 드라이브 제어 명령
- 드라이브 현재 상태
- 운전 모드
- 목표 위치
- 실제 위치
- 실제 속도
- 실제 토크
- 최대 속도와 토크
- 제어 게인과 모터 설정값

정확한 지원 항목과 데이터 형식은
서보 드라이브 매뉴얼과 ESI 파일을 기준으로 확인한다.

### 3.1 PDO와 SDO

CoE에서 데이터를 교환하는 방식은 크게 PDO와 SDO로 구분할 수 있다.

| 구분 | 역할 | 사용 예 |
|---|---|---|
| PDO | 통신 주기마다 빠르게 교환하는 데이터 | 목표 위치, 실제 위치, 실제 속도, 실제 토크 |
| SDO | 설정 및 진단을 위해 필요할 때 접근하는 데이터 | 모터 파라미터, 제한값, 운전 모드 설정 |
  
SDO는 유저가 호출해야 사용이 되는 전송 방식이다.  
 (PDO처럼 매 순간 데이터를 교환하는 방식이 아닌 Master가 원하는 상황에 읽고 쓸 수 있는 프로토콜을 지칭한다. )

PDO는 실시간 모터 제어에 사용하고,  
SDO는 주로 초기 설정과 파라미터 확인에 사용한다.

### 3.2 RxPDO와 TxPDO

PDO는 Receive, Transfer로 나뉜다. 전자는 Slave가 받는 데이터. 후자는 Slave가 주는 데이터이다.
RxPDO와 TxPDO의 방향은 서보 드라이브를 기준으로 구분한다.

| 구분 | 방향 | 주요 데이터 |
|---|---|---|
| RxPDO | WMX3(Master) → 서보 드라이브(Slave) | Controlword, 운전 모드, Target Position |
| TxPDO | 서보 드라이브(Slave) → WMX3(Master) | Statusword, Actual Position, Actual Velocity, Actual Torque |


## 4. CiA 402

CiA 402는 서보 드라이브, 인버터 및 스테퍼 드라이브의
제어 방식과 상태를 표준화한 장치 프로파일이다.

CiA 402는 다음 내용을 정의한다.

- 드라이브 상태
- 상태 전환 명령
- 현재 상태 확인 방법
- 위치·속도·토크 운전 모드
- 목표값과 실제값의 데이터 구조

### 4.1 드라이브 상태 전환

드라이브는 전원이 켜졌다고 바로 모터를 구동할 수 있는 것이 아니다.

WMX3가 Controlword를 통해 상태 전환 명령을 보내고,
드라이브는 Statusword를 통해 현재 상태를 응답한다.

```text
Switch On Disabled
        ↓
Ready to Switch On
        ↓
Switched On
        ↓
Operation Enabled
```

| 상태 | 의미 |
|---|---|
| Switch On Disabled | 드라이브 전력 출력이 비활성화된 상태 |
| Ready to Switch On | 구동 준비 단계 |
| Switched On | 전력부가 켜졌지만 아직 운전 명령은 비활성화된 상태 |
| Operation Enabled | 목표 위치 등 운전 지령을 실제로 수행할 수 있는 상태 |
| Quick Stop Active | 빠른 정지 동작을 수행하는 상태 |
| Fault | 오류가 발생하여 정상 운전이 불가능한 상태 |

드라이브를 CSP 모드로 설정했더라도
CiA 402 상태가 `Operation Enabled`에 도달하지 않으면
모터는 정상적으로 지령을 수행하지 않는다.


### 4.2 EtherCAT 상태와 CiA 402 상태의 차이

서보 드라이브에는 다음 두 종류의 상태가 존재한다.

| 구분 | 나타내는 것 | 정상 운전 조건 |
|---|---|---|
| EtherCAT 상태 | WMX3와 드라이브 사이의 통신 준비 상태 | `OP` |
| CiA 402 상태 | 드라이브가 모터를 구동할 수 있는 상태 | `Operation Enabled` |

#### 4.2.1 EtherCAT 통신 상태

서보 드라이브의 EtherCAT 통신 상태는 정상 기동 시 일반적으로
다음 순서로 전환된다.

```text
INIT
→ PRE-OP
→ SAFE-OP
→ OP
```

| 상태 | 의미 |
|---|---|
| `INIT` | EtherCAT 통신 기능 초기화 |
| `PRE-OP` | 장치 설정과 Mailbox 통신 가능 |
| `SAFE-OP` | 피드백 데이터는 교환할 수 있지만 출력 지령은 제한됨 |
| `OP` | 주기적인 지령 및 피드백 데이터 교환 가능 |

각 상태 전환은 자동으로 이루어지는 것이 아니라,
WMX3 마스터의 전환 요청과 서보 드라이브의 설정·통신 조건 확인을 거쳐 수행된다.

Boot strap 단계가 추가적으로 존재하는데, 이는 SDO 호출 할 때, 펌웨어 업데이트 시의 상태이다. 

#### 4.2.2 CiA 402 드라이브 상태

CiA 402 상태는 드라이브가 모터를 실제로 구동할 수 있는지를 나타낸다.

```text
Switch On Disabled
→ Ready to Switch On
→ Switched On
→ Operation Enabled
```

`Operation Enabled` 상태에 도달해야
드라이브가 목표 위치와 같은 운전 지령을 실제 모터에 적용할 수 있다.

#### 4.2.3 두 상태의 관계

EtherCAT이 `OP` 상태이더라도
CiA 402가 `Operation Enabled` 상태가 아니면 모터는 구동되지 않는다.

```text
EtherCAT OP + CiA 402 Operation Enabled + 올바른 운전 모드와 목표값
        ↓
모터 운전 가능
```

즉, EtherCAT 상태는 **통신 가능 여부**를 나타내고,
CiA 402 상태는 **모터 구동 가능 여부**를 나타낸다.

## 5. CSP

CSP는 `Cyclic Synchronous Position`의 약자로,
마스터가 목표 위치를 주기적으로 서보 드라이브에 전달하는 운전 모드이다.

본 프로젝트에서는 WMX3가 이동 궤적을 생성하고,
각 통신 주기마다 새로운 Command Position을 드라이브에 전달한다.

```text
WMX3
- 이동 프로파일 계산
- 현재 통신 주기의 목표 위치 생성
        ↓
EtherCAT RxPDO
- Target Position 전달
        ↓
서보 드라이브
- 내부 위치·속도·전류 제어
        ↓
서보 모터 회전
        ↓
EtherCAT TxPDO
- Actual Position
- Actual Velocity
- Actual Torque
        ↓
WMX3
```

CSP에서 WMX3는 매 주기의 목표 위치를 생성하지만,
목표 위치와 실제 위치의 오차를 줄이기 위한
빠른 내부 제어 루프는 서보 드라이브에서 수행한다.

따라서 CSP는 다음과 같이 이해할 수 있다.

```text
WMX3
→ 어디까지 움직일지 주기적으로 지정

서보 드라이브
→ 해당 위치를 실제로 추종하도록 모터 제어
```

## 6. Distributed Clocks

EtherCAT의 Distributed Clocks는
각 슬레이브 장치의 로컬 시계를 공통된 시간 기준에 맞추는 기능이다.

DC 기능을 지원하는 장치 중 하나가 기준 시계 역할을 하고,
다른 장치의 시계는 기준 시계와의 오차가 작아지도록 보정된다.

```text
기준 시계
        ↓
각 슬레이브 시계의 시간 차이와 전달 지연 계산
        ↓
슬레이브 로컬 시계 보정
        ↓
동일한 시간 기준으로 입출력 처리
```

단일 모터에서는 여러 축의 동기화 효과가 크게 드러나지 않을 수 있지만,
다축 시스템에서는 각 드라이브가 같은 시점에 지령을 적용하도록 하는 데 중요하다.

## 7. 프로젝트 관련 CiA 402 신호

| 방향 | WMX3 신호 | CiA 402 객체 |
|---|---|---|
| WMX3 → 드라이브 | Command Position | Target Position `0x607A` |
| 드라이브 → WMX3 | Feedback Position | `0x6064` |
| 드라이브 → WMX3 | Feedback Velocity | `0x606C` |
| 드라이브 → WMX3 | Feedback Torque | `0x6077` |

이 신호들은 WMX3 Data Log로 저장한 뒤
Newton 트윈의 위치·속도·Actuator 토크와 비교한다.

단, Feedback Torque의 단위와 기준은 드라이브마다 다를 수 있으므로
정격 토크 대비 비율인지, 실제 토크 단위인지,
모터축과 부하축 중 어느 기준인지 확인해야 한다.


## 8. 핵심 정리

```text
EtherCAT
→ WMX3와 드라이브 사이에서 데이터를 전달

CoE
→ EtherCAT에서 CANopen 객체 사전과 장치 프로파일 사용

CiA 402
→ 드라이브의 상태와 운전 모드를 정의

CSP
→ WMX3가 목표 위치를 통신 주기마다 전달

서보 드라이브
→ 내부 제어 루프로 목표 위치를 실제로 추종
```

본 프로젝트에서 EtherCAT은 통신을 담당하고,
WMX3는 이동 궤적과 Command Position을 생성한다.

CiA 402는 서보 드라이브의 상태와 운전 방식을 정의하며,
CSP 모드의 실제 위치 추종 제어는 서보 드라이브 내부에서 수행된다.