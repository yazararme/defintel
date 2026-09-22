#!/usr/bin/env python3
"""
DEFINTEL site builder.

Reads  : source/YYYY-MM-DD.md   (YAML frontmatter + Markdown body)
Writes : reports/YYYY-MM-DD.html, index.html, data/reports.json, data/version.txt

Usage  : python3 build.py
Deps   : markdown, pyyaml   (pip install markdown pyyaml)

The daily agent run only needs to drop a new file into source/ and re-run this.
Nothing else in the repo has to be touched by hand.
"""

import hashlib
import html
import functools
import json
import pathlib
import re
import sys
import urllib.parse as up

import enrich

try:
    import markdown
    import yaml
except ImportError:
    sys.exit("missing deps: pip install markdown pyyaml --break-system-packages")

ROOT = pathlib.Path(__file__).parent
SRC = ROOT / "source"
OUT = ROOT / "reports"
NEWS_OUT = ROOT / "haberler"
DATA = ROOT / "data"
NEWS_DATA = DATA / "news"

SITE_NAME = "DEFINTEL"
SITE_TAGLINE = "Savunma pazarı · günlük bülten"
SITE_URL = "https://defintel.shadovi.com"
# Push service (Cloudflare Worker). Empty string hides the notification button.
PUSH_ENDPOINT = "https://defintel-push.yazararme-c30.workers.dev"
VAPID_PUBLIC_KEY = "BLOHxsm23_gz-DmV0E9xyB3RVQTkCwv06uPv_pme7VApr61x_gnNGGPkTnEI3mNekR7lzZGxNL9hATzaaOYsEZo"

# Kupür bağlantıları Google Çeviri vekilinden geçsin mi? Okuyucu İngilizce
# okumuyor; İngilizce özgün sayfa onun için hedef değil, başarısızlık hâli.
# Bedeli: dışa açılan her dokunuş Google'a gider (adres, zaman, IP) — sızan
# içerik değil, hangi başlığın okunduğu örüntüsü. Kapatmak bu tek satır.
TRANSLATE_PROXY = True
# Vekili reddeden yayıncılar. Engelleme site düzeyinde, makale düzeyinde değil;
# dosya scripts/probe_proxy.py tarafından yazılır, bilinmeyen alan adı geçer
# sayılır (yanlış iyimserin bedeli bir geri tuşu, yanlış kötümserinki sessizce
# İngilizce sayfa vermek).
TRANSLATE_HOSTS = DATA / "translate-hosts.json"

TR_MONTHS = [
    "Ocak", "Şubat", "Mart", "Nisan", "Mayıs", "Haziran",
    "Temmuz", "Ağustos", "Eylül", "Ekim", "Kasım", "Aralık",
]
TR_DAYS = ["Pazartesi", "Salı", "Çarşamba", "Perşembe", "Cuma", "Cumartesi", "Pazar"]
TR_DAYS_SHORT = ["Pzt", "Sal", "Çar", "Per", "Cum", "Cmt", "Paz"]

# Hiçbir yerde render edilmeyen alan bakımı yapılmaz. decision_by dokuz rapor
# boyunca 2026-10-09'da dondu ve kimse fark etmedi; türevi status da her gün
# "izle" diyordu, çünkü bayat tarih hep gelecekte kalıyor. İkisi de emekli —
# gerekirse render yeriyle aynı gün geri gelir.


def tr_date(iso, weekday=False):
    """2026-09-14 -> '14 Eylül 2026' (optionally with weekday)."""
    import datetime
    d = datetime.date.fromisoformat(str(iso))
    s = f"{d.day} {TR_MONTHS[d.month - 1]} {d.year}"
    return f"{s} · {TR_DAYS[d.weekday()]}" if weekday else s


def tr_short(iso):
    import datetime
    d = datetime.date.fromisoformat(str(iso))
    return f"{d.day} {TR_MONTHS[d.month - 1]}"


def tr_daybar(iso):
    """'17 Eyl · Per' — 375px'te daybar'ı taşırmayacak kadar kısa."""
    import datetime
    d = datetime.date.fromisoformat(str(iso))
    return f"{d.day} {TR_MONTHS[d.month - 1][:3]} · {TR_DAYS_SHORT[d.weekday()]}"


def split_frontmatter(text):
    if not text.startswith("---"):
        raise ValueError("no frontmatter")
    _, fm, body = text.split("---", 2)
    return yaml.safe_load(fm) or {}, body.lstrip("\n")


def label_table_cells(table_html):
    """Copy each column's header onto its cells so phones can stack the row."""
    headers = [
        re.sub(r"<[^>]+>", "", cell).strip()
        for cell in re.findall(r"<th[^>]*>(.*?)</th>", table_html, re.S)
    ]
    body = re.search(r"<tbody>.*?</tbody>", table_html, re.S)
    if not headers or not body:
        return table_html

    def label_row(row_match):
        seen = [0]

        def label_cell(cell_match):
            i = seen[0]
            seen[0] += 1
            if i >= len(headers):
                return cell_match.group(0)
            return f'<td data-label="{html.escape(headers[i])}"{cell_match.group(1)}'

        return re.sub(r"<td(\s[^>]*>|>)", label_cell, row_match.group(0))

    labelled = re.sub(r"<tr>.*?</tr>", label_row, body.group(0), flags=re.S)
    return table_html[: body.start()] + labelled + table_html[body.end():]


def render_body(md_text, developments=(), alarm=False, report_iso="", slugs=None, up="../"):
    # A bullet list that starts right under a bold lead-in ("**Taşınanlar:**")
    # would otherwise stay inside that paragraph; give it the blank line it needs.
    md_text = re.sub(
        r"(?m)^(?P<line>(?!\s*[-*+] )(?!\s*\d+[.)] )(?!\|)(?!#).+\S)\n(?=- )",
        r"\g<line>" "\n\n",
        md_text,
    )
    md = markdown.Markdown(extensions=["tables", "fenced_code", "attr_list", "sane_lists"])
    out = md.convert(md_text)
    out = enrich.enrich(out, developments, alarm, report_iso, slugs)
    out = out.replace("{UP}", up)
    out = re.sub(r"<table>.*?</table>", lambda m: label_table_cells(m.group(0)), out, flags=re.S)
    out = out.replace("<table>", '<div class="table-wrap"><table>')
    out = out.replace("</table>", "</table></div>")
    return out


def asset(name):
    """assets/x?v=hash — a changed file gets a new URL, so no stale cache."""
    digest = hashlib.sha256((ROOT / "assets" / name).read_bytes()).hexdigest()[:8]
    return f"assets/{name}?v={digest}"


def head(title, depth=0, canonical="", day=""):
    up = "../" * depth
    day_attr = f' data-day="{day}"' if day else ""
    return f"""<!DOCTYPE html>
<html lang="tr">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="robots" content="noindex, nofollow">{f'<link rel="canonical" href="{canonical}">' if canonical else ""}
<title>{html.escape(title)}</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;500&amp;family=Newsreader:ital,opsz,wght@0,6..72,400;0,6..72,500;0,6..72,600;1,6..72,400&amp;display=swap">
<link rel="stylesheet" href="{up}{asset("app.css")}">
<link rel="icon" type="image/png" sizes="32x32" href="{up}{asset("icons/favicon-32.png")}">
<link rel="icon" type="image/png" sizes="64x64" href="{up}{asset("icons/favicon-64.png")}">
<link rel="icon" type="image/png" sizes="16x16" href="{up}{asset("icons/favicon-16.png")}">
<link rel="apple-touch-icon" sizes="180x180" href="{up}{asset("icons/apple-touch-icon.png")}">
<link rel="manifest" href="{up}manifest.webmanifest">
<meta name="theme-color" content="#17171A">
<meta name="apple-mobile-web-app-title" content="{SITE_NAME}">
<meta name="mobile-web-app-capable" content="yes">
<meta name="apple-mobile-web-app-capable" content="yes">
<script>if ("serviceWorker" in navigator) navigator.serviceWorker.register("{up}sw.js");</script>
</head>
<body data-push="{PUSH_ENDPOINT}" data-vapid="{VAPID_PUBLIC_KEY}"{day_attr}>
"""


