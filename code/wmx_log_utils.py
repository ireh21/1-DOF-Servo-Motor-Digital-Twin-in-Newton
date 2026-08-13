"""Notebook에서 공통으로 사용하는 WMX 텍스트 로그 처리와 오차 계산 함수.

이 파일의 함수는 Newton이나 Warp에 의존하지 않는다.
따라서 시뮬레이터를 초기화하지 않아도 로그 확인과 함수 시험을 할 수 있다.
"""

from pathlib import Path
import warnings

import numpy as np


REQUIRED_WMX_COLUMNS = (
    "TIME",
    "CMDPOS0",
    "FBKPOS0",
    "FBKVEL0",
    "FBKTRQ0",
)

_TIME_FACTORS_TO_SECONDS = {
    "s": 1.0,
    "ms": 1.0e-3,
    "us": 1.0e-6,
}


def load_wmx_log(
    file_path,
    *,
    time_unit="ms",
    position_scale=1.0,
    velocity_scale=1.0,
    torque_scale=1.0,
    dt_rtol=1.0e-3,
):
    """1-DOF 단일 모터 디지털 트윈에 필요한 WMX 신호를 읽는다.

    입력값
    ------
    file_path : 경로 형태의 값
        공백으로 값이 구분된 WMX 텍스트 로그의 경로이다.
        실제 열 이름이 있는 헤더 앞에 다른 설명 줄이 있어도 된다.
    time_unit : {"s", "ms", "us"}
        로그의 TIME 열에 사용된 시간 단위이다.
    position_scale, velocity_scale, torque_scale : 실수
        로그의 위치, 속도, 토크를 각각 rad, rad/s, N·m로 변환하기 위해
        원본 값에 곱하는 계수이다.
    dt_rtol : 실수
        각 샘플의 시간 간격이 중앙값 시간 간격에서 얼마나 벗어날 수 있는지
        정하는 상대 허용 오차이다. 허용 범위를 넘으면 경고를 출력한다.

    반환값
    ------
    dict
        SI 단위로 변환한 신호 배열, 시간 간격의 중앙값 ``dt``, 원본 파일
        경로와 선택 항목인 CYCLE, SYSTEM_TIME을 사전 형태로 반환한다.
        ``time``은 0초부터 시작한다. ``time_raw``와 ``time_ms``에는 원본
        TIME 열의 시작 시각을 유지한다.
    """
    file_path = Path(file_path)
    if not file_path.exists():
        raise FileNotFoundError(
            f"WMX 로그를 찾을 수 없습니다: {file_path.resolve()}"
        )

    try:
        time_factor = _TIME_FACTORS_TO_SECONDS[time_unit]
    except KeyError as exc:
        raise ValueError(
            "time_unit은 's', 'ms', 'us' 중 하나여야 합니다."
        ) from exc

    header_index, column_names = _find_header(file_path)
    raw = np.loadtxt(file_path, skiprows=header_index + 1, ndmin=2)

    if raw.shape[1] != len(column_names):
        raise ValueError(
            f"헤더의 열 개수({len(column_names)})와 "
            f"데이터의 열 개수({raw.shape[1]})가 다릅니다."
        )

    column = {name: index for index, name in enumerate(column_names)}
    time_raw = raw[:, column["TIME"]].astype(np.float64)
    time_absolute = time_raw * time_factor
    time = time_absolute - time_absolute[0]

    if len(time) < 2:
        raise ValueError("최소 2개 이상의 샘플이 필요합니다.")

    dt_samples = np.diff(time)
    if np.any(dt_samples <= 0.0):
        raise ValueError("TIME은 중복 없이 단조 증가해야 합니다.")

    dt = float(np.median(dt_samples))
    max_dt_error = float(np.max(np.abs(dt_samples - dt)))
    if max_dt_error > float(dt_rtol) * dt:
        warnings.warn(
            "WMX 샘플 간격이 일정하지 않습니다. 고정 dt 시뮬레이션 전에 "
            f"재표본화를 검토하세요. 중앙값 dt={dt:.9g}, "
            f"최대 편차={max_dt_error:.3g}",
            stacklevel=2,
        )

    data = {
        "source": str(file_path.resolve()),
        "time_raw": time_raw,
        "time_ms": time_absolute * 1000.0,
        "time": time,
        "dt": dt,
        "command_position": (
            raw[:, column["CMDPOS0"]].astype(np.float64) * position_scale
        ),
        "feedback_position": (
            raw[:, column["FBKPOS0"]].astype(np.float64) * position_scale
        ),
        "feedback_velocity": (
            raw[:, column["FBKVEL0"]].astype(np.float64) * velocity_scale
        ),
        "feedback_torque": (
            raw[:, column["FBKTRQ0"]].astype(np.float64) * torque_scale
        ),
        "cycle": _optional_column(raw, column, "CYCLE"),
        "system_time": _optional_column(raw, column, "SYSTEM_TIME"),
    }

    for name in (
        "time",
        "command_position",
        "feedback_position",
        "feedback_velocity",
        "feedback_torque",
    ):
        if not np.all(np.isfinite(data[name])):
            raise ValueError(f"{name}에 NaN 또는 inf가 있습니다.")

    return data


def rmse(reference, simulation):
    """두 배열의 크기가 같은지 확인하고 평균제곱근오차를 반환한다."""
    reference = np.asarray(reference, dtype=np.float64)
    simulation = np.asarray(simulation, dtype=np.float64)

    if reference.shape != simulation.shape:
        raise ValueError(
            "기준 데이터와 시뮬레이션 데이터의 크기가 다릅니다.\n"
            f"기준 데이터 배열 크기       : {reference.shape}\n"
            f"시뮬레이션 데이터 배열 크기 : {simulation.shape}"
        )

    return float(np.sqrt(np.mean((reference - simulation) ** 2)))


def _find_header(file_path):
    with file_path.open("r", encoding="utf-8") as stream:
        for index, line in enumerate(stream):
            names = tuple(name.upper() for name in line.strip().split())
            if all(required in names for required in REQUIRED_WMX_COLUMNS):
                return index, names

    raise ValueError(
        "필수 열을 포함한 헤더가 없습니다: "
        f"{list(REQUIRED_WMX_COLUMNS)}"
    )


def _optional_column(raw, column, name):
    if name not in column:
        return None
    return raw[:, column[name]].astype(np.float64)


__all__ = ["REQUIRED_WMX_COLUMNS", "load_wmx_log", "rmse"]
