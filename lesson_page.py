# -*- coding: utf-8 -*-
"""오늘의 강의 페이지 + '지난 강의 모아보기' 목록 페이지 생성기 (GitHub Pages용).

- docs/lessons/<날짜>.html : 각 강의(계속 쌓임 = 자동 아카이브)
- docs/index.html          : 지난 강의를 모두 모아 보여주는 목록(최신순)
카카오 메시지의 링크가 이 페이지들을 연다.
"""
import os
import re
import glob
import html
from datetime import datetime
from string import Template

_LESSON = Template("""<!DOCTYPE html>
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
  .foot { margin-top:40px; text-align:center; font-size:14px; }
  .foot a { color:#3a6ea5; text-decoration:none; font-weight:600; }
  .foot .sub { display:block; margin-top:12px; color:#b0b0b0; font-size:13px; }
  @media (prefers-color-scheme: dark) {
    body { background:#191919; color:#e9e9e9; }
    .label { background:#e9e9e9; color:#191919; }
    .next { background:#272727; color:#bcbcbc; }
    .foot a { color:#7fb0e8; }
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
    <div class="foot">
      <a href="../">📚 지난 강의 전체 보기</a>
      <span class="sub">매일 아침 · 나의 교양 강의</span>
    </div>
  </div>
</body>
</html>
""")

_INDEX = Template("""<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>나의 교양 강의 · 모아보기</title>
<style>
  :root { color-scheme: light dark; }
  body { margin:0; background:#f6f5f2; color:#232323;
    font-family:-apple-system,BlinkMacSystemFont,"Apple SD Gothic Neo","Pretendard","Malgun Gothic",sans-serif;
    -webkit-text-size-adjust:100%; }
  .wrap { max-width:680px; margin:0 auto; padding:34px 22px 72px; }
  h1 { font-size:26px; margin:0 0 6px; letter-spacing:-.01em; }
  .sub { color:#8a8a8a; font-size:14px; margin:0 0 26px; }
  ul { list-style:none; margin:0; padding:0; }
  li { margin:0 0 12px; }
  li a { display:block; padding:16px 18px; background:#fff; border-radius:14px;
    text-decoration:none; color:inherit; box-shadow:0 1px 3px rgba(0,0,0,.06); }
  .d { display:block; font-size:13px; color:#9a9a9a; }
  .lb { display:inline-block; margin:6px 0 4px; padding:2px 9px; border-radius:999px;
    background:#efeee9; color:#555; font-size:12px; font-weight:600; }
  .t { display:block; font-size:17px; font-weight:600; line-height:1.45; margin-top:2px; }
  .foot { margin-top:36px; text-align:center; color:#b0b0b0; font-size:13px; }
  @media (prefers-color-scheme: dark) {
    body { background:#191919; color:#e9e9e9; }
    li a { background:#242424; box-shadow:none; }
    .lb { background:#333; color:#bbb; }
  }
</style>
</head>
<body>
  <div class="wrap">
    <h1>📚 나의 교양 강의</h1>
    <p class="sub">지난 강의 모아보기 · 최신순</p>
    <ul>
      $rows
    </ul>
    <div class="foot">매일 아침 · 하나씩 쌓아가는 교양</div>
  </div>
</body>
</html>
""")


def _paragraphs_html(body):
    parts = [p.strip() for p in re.split(r"\n\s*\n", body.strip()) if p.strip()]
    return "\n    ".join(f"<p>{html.escape(p).replace(chr(10), '<br>')}</p>" for p in parts)


def render_html(date_human, label, title, body, next_line):
    next_html = f'<div class="next">🔜 다음 시간: {html.escape(next_line)}</div>' if next_line else ""
    return _LESSON.safe_substitute(
        date_human=html.escape(date_human),
        label=html.escape(label),
        title=html.escape(title),
        paragraphs=_paragraphs_html(body),
        next_html=next_html,
    )


def write_pages(docs_dir, date_str, date_human, label, title, body, next_line):
    """오늘 강의 페이지(dated)를 쓴다. dated 파일의 상대경로 반환."""
    lessons_dir = os.path.join(docs_dir, "lessons")
    os.makedirs(lessons_dir, exist_ok=True)
    open(os.path.join(docs_dir, ".nojekyll"), "w").close()  # Jekyll 처리 비활성화
    rel = f"lessons/{date_str}.html"
    with open(os.path.join(docs_dir, rel), "w", encoding="utf-8") as f:
        f.write(render_html(date_human, label, title, body, next_line))
    return rel


def _extract(path):
    """저장된 강의 HTML에서 제목과 라벨을 뽑아낸다."""
    with open(path, encoding="utf-8") as f:
        s = f.read()
    mt = re.search(r"<h1>(.*?)</h1>", s, re.S)
    ml = re.search(r'<span class="label">(.*?)</span>', s, re.S)
    title = html.unescape(mt.group(1).strip()) if mt else "(제목 없음)"
    label = html.unescape(ml.group(1).strip()) if ml else ""
    return title, label


def write_index(docs_dir):
    """docs/lessons/*.html 을 모두 훑어 '지난 강의 모아보기' index.html 을 만든다."""
    lessons_dir = os.path.join(docs_dir, "lessons")
    files = sorted(glob.glob(os.path.join(lessons_dir, "*.html")), reverse=True)
    rows = []
    for path in files:
        date_str = os.path.splitext(os.path.basename(path))[0]
        try:
            d = datetime.strptime(date_str, "%Y-%m-%d")
            date_disp = f"{d.year}년 {d.month}월 {d.day}일 (" + "월화수목금토일"[d.weekday()] + ")"
        except ValueError:
            date_disp = date_str
        title, label = _extract(path)
        rows.append(
            f'<li><a href="lessons/{date_str}.html">'
            f'<span class="d">{html.escape(date_disp)}</span>'
            f'<span class="lb">{html.escape(label)}</span>'
            f'<span class="t">{html.escape(title)}</span></a></li>'
        )
    body = "\n      ".join(rows) if rows else "<li>아직 강의가 없어요.</li>"
    with open(os.path.join(docs_dir, "index.html"), "w", encoding="utf-8") as f:
        f.write(_INDEX.safe_substitute(rows=body))
    open(os.path.join(docs_dir, ".nojekyll"), "w").close()
