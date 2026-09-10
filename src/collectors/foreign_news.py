"""해외 경제 뉴스 수집 (신뢰 언론사 공식 RSS 피드)"""
import html
import logging
import re

import feedparser

from .. import config
from ..sources import is_allowed_domain

logger = logging.getLogger(__name__)

# 언론사 도메인 -> 공식 RSS 피드 URL. FOREIGN_SOURCE_DOMAINS를 바꿔도 여기 매핑이 없으면
# 해당 언론사는 건너뛴다 (Google News RSS의 site: 검색은 실제 언론사 URL이 아닌
# news.google.com 리다이렉트만 돌려줘서 신뢰할 수 없어 사용하지 않는다).
KNOWN_FEEDS = {
    "wsj.com": "https://feeds.a.dj.com/rss/RSSMarketsMain.xml",
    "ft.com": "https://www.ft.com/rss/home",
    "nikkei.com": "https://asia.nikkei.com/rss/feed/nar",
}


def _strip_tags(text: str) -> str:
    return html.unescape(re.sub(r"<[^>]+>", "", text or ""))


def fetch(entries_per_query: int = 30) -> list[dict]:
    """신뢰 언론사(FOREIGN_SOURCE_DOMAINS)의 공식 RSS 피드에서 최근 기사를 가져온다."""
    seen_links = set()
    articles = []
    for domain in config.FOREIGN_SOURCE_DOMAINS:
        feed_url = KNOWN_FEEDS.get(domain)
        if not feed_url:
            logger.warning("FOREIGN_SOURCE_DOMAINS의 '%s'에 대한 RSS 피드가 등록되어 있지 않아 건너뜁니다.", domain)
            continue

        feed = feedparser.parse(feed_url)
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
                    "source": "foreign_news",
                    "query": domain,
                    "title": _strip_tags(entry.get("title")),
                    "description": _strip_tags(entry.get("summary")),
                    "link": link,
                    "published": entry.get("published", ""),
                }
            )
        logger.info("Foreign news[%s]: raw=%d kept=%d", domain, len(feed.entries), kept)
    return articles
