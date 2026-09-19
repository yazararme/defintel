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

import feedparser
import requests
from google.auth.transport.requests import Request
from google.oauth2 import service_account

ROOT = pathlib.Path(__file__).resolve().parent.parent
OUT_DIR = ROOT / "data" / "news"
DRIVE_API = "https://www.googleapis.com/drive/v3/files"
# Several publishers reject unknown agents outright; present a normal browser
# string and keep the crawl polite instead (one request per feed, once a day).
UA = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/140.0 Safari/537.36")
TIMEOUT = 30

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

# Category -> terms, in priority order. Short terms are matched on word
# boundaries: "safe" as a plain word matched half the English-language feeds.
CATEGORIES = [
    ("C-UAS ve Hava Savunma", [
        "c-uas", "counter-uas", "counter drone", "counter-drone", "anti-drone", "drone defen",
        "dron savunma", "air defen", "hava savunma", "shorad", "manpads", "skyranger",
        "jammer", "karıştırıc", "interceptor", "önleyici", "uav", "uas", "drone", "dron",
        "loitering", "dolanan mühimmat", "patriot", "nasams", "iron dome", "s-400",
    ]),
    ("Topçu ve Mühimmat", [
        "artillery", "topçu", "howitzer", "obüs", "mortar", "havan", "ammunition", "mühimmat",
        "munition", "shell", "155mm", "155 mm", "105mm", "120mm", "30mm", "35mm", "propellant",
        "barut", "fuze", "fünye", "airburst", "proximity", "nitrocellulose", "nitroselüloz",
        "rocket artillery", "mlrs", "himars",
    ]),
    ("Deniz ve İnsansız Sistemler", [
        "naval", "frigate", "fırkateyn", "submarine", "denizalt", "corvette", "korvet",
        "usv", "uuv", "sea drone", "deniz araç", "torpedo", "mayın gemi",
    ]),
    ("Hafif Silah ve Mayın", [
        "rifle", "tüfek", "small arms", "hafif silah", "machine gun", "makineli",
        "demining", "mayın temizleme", "geçit açma", "sniper", "keskin nişancı",
    ]),
    ("Tedarik Zinciri", [
        "supply chain", "tedarik zinciri", "tungsten", "rare earth", "nadir toprak",
        "steel price", "çelik", "copper", "bakır", "semiconductor", "chip shortage",
        "shortage", "darboğaz", "raw material", "hammadde",
    ]),
    ("İhale ve Sözleşmeler", [
        "tender", "ihale", "contract", "sözleşme", "awarded", "awards", "order for",
        "sipariş", "procure", "tedarik", "rfi", "rfp", "solicitation", "framework agreement",
        "çerçeve anlaşma", "signs", "imzala", "deal",
    ]),
    ("Politika ve Regülasyon", [
        "export control", "ihracat kontrol", "itar", "caatsa", "sanction", "yaptırım",
        "regulation", "regülasyon", "defence policy", "savunma politika", "defense budget",
        "savunma bütçe", "parliament approve", "meclis", "nato summit", "eu defence",
    ]),
    ("Rakip Duyuruları", [
        "rheinmetall", "hanwha", "aselsan", "roketsan", "elbit", "knds", "nexter",
        "bae systems", "leonardo", "kongsberg", "saab", "nammo", "anduril", "epirus",
        "droneshield", "norinco", "raytheon", "lockheed", "northrop", "mbda", "diehl",
        "junghans", "thales", "rtx",
    ]),
]

MKE_TERMS = ["mke", "makine ve kimya", "tolga", "boran", "attila", "mpt-76", "pirana", "barkın"]
GENERAL = "Genel Savunma Gündemi"

def title_key(title):
    """Dedupe key that survives non-Latin scripts.

    norm() strips anything outside a-z0-9 for keyword matching; using it here
    collapsed every Korean, Russian and Japanese headline to the empty string,
    so one item swallowed all the others as duplicates.
    """
    key = " ".join(re.sub(r"[^\w\s]+", " ", (title or "").casefold(), flags=re.U).split())
    return key[:70] if len(key) >= 12 else ""


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
    """Return (source, items, error). feedparser copes with the broken feeds."""
    error = None
    for attempt in (1, 2):
        try:
            res = requests.get(source["url"], headers={"User-Agent": UA, "Accept": "*/*"},
                               timeout=TIMEOUT)
            res.raise_for_status()
            break
        except Exception as exc:  # noqa: BLE001 - a dead feed must not stop the run
            error = f"{type(exc).__name__}: {exc}"[:110]
            if attempt == 2:
                return source, [], error

    parsed = feedparser.parse(res.content)
    items = []
    for entry in parsed.entries:
        title = strip_tags(entry.get("title"))
        link = (entry.get("link") or "").strip()
        stamp = entry.get("published_parsed") or entry.get("updated_parsed")
        published = (dt.datetime(*stamp[:6], tzinfo=dt.timezone.utc) if stamp
                     else parse_date(entry.get("published") or entry.get("updated")))
        if title and link:
            items.append({"title": title, "url": link, "published": published})
    return source, items, None


