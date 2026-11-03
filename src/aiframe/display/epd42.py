"""WeAct Studio 4.2인치 E-Paper(SSD1683, 400x300, 흑백) SPI 드라이버.

WeAct 공식 라즈베리파이 예제(epaper.c)의 EPD420 초기화 순서를 Python으로 옮긴 것.
https://github.com/WeActStudio/WeActStudio.EpaperModule

배선 (BCM 번호 / 물리 핀)
    RES  -> GPIO17 / 11      BUSY -> GPIO24 / 18
    D/C  -> GPIO25 / 22      CS   -> CE0    / 24
    SCK  -> SCLK   / 23      SDA  -> MOSI   / 19
    VCC  -> 3.3V   / 1       GND  -> GND    / 6

컴퓨터구조 관점 포인트
  - 프레임버퍼: 400x300 픽셀 x 1bit = 15,000 바이트 (가로 50바이트 x 세로 300줄)
  - D/C 핀이 LOW면 명령(레지스터 주소), HIGH면 데이터로 해석된다.
  - BUSY 핀이 HIGH인 동안 컨트롤러가 작업 중이므로 폴링으로 기다린다.

담당: 전성재
"""
from __future__ import annotations

import time

from PIL import Image

from .base import Display
from ..config import DisplayConfig

# SSD1683 명령어
CMD_DRIVER_OUTPUT = 0x01
CMD_DEEP_SLEEP = 0x10
CMD_DATA_ENTRY = 0x11
CMD_SW_RESET = 0x12
CMD_TEMP_SENSOR = 0x18
CMD_MASTER_ACTIVATE = 0x20
CMD_UPDATE_CTRL1 = 0x21
CMD_UPDATE_CTRL2 = 0x22
CMD_WRITE_RAM_BW = 0x24
CMD_WRITE_RAM_RED = 0x26
CMD_BORDER = 0x3C
CMD_RAM_X_RANGE = 0x44
CMD_RAM_Y_RANGE = 0x45
CMD_RAM_X_COUNTER = 0x4E
CMD_RAM_Y_COUNTER = 0x4F

SPI_CHUNK = 4096


class EPD42(Display):
    def __init__(self, cfg: DisplayConfig):
        import spidev
        from gpiozero import DigitalInputDevice, DigitalOutputDevice

        self.width, self.height = cfg.width, cfg.height
        self.rotate = cfg.rotate
        self.rst = DigitalOutputDevice(cfg.pin_rst, initial_value=True)
        self.dc = DigitalOutputDevice(cfg.pin_dc, initial_value=True)
        self.busy = DigitalInputDevice(cfg.pin_busy, pull_up=False)

        self.spi = spidev.SpiDev()
        self.spi.open(cfg.spi_bus, cfg.spi_device)
        self.spi.max_speed_hz = cfg.spi_speed_hz
        self.spi.mode = cfg.spi_mode

        self._sleeping = True

    # --- 저수준 SPI/GPIO --------------------------------------------------
    def _command(self, cmd: int, *data: int) -> None:
        self.dc.off()
        self.spi.writebytes([cmd])
        self.dc.on()
        if data:
            self.spi.writebytes(list(data))

    def _data_bulk(self, buf: bytes) -> None:
        self.dc.on()
        for i in range(0, len(buf), SPI_CHUNK):
            self.spi.writebytes2(buf[i:i + SPI_CHUNK])

    def _wait_busy(self, timeout_s: float = 40.0) -> None:
        start = time.monotonic()
        while self.busy.value:
            if time.monotonic() - start > timeout_s:
                raise TimeoutError("E-Paper BUSY 대기 시간 초과")
            time.sleep(0.005)

    def _reset(self) -> None:
        self.rst.off()
        time.sleep(0.05)
        self.rst.on()
        time.sleep(0.05)
        self._sleeping = False

    # --- 초기화 -----------------------------------------------------------
    def init(self) -> None:
        if self._sleeping:
            self._reset()
        self._wait_busy()
        self._command(CMD_SW_RESET)
        time.sleep(0.1)
        self._wait_busy()

        self._command(CMD_UPDATE_CTRL1, 0x40, 0x00)
        self._command(CMD_DRIVER_OUTPUT, 0x2B, 0x01, 0x00)  # MUX = 300 줄
        self._command(CMD_BORDER, 0x01)
        self._command(CMD_DATA_ENTRY, 0x03)  # X 증가 -> Y 증가
        self._set_window(0, 0, self.width - 1, self.height - 1)
        self._command(CMD_TEMP_SENSOR, 0x80)  # 내장 온도 센서 사용
        self._set_cursor(0, 0)

        # 전원 켜기
        self._command(CMD_UPDATE_CTRL2, 0xE0)
        self._command(CMD_MASTER_ACTIVATE)
        self._wait_busy()

    def _set_window(self, x0: int, y0: int, x1: int, y1: int) -> None:
        self._command(CMD_RAM_X_RANGE, (x0 >> 3) & 0xFF, (x1 >> 3) & 0xFF)
        self._command(CMD_RAM_Y_RANGE, y0 & 0xFF, (y0 >> 8) & 0xFF, y1 & 0xFF, (y1 >> 8) & 0xFF)

    def _set_cursor(self, x: int, y: int) -> None:
        self._command(CMD_RAM_X_COUNTER, (x >> 3) & 0xFF)
        self._command(CMD_RAM_Y_COUNTER, y & 0xFF, (y >> 8) & 0x01)

    # --- 프레임버퍼 변환 ---------------------------------------------------
    def to_buffer(self, image: Image.Image) -> bytes:
        """PIL 이미지 -> SSD1683 RAM 형식(1=흰색, 0=검정, MSB가 왼쪽 픽셀)."""
        return image_to_buffer(image, self.width, self.height, self.rotate)

    # --- 표시 -------------------------------------------------------------
    def show(self, image: Image.Image) -> None:
        buf = self.to_buffer(image)
        self.init()
        # 흑백 모드에서는 이전/현재 RAM에 같은 데이터를 써서 잔상 없이 전체 갱신
        self._set_cursor(0, 0)
        self._command(CMD_WRITE_RAM_RED)
        self._data_bulk(buf)
        self._set_cursor(0, 0)
        self._command(CMD_WRITE_RAM_BW)
        self._data_bulk(buf)

        self._command(CMD_UPDATE_CTRL2, 0xF7)  # 전체 갱신
        self._command(CMD_MASTER_ACTIVATE)
        self._wait_busy()
        self.sleep()

    def sleep(self) -> None:
        if self._sleeping:
            return
        self._command(CMD_UPDATE_CTRL2, 0x83)  # 전원 끄기
        self._command(CMD_MASTER_ACTIVATE)
        self._wait_busy()
        self._command(CMD_DEEP_SLEEP, 0x01)
        self._sleeping = True

    def close(self) -> None:
        try:
            self.sleep()
        finally:
            self.spi.close()
            self.rst.close()
            self.dc.close()
            self.busy.close()


def image_to_buffer(image: Image.Image, width: int, height: int, rotate: int = 0) -> bytes:
    """하드웨어 없이도 테스트할 수 있도록 분리한 프레임버퍼 변환 함수."""
    if rotate:
        image = image.rotate(rotate, expand=True)
    if image.size != (width, height):
        raise ValueError(f"이미지 크기 {image.size} != 디스플레이 {(width, height)}")
    buf = image.convert("1").tobytes()  # PIL '1' 모드: 1=흰색, MSB first
    assert len(buf) == width * height // 8
    return buf