def masthead(up="", home=False):
    """Künye. Kökteyken logo bağlantı değil: zaten oradasın.

    Kök bugünün brifingi, yani logo oraya götürüyor — ama kök sayfadayken
    tıklayınca hiçbir şey olmuyordu ve bu, bozuk bir bağlantı gibi okunuyor.
    Götüremeyeceği bir yer vaat etmeyen tek doğru şekil: düz metin.
    """
    mark = (f'<span class="wordmark wordmark--here">{SITE_NAME}</span>' if home
            else f'<a class="wordmark" href="{up}index.html">{SITE_NAME}</a>')
    return f"""<header class="masthead">
  <div class="wrap masthead-inner">
    {mark}
    <span class="tagline">{SITE_TAGLINE}</span>
  </div>
</header>
"""


def daybar(kind, day, prev, nxt, cross_day, up=""):
    """Okunan günün tek gezinme şeridi: ürün içinde ‹/›, ortada arşiv, sağda karşı ürün.

    Karşı ürün her zaman aynı güne gider; o gün için karşı sayfa yoksa bağlantı
    tıklanamaz hale gelir ama kaldırılmaz — yokluğu da bilgidir.
    """
    def arrow(target, glyph, label):
        if target:
            return f'<a class="daybar-arrow" href="{target}.html" aria-label="{label}">{glyph}</a>'
        return f'<span class="daybar-arrow" aria-disabled="true" aria-label="{label}">{glyph}</span>'

    if kind == "report":
        cross = f'<a class="daybar-link" href="{up}haberler/{cross_day}.html">MEDYA TAKİBİ →</a>'
        missing = '<span class="daybar-link daybar-link--off">Medya takibi yok</span>'
    else:
        cross = f'<a class="daybar-link" href="{up}reports/{cross_day}.html">← BRİFİNG</a>'
        missing = '<span class="daybar-link daybar-link--off">Brifing yok</span>'

    return f"""<nav class="daybar" aria-label="Gün gezinmesi">
  <div class="wrap daybar-inner">
    {arrow(prev, "‹", "Önceki gün")}
    <a class="daybar-date num" href="{up}arsiv.html">{tr_daybar(day)}</a>
    {arrow(nxt, "›", "Sonraki gün")}
    {cross if cross_day else missing}
  </div>
</nav>
"""


def endnav(kind, day, prev, cross_day, cross_count=None, up=""):
    """Sayfa sonundaki çıkış yolu.

    `daybar` okumaya başlamadan önceki niyeti karşılıyor; okuyucu asıl niyetini
    brifingi bitirdiği anda kuruyor ve orada yapışkan şerit çoktan kaybolmuş
    oluyor. Aynı üç hedef, tam cümleyle.
    """
    same = "brifingi" if kind == "report" else "medya takibi"
    other = "medya takibi" if kind == "report" else "brifing"
    links = []
    if prev:
        links.append(f'<a class="endnav-go" href="{prev}.html">← {tr_date(prev)} {same}</a>')

    if not cross_day:
        links.append(f'<span class="endnav-go endnav-go--off">Bu gün için {other} yok</span>')
    elif kind == "report":
        links.append(
            f'<a class="endnav-go" href="{up}haberler/{cross_day}.html">'
            f"Bu günün medya takibi · {cross_count} başlık →</a>"
        )
    else:
        links.append(f'<a class="endnav-go" href="{up}reports/{cross_day}.html">Bu günün brifingi →</a>')

    links.append(f'<a class="endnav-go" href="{up}arsiv.html">Tüm raporlar</a>')
    return f"""<nav class="endnav" aria-label="Sayfa sonu">
  <div class="wrap endnav-inner">{"".join(links)}</div>
</nav>
"""


PROMPTS = """<div class="promptbar" id="installbar" hidden role="region" aria-label="Uygulama olarak yükle">
  <div class="wrap promptbar-inner">
    <p class="promptbar-text">
      <strong>DEFINTEL'i uygulama olarak ekle.</strong>
      <span class="for-chrome">Raporlar tek dokunuşla açılır, çevrimdışı da okunur.</span>
      <span class="for-ios">Paylaş düğmesine dokun, ardından <b>Ana Ekrana Ekle</b>.</span>
      <span class="for-manual">Tarayıcı menüsünden <b>Uygulamayı yükle</b>.</span>
    </p>
    <span class="promptbar-actions">
      <button class="pbtn for-chrome" type="button" data-action="install">Yükle</button>
      <button class="pbtn pbtn--quiet" type="button" data-action="close">Kapat</button>
    </span>
  </div>
</div>
<div class="promptbar" id="notifycard" hidden role="region" aria-label="Bildirim izni">
  <div class="wrap promptbar-inner">
    <p class="promptbar-text">
      <strong data-role="head">Yeni rapor çıkınca haber verelim mi?</strong>
      <span data-role="body">Her sabah rapor yayınlandığında tek bildirim; istediğinde kapatırsın.</span>
    </p>
    <span class="promptbar-actions">
      <button class="pbtn" type="button" data-action="enable">Aç</button>
      <button class="pbtn pbtn--quiet" type="button" data-action="later">Şimdi değil</button>
    </span>
  </div>
</div>
"""

FOOT = """<footer class="foot">
  <div class="wrap foot-inner">
    <p class="foot-note">Yalnızca kamuya açık kaynaklara dayanır; doğrulanmamış iddialar raporda ayrıca işaretlenir.
      MKE'nin resmî görüşünü yansıtmaz.</p>
    <button class="notify" type="button" id="notify" hidden aria-pressed="false">
      <svg class="notify-bell" viewBox="0 0 16 16" width="15" height="15" aria-hidden="true">
        <path d="M8 1.6a3.6 3.6 0 0 0-3.6 3.6c0 2.5-.5 3.7-1.1 4.5-.3.4 0 1 .5 1h8.4c.5 0 .8-.6.5-1-.6-.8-1.1-2-1.1-4.5A3.6 3.6 0 0 0 8 1.6Z"
              fill="none" stroke="currentColor" stroke-width="1.3" stroke-linejoin="round"/>
        <path d="M6.6 12.2a1.5 1.5 0 0 0 2.8 0" fill="none" stroke="currentColor" stroke-width="1.3" stroke-linecap="round"/>
      </svg>
      <span class="notify-label">Yeni rapor bildirimi al</span>
    </button>
  </div>
</footer>
</body>
</html>
"""


HEADLINE_WARNINGS = []
PUBLISHED = DATA / "published.json"


def publish_times():
    """{gün: 'HH:MM'} — ilk yayın anı, bir kez yazılır bir daha değişmez.

    Saat build anından alınıyor ama kalıcı: yoksa her yeniden kurulum dokuz
    günlük arşive bugünün saatini basardı, yani okuyucuya yalan söylerdi.
    """
    try:
        return json.loads(PUBLISHED.read_text(encoding="utf-8"))
    except Exception:
        return {}


def stamp_publish(times, isos):
    """Saati olmayan güne şimdiki saati yaz; olanı asla değiştirme."""
    import datetime as _dt
    from zoneinfo import ZoneInfo
    now = _dt.datetime.now(ZoneInfo("Europe/Istanbul")).strftime("%H:%M")
    changed = False
    for iso in isos:
        if iso not in times:
            times[iso] = now
            changed = True
    if changed:
        PUBLISHED.write_text(json.dumps(times, ensure_ascii=False, indent=1, sort_keys=True) + "\n",
                             encoding="utf-8")
    return times


