import logging
from datetime import datetime
from zoneinfo import ZoneInfo

from .collectors import google_news, naver
from . import kakao, summarizer

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

KST = ZoneInfo("Asia/Seoul")


def run() -> None:
    logger.info("국내 뉴스 수집 시작")
    domestic = naver.fetch()
    logger.info("국내 뉴스 %d건 수집", len(domestic))

    logger.info("해외 뉴스 수집 시작")
    foreign = google_news.fetch()
    logger.info("해외 뉴스 %d건 수집", len(foreign))

    candidates = domestic + foreign
    if not candidates:
        logger.warning("수집된 뉴스가 없습니다. 종료합니다.")
        return

    logger.info("OpenAI로 중복 제거/필터링/번역/요약/선별 중 (후보 %d건)", len(candidates))
    selected = summarizer.select_and_summarize(candidates)
    logger.info("최종 선별 %d건", len(selected))

    date_str = datetime.now(KST).strftime("%Y-%m-%d")
    logger.info("카카오톡 발송 시작")
    kakao.send_briefing(selected, date_str)
    logger.info("카카오톡 발송 완료")


if __name__ == "__main__":
    run()
