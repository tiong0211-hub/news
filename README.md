# 매일 경제 뉴스 브리핑 → 카카오톡

매일 아침 국내(네이버)·해외(WSJ/FT/Nikkei Asia 공식 RSS)의 **당일 발행** 경제 뉴스를 **신뢰 언론사 목록**에서만
수집해 OpenAI로 중복 제거·번역·요약·선별한 뒤, 예쁘게 정리된 뉴스레터 페이지를 GitHub Pages에
발행하고 카카오톡 "나에게 보내기"로 그 링크 1건을 전송합니다. GitHub Actions 스케줄로 완전 자동
실행됩니다.

## 동작 흐름

1. 네이버 검색 API(뉴스)로 `NAVER_QUERIES` 키워드별 국내 경제 뉴스 수집 → `DOMESTIC_SOURCE_DOMAINS`
   언론사 + 오늘(KST) 발행분만 필터링
2. `FOREIGN_SOURCE_DOMAINS`에 매핑된 각 언론사(WSJ/FT/Nikkei Asia)의 공식 RSS 피드에서 수집
   → 오늘(KST) 발행분만 필터링
3. OpenAI(`OPENAI_MODEL`, 기본 `gpt-4o-mini`)가 두 목록을 합쳐서
   - 중복/유사 기사 통합
   - 투자와 무관한 기사 제외
   - 해외 기사 한국어 번역
   - 각 기사 2~3문장 한국어 요약
   - 중요도 순 상위 `TOP_N`(기본 10)건 선별
4. 선별 결과를 `docs/archive/YYYY-MM-DD.html`(날짜별 아카이브)과 `docs/index.html`(오늘자 + 최근
   14일 아카이브 링크)로 렌더링 (기사별 제목/요약/출처/발행시각/원문 링크 포함)
5. 14일 지난 아카이브 파일은 자동 삭제, 변경사항을 저장소에 커밋
6. GitHub Pages에 페이지 배포
7. 카카오톡 "나에게 보내기"로 오늘 페이지 링크 1건 발송
8. (선택) `EMAIL_ADDRESS`/`EMAIL_APP_PASSWORD`가 설정되어 있으면, 같은 내용을 이메일로도 발송

## 사전 준비

### 1) 네이버 검색 API (Naver Cloud Platform)

검색 오픈API가 Naver Cloud Platform(NCP)으로 이전되어, 현재는 NCP 콘솔에서 신청합니다.

1. https://console.ncloud.com 에서 "AI·Application Service > Search" (또는 "NAVER 검색") API 신청
2. 신청한 Application의 "인증 정보"에서 Client ID(`X-NCP-APIGW-API-KEY-ID`) / Client Secret(`X-NCP-APIGW-API-KEY`) 확인
   - 예전 developers.naver.com 방식과 키 형태는 비슷하지만, 요청 헤더 이름과 엔드포인트가 다릅니다
     (`src/collectors/naver.py` 참고)

### 2) OpenAI API

1. https://platform.openai.com/api-keys 에서 API 키 발급
2. 결제 수단 등록 (요약 10건/일 기준 비용은 매우 낮은 수준)

### 3) 카카오 "나에게 보내기"

1. https://developers.kakao.com 에서 애플리케이션 생성 → REST API 키 확인
2. 내 애플리케이션 > 카카오 로그인 → 활성화 ON
3. 카카오 로그인 > Redirect URI 등록 (예: `https://example.com/oauth`, 실제로 접속 가능한 페이지가
   아니어도 됩니다. 로컬 인증 시 주소창의 code 값만 복사하면 됩니다)
4. 카카오 로그인 > 동의항목 → "카카오톡 메시지 전송"(`talk_message`) 을 "선택 동의" 이상으로 설정
   - 본인 계정에만 보내는 용도이므로 비즈앱 전환/검수는 필요하지 않습니다.
5. 앱 키 > 클라이언트 시크릿이 "카카오 로그인"에 대해 활성화(ON)되어 있다면 그 코드 값을 메모해두세요
   (아래 `KAKAO_CLIENT_SECRET`에 사용).
6. 로컬에서 최초 1회 인증 실행:
   ```bash
   cp .env.example .env
   # .env에 KAKAO_REST_API_KEY, KAKAO_REDIRECT_URI, (필요시) KAKAO_CLIENT_SECRET 입력
   pip install -r requirements.txt
   python -m scripts.kakao_auth
   ```
   안내되는 URL로 접속 → 카카오 로그인/동의 → 리다이렉트된 주소의 `code=` 값(또는 전체 URL)을
   터미널에 붙여넣으면 `access_token`/`refresh_token`이 출력됩니다.

### 4) (선택) 이메일로도 받기

