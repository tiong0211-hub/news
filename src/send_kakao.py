"""briefing_meta.json + PAGE_URL 환경변수를 이용해 카카오톡 '나에게 보내기'로 링크를 전송한다."""
import json
import logging
import os
from pathlib import Path

from . import kakao

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

META_PATH = Path(__file__).resolve().parent.parent / "briefing_meta.json"


def run() -> None:
    meta = json.loads(META_PATH.read_text(encoding="utf-8"))
    page_url = os.environ.get("PAGE_URL", "").strip()

    logger.info("카카오톡 발송 시작 (%d건, %s)", meta["count"], page_url or "링크 없음")
    kakao.send_briefing_link(meta["count"], meta["date"], page_url)
    logger.info("카카오톡 발송 완료")


if __name__ == "__main__":
    run()
