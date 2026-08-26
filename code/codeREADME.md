# Code Folder Guide

이 폴더에는 단일 모터 디지털 트윈 프로젝트에서 재사용하는 Python 모듈을 둔다.
노트북 안에서 반복해서 정의할 필요가 있는 로직이나, 여러 실험에서 공통으로 사용하는 함수는 이 폴더에 두는 것을 기준으로 한다.

## 파일 목록

- `single_motor_twin.py`  
  단일 무부하 서보 모터의 Newton 기반 1-DOF 디지털 트윈 모델과 시뮬레이션 실행 함수가 들어 있다.
- `wmx_log_utils.py`  
  WMX 로그 로드, 시간축 처리, 단위 변환에 필요한 공통 유틸리티가 들어 있다.
- `metrics.py`  
  위치, 속도, 토크 오차와 step/sine/ramp 응답 비교에 사용하는 평가 지표 함수가 들어 있다.
- `generate_sample_log.py`  
  실제 실험 로그가 준비되기 전 파이프라인 점검에 사용할 합성 WMX 로그를 생성한다.

## 호출 가능한 주요 항목

### **single_motor_twin.py**

- `MotorParams`  
  단일 모터 모델의 제어기, 관성, 마찰, 토크 제한 파라미터 묶음
- `build_motor_model()`  
  Newton의 1-DOF 단일 모터 모델 생성
- `simulate_motor()`  
  command position 배열을 넣어 위치, 속도, 토크 응답 계산
- `simulate()`  
  simulate_motor( )의 짧은 호출용 래퍼
- `simulate_wmx_log()`  
  WMX 로그를 바로 불러와 실측 데이터와 시뮬레이션 결과를 함께 반환
- `profile_step()`, `profile_sine()`, `profile_chirp()`, `profile_point_to_point()`, `profile_scurve()`  
  시험용 command profile 생성

### **wmx_log_utils.py**

- `load_wmx_log()`  
  WMX 로그 파일을 읽고 시간축 처리, 단위 정합까지 수행
- `rmse()`  
  두 배열의 RMSE 계산

### **metrics.py**

- `rmse()`, `nrmse()`  
  기본 오차 계산
- `following_error()`, `following_error_metrics()`  
  추종오차 계산과 요약 지표 반환
- `step_response_metrics()`  
  rise time, settling time, overshoot 등 step 응답 비교
- `sine_response_metrics()`  
  gain, phase, following error 등 sine 응답 비교
- `ramp_response_metrics()`  
  steady-speed torque bias와 following error 등 ramp 응답 비교
- `trajectory_metrics()`  
  위치, 속도, 토크의 전체 오차 요약

## 사용 기준

- 재사용 가능한 함수와 모듈은 `code/`에 둔다.
- 실험 순서, 그래프, 해석, 비교 과정은 `notebooks/`에 둔다.
- 특정 노트북에서만 한 번 쓰고 끝나는 임시 코드는 바로 모듈화하지 않아도 되지만,
  같은 함수 정의가 반복되기 시작하면 `code/`로 옮기는 것을 우선한다.

## 참고

`generate_sample_log.py`는 실측 WMX 로그 취득 전 테스트와 파이프라인 점검을 위한 보조 스크립트이다.  
실제 캘리브레이션과 결과 해석은 합성 로그가 아니라 WMX3로 취득한 실측 데이터를 기준으로 한다.