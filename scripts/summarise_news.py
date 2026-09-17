"""Two-sentence Turkish summaries for the headlines a reader actually sees.

Deliberately not "translate everything": the article text is fetched only for
the top N items of the day, summarised rather than reproduced, and cached by
URL so it is paid for once.

Reads   : data/news/YYYY-MM-DD.json
Writes  : the same file, adding "summary_tr" to the items it could summarise
Cache   : data/news/summaries.json
Usage   : python3 scripts/summarise_news.py [--date …] [--limit 20] [--batch 5]
"""

import argparse
import datetime as dt
import json
import pathlib
import re
import subprocess
import sys
import tempfile

import requests

ROOT = pathlib.Path(__file__).resolve().parent.parent
NEWS_DIR = ROOT / "data" / "news"
CACHE = NEWS_DIR / "summaries.json"
UA = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/140.0 Safari/537.36")
BODY_CHARS = 5000

PROMPT = """Aşağıda savunma sanayii haberlerinin metinleri var. Her biri için Türkçe, en fazla iki cümlelik bir özet yaz.

Kurallar:
- Ne oldu ve neden önemli — yorum, tahmin, tavsiye yok.
- Rakam, tarih, taraf adı varsa özete gir; özel isimler ve kısaltmalar olduğu gibi kalır.
- Metinden çıkarılamayan bir şey yazma. Metin yetersizse "summary" alanını boş bırak.
- Haber metnini olduğu gibi aktarma; kendi cümlelerinle özetle.

Çıktı: yalnızca JSON dizisi, her kalem için {"n": numara, "summary": "..."}. Başka metin yazma.

Haberler:
{items}"""


def load(path, default):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return default


def fetch_text(url):
    """Best-effort body text. Returns (text, reason-if-empty)."""
    try:
        res = requests.get(url, headers={"User-Agent": UA}, timeout=20)
        res.raise_for_status()
    except Exception as exc:
        return "", f"{type(exc).__name__}"
    html_text = res.text
    html_text = re.sub(r"(?is)<(script|style|nav|header|footer|aside)[^>]*>.*?</\1>", " ", html_text)
    paragraphs = re.findall(r"(?is)<p[^>]*>(.*?)</p>", html_text)
    text = " ".join(re.sub(r"<[^>]+>", " ", p) for p in paragraphs)
    text = re.sub(r"\s+", " ", text).strip()
    if len(text) < 300:
        return "", "metin kısa"
    return text[:BODY_CHARS], ""


def claude(prompt):
    try:
        run = subprocess.run(
            ["claude", "-p", prompt, "--output-format", "json",
             "--dangerously-skip-permissions"],
            capture_output=True, text=True, timeout=600, cwd=tempfile.gettempdir(),
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        print(f"  ! claude çağrısı başarısız: {exc}")
        return None
    envelope = load_json_text(run.stdout) or {}
    if run.returncode != 0:
        print(f"  ! claude çıkış kodu {run.returncode}: {str(envelope.get('result'))[:200]}")
        return None
    return envelope.get("result", "")


def load_json_text(text):
    try:
        return json.loads(text)
    except Exception:
        return None


def parse_pairs(text):
    if not text:
        return []
    block = re.search(r"\[[\s\S]*\]", text)
    data = load_json_text(block.group(0)) if block else None
    if not isinstance(data, list):
        return []
    out = []
    for row in data:
        if isinstance(row, dict) and row.get("summary"):
            try:
                out.append((int(row["n"]), str(row["summary"]).strip()))
            except (TypeError, ValueError):
                continue
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--date", default=dt.datetime.now(dt.timezone.utc).date().isoformat())
    ap.add_argument("--limit", type=int, default=20)
    ap.add_argument("--batch", type=int, default=5)
    args = ap.parse_args()

    day_file = NEWS_DIR / f"{args.date}.json"
    if not day_file.exists():
        sys.exit(f"{day_file.name} yok")

    day = json.loads(day_file.read_text(encoding="utf-8"))
    cache = load(CACHE, {})
    items = day.get("items", [])
    todo = [i for i in items if i["url"] not in cache][: args.limit]
    print(f"{len(items)} kalem · özetlenecek {len(todo)}")

    fetched, failures = [], []
    for item in todo:
        text, reason = fetch_text(item["url"])
        if text:
            fetched.append((item, text))
        else:
            failures.append((item["source"], reason))
    print(f"  · metin alınan {len(fetched)}/{len(todo)}")
    for source, reason in failures:
        print(f"    ! {source}: {reason}")

    for start in range(0, len(fetched), args.batch):
        chunk = fetched[start:start + args.batch]
        listing = "\n\n".join(
            f'{n}. BAŞLIK: {item["title"]}\nMETİN: {text}'
            for n, (item, text) in enumerate(chunk, 1)
        )
        pairs = parse_pairs(claude(PROMPT.replace("{items}", listing)))
        for n, summary in pairs:
            if 1 <= n <= len(chunk):
                cache[chunk[n - 1][0]["url"]] = summary
        print(f"  · {start + 1}-{start + len(chunk)}: {len(pairs)}/{len(chunk)} özet")

    for item in items:
        if cache.get(item["url"]):
            item["summary_tr"] = cache[item["url"]]

    day_file.write_text(json.dumps(day, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    CACHE.write_text(json.dumps(cache, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print(f"  · {sum(1 for i in items if i.get('summary_tr'))} kalemde özet · önbellek {len(cache)}")


if __name__ == "__main__":
    main()
