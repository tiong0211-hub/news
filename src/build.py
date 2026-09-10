"""뉴스 수집 → 오늘자 필터링 → 요약/선별 → docs/index.html 생성

GitHub Pages 배포용 정적 페이지와, 카카오 발송 단계에서 쓸 메타데이터(briefing_meta.json)를 만든다.
"""
import json
import logging
from datetime import datetime
from pathlib import Path

from . import newsletter, summarizer
from .collectors import foreign_news, naver
from .freshness import KST, is_today_kst

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

DOCS_DIR = Path(__file__).resolve().parent.parent / "docs"
META_PATH = Path(__file__).resolve().parent.parent / "briefing_meta.json"


def run() -> None:
    logger.info("국내 뉴스 수집 시작")
    domestic = naver.fetch()
    domestic = [a for a in domestic if is_today_kst(a["published"])]
    logger.info("국내 뉴스 %d건 수집 (오늘자만)", len(domestic))

    logger.info("해외 뉴스 수집 시작")
    foreign = foreign_news.fetch()
    foreign = [a for a in foreign if is_today_kst(a["published"])]
    logger.info("해외 뉴스 %d건 수집 (오늘자만)", len(foreign))

    candidates = domestic + foreign
    date_str = datetime.now(KST).strftime("%Y-%m-%d")

    if not candidates:
        logger.warning("오늘자 수집된 뉴스가 없습니다.")
        selected = []
    else:
        logger.info("OpenAI로 중복 제거/필터링/번역/요약/선별 중 (후보 %d건)", len(candidates))
        selected = summarizer.select_and_summarize(candidates)
        logger.info("최종 선별 %d건", len(selected))

    DOCS_DIR.mkdir(parents=True, exist_ok=True)
    (DOCS_DIR / "index.html").write_text(newsletter.render_html(selected, date_str), encoding="utf-8")
    META_PATH.write_text(
        json.dumps({"date": date_str, "count": len(selected)}, ensure_ascii=False),
        encoding="utf-8",
    )
    logger.info("docs/index.html 생성 완료 (%d건)", len(selected))


if __name__ == "__main__":
    run()
