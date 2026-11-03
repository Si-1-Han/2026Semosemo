"""영상처리 모듈.

AI가 만든 컬러 이미지를 400x300 1비트 흑백 이미지로 바꾼다.
  1) 4:3 비율로 중앙 크롭 후 리사이즈
  2) 그레이스케일 + 대비 보정
  3) 디더링 (Floyd–Steinberg / Atkinson / 단순 임계값)
  4) 날짜·지역·기온 문구 오버레이

담당: 채성우
"""
from __future__ import annotations

import datetime as dt
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageEnhance, ImageFont, ImageOps

from .config import ImagingConfig
from .weather import WeatherInfo


def fit_to_display(img: Image.Image, width: int, height: int) -> Image.Image:
    """비율을 유지하며 중앙을 잘라 디스플레이 크기에 맞춘다."""
    return ImageOps.fit(img, (width, height), method=Image.Resampling.LANCZOS)


def to_gray(img: Image.Image, contrast: float = 1.0) -> np.ndarray:
    gray = img.convert("L")
    if contrast != 1.0:
        gray = ImageEnhance.Contrast(gray).enhance(contrast)
    return np.asarray(gray, dtype=np.float32)


# ---------------------------------------------------------------------------
# 디더링 알고리즘 — 오차 확산 방식
# ---------------------------------------------------------------------------

def dither_threshold(gray: np.ndarray, threshold: float = 128) -> np.ndarray:
    return (gray >= threshold).astype(np.uint8) * 255


def dither_floyd_steinberg(gray: np.ndarray) -> np.ndarray:
    """Floyd–Steinberg 오차 확산.

    현재 픽셀을 0/255로 양자화하고, 생긴 오차를 이웃 픽셀에
        오른쪽 7/16, 왼쪽아래 3/16, 아래 5/16, 오른쪽아래 1/16
    비율로 나눠 준다.
    """
    img = gray.astype(np.float32).copy()
    h, w = img.shape
    for y in range(h):
        row = img[y]
        nxt = img[y + 1] if y + 1 < h else None
        for x in range(w):
            old = row[x]
            new = 255.0 if old >= 128 else 0.0
            row[x] = new
            err = old - new
            if x + 1 < w:
                row[x + 1] += err * 7 / 16
            if nxt is not None:
                if x > 0:
                    nxt[x - 1] += err * 3 / 16
                nxt[x] += err * 5 / 16
                if x + 1 < w:
                    nxt[x + 1] += err * 1 / 16
    return np.clip(img, 0, 255).astype(np.uint8)


def dither_atkinson(gray: np.ndarray) -> np.ndarray:
    """Atkinson 디더링: 오차의 6/8만 확산해 대비가 더 강하다 (초기 맥킨토시 방식)."""
    img = gray.astype(np.float32).copy()
    h, w = img.shape
    offsets = [(1, 0), (2, 0), (-1, 1), (0, 1), (1, 1), (0, 2)]
    for y in range(h):
        for x in range(w):
            old = img[y, x]
            new = 255.0 if old >= 128 else 0.0
            img[y, x] = new
            err = (old - new) / 8
            for dx, dy in offsets:
                nx, ny = x + dx, y + dy
                if 0 <= nx < w and ny < h:
                    img[ny, nx] += err
    return np.clip(img, 0, 255).astype(np.uint8)


DITHERERS = {
    "floyd-steinberg": dither_floyd_steinberg,
    "atkinson": dither_atkinson,
    "threshold": dither_threshold,
}


def dither(gray: np.ndarray, method: str = "floyd-steinberg") -> Image.Image:
    try:
        fn = DITHERERS[method]
    except KeyError as e:
        raise ValueError(f"알 수 없는 디더링 방식: {method}") from e
    return Image.fromarray(fn(gray)).convert("1", dither=Image.Dither.NONE)


# ---------------------------------------------------------------------------
# 문구 오버레이
# ---------------------------------------------------------------------------

def _load_font(path: str, size: int) -> ImageFont.ImageFont:
    if path and Path(path).exists():
        return ImageFont.truetype(path, size)
    return ImageFont.load_default()


def draw_overlay(img: Image.Image, weather: WeatherInfo, font_path: str,
                 now: dt.datetime | None = None) -> Image.Image:
    """하단에 흰 띠를 깔고 날짜·지역·기온을 검은 글씨로 쓴다."""
    now = now or dt.datetime.now()
    img = img.copy()
    draw = ImageDraw.Draw(img)
    w, h = img.size
    bar_h = 26
    draw.rectangle([0, h - bar_h, w, h], fill=255)
    draw.line([(0, h - bar_h), (w, h - bar_h)], fill=0)
    font = _load_font(font_path, 16)
    left = now.strftime("%m/%d %H:%M")
    right = f"{weather.location_label} {weather.description} {weather.temp_c:.0f}°C"
    draw.text((6, h - bar_h + 4), left, fill=0, font=font)
    rw = draw.textlength(right, font=font)
    draw.text((w - rw - 6, h - bar_h + 4), right, fill=0, font=font)
    return img


def process(img: Image.Image, weather: WeatherInfo, cfg: ImagingConfig,
            width: int, height: int) -> Image.Image:
    """전체 영상처리 파이프라인. 결과는 PIL '1' 모드(1비트) 이미지."""
    fitted = fit_to_display(img, width, height)
    gray = to_gray(fitted, cfg.contrast)
    bw = dither(gray, cfg.dither)
    if cfg.overlay:
        bw = draw_overlay(bw, weather, cfg.font_path)
    return bw
