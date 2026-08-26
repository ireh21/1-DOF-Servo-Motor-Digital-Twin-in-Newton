# 저장소 정리 및 인수인계 실행 계획

## 1. 목적

이 문서는 현재 `~/rei` 저장소를 기준으로,

- 이미 정리된 항목
- 더 이상 계획에 남길 필요가 없는 항목
- 다른 문서로 옮겨야 하는 항목
- 남은 기간 안에 실제로 수행해야 하는 항목

만 남기기 위한 실행 계획이다.

지금 단계에서는 새 문서를 무작정 늘리기보다,
이미 있는 문서와 노트, 노트북을 기준으로 **필요한 내용만 옮기고 정리하는 것**을 우선한다.


## 2. 현재 상태 요약

현재 저장소에서 이미 반영된 항목은 아래와 같다.

- `docs/guideline/01_project_overview.md`
  오차 지표와 검증 설명을 다듬었고, `프로젝트 범위 밖 항목`을 추가했다.
- `docs/study/02_newton_motor.md`
  깨진 참조 링크를 수정했고, 이 문서가 개념 설명용이며 실제 구현은 `single_motor_twin.py`에서 일부 요소를 직접 계산한다는 안내를 상단에 추가했다.
- `docs/study/03_newton_ikcable_study.md`
  baseline 학습 문서 구조로 재정리했고, 파일명도 `jujeori`에서 `study`로 정리했다.
- `docs/guideline/02_digital_twin.md`
  현재 단일 모터 구조 요약 블록을 추가했다.
- `code/codeREADME.md`
  `code/` 폴더 설명 문서를 추가했다.
- `code/fit_pipeline_skeleton.py`
  현재 저장소 기준 필수 파일이 아니므로 삭제했다.

즉, `study 02`, `study 03`, `guideline 01`, `code` 쪽의 큰 혼란 요소는 이미 한 차례 정리된 상태이다.


## 3. 더 이상 계획에 남길 필요가 없는 항목

아래 항목은 이미 반영되었으므로 추가 작업 목록에서 제외한다.

- `docs/study/02_newton_motor.md`의 깨진 링크 수정
- `docs/study/02_newton_motor.md` 상단의 구현 관계 설명 추가
- `docs/study/03_newton_ikcable_study.md` 구조 재정리
- `docs/study/03_newton_ikcable_study.md` 파일명 정리
- `docs/guideline/01_project_overview.md`의 범위 밖 항목 추가
- `code/` 폴더 설명 문서 추가
- `fit_pipeline_skeleton.py` 정리

따라서 이전 계획 문서에 남아 있던
"이 파일을 손봐야 한다" 수준의 포괄적 지시는 삭제해도 된다.


## 4. 지금 남아 있는 핵심 문제

현재 저장소에서 실제로 남아 있는 핵심 문제는 아래 정도이다.

- `PROJECT.md`가 아직 실제 경로와 맞지 않는 링크를 가지고 있고, 입구 문서 역할로 정리되지 않았다.
- `docs/guideline/02_digital_twin.md`는 구조 설명은 있지만, 직접 구현 선택 이유와 현재 모델 한계는 더 정리할 여지가 있다.
- `docs/study/04_wmx3_data_log.md`는 피팅 전략과 로그 의미는 좋지만, 사용한 주파수 대역과 제외 이유, 해석 주의점이 더 필요하다.
- `docs/results`, `docs/discussion`, `docs/handover` 폴더가 아직 실제로 만들어지지 않았다.
- `notebooks/notebooks_folder_jjr.md`에는 개념 메모, 구현 메모, 예전 작업 계획, 피팅 아이디어가 함께 섞여 있다.
- `notebooks/README`가 없어서 `04_*` 노트북 차이가 밖에서 바로 보이지 않는다.


## 5. 노트와 문서에서 옮겨야 하는 항목

특히 `notebooks/notebooks_folder_jjr.md`는
현재 상태 그대로 두면 메모와 계획과 설명이 섞여 있어 인수인계용으로는 불리하다.

이 파일의 내용은 아래 기준으로 옮긴다.

### `docs/guideline/02_digital_twin.md`로 옮길 내용

- `feedback_torque`와 `net_torque`의 차이
- 왜 Newton 내부 마찰을 끄고 직접 마찰 토크를 계산하는지
- 왜 현재 구현에서 일부 요소를 Python 코드로 직접 계산하는지

즉, **현재 모델이 실제로 어떻게 동작하는지**를 설명하는 내용은
`guideline/02`가 맡는다.

### `docs/study/02_newton_motor.md`로 옮길 수 있는 내용

- 파라미터가 모터 응답에 어떤 영향을 주는지에 대한 개념 요약

다만 이 문서는 `study` 문서이므로,
프로젝트 진행 기록이나 실제 결과 해석까지 길게 넣지는 않는다.

### `docs/study/04_wmx3_data_log.md`로 옮길 내용

- 각 로그가 어떤 파라미터 식별에 유리한지에 대한 설명
- 왜 특정 주파수 대역을 사용했는지
- 왜 학습용 로그와 검증용 로그를 분리하는지

즉, **로그와 파형의 의미**는 `study/04`가 맡는다.

### `docs/results/01_fitting_strategy_and_results.md`로 옮길 내용

- 실제로 어떤 로그를 학습에 사용했고 어떤 로그를 검증에 사용했는지
- 실제로 어떤 optimizer 조합을 썼는지
- `04_1`, `04_2`, `04_3`가 각각 무엇을 시도했는지
- 최종 채택한 파라미터와 채택 이유

즉, **이번 프로젝트에서 실제로 한 피팅 절차와 결과**는 `results`가 맡는다.

### 옮긴 뒤 삭제해도 되는 내용

