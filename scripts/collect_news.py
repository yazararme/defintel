"""Collect the day's candidate headlines from the source inventory.

Why this runs here and not inside the agent: pulling ~70 feeds is mechanical
work. Done in Python it is complete (every item, exact date, exact link),
repeatable and fast; done with an agent's fetch tool it comes back summarised
and truncated. The agent gets the finished candidate list and spends its budget
on judgement instead.

Reads   : kaynaklar.json from the Drive folder (the customer edits it there)
Writes  : data/news/YYYY-MM-DD.json   — candidates, deduped, categorised
Usage   : python3 scripts/collect_news.py [--dry-run] [--hours 48]

Rev 31 — the same day collected twice (05:19 Apps Script trigger, then GitHub's late
`40 2` cron as backup) used to overwrite the day's files. Now every item carries
`ilk_goruldu` (first-seen stamp, Europe/Istanbul ISO). A re-collection merges into the
existing day file: existing items are kept byte-for-byte (stamp included, never deleted),
new items are appended with this run's stamp. The candidate list opens with
"## Dünkü brifingden sonra gelenler (N)" — yesterday's items first seen after yesterday's
briefing went out (data/published.json). Build rule GEÇ-GELEN (Rev 30 channel): a stamp
changed on re-collection, or a late item missing from that first section.

Rev 25 — SİLME-YOK: the defence filter on sources whose `not` says "filtre" marks
(`savunma_terimi: false`, category Genel), it never drops; per source "read == written" goes to
(A) as a table, and a mismatch sends SİLME-YOK (Rev 30, blocking) and exits 1. İPUCU-YOK: the
category comes only from a word in the title (S2 source hints removed; S3, S4, S6; see
CATEGORIES / PLAYER_CATEGORY). `--sinama-silme-boz` (fixture only) drops one read item to prove
SİLME-YOK fires. See scripts/test_silme_yok.py; scripts/yeniden_kategorile.py re-applies the
rules to a stored day offline.

Offline test path (no network, no Drive, no model):
    python3 scripts/collect_news.py --fixture F.json --out DIR --date D --now ISO
F.json = {"sources": [kaynaklar entries], "feeds": {"<ad>": {"items": [{title, url,
published}]} | {"error": "…"}}}. `--sinama-damga-boz` (fixture only) deliberately changes
one existing stamp to prove GEÇ-GELEN fires. See scripts/test_collect.py.
A fixture feed may instead carry the raw response, {"body": "…"}: it then goes through the
same parse_body() as a live fetch (K6, scripts/test_k6.py).

K6 — two optional per-source fields in kaynaklar.json (absent = behaviour unchanged):
  "istek_basligi": {"Header": "value"}   extra request headers for this source only.
      Northrop's investor RSS (Akamai) answers 403 to a Chrome User-Agent that sends no
      Accept-Language — a bot fingerprint — and 200 with it.
  "tur": "html" + "ayristirici": "<name>"  a press-release page with no working feed; a narrow
      parser from HTML_PARSERS reads title + date + URL (stdlib only). Elbit Systems' /feed/
      301s to the HTML page www.elbitsystems.com/news (CI diagnosis, 24 Sep 2026) →
      "elbitsystems-news"; Elbit Systems UK's recent-news page → "elbitsystems-uk".
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
import urllib.parse
import xml.etree.ElementTree as ET

# feedparser / requests / google-auth are imported where they are used: the offline
# fixture path (Rev 31 test workflow) runs on a bare python with no pip install.

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
# Rev 25 (İPUCU-YOK): a category comes only from a word in the title — there is no
# source hint any more (S2). An item whose title hits no word stays in Genel: right in
# Genel beats wrong in a named category, because the reader opens a named category on
# its topic promise.
CATEGORIES = [
    # S3: only counter/air-defence phrases. Bare drone words (drone, dron, uav, uas) and
    # loitering munitions are unmanned systems, not their defeat → İnsansız Sistemler.
    ("C-UAS ve Hava Savunma", [
        "c-uas", "counter-uas", "counter drone", "counter-drone", "anti-drone", "drone defen",
        "karşı-dron", "dron savunma", "air defen", "hava savunma", "shorad", "manpads",
        "skyranger", "jammer", "karıştırıc", "interceptor", "önleyici", "patriot", "nasams",
        "iron dome", "s-400",
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
        "drone", "dron", "uav", "uas", "loitering", "dolanan mühimmat",
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
    # S6: only procurement-event phrases. "deal", "signs", "imzala", "contract" pulled
    # diplomatic headlines in ("Trump signs Greenland security agreement").
    ("İhale ve Sözleşmeler", [
        "tender", "ihale", "solicitation", "rfp", "rfi", "awarded", "sözleşme verdi",
        "sipariş verdi", "çerçeve anlaşma", "framework agreement",
    ]),
    ("Politika ve Regülasyon", [
        "export control", "ihracat kontrol", "itar", "caatsa", "sanction", "yaptırım",
        "regulation", "regülasyon", "defence policy", "savunma politika", "defense budget",
        "savunma bütçe", "parliament approve", "meclis", "nato summit", "eu defence",
    ]),
]

# S4 (Rev 25): "Oyuncu Duyuruları" (data key unchanged, Rev 2 precedent) — the title's
# subject is one of the 64 tracked players (data/rakipler.json, Rev 21 alias matcher) and
# the headline is that player's own action. Checked after MKE, before the product segments:
# a player's announcement belongs here, not under its product. The old 24-brand word list
# is gone — a brand merely mentioned is not its announcement.
PLAYER_CATEGORY = "Rakip Duyuruları"
# Subject = the name opens the title: at most a bullet/quote, a headline kicker ending in
# ":" ("Heavy Weapon Carrier for the Infantry: Rheinmetall completes …"), one possessive
# ("Poland's PGZ") or one co-subject ("Lockheed, Kongsberg test …") before it.
SUBJECT_PREFIX = re.compile(
    r"^[\W_]*"                                        # ► • " ‘ ( …
    r"(?:[^:]{1,80}:\s*)?"                            # kicker:
    r"(?:[\w.\-]+['’]s\s+"                            # possessive
    r"|(?:[\w.\-&]+\s+){0,2}[\w.\-&]+(?:\s*,|\s+(?:and|&|ve|ile|und|et|e))\s+)?$",
    re.U)
# The player's own act: won, unveiled, delivered, invested, partnered … (EN / TR / DE),
# matched on norm() text (ascii-folded, lower case).
PLAYER_ACTION = re.compile(r"\b(?:" + "|".join([
    r"wins?", r"won", r"secur(?:es|ed)", r"lands", r"bags", r"books",
    r"unveil\w*", r"launch\w*", r"introduc\w*", r"debut\w*", r"showcas\w*", r"present\w*",
    r"deliver\w*", r"hands? over", r"invest\w*", r"expand\w*", r"opens?", r"opened",
    r"breaks? ground", r"acquir\w*", r"buys?", r"bought", r"partner\w*", r"teams? up",
    r"teams? with", r"joins? forces", r"joint venture", r"signs?", r"signed", r"awarded",
    r"receiv\w*", r"complet\w*", r"tests?", r"tested", r"test fires?", r"demonstrat\w*",
    r"announc\w*", r"builds?", r"establish\w*", r"starts?", r"begins?", r"ramps? up",
    r"to (?:build|supply|deliver|produce|develop|open|invest|acquire)", r"supplies",
    r"kazand\w*", r"tanitt\w*", r"teslim\w*", r"yatirim\w*", r"ortaklik\w*", r"imzala\w*",
    r"acti", r"acildi", r"satin al\w*", r"sergile\w*", r"baslatt\w*", r"uretime\w*", r"kurdu\w*",
    r"genislet\w*", r"test etti\w*",
    r"inaugurat\w*",
    r"gewinnt", r"liefert", r"investiert", r"erhalt", r"ubernimmt", r"prasentiert", r"baut",
    r"testet", r"unterzeichnet", r"startet", r"eroffnet", r"stellt\w* vor",
]) + r")\b")

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
    import requests
    from google.auth.transport.requests import Request
    from google.oauth2 import service_account
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


def request_headers(source):
    """K6: the collector's standard headers plus the source's own `istek_basligi`."""
    headers = {"User-Agent": UA, "Accept": "*/*"}
    headers.update({str(k): str(v) for k, v in (source.get("istek_basligi") or {}).items()})
    return headers


def parse_elbitsystems_uk(text, base_url):
    """elbitsystems-uk.com/media-events/recent-news: one <li class="media"> per release —
    <h3>16 September 2026</h3> then <p><a href="/media-events/recent-news/…">Title</a></p>."""
    items = []
    for block in re.findall(r'<li class="media[^"]*">(.*?)</li>', text, re.S):
        day = re.search(r"<h3>\s*(\d{1,2} [A-Za-z]+ \d{4})\s*</h3>", block)
        link = re.search(r'<p>\s*<a href="([^"]+)"[^>]*>(.*?)</a>', block, re.S)
        if not (day and link):
            continue
        try:
            published = dt.datetime.strptime(day.group(1), "%d %B %Y").replace(tzinfo=dt.timezone.utc)
        except ValueError:
            published = None
        title = " ".join(strip_tags(link.group(2)).split())
        url = urllib.parse.urljoin(base_url, html.unescape(link.group(1)).strip())
        if title and url:
            items.append({"title": title, "url": url, "published": published})
    return items


def parse_elbitsystems_news(text, base_url):
    """www.elbitsystems.com/news (Drupal view; elbitsystems.com/feed/ 301s here since the feed was
    removed): one `new-first-item views-row` / `new-box views-row` block per release — first link
    href, <time datetime="2026-09-18T12:00:00Z">, title in <h2 class="title"> or
    <div class="title"><span>. Page 1 only (10 releases)."""
    items = []
    for block in re.split(r'<div class="new-(?:first-item|box) views-row', text)[1:]:
        link = re.search(r'<a href="([^"]+)"', block)
        stamp = re.search(r'<time datetime="(\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2})Z"', block)
        title = re.search(r'<h2 class="title">(.*?)</h2>|<div class="title">\s*<span>(.*?)</span>', block, re.S)
        if not (link and stamp and title):
            continue
        published = dt.datetime.strptime(stamp.group(1), "%Y-%m-%dT%H:%M:%S").replace(tzinfo=dt.timezone.utc)
        name = " ".join(strip_tags(title.group(1) or title.group(2)).split())
        url = urllib.parse.urljoin(base_url, html.unescape(link.group(1)).strip())
        if name and url:
            items.append({"title": name, "url": url, "published": published})
    return items


# K6: `tur: "html"` sources name their parser with `ayristirici`. Each parser is narrow on
# purpose — one page's markup; a redesign gives "feed parsed but empty", as a dead feed does.
HTML_PARSERS = {"elbitsystems-uk": parse_elbitsystems_uk, "elbitsystems-news": parse_elbitsystems_news}


def parse_body(source, content):
    """Response body → [{title, url, published}] by the source's `tur`. Raises on an unknown
    parser. RSS/Atom needs feedparser (imported here: the html path stays stdlib-only)."""
    if source.get("tur") == "html":
        parser = HTML_PARSERS.get(source.get("ayristirici") or "")
        if parser is None:
            raise ValueError(f"bilinmeyen ayristirici: {source.get('ayristirici')!r}")
        text = content.decode("utf-8", "replace") if isinstance(content, bytes) else content
        return parser(text, source.get("url") or "")
    import feedparser
    parsed = feedparser.parse(content)
    items = []
    for entry in parsed.entries:
        title = strip_tags(entry.get("title"))
        link = (entry.get("link") or "").strip()
        stamp = entry.get("published_parsed") or entry.get("updated_parsed")
        published = (dt.datetime(*stamp[:6], tzinfo=dt.timezone.utc) if stamp
                     else parse_date(entry.get("published") or entry.get("updated")))
        if title and link:
            items.append({"title": title, "url": link, "published": published})
    return items


def read_feed(source):
    """Return (source, items, error). feedparser copes with the broken feeds."""
    import requests
    error = None
    for attempt in (1, 2):
        try:
            res = requests.get(source["url"], headers=request_headers(source), timeout=TIMEOUT)
            res.raise_for_status()
            break
        except Exception as exc:  # noqa: BLE001 - a dead feed must not stop the run
            error = f"{type(exc).__name__}: {exc}"[:110]
            if attempt == 2:
                return source, [], error
    try:
        return source, parse_body(source, res.content), None
    except Exception as exc:  # noqa: BLE001
        return source, [], f"{type(exc).__name__}: {exc}"[:110]


def has_term(text, term):
    term = norm(term).strip()
    if len(term) <= 5 and " " not in term:
        return re.search(rf"\b{re.escape(term)}\b", text) is not None
    return term in text


def _players():
    """Rev 21 matcher (oyuncu_eslestir.py at the repo root; stdlib only)."""
    if str(ROOT) not in sys.path:
        sys.path.insert(0, str(ROOT))
    import oyuncu_eslestir
    return oyuncu_eslestir


def player_announcement(title, lang=""):
    """S4: id of the tracked player whose own action this headline is, else None."""
    if not PLAYER_ACTION.search(norm(title)):
        return None
    m = _players()
    for rival in m.rivals_config():
        before = m.rival_start(rival["id"], title, tr=lang == "tr")
        if before is not None and SUBJECT_PREFIX.match(before):
            return rival["id"]
    return None


def rule_hits(title, lang=""):
    """Every category whose own rule the title satisfies, in priority order.

    categorise() takes the first; S8 uses the whole list to count items that arrived
    without a word of their own (hint-only) and items that touch no word at all.
    """
    text = norm(title)
    hits = []
    if any(has_term(text, t) for t in MKE_TERMS):
        hits.append("MKE")
    if player_announcement(title, lang):
        hits.append(PLAYER_CATEGORY)
    hits += [name for name, terms in CATEGORIES if any(has_term(text, t) for t in terms)]
    return hits


def categorise(title, lang=""):
    """İPUCU-YOK: the category comes only from a word in the title (no source hint)."""
    hits = rule_hits(title, lang)
    return hits[0] if hits else GENERAL


def s8_counts(items):
    """S8: per stored category → {"n", "ipucu", "kelimesiz"}.

    ipucu     : in a named category although the title does not hit that category's own
                rule — it could only have come from a source hint (İPUCU-YOK wants 0).
    kelimesiz : the title hits no word of any category (MKE, S4 and all term lists).
    Genel has no rule of its own, so its ipucu is None.
    """
    out = {}
    for item in items:
        cat = item.get("category") or GENERAL
        hits = rule_hits(item.get("title") or "", item.get("lang") or "")
        row = out.setdefault(cat, {"n": 0, "ipucu": None if cat == GENERAL else 0, "kelimesiz": 0})
        row["n"] += 1
        if cat != GENERAL and cat not in hits:
            row["ipucu"] += 1
        if not hits:
            row["kelimesiz"] += 1
    return out


def looks_defence(title):
    text = norm(title)
    return any(has_term(text, term) for term in DEFENCE_TERMS)


# The agent reads this file, so keep it small enough to be read whole and put
# the categories it acts on first. Rev 31: yesterday's late arrivals come before
# everything, so the 260 limit can never cut them.
LATE_SECTION = "Dünkü brifingden sonra gelenler"
CANDIDATE_ORDER = [
    LATE_SECTION,
    "MKE", "C-UAS ve Hava Savunma", "Topçu ve Mühimmat", "Rakip Duyuruları",
    "İhale ve Sözleşmeler", "Deniz ve İnsansız Sistemler", "Hafif Silah ve Mayın",
    "Tedarik Zinciri", "Politika ve Regülasyon", "Genel Savunma Gündemi",
]
CANDIDATE_LIMIT = 260
PUBLISHED = ROOT / "data" / "published.json"


def _tz_tr():
    try:
        from zoneinfo import ZoneInfo
        return ZoneInfo("Europe/Istanbul")
    except Exception:   # tzdata yoksa: Türkiye 2016'dan beri sabit UTC+3
        return dt.timezone(dt.timedelta(hours=3))


TR = _tz_tr()


def url_key(url):
    return re.sub(r"[?#].*$", "", url or "").rstrip("/")


def parse_stamp(value):
    """ISO zaman damgası → saat dilimli datetime; okunamazsa None (bilinmeyen ≠ geç)."""
    try:
        stamp = dt.datetime.fromisoformat(str(value))
    except (TypeError, ValueError):
        return None
    return stamp if stamp.tzinfo else stamp.replace(tzinfo=TR)


def brief_time(day, published_path=PUBLISHED):
    """O günün brifinginin ilk yayın anı (data/published.json, TR saati) ya da None."""
    try:
        hhmm = json.loads(pathlib.Path(published_path).read_text(encoding="utf-8")).get(day)
        h, m = (int(x) for x in re.fullmatch(r"(\d{1,2}):(\d{2})", hhmm or "").groups())
        return dt.datetime.fromisoformat(day).replace(hour=h, minute=m, tzinfo=TR)
    except Exception:
        return None


def after_briefing(item, brief_at):
    """Kalem, brifing yayımlandıktan sonra mı ilk görüldü? Damgasız kalem: hayır."""
    seen = parse_stamp(item.get("ilk_goruldu"))
    return bool(brief_at and seen and seen > brief_at)


def late_from_yesterday(day, out_dir=OUT_DIR, published_path=PUBLISHED):
    """(dün, dünkü brifing anı, dünün brifingden sonra ilk görülen kalemleri)."""
    prev = (dt.date.fromisoformat(day) - dt.timedelta(days=1)).isoformat()
    brief_at = brief_time(prev, published_path)
    path = next((d / f"{prev}.json" for d in (pathlib.Path(out_dir), OUT_DIR)
                 if (d / f"{prev}.json").exists()), None)
    if not path or not brief_at:
        return prev, brief_at, []
    items = json.loads(path.read_text(encoding="utf-8")).get("items") or []
    return prev, brief_at, [i for i in items if after_briefing(i, brief_at)]


def candidate_line(item, seen=False):
    extra = f" +{len(item['also'])} yayın" if item.get("also") else ""
    stamp = parse_stamp(item.get("ilk_goruldu")) if seen else None
    when = f", ilk görüldü {stamp.astimezone(TR):%d.%m %H:%M}" if stamp else ""
    return (f"- {item['title']} — {item['source']}, {item.get('published') or '?'}"
            f"{extra}{when} — {item['url']}")


def write_candidates(day, payload, by_category, late=(), prev=None, brief_at=None,
                     out_dir=OUT_DIR):
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
    sections = [(LATE_SECTION, list(late))] + [
        (name, by_category.get(name) or [])
        for name in CANDIDATE_ORDER[1:] + sorted(set(by_category) - set(CANDIDATE_ORDER))]
    used = 0
    for name, items in sections:
        if not items or used >= CANDIDATE_LIMIT:
            continue
        room = CANDIDATE_LIMIT - used
        # Rev 25: ajan da okuyucunun gördüğü adı görsün (veri anahtarı değişmez).
        label = "Oyuncu Duyuruları" if name == PLAYER_CATEGORY else name
        lines.append(f"## {label} ({len(items)})")
        if name == LATE_SECTION:
            lines.append(f"{prev} brifingi {brief_at:%H:%M}'de yayımlandı; bu kalemler ondan sonra "
                         "ilk görüldü, brifing onları görmedi. Kendi kategorilerinde de yer alabilirler.")
        for item in items[:room]:
            lines.append(candidate_line(item, seen=name == LATE_SECTION))
        if len(items) > room:
            lines.append(f"- … bu kategoride {len(items) - room} kalem daha var, tam listede.")
        lines.append("")
        used += min(len(items), room)
    path = pathlib.Path(out_dir) / f"{day}-aday.md"
    path.write_text("\n".join(lines), encoding="utf-8")
    print(f"  · {path.relative_to(ROOT) if path.is_relative_to(ROOT) else path} ({used} kalem)")
    return path


def first_section_urls(text):
    """Aday dosyasının ilk bölümü geç-gelenler bölümüyse içindeki bağlantılar."""
    m = re.search(r"^## (.+?) \(\d+\)$", text, re.M)
    if not m or m.group(1) != LATE_SECTION:
        return set()
    body = text[m.end():]
    nxt = re.search(r"^## ", body, re.M)
    body = body[:nxt.start()] if nxt else body
    return {url_key(u) for u in re.findall(r"^- .* — (\S+)$", body, re.M)}


def merge_day(existing, fresh, stamp):
    """Var olan kalemler olduğu gibi kalır (damga dahil, hiçbiri silinmez); yalnızca
    yeni kalemler bu çalıştırmanın damgasıyla eklenir. Döner: (kalemler, yeni, yeniden görülen)."""
    items = list(existing)
    by_url = {url_key(i.get("url")): i for i in items}
    by_title = {k: i for i in items if (k := title_key(i.get("title")))}
    added = again = 0
    for item in fresh:
        key = title_key(item["title"])
        if url_key(item["url"]) in by_url or (key and key in by_title):
            again += 1
            continue
        item["ilk_goruldu"] = stamp
        items.append(item)
        by_url[url_key(item["url"])] = item
        if key:
            by_title[key] = item
        added += 1
    # aynı sıralama ölçütü; kararlı sıralama var olanların göreli sırasını korur
    items.sort(key=lambda i: (i.get("published") or "", i.get("source") or ""), reverse=True)
    return items, added, again


def stamp_audit(before, after):
    """Diskteki kalemler ile yazılmak üzere olanlar: (değişmedi, damgası değişen, kaybolan)."""
    now = {url_key(i.get("url")): i for i in after}
    same, changed, missing = 0, [], []
    for old in before:
        new = now.get(url_key(old.get("url")))
        if new is None:
            missing.append(old)
        elif new.get("ilk_goruldu") != old.get("ilk_goruldu"):
            changed.append((old, new))
        else:
            same += 1
    return same, changed, missing


def write_summary(lines):
    path = os.environ.get("GITHUB_STEP_SUMMARY")
    if not path:
        return
    try:
        with open(path, "a", encoding="utf-8") as fh:
            fh.write("\n".join(lines) + "\n\n")
    except OSError as exc:
        print(f"  ! özet yazılamadı: {exc}")


def silme_yok(okunan, items, filtreli):
    """SİLME-YOK (Rev 25): kaynak başına okunan == yazılan.

    okunan : zaman penceresine giren, akıştan okunan kalemler ({kaynak: [kalem]})
    items  : günün dosyasına yazılacak kalemler (birleştirme dahil)
    Okunan bir kalem yazılmış sayılır: bağlantısı dosyada ya da aynı başlık başka bir
    yayından geldiği için `also` altında (tekilleştirme) ya da günün önceki toplamasında
    zaten yazılmış. Döner: [(kaynak, filtre notlu mu, okunan, yazılan, savunma dışı,
    ilk eksik başlık | None)] — filtre notlular önce, sonra ada göre.
    """
    urls = {url_key(i.get("url")) for i in items}
    titles = {k for i in items if (k := title_key(i.get("title")))}
    disi = {}
    for i in items:
        if i.get("savunma_terimi") is False:
            disi[i.get("source")] = disi.get(i.get("source"), 0) + 1
    rows = []
    for ad, window in okunan.items():
        lost = [r for r in window if url_key(r["url"]) not in urls
                and not ((k := title_key(r["title"])) and k in titles)]
        rows.append((ad, ad in filtreli, len(window), len(window) - len(lost),
                     disi.get(ad, 0), lost[0]["title"] if lost else None))
    rows.sort(key=lambda r: (not r[1], r[0].casefold()))
    return rows


def silme_yok_ozet(rows, today, onek=""):
    """(A) tablosu + bozuksa Rev 30 uyarısı (bloklayıcı). Döner: bozuk kaynak sayısı."""
    bozuk = [r for r in rows if r[2] != r[3]]
    fl = [r for r in rows if r[1]]
    renk = "🔴" if bozuk else "🟢"
    lines = [f"### SİLME-YOK · {today} (Rev 25, bloklayıcı)", "",
             f"**{renk} okunan == yazılan: {len(rows) - len(bozuk)}/{len(rows)} kaynak eşit** · "
             f"filtre notlu {len(fl)} kaynak: okunan {sum(r[2] for r in fl)} · yazılan "
             f"{sum(r[3] for r in fl)} · savunma dışı işaretli {sum(r[4] for r in fl)}", "",
             "| Kaynak | Filtre notu | Okunan | Yazılan | Savunma dışı (`savunma_terimi: false`) | Durum |",
             "|---|---|--:|--:|--:|---|"]
    for ad, filtre, oku, yaz, disi, _ in rows:
        lines.append(f"| {ad} | {'filtre' if filtre else '—'} | {oku} | {yaz} | "
                     f"{disi if filtre else '—'} | {'🟢 eşit' if oku == yaz else '🔴 EŞİT DEĞİL'} |")
    write_summary(lines)
    for ad, filtre, oku, yaz, _, ilk in rows:
        print(f"  · SİLME-YOK {ad}{' (filtre)' if filtre else ''}: okunan {oku} · yazılan {yaz}")
    if bozuk:
        import uyari
        ad, _, oku, yaz, _, ilk = bozuk[0]
        uyari.ekle("SİLME-YOK", f"{onek}{today} · {len(bozuk)} kaynakta okunan ≠ yazılan — ör. {ad}: "
                   f"okunan {oku}, yazılan {yaz}, düşen “{(ilk or '')[:70]}”")
    return len(bozuk)


def fixture_reader(feeds):
    """Ağsız sınama: kayıtlı başlıklar read_feed ile aynı biçimde döner."""
    def read(source):
        feed = feeds.get(source["ad"]) or {"items": []}
        if feed.get("error"):
            return source, [], feed["error"]
        if "body" in feed:   # K6: kayıtlı ham yanıt, canlı toplamayla aynı ayrıştırıcıdan
            try:
                return source, parse_body(source, feed["body"]), None
            except Exception as exc:  # noqa: BLE001
                return source, [], f"{type(exc).__name__}: {exc}"[:110]
        return source, [{"title": i["title"], "url": i["url"],
                         "published": parse_date(i.get("published"))}
                        for i in feed.get("items") or []], None
    return read


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true", help="only report counts")
    ap.add_argument("--hours", type=int, default=48)
    # Rev 31 ağsız sınama yolu — gerçek toplamada hiçbiri verilmez.
    ap.add_argument("--fixture", help="kayıtlı başlıklar (JSON); ağa, Drive'a çıkılmaz")
    ap.add_argument("--out", help="çıktı dizini (--fixture ile zorunlu; data/news'e yazmaz)")
    ap.add_argument("--date", help="günü sabitle (YYYY-MM-DD)")
    ap.add_argument("--now", help="çalıştırma anını sabitle (ISO, ör. 2026-09-24T05:19:00+03:00)")
    ap.add_argument("--published", default=str(PUBLISHED), help="brifing yayın saatleri")
    ap.add_argument("--sinama-damga-boz", action="store_true",
                    help="(yalnız --fixture) var olan bir kalemin damgasını bilerek değiştir")
    ap.add_argument("--sinama-silme-boz", action="store_true",
                    help="(yalnız --fixture) okunan bir kalemi bilerek düşür → SİLME-YOK")
    args = ap.parse_args()
    if args.fixture and not args.out:
        sys.exit("--fixture ile --out zorunlu: sınama data/news'e yazmaz")
    if args.sinama_damga_boz and not args.fixture:
        sys.exit("--sinama-damga-boz yalnız --fixture ile")
    if args.sinama_silme_boz and not args.fixture:
        sys.exit("--sinama-silme-boz yalnız --fixture ile")
    onek = "SINAMA (fixture) — gerçek uyarı değil: " if args.fixture else ""

    out_dir = pathlib.Path(args.out) if args.out else OUT_DIR
    now = parse_stamp(args.now) if args.now else dt.datetime.now(dt.timezone.utc)
    if now is None:
        sys.exit(f"--now okunamadı: {args.now}")
    stamp = now.astimezone(TR).isoformat(timespec="seconds")
    today = args.date or now.astimezone(dt.timezone.utc).date().isoformat()

    if args.fixture:
        fixture = json.loads(pathlib.Path(args.fixture).read_text(encoding="utf-8"))
        all_sources, reader = fixture["sources"], fixture_reader(fixture.get("feeds") or {})
    else:
        all_sources, reader = load_sources(), read_feed
    sources = [s for s in all_sources
               if s.get("tur") in ("rss", "html") and s.get("test", {}).get("sonuc") != "kapali"]
    cutoff = now - dt.timedelta(hours=args.hours)

    collected, failures = [], []
    okunan = {}   # SİLME-YOK: kaynak → zaman penceresine giren okunan kalemler
    filtreli = set()
    with concurrent.futures.ThreadPoolExecutor(max_workers=12) as pool:
        for source, items, error in pool.map(reader, sources):
            if error:
                failures.append((source["ad"], error))
                continue
            general = "filtre" in (source.get("not") or "").lower()
            if general:
                filtreli.add(source["ad"])
            window = okunan.setdefault(source["ad"], [])
            for item in items:
                if item["published"] and item["published"] < cutoff:
                    continue
                window.append(item)
                entry = {
                    "title": item["title"],
                    "url": item["url"],
                    "source": source["ad"],
                    "country": source.get("ulke", ""),
                    "lang": source.get("dil", ""),
                    "tier": source.get("kademe", ""),
                    "published": item["published"].date().isoformat() if item["published"] else "",
                    "category": categorise(item["title"], source.get("dil", "")),
                }
                # R25-P0-1: the defence filter marks, it never drops (Rev 0: no item is
                # deleted). A general-feed item with no defence term stays in the day
                # file — searchable, title translated, never summarised — and sits in
                # Genel's closed full dump (build.py), not in any named category.
                if general:
                    entry["savunma_terimi"] = looks_defence(item["title"])
                    if not entry["savunma_terimi"]:
                        entry["category"] = GENERAL
                collected.append(entry)
            if not items:
                failures.append((source["ad"], "feed parsed but empty"))
    if args.sinama_silme_boz:
        # Rev 25 kanıtı: eski `continue` gibi, filtre notlu bir kaynağın bir kalemi düşürülür.
        hedef = next((c for c in collected if c["source"] in filtreli), None) or \
            next(iter(collected), None)
        if hedef:
            collected.remove(hedef)
            print(f"  ~ SINAMA: bir kalem bilerek düşürüldü · {hedef['source']} · {hedef['title'][:60]}")

    # dedupe: same link, or the same headline from several outlets
    seen_urls, seen_titles, unique = set(), {}, []
    for item in sorted(collected, key=lambda i: (i["published"], i["source"]), reverse=True):
        key = title_key(item["title"])
        if url_key(item["url"]) in seen_urls:
            continue
        if key and key in seen_titles:
            seen_titles[key]["also"].append(item["source"])
            continue
        seen_urls.add(url_key(item["url"]))
        item["also"] = []
        if key:
            seen_titles[key] = item
        unique.append(item)

    # Rev 31: aynı gün yeniden toplanırsa günün dosyası ezilmez, birleştirilir.
    day_file = out_dir / f"{today}.json"
    old_payload, before = {}, []
    if day_file.exists():
        text = day_file.read_text(encoding="utf-8")
        old_payload = json.loads(text)
        before = json.loads(text).get("items") or []   # denetim için bağımsız kopya
    items, added, again = merge_day(old_payload.get("items") or [], unique, stamp)
    if args.sinama_damga_boz:
        hedef = next((i for i in items if i.get("ilk_goruldu") and i["ilk_goruldu"] != stamp), None)
        if hedef:
            print(f"  ~ SINAMA: damga bilerek değiştirildi · {hedef['title'][:60]} · "
                  f"{hedef['ilk_goruldu']} → {stamp}")
            hedef["ilk_goruldu"] = stamp
        else:
            print("  ~ SINAMA: değiştirilecek damgalı kalem yok")
    same, changed, missing = stamp_audit(before, items)
    silme_rows = silme_yok(okunan, items, filtreli)

    by_category = {}
    for item in items:
        by_category.setdefault(item["category"], []).append(item)
    # Savunma dışı işaretli kalemler (R25-P0-1) ajanın aday dosyasında Genel'in sonunda:
    # 260 sınırı önce onları keser, savunma başlıklarını değil.
    if GENERAL in by_category:
        by_category[GENERAL].sort(key=lambda i: i.get("savunma_terimi") is False)

    payload = dict(old_payload)
    payload.update({
        "date": today,
        "window_hours": args.hours,
        "scanned_sources": len(sources),
        "failed_sources": len(failures),
        "collected_items": len(collected),
        "unique_items": len(items),
        "categories": {k: len(v) for k, v in sorted(by_category.items())},
        "items": items,
        "failures": [{"source": n, "error": e} for n, e in failures],
        # Taranan kaynakların tam listesi. Yanıt verip hiçbir başlık
        # getirmeyen kaynağın adı başka hiçbir yerde yok: kupürlerden
        # çıkarılamıyor, failures'ta da değil. Kaynak dökümü sayfası onsuz
        # 66'nın 58'ini gösteriyordu ve eksiği fark edilmiyordu.
        "sources": [s["ad"] for s in sources],
        # Rev 31: günün her toplaması — hangi çalıştırma kaç yeni kalem getirdi.
        "toplamalar": (old_payload.get("toplamalar") or []) + [
            {"at": stamp, "yeni": added, "yeniden": again}],
    })

    print(f"kaynak: {len(sources)} · okunamayan: {len(failures)}")
    print(f"ham kalem: {len(collected)} · tekilleştirilmiş: {len(unique)}")
    for name, group in sorted(by_category.items(), key=lambda kv: -len(kv[1])):
        print(f"  {name}: {len(group)}")
    for name, error in failures:
        print(f"  ! {name}: {error}")
    sayim = f"yeni: {added} · değişmedi: {same} · damga değişti: {len(changed)}"
    print(f"  · GEÇ-GELEN {today} ({stamp}): {sayim}"
          + ("" if old_payload else " (günün ilk toplaması)"))

    import uyari   # Rev 30 kanalı; scripts/ bu betiğin dizini
    if changed:
        old, new = changed[0]
        uyari.ekle("GEÇ-GELEN", f"{onek}{today} · yeniden toplamada {len(changed)} kalemin "
                   f"ilk_goruldu damgası değişti — ör. “{old['title'][:70]}” "
                   f"{old.get('ilk_goruldu') or '—'} → {new.get('ilk_goruldu') or '—'}")
    if missing:
        uyari.ekle("GEÇ-GELEN", f"{onek}{today} · yeniden toplamada {len(missing)} kalem "
                   f"günün dosyasından düştü — ör. “{missing[0]['title'][:70]}”")

    prev, prev_brief, late = late_from_yesterday(today, out_dir, args.published)
    today_brief = brief_time(today, args.published)
    today_late = sum(1 for i in items if after_briefing(i, today_brief))
    in_first = None
    if not args.dry_run:
        out_dir.mkdir(parents=True, exist_ok=True)
        aday = write_candidates(today, payload, by_category, late, prev, prev_brief, out_dir)
        day_file.write_text(json.dumps(payload, ensure_ascii=False, indent=1) + "\n",
                            encoding="utf-8")
        print(f"  · {day_file.relative_to(ROOT) if day_file.is_relative_to(ROOT) else day_file}")
        # GEÇ-GELEN: dünün her geç kalemi bugünkü aday dosyasının ilk bölümünde olmalı.
        listed = first_section_urls(aday.read_text(encoding="utf-8"))
        absent = [i for i in late if url_key(i["url"]) not in listed]
        in_first = len(late) - len(absent)
        if absent:
            uyari.ekle("GEÇ-GELEN", f"{onek}{today} · dünkü ({prev}) brifingden sonra gelen "
                       f"{len(absent)}/{len(late)} kalem aday dosyasının ilk bölümünde yok — "
                       f"ör. “{absent[0]['title'][:70]}”")

    brief_txt = lambda b: f"{b:%H:%M}" if b else "yayımlanmadı"
    print(f"  · GEÇ-GELEN: {today} brifingi {brief_txt(today_brief)} → BRİFİNGDEN SONRA {today_late}"
          f" · dün {prev} brifingi {brief_txt(prev_brief)} → {len(late)} geç kalem"
          + (f", aday ilk bölümünde {in_first}/{len(late)}" if in_first is not None else ""))
    renk = "🔴" if changed or missing or (in_first is not None and in_first < len(late)) else "🟢"
    write_summary([
        f"### Toplama · {today} · GEÇ-GELEN (Rev 31)", "",
        f"**{renk} {sayim}**" + ("" if old_payload else " — günün ilk toplaması"), "",
        f"- bu çalıştırmanın damgası `{stamp}` · günün dosyasında {len(items)} kalem"
        f" ({again} kalem yeniden görüldü, üzerine yazılmadı)"
        + (" · SINAMA: bir damga bilerek değiştirildi" if args.sinama_damga_boz else ""),
        f"- {today} brifingi: {brief_txt(today_brief)} · BRİFİNGDEN SONRA jetonlu satır: {today_late}",
        f"- dünkü ({prev}) brifing: {brief_txt(prev_brief)} · BRİFİNGDEN SONRA jetonlu satır: {len(late)}"
        + (f" · aday dosyasının ilk bölümünde {in_first}/{len(late)}" if in_first is not None else ""),
    ])

    # Rev 25 — SİLME-YOK (bloklayıcı, Rev 30: uyari.BLOKLAYICI): dosyalar yazıldıktan sonra
    # tablo (A)'ya basılır; eşitlik bozuksa uyarı kanala gider ve iş kırmızı biter.
    if silme_yok_ozet(silme_rows, today, onek):
        sys.exit(1)


if __name__ == "__main__":
    main()
