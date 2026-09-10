"""해외 경제 뉴스 수집 (Google News RSS)"""
import html
import re
import urllib.parse

import feedparser

from .. import config
from ..sources import is_allowed_domain

GOOGLE_NEWS_RSS_URL = "https://news.google.com/rss/search"


def _strip_tags(text: str) -> str:
    return html.unescape(re.sub(r"<[^>]+>", "", text or ""))


def _quoted(term: str) -> str:
    return f'"{term}"' if " " in term else term


def fetch(entries_per_query: int = 20, window: str = "when:1d") -> list[dict]:
    """Google News RSS로 신뢰 언론사(FOREIGN_SOURCE_DOMAINS)의 최근 해외 경제 뉴스만 가져온다.

    언론사별로 site: 검색을 걸어, 각 언론사 도메인의 기사만 수집한다.
    """
    topic_query = " OR ".join(_quoted(q) for q in config.GOOGLE_NEWS_QUERIES)

    seen_links = set()
    articles = []
    for domain in config.FOREIGN_SOURCE_DOMAINS:
        q = urllib.parse.quote(f"({topic_query}) site:{domain} {window}")
        url = f"{GOOGLE_NEWS_RSS_URL}?q={q}&hl=en-US&gl=US&ceid=US:en"
        feed = feedparser.parse(url)
        for entry in feed.entries[:entries_per_query]:
            link = entry.get("link", "")
            if not link or link in seen_links:
                continue
            if not is_allowed_domain(link, [domain]):
                continue
            seen_links.add(link)
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
    return articles