아래 내용은 다른 문서에 핵심만 옮긴 뒤 `notebooks/notebooks_folder_jjr.md`에서 삭제해도 된다.

- `지금 당장 할 일`
- `추천 방식`
- `가장 추천하는 피팅 방법`
- 예전 시점의 작업 메모나 임시 계획

이 항목들은 과거 작업 계획이지, 최종 인수인계 문서에 그대로 남길 내용은 아니다.


## 6. 아직 새로 작성해야 하는 문서

현재 저장소 상태를 보면 아래 문서는 아직 실제 파일이 없다.

### `docs/results/01_fitting_strategy_and_results.md`

이 문서에는 아래 내용을 적는다.

- 학습에 사용한 로그와 검증에 사용한 held-out 로그
- 사용한 주파수 목록과 제외한 주파수 목록
- 초기값 추정 절차
- 사용한 최적화 방법과 적용 순서
- `04_1`, `04_2`, `04_3` 차이
- 최종 채택 결과와 근거

이 문서는 결과 그림만 두는 문서가 아니라,
**실제 피팅 실험 기록 + 결과 요약** 문서로 두는 편이 맞다.

### `docs/discussion/01_limitations_and_future_work.md`

이 문서에는 아래 내용을 적는다.

- 현재 모델이 설명하지 못하는 요소
- 왜 10Hz 이상을 적극 학습에 사용하지 않았는지
- 왜 Newton 기본 actuator 기반 접근을 바로 쓰지 않았는지
- GPU/CUDA 사용 시 기대되는 개선점
- CR3A 로봇암 확장 방향
- 향후 비선형 요소 추가 방향

이 문서는 "못한 것 목록"이 아니라,
**현재 한계와 다음 확장 방향 요약** 문서로 둔다.

### `docs/handover/01_project_presentation.md`

이 문서는 발표 흐름용 초안이다.
권장 순서는 아래와 같다.

1. 프로젝트 배경
2. 내가 맡은 범위
3. 사용한 데이터와 방법
4. 구현한 디지털 트윈 구조
5. 피팅 절차와 결과
6. 결론
7. 배운 점
8. 토의할 점
9. 향후 방향


## 7. 남아 있는 기존 문서 수정 항목

### `docs/guideline/02_digital_twin.md`

남은 핵심은 아래 3가지다.

- 직접 구현을 선택한 이유를 더 분명히 적기
- Newton 기본 actuator 기반 접근의 한계와 직접 구현의 한계 적기
- 현재 모델이 포착하지 못하는 요소 적기

### `docs/study/04_wmx3_data_log.md`

남은 핵심은 아래 3가지다.

- 사용한 주파수 대역과 제외한 대역 적기
- 10Hz 이상을 학습에 적극 사용하지 않은 이유 적기
- 데이터 한계와 해석 주의점 적기

### `PROJECT.md`

이 문서는 마지막에 정리한다.

남은 핵심은 아래와 같다.

- 실제 경로 기준으로 링크 수정
- 프로젝트 입구 문서 역할로 축약
- 문서 읽는 순서 정리
- 코드/노트북/문서 역할 연결
- 현재 상태와 향후 방향 짧게 요약


## 8. 코드와 노트북 쪽 남은 작업

### `code/`

현재 기준으로는 큰 수정이 더 필요하지 않다.

- 핵심 Python 파일은 이미 남겨 둘 것과 지울 것을 한 번 정리했다.
- `code/codeREADME.md`도 추가되어 있어, 새로운 공통 모듈이 생기지 않는 한 큰 구조 변경은 필요하지 않다.

즉, 지금 시점에서는 `code/`는 거의 정리 완료로 본다.

### `notebooks/`

노트북 쪽은 아직 아래 두 작업이 남아 있다.

- `notebooks/README.md` 작성
- `04_*` 노트북 차이 정리

`notebooks/README.md`에는 아래 정도만 있으면 충분하다.

- 각 노트북의 목적
- 어떤 노트북이 기본 확인용인지
- 어떤 노트북이 피팅용인지
- 어떤 노트북이 비교/검증용인지


## 9. 실제 작업 순서

지금 저장소 상태를 기준으로 하면,
아래 순서로 진행하는 것이 가장 덜 꼬인다.

1. `docs/study/04_wmx3_data_log.md` 보강
2. `docs/guideline/02_digital_twin.md` 보강
3. `notebooks/notebooks_folder_jjr.md`에서 필요한 내용만 다른 문서로 이동
4. `docs/results/01_fitting_strategy_and_results.md` 작성
5. `docs/discussion/01_limitations_and_future_work.md` 작성
6. `notebooks/README.md` 작성
7. `docs/handover/01_project_presentation.md` 작성
8. 마지막에 `PROJECT.md` 정리

핵심은 `PROJECT.md`를 먼저 손보는 것이 아니라,
나머지 문서가 정리된 뒤 최종 인덱스로 고치는 것이다.


## 10. 최종 목표

정리가 끝나면 저장소는 아래 흐름으로 읽히면 된다.

1. `PROJECT.md`
2. `docs/guideline/01_project_overview.md`
3. `docs/guideline/02_digital_twin.md`
4. `docs/study/04_wmx3_data_log.md`
5. `docs/results/01_fitting_strategy_and_results.md`
6. `docs/discussion/01_limitations_and_future_work.md`
7. `notebooks/05_fitting_comparison.ipynb`

이 흐름이 되면, 처음 보는 사람도

- 프로젝트가 무엇인지
- 어떤 데이터와 모델을 썼는지
- 실제로 어떤 피팅을 했는지
- 결과와 한계가 무엇인지
- 다음에 무엇을 하면 되는지

를 짧은 시간 안에 따라갈 수 있다.
