import numpy as np
from PIL import Image

from aiframe.config import ImagingConfig
from aiframe.display.epd42 import image_to_buffer
from aiframe.image_gen import mock_image
from aiframe.imaging import dither_floyd_steinberg, process
from aiframe.weather import WeatherInfo


def test_fs_dither_is_binary_and_preserves_mean():
    gray = np.full((40, 40), 100, dtype=np.float32)
    out = dither_floyd_steinberg(gray)
    assert set(np.unique(out)) <= {0, 255}
    # 평균 밝기(100)가 대략 유지되어야 오차 확산이 제대로 된 것
    assert abs(out.mean() - 100) < 10


def test_process_outputs_1bit_400x300_and_15000_byte_buffer():
    w = WeatherInfo("clear", "맑음", 12, 40, "morning", "서울")
    cfg = ImagingConfig(dither="floyd-steinberg", overlay=True, font_path="")
    frame = process(mock_image("x"), w, cfg, 400, 300)
    assert frame.mode == "1"
    assert frame.size == (400, 300)
    assert len(image_to_buffer(frame, 400, 300)) == 15000
