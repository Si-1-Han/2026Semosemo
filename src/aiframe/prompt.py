"""프롬프트 생성 모듈.

날씨 + 시간대 + 무작위 풍경을 조합해 '흑백 펜화' 스타일 프롬프트를 만든다.
E-Paper는 흑백 1비트라서, 처음부터 펜화/판화 스타일로 생성해야
디더링 후에도 형태가 잘 살아난다.

담당: 한시원
"""
from __future__ import annotations

import random

from .weather import WeatherInfo

LANDSCAPES = [
    "a mountain range with a winding trail",
    "a quiet seaside with rocks and waves",
    "a small Korean hanok village",
    "a dense pine forest",
    "a calm lake with a wooden pier",
    "a city skyline seen from a hill",
    "rolling farm fields with a lone tree",
    "a narrow alley with old houses",
    "a riverside path with willow trees",
    "a lighthouse on a cliff",
]

WEATHER_PHRASES = {
    "clear": "under a clear sky with crisp sunlight and sharp shadows",
    "clouds": "under a sky full of layered clouds",
    "rain": "in steady rain, with wet ground and puddles reflecting light",
    "drizzle": "in light drizzle and soft mist",
    "thunderstorm": "during a thunderstorm with dramatic clouds and a lightning bolt",
    "snow": "covered in fresh snow while snowflakes fall",
    "fog": "wrapped in thick fog that fades distant shapes",
}

TIME_PHRASES = {
    "dawn": "at dawn, the sun just rising on the horizon",
    "morning": "in the bright morning",
    "afternoon": "in the afternoon",
    "evening": "at sunset with long shadows",
    "night": "at night with a moon and stars",
}

STYLE = (
    "black and white pen and ink illustration, fine cross-hatching, "
    "high contrast, clean white background areas, no color, no gray wash, "
    "no text, no letters, landscape composition, 4:3 aspect ratio"
)


def build_prompt(weather: WeatherInfo, rng: random.Random | None = None) -> tuple[str, str]:
    """(프롬프트, 선택된 풍경)을 반환한다."""
    rng = rng or random.Random()
    scene = rng.choice(LANDSCAPES)
    weather_phrase = WEATHER_PHRASES.get(weather.condition, WEATHER_PHRASES["clouds"])
    time_phrase = TIME_PHRASES.get(weather.time_of_day, "")
    prompt = f"{scene}, {weather_phrase}, {time_phrase}. Style: {STYLE}."
    return prompt, scene