def summary_line(body):
    """YÖNETİCİ ÖZETİ'nin ilk maddesi — bildirimin gövdesi.

    Manşet sekmede ve arşiv kartında zaten var; bildirimde tekrar etmek yerine
    günün en önemli tek cümlesini taşımak daha çok şey söylüyor.
    """
    block = re.search(r"##\s*YÖNETİCİ ÖZETİ\s*\n(.*?)(?=\n##|\Z)", body, re.S)
    if not block:
        return ""
    for line in block.group(1).split("\n"):
        text = re.sub(r"^\s*(?:\d+[.)]|[-*])\s*", "", line).strip()
        if not text:
            continue
        text = re.sub(r"^\*\*?G\d+\*\*?\s*[—-]\s*", "", text)
        text = re.sub(r"^G\d+\s*[—-]\s*", "", text)
        text = re.sub(r"[*_`\[\]]|\(bkz\.[^)]*\)", "", text).strip()
        return text[:119].rstrip() + "…" if len(text) > 120 else text
    return ""


def guard_headline(title, iso=""):
    """Tek gelişme, en çok 14 kelime — istemin sözüne değil yapıya bakarak.

    Ajan "A; B" biçiminde iki gelişmeyi tek manşete sıkıştırıyordu: arşiv
    kartında da, tarayıcı sekmesinde de, bildirimde de okunamayan bir dize
    çıkıyordu. Kural promptta da var ama garanti burada: noktalı virgül
    varsa ilkinden öncesi alınır.
    """
    text = " ".join(str(title or "").split())
    if ";" in text:
        warn = f"{iso}: manşette ';' vardı, ilk gelişme alındı"
        if warn not in HEADLINE_WARNINGS:
            HEADLINE_WARNINGS.append(warn)
        text = text.split(";", 1)[0].strip().rstrip(",")
    words = text.split()
    if len(words) > 14:
        warn = f"{iso}: manşet {len(words)} kelime (üst sınır 14)"
        if warn not in HEADLINE_WARNINGS:
            HEADLINE_WARNINGS.append(warn)
    return text


def build_report(meta, body_html, iso, prev_day=None, next_day=None,
                 news_counts=None, mke_count=0, published="", scan=None, depth=1):
    title = guard_headline(meta.get("title"), iso) or f"{tr_date(iso)} raporu"
    up = "../" * depth
    # Kök sayfa bugünün brifingi; aynı belge iki adreste durduğu için
    # kanonik olan tarihli olanıdır.
    canonical = f"{SITE_URL}/reports/{iso}.html" if depth == 0 else ""

    banner = (
        f'<p class="alarmbar">{html.escape(str(meta.get("alarm_title") or "Alarm"))}</p>'
        if meta.get("alarm")
        else ""
    )
    # The day bar above already carries the date and the link to that day's
    # clippings, so the rail only repeats what the reader just read.
    rail = [
        '<div class="rail-block rail-block--date"><span class="rail-label">Tarih</span>'
        f'<span class="rail-value num">{tr_date(iso, weekday=True)}</span>'
        # Alışkanlık saate tutunur: her sabah aynı saatte orada olduğunu
        # söylemeyen bir yayın, okuyucuya ne zaman bakacağını öğretemez.
        + (f'<span class="rail-sub num">{published}\'de yayımlandı</span>' if published else "")
        + '</div>'
    ]
    # Emek kanıtı: raporun arkasında kaç kaynak ve kaç başlık durduğu.
    # Veri yoksa basılmaz — bilinmiyor sıfır değildir.
    if scan:
        rail.append(
            '<div class="rail-block"><span class="rail-label">Tarama</span>'
            f'<span class="rail-value"><a href="{up}haberler/{iso}.html">'
            f'<span class="num">{scan[0]}</span> kaynak · '
            f'<span class="num">{scan[1]}</span> başlık →</a></span></div>'
        )
    # Tarama üstverisi — bölüm değil. Taşıdığı şey tek bir sayı ve anlamı
    # "sana da baktık, ama konumuz bu değil": bir tamlık işareti. Sıfırda
    # hiçbir şey basılmaz, çünkü sıfırın gidecek yeri yoktur — kategori boşsa
    # #kat-mke çapası da yoktur ve "0 başlık" tıklanamaz bir etiket olurdu.
    if mke_count:
        rail.append(
            '<div class="rail-block"><span class="rail-label">MKE gündemi</span>'
            f'<span class="rail-value"><a href="{up}haberler/{iso}.html#{cat_id("MKE")}">'
            f'<span class="num">{mke_count}</span> başlık →</a></span></div>'
        )

    news_counts = news_counts or {}
    cross_day = iso if iso in news_counts else None

    return (
        head(f"{title} — {SITE_NAME}", depth=depth, canonical=canonical, day=iso)
        + masthead(up=up, home=depth == 0)
        + daybar("report", iso, prev_day, next_day, cross_day, up=up)
        + f"""<main class="wrap report{' report--alarm' if meta.get('alarm') else ''}">
  <div class="report-grid">
    <aside class="rail{' rail--rich' if len(rail) > 1 else ''}">{''.join(rail)}</aside>
    <article class="column">
      {banner}
      <h1 class="report-title">{html.escape(title)}</h1>
      {enrich.nav(body_html)}
      <div class="prose">
{body_html}
      </div>
    </article>
  </div>
</main>
"""
        + endnav("report", iso, prev_day, cross_day, news_counts.get(iso), up=up)
        + PROMPTS
        + f'<script src="{up}{asset("app.js")}" defer></script>\n'
        + FOOT
    )


NEWS_ORDER = [
    "MKE", "C-UAS ve Hava Savunma", "Topçu ve Mühimmat", "Rakip Duyuruları",
    "İhale ve Sözleşmeler", "Deniz ve İnsansız Sistemler", "Hafif Silah ve Mayın",
    "Tedarik Zinciri", "Politika ve Regülasyon", "Genel Savunma Gündemi",
]
# Hiçbir kategori terimini tutturamayan kalemlerin kovası: bir kategori değil, artık.
GENERAL = "Genel Savunma Gündemi"

# Veri anahtarı "MKE" kalıyor (collect_news.py ile eşleşsin diye); ekranda
# şirket adı en büyük bölüm başlığı olarak durmasın.
NEWS_LABELS = {"MKE": "Doğrudan ilgili"}


def news_label(name):
    return NEWS_LABELS.get(name, name)

NEWS_CORE = {
    "MKE", "C-UAS ve Hava Savunma", "Topçu ve Mühimmat",
    "İhale ve Sözleşmeler", "Rakip Duyuruları",
}
NEWS_SIDE = {
    "Deniz ve İnsansız Sistemler", "Hafif Silah ve Mayın",
    "Tedarik Zinciri", "Politika ve Regülasyon",
}
TIER_POINTS = {"A": 12, "B": 4, "C": 0}

TR_SLUG = str.maketrans({
    "ı": "i", "İ": "i", "ş": "s", "Ş": "s", "ğ": "g", "Ğ": "g",
    "ü": "u", "Ü": "u", "ö": "o", "Ö": "o", "ç": "c", "Ç": "c",
})


def cat_id(name):
    """'C-UAS ve Hava Savunma' -> 'kat-c-uas-ve-hava-savunma'."""
    return "kat-" + re.sub(r"[^a-z0-9]+", "-", name.translate(TR_SLUG).lower()).strip("-")


def norm_url(url):
    """Aynı sayfayı gösteren iki adresi eşitle: sorgu, çapa ve sondaki / atılır."""
    return str(url or "").split("?")[0].split("#")[0].rstrip("/").lower()


@functools.lru_cache(maxsize=1)
def blocked_hosts():
    """Vekili reddettiği ölçülen alan adları. Dosya yoksa kimse engelli değil."""
    try:
        known = json.loads(TRANSLATE_HOSTS.read_text(encoding="utf-8"))
    except Exception:
        return frozenset()
    return frozenset(host for host, ok in known.items() if ok is False)


