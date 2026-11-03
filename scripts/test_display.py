"""E-Paper 배선 확인용 테스트 패턴 출력 (AI/날씨 API 없이 동작).

    python scripts/test_display.py            # 실제 E-Paper
    python scripts/test_display.py --mock     # PNG로 저장
"""
import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from PIL import Image, ImageDraw  # noqa: E402

from aiframe.config import load_config  # noqa: E402
from aiframe.display import create_display  # noqa: E402


def test_pattern(w: int, h: int) -> Image.Image:
    img = Image.new("1", (w, h), 1)
    d = ImageDraw.Draw(img)
    d.rectangle([0, 0, w - 1, h - 1], outline=0, width=3)
    d.line([(0, 0), (w, h)], fill=0, width=2)
    d.line([(0, h), (w, 0)], fill=0, width=2)
    for i in range(8):  # 체커보드
        for j in range(4):
            if (i + j) % 2 == 0:
                d.rectangle([20 + i * 20, 20 + j * 20, 39 + i * 20, 39 + j * 20], fill=0)
    d.text((20, h - 40), "SEMOSEMO E-PAPER TEST 400x300", fill=0)
    return img


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--mock", action="store_true")
    args = ap.parse_args()
    cfg = load_config()
    if args.mock:
        cfg.display.driver = "mock"
    with create_display(cfg.display, cfg.output_dir) as disp:
        disp.show(test_pattern(cfg.display.width, cfg.display.height))
    print("완료")
