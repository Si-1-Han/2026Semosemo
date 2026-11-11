import random

from aiframe.prompt import LANDSCAPES, build_prompt
from aiframe.weather import WeatherInfo, condition_from_kma_code


def _w(cond="rain", tod="night"):
    return WeatherInfo(cond, "비", 10.0, 80, tod, "서울")


def test_prompt_contains_weather_time_and_style():
    prompt, scene = build_prompt(_w(), random.Random(0))
    assert scene in LANDSCAPES
    assert "rain" in prompt
    assert "night" in prompt
    assert "pen and ink" in prompt


def test_kma_weather_code_mapping():
    assert condition_from_kma_code(45) == "fog"
    assert condition_from_kma_code(55) == "drizzle"
    assert condition_from_kma_code(65) == "rain"
    assert condition_from_kma_code(75) == "snow"
    assert condition_from_kma_code(95) == "thunderstorm"
    assert condition_from_kma_code(-9, cloud_amount=1) == "clear"
    assert condition_from_kma_code(-9, cloud_amount=8) == "clouds"
