# Newton Single-Motor Digital Twin

## 목표

WMX3에서 취득한 서보 모터의 입력·출력 데이터를 이용해
Newton 기반 단일 모터 디지털 트윈을 구성한다.

### 추가 목표
- Newton 학습 및 WSL 로컬 환경 실행 검증
- WMX3 실측 기반 단일 모터 디지털 트윈 구현 및 캘리브레이션
- 코드와 가이드 문서화 

## 문서


### docs/
- [전체 제어 구조 및 개념](docs/01_project_overview.md)
- [EtherCAT, CiA402, CSP](docs/02_ethercat_cia402_csp.md)
- [Newton 및 Actuator](docs/03_newton_actuator.md)
- [환경 및 Baseline 실행](docs/04_newton_ikcable_jujeori.md)
- [WMX3 Data Log 및 WMX](docs/05_wmx3_data_log.md)



### code/
인턴십 프로젝트 수행을 위해 제공받은 단일 모터 디지털 트윈 및 캘리브레이션 시작용 코드이다.

- [합성 WMX3 로그 생성](code/generate_sample_log.py)  
  실제 WMX3 실측 데이터를 취득하기 전에 피팅 과정을 시험할 수 있도록 가상의 WMX3 Data Log를 생성하는 코드이다.  
  Command Position, Feedback Position, Feedback Velocity, Feedback Torque 형식의 데이터를 생성한다.

- [단일 모터 디지털 트윈](code/single_motor_twin.py)  
  WMX3의 Command Position을 입력받아 단일 서보 모터의 Feedback Position, Velocity, Torque를 모사하는 Newton 기반 1-DOF 디지털 트윈 코드이다.  
  PID 제어, 지령 지연, 토크 제한, 관성 및 마찰 등의 파라미터와 Step/Sine/Chirp/S-curve Motion Profile, Viser Viewer가 포함되어 있다.

## 단일 모터 실행

Newton/Warp가 설치된 가상환경에서 프로젝트 루트를 기준으로 실행한다.

```bash
PYTHONPATH=code python code/single_motor_twin.py --profile scurve --viewer
```

노트북에서 WMX 로그와 바로 연결할 때는 다음과 같이 사용한다. 로그의 위치,
속도, 토크 단위가 이미 rad, rad/s, N·m이면 scale은 모두 `1.0`을 사용한다.

```python
from single_motor_twin import MotorParams, simulate_wmx_log

simulation, measurement = simulate_wmx_log(
    "path/to/wmx_log.txt",
    MotorParams(
        kp=8.0,
        ki=0.0,
        kd=0.6,
        inertia=0.02,
        viscous=0.01,
        coulomb=0.0,
        continuous_torque_limit=0.16,
        peak_torque_limit=0.48,
        delay_steps=1,
    ),
    time_unit="ms",
    position_scale=1.0,
    velocity_scale=1.0,
    torque_scale=1.0,
    use_viewer=True,
)

simulation["viewer"].show_notebook(width="100%", height=600)
```



## $$

NVIDIA에서 제공하는 `franka_cube` baseline 노트북을 실행하고 분석하여 Newton/Warp의 기본 구조와 시뮬레이션 실행 흐름을 이해한다. 기존 교육용 서버 환경에서 제공되는 Newton 노트북을 WSL2 로컬 환경으로 옮겨 실행하고, 별도의 NVIDIA GPU 없이 노트북 CPU만으로 다음 항목이 정상적으로 동작하는지 확인한다.


Newton을 처음 접하는 사용자도 동일한 환경을 구성하고 baseline을 실행할 수 있도록 다음 내용을 정리한다. 
- WSL2 기반 로컬 개발 환경 구성 
- Python 가상환경 생성 및 패키지 설치 
- Newton/Warp CPU 실행 방법 
- JupyterLab 실행 및 노트북 접근 방법 
- `franka_cube` baseline 실행 절차 
- ModelBuilder → Model → State/Control → Solver 실행 흐름 
- Actuator 및 물리 파라미터 구조 
- 자주 발생하는 오류와 해결 방법
