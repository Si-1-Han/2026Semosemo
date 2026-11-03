"""디스플레이 드라이버 패키지.

담당: 전성재
"""
from __future__ import annotations

from .base import Display
from ..config import DisplayConfig


def create_display(cfg: DisplayConfig, output_dir: str = "output") -> Display:
    if cfg.driver == "epd42":
        from .epd42 import EPD42  # 라즈베리파이에서만 import (spidev, gpiozero)
        return EPD42(cfg)
    if cfg.driver == "mock":
        from .mock import MockDisplay
        return MockDisplay(cfg, output_dir)
    raise ValueError(f"지원하지 않는 display.driver: {cfg.driver}")


__all__ = ["Display", "create_display"]
