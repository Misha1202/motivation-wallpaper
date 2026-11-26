#!/usr/bin/env python3
"""
Собирает цитаты с azbyka.ru в web/quotes.json.

Запуск:
    python3 tools/fetch_quotes.py            # все ID из ЦИТАТЫ.txt
    python3 tools/fetch_quotes.py --limit 20 # только первые 20 (для теста)
    python3 tools/fetch_quotes.py --workers 3

Скрипт инкрементальный: уже собранные цитаты (по source_id) сохраняются,
повторный запуск докачивает только отсутствующие страницы.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parent.parent
IDS_FILE = ROOT / "ЦИТАТЫ.txt"
OUT_FILE = ROOT / "web" / "quotes.json"

BASE_URL = "https://azbyka.ru/otechnik/Biblia/tsitaty-iz-biblii/{id}"
UA = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124 Safari/537.36"

# Аббревиатуры книг: «Еф. 2,10», «Мф.7,17–18», «Псалом 22:1», «1 Кор. 13,4»
REF_RE = re.compile(
    r"(?P<ref>"
    r"(?:[1-3]\s*)?"
    r"(?:[А-ЯЁ][а-яё]+\.?|[A-Z][a-z]+\.?)"
    r"\s*\d+"
    r"(?:\s*[,:]\s*\d+(?:\s*[–—-]\s*\d+)?)?"
    r"(?:\s*;\s*(?:[1-3]\s*)?(?:[А-ЯЁ][а-яё]+\.?)\s*\d+(?:\s*[,:]\s*\d+)?)*"
    r")\s*$"
)

ODD_TEXTS = {
    "читать далее",
    "поделиться",
    "цитаты из библии",
}


def load_ids() -> list[tuple[str, str]]:
    """Возвращает [(id, категория)] из ЦИТАТЫ.txt."""
    items: list[tuple[str, str]] = []
    if not IDS_FILE.exists():
        print(f"⚠️  Нет файла {IDS_FILE.name}, беру запасной список", file=sys.stderr)
        return [(str(i), "") for i in (162, 15, 28, 39, 51, 95, 121, 155, 188, 217)]

    for line in IDS_FILE.read_text(encoding="utf-8").splitlines():
        if "\t" not in line:
            continue
        raw_id, category = line.split("\t", 1)
        raw_id = raw_id.strip()
        if raw_id.isdigit():
            items.append((raw_id, category.strip()))
    return items


def clean_html(block: str) -> str:
    text = re.sub(r"<br\s*/?>", "\n", block, flags=re.I)
    text = re.sub(r"<[^>]+>", "", text)
    text = text.replace("&nbsp;", " ").replace("&laquo;", "«").replace("&raquo;", "»")
    text = text.replace("&mdash;", "—").replace("&ndash;", "–").replace("&quot;", '"')
    text = text.replace("&amp;", "&").replace("&#8212;", "—").replace("&#160;", " ")
    text = text.replace("\u00a0", " ").replace("\u200b", "")
    text = " ".join(text.split())
    # На сайте обрывок стиха иногда начинается с «..» или тире — убираем.
    text = re.sub(r"^[.\u2026\s—–-]+", "", text)
    text = re.sub(r"\s+([,.;:!?])", r"\1", text)
    return text.strip()


def split_ref(full_text: str) -> tuple[str, str]:
    """Отделяет ссылку на стих от текста цитаты."""
    match = REF_RE.search(full_text)
    if not match:
        return full_text, ""
    ref = match.group("ref").strip()
    quote = full_text[: match.start()].strip()
    # Слишком короткий остаток — значит regex съел часть цитаты, не трогаем.
    if len(quote) < 12:
        return full_text, ""
    return quote, ref


def fetch_page(quote_id: str, category: str, attempts: int = 3) -> list[dict]:
    url = BASE_URL.format(id=quote_id)
    last_error = ""

    for attempt in range(1, attempts + 1):
        try:
            request = Request(url, headers={"User-Agent": UA, "Accept-Language": "ru"})
            with urlopen(request, timeout=20) as response:
                if response.status != 200:
                    last_error = f"HTTP {response.status}"
                    break
                html = response.read().decode("utf-8", errors="replace")
            break
        except HTTPError as exc:
            last_error = f"HTTP {exc.code}"
            if exc.code in (403, 429):
                time.sleep(2 * attempt)
                continue
            break
        except (URLError, TimeoutError, OSError) as exc:
            last_error = str(exc)
            time.sleep(1.5 * attempt)
    else:
        print(f"  ✗ {quote_id}: {last_error}", file=sys.stderr)
        return []

    if not html:
        return []

    blocks = re.findall(r'<p class="txt">(.*?)</p>', html, re.S | re.I)
    if not blocks:
        blocks = re.findall(r'<p[^>]*class="[^"]*\btxt\b[^"]*"[^>]*>(.*?)</p>', html, re.S | re.I)

    results: list[dict] = []
    for block in blocks:
        full = clean_html(block)
        if not full or len(full) < 10:
            continue
        if full.lower().strip(" .") in ODD_TEXTS:
            continue
        quote, ref = split_ref(full)
        results.append(
            {
                "source_id": quote_id,
                "category": category,
                "text": quote,
                "ref": ref,
            }
        )
    return results


def dedupe(quotes: list[dict]) -> list[dict]:
    seen: set[str] = set()
    result: list[dict] = []
    for quote in quotes:
        key = re.sub(r"\s+", " ", quote["text"]).strip().lower()
        if key in seen:
            continue
        seen.add(key)
        result.append(quote)
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--limit", type=int, default=0, help="обработать только N ID")
    parser.add_argument("--workers", type=int, default=3, help="параллельных запросов")
    parser.add_argument("--delay", type=float, default=0.25, help="пауза перед запросом, сек")
    args = parser.parse_args()

    ids = load_ids()
    if args.limit:
        ids = ids[: args.limit]

    existing: dict[str, dict] = {}
    if OUT_FILE.exists():
        try:
            payload = json.loads(OUT_FILE.read_text(encoding="utf-8"))
            for quote in payload.get("quotes", []):
                existing.setdefault(quote["source_id"], quote)
            print(f"ℹ️  Уже собрано: {len(existing)} страниц")
        except (json.JSONDecodeError, KeyError):
            print("⚠️  quotes.json повреждён, пересобираю", file=sys.stderr)

    todo = [(qid, cat) for qid, cat in ids if qid not in existing]
    print(f"→ Страниц к загрузке: {len(todo)} из {len(ids)} (воркеров: {args.workers})")
    if not todo:
        write_output(existing, ids)
        return 0

    started = time.time()
    done = 0
    by_id: dict[str, list[dict]] = {qid: [existing[qid]] for qid in existing}
    failures = 0

    with ThreadPoolExecutor(max_workers=max(1, args.workers)) as pool:
        futures = {}
        for quote_id, category in todo:
            time.sleep(args.delay)
            futures[pool.submit(fetch_page, quote_id, category)] = quote_id

        for future in as_completed(futures):
            quote_id = futures[future]
            done += 1
            try:
                batch = future.result()
            except Exception as exc:  # noqa: BLE001
                print(f"  ✗ {quote_id}: {exc}", file=sys.stderr)
                failures += 1
                batch = []
            if batch:
                by_id[quote_id] = batch
            else:
                failures += 1
            if done % 25 == 0 or done == len(todo):
                elapsed = time.time() - started
                print(f"  … {done}/{len(todo)} страниц, {elapsed:.0f}s")

    write_output(by_id, ids, failures=failures, elapsed=time.time() - started)
    return 0


def write_output(by_id: dict[str, list[dict]], ids: list[tuple[str, str]], failures: int = 0, elapsed: float = 0) -> None:
    order = {qid: index for index, (qid, _) in enumerate(ids)}
    quotes = [quote for qid in sorted(by_id, key=lambda value: order.get(value, 10**9)) for quote in by_id[qid]]
    quotes = dedupe(quotes)
    quotes.sort(key=lambda item: (order.get(item["source_id"], 10**9), item["text"]))

    OUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "generated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "pages": len(by_id),
        "count": len(quotes),
        "quotes": quotes,
    }
    OUT_FILE.write_text(json.dumps(payload, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    size_kb = OUT_FILE.stat().st_size / 1024
    print(f"✅ {len(quotes)} цитат из {len(by_id)} страниц → {OUT_FILE.relative_to(ROOT)} ({size_kb:.0f} КБ)")
    if failures:
        print(f"⚠️  Не удалось загрузить страниц: {failures} (перезапуск докачает)", file=sys.stderr)
    if elapsed:
        print(f"⏱  {elapsed:.0f}s")


if __name__ == "__main__":
    raise SystemExit(main())
