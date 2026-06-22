# 아침 브리핑 (카카오 '나에게 보내기' + 웹 강의)

매일 아침 **09:40 (KST)** 에 GitHub Actions가 자동 실행되어,
내 카카오톡 '나와의 채팅'으로 **짧은 한 통(리마인더 + 오늘 강의 제목 + '전문 읽기' 버튼)** 을 보냅니다.
'전문 읽기'를 누르면 **그날 강의 전체가 깔끔한 웹페이지(GitHub Pages)** 로 열려요.
내 컴퓨터나 앱이 꺼져 있어도 클라우드에서 실행됩니다.

```
GitHub Actions (매일 00:40 UTC = 09:40 KST)
   ├─ 1) python send_briefing.py build   # 강의 생성 + docs/ 웹페이지 작성
   ├─ 2) git push docs/                   # GitHub Pages 게시
   └─ 3) python send_briefing.py send     # 짧은 카톡 한 통 + '전문 읽기' 링크
```

## 보내는 내용

**리마인더 (날짜에 해당될 때만)**
- 매월 1일 — 외모 체크 (손발톱, 마사지, 헤어)
- 매월 15일 — 외모 체크 (피부, 체중, 뷰티 루틴)
- 매월 22일 — 돈 관리 (보험 출금, 적금, 지출 결산)
- 1·3주차 주말 (1~7일·15~21일의 토/일) — 대청소

**오늘의 강의 (요일별 연재 — 매주 한 강씩 진도)**
- 월: 영화사 · 화: 음악사 · 수: AI 공부 · 목: 도예/건축/예술 · 금: 시 읽기
- 초보자용 커리큘럼(`curriculum.py`)을 순서대로 따라가며, 매주 그 요일에 다음 강으로 넘어갑니다.
- 각 강은 600~900자 정도의 알찬 본문으로, '지난 시간 ↔ 오늘 ↔ 다음 예고'로 이어져요.
- 토·일: 가벼운 자유 주제

---

## 설치 (한 번만)

### 1. 카카오 앱 만들기 + 토큰 발급

1. https://developers.kakao.com → **내 애플리케이션 → 애플리케이션 추가하기**
2. **앱 키**에서 `REST API 키` 복사 → `KAKAO_REST_API_KEY`
3. **카카오 로그인 → 활성화 설정** ON
4. **카카오 로그인 → Redirect URI** 에 `https://localhost` 등록
5. **카카오 로그인 → 동의항목** 에서 **카카오톡 메시지 전송**(`talk_message`) 사용 ON
   - (참고) **보안 → Client Secret** 은 '사용 안 함' 권장. 켜면 토큰 발급/전송에 값이 필요해요.
6. 터미널에서 토큰 발급:
   ```bash
   pip install requests
   python get_kakao_token.py
   ```
   브라우저 로그인·동의 후 주소창의 `code=...` 를 붙여넣으면 `KAKAO_REFRESH_TOKEN` 이 출력됩니다.

### 2. Claude API 키 준비

- https://console.anthropic.com → **Billing** 결제수단/크레딧 등록 → **API Keys** 에서 발급 → `ANTHROPIC_API_KEY`
- 하루 한 번 강의 1개 생성이라 비용은 적습니다(월 대략 500~600원).

### 3. GitHub에 올리기 (저장소는 **public** 권장)

> GitHub Pages를 무료로 쓰려면 public 저장소가 가장 간단합니다.
> 시크릿(토큰·API 키)은 public이어도 **암호화되어 안전**하고 코드·로그에 노출되지 않아요.
> 공개되는 건 코드와 강의 본문뿐이며 민감 정보가 아닙니다.

```bash
cd morning-briefing
git init
git add .
git commit -m "아침 브리핑"
# GitHub에서 빈 public 저장소를 만든 뒤:
git remote add origin https://github.com/<내아이디>/morning-briefing.git
git branch -M main
git push -u origin main
```

### 4. 시크릿 등록

GitHub 저장소 → **Settings → Secrets and variables → Actions → New repository secret**

| 이름 | 값 |
|------|-----|
| `KAKAO_REST_API_KEY` | 카카오 REST API 키 |
| `KAKAO_REFRESH_TOKEN` | 위에서 발급한 refresh token |
| `ANTHROPIC_API_KEY` | Claude API 키 |
| `KAKAO_CLIENT_SECRET` | (선택) Client Secret을 '사용함'으로 켰을 때만 |

### 5. GitHub Pages 켜기

저장소 → **Settings → Pages** → **Source: Deploy from a branch** →
Branch: **main**, 폴더: **/docs** → Save.
첫 강의가 한 번 실행되면 `https://<내아이디>.github.io/morning-briefing/` 에서 보입니다.

### 6. 바로 테스트

저장소 → **Actions → morning-briefing → Run workflow** 클릭 → 즉시 1회 실행.
카톡 한 통이 오고, '전문 읽기'를 **휴대폰에서** 누르면 강의 페이지가 열립니다.
이후로는 매일 09:40 KST 경에 자동 실행돼요.

> 📱 '전문 읽기' 링크는 **휴대폰**에서 잘 열립니다. PC 카톡은 "모바일에서 확인"만 뜰 수 있어요(카톡 PC 한계).
> 또 게시 직후 1~2분은 페이지 반영이 늦을 수 있으니, 막 받은 직후 404가 보이면 잠시 뒤 새로고침하세요.

---

## 로컬에서 먼저 테스트하기 (선택)

```bash
pip install -r requirements.txt
export KAKAO_REST_API_KEY=...
export KAKAO_REFRESH_TOKEN=...
export ANTHROPIC_API_KEY=...
python send_briefing.py            # build + send 한 번에
```
- 카톡 한 통이 도착하고, 강의 페이지는 `docs/lessons/<날짜>.html` 로 생성됩니다(브라우저로 열어 미리보기).
- 단, '전문 읽기' 링크는 **GitHub Pages 배포 후에만** 실제로 열립니다(로컬 테스트 땐 임시로 네이버 검색으로 연결).

## 토큰 자동 갱신 (선택, 권장)

카카오 refresh token은 약 2개월 유효합니다. 자동 저장하지 않으면 약 2개월마다 1번 단계를 다시 해야 해요.
자동화하려면:

1. GitHub → **Settings → Developer settings → Fine-grained tokens** 에서 토큰 생성
   - Repository access: 이 저장소만 / Permissions → **Secrets: Read and write**
2. 그 값을 저장소 시크릿 `GH_PAT` 로 등록

---

## 자주 겪는 문제

- **카톡이 안 와요**: Actions 로그 확인. 토큰 만료(재발급), 동의항목(`talk_message`) 미설정이 흔한 원인.
- **'전문 읽기'가 404**: Pages 설정(5번)을 했는지, 게시 후 1~2분 지났는지 확인하세요.
- **시간이 안 맞아요**: GitHub Actions 예약 실행은 부하에 따라 몇 분~수십 분 늦거나 드물게
  건너뛸 수 있습니다(정시 보장 아님). 더 정확하려면 Cloudflare Workers Cron으로 옮길 수 있어요.
- **내용을 바꾸고 싶어요**: 강의 커리큘럼은 `curriculum.py`, 리마인더는 `build_reminders()`,
  강의 길이·말투는 `generate_body()`, 페이지 디자인은 `lesson_page.py`, 카톡 문구는 `compose_kakao_message()`.
- **진도를 바꾸고 싶어요**: `send_briefing.py`의 `CURRICULUM_START`(시작 기준 월요일)를 조정.
  커리큘럼을 한 바퀴 돌면 자동으로 1강부터 다시 순환합니다.
