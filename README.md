# 2026Semosemo — 날씨 기반 AI 전자액자

> 컴퓨터구조론 조별 프로젝트 · 팀 **세모세모**

라즈베리파이 4B와 4.2인치 E-Paper(400×300, 흑백)로 만드는 전자액자입니다.
설정한 지역의 날씨를 받아 오고, 그 날씨와 시간대에 맞는 풍경을 AI가 **흑백 펜화 스타일**로 그립니다.
그림은 디더링을 거쳐 액자에 표시되고, 일정 간격으로 새 그림으로 바뀝니다.

```
config.yaml ─► 날씨 API ─► 프롬프트 생성 ─► 이미지 생성 API ─► 영상처리(디더링) ─► SPI ─► E-Paper
 (지역)       (OpenWeather)  (날씨+시간+랜덤풍경)   (OpenAI)        (400x300 1bit)          (SSD1683)
```

## 팀 구성

| 이름 | 역할 | 담당 코드 |
|---|---|---|
| 전성재 (조장) | 하드웨어·디스플레이 | `src/aiframe/display/`, `scripts/test_display.py`, 액자 제작 |
| 한시원 | 백엔드·AI 파이프라인 | `config.py`, `weather.py`, `prompt.py`, `image_gen.py`, `main.py` |
| 채성우 | 영상처리 | `imaging.py` (리사이즈, 대비, 디더링, 문구 오버레이) |

## 폴더 구조

```
2026Semosemo/
├─ src/aiframe/
│  ├─ main.py          # 진입점, 전체 흐름 + 주기 실행
│  ├─ config.py        # config.yaml / .env 로딩
│  ├─ weather.py       # 날씨 API
│  ├─ prompt.py        # 프롬프트 생성 (날씨 + 시간대 + 랜덤 풍경)
│  ├─ image_gen.py     # 이미지 생성 API (OpenAI / mock)
│  ├─ imaging.py       # 리사이즈 · 디더링 · 오버레이
│  └─ display/
│     ├─ base.py       # 디스플레이 인터페이스
│     ├─ epd42.py      # WeAct 4.2" E-Paper SPI 드라이버 (SSD1683)
│     └─ mock.py       # PNG 저장용 가짜 디스플레이
├─ config/config.example.yaml
├─ scripts/install_rpi.sh, test_display.py
├─ systemd/aiframe.service
├─ tests/
└─ docs/  (계획서, 배선도, 협업 규칙)
```

## 빠른 시작

### PC에서 개발 (하드웨어 없이)
```bash
python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements-dev.txt
pip install -e .
cp config/config.example.yaml config/config.yaml
cp .env.example .env               # API 키 입력 (비워 두면 mock 데이터로 동작)

python -m aiframe --once --display mock   # output/latest_frame.png 생성
pytest
```

### 라즈베리파이 4B
```bash
git clone https://github.com/Si-1-Han/2026Semosemo.git
cd 2026Semosemo
bash scripts/install_rpi.sh
.venv/bin/python scripts/test_display.py   # 배선 확인용 테스트 패턴
.venv/bin/python -m aiframe --once         # 실제 1회 실행
```
배선은 [docs/WIRING.md](docs/WIRING.md)를 참고하세요.

## 하드웨어

- Raspberry Pi 4B
- [WeAct Studio 4.2" E-Paper 모듈 (흑백)](https://www.openidea.co.kr/goods/details?goodsId=55400): 400×300, SSD1683, SPI
- 점퍼 케이블, 5V 3A 전원, 액자 프레임

## 문서

- [프로젝트 계획서](docs/PROPOSAL.md)
- [배선도](docs/WIRING.md)
- [협업 규칙](docs/CONTRIBUTING.md)
