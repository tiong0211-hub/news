"""뉴스 수집 → 오늘자 필터링 → 요약/선별 → docs/index.html 및 날짜별 아카이브 생성

GitHub Pages 배포용 정적 페이지와, 카카오 발송 단계에서 쓸 메타데이터(briefing_meta.json)를 만든다.
지난 브리핑은 docs/archive/YYYY-MM-DD.html로 보관하며, ARCHIVE_RETENTION_DAYS보다 오래된 파일은
매 실행 시 자동으로 삭제한다.
"""
import json
import logging
import os
from datetime import datetime, timedelta
from pathlib import Path

from . import config, newsletter, summarizer
from .collectors import foreign_news, naver
from .freshness import KST, is_today_kst
from .kr_calendar import is_skip_day

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

DOCS_DIR = Path(__file__).resolve().parent.parent / "docs"
ARCHIVE_DIR = DOCS_DIR / "archive"
META_PATH = Path(__file__).resolve().parent.parent / "briefing_meta.json"

ARCHIVE_RETENTION_DAYS = 14


def _prune_old_archives(today: datetime) -> None:
    if not ARCHIVE_DIR.exists():
        return
    for path in ARCHIVE_DIR.glob("*.html"):
        try:
            file_date = datetime.strptime(path.stem, "%Y-%m-%d").replace(tzinfo=KST)
        except ValueError:
            continue
        if (today - file_date).days > ARCHIVE_RETENTION_DAYS:
            path.unlink()
            logger.info("오래된 아카이브 삭제: %s", path.name)


def _recent_archive_links(exclude_date_str: str) -> list[tuple[str, str]]:
    if not ARCHIVE_DIR.exists():
        return []
    dates = sorted(
        (path.stem for path in ARCHIVE_DIR.glob("*.html") if path.stem != exclude_date_str),
        reverse=True,
    )
    return [(d, f"archive/{d}.html") for d in dates]


def _write_github_output(key: str, value: str) -> None:
    path = os.environ.get("GITHUB_OUTPUT")
    if not path:
        return
    with open(path, "a", encoding="utf-8") as fh:
        fh.write(f"{key}={value}\n")


def run() -> None:
    now = datetime.now(KST)
    if config.GITHUB_EVENT_NAME == "schedule" and is_skip_day(now):
        logger.info("주말/공휴일이라 오늘(%s)은 발행을 건너뜁니다.", now.strftime("%Y-%m-%d"))
        _write_github_output("skip", "true")
        return
    _write_github_output("skip", "false")

    logger.info("국내 뉴스 수집 시작")
    domestic = naver.fetch()
    domestic = [a for a in domestic if is_today_kst(a["published"])]
    logger.info("국내 뉴스 %d건 수집 (오늘자만)", len(domestic))

    logger.info("해외 뉴스 수집 시작")
    foreign = foreign_news.fetch()
    foreign = [a for a in foreign if is_today_kst(a["published"])]
    logger.info("해외 뉴스 %d건 수집 (오늘자만)", len(foreign))

    candidates = domestic + foreign
    date_str = now.strftime("%Y-%m-%d")

    if not candidates:
        logger.warning("오늘자 수집된 뉴스가 없습니다.")
        selected = []
    else:
        logger.info("OpenAI로 중복 제거/필터링/번역/요약/선별 중 (후보 %d건)", len(candidates))
        selected = summarizer.select_and_summarize(candidates)
        logger.info("최종 선별 %d건", len(selected))

    ARCHIVE_DIR.mkdir(parents=True, exist_ok=True)
    _prune_old_archives(now)

    page_html = newsletter.render_html(selected, date_str)
    (ARCHIVE_DIR / f"{date_str}.html").write_text(page_html, encoding="utf-8")

    archive_links = _recent_archive_links(exclude_date_str=date_str)
    index_html = newsletter.render_html(selected, date_str, archive_links=archive_links)
    (DOCS_DIR / "index.html").write_text(index_html, encoding="utf-8")

    META_PATH.write_text(
        json.dumps({"date": date_str, "count": len(selected)}, ensure_ascii=False),
        encoding="utf-8",
    )
    logger.info("docs/index.html 생성 완료 (%d건, 지난 브리핑 %d개 보관)", len(selected), len(archive_links))


if __name__ == "__main__":
    run()
