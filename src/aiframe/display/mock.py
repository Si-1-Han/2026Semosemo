"""하드웨어 없이 개발할 때 쓰는 가짜 디스플레이 — 결과를 PNG로 저장한다.

담당: 전성재
"""
from __future__ import annotations

import datetime as dt
from pathlib import Path

from PIL import Image

from .base import Display
from ..config import DisplayConfig


class MockDisplay(Display):
    def __init__(self, cfg: DisplayConfig, output_dir: str = "output"):
        self.width, self.height = cfg.width, cfg.height
        self.out = Path(output_dir)
        self.out.mkdir(parents=True, exist_ok=True)
        self.last_path: Path | None = None

    def show(self, image: Image.Image) -> None:
        stamp = dt.datetime.now().strftime("%Y%m%d_%H%M%S")
        path = self.out / f"frame_{stamp}.png"
        image.convert("1").save(path)
        (self.out / "latest.png").write_bytes(path.read_bytes())
        self.last_path = path
        print(f"[mock display] 저장: {path}")