SOURCE_HINTS = [
    ("C-UAS ve Hava Savunma", ["c-uas", "dron savunma", "insansız"]),
    ("Topçu ve Mühimmat", ["mühimmat", "topçu"]),
    ("Deniz ve İnsansız Sistemler", ["deniz sistem"]),
    ("Rakip Duyuruları", ["rakip kurumsal", "üretici duyuru"]),
]


def has_term(text, term):
    term = norm(term).strip()
    if len(term) <= 5 and " " not in term:
        return re.search(rf"\b{re.escape(term)}\b", text) is not None
    return term in text


def categorise(title, source=None):
    text = norm(title)
    if any(has_term(text, t) for t in MKE_TERMS):
        return "MKE"
    for name, terms in CATEGORIES:
        if any(has_term(text, t) for t in terms):
            return name
    scope = norm((source or {}).get("kapsam", ""))
    for name, terms in SOURCE_HINTS:
        if any(norm(term) in scope for term in terms):
            return name
    return GENERAL


def looks_defence(title):
    text = norm(title)
    return any(has_term(text, term) for term in DEFENCE_TERMS)


# The agent reads this file, so keep it small enough to be read whole and put
# the categories it acts on first.
CANDIDATE_ORDER = [
    "MKE", "C-UAS ve Hava Savunma", "Topçu ve Mühimmat", "Rakip Duyuruları",
    "İhale ve Sözleşmeler", "Deniz ve İnsansız Sistemler", "Hafif Silah ve Mayın",
    "Tedarik Zinciri", "Politika ve Regülasyon", "Genel Savunma Gündemi",
]
CANDIDATE_LIMIT = 260


def write_candidates(day, payload, by_category):
    lines = [
        f"# Aday başlıklar · {day}",
        "",
        # "66 kaynak tarandı" tanımlı kaynak sayısıydı, okunan değil — sitede
        # düzeltilen aynı hata burada da duruyordu.
        f"{payload['scanned_sources'] - payload['failed_sources']} kaynak okundu"
        + (f" ({payload['failed_sources']} kaynak yanıt vermedi)" if payload['failed_sources'] else "")
        + f", son {payload['window_hours']} saat, "
        f"{payload['unique_items']} tekil başlık. Bu dosya en fazla {CANDIDATE_LIMIT} kalem taşır; "
        f"tam liste: https://defintel.shadovi.com/haberler/{day}.html",
        "",
    ]
    used = 0
    for name in CANDIDATE_ORDER + sorted(set(by_category) - set(CANDIDATE_ORDER)):
        items = by_category.get(name) or []
        if not items or used >= CANDIDATE_LIMIT:
            continue
        room = CANDIDATE_LIMIT - used
        lines.append(f"## {name} ({len(items)})")
        for item in items[:room]:
            extra = f" +{len(item['also'])} yayın" if item.get("also") else ""
            lines.append(
                f"- {item['title']} — {item['source']}, {item['published'] or '?'}"
                f"{extra} — {item['url']}"
            )
        if len(items) > room:
            lines.append(f"- … bu kategoride {len(items) - room} kalem daha var, tam listede.")
        lines.append("")
        used += min(len(items), room)
    (OUT_DIR / f"{day}-aday.md").write_text("\n".join(lines), encoding="utf-8")
    print(f"  · data/news/{day}-aday.md ({used} kalem)")


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
                    "category": categorise(item["title"], source),
                })
                kept += 1
            if not kept and not items:
                failures.append((source["ad"], "feed parsed but empty"))

    # dedupe: same link, or the same headline from several outlets
    seen_urls, seen_titles, unique = set(), {}, []
    for item in sorted(collected, key=lambda i: (i["published"], i["source"]), reverse=True):
        url_key = re.sub(r"[?#].*$", "", item["url"]).rstrip("/")
        key = title_key(item["title"])
        if url_key in seen_urls:
            continue
        if key and key in seen_titles:
            seen_titles[key]["also"].append(item["source"])
            continue
        seen_urls.add(url_key)
        item["also"] = []
        if key:
            seen_titles[key] = item
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
        write_candidates(today, payload, by_category)

        OUT_DIR.mkdir(parents=True, exist_ok=True)
        (OUT_DIR / f"{today}.json").write_text(
            json.dumps(payload, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
        print(f"  · data/news/{today}.json")


if __name__ == "__main__":
    main()
