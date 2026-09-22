"""Hangi yayıncılar Google Çeviri vekilini geçiriyor, günde bir kez.

Vekil bağlantısı ("başlığa dokun, haber Türkçe açılsın") yalnızca yayıncı
izin verdiğinde çalışır; vermeyen bir avuç site okuru Google hata sayfasına
düşürür. Yoklama alan adı başına yapılır — 558 kalem 44 alan adından gelir —
ve sonuç önbelleğe yazılır, böylece build sayfayı kurarken deneme yapmaz.

Reads   : data/news/YYYY-MM-DD.json
Writes  : data/translate-hosts.json  {"host": true|false, ...}
Usage   : python3 scripts/probe_proxy.py [--date …] [--recheck]
"""

import argparse
import datetime as dt
import json
import pathlib
import re
import sys
import time
import urllib.parse as up

import requests

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
import build  # noqa: E402 — aynı vekil adresini iki yerde kurmamak için

NEWS_DIR = ROOT / "data" / "news"
CACHE = ROOT / "data" / "translate-hosts.json"
UA = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/140.0 Safari/537.36")


# Yayıncının kararı olan kodlar. 429, 5xx ve zaman aşımı bugünün hâli, kalıcı
# hüküm değil: kaydedilirse bir sitenin okurları sessizce İngilizceye düşer.
DENIED = {401, 403, 404, 451}


def probe(host, url):
    """(verdict, detail) — verdict None ise "bugün anlaşılamadı", dosyaya yazılmaz.

    Tek tek ve aralıklı: paralel yoklama Google'ın hız sınırına takılıyor ve
    41 alan adının yarısı 429 dönüyordu — yani ölçmek istediğimiz şeyi ölçmek
    yerine kendi hızımızı ölçüyorduk. Haftada bir çalışan iş için acele yok.
    """
    for attempt in (1, 2):
        try:
            res = requests.get(build.proxy_url(url), headers={"User-Agent": UA}, timeout=25)
        except Exception as exc:
            return None, type(exc).__name__
        if res.status_code == 200:
            return True, "200"
        if res.status_code in DENIED:
            return False, str(res.status_code)
        if attempt == 1:
            time.sleep(20)  # 429/5xx: bir kez daha, bu kez sabırla
    return None, str(res.status_code)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--date", default=dt.datetime.now(dt.timezone.utc).date().isoformat())
    ap.add_argument("--recheck", action="store_true",
                    help="engelli bilinen alan adlarını da yeniden dene")
    args = ap.parse_args()

    day_file = NEWS_DIR / f"{args.date}.json"
    if not day_file.exists():
        sys.exit(f"{day_file.name} yok")
    items = json.loads(day_file.read_text(encoding="utf-8")).get("items", [])

    try:
        known = json.loads(CACHE.read_text(encoding="utf-8"))
    except Exception:
        known = {}

    # Alan adı başına bir örnek yeter; vekil karar verirken yolu değil sunucuyu
    # görür. Türkçe yayınlar hiç yoklanmaz: onlar zaten vekile girmiyor.
    sample = {}
    for item in items:
        host = up.urlsplit(item["url"]).hostname or ""
        if host and item.get("lang") != "tr":
            sample.setdefault(host, item["url"])

    # Brifingin kaynakçası da yoklanır: oradaki çip yalnızca alan adının
    # geçtiği ÖLÇÜLDÜYSE basılıyor (delil yüzeyinde iyimser varsayım yok),
    # ve o kaynaklar haber havuzundakilerle aynı olmak zorunda değil.
    for md in sorted((ROOT / "source").glob("*.md")):
        for raw in re.findall(r"https?://[^\s)\]]+", md.read_text(encoding="utf-8")):
            url = raw.rstrip(".,;")
            host = up.urlsplit(url).hostname or ""
            if host:
                sample.setdefault(host, url)
    todo = {h: u for h, u in sample.items() if args.recheck or h not in known}
    print(f"{len(sample)} alan adı · yoklanacak {len(todo)}")

    undecided = 0
    for n, (host, url) in enumerate(todo.items()):
        if n:
            time.sleep(2)
        verdict, detail = probe(host, url)
        if verdict is None:
            undecided += 1
            print(f"  ? {host}: {detail} (karar yok, geçer sayılıyor)")
            continue
        known[host] = verdict
        if not verdict:
            print(f"  ! {host}: {detail}")

    CACHE.write_text(json.dumps(known, ensure_ascii=False, indent=1, sort_keys=True) + "\n",
                     encoding="utf-8")
    blocked = {h for h in sample if known.get(h) is False}
    held = sum(1 for i in items
               if i.get("lang") != "tr" and (up.urlsplit(i["url"]).hostname or "") in blocked)
    print(f"  · {len(sample) - len(blocked)}/{len(sample)} alan adı geçiyor"
          f" · vekilsiz kalan {held} kalem"
          + (f" · {undecided} alan adı bugün karar vermedi" if undecided else ""))


if __name__ == "__main__":
    main()