카카오톡 외에 이메일로도 같은 브리핑을 받고 싶다면 설정하세요. 설정하지 않으면 이 단계는 자동으로
건너뜁니다.

**Gmail 기준:**
1. Google 계정 → 보안 → 2단계 인증 켜기 (필수, 앱 비밀번호는 2단계 인증 활성화 후에만 발급됩니다)
2. Google 계정 → 보안 → 앱 비밀번호(App passwords) → 새로 만들기 → 발급된 16자리 값을 복사
   (일반 로그인 비밀번호가 아닙니다)
3. 아래 GitHub Secrets에 본인 Gmail 주소와 이 앱 비밀번호를 등록

다른 메일 제공자를 쓰신다면 `EMAIL_SMTP_HOST`/`EMAIL_SMTP_PORT`를 해당 제공자의 SMTP 정보로
바꾸고, 해당 제공자의 "앱 비밀번호" 또는 SMTP 인증 정보를 사용하세요.

### 5) GitHub Pages 활성화

저장소 **Settings → Pages → Build and deployment → Source**를 **"GitHub Actions"**로 설정하세요.
(별도 브랜치/폴더 지정 불필요 — 워크플로우가 매일 `docs/` 내용을 직접 배포합니다.)

### 6) GitHub Secrets 등록

저장소 Settings → Secrets and variables → Actions → New repository secret 에 아래 값을 등록하세요.

| Secret 이름 | 값 |
|---|---|
| `NAVER_CLIENT_ID` | 네이버(NCP) Application Client ID |
| `NAVER_CLIENT_SECRET` | 네이버(NCP) Application Client Secret |
| `OPENAI_API_KEY` | OpenAI API 키 |
| `KAKAO_REST_API_KEY` | 카카오 앱 REST API 키 |
| `KAKAO_CLIENT_SECRET` (조건부) | 앱 키 > 클라이언트 시크릿이 "카카오 로그인"에 대해 활성화(ON)된 경우 그 코드 값. 활성화되어 있으면 토큰 발급/갱신 요청에 필수입니다(없으면 `KOE010 Bad client credentials` 에러). |
| `KAKAO_REFRESH_TOKEN` | `scripts/kakao_auth.py` 실행 후 발급된 refresh_token |
| `GH_PAT` (선택) | `repo` 권한 Personal Access Token. 카카오 refresh_token이 만료 임박 시 자동 회전되는데, 이 값을 등록해두면 새 토큰을 GitHub Secret에 자동 반영합니다. 없으면 refresh_token이 회전될 때(대략 2달 주기) 수동으로 다시 발급해야 할 수 있습니다. |
| `EMAIL_ADDRESS` (선택) | 발신용 이메일 주소 (예: Gmail 주소). 비워두면 이메일 발송 자체를 건너뜁니다. |
| `EMAIL_APP_PASSWORD` (선택) | 위 계정의 앱 비밀번호(App password). 일반 로그인 비밀번호가 아닙니다. |

선택적으로 Settings → Secrets and variables → Actions → Variables 탭에서 아래 값을 조정할 수 있습니다
(등록하지 않으면 기본값 사용):

| Variable 이름 | 기본값 | 설명 |
|---|---|---|
| `OPENAI_MODEL` | `gpt-4o-mini` | 사용할 OpenAI 모델 |
| `NAVER_QUERIES` | `경제,증시,코스피,금리,환율,부동산,수출입` | 국내 뉴스 검색 키워드(쉼표 구분) |
| `DOMESTIC_SOURCE_DOMAINS` | `mk.co.kr,hankyung.com,mt.co.kr,heraldcorp.com,biz.chosun.com,fnnews.com` | 국내 신뢰 언론사 도메인(쉼표 구분). 매일경제/한국경제/머니투데이/헤럴드경제/조선비즈/파이낸셜뉴스 |
| `FOREIGN_SOURCE_DOMAINS` | `wsj.com,ft.com,nikkei.com` | 해외 신뢰 언론사 도메인(쉼표 구분). WSJ/FT/닛케이. 각 도메인은 `src/collectors/foreign_news.py`의 `KNOWN_FEEDS`에 등록된 RSS 피드가 있어야 실제로 수집됩니다 |
| `TOP_N` | `10` | 최종 선별 뉴스 개수 |
| `EMAIL_SMTP_HOST` | `smtp.gmail.com` | 이메일 발송용 SMTP 서버 (Gmail이 아니면 변경) |
| `EMAIL_SMTP_PORT` | `587` | SMTP 포트 |
| `EMAIL_TO` | `EMAIL_ADDRESS`와 동일 | 받는 사람 주소. 다른 주소로 받고 싶으면 설정 |