def proxy_url(url):
    """Adresin koşulsuz vekil hâli: konak noktaları -, tireler --. Yoklayıcı da kullanır."""
    parts = up.urlsplit(url)
    host = parts.hostname or ""
    if not host or parts.scheme not in ("http", "https"):
        return url
    mangled = host.replace("-", "--").replace(".", "-") + ".translate.goog"
    query = up.parse_qsl(parts.query) + [
        ("_x_tr_sl", "auto"), ("_x_tr_tl", "tr"), ("_x_tr_hl", "tr"),
    ]
    return up.urlunsplit(("https", mangled, parts.path, up.urlencode(query), parts.fragment))


def tr_url(url, lang=""):
    """Kupürün gideceği adres: kural elverdiğince vekil, elvermezse özgün.

    Yalnızca kupürler için. Brifingin kaynakçası özgün adresi gösterir; orası
    bir okuma nesnesi değil, delil — neyin okunduğunu değil nerede yazdığını
    söylemek zorunda. Türkçe yayınlar da vekile girmez: çevrilecek bir şey yok,
    kazanç sıfır, bedeli (Google'a giden bir dokunuş daha) sıfır değil.
    """
    host = up.urlsplit(url).hostname or ""
    if not TRANSLATE_PROXY or lang == "tr" or host in blocked_hosts():
        return url
    return proxy_url(url)


def cited_urls(day):
    """O günün brifingindeki adresler — bir kupürün alabileceği en güçlü sinyal."""
    path = SRC / f"{day}.md"
    if not path.exists():
        return set()
    found = re.findall(r"https?://[^\s<>\")]+", path.read_text(encoding="utf-8"))
    return {norm_url(u.rstrip(".,;")) for u in found}


def news_score(item, day, cited, seen=0):
    """Kupürün sıralama puanı.

    `seen`: aynı kaynaktan bu kalemden daha yüksek puanlı kaç kalem olduğu.
    Ceza yalnızca 5'inciden sonra işler — tek kaynak sayfanın beşte birini
    yazabiliyor, ama ilk beş kalemi cezalandırmak sinyali de siliyor.
    """
    category = item.get("category") or GENERAL
    score = 100 if norm_url(item.get("url")) in cited else 0
    score += 25 if category in NEWS_CORE else 10 if category in NEWS_SIDE else 0
    score += TIER_POINTS.get(item.get("tier"), 0)
    score += 6 * min(len(item.get("also") or []), 3)
    published = item.get("published")
    score += 6 if published == day else 2 if published else 0
    return score - 8 * max(0, seen - 5)


def rank_news(items, day, cited):
    """(puan, dosya sırası, kalem) listesi, puana göre.

    Kaynak cezası kalemin dosyadaki sırasına göre dağıtılsaydı bir kaynağın
    hangi kaleminin cezalandırıldığı rastlantı olurdu; önce cezasız puana göre
    sıralanıyor, ceza o sırada dağıtılıyor. Aynı veriden hep aynı liste çıkar.
    """
    ordered = sorted(
        ((news_score(item, day, cited), i, item) for i, item in enumerate(items)),
        key=lambda row: (-row[0], row[1]),
    )
    seen, ranked = {}, []
    for _, i, item in ordered:
        source = item.get("source", "")
        seen[source] = seen.get(source, 0) + 1
        ranked.append((news_score(item, day, cited, seen[source]), i, item))
    return sorted(ranked, key=lambda row: (-row[0], row[1]))


HIGHLIGHT_MAX = 12
HIGHLIGHT_PER_SOURCE = 2
CATEGORY_ALL_UNDER = 20   # bu sayıya kadar kategori bütünüyle açık durur
CATEGORY_HEAD = 15        # aşarsa açık kalan baş kısım, gerisi "+N daha" arkasında


def category_head(rows):
    """Bir kategorinin katlama açmadan görünen baş kısmı."""
    return rows if len(rows) <= CATEGORY_ALL_UNDER else rows[:CATEGORY_HEAD]


def news_layout(items, day, cited):
    """Sayfanın varsayılan görünümü: (öne çıkanlar, [(kategori, sıralı satırlar)]).

    Hem `build_news_page` hem `scripts/summarise_news.py` buradan okuyor. Özet
    kapsamı "katlama açmadan görebildiğin her satır" diye tanımlandığına göre
    sayfanın şeklini iki yerde ayrı ayrı tarif etmek kapsamı sessizce kaydırırdı.
    """
    ranked = rank_news(items, day, cited)

    buckets = {}
    for row in ranked:
        buckets.setdefault(row[2].get("category") or GENERAL, []).append(row)
    order = ([n for n in NEWS_ORDER if n != GENERAL]
             + sorted(set(buckets) - set(NEWS_ORDER)) + [GENERAL])
    present = [(name, sorted(buckets[name], key=lambda r: (-r[0], r[1])))
               for name in order if buckets.get(name)]

    # Öne çıkanlar: analistin listeye giriş noktası — kategoriler arası, puana
    # göre, kaynak başına en fazla ikisi
    top, quota = [], {}
    for row in ranked:
        source = row[2].get("source", "")
        if quota.get(source, 0) >= HIGHLIGHT_PER_SOURCE:
            continue
        quota[source] = quota.get(source, 0) + 1
        top.append(row)
        if len(top) == HIGHLIGHT_MAX:
            break

    return top, present


def default_visible(items, day, cited):
    """Özet kapsamı: tıklamadan görüyorsan özeti vardır.

    Öne çıkanlar'ın 12'si + her kategorinin açık baş kısmı, sayfa sırasında.
    "+N daha" arkasındaki kuyruk ve Genel kovasının tamamı tasarım gereği
    kapsam dışı — orada özet satır başına gürültü olurdu.
    """
    top, present = news_layout(items, day, cited)
    rows = list(top)
    for name, bucket in present:
        if name != GENERAL:
            rows += category_head(bucket)

    seen, out = set(), []
    for _, _, item in rows:
        url = norm_url(item.get("url"))
        if url in seen:
            continue
        seen.add(url)
        out.append(item)
    return out


def watch_key(text):
    """İzleme kalemini günler arası eşleştiren kaba anahtar.

    Kalemin kuyruğu ("— bekliyor. …") her gün değişebiliyor; kimliği baştaki
    adı. Kimlik numarası konumsal olduğu için anahtarın parçası olamaz.
    """
    head = re.split(r"—|\(", text)[0]
    head = re.sub(r"^\W*G\d+\s*·?\s*", "", head.strip())
    head = re.sub(r"[^\w\s]", " ", head.lower())
    return " ".join(head.split())[:45]


def watch_items(body):
    """İZLEME LİSTESİ maddeleri: {anahtar: ham satır}."""
    block = re.search(r"##\s*İZLEME LİSTESİ\s*\n(.*?)(?=\n##|\Z)", body, re.S)
    if not block:
        return {}
    items = {}
    for line in block.group(1).split("\n"):
        if not line.strip().startswith("-"):
            continue
        text = re.sub(r"\s+", " ", line).strip("- ").strip()
        key = watch_key(text)
        if key:
            items[key] = text
    return items


def thread_slug(name, taken):
    """Addan kalıcı kimlik: iplik sayfasının adresi bu.

    Ajan watch: alanında kendi id'sini verdiğinde o kullanılıyor; vermediği
    sürece ad üzerinden türetiliyor. İkisi de aynı yere çıkıyor, ama ajanınki
    ifade değiştiğinde de sabit kalır — türetilen kalmaz.
    """
    base = re.sub(r"[^a-z0-9]+", "-", name.translate(TR_SLUG).lower()).strip("-")[:48]
    base = base or "iplik"
    slug, n = base, 2
    while slug in taken and taken[slug] != name:
        slug, n = f"{base}-{n}", n + 1
    taken[slug] = name
    return slug


