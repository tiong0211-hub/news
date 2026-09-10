"""언론사 화이트리스트(도메인) 판별 유틸"""
import urllib.parse


def is_allowed_domain(link: str, allowed_domains: list[str]) -> bool:
    """link의 도메인이 allowed_domains 중 하나와 일치하거나 그 하위 도메인이면 True."""
    if not link or not allowed_domains:
        return False
    netloc = urllib.parse.urlparse(link).netloc.lower().removeprefix("www.")
    return any(netloc == d or netloc.endswith(f".{d}") for d in allowed_domains)
