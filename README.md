# REI: Newton Single-Motor Digital Twin

WMX3에서 취득한 단일 서보 모터 로그를 바탕으로, Newton 엔진 안에서 비슷한 위치, 속도, 토크 응답을 재현하는 1축 디지털 트윈 레포다.  
핵심은 `Command Position -> Feedback Position / Velocity / Torque` 응답을 맞추도록 모델 파라미터를 피팅하는 것이다.

이 `README`는 상위 진입 문서다. 자세한 설명은 각 폴더의 `README`와 `docs/` 문서로 내려가서 보는 구조를 전제로 한다.

## 이 레포가 하는 일

- 무부하 단일 서보 모터 `1-DOF` 응답을 Newton 기반 모델로 근사
- WMX3 로그를 읽어 단위와 시간축을 정리하고 시뮬레이션과 비교
- `step`, `ramp`, `sine`, `S-curve` 로그를 이용해 파라미터를 피팅 + 검증
- 결과를 JSON 파라미터 파일과 비교용 노트북으로 남긴다.

## 목표와 범위

- 목표: 실측 로그 기반으로 단일 서보 모터의 평균적인 폐루프 응답을 Newton에서 재현
- 포함: 지령 지연, PID 응답, 토크 제한, 관성, 점성 마찰, 쿨롱 마찰, 토크 응답 지연
- 검증: 학습에 쓰지 않은 held-out `S-curve` 로그에서 일반화 성능 확인
- 제외: 다축 로봇 전체, 감속기/링크 결합, 외부 부하, 복잡한 드라이브 보호 로직의 완전 복제

`가장 작은 1축 수준의 로그 기반 캘리브레이션`에 초점을 둔다.

## 빠른 시작

먼저 [Newton 환경 구축 가이드](docs/guideline/00_newton_env.md)를 1회 따라간다. 현재 레포 실행에는 Newton/Warp 로컬 환경이면 충분하고, 향후 확장자를 위해 GPU + Isaac Sim 경로 메모도 같은 문서에 함께 정리돼 있다.

### 1. 기본 시뮬레이터 실행

Newton/Warp가 설치된 Python 환경에서 프로젝트 루트 기준으로 실행한다.

```bash
PYTHONPATH=code python3 code/single_motor_twin.py --profile scurve --viewer
```

### 2. 노트북 열기

```bash
jupyter lab notebooks/
```

피팅 노트북은 실측 WMX 로그 경로를 직접 확인하거나 수정해야 한다. 현재 예시 노트북은 Windows WSL 경로를 기본값으로 두고 있다.

## 추천 읽기 순서

1. [`docs/guideline/00_newton_env.md`](docs/guideline/00_newton_env.md)  
   Newton/Warp 실행 환경을 먼저 맞춘다.
2. [`docs/guideline/01_project_overview.md`](docs/guideline/01_project_overview.md)  
   프로젝트 목적, 시스템 경계, 전체 제어 흐름 확인
3. [`docs/guideline/02_digital_twin.md`](docs/guideline/02_digital_twin.md)  
   디지털 트윈 작업 순서와 피팅 개요 확인
4. [`notebooks/README.md`](notebooks/README.md)  
   어떤 노트북을 어떤 순서로 봐야 하는지 확인
5. [`code/README.md`](code/README.md)  
   재사용 코드와 주요 함수 확인
6. [`docs/result/01_fitting_strategy_and_results.md`](docs/result/01_fitting_strategy_and_results.md)  
   현재 파라미터 후보와 비교 결과 확인
7. [`docs/result/02_limitations_and_future_plan.md`](docs/result/02_limitations_and_future_plan.md)  
    한계점, 개선점, 향후 방향성

## 레포 구조

- [`code/`](code/)  
  재사용 Python 모듈과 로그 처리 유틸리티
- [`docs/`](docs/)  
  프로젝트 개요, 배경 설명, 결과 해석 문서
