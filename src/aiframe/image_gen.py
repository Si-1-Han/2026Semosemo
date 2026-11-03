"""이미지 생성 API 연동 모듈.

기본은 OpenAI 이미지 API(gpt-image-1)를 쓴다.
API 키가 없거나 provider가 mock이면 테스트용 이미지를 만든다.

담당: 한시원
"""
from __future__ import annotations

import base64
import io

from PIL import Image, ImageDraw

from .config import ImageGenConfig


def generate_image(prompt: str, cfg: ImageGenConfig) -> Image.Image:
    if cfg.provider == "mock" or not cfg.api_key:
        return mock_image(prompt)
    if cfg.provider == "openai":
        return _generate_openai(prompt, cfg)
    raise ValueError(f"지원하지 않는 image_gen.provider: {cfg.provider}")


def _generate_openai(prompt: str, cfg: ImageGenConfig) -> Image.Image:
    from openai import OpenAI  # 필요할 때만 import

    client = OpenAI(api_key=cfg.api_key)
    result = client.images.generate(
        model=cfg.model,
        prompt=prompt,
        size=cfg.size,
        quality=cfg.quality,
        n=1,
    )
    data = base64.b64decode(result.data[0].b64_json)
    return Image.open(io.BytesIO(data)).convert("RGB")


def mock_image(prompt: str, size: tuple[int, int] = (800, 600)) -> Image.Image:
    """API 없이 파이프라인을 시험하기 위한 그라데이션 산 풍경."""
    w, h = size
    img = Image.new("RGB", size)
    draw = ImageDraw.Draw(img)
    for y in range(h):  # 하늘 그라데이션
        v = int(230 - 120 * y / h)
        draw.line([(0, y), (w, y)], fill=(v, v, min(255, v + 20)))
    draw.ellipse([w * 0.7, h * 0.1, w * 0.85, h * 0.3], fill=(255, 255, 240))  # 해
    draw.polygon([(0, h), (w * 0.3, h * 0.35), (w * 0.6, h)], fill=(70, 70, 70))
    draw.polygon([(w * 0.35, h), (w * 0.7, h * 0.45), (w, h)], fill=(110, 110, 110))
    draw.rectangle([0, h * 0.85, w, h], fill=(40, 40, 40))
    return img
