# -*- coding: utf-8 -*-
"""오늘의 강의를 보여줄 정적 HTML 페이지 생성기 (GitHub Pages용).

docs/lessons/<날짜>.html 과 docs/index.html(최신 강의)을 만든다.
카카오 메시지의 '전문 읽기' 버튼이 이 페이지를 연다.
"""
import os
import re
import html
from string import Template

_PAGE = Template("""<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>$title · 아침 강의</title>
<style>
  :root { color-scheme: light dark; }
  body { margin:0; background:#f6f5f2; color:#232323;
    font-family:-apple-system,BlinkMacSystemFont,"Apple SD Gothic Neo","Pretendard","Malgun Gothic",sans-serif;
    line-height:1.78; -webkit-text-size-adjust:100%; }
  .wrap { max-width:680px; margin:0 auto; padding:34px 22px 72px; }
  .date { color:#8a8a8a; font-size:14px; letter-spacing:.02em; }
  .label { display:inline-block; margin-top:10px; padding:4px 13px; border-radius:999px;
    background:#2b2b2b; color:#fff; font-size:13px; font-weight:600; }
  h1 { font-size:25px; line-height:1.4; margin:14px 0 26px; letter-spacing:-.01em; }
  .body p { margin:0 0 19px; font-size:17px; }
  .next { margin-top:34px; padding:16px 18px; background:#eceae4; border-radius:14px;
    font-size:15px; color:#555; }
  .foot { margin-top:44px; color:#b0b0b0; font-size:13px; text-align:center; }
  @media (prefers-color-scheme: dark) {
    body { background:#191919; color:#e9e9e9; }
    .label { background:#e9e9e9; color:#191919; }
    .next { background:#272727; color:#bcbcbc; }
  }
</style>
</head>
<body>
  <div class="wrap">
    <div class="date">$date_human</div>
    <span class="label">$label</span>
    <h1>$title</h1>
    <div class="body">$paragraphs</div>
    $next_html
    <div class="foot">매일 아침 9:40 · 나의 교양 강의 📚</div>
  </div>
</body>
</html>
""")


def _paragraphs_html(body):
    parts = [p.strip() for p in re.split(r"\n\s*\n", body.strip()) if p.strip()]
    out = []
    for p in parts:
        safe = html.escape(p).replace("\n", "<br>")
        out.append(f"<p>{safe}</p>")
    return "\n    ".join(out)


def render_html(date_human, label, title, body, next_line):
    next_html = f'<div class="next">🔜 다음 시간: {html.escape(next_line)}</div>' if next_line else ""
    return _PAGE.safe_substitute(
        date_human=html.escape(date_human),
        label=html.escape(label),
        title=html.escape(title),
        paragraphs=_paragraphs_html(body),
        next_html=next_html,
    )


def write_pages(docs_dir, date_str, date_human, label, title, body, next_line):
    """오늘 강의 페이지(dated)와 index.html(최신)을 쓴다. dated 파일의 상대경로 반환."""
    lessons_dir = os.path.join(docs_dir, "lessons")
    os.makedirs(lessons_dir, exist_ok=True)
    # Jekyll 처리 비활성화(파일을 그대로 서빙)
    open(os.path.join(docs_dir, ".nojekyll"), "w").close()

    page = render_html(date_human, label, title, body, next_line)
    rel = f"lessons/{date_str}.html"
    with open(os.path.join(docs_dir, rel), "w", encoding="utf-8") as f:
        f.write(page)
    with open(os.path.join(docs_dir, "index.html"), "w", encoding="utf-8") as f:
        f.write(page)  # 기본 주소(/)는 항상 최신 강의를 보여줌
    return rel
