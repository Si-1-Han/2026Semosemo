"""날씨 API 연동 모듈.

설정 파일에 지정된 지역의 현재 날씨를 OpenWeatherMap에서 받아
프롬프트 생성에 쓰기 좋은 형태(WeatherInfo)로 정리한다.

담당: 한시원
"""
from __future__ import annotations

import datetime as dt
from dataclasses import dataclass

import requests

from .config import LocationConfig, WeatherConfig

OWM_URL = "https://api.openweathermap.org/data/2.5/weather"


@dataclass
class WeatherInfo:
    condition: str      # clear | clouds | rain | drizzle | thunderstorm | snow | fog
    description: str    # API가 준 한글 설명 (예: "튼구름")
    temp_c: float
    humidity: int
    time_of_day: str    # dawn | morning | afternoon | evening | night
    location_label: str


def condition_from_owm_id(weather_id: int) -> str:
    """OpenWeatherMap 날씨 코드(id)를 단순 분류로 바꾼다.
    https://openweathermap.org/weather-conditions
    """
    if 200 <= weather_id < 300:
        return "thunderstorm"
    if 300 <= weather_id < 400:
        return "drizzle"
    if 500 <= weather_id < 600:
        return "rain"
    if 600 <= weather_id < 700:
        return "snow"
    if 700 <= weather_id < 800:
        return "fog"
    if weather_id == 800:
        return "clear"
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

    params = {"appid": cfg.api_key, "units": "metric", "lang": "kr"}
    if loc.lat is not None and loc.lon is not None:
        params.update(lat=loc.lat, lon=loc.lon)
    else:
        params["q"] = f"{loc.city},{loc.country}"

    resp = requests.get(OWM_URL, params=params, timeout=timeout)
    resp.raise_for_status()
    data = resp.json()

    tz = dt.timezone(dt.timedelta(seconds=data.get("timezone", 0)))
    now = dt.datetime.now(tz)
    sunrise = dt.datetime.fromtimestamp(data["sys"]["sunrise"], tz)
    sunset = dt.datetime.fromtimestamp(data["sys"]["sunset"], tz)
    w = data["weather"][0]

    return WeatherInfo(
        condition=condition_from_owm_id(w["id"]),
        description=w.get("description", ""),
        temp_c=float(data["main"]["temp"]),
        humidity=int(data["main"]["humidity"]),
        time_of_day=time_of_day(now, sunrise, sunset),
        location_label=loc.label,
    )


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
