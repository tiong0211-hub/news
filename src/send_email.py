"""briefing_meta.json에 기록된 날짜의 아카이브 페이지를 이메일로 발송한다.

EMAIL_ADDRESS / EMAIL_APP_PASSWORD가 설정되어 있지 않으면 조용히 건너뛴다 (선택 기능).
"""
import json
import logging
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from pathlib import Path

from . import config

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

META_PATH = Path(__file__).resolve().parent.parent / "briefing_meta.json"
ARCHIVE_DIR = Path(__file__).resolve().parent.parent / "docs" / "archive"


def run() -> None:
    if not config.EMAIL_ADDRESS or not config.EMAIL_APP_PASSWORD:
        logger.info("EMAIL_ADDRESS/EMAIL_APP_PASSWORD가 설정되지 않아 이메일 발송을 건너뜁니다.")
        return

    meta = json.loads(META_PATH.read_text(encoding="utf-8"))
    date_str = meta["date"]
    count = meta["count"]

    archive_path = ARCHIVE_DIR / f"{date_str}.html"
    body_html = archive_path.read_text(encoding="utf-8")

    message = MIMEMultipart("alternative")
    message["Subject"] = f"오늘의 경제 뉴스 브리핑 ({date_str}) - 총 {count}건"
    message["From"] = config.EMAIL_ADDRESS
    message["To"] = config.EMAIL_TO
    message.attach(MIMEText(body_html, "html", "utf-8"))

    logger.info("이메일 발송 시작 (%s -> %s)", config.EMAIL_ADDRESS, config.EMAIL_TO)
    with smtplib.SMTP(config.EMAIL_SMTP_HOST, config.EMAIL_SMTP_PORT) as server:
        server.starttls()
        server.login(config.EMAIL_ADDRESS, config.EMAIL_APP_PASSWORD)
        server.sendmail(config.EMAIL_ADDRESS, [config.EMAIL_TO], message.as_string())
    logger.info("이메일 발송 완료")


if __name__ == "__main__":
    run()