- [`notebooks/`](notebooks/)  
  실험, 피팅, 비교, 시각화용 노트북
- [`images/`](images/)  
  발표나 문서용 그림

각 폴더의 상세 설명은 아래 `README`를 우선 본다.

- [`code/README.md`](code/README.md)
- [`docs/README.md`](docs/README.md)
- [`notebooks/README.md`](notebooks/README.md)

## 주요 파일

- [`code/single_motor_twin.py`](code/single_motor_twin.py)  
  단일 모터 Newton 모델과 `simulate_motor()` 구현
- [`code/wmx_log_utils.py`](code/wmx_log_utils.py)  
  WMX TXT/CSV 로그 로드와 단위 변환
- [`code/metrics.py`](code/metrics.py)  
  위치, 속도, 토크, step/sine/ramp 비교 지표
- [`notebooks/04_1_parameter_fitting.ipynb`](notebooks/04_1_parameter_fitting.ipynb)  
  원본 `1 ms` 해상도 기준 전체 피팅
- [`notebooks/04_2_parameter_fitting_dec.ipynb`](notebooks/04_2_parameter_fitting_dec.ipynb)  
  adaptive decimation 기반 전체 피팅
- [`docs/result/02_limitations_and_future_plan.md`](docs/result/02_limitations_and_future_plan.md)   
  해당 프로젝트의 개선점, 향후 확장 방향성

## 현재 산출물

레포 루트에는 현재 피팅 결과가 JSON으로 남아 있다.

- [`fitted_motor_params.json`](fitted_motor_params.json)  
  `04_1` 결과
- [`fitted_motor_params_dec.json`](fitted_motor_params_dec.json)  
  `04_2` 결과
- [`fitted_motor_params_init.json`](fitted_motor_params_init.json)  
  `04_3` 결과
- [`fitted_motor_params_multi_sine_checkpoint.json`](fitted_motor_params_multi_sine_checkpoint.json)  
  multi-sine 중간 체크포인트(04_1 파일만 해당)

후보별 해석은 [`docs/result/01_fitting_strategy_and_results.md`](docs/result/01_fitting_strategy_and_results.md)에서 본다.

## 현재 모델의 한계

- 평균적인 응답 형상은 맞추지만, `reversal` 근처의 강한 비선형은 아직 약하다.
- 고주파 구간과 세부 토크 파형은 현재 저차 모델이 직접 설명하지 못하는 부분이 남아 있다.
- 현재 구현은 Newton 기본 actuator만으로 끝내지 않고, 일부 제어 및 제한 로직을 사용자 코드에서 직접 계산한다.


## 더 자세한 문서

- 프로젝트 개요: [`docs/guideline/01_project_overview.md`](docs/guideline/01_project_overview.md)
- 디지털 트윈 절차: [`docs/guideline/02_digital_twin.md`](docs/guideline/02_digital_twin.md)
- 결과와 후보 비교: [`docs/result/01_fitting_strategy_and_results.md`](docs/result/01_fitting_strategy_and_results.md)
- 한계와 향후 방향: [`docs/result/02_limitations_and_future_plan.md`](docs/result/02_limitations_and_future_plan.md)

## 환경 메모

- 레포 안에는 패키지 관리 파일(`pyproject.toml`, `requirements.txt`)이 아직 없다.
- 실제 실행에는 최소한 `numpy`가 필요하고, Newton 시뮬레이션에는 `newton`, `warp` 환경이 준비돼 있어야 한다.
- 노트북 실행에는 `jupyterlab` 환경이 필요하다.
- 현재 레포 실행은 CPU 폴백 환경으로도 가능하지만, 향후 Isaac Sim 계열 확장은 GPU 환경을 사실상 전제로 본다.

환경 구축은 먼저 [`docs/guideline/00_newton_env.md`](docs/guideline/00_newton_env.md)를 보고, 그 다음 설명은 [`docs/README.md`](docs/README.md)부터 내려가서 보는 편이 빠르다.
