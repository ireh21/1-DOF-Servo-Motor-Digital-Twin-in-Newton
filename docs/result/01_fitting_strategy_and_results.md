# 단일 모터 피팅 결과 요약

이 문서는 단일 모터 디지털 트윈 피팅에서 사용한 로그, 노트북별 결과, 저장된 파라미터 후보, 기록된 loss를 결과 중심으로 정리한 문서이다.  
해석과 한계, 향후 계획은 `02_limitations_and_future_plan.md`에서 따로 다룬다.

## 1. 사용한 로그

### 학습 로그

- `step_v.csv`
- `ramp_v.csv`
- `sine_0.1Hz.csv`
- `sine_0.2Hz.csv`
- `sine_0.5Hz.csv`
- `sine_1Hz.csv`
- `sine_2Hz.csv`

### held-out 검증 로그

- `SCurve.csv`
- `SCurve2.csv`

현재 저장소에는 위 로그 구성을 바탕으로 한 결과 파일 3개가 남아 있다.

## 2. 노트북별 결과 파일

| 노트북 | 역할 | 결과 파일 |
|---|---|---|
| `04_1_parameter_fitting.ipynb` | 원본 `1 ms` 해상도 기반 전체 응답 피팅 | `fitted_motor_params.json` |
| `04_2_parameter_fitting_dec.ipynb` | adaptive decimation과 delay 재보정을 포함한 refinement 피팅 | `fitted_motor_params_dec.json` |
| `04_3_parameter_fitting_init.ipynb` | 단순 decimation 기반 초기 피팅 | `fitted_motor_params_init.json` |

## 3. 저장된 파라미터 후보

| 후보 | 결과 파일 | 설명 |
|---|---|---|
| `04_1` | `fitted_motor_params.json` | 원본 `1 ms` 해상도 기반 전체 refinement 결과 |
| `04_2` | `fitted_motor_params_dec.json` | adaptive decimation 기반 refinement 결과 |
| `04_3` | `fitted_motor_params_init.json` | 초기 decimation 기반 피팅 결과 |

### `04_1`

| parameter | value |
|---|---:|
| `kp` | 1.7834420459 |
| `ki` | 0.0 |
| `kd` | 0.0348927510 |
| `inertia` | 0.0000080923 |
| `viscous` | 0.0001652946 |
| `coulomb` | 0.0039704990 |
| `delay_steps` | 6 |
| `torque_response_time_constant` | 0.0024624684 |

### `04_2`

| parameter | value |
|---|---:|
| `kp` | 0.7634725769 |
| `ki` | 0.0 |
| `kd` | 0.0259528304 |
| `inertia` | 0.0000871450 |
| `viscous` | 0.0000508080 |
| `coulomb` | 0.0039315855 |
| `delay_steps` | 0 |
| `torque_response_time_constant` | 0.0060912680 |

### `04_3`

| parameter | value |
|---|---:|
| `kp` | 0.2330336769 |
| `ki` | 0.0 |
| `kd` | 0.0077243957 |
| `inertia` | 0.0002240550 |
| `viscous` | 0.0000100001 |
| `coulomb` | 0.0034327297 |
| `delay_steps` | 0 |
| `torque_response_time_constant` | 0.0 |

## 4. 저장된 normalized loss 비교

아래 값은 위치, 속도, 토크를 서로 다른 scale로 정규화한 평균제곱오차이다.  
따라서 절대 오차의 크기나 그래프 인상과 1:1로 대응하는 값은 아니다.

### 학습 로그 기준

| 후보 | position | velocity | torque | total |
|---|---:|---:|---:|---:|
| `04_1` | 0.241997 | 4.627083 | 1.288011 | 1.913105 |
| `04_2` | 0.423258 | 4.905698 | 4.920562 | 3.186256 |
| `04_3` | 0.550906 | 8.008795 | 0.003474 | 2.677200 |

### held-out 검증 로그 기준

| 후보 | position | velocity | torque | total |
|---|---:|---:|---:|---:|
| `04_1` | 0.065575 | 1.636338 | 0.170089 | 0.554198 |
| `04_2` | 1.593155 | 1.633148 | 0.093132 | 1.167313 |
| `04_3` | 1.690070 | 1.629089 | 0.000079 | 1.179369 |

## 5. 대표 비교 지표 참고

`05_fitting_comparison.ipynb`에서 정리한 대표 지표는 아래와 같다.

| 후보 | held-out position NRMSE | held-out velocity NRMSE | step settling abs error [s] | ramp torque bias abs [N·m] | sine phase abs error [deg] |
|---|---:|---:|---:|---:|---:|
| `04_1` | 0.000907 | 0.105966 | 0.052 | 0.000116 | 1.946675 |
| `04_2` | 0.004468 | 0.105819 | 0.052 | 0.000025 | 1.455392 |
| `04_3` | 0.004602 | 0.105689 | 0.052 | 0.000132 | 2.107744 |

## 6. 수치만 기준으로 보면

- 저장된 normalized total loss 기준으로는 `04_1`이 학습 로그와 held-out 검증 로그에서 모두 가장 낮다.
- held-out torque loss는 `04_3`가 가장 낮고, 그 다음이 `04_2`다.
- held-out position NRMSE는 `04_1`이 가장 낮다.
- ramp torque bias와 sine phase 오차는 `04_2`가 가장 낮다.
- `delay_steps`는 `04_1`이 `6`, `04_2`와 `04_3`가 `0`으로 저장되어 있다.
