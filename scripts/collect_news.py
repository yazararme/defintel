"""Collect the day's candidate headlines from the source inventory.

Why this runs here and not inside the agent: pulling ~70 feeds is mechanical
work. Done in Python it is complete (every item, exact date, exact link),
repeatable and fast; done with an agent's fetch tool it comes back summarised
and truncated. The agent gets the finished candidate list and spends its budget
on judgement instead.

Reads   : kaynaklar.json from the Drive folder (the customer edits it there)
Writes  : data/news/YYYY-MM-DD.json   — candidates, deduped, categorised
Usage   : python3 scripts/collect_news.py [--dry-run] [--hours 48]
"""

import argparse
import concurrent.futures
import datetime as dt
import html
import json
import os
import pathlib
import re
import sys
import unicodedata
import xml.etree.ElementTree as ET

import requests
from google.auth.transport.requests import Request
from google.oauth2 import service_account

ROOT = pathlib.Path(__file__).resolve().parent.parent
OUT_DIR = ROOT / "data" / "news"
DRIVE_API = "https://www.googleapis.com/drive/v3/files"
UA = "DefintelBot/1.0 (+https://defintel.shadovi.com)"
TIMEOUT = 25

# Feeds that carry general news need a defence filter; specialised feeds don't.
DEFENCE_TERMS = [
    "drone", "dron", "uav", "uas", "c-uas", "counter-uas", "counter-drone", "insansız",
    "air defen", "hava savunma", "shorad", "manpads", "missile", "füze", "roket", "rocket",
    "artillery", "topçu", "howitzer", "obüs", "mortar", "havan",
    "ammunition", "mühimmat", "munition", "fuze", "fünye", "propellant", "barut",
    "defence", "defense", "savunma", "military", "askeri", "askerî", "army", "ordu",
    "navy", "donanma", "tender", "ihale", "procurement", "tedarik", "contract", "sözleşme",
    "nato", "radar", "jammer", "karıştırıcı", "shotgun", "gun system", "silah",
]

# Category -> terms. First match wins; anything else lands in "Diğer".
CATEGORIES = [
    ("C-UAS ve Hava Savunma", [
        "c-uas", "counter-uas", "counter-drone", "anti-drone", "drone defen", "dron savunma",
        "air defen", "hava savunma", "shorad", "manpads", "skyranger", "jammer", "karıştırıc",
        "interceptor", "önleyici", "uav", "uas", "drone", "dron", "loitering", "dolanan",
    ]),
    ("Topçu ve Mühimmat", [
        "artillery", "topçu", "howitzer", "obüs", "mortar", "havan", "ammunition", "mühimmat",
        "munition", "shell", "155mm", "155 mm", "105mm", "propellant", "barut", "fuze",
        "fünye", "airburst", "proximity", "nitrocellulose", "nitroselüloz",
    ]),
    ("Deniz ve İnsansız Sistemler", [
        "naval", "deniz", "frigate", "fırkateyn", "submarine", "denizalt", "usv", "uuv",
        "mine", "mayın", "torpedo",
    ]),
    ("Hafif Silah ve Mayın", [
        "rifle", "tüfek", "small arms", "hafif silah", "machine gun", "makineli",
        "demining", "geçit açma", "ied",
    ]),
    ("Politika ve Regülasyon", [
        "export control", "ihracat kontrol", "itar", "caatsa", "sanction", "yaptırım",
        "edf", "asap", "safe", "nspa", "regulation", "regülasyon", "policy", "politika",
        "budget", "bütçe", "parliament", "meclis",
    ]),
    ("Tedarik Zinciri", [
        "supply chain", "tedarik zinciri", "tungsten", "rare earth", "nadir toprak",
        "steel", "çelik", "copper", "bakır", "semiconductor", "çip", "shortage", "darboğaz",
    ]),
    ("İhale ve Sözleşmeler", [
        "tender", "ihale", "contract", "sözleşme", "award", "order", "sipariş", "deal",
        "procure", "tedarik", "rfi", "rfp", "solicitation",
    ]),
]

MKE_TERMS = ["mke", "makine ve kimya", "tolga", "boran", "attila", "attİla", "mpt-76", "pirana", "barkın"]


def norm(text):
    text = unicodedata.normalize("NFKD", (text or "").lower())
    text = text.replace("ı", "i").replace("İ", "i").replace("ş", "s").replace("ğ", "g")
    return re.sub(r"[^a-z0-9 ]+", " ", text)


def drive_session():
    creds = service_account.Credentials.from_service_account_info(
        json.loads(os.environ["GDRIVE_SA_KEY"]),
        scopes=["https://www.googleapis.com/auth/drive.readonly"],
    )
    creds.refresh(Request())
    s = requests.Session()
    s.headers["Authorization"] = f"Bearer {creds.token}"
    return s


def load_sources():
    """kaynaklar.json lives in Drive so the customer can edit it without a deploy."""
    local = os.environ.get("SOURCES_FILE")
    if local:
        return json.loads(pathlib.Path(local).read_text(encoding="utf-8"))
    session = drive_session()
    folder = os.environ["DRIVE_FOLDER_ID"]
    r = session.get(DRIVE_API, params={
        "q": f"'{folder}' in parents and name = 'kaynaklar.json' and trashed = false",
        "fields": "files(id)",
    })
    r.raise_for_status()
    files = r.json().get("files", [])
    if not files:
        sys.exit("kaynaklar.json not found in the Drive folder")
    r = session.get(f"{DRIVE_API}/{files[0]['id']}", params={"alt": "media"})
    r.raise_for_status()
    return r.json()


