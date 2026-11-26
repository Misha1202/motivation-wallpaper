#!/usr/bin/env python3
"""Скачивает PT Serif (woff2, кириллица + латиница) и генерирует css/fonts.css."""

from __future__ import annotations

import re
import sys
from pathlib import Path
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parent.parent
FONT_DIR = ROOT / "web" / "fonts"
CSS_OUT = ROOT / "web" / "css" / "fonts.css"

CSS_URL = (
    "https://fonts.googleapis.com/css2"
    "?family=PT+Serif:wght@400;700&display=swap"
)
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36"

FACE_RE = re.compile(r"/\*\s*([a-z-]+)\s*\*/\s*@font-face\s*\{(.*?)\}", re.S)
WEIGHT_RE = re.compile(r"font-weight:\s*(\d+)")
URL_RE = re.compile(r"url\((https://[^)]+\.woff2)\)")
RANGE_RE = re.compile(r"unicode-range:\s*([^;]+);")


def main() -> int:
    request = Request(CSS_URL, headers={"User-Agent": UA})
    with urlopen(request, timeout=30) as response:
        css = response.read().decode("utf-8")

    FONT_DIR.mkdir(parents=True, exist_ok=True)
    CSS_OUT.parent.mkdir(parents=True, exist_ok=True)

    faces: list[str] = []
    for subset, body in FACE_RE.findall(css):
        weight_match = WEIGHT_RE.search(body)
        url_match = URL_RE.search(body)
        if not weight_match or not url_match:
            continue
        weight, url = weight_match.group(1), url_match.group(1)
        filename = f"pt-serif-{weight}-{subset}.woff2"
        target = FONT_DIR / filename
        if not target.exists():
            print(f"↓ {filename}")
            with urlopen(Request(url, headers={"User-Agent": UA}), timeout=30) as font:
                target.write_bytes(font.read())
        range_match = RANGE_RE.search(body)
        range_css = f"unicode-range:{range_match.group(1).strip()};" if range_match else ""
        faces.append(
            "@font-face{"
            "font-family:'PT Serif';"
            "font-style:normal;"
            f"font-weight:{weight};"
            "font-display:swap;"
            f"src:url('../fonts/{filename}') format('woff2');"
            f"{range_css}"
            "}"
        )

    CSS_OUT.write_text("\n".join(faces) + "\n", encoding="utf-8")
    total = sum(file.stat().st_size for file in FONT_DIR.glob("*.woff2")) / 1024
    print(f"✅ {len(faces)} @font-face, {total:.0f} КБ → {CSS_OUT.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
