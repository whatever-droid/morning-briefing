#!/usr/bin/env python3
"""
[1회용] 카카오 refresh token 발급 도우미.

사전 준비 — 카카오 개발자 콘솔(https://developers.kakao.com):
  1. 내 애플리케이션 → 애플리케이션 추가하기 (이름 아무거나)
  2. [앱 키]에서 'REST API 키' 복사
  3. [카카오 로그인] → 활성화 설정 ON
  4. [카카오 로그인] → Redirect URI 등록:  https://localhost
  5. [카카오 로그인] → 동의항목 → '카카오톡 메시지 전송'(talk_message) 사용 ON

사용법:
  python get_kakao_token.py
  → REST API 키 입력 → 출력된 URL을 브라우저에서 열고 카카오 로그인/동의
  → 'localhost에 연결할 수 없음' 페이지의 주소창에서 code=... 값을 복사해 붙여넣기
  → 출력된 refresh_token을 GitHub Secret(KAKAO_REFRESH_TOKEN)에 저장
"""
import sys
from urllib.parse import quote

import requests

REDIRECT_URI = "https://localhost"
SCOPE = "talk_message"


def main():
    rest_api_key = input("카카오 REST API 키를 입력하세요: ").strip()
    client_secret = input("카카오 Client Secret을 입력하세요 (사용 안 하면 그냥 엔터): ").strip()
    authorize_url = (
        "https://kauth.kakao.com/oauth/authorize"
        f"?response_type=code&client_id={rest_api_key}"
        f"&redirect_uri={quote(REDIRECT_URI, safe='')}"
        f"&scope={SCOPE}"
    )
    print("\n1) 아래 URL을 브라우저에서 여세요:\n")
    print(authorize_url)
    print("\n2) 카카오 로그인 후 '카카오톡 메시지 전송' 동의를 누르세요.")
    print("3) 'localhost에 연결할 수 없음' 페이지가 떠도 정상입니다.")
    print("   주소창의  https://localhost/?code=XXXXX  에서 XXXXX 부분만 복사하세요.\n")
    code = input("code 값을 붙여넣으세요: ").strip()

    token_data = {
        "grant_type": "authorization_code",
        "client_id": rest_api_key,
        "redirect_uri": REDIRECT_URI,
        "code": code,
    }
    if client_secret:
        token_data["client_secret"] = client_secret

    print("\n[보내는 요청 정보]")
    print(f"  client_id     = {rest_api_key[:8]}... (총 {len(rest_api_key)}자)")
    print(f"  redirect_uri  = {REDIRECT_URI}")
    print(f"  client_secret = {'포함함 (' + str(len(client_secret)) + '자)' if client_secret else '안 보냄 (빈칸)'}")

    resp = requests.post(
        "https://kauth.kakao.com/oauth/token",
        data=token_data,
        timeout=15,
    )
    if resp.status_code != 200:
        print("\n❌ 토큰 발급 실패:", resp.text, file=sys.stderr)
        if "KOE010" in resp.text:
            print(
                "\n👉 KOE010 = client_secret 설정과 입력이 안 맞습니다.\n"
                "   콘솔(보안 → Client Secret)의 '활성화 상태'와 위 client_secret이 일치해야 합니다:\n"
                "   · 활성화 상태 '사용함'  → 실행 시 그 코드 값을 정확히 입력\n"
                "   · 활성화 상태 '사용 안 함' → 실행 시 그냥 Enter (안 보냄)\n"
                "   그리고 REST API 키와 Client Secret이 '같은 앱'인지 꼭 확인하세요.",
                file=sys.stderr,
            )
        sys.exit(1)

    data = resp.json()
    print("\n✅ 발급 성공! 아래 값을 GitHub Secret에 저장하세요.\n")
    print("  KAKAO_REFRESH_TOKEN =", data["refresh_token"])
    print("\n(access_token은 저장할 필요 없습니다 — 매 실행 시 자동 갱신됩니다.)")


if __name__ == "__main__":
    main()
