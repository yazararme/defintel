"""Translate the day's headlines into Turkish with Claude Code.

Runs on the subscription token, not an API key: the workflow installs the
Claude Code CLI and this script shells out to `claude -p`.

Reads   : data/news/YYYY-MM-DD.json
Writes  : the same file, adding "title_tr" to each item
Cache   : data/news/translations.json keyed by URL, so a headline is only ever
          translated once — reruns and repeated stories cost nothing.
Usage   : python3 scripts/translate_news.py [--date YYYY-MM-DD] [--batch 60]
"""

import argparse
import datetime as dt
import json
import pathlib
import re
import subprocess
import sys
import tempfile

ROOT = pathlib.Path(__file__).resolve().parent.parent
NEWS_DIR = ROOT / "data" / "news"
CACHE = NEWS_DIR / "translations.json"

PROMPT = """Aşağıdaki savunma sanayii haber başlıklarını Türkçeye çevir.

Kurallar:
- Özel isimler, şirket ve program adları, platform adları ve kısaltmalar olduğu gibi kalır: C-UAS, SHORAD, MADIS, HIMARS, NATO, Rheinmetall, Skyranger, Patriot gibi.
- Kalibre, para birimi ve sayılar korunur (30mm, 155 mm, $450 milyon).
- Başlık dili kullan: kısa, haber başlığı tonunda, nokta koyma.
- Başlık zaten Türkçeyse aynen geri ver.
- Çeviremediğin bir başlık olursa özgün hâlini geri ver; boş bırakma, açıklama yazma.

Çıktı: yalnızca JSON. Her satır için {"n": numara, "tr": "çeviri"} nesnelerinden oluşan bir dizi. Başka hiçbir metin yazma.

Başlıklar:
{items}"""


def load(path, default):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return default


def claude(prompt):
    """One `claude -p` call. Returns the assistant's text, or None on failure.

    Runs from a scratch directory: inside a repo the CLI wants to establish
    trust for the project first, which it cannot do without a terminal.
    """
    try:
        run = subprocess.run(
            ["claude", "-p", prompt, "--output-format", "json",
             "--dangerously-skip-permissions"],
            capture_output=True, text=True, timeout=600, cwd=tempfile.gettempdir(),
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        print(f"  ! claude çağrısı başarısız: {exc}")
        return None
    if run.returncode != 0:
        envelope = load_json_text(run.stdout) or {}
        detail = " | ".join(
            str(envelope.get(k)) for k in ("subtype", "is_error", "result", "error")
            if envelope.get(k) is not None
        ) or (run.stderr.strip() or run.stdout.strip())
        print(f"  ! claude çıkış kodu {run.returncode}: {detail[:400]}")
        return None
    envelope = load_json_text(run.stdout)
    if isinstance(envelope, dict):
        return envelope.get("result") or ""
    return run.stdout


def load_json_text(text):
    try:
        return json.loads(text)
    except Exception:
        return None


def parse_pairs(text):
    """The model is asked for bare JSON; tolerate a fenced block around it."""
    if not text:
        return []
    block = re.search(r"\[[\s\S]*\]", text)
    data = load_json_text(block.group(0)) if block else None
    if not isinstance(data, list):
        return []
    pairs = []
    for row in data:
        if isinstance(row, dict) and "n" in row and row.get("tr"):
            try:
                pairs.append((int(row["n"]), str(row["tr"]).strip()))
            except (TypeError, ValueError):
                continue
    return pairs


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--date", default=dt.datetime.now(dt.timezone.utc).date().isoformat())
    ap.add_argument("--batch", type=int, default=60)
    ap.add_argument("--limit", type=int, help="yalnızca ilk N başlığı çevir (deneme)")
    args = ap.parse_args()

    day_file = NEWS_DIR / f"{args.date}.json"
    if not day_file.exists():
        sys.exit(f"{day_file.name} yok; önce toplayıcı çalışmalı")

    day = json.loads(day_file.read_text(encoding="utf-8"))
    cache = load(CACHE, {})
    items = day.get("items", [])

    pending = [i for i in items if i["url"] not in cache]
    print(f"{len(items)} başlık · önbellekte {len(items) - len(pending)} · çevrilecek {len(pending)}")
    if args.limit and args.limit > 0:
        pending = pending[: args.limit]
        print(f"  (deneme: ilk {len(pending)} başlık)")

    for start in range(0, len(pending), args.batch):
        chunk = pending[start:start + args.batch]
        listing = "\n".join(f'{n}. {i["title"]}' for n, i in enumerate(chunk, 1))
        pairs = parse_pairs(claude(PROMPT.replace("{items}", listing)))
        got = 0
        for n, turkish in pairs:
            if 1 <= n <= len(chunk):
                cache[chunk[n - 1]["url"]] = turkish
                got += 1
        print(f"  · {start + 1}-{start + len(chunk)}: {got}/{len(chunk)} çevrildi")
        if not got:
            print("  ! bu parti boş döndü, kalanlar özgün başlıkla kalacak")

    for item in items:
        turkish = cache.get(item["url"])
        if turkish and turkish != item["title"]:
            item["title_tr"] = turkish

    day_file.write_text(json.dumps(day, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    CACHE.write_text(json.dumps(cache, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    translated = sum(1 for i in items if i.get("title_tr"))
    print(f"  · {translated}/{len(items)} başlık Türkçe · önbellek {len(cache)} kayıt")


if __name__ == "__main__":
    main()
