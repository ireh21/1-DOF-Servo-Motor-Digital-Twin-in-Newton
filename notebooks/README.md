# Notebooks Guide

이 폴더는 실험용 노트북을 모아 두는 곳이다.
공통 모듈은 `code/`에 두고, 노트북은 실험 순서와 비교, 시각화, 해석을 담당한다.

## 권장 읽기 순서

1. `01_newton_single_motor_model.ipynb`
2. `04_2_parameter_fitting_dec.ipynb`
3. `05_fitting_comparison.ipynb`

## 파일별 역할

### `01_newton_single_motor_model.ipynb`

- 단일 모터 Newton 모델의 기본 구조 확인용
- 파라미터와 출력 신호의 관계를 처음 살펴볼 때 사용

### `02_newton_command_profile_test.ipynb`

- command profile 생성과 입력 파형 점검용
- step, sine, ramp, s-curve 같은 시험 입력의 모양을 확인할 때 사용


### `04_1_parameter_fitting.ipynb`

- 원본 `1 ms` 해상도를 유지한 전체 피팅 실험
- `fitted_motor_params.json` 생성

### `04_2_parameter_fitting_dec.ipynb`

- adaptive decimation을 포함한 전체 피팅 실험
- `fitted_motor_params_dec.json` 생성

### `04_3_parameter_fitting_init.ipynb`

- 단순 decimation 기반 피팅 실험
- `fitted_motor_params_init.json` 생성

### `05_fitting_comparison.ipynb`

- 여러 파라미터 세트의 결과를 공통 지표와 그래프로 비교
- 결과 문서에 넣을 표와 확대 그래프를 고를 때 가장 먼저 보는 노트북

### `dobot_cr3a_newton_loader.ipynb`

- 단일 모터 범위를 넘어 CR3A 쪽으로 확장을 시도한 실험 노트북
- 현재 핵심 fitting 흐름과는 별도의 확장 실험 성격 
