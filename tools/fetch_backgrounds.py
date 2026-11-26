#!/usr/bin/env python3
"""
Скачивает портретные фото с Unsplash для статичной части сайта.

Запускается в GitHub Actions перед деплоем: фото не коммитятся в репозиторий,
а попадают в артефакт Pages. Если ключа нет или API недоступен — сайт
продолжает работать на процедурных фонах (exit 0).

    UNSPLASH_ACCESS_KEY=... python3 tools/fetch_backgrounds.py --count 60
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
import time
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parent.parent
OUT_DIR = ROOT / "web" / "backgrounds"
MANIFEST = OUT_DIR / "manifest.json"

API_URL = "https://api.unsplash.com/photos/random"
QUERIES = [
    "mountain landscape",
    "misty forest",
    "calm sea horizon",
    "sunrise mountains",
    "clouds sky",
    "lake reflection",
    "green hills",
    "desert dunes",
    "snowy peaks",
    "forest fog",
    "golden hour landscape",
    "quiet beach",
]
# Публичный demo-ключ из старой версии приложения. Лучше задать секрет
# UNSPLASH_ACCESS_KEY в настройках репозитория и отозвать этот ключ.
FALLBACK_KEY = "t9SeuIi4nAnCIb2vIPnA9hAYx4CbIbrbgdTHrBSDjZc"


def api_get(url: str, key: str, timeout: int = 25) -> list[dict]:
    request = Request(url, headers={"Authorization": f"Client-ID {key}", "Accept-Version": "v1"})
    with urlopen(request, timeout=timeout) as response:
        payload = json.loads(response.read().decode("utf-8"))
    return payload if isinstance(payload, list) else [payload]


def download(url: str, target: Path) -> int:
    request = Request(url, headers={"User-Agent": "motivation-wallpaper/2.0"})
    with urlopen(request, timeout=45) as response:
        data = response.read()
    target.write_bytes(data)
    return len(data)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--count", type=int, default=60, help="сколько фото скачать")
    parser.add_argument("--per-request", type=int, default=30, help="максимум 30 у Unsplash")
    args = parser.parse_args()

    key = os.environ.get("UNSPLASH_ACCESS_KEY", "").strip() or FALLBACK_KEY
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    # Чистим прошлый прогон, чтобы не тащить устаревшие фото в артефакт.
    for old in OUT_DIR.glob("*.jpg"):
        old.unlink()

    photos: list[dict] = []
    per_request = max(1, min(30, args.per_request))
    seen: set[str] = set()

    try:
        while len(photos) < args.count:
            want = min(per_request, args.count - len(photos))
            query = random.choice(QUERIES)
            params = urlencode(
                {
                    "query": query,
                    "orientation": "portrait",
                    "count": want,
                    "content_filter": "high",
                }
            )
            batch = api_get(f"{API_URL}?{params}", key)
            added = 0
            for photo in batch:
                photo_id = photo.get("id", "")
                if not photo_id or photo_id in seen:
                    continue
                seen.add(photo_id)
                raw = photo.get("urls", {}).get("raw", "")
                if not raw:
                    continue
                url = f"{raw}&w=1170&h=2532&fit=crop&crop=entropy&q=82&fm=jpg"
                index = len(photos) + 1
                filename = f"{index:02d}-{photo_id}.jpg"
                target = OUT_DIR / filename
                try:
                    size = download(url, target)
                except (HTTPError, URLError, TimeoutError, OSError) as exc:
                    print(f"  ✗ {photo_id}: {exc}", file=sys.stderr)
                    continue
                if size < 20_000:
                    target.unlink(missing_ok=True)
                    continue
                photos.append(
                    {
                        "file": filename,
                        "author": photo.get("user", {}).get("name", ""),
                        "link": photo.get("links", {}).get("html", ""),
                        "color": photo.get("color", "#101018"),
                        "query": query,
                    }
                )
                added += 1
            print(f"→ «{query}»: +{added} (всего {len(photos)})")
            if not batch:
                break
            time.sleep(1)
    except (HTTPError, URLError, TimeoutError, OSError, ValueError) as exc:
        print(f"⚠️  Unsplash недоступен: {exc}", file=sys.stderr)

    manifest = {
        "generated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "photos": photos,
    }
    MANIFEST.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    total_mb = sum((OUT_DIR / photo["file"]).stat().st_size for photo in photos) / 1024 / 1024
    print(f"✅ {len(photos)} фото ({total_mb:.1f} МБ) → {MANIFEST.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