def build_threads(sources):
    """Her izleme kalemini günler boyunca izle: ne zaman açıldı, ne zaman kımıldadı.

    Bir ipliğin geçmişi başka hiçbir yerde yok — rapor onu her gün yeniden
    yazıyor ama dünkü hâliyle yan yana koymuyor. Ürünün en güçlü bağlanma
    kolu bu: "Malezya MERAD" sayfası, o dosyanın kendi zaman çizgisi.
    """
    alias = thread_aliases()
    threads, taken, prev, day_map = {}, {}, {}, {}
    for iso, meta, body in sources:
        today = watch_items(body)
        # Ajanın verdiği kalıcı kimlikler: varsa bulanık eşleşmenin önüne geçer.
        declared = {}
        for w in (meta.get("watch") or []):
            if isinstance(w, dict) and w.get("id"):
                declared[watch_key(str(w.get("name") or w["id"]))] = w
        seen = {}
        for key, raw in today.items():
            spec = declared.get(key)
            if spec:
                slug = alias.get(str(spec["id"]), str(spec["id"]))
            else:
                old = watch_match(key, prev)
                slug = (prev[old][0] if old and old in prev
                        else thread_slug(watch_label(raw), taken))
                slug = alias.get(slug, slug)
            seen[key] = (slug, raw)
            day_map.setdefault(iso, {})[key] = slug
            th = threads.setdefault(slug, {
                "slug": slug, "name": watch_label(raw), "opened": iso,
                "entries": [], "last": iso, "closed": None, "state": "open",
            })
            th["name"] = watch_label(raw) or th["name"]
            th["last"] = iso
            th["state"], th["closed"] = "open", None
            if "ilerledi" in raw:
                # Kimlikler Rev 11'den beri ekranda yok; iplik satırında da olmaz.
                line = re.sub(r"[*_`]", "", raw)
                line = re.sub(r"\s*\((?:bkz\.\s*)?G\d+\)", "", line)
                line = re.sub(r"\s+", " ", line).strip(" .")
                th["entries"].append({"day": iso, "line": line})
        # Kapanma yalnızca açık bildirimle olur: ajanın o gün yazmayı unutması
        # ipliğin bittiği anlamına gelmez. Listeden düşen kalem "uykuda"
        # sayılır — bildiğimiz tek şey görünmediği, bittiği değil.
        for w in (meta.get("watch") or []):
            if isinstance(w, dict) and w.get("closed") and w.get("id"):
                slug = alias.get(str(w["id"]), str(w["id"]))
                if slug in threads:
                    threads[slug]["state"], threads[slug]["closed"] = "closed", iso
        # Uyku kararı anahtara değil kimliğe bakar: ajan ifadeyi değiştirdiğinde
        # dünkü anahtar bugün yok sayılıyor ama iplik aynı iplik. Bugün hiçbir
        # kalem o kimliğe düşmediyse uykuda; düştüyse, adı ne olursa olsun açık.
        still = {slug for slug, _raw in seen.values()}
        for slug, _raw in prev.values():
            if slug not in still and threads[slug]["state"] == "open":
                threads[slug]["state"] = "dormant"
        prev = seen
    return threads, day_map


def watch_match(key, previous):
    """Dünün hangi kalemi bu? Ajan ifadeyi her gün biraz değiştiriyor.

    Tam eşitlik ararsak "…ayrı hedef sınıfı" ile "…şartnamelerde ayrı hedef
    sınıfı" iki ayrı kalem sayılıyor: biri düşmüş biri yeni doğmuş görünüyor
    ve ikisi de yalan. Kelime örtüşmesi bu kaymaya dayanıyor.
    """
    if key in previous:
        return key
    words = set(key.split())
    if not words:
        return None
    best, score = None, 0.0
    for old in previous:
        ow = set(old.split())
        if not ow:
            continue
        overlap = len(words & ow) / max(len(words), len(ow))
        if overlap > score:
            best, score = old, overlap
    return best if score >= 0.6 else None


def watch_label(text):
    """Ham satırdan görünen adı çıkar: kimlik, durum ve açıklama olmadan."""
    head = re.split(r"—", text)[0]
    head = re.sub(r"^\W*G\d+\s*·?\s*", "", head.strip())
    return re.sub(r"[*_`]", "", head).strip(" .")


THREAD_OUT = ROOT / "izleme"
THREADS_JSON = DATA / "threads.json"
THREAD_ALIASES = DATA / "thread-aliases.json"


def thread_aliases():
    """{eski kimlik: kanonik kimlik} — bulanık eşleşmenin bıraktığı bölünmeleri onarır.

    Ajan ifadeyi esaslı değiştirdiğinde kelime örtüşmesi ipliği kaybediyor ve
    aynı dosya ikiye bölünüyor. Takma ad dosyası bunu eski günleri yeniden
    ürettirmeden birleştirir; ajan kalıcı id vermeye başladıktan sonra yeni
    bölünme oluşmaz.
    """
    try:
        data = json.loads(THREAD_ALIASES.read_text(encoding="utf-8"))
    except Exception:
        return {}
    # "_" ile başlayan anahtarlar dosyanın kendi açıklaması, takma ad değil.
    return {k: v for k, v in data.items() if not k.startswith("_")}


def age_words(days):
    return "bugün" if days == 0 else "dün" if days == 1 else f"{days} gün önce"


def thread_page(th, latest):
    """Bir ipliğin kendi zaman çizgisi."""
    import datetime as _dt
    opened = tr_date(th["opened"])
    moved = th["entries"]
    gap = (_dt.date.fromisoformat(latest) - _dt.date.fromisoformat(th["last"])).days
    state = th.get("state", "open")
    if state == "closed":
        status = f'<span class="thread-state thread-state--closed">Kapandı · {tr_date(th["closed"])}</span>'
    elif state == "dormant":
        # "Kapandı" demiyoruz: bildiğimiz tek şey listede görünmediği.
        status = (f'<span class="thread-state thread-state--dormant">Listede görünmüyor'
                  f' · son kayıt {tr_date(th["last"])}</span>')
    else:
        status = f'<span class="thread-state">Açık · son hareket {age_words(gap)}</span>'
    rows = "".join(
        f'<li class="thread-entry"><a href="../reports/{e["day"]}.html">'
        f'<span class="thread-day num">{tr_date(e["day"])}</span>'
        f'<span class="thread-line">{html.escape(e["line"])}</span></a></li>'
        for e in reversed(moved)
    ) or ('<li class="thread-entry thread-entry--none">Açıldığından beri kayda geçen '
          "bir hareket olmadı.</li>")
    return (
        head(f'{th["name"]} — izleme — {SITE_NAME}', depth=1)
        + masthead(up="../")
        + f"""<main class="wrap thread">
  <p class="kicker">İzleme dosyası</p>
  <h1 class="report-title">{html.escape(th["name"])}</h1>
  <p class="thread-meta"><span class="num">{opened}</span> tarihinde açıldı · {status}
    · <span class="num">{len(moved)}</span> hareket</p>
  <ol class="thread-list">{rows}</ol>
  <nav class="endnav" aria-label="Devam">
    <span class="wrap endnav-inner">
      <a class="endnav-go" href="index.html">Tüm izleme dosyaları</a>
      <a class="endnav-go" href="../arsiv.html">Tüm raporlar</a>
    </span>
  </nav>
</main>
"""
        + f'<script src="../{asset("app.js")}" defer></script>\n'
        + FOOT
    )


