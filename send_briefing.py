#!/usr/bin/env python3
"""
매일 아침 카카오톡 '나에게 보내기'로 모닝 브리핑을 보내는 스크립트.

받는 방식: 카톡엔 짧은 한 통(인사+리마인더+오늘 강의 제목+'전문 읽기' 버튼),
           전체 강의는 GitHub Pages 웹페이지에서 본다.

흐름:
  1) [build] 오늘(KST) 리마인더 계산 + 요일별 연재 강의 선택 + Claude로 본문 생성
             → docs/ 에 강의 웹페이지(HTML) 작성 + out/message.json 저장
  2) (워크플로) docs/ 커밋·푸시 → GitHub Pages 게시
  3) [send]  카카오 access token 갱신 → 짧은 메시지 + 페이지 링크 전송

실행 모드:
  python send_briefing.py build   # 페이지 생성만 (Actions 1단계)
  python send_briefing.py send    # 카톡 전송만   (Actions 3단계)
  python send_briefing.py         # 둘 다 (로컬 테스트용)

환경변수:
  [send] KAKAO_REST_API_KEY, KAKAO_REFRESH_TOKEN, (선택)KAKAO_CLIENT_SECRET
  [build] ANTHROPIC_API_KEY, (선택)BRIEFING_MODEL=claude-sonnet-4-6
  공통/선택: GH_REPO(owner/repo·페이지 URL 계산), PAGES_BASE_URL(직접 지정),
            GH_PAT(refresh token 자동 갱신)
"""
import os
import re
import sys
import json
import textwrap
from datetime import datetime, date, timezone, timedelta
from urllib.parse import quote

import requests

import curriculum
import lesson_page

KST = timezone(timedelta(hours=9))

KAKAO_TOKEN_URL = "https://kauth.kakao.com/oauth/token"
KAKAO_MEMO_URL = "https://kapi.kakao.com/v2/api/talk/memo/default/send"

MESSAGE_FILE = "out/message.json"
DOCS_DIR = "docs"

# 커리큘럼 시작 기준일(월요일). 매주 한 강씩 진도가 나간다.
CURRICULUM_START = date(2026, 6, 22)

# 요일(월=0…금=4) → (영역 이름, 커리큘럼 리스트)
WEEKDAY_AREA = {
    0: ("영화사", curriculum.FILM),
    1: ("음악사", curriculum.MUSIC),
    2: ("AI 공부", curriculum.AI),
    3: ("도예·건축·예술", curriculum.ART),
    4: ("시 읽기", curriculum.POETRY),
}


# ---------- 공통 로직 ----------

def build_reminders(now):
    day, weekday = now.day, now.weekday()
    reminders = []
    if day == 1:
        reminders.append("외모 체크 — 손발톱 정리, 마사지, 헤어 상태 점검")
    if day == 15:
        reminders.append("외모 체크 — 피부 상태, 체중, 보충이 필요한 뷰티 루틴 점검")
    if day == 22:
        reminders.append("돈 관리 — 보험 출금 확인, 적금 확인, 한 달 지출 결산")
    if weekday in (5, 6) and (1 <= day <= 7 or 15 <= day <= 21):  # 1·3주차 주말
        reminders.append("대청소")
    return reminders


