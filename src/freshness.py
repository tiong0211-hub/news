"""기사 발행일(KST) 판별 유틸"""
import email.utils
from datetime import datetime, time, timedelta
from zoneinfo import ZoneInfo

KST = ZoneInfo("Asia/Seoul")
UTC = ZoneInfo("UTC")

# 브리핑 수집 대상 시간대: 전일 정오(12:00 KST)부터 발행 시점(보통 당일 08:00 KST)까지.
# 자정~아침 사이에는 새 기사가 적어 "오늘 날짜" 필터만으로는 좋은 기사가 부족했던 문제를 보완한다.
WINDOW_START_HOUR = 12


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


def is_in_briefing_window(raw: str, now: datetime | None = None) -> bool:
    """전일 정오(12:00 KST)부터 기준 시각(보통 발행 시점)까지 발행된 기사인지 확인한다.
    파싱 실패 시 False."""
    dt = parse_pub_date(raw)
    if dt is None:
        return False
    ref = now or datetime.now(KST)
    window_start = datetime.combine(ref.date() - timedelta(days=1), time(WINDOW_START_HOUR, 0), tzinfo=KST)
    return window_start <= dt <= ref


def format_kst(raw: str) -> str:
    """표시용 문자열로 변환한다 (예: 2026-09-10 09:15). 파싱 실패 시 원본을 그대로 반환."""
    dt = parse_pub_date(raw)
    if dt is None:
        return raw
    return dt.strftime("%Y-%m-%d %H:%M")
