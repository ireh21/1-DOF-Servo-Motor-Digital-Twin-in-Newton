# Code Guide

이 폴더는 단일 모터 Newton 디지털 트윈 프로젝트에서 재사용하는 Python 모듈과
실험 보조 파일을 두는 곳이다.

## 파일 목록

- [`single_motor_twin.py`](/home/ireh21/rei/code/single_motor_twin.py)  
  단일 무부하 서보 모터의 Newton 기반 1-DOF 디지털 트윈 모델과 시뮬레이션 함수
- [`wmx_log_utils.py`](/home/ireh21/rei/code/wmx_log_utils.py)  
  WMX 로그 로드, CSV/TXT 헤더 처리, 시간축 처리, 단위 변환 유틸리티
- [`metrics.py`](/home/ireh21/rei/code/metrics.py)  
  위치, 속도, 토크, step/sine/ramp 응답 비교용 평가 지표 함수
- [`result_summary.py`](/home/ireh21/rei/code/result_summary.py)  
  저장된 결과 JSON을 다시 읽어 validation/step/ramp/sine 요약 지표를 재계산하는 헬퍼
- [`generate_sample_log.py`](/home/ireh21/rei/code/generate_sample_log.py)  
  실측 로그 전 파이프라인 점검용 합성 WMX 로그 생성 스크립트
- [`wmx_waveform_generation_sources.txt`](/home/ireh21/rei/code/wmx_waveform_generation_sources.txt)  
  step/ramp/sine/S-curve 입력 파형 원문 코드 모음 

## 주요 모듈

### [`single_motor_twin.py`](/home/ireh21/rei/code/single_motor_twin.py)

- `MotorParams`  
  제어기, 토크 제한, 열 시정수, 관성, 마찰, 지연 파라미터 묶음
- `build_motor_model()`  
  Newton 1-DOF revolute joint 모델 생성
- `simulate_motor()`  
  command position 배열을 넣어 위치, 속도, 토크 응답 계산
- `simulate()`  
  기존 코드 호환용 `simulate_motor()` 별칭 
- `simulate_wmx_log()`  
  WMX 로그를 바로 읽어 시뮬레이션 결과와 실측 데이터를 함께 반환
- `profile_step()`  
  step command profile 생성
- `profile_sine()`  
  sine command profile 생성
- `profile_chirp()`  
  chirp command profile 생성
- `profile_point_to_point()`  
  선형 point-to-point profile 생성
- `profile_scurve()`  
  jerk-limited s-curve profile 생성

### [`wmx_log_utils.py`](/home/ireh21/rei/code/wmx_log_utils.py)

- `load_wmx_log()`  
  WMX TXT/CSV 로그를 읽고 `command_position`, `feedback_position`,
  `feedback_velocity`, `feedback_torque`, `dt` 등을 반환
- `rmse()`  
  두 배열의 RMSE 계산

참고:
- CSV는 `Cycle`, `CommandPos-0`, `FeedbackPos-0`, `FeedbackVelocity-0`,
  `FeedbackTrq-0` 계열 헤더를 정규화해서 읽는다.

### [`metrics.py`](/home/ireh21/rei/code/metrics.py)

- `rmse()`, `nrmse()`  
  기본 오차 계산
- `following_error()`, `following_error_metrics()`  
  추종 오차와 요약 지표 계산
- `overshoot()`, `overshoot_error()`  
  overshoot 계산
- `settling_time()`, `settling_time_error()`  
  settling time 계산
- `rise_time()`, `rise_time_error()`  
  rise time 계산
- `estimate_gain_phase()`, `gain_phase_metrics()`  
  sine 응답 gain/phase 계산
- `trajectory_metrics()`  
  위치, 속도, 토크 전체 오차 요약
- `step_response_metrics()`  
  step 응답 비교 지표 계산
- `sine_response_metrics()`  
  sine 응답 비교 지표 계산
- `steady_speed_torque_bias()`, `ramp_response_metrics()`  
  ramp 정상속도 구간 토크 편향과 ramp 응답 비교

### [`result_summary.py`](/home/ireh21/rei/code/result_summary.py)

- `load_result_payload()`  
  저장된 결과 JSON에서 파라미터와 로그 경로를 읽음
- `summarize_result_bundle()`  
  결과 JSON 기준으로 validation, step, ramp, sine 대표 지표를 다시 계산
- `format_summary()`, `print_summary()`  
  노트북 마지막 요약 셀에서 바로 쓸 수 있는 문자열 출력 형태로 정리

참고:
- `04_1`, `04_2`, `04_3` 노트북의 마지막 요약 셀은 이 모듈을 사용한다.
- 중간 커널 변수 대신 저장된 `fitted_motor_params*.json`을 기준으로 요약을 다시 만든다.

### [`generate_sample_log.py`](/home/ireh21/rei/code/generate_sample_log.py)

- `generate_logs()`  
  여러 시험 프로파일의 합성 로그 생성
- 생성 대상:
  ramp, step, scurve, 여러 주파수의 sine
- 목적:
  실측 로그가 없을 때 시뮬레이션/피팅 파이프라인 동작 점검

## 사용 기준

- 재사용 가능한 함수와 모듈은 `code/`에 둔다.
- 실험 절차, 그래프, 비교, 해석은 `notebooks/`에 둔다.
- 외부에서 가져온 raw 참고 코드나 메모는 실행 모듈과 분리해 보관한다.
