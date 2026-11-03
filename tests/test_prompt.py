import random

from aiframe.prompt import LANDSCAPES, build_prompt
from aiframe.weather import WeatherInfo, condition_from_owm_id


def _w(cond="rain", tod="night"):
    return WeatherInfo(cond, "비", 10.0, 80, tod, "서울")


def test_prompt_contains_weather_time_and_style():
    prompt, scene = build_prompt(_w(), random.Random(0))
    assert scene in LANDSCAPES
    assert "rain" in prompt
    assert "night" in prompt
    assert "pen and ink" in prompt


def test_owm_id_mapping():
    assert condition_from_owm_id(211) == "thunderstorm"
    assert condition_from_owm_id(501) == "rain"
    assert condition_from_owm_id(601) == "snow"
    assert condition_from_owm_id(741) == "fog"
    assert condition_from_owm_id(800) == "clear"
    assert condition_from_owm_id(803) == "clouds"
