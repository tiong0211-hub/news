"""해외 경제 뉴스 수집 (Google News RSS)"""
import html
import re
import urllib.parse

import feedparser

from .. import config

GOOGLE_NEWS_RSS_URL = "https://news.google.com/rss/search"


def _strip_tags(text: str) -> str:
    return html.unescape(re.sub(r"<[^>]+>", "", text or ""))


def fetch(entries_per_query: int = 10, window: str = "when:1d") -> list[dict]:
    """Google News RSS로 키워드별 최근 해외 경제 뉴스를 가져와 표준 형식으로 반환한다."""
    seen_links = set()
    articles = []
    for query in config.GOOGLE_NEWS_QUERIES:
        q = urllib.parse.quote(f"{query} {window}")
        url = f"{GOOGLE_NEWS_RSS_URL}?q={q}&hl=en-US&gl=US&ceid=US:en"
        feed = feedparser.parse(url)
        for entry in feed.entries[:entries_per_query]:
            link = entry.get("link", "")
            if not link or link in seen_links:
                continue
            seen_links.add(link)
            articles.append(
                {
                    "source": "google_news",
                    "query": query,
                    "title": _strip_tags(entry.get("title")),
                    "description": _strip_tags(entry.get("summary")),
                    "link": link,
                    "published": entry.get("published", ""),
                }
            )
    return articles