def thread_index(threads, latest):
    import datetime as _dt
    rank = {"open": 0, "dormant": 1, "closed": 2}

    def key(t):
        return (rank.get(t.get("state", "open"), 0),
                -_dt.date.fromisoformat(t["last"]).toordinal())
    rows = []
    for th in sorted(threads.values(), key=key):
        gap = (_dt.date.fromisoformat(latest) - _dt.date.fromisoformat(th["last"])).days
        state = th.get("state", "open")
        age = ("kapandı " + tr_date(th["closed"]) if state == "closed"
               else "son kayıt " + tr_date(th["last"]) if state == "dormant"
               else age_words(gap))
        rows.append(
            f'<li class="thread-row thread-row--{state}">'
            f'<a href="{th["slug"]}.html"><span class="thread-name">{html.escape(th["name"])}</span>'
            f'<span class="thread-age num">{age}</span>'
            f'<span class="thread-count num">{len(th["entries"])} hareket</span></a></li>'
        )
    counts = {k: sum(1 for t in threads.values() if t.get("state", "open") == k)
              for k in ("open", "dormant", "closed")}
    open_n = counts["open"]
    return (
        head(f"İzleme dosyaları — {SITE_NAME}", depth=1)
        + masthead(up="../")
        + f"""<main class="wrap thread">
  <h1 class="report-title">İzleme dosyaları</h1>
  <p class="thread-meta"><span class="num">{counts["open"]}</span> açık ·
    <span class="num">{counts["dormant"]}</span> listede görünmüyor ·
    <span class="num">{counts["closed"]}</span> kapanmış</p>
  <ul class="thread-index">{''.join(rows)}</ul>
  <nav class="endnav" aria-label="Devam"><span class="wrap endnav-inner">
    <a class="endnav-go" href="../arsiv.html">Tüm raporlar</a>
  </span></nav>
</main>
"""
        + f'<script src="../{asset("app.js")}" defer></script>\n'
        + FOOT
    )


def search_rows(sources, threads):
    """Arşiv aramasının dizini: gelişme başına bir satır, iplik başına bir satır.

    Arşiv bugüne kadar yalnızca kart başlıklarını süzüyordu — yani günün
    manşetini. "Weibel" aramak, o adın geçtiği günü bulmuyordu. Dizin gelişme
    düzeyinde: sekiz gelişme/gün ile yıllarca 1 MB'ın altında kalıyor.
    """
    rows = []
    for iso, meta, body in sources:
        labels = {str(d.get("id", "")).lower(): str(d.get("label", "")).strip()
                  for d in (meta.get("developments") or []) if d.get("id")}
        # Gelişmenin tam anlatımı: "### G1 · ad" başlığının altındaki ilk cümle.
        for gid, label, para in re.findall(
                r"###\s*(G\d+)\s*·\s*([^\n]+)\n+([^\n]+)", body):
            text = re.sub(r"[*_`\[\]]|\(bkz\.[^)]*\)", "", para).strip()
            first = re.split(r"(?<=[.!?])\s", text)[0]
            rows.append({"d": iso, "t": label.strip(), "s": first[:180],
                         "u": f"reports/{iso}.html#{gid.lower()}"})
        # Ev'i başka bölüm olan gelişmeler: madde satırından ad + ilk cümle.
        for gid, label, rest in re.findall(
                r"-\s*\*\*(G\d+)\s*·\s*([^*]+)\*\*\s*—\s*([^\n]+)", body):
            if gid.lower() in {r["u"].split("#")[-1] for r in rows if r["d"] == iso}:
                continue
            text = re.sub(r"[*_`\[\]]|\(bkz\.[^)]*\)", "", rest).strip()
            rows.append({"d": iso, "t": label.strip(),
                         "s": re.split(r"(?<=[.!?])\s", text)[0][:180],
                         "u": f"reports/{iso}.html#{gid.lower()}"})
    for th in threads.values():
        rows.append({"d": th["last"], "t": th["name"], "s": "İzleme dosyası",
                     "u": f'izleme/{th["slug"]}.html', "k": "thread"})
    return rows


def load_news():
    """One file per day, written by scripts/collect_news.py."""
    days = {}
    # data/news also holds translations.json and the candidate lists; only the
    # date-named files are days.
    for path in sorted(NEWS_DATA.glob("*.json")):
        if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", path.stem):
            continue
        try:
            days[path.stem] = json.loads(path.read_text(encoding="utf-8"))
        except Exception as exc:
            print(f"  ! skipped {path.name}: {exc}")
    return days


def clip_html(item, day, cited):
    """Özetli satır açılır bir öğe, özetsiz satır tek bağlantı.

    Özet, İngilizce makaleyi *açmamak* için var; o yüzden özetli satırın birincil
    eylemi "özeti oku" oluyor ve kaynak bağlantısı gövdeye iniyor — iki hedefi olan
    bir yüzey tek bağlantı olamaz. Duruş hâlinde iki anatomi neredeyse özdeş görünür;
    farkı chevronun varlığı söyler.
    """
    meta = [html.escape(item.get("source", ""))]
    if norm_url(item.get("url")) in cited:
        meta.append('<span class="clip-cited">Brifingde</span>')
    if item.get("published") and item["published"] != day:
        meta.append(tr_date(item["published"]))
    if item.get("also"):
        meta.append(f'+{len(item["also"])}')
    # Kapsam içindeyken özet gelmemişse söylenir; kapsam dışındaki 400+ satıra
    # konmaz, olmayan bir arızayı duyurmak olurdu. Bu sitede yokluk gizlenmez.
    if item.get("summary_scope") is True and not item.get("summary_tr"):
        meta.append('<span class="clip-nosum">özet alınamadı</span>')

    url = html.escape(tr_url(item["url"], item.get("lang", "")), quote=True)
    raw_url = html.escape(item["url"], quote=True)
    title = html.escape(item.get("title_tr") or item["title"])
    summary = item.get("summary_tr")
    # özet metni de aranabilir olmalı, yoksa yalnızca özette geçen bir ad bulunamaz
    haystack = html.escape(
        " ".join([item.get("title_tr") or "", item["title"], item.get("source", ""), summary or ""])
    )
    row = (
        f'<span class="clip-title">{title}</span>'
        f'<span class="clip-meta">{" · ".join(meta)}</span>'
    )

    if not summary:
        return (
            f'<li class="clip" data-search="{haystack}">'
            f'<a href="{url}" target="_blank" rel="noopener">{row}</a></li>'
        )

    # İngilizce başlık bir doğrulama öğesi, tarama öğesi değil: gövdede duruyor.
    orig = (
        f'<p class="clip-orig">{html.escape(item["title"])}</p>'
        if item.get("title_tr") else ""
    )
    return (
        f'<li><details class="clip" data-search="{haystack}">'
        f"<summary>{row}</summary>"
        f'<div class="clip-body">{orig}'
        f'<p class="clip-summary">{html.escape(summary)}</p>'
        # Gövdede iki hedef: okumaya devam (Türkçe tam metin) ve doğrulama
        # (özgün dildeki sayfa). Sıra niyete göre — okuyan çoğunluk önce gelir.
        + (f'<a class="entry-go" href="{url}" target="_blank" rel="noopener">Türkçe oku ↗</a>'
           if url != raw_url else "")
        + f'<a class="entry-go entry-go--off" href="{raw_url}" target="_blank" rel="noopener">'
        "Özgün metin ↗</a>"
        "</div></details></li>"
    )


def clip_list(rows, day, cited):
    return (
        '<ul class="clips">'
        + "".join(clip_html(r[2], day, cited) for r in rows)
        + "</ul>"
    )


def news_section(name, rows, day, cited):
    """Bir kategori: baş kısmı açık, kuyruğu "+N daha" arkasında."""
    head_html = (
        f'<h2 class="kicker" id="{cat_id(name)}">{html.escape(news_label(name))}'
        f' <span class="kicker-count num">{len(rows)}</span></h2>'
    )
    shown = category_head(rows)
    rest = rows[len(shown):]
    if not rest:
        return head_html + clip_list(shown, day, cited)
    return (
        head_html
        + clip_list(shown, day, cited)
        + f'<details class="more"><summary>+{len(rest)} daha</summary>'
        + clip_list(rest, day, cited)
        + "</details>"
    )


