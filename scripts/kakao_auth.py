"""
카카오 '나에게 보내기' 권한을 위한 최초 1회 OAuth 인증 스크립트.

사전 준비:
1. https://developers.kakao.com 에서 애플리케이션 생성
2. 앱 설정 > 카카오 로그인 활성화, Redirect URI 등록 (예: https://example.com/oauth)
3. 앱 설정 > 카카오 로그인 > 동의항목에서 "카카오톡 메시지 전송"(talk_message) 항목을
   "필수 동의" 또는 "선택 동의"로 설정
4. .env 에 KAKAO_REST_API_KEY, KAKAO_REDIRECT_URI 설정 (Redirect URI는 2번과 동일해야 함)
5. 앱 키 > 클라이언트 시크릿이 "카카오 로그인"에 대해 활성화(ON)되어 있다면, 그 코드 값을
   .env의 KAKAO_CLIENT_SECRET에도 설정 (비활성화 상태라면 비워둬도 됨)

실행:
    python -m scripts.kakao_auth

브라우저에서 안내된 URL로 접속해 로그인/동의 후, redirect된 주소창의 "code=" 뒤 값을
터미널에 붙여넣으면 access_token / refresh_token이 출력됩니다.
refresh_token 값을 GitHub Secrets의 KAKAO_REFRESH_TOKEN에 등록하세요.
"""
import sys
import urllib.parse

import requests
from dotenv import load_dotenv

load_dotenv()

import os  # noqa: E402

REST_API_KEY = os.environ.get("KAKAO_REST_API_KEY", "").strip()
REDIRECT_URI = os.environ.get("KAKAO_REDIRECT_URI", "").strip()
CLIENT_SECRET = os.environ.get("KAKAO_CLIENT_SECRET", "").strip()

AUTHORIZE_URL = "https://kauth.kakao.com/oauth/authorize"
TOKEN_URL = "https://kauth.kakao.com/oauth/token"


def main() -> None:
    if not REST_API_KEY or not REDIRECT_URI:
        print("KAKAO_REST_API_KEY / KAKAO_REDIRECT_URI를 .env에 설정한 뒤 다시 실행하세요.", file=sys.stderr)
        sys.exit(1)

    params = {
        "client_id": REST_API_KEY,
        "redirect_uri": REDIRECT_URI,
        "response_type": "code",
        "scope": "talk_message",
    }
    auth_url = f"{AUTHORIZE_URL}?{urllib.parse.urlencode(params)}"

    print("아래 URL을 브라우저에서 열고 로그인/동의를 진행하세요:\n")
    print(auth_url)
    print("\n동의 후 리다이렉트된 주소창 URL 전체를 붙여넣거나, code= 뒤의 값만 입력하세요.")
    raw = input("> ").strip()

    if "code=" in raw:
        code = urllib.parse.parse_qs(urllib.parse.urlparse(raw).query)["code"][0]
    else:
        code = raw

    data = {
        "grant_type": "authorization_code",
        "client_id": REST_API_KEY,
        "redirect_uri": REDIRECT_URI,
        "code": code,
    }
    if CLIENT_SECRET:
        data["client_secret"] = CLIENT_SECRET
    resp = requests.post(TOKEN_URL, data=data, timeout=15)
    if resp.status_code != 200:
        print(f"토큰 발급 실패 ({resp.status_code}): {resp.text}", file=sys.stderr)
        sys.exit(1)

    payload = resp.json()
    print("\n=== 발급 성공 ===")
    print(f"access_token: {payload['access_token']}")
    print(f"refresh_token: {payload['refresh_token']}")
    print(f"refresh_token_expires_in(초): {payload.get('refresh_token_expires_in')}")
    print("\n위 refresh_token 값을 GitHub repo Settings > Secrets and variables > Actions 에서")
    print("KAKAO_REFRESH_TOKEN 이름으로 등록하세요.")


if __name__ == "__main__":
    main()
