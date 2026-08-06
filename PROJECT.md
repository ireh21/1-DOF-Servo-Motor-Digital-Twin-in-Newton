# Newton Single-Motor Digital Twin

## 목표

WMX3에서 취득한 서보 모터의 입력·출력 데이터를 이용해
Newton 기반 단일 모터 디지털 트윈을 구성한다.

### 추가 목표
- Newton 학습 및 WSL 로컬 환경 실행 검증
- WMX3 실측 기반 단일 모터 디지털 트윈 구현 및 캘리브레이션
- 코드와 가이드 문서화 

## 문서

- [전체 제어 구조 및 개념](docs/01_project_overview.md)
- [Newton 및 Actuator](docs/02_newton_actuator.md)
- [EtherCAT, CiA402, CSP](docs/03_ethercat_cia402_csp.md)
- [환경 및 Baseline 실행](docs/04_environment_baseline.md)
- [WMX3 Data Log](docs/05_wmx3_data_log.md)





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