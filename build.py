#!/usr/bin/env python3
"""
POMYJO 정적 사이트 빌드 스크립트

하는 일
  1. assets/site.css 를 각 HTML 페이지에 인라인으로 삽입한다.
     pomyjo.com 존에 "미매칭 경로 → 서브도메인" 리디렉트 규칙이 걸려 있어
     /assets/* 요청이 https://assets/....pomyjo.com/ 으로 301 되기 때문에,
     외부 스타일시트를 링크하면 apex 도메인에서 스타일이 적용되지 않는다.
     규칙을 고치기 전까지는 인라인이 유일하게 안전한 방법이다.
  2. 내부 링크와 canonical 을 확장자 없는 형태로 정규화한다.
     Cloudflare Pages 가 /foo.html → /foo 로 308 하므로 리디렉트 홉을 없앤다.

site.css 를 수정한 뒤에는 이 스크립트를 다시 실행할 것.
  python build.py
"""
import re
import pathlib

ROOT = pathlib.Path(__file__).parent
CSS = (ROOT / "assets" / "site.css").read_text(encoding="utf-8")

BEGIN = "<!-- build:css -->"
END = "<!-- /build:css -->"

LINK_RE = re.compile(
    r'[ \t]*<link[^>]+href=["\']/assets/site\.css["\'][^>]*>\n?'
)
BLOCK_RE = re.compile(
    re.escape(BEGIN) + r".*?" + re.escape(END) + r"\n?",
    re.S,
)

# .html 을 떼도 되는 내부 경로 (index.html 은 디렉터리로 처리)
HREF_RE = re.compile(r'href="(/[^"#?]*?)\.html((?:[#?][^"]*)?)"')
CANON_RE = re.compile(r'(<link rel="canonical" href="https://pomyjo\.com[^"]*?)\.html(")')


def normalize_href(m):
    path, tail = m.group(1), m.group(2)
    if path.endswith("/index"):
        path = path[: -len("index")]          # /guides/index → /guides/
    return f'href="{path}{tail}"'


def build_block():
    return f"{BEGIN}\n<style>\n{CSS.strip()}\n</style>\n{END}\n"


def process(path: pathlib.Path) -> str:
    html = path.read_text(encoding="utf-8")
    before = html

    # 1) 기존 인라인 블록 제거 후 재삽입 (재실행 가능하게)
    html = BLOCK_RE.sub("", html)
    if LINK_RE.search(html):
        html = LINK_RE.sub(build_block(), html, count=1)
        html = LINK_RE.sub("", html)          # 혹시 중복 링크가 있으면 제거
    else:
        # 링크가 이미 없으면 </head> 직전에 삽입
        html = html.replace("</head>", build_block() + "</head>", 1)

    # 2) 내부 링크 / canonical 정규화
    html = HREF_RE.sub(normalize_href, html)
    html = CANON_RE.sub(r"\1\2", html)
    html = html.replace(
        '<link rel="canonical" href="https://pomyjo.com/guides/"',
        '<link rel="canonical" href="https://pomyjo.com/guides/"',
    )

    if html != before:
        path.write_text(html, encoding="utf-8", newline="\n")
    return "갱신" if html != before else "변화 없음"


def main():
    pages = sorted(ROOT.glob("*.html")) + sorted(ROOT.glob("guides/*.html"))
    print(f"site.css {len(CSS):,} bytes 를 {len(pages)}개 페이지에 인라인합니다.\n")
    for p in pages:
        rel = p.relative_to(ROOT).as_posix()
        print(f"  {rel:<32} {process(p)}")
    print("\n완료. assets/site.css 는 원본으로 유지됩니다 (배포본은 인라인 사용).")


if __name__ == "__main__":
    main()
