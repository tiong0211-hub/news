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

GOOGLE_NEWS_QUERIES = _split_csv(
    _env("GOOGLE_NEWS_QUERIES", "economy,stock market,federal reserve,inflation,interest rates")
)

OPENAI_API_KEY = _env("OPENAI_API_KEY")
OPENAI_MODEL = _env("OPENAI_MODEL", "gpt-4o-mini")

KAKAO_REST_API_KEY = _env("KAKAO_REST_API_KEY")
KAKAO_CLIENT_SECRET = _env("KAKAO_CLIENT_SECRET")
KAKAO_REFRESH_TOKEN = _env("KAKAO_REFRESH_TOKEN")
KAKAO_REDIRECT_URI = _env("KAKAO_REDIRECT_URI")

TOP_N = int(_env("TOP_N", "10"))

GH_PAT = _env("GH_PAT")
GITHUB_REPOSITORY = _env("GITHUB_REPOSITORY")
