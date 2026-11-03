# 협업 규칙

## 브랜치
- `main`: 항상 동작하는 상태 유지. 직접 push하지 말고 PR로 합칩니다.
- 작업 브랜치: `feature/<담당>-<내용>`
  - 예) `feature/display-partial-refresh`, `feature/weather-kma`, `feature/imaging-atkinson`

## 커밋 메시지
```
<type>: <내용>

type: feat(기능) | fix(버그) | docs(문서) | refactor | test | chore
예) feat: 날씨 API 재시도 로직 추가
```

## PR 규칙
1. PR을 올리기 전에 `pytest`와 `python -m aiframe --once --display mock`이 통과하는지 확인합니다.
2. 다른 팀원 1명 이상이 리뷰한 뒤 merge합니다.
3. 담당 모듈 밖의 파일을 고쳤다면 PR 설명에 이유를 적습니다.

## 비밀 정보
- API 키는 `.env`에만 넣습니다. `.env`와 `config/config.yaml`은 `.gitignore`에 들어 있습니다.
- 실수로 키를 커밋했다면 즉시 키를 재발급하세요.

## 모듈 경계 (인터페이스)
| 함수 | 입력 | 출력 |
|---|---|---|
| `weather.fetch_weather` | 지역 설정 | `WeatherInfo` |
| `prompt.build_prompt` | `WeatherInfo` | 프롬프트 문자열 |
| `image_gen.generate_image` | 프롬프트 | 컬러 `PIL.Image` |
| `imaging.process` | 컬러 이미지, `WeatherInfo` | 400×300 1비트 `PIL.Image` |
| `display.show` | 1비트 이미지 | 화면 출력 |

이 인터페이스만 지키면 각자 모듈 안쪽은 자유롭게 바꿔도 됩니다.
