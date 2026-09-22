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


def render_body(md_text, developments=()):
    # A bullet list that starts right under a bold lead-in ("**Taşınanlar:**")
    # would otherwise stay inside that paragraph; give it the blank line it needs.
    md_text = re.sub(
        r"(?m)^(?P<line>(?!\s*[-*+] )(?!\s*\d+[.)] )(?!\|)(?!#).+\S)\n(?=- )",
        r"\g<line>" "\n\n",
        md_text,
    )
    md = markdown.Markdown(extensions=["tables", "fenced_code", "attr_list", "sane_lists"])
    out = md.convert(md_text)
    out = enrich.enrich(out, developments)
    out = re.sub(r"<table>.*?</table>", lambda m: label_table_cells(m.group(0)), out, flags=re.S)
    out = out.replace("<table>", '<div class="table-wrap"><table>')
    out = out.replace("</table>", "</table></div>")
    return out


def asset(name):
    """assets/x?v=hash — a changed file gets a new URL, so no stale cache."""
    digest = hashlib.sha256((ROOT / "assets" / name).read_bytes()).hexdigest()[:8]
    return f"assets/{name}?v={digest}"


def head(title, depth=0):
    up = "../" * depth
    return f"""<!DOCTYPE html>
<html lang="tr">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="robots" content="noindex, nofollow">
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
<body data-push="{PUSH_ENDPOINT}" data-vapid="{VAPID_PUBLIC_KEY}">
"""


def masthead(up=""):
    return f"""<header class="masthead">
  <div class="wrap masthead-inner">
    <a class="wordmark" href="{up}index.html">{SITE_NAME}</a>
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
    <a class="daybar-date num" href="{up}index.html">{tr_daybar(day)}</a>
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

    links.append(f'<a class="endnav-go" href="{up}index.html">Tüm raporlar</a>')
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


def build_report(meta, body_html, iso, prev_day=None, next_day=None, news_counts=None):
    title = meta.get("title") or f"{tr_date(iso)} raporu"

    banner = (
        f'<p class="alarmbar">{html.escape(str(meta.get("alarm_title") or "Alarm"))}</p>'
        if meta.get("alarm")
        else ""
    )
    # The day bar above already carries the date and the link to that day's
    # clippings, so the rail only repeats what the reader just read.
    rail = [
        '<div class="rail-block"><span class="rail-label">Tarih</span>'
        f'<span class="rail-value num">{tr_date(iso, weekday=True)}</span></div>'
    ]

    news_counts = news_counts or {}
    cross_day = iso if iso in news_counts else None

    return (
        head(f"{title} — {SITE_NAME}", depth=1)
        + masthead(up="../")
        + daybar("report", iso, prev_day, next_day, cross_day, up="../")
        + f"""<main class="wrap report">
  <div class="report-grid">
    <aside class="rail">{''.join(rail)}</aside>
    <article class="column">
      {banner}
      <h1 class="report-title">{html.escape(title)}</h1>
      {enrich.nav(meta.get("developments") or [])}
      <div class="prose">
{body_html}
      </div>
    </article>
  </div>
</main>
"""
        + endnav("report", iso, prev_day, cross_day, news_counts.get(iso), up="../")
        + PROMPTS
        + f'<script src="../{asset("app.js")}" defer></script>\n'
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
        + f'<script src="../{asset("app.js")}" defer></script>\n'
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

    # daybar komşuları için önce hangi günlerin gerçekten rapor verdiğini bil
    sources = []
    for path in sorted(SRC.glob("*.md")):
        try:
            meta, body = split_frontmatter(path.read_text(encoding="utf-8"))
        except Exception as exc:
            print(f"  ! skipped {path.name}: {exc}")
            continue
        sources.append((path.stem, meta, body))

    reports = []
    for i, (iso, meta, body) in enumerate(sources):
        developments = meta.get("developments") or []
        body_html = render_body(body, developments)
        page = build_report(
            meta, body_html, iso,
            sources[i - 1][0] if i else None,
            sources[i + 1][0] if i + 1 < len(sources) else None,
            news_counts,
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
                "title": meta.get("title", ""),
                "summary": meta.get("summary", ""),
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

    (ROOT / "index.html").write_text(
        build_index(reports, version, news_counts), encoding="utf-8"
    )
    (ROOT / ".nojekyll").touch()

    print(f"  · index.html  ({len(reports)} rapor)")
    print("  · data/reports.json")


if __name__ == "__main__":
    main()
