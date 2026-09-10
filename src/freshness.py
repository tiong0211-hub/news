"""기사 발행일(KST) 판별 유틸"""
import email.utils
from datetime import datetime
from zoneinfo import ZoneInfo

KST = ZoneInfo("Asia/Seoul")
UTC = ZoneInfo("UTC")


def parse_pub_date(raw: str) -> datetime | None:
    """RFC 822 형식(Naver/Google News의 pubDate)을 KST datetime으로 파싱한다. 실패 시 None."""
    if not raw:
        return None
    try:
        dt = email.utils.parsedate_to_datetime(raw)
    except (TypeError, ValueError):
        return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=UTC)
    return dt.astimezone(KST)


def is_today_kst(raw: str, now: datetime | None = None) -> bool:
    """주어진 발행일이 KST 기준 오늘 날짜인지 확인한다. 파싱 실패 시 False."""
    dt = parse_pub_date(raw)
    if dt is None:
        return False
    ref = now or datetime.now(KST)
    return dt.date() == ref.date()


def format_kst(raw: str) -> str:
    """표시용 문자열로 변환한다 (예: 2026-09-10 09:15). 파싱 실패 시 원본을 그대로 반환."""
    dt = parse_pub_date(raw)
    if dt is None:
        return raw
    return dt.strftime("%Y-%m-%d %H:%M")
