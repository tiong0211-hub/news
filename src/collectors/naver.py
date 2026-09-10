"""국내 경제 뉴스 수집 (NAVER Cloud Platform 검색 API - 뉴스)"""
import html
import re

import requests

from .. import config
from ..sources import is_allowed_domain

# 검색 오픈API가 NAVER API HUB(NCP)로 이전되면서 호스트와 경로가 바뀌었다.
# (기존 openapi.naver.com/v1/search/news.json 은 NCP 발급 키로는 401)
NAVER_NEWS_URL = "https://naverapihub.apigw.ntruss.com/search/v1/news"


def _strip_tags(text: str) -> str:
    return html.unescape(re.sub(r"<[^>]+>", "", text or ""))


def fetch(display_per_query: int = 30) -> list[dict]:
    """네이버 검색 API로 키워드별 최신 경제 뉴스를 가져와, 신뢰 언론사(DOMESTIC_SOURCE_DOMAINS)
    도메인의 기사만 표준 형식으로 반환한다."""
    if not config.NAVER_CLIENT_ID or not config.NAVER_CLIENT_SECRET:
        raise RuntimeError("NAVER_CLIENT_ID / NAVER_CLIENT_SECRET 환경변수가 설정되지 않았습니다.")

    headers = {
        "X-NCP-APIGW-API-KEY-ID": config.NAVER_CLIENT_ID,
        "X-NCP-APIGW-API-KEY": config.NAVER_CLIENT_SECRET,
    }

    seen_links = set()
    articles = []
    for query in config.NAVER_QUERIES:
        params = {"query": query, "display": display_per_query, "sort": "date"}
        resp = requests.get(NAVER_NEWS_URL, headers=headers, params=params, timeout=15)
        if resp.status_code != 200:
            raise RuntimeError(f"네이버 검색 API 호출 실패 ({resp.status_code}): {resp.text}")
        for item in resp.json().get("items", []):
            link = item.get("originallink") or item.get("link")
            if not link or link in seen_links:
                continue
            if not is_allowed_domain(link, config.DOMESTIC_SOURCE_DOMAINS):
                continue
            seen_links.add(link)
            articles.append(
                {
                    "source": "naver",
                    "query": query,
                    "title": _strip_tags(item.get("title")),
                    "description": _strip_tags(item.get("description")),
                    "link": link,
                    "published": item.get("pubDate", ""),
                }
            )
    return articles
