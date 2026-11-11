"""기상청 ASOS 시간자료 API 연동 모듈.

기상청 API허브 관측자료를 프롬프트용 WeatherInfo로 정리한다.

담당: 한시원
"""
from __future__ import annotations

import datetime as dt
from dataclasses import dataclass

import requests

from .config import LocationConfig, WeatherConfig

KMA_URL = "https://apihub.kma.go.kr/api/typ01/url/kma_sfctm2.php"
KMA_FIELDS = (
    "TM STN WD WS GST_WD GST_WS GST_TM PA PS PT PR TA TD HM PV RN RN_DAY "
    "RN_JUN RN_INT SD_HR3 SD_DAY SD_TOT WC WP WW CA_TOT CA_MID CH_MIN CT "
    "CT_TOP CT_MID CT_LOW VS SS SI ST_GD TS TE_005 TE_01 TE_02 TE_03 "
    "ST_SEA WH BF IR IX"
).split()


@dataclass
class WeatherInfo:
    condition: str      # clear | clouds | rain | drizzle | thunderstorm | snow | fog
    description: str    # API가 준 한글 설명 (예: "튼구름")
    temp_c: float
    humidity: int
    time_of_day: str    # dawn | morning | afternoon | evening | night
    location_label: str


def condition_from_kma_code(code: str | int, cloud_amount: float | None = None) -> str:
    """GTS 현재일기 코드(WMO 4677)를 프롬프트용 분류로 바꾼다."""
    try:
        value = int(code)
    except (TypeError, ValueError):
        value = -1
    if 40 <= value <= 49:
        return "fog"
    if 50 <= value <= 59:
        return "drizzle"
    if 60 <= value <= 69:
        return "rain"
    if 70 <= value <= 79:
        return "snow"
    if 80 <= value <= 99:
        return "thunderstorm" if value >= 90 else "rain"
    if value >= 0:
        return "clear" if value <= 3 else "clouds"
    if cloud_amount is not None:
        return "clear" if cloud_amount <= 2 else "clouds"
    return "clouds"


def time_of_day(now: dt.datetime, sunrise: dt.datetime | None = None,
                sunset: dt.datetime | None = None) -> str:
    """현재 시각을 일출/일몰 기준으로 시간대로 나눈다."""
    if sunrise and sunset:
        if now < sunrise - dt.timedelta(minutes=30) or now > sunset + dt.timedelta(minutes=60):
            return "night"
        if now < sunrise + dt.timedelta(hours=1):
            return "dawn"
        if now > sunset - dt.timedelta(hours=1):
            return "evening"
    hour = now.hour
    if hour < 5 or hour >= 21:
        return "night"
    if hour < 7:
        return "dawn"
    if hour < 12:
        return "morning"
    if hour < 17:
        return "afternoon"
    return "evening"


def fetch_weather(loc: LocationConfig, cfg: WeatherConfig, timeout: float = 10.0) -> WeatherInfo:
    if cfg.provider == "mock" or not cfg.api_key:
        return mock_weather(loc)
    if cfg.provider != "kma":
        raise ValueError(f"지원하지 않는 weather.provider: {cfg.provider}")

    # ASOS 자료는 KST 정시 단위이므로 직전 완성된 관측 시각을 요청한다.
    now = dt.datetime.now(dt.timezone(dt.timedelta(hours=9)))
    observed_at = now.replace(minute=0, second=0, microsecond=0) - dt.timedelta(hours=1)
    params = {
        "tm": observed_at.strftime("%Y%m%d%H%M"),
        "stn": cfg.station_id,
        "help": 0,
        "authKey": cfg.api_key,
    }
    resp = requests.get(KMA_URL, params=params, timeout=timeout)
    resp.raise_for_status()
    row = _find_station_row(resp.text, cfg.station_id)

    def number(field: str) -> float | None:
        try:
            value = float(row[field])
        except (TypeError, ValueError):
            return None
        # TA는 영하 9도도 정상값이므로 -99 계열만 결측으로 본다.
        missing = {-99.0, -99.9} if field == "TA" else {-9.0, -99.0, -99.9}
        return None if value in missing else value

    temperature = number("TA")
    if temperature is None:
        raise ValueError(f"기상청 응답에 유효한 기온(TA)이 없습니다: {row['TM']}")
    humidity = number("HM")
    cloud_amount = number("CA_TOT")
    condition = condition_from_kma_code(row["WC"], cloud_amount)
    description = {
        "clear": "맑음", "clouds": "흐림", "rain": "비", "drizzle": "이슬비",
        "thunderstorm": "뇌우", "snow": "눈", "fog": "안개",
    }[condition]

    return WeatherInfo(
        condition=condition,
        description=description,
        temp_c=temperature,
        humidity=int(humidity) if humidity is not None else 0,
        time_of_day=time_of_day(now),
        location_label=loc.label,
    )


def _find_station_row(text: str, station_id: int) -> dict[str, str]:
    """주석 행을 건너뛰고 지정 관측소의 시간자료 행을 찾는다."""
    for line in text.splitlines():
        line = line.strip()
        if not line or line.startswith("#") or line.startswith("-"):
            continue
        values = line.split()
        if len(values) < len(KMA_FIELDS) or not values[0].isdigit():
            continue
        row = dict(zip(KMA_FIELDS, values))
        if row["STN"] == str(station_id):
            return row
    raise ValueError(f"기상청 응답에서 관측소 {station_id}의 시간자료를 찾지 못했습니다")


def mock_weather(loc: LocationConfig) -> WeatherInfo:
    """API 키 없이 개발할 때 쓰는 가짜 날씨."""
    return WeatherInfo(
        condition="clear",
        description="맑음 (mock)",
        temp_c=12.0,
        humidity=45,
        time_of_day=time_of_day(dt.datetime.now()),
        location_label=loc.label,
    )
