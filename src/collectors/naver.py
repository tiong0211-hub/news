"""국내 경제 뉴스 수집 (NAVER Cloud Platform 검색 API - 뉴스)"""
import html
import re

import requests

from .. import config

# 검색 오픈API가 Naver Cloud Platform(NCP) API Gateway로 이전되면서
# 엔드포인트와 인증 헤더가 변경되었다. (기존 openapi.naver.com + X-Naver-Client-* 방식은 더 이상 사용 불가)
NAVER_NEWS_URL = "https://naveropenapi.apigw.ntruss.com/search/v1/news.json"


def _strip_tags(text: str) -> str:
    return html.unescape(re.sub(r"<[^>]+>", "", text or ""))


def fetch(display_per_query: int = 15) -> list[dict]:
    """네이버 검색 API로 키워드별 최신 경제 뉴스를 가져와 표준 형식으로 반환한다."""
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