def general_section(rows, day, cited):
    """Artık kovası: kapalı açılır, içinde taranmaya değer üst küme + tam döküm.

    Üst kümenin ölçütü müşterinin kendi kaynak kademelendirmesi (tier A) ve
    kaynak başına tavan; yeni bir anahtar kelime sözlüğü denendi, işe yaramadı.
    """
    worth, seen, picked = [], {}, set()
    for row in sorted(rows, key=lambda r: (-r[0], r[1])):
        source = row[2].get("source", "")
        if row[2].get("tier") != "A" or seen.get(source, 0) >= 3:
            continue
        seen[source] = seen.get(source, 0) + 1
        worth.append(row)
        picked.add(row[1])
    rest = sorted((r for r in rows if r[1] not in picked), key=lambda r: r[1])

    return (
        '<details class="general">'
        f'<summary class="kicker" id="{cat_id(GENERAL)}">{html.escape(GENERAL)}'
        f' <span class="kicker-count num">{len(rows)}</span></summary>'
        f'<h3 class="subkicker">Taramaya değer <span class="kicker-count num">{len(worth)}</span></h3>'
        + clip_list(worth, day, cited)
        + f'<details class="more"><summary>Tam döküm ({len(rest)})</summary>'
        + clip_list(rest, day, cited)
        + "</details></details>"
    )


def build_news_page(day, data, prev_day, next_day, has_report, cited):
    items = data.get("items", [])
    top, present = news_layout(items, day, cited)

    body = [
        '<section class="highlights" id="one-cikanlar">'
        '<h2 class="kicker">Öne çıkanlar'
        f' <span class="kicker-count num">{len(top)}</span></h2>'
        # Öne çıkanlar da kapalı başlar. Sayfa bir tarama yüzeyi: önce 12 başlık
        # görünür, özet isteyen açar. Açık başlayan blok ekranın ilk görüntüsünü
        # üç satıra düşürüyordu.
        + clip_list(top, day, cited)
        + "</section>"
    ]
    for name, rows in present:
        body.append(general_section(rows, day, cited) if name == GENERAL
                    else news_section(name, rows, day, cited))

    # aynı liste iki biçimde: dar ekranda yapışkan çip şeridi, geniş ekranda rail
    jumps = [("one-cikanlar", "Öne çıkanlar", len(top))]
    jumps += [(cat_id(name), news_label(name), len(rows)) for name, rows in present]
    chips = "".join(
        f'<a class="chip" href="#{anchor}">{html.escape(label)}'
        f' <span class="chip-count num">{count}</span></a>'
        for anchor, label, count in jumps
    )
    rail = "".join(
        f'<a class="news-rail-row{" news-rail-row--rest" if label == GENERAL else ""}"'
        f' href="#{anchor}"><span>{html.escape(label)}</span>'
        f'<span class="num">{count}</span></a>'
        for anchor, label, count in jumps
    )

    # "66 kaynak" okunan değil tanımlı kaynak sayısıydı; okunanı yaz, farkı da göster
    defined = data.get("scanned_sources", 0)
    unread = data.get("failed_sources", 0)
    read = defined - unread
    # kapsam yazılmamış eski günlerde (scope 0) jeton hiç basılmaz
    scope = [i for i in items if i.get("summary_scope") is True]
    covered = sum(1 for i in scope if i.get("summary_tr"))
    stat = (
        f'{read} kaynak okundu · {data.get("unique_items", 0)} başlık'
        f' · son {data.get("window_hours", 48)} saat'
        + (f' · {covered}/{len(scope)} özet' if scope else "")
        + (f' · {unread} kaynak yanıt vermedi' if unread else "")
        # Google çubuğu ancak dokunuştan sonra beliriyor; beyan bir kez burada
        # duruyor, 500 satırın her birinde bir jeton olarak değil.
        + (" · başlıklar Türkçe çeviriyle açılır" if TRANSLATE_PROXY else "")
    )
    return (
        head(f"Medya takibi · {tr_date(day)} — {SITE_NAME}", depth=1)
        + masthead(up="../")
        + daybar("news", day, prev_day, next_day, day if has_report else None, up="../")
        + f"""<main class="wrap news">
  <div class="news-head">
    <h1 class="report-title">Medya takibi · {tr_date(day)}</h1>
    <p class="news-stat num">{stat}</p>
  </div>
  <div class="controls">
    <input class="search" id="q" type="search" placeholder="Ara: başlık, kaynak ya da özet…" autocomplete="off">
  </div>
  <nav class="devnav catbar" id="catbar" aria-label="Kategoriler">
    <div class="devnav-track">{chips}</div>
  </nav>
  <div class="news-grid">
    <aside class="rail news-rail">{rail}</aside>
    <div class="news-column">
      {"".join(body) if items else '<p class="empty">Bu gün için kayıt yok.</p>'}
      <p class="empty" id="noresults" hidden>Bu aramayla eşleşen kupür yok.</p>
    </div>
  </div>
</main>
"""
        + endnav("news", day, prev_day, day if has_report else None, up="../")
        + PROMPTS
        + f'<script src="{up}{asset("app.js")}" defer></script>\n'
        + FOOT
    )


def entry_html(r, news_counts):
    day = r["date"]
    rail = [f'<time class="datestamp num">{tr_date(day)}</time>']
    if r["alarm"]:
        rail.append('<span class="badge badge--alarm">Alarm</span>')

    # İki yüzü olan bir günün seçicisi, yüzü de seçtirmek zorunda: kartın tamamı
    # tek bağlantı olduğunda arşivden kupür listesine giden hiçbir yol yoktu.
    count = news_counts.get(day)
    clips = (
        f'<a class="entry-go" href="haberler/{day}.html">Medya takibi · {count} →</a>'
        if count is not None
        else '<span class="entry-go entry-go--off">Medya takibi yok</span>'
    )

    # Gelişme etiketleri karttan kalktı; arama zayıflamasın diye haystack'te kalıyorlar.
    labels = [str(d.get("label") or d.get("id") or "") for d in (r.get("developments") or [])]
    haystack = " ".join(
        [day, tr_date(day), tr_short(day), r.get("title", ""), r.get("summary", "")]
        + [str(t) for t in r.get("tags", [])] + labels
    ).lower()

    return f"""<article class="entry"
   data-tags="{html.escape('|'.join(str(t) for t in r.get('tags', [])))}"
   data-search="{html.escape(haystack)}">
  <div class="entry-rail">{''.join(rail)}</div>
  <div class="entry-main">
    <h2 class="entry-title"><a href="{r['path']}">{html.escape(r.get('title', ''))}</a></h2>
    <p class="entry-summary">{html.escape(r.get('summary', ''))}</p>
    <div class="entry-nav">
      <a class="entry-go" href="{r['path']}">Brifing →</a>
      {clips}
    </div>
  </div>
</article>"""


def build_index(reports, version, news_counts):
    if not reports:
        body = '<p class="empty">Henüz rapor yok.</p>'
    else:
        body = '<div class="feed">' + "".join(entry_html(r, news_counts) for r in reports) + "</div>"
        body += '<p class="empty" id="noresults" hidden>Bu filtreyle eşleşen rapor yok.</p>'

    return (
        head(f"{SITE_NAME} — {SITE_TAGLINE}")
        + masthead()
        + f"""<main class="wrap">
  <div class="controls">
    <input class="search" id="q" type="search" placeholder="Ara: konu ya da tarih…" autocomplete="off">
  </div>
  {body}
</main>
<script>
// An installed app on a phone resumes the page it had open instead of
// reloading it, so check whether any report changed whenever the app comes back.
(function () {{
  var shown = "{version}", last = 0;
  function check() {{
    if (document.visibilityState !== "visible" || Date.now() - last < 30000) return;
    last = Date.now();
    fetch("data/version.txt", {{ cache: "no-store" }})
      .then(function (r) {{ return r.ok ? r.text() : shown; }})
      .then(function (v) {{ if (v.trim() !== shown) location.reload(); }})
      .catch(function () {{}});
  }}
  document.addEventListener("visibilitychange", check);
  window.addEventListener("pageshow", check);
  window.addEventListener("focus", check);
}})();
</script>
<script src="{asset("app.js")}" defer></script>
"""
        + PROMPTS
        + FOOT
    )


