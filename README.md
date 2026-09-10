# 매일 투자 뉴스 브리핑 → 카카오톡

매일 아침 국내(네이버)·해외(Google News) 경제 뉴스를 수집해 Gemini로 중복 제거·번역·요약·선별한 뒤,
투자 참고용 핵심 뉴스 상위 N건(기본 10건)을 카카오톡 "나에게 보내기"로 전송합니다.
GitHub Actions 스케줄로 완전 자동 실행됩니다.

## 동작 흐름

1. 네이버 검색 API(뉴스)로 `NAVER_QUERIES` 키워드별 최신 국내 경제 뉴스 수집
2. Google News RSS로 `GOOGLE_NEWS_QUERIES` 키워드별 최근 24시간 해외 경제 뉴스 수집
3. Gemini(`GEMINI_MODEL`, 기본 `gemini-2.5-flash`)가 두 목록을 합쳐서
   - 중복/유사 기사 통합
   - 투자와 무관한 기사 제외
   - 해외 기사 한국어 번역
   - 각 기사 2~3문장 한국어 요약
   - 중요도 순 상위 `TOP_N`(기본 10)건 선별
4. 카카오톡 "나에게 보내기" API로 헤더 메시지 1건 + 기사별 메시지를 순차 발송

## 사전 준비

### 1) 네이버 검색 API (Naver Cloud Platform)

검색 오픈API가 Naver Cloud Platform(NCP)으로 이전되어, 현재는 NCP 콘솔에서 신청합니다.

1. https://console.ncloud.com 에서 "AI·Application Service > Search" (또는 "NAVER 검색") API 신청
2. 신청한 Application의 "인증 정보"에서 Client ID(`X-NCP-APIGW-API-KEY-ID`) / Client Secret(`X-NCP-APIGW-API-KEY`) 확인
   - 예전 developers.naver.com 방식과 키 형태는 비슷하지만, 요청 헤더 이름과 엔드포인트가 다릅니다
     (`src/collectors/naver.py` 참고)

### 2) Gemini API

1. https://aistudio.google.com/apikey 에서 API 키 발급
2. 무료 등급으로도 요약 10건/일 정도는 충분히 커버되지만, 필요 시 Google Cloud 결제 연결로 등급 상향 가능

### 3) 카카오 "나에게 보내기"

1. https://developers.kakao.com 에서 애플리케이션 생성 → REST API 키 확인
2. 내 애플리케이션 > 카카오 로그인 → 활성화 ON
3. 카카오 로그인 > Redirect URI 등록 (예: `https://example.com/oauth`, 실제로 접속 가능한 페이지가
   아니어도 됩니다. 로컬 인증 시 주소창의 code 값만 복사하면 됩니다)
4. 카카오 로그인 > 동의항목 → "카카오톡 메시지 전송"(`talk_message`) 을 "선택 동의" 이상으로 설정
   - 본인 계정에만 보내는 용도이므로 비즈앱 전환/검수는 필요하지 않습니다.
5. 로컬에서 최초 1회 인증 실행:
   ```bash
   cp .env.example .env
   # .env에 KAKAO_REST_API_KEY, KAKAO_REDIRECT_URI 입력
   pip install -r requirements.txt
   python -m scripts.kakao_auth
   ```
   안내되는 URL로 접속 → 카카오 로그인/동의 → 리다이렉트된 주소의 `code=` 값(또는 전체 URL)을
   터미널에 붙여넣으면 `access_token`/`refresh_token`이 출력됩니다.

### 4) GitHub Secrets 등록

저장소 Settings → Secrets and variables → Actions → New repository secret 에 아래 값을 등록하세요.

| Secret 이름 | 값 |
|---|---|
| `NAVER_CLIENT_ID` | 네이버 애플리케이션 Client ID |
| `NAVER_CLIENT_SECRET` | 네이버 애플리케이션 Client Secret |
| `GEMINI_API_KEY` | Gemini API 키 |
| `KAKAO_REST_API_KEY` | 카카오 앱 REST API 키 |
| `KAKAO_REFRESH_TOKEN` | `scripts/kakao_auth.py` 실행 후 발급된 refresh_token |
| `GH_PAT` (선택) | `repo` 권한 Personal Access Token. 카카오 refresh_token이 만료 임박 시 자동 회전되는데, 이 값을 등록해두면 새 토큰을 GitHub Secret에 자동 반영합니다. 없으면 refresh_token이 회전될 때(대략 2달 주기) 수동으로 다시 발급해야 할 수 있습니다. |

선택적으로 Settings → Secrets and variables → Actions → Variables 탭에서 아래 값을 조정할 수 있습니다
(등록하지 않으면 기본값 사용):

| Variable 이름 | 기본값 | 설명 |
|---|---|---|
| `GEMINI_MODEL` | `gemini-2.5-flash` | 사용할 Gemini 모델 |
| `NAVER_QUERIES` | `경제,증시,코스피,금리,환율,부동산,수출입` | 국내 뉴스 검색 키워드(쉼표 구분) |
| `GOOGLE_NEWS_QUERIES` | `economy,stock market,federal reserve,inflation,interest rates` | 해외 뉴스 검색 키워드(쉼표 구분) |
| `TOP_N` | `10` | 최종 발송 뉴스 개수 |

## 실행 스케줄

`.github/workflows/daily-news.yml` 기본값은 매일 07:30 KST(UTC 22:30 전날)입니다.
다른 시간을 원하면 워크플로우 파일의 `cron` 표현식을 수정하세요(cron은 UTC 기준).

수동 실행: 저장소 Actions 탭 → "Daily Investment News Briefing" → Run workflow

## 로컬 테스트

```bash
cp .env.example .env  # 값 채우기
pip install -r requirements.txt
python -m src.main
```

## 커스터마이징

- 검색 키워드: `.env`(로컬) 또는 GitHub Variables `NAVER_QUERIES` / `GOOGLE_NEWS_QUERIES`
- 요약/선별 기준: `src/summarizer.py`의 `SYSTEM_PROMPT`
- 카카오 메시지 길이/형식: `src/kakao.py`의 `KAKAO_TEXT_MAX_LEN`, `send_briefing`
- 실행 시각: `.github/workflows/daily-news.yml`의 `cron`

## 알려진 제약

- 네이버 검색 API는 기사 본문 전체가 아닌 제목/요약(snippet)만 제공합니다. 따라서 요약 품질은
  검색 결과 스니펫 수준에 의존합니다. 더 깊은 요약이 필요하면 기사 원문 크롤링을 추가해야 하며,
  이 경우 각 언론사 이용약관을 확인해야 합니다.
- Google News RSS는 비공식 피드로, 향후 변경/중단될 수 있습니다.
- 카카오 "나에게 보내기" 기본 `text` 템플릿은 글자 수 제한이 있어 요약이 길면 잘릴 수 있습니다
  (`KAKAO_TEXT_MAX_LEN`으로 조정).
- Gemini API 호출 비용이 발생할 수 있습니다(무료 등급 한도를 넘으면 사용량에 따라 과금).
