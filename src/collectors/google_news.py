"""해외 경제 뉴스 수집 (Google News RSS)"""
import html
import logging
import re
import urllib.parse

import feedparser

from .. import config
from ..sources import is_allowed_domain

GOOGLE_NEWS_RSS_URL = "https://news.google.com/rss/search"

logger = logging.getLogger(__name__)


def _strip_tags(text: str) -> str:
    return html.unescape(re.sub(r"<[^>]+>", "", text or ""))


def fetch(entries_per_query: int = 20, window: str = "when:1d") -> list[dict]:
    """Google News RSS로 신뢰 언론사(FOREIGN_SOURCE_DOMAINS)의 최근 기사를 가져온다.

    언론사별로 site: 검색을 걸어 해당 언론사 도메인의 기사만 수집한다. 대상이 모두 경제 전문지라
    별도 주제 키워드 없이도 대부분 투자 참고용 뉴스이며, 최종 관련성 판단은 요약 단계(OpenAI)에서 한다.
    """
    seen_links = set()
    articles = []
    for domain in config.FOREIGN_SOURCE_DOMAINS:
        q = urllib.parse.quote(f"site:{domain} {window}")
        url = f"{GOOGLE_NEWS_RSS_URL}?q={q}&hl=en-US&gl=US&ceid=US:en"
        feed = feedparser.parse(url)
        kept = 0
        for entry in feed.entries[:entries_per_query]:
            link = entry.get("link", "")
            if not link or link in seen_links:
                continue
            if not is_allowed_domain(link, [domain]):
                continue
            seen_links.add(link)
            kept += 1
            articles.append(
                {
                    "source": "google_news",
                    "query": domain,
                    "title": _strip_tags(entry.get("title")),
                    "description": _strip_tags(entry.get("summary")),
                    "link": link,
                    "published": entry.get("published", ""),
                }
            )
        logger.info(
            "Google News[%s]: raw=%d kept=%d sample_link=%s status=%s bozo=%s",
            domain,
            len(feed.entries),
            kept,
            feed.entries[0].get("link", "") if feed.entries else "",
            getattr(feed, "status", "?"),
            getattr(feed, "bozo", "?"),
        )
    return articles
