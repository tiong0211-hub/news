"""한국 영업일(주말/공휴일 제외) 판별"""
from datetime import datetime

import holidays

_KR_HOLIDAYS = holidays.KR()


def is_skip_day(now: datetime) -> bool:
    """주말이거나 한국 공휴일(대체공휴일 포함)이면 True."""
    if now.weekday() >= 5:  # 5=토요일, 6=일요일
        return True
    return now.date() in _KR_HOLIDAYS