def main():
    OUT.mkdir(exist_ok=True)
    DATA.mkdir(exist_ok=True)
    SRC.mkdir(exist_ok=True)

    news = load_news()
    news_days = sorted(news)
    # kupür çipi o günün başlık sayısını taşıyor: dokunmak için somut bir sebep
    news_counts = {day: data.get("unique_items", 0) for day, data in news.items()}
    # Sayılabilen şeyi build sayar: ajan aday listesinden bir sayıyı elle
    # kopyalıyordu ve yanlış saysa kimse çapraz kontrol etmezdi.
    # Emek kanıtı: o günün taraması kaç kaynak okudu, kaç başlık buldu.
    scan_counts = {
        day: (data.get("scanned_sources", 0) - data.get("failed_sources", 0),
              data.get("unique_items", 0))
        for day, data in news.items()
        if data.get("unique_items")
    }
    mke_counts = {
        day: sum(1 for i in data.get("items", []) if i.get("category") == "MKE")
        for day, data in news.items()
    }

    # daybar komşuları için önce hangi günlerin gerçekten rapor verdiğini bil
    sources = []
    for path in sorted(SRC.glob("*.md")):
        try:
            meta, body = split_frontmatter(path.read_text(encoding="utf-8"))
        except Exception as exc:
            print(f"  ! skipped {path.name}: {exc}")
            continue
        sources.append((path.stem, meta, body))

    published = stamp_publish(publish_times(), [iso for iso, _m, _b in sources])
    # Gün -> {kalem anahtarı: iplik slug'ı}: satırdaki ad kendi dosyasına bağlanır.
    threads, day_slugs = build_threads(sources)

    reports = []
    for i, (iso, meta, body) in enumerate(sources):
        developments = meta.get("developments") or []
        body_html = render_body(body, developments, bool(meta.get("alarm")), iso,
                                day_slugs.get(iso), up="../")
        page = build_report(
            meta, body_html, iso,
            sources[i - 1][0] if i else None,
            sources[i + 1][0] if i + 1 < len(sources) else None,
            news_counts,
            mke_counts.get(iso, 0),
            published.get(iso, ""),
            scan_counts.get(iso),
        )
        # Atıf kanonik kalmalı: [K#] yayıncının kendi sayfasını gösterir, vekili
        # değil. Okuma yolu ayrı bir çipte durur — o yüzden koruma "KAYNAKLAR
        # dışında" gibi konuma göre değil yapıya göre daraltılıyor: vekil adresi
        # yalnızca a.tr-read içinde geçebilir. Yeniden düzenlemelere dayanır.
        if "translate.goog" in re.sub(r'<a class="tr-read".*?</a>', "", page, flags=re.S):
            sys.exit(f"{iso}: brifingde izinsiz çeviri vekili bağlantısı var")
        (OUT / f"{iso}.html").write_text(page, encoding="utf-8")

        reports.append(
            {
                "date": iso,
                "title": guard_headline(meta.get("title"), iso),
                "summary": meta.get("summary", ""),
                "lead": summary_line(body),
                "alarm": bool(meta.get("alarm")),
                "alarm_title": meta.get("alarm_title", ""),
                "tags": [str(t) for t in meta.get("tags", [])],
                "developments": developments,
                "path": f"reports/{iso}.html",
            }
        )
        print(f"  · reports/{iso}.html")

    reports.sort(key=lambda r: r["date"], reverse=True)

    (DATA / "reports.json").write_text(
        json.dumps(reports, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    # changes whenever any report is added, removed or edited
    version = hashlib.sha256(
        b"".join(p.name.encode() + p.read_bytes() for p in sorted(SRC.glob("*.md")))
    ).hexdigest()[:16]
    (DATA / "version.txt").write_text(version + "\n", encoding="utf-8")
    if news_days:
        NEWS_OUT.mkdir(exist_ok=True)
        report_days = {r["date"] for r in reports}
        for i, day in enumerate(news_days):
            cited = cited_urls(day)
            page = build_news_page(
                day, news[day],
                news_days[i - 1] if i else None,
                news_days[i + 1] if i + 1 < len(news_days) else None,
                day in report_days, cited,
            )
            (NEWS_OUT / f"{day}.html").write_text(page, encoding="utf-8")
            hits = sum(1 for it in news[day].get("items", []) if norm_url(it.get("url")) in cited)
            print(
                f'  · haberler/{day}.html ({news[day].get("unique_items", 0)} başlık'
                f" · {hits} brifing atıflı)"
            )

    (ROOT / "arsiv.html").write_text(
        build_index(reports, version, news_counts), encoding="utf-8"
    )
    # Kök = bugünün brifingi. Kurulu uygulamayı açan okuyucu bir dizinle değil
    # o günün raporuyla karşılaşır; arşiv bir tık ötede durur.
    if sources:
        iso, meta, body = sources[-1]
        body_html = render_body(body, meta.get("developments") or [],
                                bool(meta.get("alarm")), iso,
                                day_slugs.get(iso), up="")
        (ROOT / "index.html").write_text(
            build_report(meta, body_html, iso,
                         sources[-2][0] if len(sources) > 1 else None, None,
                         news_counts, mke_counts.get(iso, 0),
                         published.get(iso, ""), scan_counts.get(iso), depth=0),
            encoding="utf-8")
    # İzleme dosyaları: bir ipliğin geçmişi başka hiçbir yerde durmuyor.
    if threads and sources:
        THREAD_OUT.mkdir(exist_ok=True)
        latest = sources[-1][0]
        for th in threads.values():
            (THREAD_OUT / f'{th["slug"]}.html').write_text(
                thread_page(th, latest), encoding="utf-8")
        (THREAD_OUT / "index.html").write_text(
            thread_index(threads, latest), encoding="utf-8")
        # Ajanın okuyacağı açık iplik listesi. Yapıştırılan metin ikinci gün
        # bayatlar; dosya her kurulumda tazelenir.
        THREADS_JSON.write_text(json.dumps(
            [{"id": t["slug"], "name": t["name"], "son_hareket": t["last"]}
             for t in sorted(threads.values(), key=lambda x: x["last"], reverse=True)
             if t.get("state", "open") != "closed"],
            ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
        st = {k: sum(1 for t in threads.values() if t.get("state", "open") == k)
              for k in ("open", "dormant", "closed")}
        print(f"  · izleme/ ({len(threads)} dosya · {st['open']} açık · "
              f"{st['dormant']} uykuda · {st['closed']} kapalı)")

    # Okuyucu gün atlar; ürün bugüne kadar bunu sessizlikle cezalandırıyordu.
    # Atlanan günler kendi tek cümleleriyle geri veriliyor.
    (DATA / "index.json").write_text(
        json.dumps([
            {"date": r["date"], "title": r["title"], "alarm": r["alarm"],
             "lead": r.get("lead", "") or r.get("summary", ""), "url": r["path"]}
            for r in reports
        ], ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    (DATA / "search.json").write_text(
        json.dumps(search_rows(sources, threads), ensure_ascii=False,
                   separators=(",", ":")) + "\n", encoding="utf-8")
    (ROOT / ".nojekyll").touch()

    for w in HEADLINE_WARNINGS:
        print(f'  ! {w}')
    # Sessizce birikmesin: tarihi okunamayan kaynak, yaş jetonu alamıyor.
    if enrich.UNPARSED_DATES:
        print(f"  ! {len(enrich.UNPARSED_DATES)} kaynakta tarih okunamadı "
              f"(DD.MM.YYYY bekleniyor)")
        for entry in enrich.UNPARSED_DATES[:4]:
            print(f"      {entry}")
    print(f"  · arsiv.html  ({len(reports)} rapor)  ·  index.html = {sources[-1][0] if sources else '—'}")
    print("  · data/reports.json")


if __name__ == "__main__":
    main()
