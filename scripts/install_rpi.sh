#!/usr/bin/env bash
# 라즈베리파이 4B 초기 설정 스크립트 (Raspberry Pi OS Bookworm 기준)
#   bash scripts/install_rpi.sh
set -euo pipefail
cd "$(dirname "$0")/.."

echo "[1/5] SPI 활성화"
sudo raspi-config nonint do_spi 0

echo "[2/5] 시스템 패키지 설치 (한글 폰트 포함)"
sudo apt-get update
sudo apt-get install -y python3-venv python3-dev fonts-nanum

echo "[3/5] 가상환경 생성 및 의존성 설치"
python3 -m venv .venv
.venv/bin/pip install --upgrade pip
.venv/bin/pip install -r requirements-rpi.txt
.venv/bin/pip install -e .

echo "[4/5] 설정 파일 준비"
[ -f config/config.yaml ] || cp config/config.example.yaml config/config.yaml
[ -f .env ] || cp .env.example .env

echo "[5/5] 완료"
echo "  - .env 에 API 키를 입력하세요"
echo "  - config/config.yaml 에서 지역을 설정하세요"
echo "  - 화면 테스트: .venv/bin/python scripts/test_display.py"
echo "  - 한 번 실행:  .venv/bin/python -m aiframe --once"
