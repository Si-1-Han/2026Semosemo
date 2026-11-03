"""AI 전자액자 진입점.

    python -m aiframe --once          # 한 번만 실행
    python -m aiframe                 # interval_minutes 간격으로 반복
    python -m aiframe --display mock  # 하드웨어 없이 PNG로 저장

전체 흐름: 설정 -> 날씨 -> 프롬프트 -> 이미지 생성 -> 영상처리 -> 디스플레이
"""
from __future__ import annotations

import argparse
import json
import logging
import time
from pathlib import Path

from .config import load_config
from .display import create_display
from .image_gen import generate_image
from .imaging import process
from .prompt import build_prompt
from .weather import fetch_weather

log = logging.getLogger("aiframe")


def run_once(cfg, display) -> None:
    weather = fetch_weather(cfg.location, cfg.weather)
    log.info("날씨: %s", weather)

    prompt, scene = build_prompt(weather)
    log.info("프롬프트: %s", prompt)

    raw = generate_image(prompt, cfg.image_gen)
    out = Path(cfg.output_dir)
    out.mkdir(parents=True, exist_ok=True)
    raw.save(out / "latest_raw.png")

    frame = process(raw, weather, cfg.imaging, cfg.display.width, cfg.display.height)
    frame.save(out / "latest_frame.png")
    (out / "latest_meta.json").write_text(
        json.dumps({"scene": scene, "prompt": prompt, "weather": weather.__dict__},
                   ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    display.show(frame)
    log.info("표시 완료")


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="세모세모 AI 전자액자")
    parser.add_argument("--config", help="설정 파일 경로 (기본: config/config.yaml)")
    parser.add_argument("--once", action="store_true", help="한 번만 실행하고 종료")
    parser.add_argument("--display", choices=["epd42", "mock"], help="디스플레이 드라이버 덮어쓰기")
    parser.add_argument("-v", "--verbose", action="store_true")
    args = parser.parse_args(argv)

    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
    )

    cfg = load_config(args.config)
    if args.display:
        cfg.display.driver = args.display

    with create_display(cfg.display, cfg.output_dir) as display:
        while True:
            try:
                run_once(cfg, display)
            except Exception:  # 네트워크 오류 등이 나도 액자는 계속 돌아가야 함
                log.exception("갱신 실패 — 다음 주기에 다시 시도")
            if args.once:
                break
            time.sleep(cfg.interval_minutes * 60)


if __name__ == "__main__":
    main()
