# Newton_ikcable_notebook
franka_cube 파일을 압축을 풀면 다음과 같이 나온다
```
franka_cube/
├── README.md                # (원본은 Isaac Lab 확장 템플릿 안내문)
├── notebooks/
│   ├── 01_newton_ikcable_notebook.ipynb   ← 시작 지점 (Newton 단독)
│   ├── 02_isaaclab_newton...ipynb          ← 심화 (Isaac Lab 필요)
│   └── images/
├── scripts/                 # 강화학습(rsl_rl) 스크립트: train.py / play.py
└── source/franka_cube/      # Isaac Lab 확장 패키지 소스
```

현재는 GPU (NVDIA CUDA GPU)를 사용하지 않기에 02_isaaclab_newton...ipynb 해당 파일보다는 01_newton_ikcable_notebook.ipynb을 실행해본다.

## 일단 적어나가는 개념 (노트에 없는 내용 위주)

### • 1.1 CUDA
NVIDIA 그래픽 카드인 GPU를 이용해 계산을 빠르게 수행하는 기술
Newton과 갗은 물리 시뮬레이션처럼 같은 계산을 엄청 많이 반복하는 작업에 능함

### • 1.2 URDF
Unified Robot Description Format의 약자. 로봇의 몸 구조를 적어놓은 설계 설명서 파일이다.  

URDF의 파일 안에는 로봇에 대한 다음과 같은 정보가 들어간다
```
몸체가 몇 개, 관절이 어디 존재, 관절이 회전하는지 직선으로 움직이는지, 링크의 길이와 무게, 관절의 회전축, 충돌 현상, 화면에 표시할 3D 모델, 관절의 움직임 제한 
```

예를 들어 로봇팔을 단순히 표현하면 
```
바닥
 └── 관절 1
      └── 링크 1
           └── 관절 2
                └── 링크 2
```
이 연결 구조를 URDF 파일에 작성하는 것이다.   

URDF에서 가장 중요한 개념은 link와 joint 이다. 
- Link : 로봇의 움직이지 않는 하나의 단단한 부품 (로봇의 바닥, 그리퍼)
- joint : 두 링크를 연결하면서 움직임을 허용하는 부분 (회전 관절, 직선 이동 관절)

## 노트에 적힌 글 정리...?

- 핵심개념 : ModelBuilder → Model → State / Control → Solver  
└ **ModelBuiler** : USD, MJCF, URDF 형식의 에셋 불러오고, 강체·형상·관절과 각각의 속성을   조립하기 위한 모델 생성 API  
└ **Model** : 시뮬이 가능하게 변환된 데이터 (배열과 메타 데이터로 구성). CPU/GPU와 같은 연산 장치에 저장  
└ **State** : 시간에 따라 변하는 데이터 (ex. 위치, 속도, 힘)  
└ **Control** : joint에 전달하는 제어 입력 (ex. 목표 위치, 토크)  
└ **Contacts** : 충돌 감지 pipeline에서 생성되는 물체 간의 기하학적 접촉 정보  
└ **Solver** : 물리 법칙을 적분, 각종 제약 조건을 처리해 *시뮬을 다음 시점으로 진행*  

- 각 시뮬 substep *(한 번의 큰 시뮬 시간 간격을 더 잘게 나눈 계산 단위)* 에서 `Solver`는 `Model, State, Control, Contacts, dt (시간 간격)를 입력`으로 받아 `다음 시점의 State`를 계산.  

- **finalize()** : 다음의 함수를 수행하면 ModelBuilder가 연산 장치에서 바로 사용 가능한 Model로 변환된다. 

- URDF로 로봇을 불러오고, `Control.joint_target_pos`를 이용해 관절에 목표 각도를 준다. 

- 수치 계산에는 Wrap, 시뮬레이션에는 Newton을 사용  
└ **Warp** : CUDA 코드를 직접 작성하지 않아도 고성능 시뮬 및 기하 연산 코드를 작성 가능하도록 NVIDIA가 만든 Ptyhon 프레임워크. Warp가 CPU에 최족화된 네이티브 코드로 변환해주어, Python의 편리한 개발 방식을 유지하면서도, 물리 시뮬·로보틱스·그래픽스 작업에서 저수준 언어에 가까운 높은 성능을 얻을 수 있음.

- 


## 노트에 적힌 셀 정리...?

**1** : Newton이 MuJoCo 솔버를 사용할 수 있도록 MuJoCo 관련 라이브러리를 불러와 내부에 저장해 두는 준비 작업

**2** : CPU 사용 여부 선택, ViewerViser 생성 도구, Mermaid 흐름도(다이어그램) 출력 도구, 노트북용 진행률 표시줄 생성

**3, 4** : 개념에 해당하는 사진 출력

**5** : Newton 시뮬 장면의 설계도(ModelBuilder)에 바닥 1개, 떨어질 수 있는 박스 1개, 구 1개를 추가하고 생성된 물체 수를 확인. 
```  
Bodies: 2 -> 움직이는 박스와 구 /  Shapes: 3 -> 바닥, 박스 모양, 구 모양
```

**6** : *5*에서 만든 설계도를 실제 시뮬 Model로 확정. 이 Model 기반으로 `state` `control` `contacts` 객체 생성. 초기 장면을 ViewerViser에 표시.
```
state 2개 -> 현재 상태(state_0), 다음 상태(state_1)
control 1개 -> 제어 입력값
contacts 1개 -> 각 substep마다 충돌 감지 pipeline이 계산한 접촉 정보 저장

Contacts는 현재 상태인 State, 제어 입력인 Control, 시간 간격인 dt와 함께 solver.step(...)에 전달.