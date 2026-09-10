"""카카오톡 '나에게 보내기' API 연동 (토큰 갱신 + 메시지 발송)"""
import base64
import json
import logging

import requests

from . import config

TOKEN_URL = "https://kauth.kakao.com/oauth/token"
SEND_URL = "https://kapi.kakao.com/v2/api/talk/memo/default/send"

logger = logging.getLogger(__name__)


def refresh_access_token() -> tuple[str, str | None]:
    """refresh_token으로 access_token을 발급받는다. 반환값: (access_token, 새로운 refresh_token 또는 None)"""
    if not config.KAKAO_REST_API_KEY or not config.KAKAO_REFRESH_TOKEN:
        raise RuntimeError("KAKAO_REST_API_KEY / KAKAO_REFRESH_TOKEN 환경변수가 설정되지 않았습니다.")

    data = {
        "grant_type": "refresh_token",
        "client_id": config.KAKAO_REST_API_KEY,
        "refresh_token": config.KAKAO_REFRESH_TOKEN,
    }
    if config.KAKAO_CLIENT_SECRET:
        data["client_secret"] = config.KAKAO_CLIENT_SECRET
    resp = requests.post(TOKEN_URL, data=data, timeout=15)
    if resp.status_code != 200:
        raise RuntimeError(f"카카오 토큰 갱신 실패 ({resp.status_code}): {resp.text}")

    payload = resp.json()
    access_token = payload["access_token"]
    new_refresh_token = payload.get("refresh_token")  # 만료 임박 시에만 내려옴
    return access_token, new_refresh_token


def send_text_memo(access_token: str, text: str, link_url: str | None = None, button_title: str = "기사 보기") -> None:
    template_object = {
        "object_type": "text",
        "text": text,
        "link": {
            "web_url": link_url or "https://news.google.com",
            "mobile_web_url": link_url or "https://news.google.com",
        },
    }
    if link_url:
        template_object["button_title"] = button_title

    resp = requests.post(
        SEND_URL,
        headers={"Authorization": f"Bearer {access_token}"},
        data={"template_object": json.dumps(template_object, ensure_ascii=False)},
        timeout=15,
    )
    if resp.status_code != 200:
        raise RuntimeError(f"카카오 메시지 전송 실패 ({resp.status_code}): {resp.text}")


def send_briefing_link(count: int, date_str: str, page_url: str | None) -> None:
    """뉴스레터 페이지 링크 1건을 카카오톡 '나에게 보내기'로 전송한다."""
    access_token, new_refresh_token = refresh_access_token()

    if count and page_url:
        text = f"📈 오늘의 경제 뉴스 브리핑 ({date_str})\n국내·해외 경제 뉴스 {count}건을 정리했습니다.\n아래 버튼을 눌러 확인하세요."
        send_text_memo(access_token, text, link_url=page_url, button_title="브리핑 보기")
    else:
        send_text_memo(access_token, f"📈 ({date_str}) 오늘은 선별된 투자 관련 뉴스가 없습니다.")

    if new_refresh_token and new_refresh_token != config.KAKAO_REFRESH_TOKEN:
        _try_rotate_refresh_token_secret(new_refresh_token)


def _try_rotate_refresh_token_secret(new_refresh_token: str) -> None:
    """카카오가 새 refresh_token을 내려준 경우, 가능하면 GitHub Actions Secret을 자동 갱신한다."""
    if not config.GH_PAT or not config.GITHUB_REPOSITORY:
        logger.warning(
            "Kakao refresh_token이 갱신되었지만 GH_PAT/GITHUB_REPOSITORY가 없어 "
            "GitHub Secret을 자동 갱신하지 못했습니다. KAKAO_REFRESH_TOKEN 시크릿을 "
            "수동으로 갱신해 주세요."
        )
        return

    try:
        from nacl import encoding, public

        api_base = f"https://api.github.com/repos/{config.GITHUB_REPOSITORY}"
        headers = {
            "Authorization": f"Bearer {config.GH_PAT}",
            "Accept": "application/vnd.github+json",
        }

        key_resp = requests.get(f"{api_base}/actions/secrets/public-key", headers=headers, timeout=15)
        key_resp.raise_for_status()
        key_data = key_resp.json()

        public_key = public.PublicKey(key_data["key"].encode("utf-8"), encoding.Base64Encoder())
        sealed_box = public.SealedBox(public_key)
        encrypted = sealed_box.encrypt(new_refresh_token.encode("utf-8"))
        encrypted_value = base64.b64encode(encrypted).decode("utf-8")

        put_resp = requests.put(
            f"{api_base}/actions/secrets/KAKAO_REFRESH_TOKEN",
            headers=headers,
            json={"encrypted_value": encrypted_value, "key_id": key_data["key_id"]},
            timeout=15,
        )
        put_resp.raise_for_status()
        logger.info("KAKAO_REFRESH_TOKEN GitHub Secret을 새 토큰으로 갱신했습니다.")
    except Exception:
        logger.exception(
            "KAKAO_REFRESH_TOKEN GitHub Secret 자동 갱신에 실패했습니다. 수동으로 갱신해 주세요."
        )
