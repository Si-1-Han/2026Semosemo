# 배선도 — WeAct 4.2" E-Paper ↔ Raspberry Pi 4B

WeAct 공식 라즈베리파이 예제와 같은 핀 배치입니다.

| E-Paper 핀 | 기능 | Pi 물리 핀 | BCM |
|---|---|---|---|
| VCC | 전원 3.3V | 1 | 3V3 |
| GND | 접지 | 6 | GND |
| SDA | SPI MOSI | 19 | GPIO10 |
| SCL | SPI SCLK | 23 | GPIO11 |
| CS | SPI 칩 선택 | 24 | GPIO8 (CE0) |
| D/C | 명령/데이터 선택 | 22 | GPIO25 |
| RES | 리셋 | 11 | GPIO17 |
| BUSY | 작업 중 신호 | 18 | GPIO24 |

> ⚠️ VCC는 반드시 **3.3V**(1번 핀)에 연결합니다.

## 동작 원리 (컴퓨터구조 관점)

- **SPI 통신**: Pi(마스터)가 SCLK에 맞춰 MOSI로 한 비트씩 보냅니다. CS가 LOW일 때만 모듈이 신호를 받습니다.
- **D/C 핀**: LOW면 보내는 바이트를 *명령(레지스터 주소)* 으로, HIGH면 *데이터* 로 해석합니다.
- **BUSY 핀**: 컨트롤러(SSD1683)가 화면을 갱신하는 동안 HIGH가 됩니다. 소프트웨어가 이 핀을 폴링하며 기다립니다.
- **프레임버퍼**: 400×300 픽셀을 1비트로 표현하면 15,000바이트입니다. 가로 50바이트 × 세로 300줄로 RAM(0x24)에 순서대로 씁니다.
- **쌍안정성**: E-Paper는 전원을 끊어도 마지막 화면이 유지됩니다. 그래서 갱신 후 deep sleep으로 전력을 거의 쓰지 않습니다.

## 확인 방법
```bash
sudo raspi-config nonint do_spi 0   # SPI 켜기
ls /dev/spidev0.*                    # spidev0.0 이 보여야 함
python scripts/test_display.py       # 체커보드 테스트 패턴 출력
```
