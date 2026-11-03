"""설정 로딩 모듈.

config/config.yaml(지역, 갱신 주기, 디스플레이 등)과 .env(API 키)를 읽어
하나의 Config 객체로 묶는다.

담당: 한시원
"""
from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path

import yaml
from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_CONFIG_PATH = PROJECT_ROOT / "config" / "config.yaml"
EXAMPLE_CONFIG_PATH = PROJECT_ROOT / "config" / "config.example.yaml"


@dataclass
class LocationConfig:
    city: str = "Seoul"
    country: str = "KR"
    lat: float | None = None
    lon: float | None = None
    label: str = "서울"  # 화면에 표시할 지역 이름


@dataclass
class WeatherConfig:
    provider: str = "openweathermap"  # openweathermap | mock
    api_key: str = ""


@dataclass
class ImageGenConfig:
    provider: str = "openai"  # openai | mock
    model: str = "gpt-image-1"
    size: str = "1536x1024"
    quality: str = "low"
    api_key: str = ""


@dataclass
class ImagingConfig:
    dither: str = "floyd-steinberg"  # floyd-steinberg | atkinson | threshold
    contrast: float = 1.3
    overlay: bool = True
    font_path: str = "/usr/share/fonts/truetype/nanum/NanumGothicBold.ttf"


@dataclass
class DisplayConfig:
    driver: str = "mock"  # epd42 | mock
    width: int = 400
    height: int = 300
    rotate: int = 0
    spi_bus: int = 0
    spi_device: int = 0
    spi_speed_hz: int = 4_000_000
    spi_mode: int = 3  # WeAct 예제 기준
    pin_rst: int = 17   # BCM 번호 (물리 11번)
    pin_dc: int = 25    # BCM 번호 (물리 22번)
    pin_busy: int = 24  # BCM 번호 (물리 18번)


@dataclass
class Config:
    location: LocationConfig = field(default_factory=LocationConfig)
    weather: WeatherConfig = field(default_factory=WeatherConfig)
    image_gen: ImageGenConfig = field(default_factory=ImageGenConfig)
    imaging: ImagingConfig = field(default_factory=ImagingConfig)
    display: DisplayConfig = field(default_factory=DisplayConfig)
    interval_minutes: int = 60
    output_dir: str = "output"


def _merge(dc, values: dict | None):
    for key, value in (values or {}).items():
        if hasattr(dc, key):
            setattr(dc, key, value)
    return dc


def load_config(path: str | Path | None = None) -> Config:
    """YAML 설정과 환경 변수를 읽어 Config를 만든다."""
    load_dotenv(PROJECT_ROOT / ".env")

    if path is None:
        path = DEFAULT_CONFIG_PATH if DEFAULT_CONFIG_PATH.exists() else EXAMPLE_CONFIG_PATH
    raw = yaml.safe_load(Path(path).read_text(encoding="utf-8")) or {}

    cfg = Config()
    _merge(cfg.location, raw.get("location"))
    _merge(cfg.weather, raw.get("weather"))
    _merge(cfg.image_gen, raw.get("image_gen"))
    _merge(cfg.imaging, raw.get("imaging"))
    _merge(cfg.display, raw.get("display"))
    cfg.interval_minutes = raw.get("interval_minutes", cfg.interval_minutes)
    cfg.output_dir = raw.get("output_dir", cfg.output_dir)

    # API 키는 YAML이 아니라 .env에서만 읽는다 (깃에 올라가지 않도록)
    cfg.weather.api_key = os.getenv("OPENWEATHER_API_KEY", "")
    cfg.image_gen.api_key = os.getenv("OPENAI_API_KEY", "")
    return cfg