## 실행 스케줄

`.github/workflows/daily-news.yml` 기본값은 **평일(월~금) 08:00 KST**(UTC 기준 일~목 23:00)입니다.
주말은 cron 자체에서 실행되지 않고, **한국 공휴일**(대체공휴일 포함)은 `src/kr_calendar.py`가
스케줄 실행일 때만 판별해서 뉴스 수집/발송을 전부 건너뜁니다(수동 실행은 공휴일이어도 항상 진행).

다른 시간을 원하면 워크플로우 파일의 `cron` 표현식을 수정하세요(cron은 UTC 기준이라, KST 08:00은
전날 UTC 23:00입니다). 요일 제한을 바꾸려면 `cron`의 마지막 필드(`0-4` = 일~목, KST 기준 월~금)를
조정하세요.

수동 실행: 저장소 Actions 탭 → "Daily Investment News Briefing" → Run workflow

## 로컬 테스트

```bash
cp .env.example .env  # 값 채우기
pip install -r requirements.txt
python -m src.build        # docs/index.html 생성 (뉴스 수집 + 요약)
open docs/index.html       # 결과 미리보기 (macOS 기준, 다른 OS는 파일 직접 열기)

# 카카오 발송까지 로컬에서 테스트하려면 GitHub Pages에 해당하는 공개 URL이 필요합니다.
# 임시로 아무 URL(또는 실제로 배포된 이전 페이지 URL)을 넣어 형식만 확인할 수 있습니다.
PAGE_URL="https://example.com" python -m src.send_kakao

# 이메일 발송 테스트 (EMAIL_ADDRESS/EMAIL_APP_PASSWORD를 .env에 설정한 경우)
python -m src.send_email
```

## 커스터마이징

- 국내 검색 키워드: `.env`(로컬) 또는 GitHub Variables `NAVER_QUERIES`
- 신뢰 언론사 목록: `.env`(로컬) 또는 GitHub Variables `DOMESTIC_SOURCE_DOMAINS` / `FOREIGN_SOURCE_DOMAINS`
- 요약/선별 기준: `src/summarizer.py`의 `SYSTEM_PROMPT`
- 뉴스레터 페이지 디자인: `src/newsletter.py`
- 카카오 메시지 문구: `src/kakao.py`의 `send_briefing_link`
- "오늘 발행" 판정 기준: `src/freshness.py`의 `is_today_kst` (KST 기준 달력일 일치)
- 아카이브 보관 기간: `src/build.py`의 `ARCHIVE_RETENTION_DAYS` (기본 14일)
- 주말/공휴일 건너뛰기 로직: `src/kr_calendar.py` (`holidays` 패키지의 한국 공휴일 데이터 사용)
- 실행 시각: `.github/workflows/daily-news.yml`의 `cron`

## 알려진 제약

- 네이버 검색 API는 기사 본문 전체가 아닌 제목/요약(snippet)만 제공합니다. 따라서 요약 품질은
  검색 결과 스니펫 수준에 의존합니다. 더 깊은 요약이 필요하면 기사 원문 크롤링을 추가해야 하며,
  이 경우 각 언론사 이용약관을 확인해야 합니다.
- 해외 뉴스는 각 언론사의 공식 RSS 피드를 사용합니다(Google News의 site: 검색은 실제 링크가 아닌
  news.google.com 리다이렉트만 반환해 사용하지 않음). `FOREIGN_SOURCE_DOMAINS`에 새 언론사를 추가하려면
  `src/collectors/foreign_news.py`의 `KNOWN_FEEDS`에 해당 언론사의 RSS 피드 URL도 함께 등록해야 합니다.
- "오늘 발행" 필터는 각 API/피드가 제공하는 발행일(pubDate)에 의존합니다. 발행일을 파싱할 수 없는
  기사는 안전하게 제외됩니다.
- 언론사 화이트리스트 + 당일 발행 필터를 같이 적용하다 보니, 날에 따라 최종 후보가 적어(심하면 0건)
  선정될 수 있습니다. 후보가 부족하면 `TOP_N`보다 적은 건수만 발송되거나, 아예 발송을 건너뜁니다.
- 카카오 API는 임의의 파일(PDF 등) 첨부를 지원하지 않아, 뉴스레터는 GitHub Pages 웹페이지로
  발행하고 카카오톡에는 링크만 전송합니다.
- 뉴스레터 아카이브(`docs/`)는 저장소에 커밋되어 매일 조금씩 늘어나지만, 14일이 지난 파일은
  자동으로 삭제되어 무한정 쌓이지 않습니다.
- OpenAI API 호출 비용이 발생합니다(사용량에 따라 과금).