def parse_date(value):
    if not value:
        return None
    value = value.strip()
    for fmt in ("%a, %d %b %Y %H:%M:%S %z", "%a, %d %b %Y %H:%M:%S %Z",
                "%Y-%m-%dT%H:%M:%S%z", "%Y-%m-%dT%H:%M:%SZ", "%Y-%m-%d %H:%M:%S",
                "%Y-%m-%d"):
        try:
            parsed = dt.datetime.strptime(value.replace("GMT", "+0000"), fmt)
            return parsed if parsed.tzinfo else parsed.replace(tzinfo=dt.timezone.utc)
        except ValueError:
            continue
    return None


def strip_tags(text):
    return html.unescape(re.sub(r"<[^>]+>", " ", text or "")).strip()


def read_feed(source):
    """Return (source, items, error). Handles both RSS and Atom."""
    try:
        res = requests.get(source["url"], headers={"User-Agent": UA}, timeout=TIMEOUT)
        res.raise_for_status()
        root = ET.fromstring(res.content)
    except Exception as exc:  # noqa: BLE001 - a dead feed must not stop the run
        return source, [], f"{type(exc).__name__}: {exc}"[:120]

    ns = {"atom": "http://www.w3.org/2005/Atom", "dc": "http://purl.org/dc/elements/1.1/"}
    items = []
    for node in root.iter():
        tag = node.tag.split("}")[-1]
        if tag not in ("item", "entry"):
            continue
        title = strip_tags(node.findtext("title") or node.findtext("atom:title", "", ns))
        link = node.findtext("link") or ""
        if not link:
            for child in node.findall("atom:link", ns):
                if child.get("rel") in (None, "alternate"):
                    link = child.get("href") or ""
                    break
        published = (node.findtext("pubDate") or node.findtext("published")
                     or node.findtext("atom:published", "", ns)
                     or node.findtext("updated") or node.findtext("dc:date", "", ns))
        if title and link:
            items.append({"title": title, "url": link.strip(), "published": parse_date(published)})
    return source, items, None


def categorise(title):
    text = norm(title)
    if any(term in text for term in (norm(t) for t in MKE_TERMS)):
        return "MKE"
    for name, terms in CATEGORIES:
        if any(norm(term) in text for term in terms):
            return name
    return "Diğer"


def looks_defence(title):
    text = norm(title)
    return any(norm(term) in text for term in DEFENCE_TERMS)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true", help="only report counts")
    ap.add_argument("--hours", type=int, default=48)
    args = ap.parse_args()

    sources = [s for s in load_sources()
               if s.get("tur") == "rss" and s.get("test", {}).get("sonuc") != "kapali"]
    cutoff = dt.datetime.now(dt.timezone.utc) - dt.timedelta(hours=args.hours)

    collected, failures = [], []
    with concurrent.futures.ThreadPoolExecutor(max_workers=12) as pool:
        for source, items, error in pool.map(read_feed, sources):
            if error:
                failures.append((source["ad"], error))
                continue
            general = "filtre" in (source.get("not") or "").lower()
            kept = 0
            for item in items:
                if item["published"] and item["published"] < cutoff:
                    continue
                if general and not looks_defence(item["title"]):
                    continue
                collected.append({
                    "title": item["title"],
                    "url": item["url"],
                    "source": source["ad"],
                    "country": source.get("ulke", ""),
                    "lang": source.get("dil", ""),
                    "tier": source.get("kademe", ""),
                    "published": item["published"].date().isoformat() if item["published"] else "",
                    "category": categorise(item["title"]),
                })
                kept += 1
            if not kept and not items:
                failures.append((source["ad"], "feed parsed but empty"))

    # dedupe: same link, or the same headline from several outlets
    seen_urls, seen_titles, unique = set(), {}, []
    for item in sorted(collected, key=lambda i: (i["published"], i["source"]), reverse=True):
        url_key = re.sub(r"[?#].*$", "", item["url"]).rstrip("/")
        title_key = " ".join(norm(item["title"]).split())[:70]
        if url_key in seen_urls:
            continue
        if title_key in seen_titles:
            seen_titles[title_key]["also"].append(item["source"])
            continue
        seen_urls.add(url_key)
        item["also"] = []
        seen_titles[title_key] = item
        unique.append(item)

    by_category = {}
    for item in unique:
        by_category.setdefault(item["category"], []).append(item)

    today = dt.datetime.now(dt.timezone.utc).date().isoformat()
    payload = {
        "date": today,
        "window_hours": args.hours,
        "scanned_sources": len(sources),
        "failed_sources": len(failures),
        "collected_items": len(collected),
        "unique_items": len(unique),
        "categories": {k: len(v) for k, v in sorted(by_category.items())},
        "items": unique,
        "failures": [{"source": n, "error": e} for n, e in failures],
    }

    print(f"kaynak: {len(sources)} · okunamayan: {len(failures)}")
    print(f"ham kalem: {len(collected)} · tekilleştirilmiş: {len(unique)}")
    for name, items in sorted(by_category.items(), key=lambda kv: -len(kv[1])):
        print(f"  {name}: {len(items)}")
    for name, error in failures:
        print(f"  ! {name}: {error}")

    if not args.dry_run:
        OUT_DIR.mkdir(parents=True, exist_ok=True)
        (OUT_DIR / f"{today}.json").write_text(
            json.dumps(payload, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
        print(f"  · data/news/{today}.json")


if __name__ == "__main__":
    main()
