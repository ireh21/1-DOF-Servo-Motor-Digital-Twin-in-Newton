# Docs Guide

이 폴더는 단일 서보 모터 Newton 디지털 트윈 프로젝트의 문서를 모아 두는 곳이다.  
문서는 역할에 따라 `guideline/`, `study/`, `result/`로 나눈다.  


## 권장 읽기 순서

1. [`guideline/00_newton_env.md`](/home/ireh21/rei/docs/guideline/00_newton_env.md)  
   Newton/Warp 실행 환경을 먼저 맞춘다.
2. [`guideline/01_project_overview.md`](/home/ireh21/rei/docs/guideline/01_project_overview.md)  
   프로젝트 목적, 범위, 전체 제어 흐름을 먼저 본다.
3. [`guideline/02_digital_twin.md`](/home/ireh21/rei/docs/guideline/02_digital_twin.md)  
   디지털 트윈 작업 순서, 로그, 파라미터, 피팅 개요를 본다.
4. [`study/04_wmx3_data_log.md`](/home/ireh21/rei/docs/study/04_wmx3_data_log.md)  
   WMX 로그 형식, 단위 정합, 입력 파형 의미를 확인한다.
5. [`result/01_fitting_strategy_and_results.md`](/home/ireh21/rei/docs/result/01_fitting_strategy_and_results.md)  
   현재 저장된 피팅 결과와 비교 기준을 본다.
6. [`result/02_limitations_and_future_plan.md`](/home/ireh21/rei/docs/result/02_limitations_and_future_plan.md)  
   현재 한계와 다음 확장 방향을 본다.

## 폴더별 역할

### `guideline/`

프로젝트를 처음 따라갈 때 필요한 큰 흐름과 작업 절차를 둔다.

- [`00_newton_env.md`](/home/ireh21/rei/docs/guideline/00_newton_env.md)
  WSL2 Ubuntu 기준 Newton/Warp, venv, JupyterLab 실행 환경 준비와 향후 GPU/Isaac Sim 확장 메모
- [`01_project_overview.md`](/home/ireh21/rei/docs/guideline/01_project_overview.md)
  프로젝트 목적, 시스템 구성, 제어 흐름, 검증 관점을 정리한 개요 문서
- [`02_digital_twin.md`](/home/ireh21/rei/docs/guideline/02_digital_twin.md)
  디지털 트윈 작업 순서, 로그 준비, 파라미터 설계, 식별과 검증 개요 문서

### `study/`

배경 개념과 설계 판단에 필요한 공부용 문서를 둔다.

- [`01_ethercat_cia402_csp.md`](/home/ireh21/rei/docs/study/01_ethercat_cia402_csp.md)
  EtherCAT, CiA402, CSP 운전 방식 정리
- [`02_newton_motor.md`](/home/ireh21/rei/docs/study/02_newton_motor.md)
  Newton/Warp, actuator 모델, 물리 파라미터, 피팅 대상 개념 정리
- [`03_newton_ikcable_study.md`](/home/ireh21/rei/docs/study/03_newton_ikcable_study.md)
  Newton 관련 추가 실험/조사 메모
- [`04_wmx3_data_log.md`](/home/ireh21/rei/docs/study/04_wmx3_data_log.md)
  WMX3 실측 로그 형식, 단위 변환, 입력 파형 준비 기준

### `result/`

현재 저장소에 남겨 둘 결과 요약, 해석, 한계 정리를 둔다.

- [`01_fitting_strategy_and_results.md`](/home/ireh21/rei/docs/result/01_fitting_strategy_and_results.md)
  사용한 로그, 노트북 역할, 파라미터 후보, loss 비교 정리
- [`02_limitations_and_future_plan.md`](/home/ireh21/rei/docs/result/02_limitations_and_future_plan.md)
  한계점, 개선점, 향후 확장성에 대한 내용

## 읽을 때 구분하면 좋은 점

- `guideline`은 "프로젝트를 어떻게 진행했는가"에 가깝다.
- `study`는 "왜 이런 개념과 구조를 봐야 하는가"에 가깝다.
- `result`는 "현재 무엇이 남아 있고 어떻게 해석하는가"에 가깝다.
