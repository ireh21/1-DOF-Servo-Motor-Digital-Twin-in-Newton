# Newton 환경 구축 가이드

## 이 문서의 역할

이 문서는 `rei` 레포를 실행하기 전에 필요한 **Newton/Warp Python 환경을 맞추는 최소 절차**와, 향후 확장 시 참고할 **GPU + Isaac Sim 계열 환경 메모**를 함께 정리한 가이드다.  
기준 자료는 `~/internship` 안의 `Newton_실행가이드.md`, `setup_newton_wsl.sh`, `requirements-newton.txt`이며, 여기서는 이 레포에 직접 필요한 내용만 남긴다.

이 문서를 읽고 바로 기대할 수 있는 것은 다음과 같다.

- WSL2 Ubuntu에서 Newton/Warp 실행 환경 준비
- Python 가상환경 생성
- 필요한 패키지 버전 설치
- GPU 사용 가능 여부 확인
- 향후 GPU + Isaac Sim 경로의 존재와 전제 조건 확인

반대로, 이 문서가 직접 다루지 않는 것은 아래와 같다.

- Isaac Lab 전체 세부 설치 절차
- 강화학습 스택의 상세 운용 방법
- Windows 드라이버 상세 설치 절차
- 서버 배포나 Docker 구성

## 1. 적용 범위

현재 기준 적용 범위는 아래와 같다.

- 운영 환경: **WSL2 Ubuntu**
- Python: **3.10 ~ 3.12 권장**
- 목적: **Newton/Warp와 JupyterLab이 돌아가는 로컬 실험 환경 준비**
- 대상 레포: **`/home/ireh21/rei`**

이 프로젝트는 Newton 기반 단일 모터 디지털 트윈 실험이 목적이므로, 기본 경로는 가벼운 Newton/Warp 로컬 환경이다. 다만 향후 확장자를 위해 GPU + Isaac Sim 계열 경로도 아래에 선택적으로 남긴다.

## 2. 먼저 확인할 것

### 2.1 Python

터미널에서 아래를 확인한다.

```bash
python3 --version
```

### 2.2 GPU 사용 여부

CUDA를 쓰려면 **Windows 쪽 NVIDIA 드라이버**가 먼저 준비되어 있어야 한다.  
WSL 안에 드라이버를 따로 설치하는 방식이 아니라, Windows 드라이버가 WSL에 노출되는 구조다.

터미널에서 아래를 확인한다.

```bash
nvidia-smi
```

- 카드 정보가 나오면 GPU 사용 준비가 된 상태다.
- 동작하지 않으면 Warp는 CPU로 폴백할 수 있다.
- CPU만으로도 작은 실험은 가능하지만 피팅은 느릴 수 있다.

## 3. 가상환경 생성

먼저 필요한 시스템 패키지를 준비한다.

```bash
sudo apt-get update
sudo apt-get install -y python3-venv python3-pip
```

그 다음 가상환경을 만든다.

```bash
python3 -m venv ~/newton-env
source ~/newton-env/bin/activate
python -m pip install --upgrade pip
```

앞으로는 작업 전에 아래를 실행하면 된다.

```bash
source ~/newton-env/bin/activate
```

## 4. 패키지 설치

`~/internship/requirements-newton.txt`와 `setup_newton_wsl.sh` 기준으로, 현재 레포에 필요한 버전은 아래와 같다.

```bash
pip install \
  warp-lang==1.13.0 \
  newton==1.2.1 \
  newton-actuators==0.1.0 \
  newton-usd-schemas==0.2.0 \
  mujoco==3.8.0 \
  mujoco-warp==3.8.0.3 \
  viser==1.0.30 \
  numpy \
  jupyterlab
```

주의:

- Newton과 Warp는 신생 스택이라 버전이 어긋나면 API 차이로 깨질 수 있다.
- 이 레포에는 아직 `requirements.txt`나 `pyproject.toml`이 없으므로, 우선 위 버전을 수동으로 맞춘다.

## 5. 설치 확인

아래 명령으로 Warp와 Newton import를 확인한다.

