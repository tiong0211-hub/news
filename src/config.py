import os

from dotenv import load_dotenv

load_dotenv()


def _env(key: str, default: str = "") -> str:
    """앞뒤 공백/줄바꿈을 제거하고, 빈 문자열(예: 설정 안 된 GitHub Actions 변수)은 미설정으로 취급해 기본값을 반환한다."""
    value = os.environ.get(key, "").strip()
    return value if value else default


def _split_csv(value: str) -> list[str]:
    return [item.strip() for item in value.split(",") if item.strip()]


NAVER_CLIENT_ID = _env("NAVER_CLIENT_ID")
NAVER_CLIENT_SECRET = _env("NAVER_CLIENT_SECRET")
NAVER_QUERIES = _split_csv(_env("NAVER_QUERIES", "경제,증시,코스피,금리,환율,부동산,수출입"))

# 신뢰할 수 있는 언론사만 사용 (도메인 기준). 국내는 Naver API가 언론사 지정 검색을 지원하지
# 않아 수집 후 필터링하고, 해외는 Google News의 site: 검색으로 아예 해당 언론사만 수집한다.
DOMESTIC_SOURCE_DOMAINS = _split_csv(
    _env("DOMESTIC_SOURCE_DOMAINS", "mk.co.kr,hankyung.com,mt.co.kr,heraldcorp.com,biz.chosun.com,fnnews.com")
)
FOREIGN_SOURCE_DOMAINS = _split_csv(_env("FOREIGN_SOURCE_DOMAINS", "wsj.com,ft.com,nikkei.com"))

OPENAI_API_KEY = _env("OPENAI_API_KEY")
OPENAI_MODEL = _env("OPENAI_MODEL", "gpt-4o-mini")

KAKAO_REST_API_KEY = _env("KAKAO_REST_API_KEY")
KAKAO_CLIENT_SECRET = _env("KAKAO_CLIENT_SECRET")
KAKAO_REFRESH_TOKEN = _env("KAKAO_REFRESH_TOKEN")
KAKAO_REDIRECT_URI = _env("KAKAO_REDIRECT_URI")

TOP_N = int(_env("TOP_N", "10"))

GH_PAT = _env("GH_PAT")
GITHUB_REPOSITORY = _env("GITHUB_REPOSITORY")

# (선택) 이메일 발송 — EMAIL_ADDRESS/EMAIL_APP_PASSWORD가 비어 있으면 이메일 발송을 건너뛴다.
EMAIL_SMTP_HOST = _env("EMAIL_SMTP_HOST", "smtp.gmail.com")
EMAIL_SMTP_PORT = int(_env("EMAIL_SMTP_PORT", "587"))
EMAIL_ADDRESS = _env("EMAIL_ADDRESS")
EMAIL_APP_PASSWORD = _env("EMAIL_APP_PASSWORD")
EMAIL_TO = _env("EMAIL_TO", EMAIL_ADDRESS)