def get_lesson(now):
    """오늘의 연재 강의. 주말이면 None.
    반환: (영역명, 강 번호, 오늘 제목, 지난 제목 or None, 다음 제목)"""
    area = WEEKDAY_AREA.get(now.weekday())
    if not area:
        return None
    label, syllabus = area
    weeks = max(0, (now.date() - CURRICULUM_START).days // 7)
    idx = weeks % len(syllabus)
    prev_title = syllabus[idx - 1] if idx > 0 else None
    next_title = syllabus[(idx + 1) % len(syllabus)]
    return label, idx + 1, syllabus[idx], prev_title, next_title


def page_link(date_str):
    """카톡 '전문 읽기'가 열 GitHub Pages URL을 계산."""
    base = os.environ.get("PAGES_BASE_URL")
    if not base:
        repo = os.environ.get("GH_REPO", "")
        if "/" in repo:
            owner, name = repo.split("/", 1)
            base = f"https://{owner}.github.io/{name}/"
    if base:
        if not base.endswith("/"):
            base += "/"
        return base + f"lessons/{date_str}.html"
    # 로컬 테스트 폴백(아직 배포 전): 네이버 검색으로 대체
    return "https://search.naver.com/search.naver?query=" + quote("교양 강의")


# ---------- build: 강의 생성 + 페이지 작성 ----------

def generate_body(now, lesson, api_key, model):
    from anthropic import Anthropic

    client = Anthropic(api_key=api_key)
    if lesson:
        label, no, title, prev_title, next_title = lesson
        prompt = textwrap.dedent(f"""\
            당신은 '{label}'를 처음 배우는 사람을 위한 다정한 선생님입니다.
            이 사람은 배경지식이 거의 없지만, 매주 한 강씩 차근차근 배워
            깊이 있는 교양을 쌓아가고 싶어 합니다. 오늘은 그 연재의 {no}강입니다.

            오늘 주제: "{title}"
            {f'지난 시간 주제: "{prev_title}"' if prev_title else '오늘이 이 연재의 첫 시간입니다.'}
            다음 시간 예고: "{next_title}"

            아래 조건으로 '오늘의 강의'를 작성하세요:
            - 한국어, 따뜻하고 쉬운 말투. 전문용어가 나오면 그 자리에서 바로 풀어 설명.
            - 분량은 한국어로 600~900자 정도, 충분히 깊고 알차게.
            - 구성: ① 오늘 배울 것을 한 문장으로 → ② 핵심을 이야기처럼 풀기 →
              ③ 기억에 남을 구체적 예(작품·인물·일화) → ④ '오늘의 핵심' 한 줄 정리.
            - 지난 시간이 있으면 자연스럽게 연결("지난주엔 ~, 오늘은 ~").
            - 문단은 빈 줄로 구분. 인사말·메타설명 없이 강의 본문만.
            - 오늘 직접 들어보거나 찾아볼 작품·키워드를 한두 개 콕 집어 추천.
        """)
        max_tokens = 1600
    else:
        weekday_kr = "월화수목금토일"[now.weekday()]
        prompt = textwrap.dedent(f"""\
            오늘은 주말({weekday_kr}요일)입니다. 영화·음악·미술·도예·건축·AI·시 가운데
            하나를 골라, 너무 뻔하지 않고 흥미로운 이야기를 한국어로 들려주세요.
            350자 내외, 따뜻한 말투, 인사말 없이 본문만. 찾아볼 키워드 하나 추천.
        """)
        max_tokens = 900

    msg = client.messages.create(
        model=model, max_tokens=max_tokens,
        messages=[{"role": "user", "content": prompt}],
    )
    return "".join(b.text for b in msg.content if b.type == "text").strip()


def compose_kakao_message(now, reminders, lesson):
    """카톡으로 보낼 짧은 한 통(전체 강의는 웹페이지에서)."""
    wd = "월화수목금토일"[now.weekday()]
    lines = [f"🌤️ 좋은 아침이에요! {now.month}월 {now.day}일 ({wd})", ""]
    if reminders:
        lines.append("📋 오늘의 리마인더")
        lines += [f"• {r}" for r in reminders]
    else:
        lines.append("📋 오늘은 고정 리마인더가 없어요 :)")
    lines.append("")
    if lesson:
        label, no, title, _prev, _next = lesson
        lines.append(f"📚 오늘의 {label} · {no}강")
        lines.append(f"〈{title}〉")
        lines.append("👇 '전문 읽기'에서 오늘 강의를 만나보세요!")
    else:
        lines.append("🎨 오늘의 이야기")
        lines.append("👇 '전문 읽기'에서 오늘의 이야기를 만나보세요!")
    return "\n".join(lines)


def do_build(now):
    anthropic_key = os.environ["ANTHROPIC_API_KEY"]
    model = os.environ.get("BRIEFING_MODEL", "claude-sonnet-4-6")

    reminders = build_reminders(now)
    lesson = get_lesson(now)
    try:
        body = generate_body(now, lesson, anthropic_key, model)
    except Exception as e:
        print(f"⚠️ 본문 생성 실패: {e}", file=sys.stderr)
        body = "오늘은 강의 준비에 잠깐 문제가 있었어요. 대신 좋아하는 음악 한 곡 어떠세요? 🎵"

    date_str = now.strftime("%Y-%m-%d")
    date_human = f"{now.year}년 {now.month}월 {now.day}일 " + "월화수목금토일"[now.weekday()] + "요일"
    if lesson:
        label = f"{lesson[0]} · {lesson[1]}강"
        title = lesson[2]
        next_line = f"{lesson[0]} — {lesson[4]}"
    else:
        label, title, next_line = "오늘의 이야기", "주말의 한 조각", None

    lesson_page.write_pages(DOCS_DIR, date_str, date_human, label, title, body, next_line)

    payload = {
        "text": compose_kakao_message(now, reminders, lesson),
        "link": page_link(date_str),
    }
    os.makedirs(os.path.dirname(MESSAGE_FILE), exist_ok=True)
    with open(MESSAGE_FILE, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False)

    print("----- 카톡으로 보낼 한 통 -----")
    print(payload["text"])
    print(f"----- 전문 링크: {payload['link']} -----")
    print(f"----- 웹페이지: {DOCS_DIR}/lessons/{date_str}.html (본문 {len(body)}자) -----")
    return payload


# ---------- send: 카카오 전송 ----------

def refresh_access_token(rest_api_key, refresh_token, client_secret=None):
    data = {
        "grant_type": "refresh_token",
        "client_id": rest_api_key,
        "refresh_token": refresh_token,
    }
    if client_secret:
        data["client_secret"] = client_secret
    resp = requests.post(KAKAO_TOKEN_URL, data=data, timeout=15)
    if resp.status_code != 200:
        raise RuntimeError(f"카카오 토큰 갱신 실패: {resp.status_code} {resp.text}")
    out = resp.json()
    return out["access_token"], out.get("refresh_token")


def chunk_text(text, limit=195):
    """혹시 메시지가 200자를 넘으면 줄 단위로 안전 분할(보통은 1개)."""
    pieces, chunks, cur = text.split("\n"), [], ""
    for line in pieces:
        candidate = line if not cur else cur + "\n" + line
        if len(candidate) <= limit:
            cur = candidate
        else:
            if cur:
                chunks.append(cur)
            cur = line[:limit]
    if cur:
        chunks.append(cur)
    return [c for c in chunks if c.strip()] or [text[:limit]]


def send_kakao_text(access_token, text, link_url, button=True):
    template = {
        "object_type": "text",
        "text": text,
        "link": {"web_url": link_url, "mobile_web_url": link_url},
    }
    if button:
        template["button_title"] = "전문 읽기"
    resp = requests.post(
        KAKAO_MEMO_URL,
        headers={"Authorization": f"Bearer {access_token}"},
        data={"template_object": json.dumps(template, ensure_ascii=False)},
        timeout=15,
    )
    if resp.status_code != 200:
        raise RuntimeError(f"카카오 전송 실패: {resp.status_code} {resp.text}")
    return resp.json()


def maybe_rotate_secret(new_refresh_token):
    pat, repo = os.environ.get("GH_PAT"), os.environ.get("GH_REPO")
    if not new_refresh_token:
        return
    if not (pat and repo):
        print("ℹ️ 새 refresh token이 발급됐지만 GH_PAT/GH_REPO가 없어 자동 갱신을 건너뜁니다.",
              file=sys.stderr)
        return
    from base64 import b64encode
    from nacl import encoding, public

    api = f"https://api.github.com/repos/{repo}/actions/secrets"
    headers = {"Authorization": f"Bearer {pat}", "Accept": "application/vnd.github+json"}
    key = requests.get(f"{api}/public-key", headers=headers, timeout=15).json()
    pk = public.PublicKey(key["key"].encode(), encoding.Base64Encoder())
    sealed = public.SealedBox(pk).encrypt(new_refresh_token.encode())
    requests.put(
        f"{api}/KAKAO_REFRESH_TOKEN", headers=headers,
        json={"encrypted_value": b64encode(sealed).decode(), "key_id": key["key_id"]},
        timeout=15,
    ).raise_for_status()
    print("✅ KAKAO_REFRESH_TOKEN 시크릿을 새 값으로 갱신했습니다.")


def do_send(payload, now):
    rest_api_key = os.environ["KAKAO_REST_API_KEY"]
    refresh_token = os.environ["KAKAO_REFRESH_TOKEN"]
    client_secret = os.environ.get("KAKAO_CLIENT_SECRET")
    access_token, new_refresh = refresh_access_token(rest_api_key, refresh_token, client_secret)

    chunks = chunk_text(payload["text"])
    for i, chunk in enumerate(chunks):
        send_kakao_text(access_token, chunk, payload["link"], button=(i == len(chunks) - 1))
    print(f"✅ 전송 완료 — 말풍선 {len(chunks)}개 ({now:%Y-%m-%d %H:%M} KST)")
    maybe_rotate_secret(new_refresh)


# ---------- 엔트리 ----------

def main():
    mode = sys.argv[1] if len(sys.argv) > 1 else "all"
    now = datetime.now(KST)

    payload = None
    if mode in ("build", "all"):
        payload = do_build(now)
    if mode in ("send", "all"):
        if payload is None:
            with open(MESSAGE_FILE, encoding="utf-8") as f:
                payload = json.load(f)
        do_send(payload, now)


if __name__ == "__main__":
    main()