```bash
python - <<'PY'
import warp as wp
wp.init()
print("CUDA devices visible to Warp:", wp.get_cuda_device_count())
import newton
print("newton OK, version:", getattr(newton, "__version__", "unknown"))
PY
```

정상이라면 다음 두 가지를 확인할 수 있다.

- Warp가 CUDA 디바이스 개수를 읽는다.
- `newton` import가 실패하지 않는다.

## 6. 이 레포 실행

가상환경을 활성화한 뒤, 레포 루트로 이동한다.

```bash
source ~/newton-env/bin/activate
cd /home/ireh21/rei
```

### 6.1 단일 모터 시뮬레이터 실행

```bash
PYTHONPATH=code python3 code/single_motor_twin.py --profile scurve --viewer
```

### 6.2 노트북 열기

```bash
jupyter lab notebooks/
```

피팅 노트북은 실측 WMX 로그 경로를 직접 확인하거나 수정해야 한다.  
현재 예시 노트북은 Windows WSL 경로를 기본값으로 두고 있다.

## 7. 자주 막히는 지점

### 7.1 `nvidia-smi`가 안 된다

- Windows 쪽 NVIDIA 드라이버 상태를 먼저 확인한다.
- WSL 내부 드라이버 설치를 시도하는 방식은 이 문서 범위가 아니다.

### 7.2 `newton` 설치가 실패한다

- Python 버전이 너무 다르지 않은지 확인한다.
- 패키지 버전을 위에 적은 값과 다르게 섞어 설치하지 않았는지 확인한다.

### 7.3 viewer가 기대대로 안 뜬다

- Jupyter 출력에 뜨는 localhost 링크를 직접 여는 편이 빠를 수 있다.
- 환경에 따라 GPU 대신 CPU로 실행되어 느리게 보일 수 있다.

## 8. 향후 확장용 GPU + Isaac Sim 메모

`~/internship/Newton_실행가이드.md`와 `~/internship/franka_cube/README.md`에는 Newton/Warp 단독 실행을 넘어서 Isaac Sim 또는 Isaac Lab 계열로 가는 경로가 함께 정리돼 있다.

이 레포를 나중에 단일 모터 수준에서 더 확장한다면 아래 조건을 같이 봐야 한다.

- Isaac Sim 계열은 사실상 NVIDIA GPU를 전제로 본다.
- WSL 내부가 아니라 Windows 쪽 NVIDIA 드라이버 상태가 먼저 맞아야 한다.
- Newton/Warp 단독 환경보다 설치 규모와 디스크 사용량이 훨씬 커진다.
- 현재 `rei`는 단일 모터 디지털 트윈이 중심이고, Isaac Sim 경로는 향후 로봇 단위 확장용 참고 경로다.

`~/internship` 기준으로 남겨둘 만한 버전 메모는 아래와 같다.

- `torch==2.11.0+cu128`
- `torchvision==0.26.0+cu128`
- `isaacsim==6.0.1.0`
- `gymnasium==1.2.1`
- Isaac Lab commit: `a4a7602f29e755e2673fe0022ea35566df6dd7d5`

이 경로는 현재 레포의 필수 선행조건은 아니다. 하지만 [`dobot_cr3a_newton_loader.ipynb`](/home/ireh21/rei/notebooks/dobot_cr3a_newton_loader.ipynb) 같은 확장 실험으로 넘어갈 가능성을 생각하면, 향후 작업자는 GPU 기반 환경 경로가 별도로 있다는 사실을 알고 시작하는 편이 안전하다.

## 9. 다음에 읽을 문서

환경이 준비되면 아래 순서로 읽는 편이 자연스럽다.

1. [`01_project_overview.md`](/home/ireh21/rei/docs/guideline/01_project_overview.md)
2. [`02_digital_twin.md`](/home/ireh21/rei/docs/guideline/02_digital_twin.md)
3. [`../study/04_wmx3_data_log.md`](/home/ireh21/rei/docs/study/04_wmx3_data_log.md)
4. [`../result/01_fitting_strategy_and_results.md`](/home/ireh21/rei/docs/result/01_fitting_strategy_and_results.md)
