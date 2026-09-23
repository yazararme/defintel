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
import urllib.parse as urlparse   # `up` değil: şablonlardaki yol değişkeni de `up`

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


# R24-P1-1 — telefonda tablo satırı karta dönüşünce sütun başlıkları gizleniyor;
# "İzlenecek gösterge" hücresi soluk son satırda, anlam hücresiyle aynı görünüyordu.
# Bu sütunun hücresi karttaki etiketini taşır (app.css: td[data-kart]::before).
# Sütun konumla değil başlığıyla bulunur: sıra değişirse etiket yerinde kalır.
KART_ETIKET = {"İzlenecek gösterge": "İzlenecek"}


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
            kart = KART_ETIKET.get(headers[i])
            kart = f' data-kart="{html.escape(kart)}"' if kart else ""
            return f'<td data-label="{html.escape(headers[i])}"{kart}{cell_match.group(1)}'

        return re.sub(r"<td(\s[^>]*>|>)", label_cell, row_match.group(0))

    labelled = re.sub(r"<tr>.*?</tr>", label_row, body.group(0), flags=re.S)
    return table_html[: body.start()] + labelled + table_html[body.end():]


def render_body(md_text, developments=(), alarm=False, report_iso="", slugs=None):
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
    out = kaynakca_sar(out)   # Rev 33: kaynakçadaki yabancı kaynak adları lang="en"
    out = re.sub(r"<table>.*?</table>", lambda m: label_table_cells(m.group(0)), out, flags=re.S)
    out = out.replace("<table>", '<div class="table-wrap"><table>')
    out = out.replace("</table>", "</table></div>")
    return out


def asset(name):
    """/assets/x?v=hash — a changed file gets a new URL, so no stale cache."""
    digest = hashlib.sha256((ROOT / "assets" / name).read_bytes()).hexdigest()[:8]
    return f"/assets/{name}?v={digest}"


DAY_DIR = {"report": "reports", "news": "haberler"}


def day_url(kind, day, anchor=""):
    """Bir günün sayfası — hangi dizinden bakılırsa bakılsın aynı adres.

    Eskiden kardeş dosya adı yazılıyordu ("2026-09-21.html"): /reports/ içinde
    doğru, kökte 404. Sayfanın nerede durduğunu bilmek zorunda olan her bağlantı
    er geç yanlış yerde üretiliyor; site kök alan adında olduğu için buna gerek
    de yok.
    """
    return f"/{DAY_DIR[kind]}/{day}.html{anchor}"


def head(title, canonical="", day=""):
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
<link rel="stylesheet" href="{asset("app.css")}">
<link rel="icon" type="image/png" sizes="32x32" href="{asset("icons/favicon-32.png")}">
<link rel="icon" type="image/png" sizes="64x64" href="{asset("icons/favicon-64.png")}">
<link rel="icon" type="image/png" sizes="16x16" href="{asset("icons/favicon-16.png")}">
<link rel="apple-touch-icon" sizes="180x180" href="{asset("icons/apple-touch-icon.png")}">
<link rel="manifest" href="/manifest.webmanifest">
<meta name="theme-color" content="#17171A">
<meta name="apple-mobile-web-app-title" content="{SITE_NAME}">
<meta name="mobile-web-app-capable" content="yes">
<meta name="apple-mobile-web-app-capable" content="yes">
<script>if ("serviceWorker" in navigator) navigator.serviceWorker.register("/sw.js");</script>
</head>
<body data-push="{PUSH_ENDPOINT}" data-vapid="{VAPID_PUBLIC_KEY}"{day_attr}>
"""


def masthead():
    """Künye. Logo her sayfada aynı bağlantı: "/".

    Kökte bir ara düz metne çevrilmişti — "zaten oradasın" diye. Yanlıştı:
    tarayıcı çerçevesi olmayan kurulu uygulamada künyeye dokunmak okuyucunun
    tek sıfırlama hareketi; başa sarar ve günün baskısını yeniden alır.
    Kendine bağlantı hiçbir şeye mal olmuyor, yokluğu ise hareketin işlemediği
    tek sayfayı yaratıyordu.

    Adres her yerde birebir aynı. Göreli adres her dizinde yeniden
    hesaplanıyordu ve derinliği yanlış geçen tek çağrı sessizce kırık bir
    logo üretiyordu — sayfanın geri kalanı çalıştığı için de fark edilmiyor.
    Site kök alan adında duruyor, o yüzden hesaplanacak bir şey yok.
    """
    return f"""<header class="masthead">
  <div class="wrap masthead-inner">
    <a class="wordmark" href="/">{SITE_NAME}</a>
    <span class="tagline">{SITE_TAGLINE}</span>
  </div>
</header>
"""


def daybar(kind, day, prev, nxt, cross_day):
    """Okunan günün tek gezinme şeridi: ürün içinde ‹/›, ortada arşiv, sağda karşı ürün.

    Karşı ürün her zaman aynı güne gider; o gün için karşı sayfa yoksa bağlantı
    tıklanamaz hale gelir ama kaldırılmaz — yokluğu da bilgidir.
    """
    other = "news" if kind == "report" else "report"

    def arrow(target, glyph, label):
        if target:
            return (f'<a class="daybar-arrow" href="{day_url(kind, target)}" '
                    f'aria-label="{label}">{glyph}</a>')
        return f'<span class="daybar-arrow" aria-disabled="true" aria-label="{label}">{glyph}</span>'

    if kind == "report":
        cross = f'<a class="daybar-link" href="{day_url(other, cross_day)}">MEDYA TAKİBİ →</a>'
        missing = '<span class="daybar-link daybar-link--off">Medya takibi yok</span>'
    else:
        cross = f'<a class="daybar-link" href="{day_url(other, cross_day)}">← BRİFİNG</a>'
        missing = '<span class="daybar-link daybar-link--off">Brifing yok</span>'

    return f"""<nav class="daybar" aria-label="Gün gezinmesi">
  <div class="wrap daybar-inner">
    {arrow(prev, "‹", "Önceki gün")}
    <a class="daybar-date num" href="/arsiv.html">{tr_daybar(day)}</a>
    {arrow(nxt, "›", "Sonraki gün")}
    {cross if cross_day else missing}
  </div>
</nav>
"""


def endnav(kind, day, prev, cross_day, cross_count=None):
    """Sayfa sonundaki çıkış yolu.

    `daybar` okumaya başlamadan önceki niyeti karşılıyor; okuyucu asıl niyetini
    brifingi bitirdiği anda kuruyor ve orada yapışkan şerit çoktan kaybolmuş
    oluyor. Aynı üç hedef, tam cümleyle.
    """
    same = "brifingi" if kind == "report" else "medya takibi"
    other = "medya takibi" if kind == "report" else "brifing"
    other_kind = "news" if kind == "report" else "report"
    links = []
    if prev:
        links.append(f'<a class="endnav-go" href="{day_url(kind, prev)}">'
                     f"← {tr_date(prev)} {same}</a>")

    if not cross_day:
        links.append(f'<span class="endnav-go endnav-go--off">Bu gün için {other} yok</span>')
    elif kind == "report":
        links.append(
            f'<a class="endnav-go" href="{day_url(other_kind, cross_day)}">'
            f"Bu günün medya takibi · {cross_count} başlık →</a>"
        )
    else:
        links.append(f'<a class="endnav-go" href="{day_url(other_kind, cross_day)}">Bu günün brifingi →</a>')

    links.append('<a class="endnav-go" href="/arsiv.html">Tüm raporlar</a>')
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
                 news_counts=None, mke_count=0, published="", scan=None, rivals=(), turkish=(), has_news=False, depth=1, bosluk=()):
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
        + (f'<span class="rail-sub num">{time_with_suffix(published)} yayımlandı</span>'
           if published else "")
        + '</div>'
    ]
    # Emek kanıtı: raporun arkasında kaç kaynak ve kaç başlık durduğu.
    # Veri yoksa basılmaz — bilinmiyor sıfır değildir. MKE sayısı buraya
    # katlandı: kendi başına bir blok olacak kadar ayrı bir şey değil,
    # taramanın içinden çıkan bir alt küme.
    if scan:
        mke_part = (
            '<span class="rival-sep"> · </span>'
            f'<span class="nb"><a href="{day_url("news", iso, "#" + cat_id("MKE"))}">'
            f'MKE <span class="num">{mke_count}</span> →</a></span>'
        ) if mke_count else ""
        tail = "" if mke_count else " →"
        rail.append(
            '<div class="rail-block"><span class="rail-label">Tarama</span>'
            f'<span class="rail-value rail-flow">'
            f'<span class="nb"><a href="{day_url("news", iso)}">'
            f'<span class="num">{scan[0]}</span> kaynak</a></span>'
            '<span class="rival-sep"> · </span>'
            f'<span class="nb"><a href="{day_url("news", iso)}">'
            f'<span class="num">{scan[1]}</span> başlık{tail}</a></span>'
            f'{mke_part}</span>{kanit_html(bosluk)}</div>'
        )
    elif bosluk:
        # Tarama satırı yoksa (başlık sayısı bilinmiyor) uyarı yine kendi bloğunda durur.
        rail.append(f'<div class="rail-block">{kanit_html(bosluk)}</div>')
    # Oyuncular: bugün adı geçen herkes, tek blokta. Dört blok raya sığmıyordu
    # ve üçü aynı soruyu farklı başlıklarla soruyordu. Rol hâlâ duruyor —
    # sırada ve bağlantının nereye gittiğinde — ama başlık artık kimseyi
    # bir şey ilan etmiyor; "oyuncu" bir sınıflandırma değil, bir gözlem.
    if rivals or turkish:
        # Bağlantı rolü değil delili izler. Bir süre rol izliyordu: Türk
        # şirketi o günün bir gelişmesinde geçse bile medya takibine
        # gidiyordu — 23 Eylül'de Aselsan #g7'deydi ve bağlantı onu atlıyordu.
        # Yan yana duran iki ad, görünür bir sebep olmadan farklı davranıyordu.
        # Kural tek: adı bugünün bir gelişmesinde geçiyorsa oraya, yalnız
        # başlık taramasında geçiyorsa taramaya.
        dev_anchor = {name: anchor for name, anchor, _role in rivals if anchor}
        units = []
        for name, anchor, role in rivals:
            if anchor and role == "rakip":
                units.append(f'<a href="{anchor}">{html.escape(name)}</a>')
        for name, nid, hit in turkish:
            if not hit:
                continue
            anchor = dev_anchor.get(name)
            if anchor:
                units.append(f'<a href="{anchor}">{html.escape(name)}</a>')
            else:
                units.append(
                    f'<a href="{day_url("news", iso)}?oyuncu={nid}">'
                    f'{html.escape(name)}</a>' if has_news else html.escape(name)
                )
        arrow = '<a class="rival-count" href="/oyuncular.html">→</a>'
        if units:
            # Ok son adla aynı kırılmaz birimde: tek başına satır başına
            # düşen bir ok, neye ait olduğunu söylemeyen bir işaret olur.
            body = "".join(
                f'<span class="nb">{u}</span><span class="rival-sep"> · </span>'
                for u in units[:-1]
            ) + f'<span class="nb">{units[-1]}&nbsp;{arrow}</span>'
        else:
            body = f'<span class="nb">— {arrow}</span>'
        rail.append(
            '<div class="rail-block"><span class="rail-label">Oyuncular</span>'
            f'<span class="rail-value rail-flow">{body}</span></div>'
        )
    news_counts = news_counts or {}
    cross_day = iso if iso in news_counts else None

    return (
        head(f"{title} — {SITE_NAME}", canonical=canonical, day=iso)
        + masthead()
        + daybar("report", iso, prev_day, next_day, cross_day)
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
        + endnav("report", iso, prev_day, cross_day, news_counts.get(iso))
        + PROMPTS
        + f'<script src="{asset("app.js")}" defer></script>\n'
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
# Rev 25: "Rakip Duyuruları" → "Oyuncu Duyuruları" — kapsam izlenen 64 oyuncu, kural S4
# (öznesi oyuncunun kendisi olan eylem). Veri anahtarı değişmez (Rev 2 emsali); çapa
# görünen adı izler, çünkü tıklanınca adres çubuğunda görünür.
NEWS_LABELS = {"MKE": "Doğrudan ilgili", "Rakip Duyuruları": "Oyuncu Duyuruları"}
NEWS_IDS = {"Rakip Duyuruları": "Oyuncu Duyuruları"}


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
    name = NEWS_IDS.get(name, name)
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
    parts = urlparse.urlsplit(url)
    host = parts.hostname or ""
    if not host or parts.scheme not in ("http", "https"):
        return url
    mangled = host.replace("-", "--").replace(".", "-") + ".translate.goog"
    query = urlparse.parse_qsl(parts.query) + [
        ("_x_tr_sl", "auto"), ("_x_tr_tl", "tr"), ("_x_tr_hl", "tr"),
    ]
    return urlparse.urlunsplit(("https", mangled, parts.path, urlparse.urlencode(query), parts.fragment))


def tr_url(url, lang=""):
    """Kupürün gideceği adres: kural elverdiğince vekil, elvermezse özgün.

    Yalnızca kupürler için. Brifingin kaynakçası özgün adresi gösterir; orası
    bir okuma nesnesi değil, delil — neyin okunduğunu değil nerede yazdığını
    söylemek zorunda. Türkçe yayınlar da vekile girmez: çevrilecek bir şey yok,
    kazanç sıfır, bedeli (Google'a giden bir dokunuş daha) sıfır değil.
    """
    host = urlparse.urlsplit(url).hostname or ""
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
        # R25-P0-1: savunma dışı işaretli kalem yalnız Genel'de (kapalı tam döküm) durur —
        # hangi kategori yazılmış olursa olsun; böylece özet kapsamına da hiç girmez.
        cat = GENERAL if row[2].get("savunma_terimi") is False else row[2].get("category")
        buckets.setdefault(cat or GENERAL, []).append(row)
    order = ([n for n in NEWS_ORDER if n != GENERAL]
             + sorted(set(buckets) - set(NEWS_ORDER)) + [GENERAL])
    present = [(name, sorted(buckets[name], key=lambda r: (-r[0], r[1])))
               for name in order if buckets.get(name)]

    # Öne çıkanlar: analistin listeye giriş noktası — kategoriler arası, puana
    # göre, kaynak başına en fazla ikisi
    top, quota = [], {}
    for row in ranked:
        if row[2].get("savunma_terimi") is False:   # R25-P0-1: yalnız Genel'in tam dökümü
            continue
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
        labels = {str(d.get("id")): str(d.get("label") or "")
                  for d in (meta.get("developments") or []) if isinstance(d, dict)}
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
                "slug": slug, "name": display_name(watch_label(raw)), "opened": iso,
                "entries": [], "last": iso, "closed": None, "state": "open",
            })
            th["name"] = display_name(watch_label(raw)) or th["name"]
            th["last"] = iso
            th["state"], th["closed"] = "open", None
            # Açılış günü sıfırıncı kayıt: "15 Eylül'de açıldı" deyip o günü
            # listelememek, iddia edilen ama gösterilmeyen bir tarih bırakıyordu.
            if not th["entries"]:
                th["entries"].append({
                    "day": iso, "title": watch_opening(raw),
                    "anchor": "#izleme-listesi" if "İZLEME LİSTESİ" in body else "",
                    "opening": True,
                })
                continue
            # Kımıldatan şey ipliğin kendi adı değil, o günkü gelişmedir.
            ref = re.search(r"\bG(\d+)\b", raw)
            if ref:
                gid = f"G{ref.group(1)}"
                th["entries"].append({
                    "day": iso, "title": labels.get(gid) or watch_opening(raw),
                    "anchor": f"#g{ref.group(1)}", "opening": False,
                    # R27-P0-1: o günün durum cümlesi — brifingde "→ bugün:"
                    # satırının kuyruğu. Yoksa boş: uydurulmaz.
                    "note": watch_status(raw),
                })
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


# Ek, saatin okunuşundaki son sayıya uyar — yazılışına değil. "06:16" için
# belirleyici olan 16 değil, "on altı"nın son sözcüğü "altı"dır.
TIME_SUFFIX = {0: "da", 1: "de", 2: "de", 3: "te", 4: "te", 5: "te",
               6: "da", 7: "de", 8: "de", 9: "da",
               10: "da", 20: "de", 30: "da", 40: "ta", 50: "de"}


def time_with_suffix(hhmm):
    """06:16'da, 08:31'de, 06:00'da, 17:05'te.

    Dakika sıfırsa saat okunur: "altı sıfır sıfır" değil "altıda". Sabit bir
    'de eki her dördüncü gün yanlış çıkıyordu; ürünün her gün gösterdiği tek
    Türkçe cümlenin bozuk olması, geri kalanın da özensiz olduğunu söyler.
    """
    try:
        hour, minute = int(hhmm[:2]), int(hhmm[3:5])
    except (ValueError, IndexError):
        return f"{hhmm}'de"
    spoken = minute or hour
    last = spoken % 10 or spoken
    return f"{hhmm}'{TIME_SUFFIX.get(last, 'de')}"


def display_name(name):
    """Ekrana çıkan iplik adı: ajanın o güne ait kimliği adın parçası değil.

    "…yanıt süresi (G3)" gibi adlar, G# kimlikleri Rev 11'de ekrandan
    kaldırıldığı hâlde iplik başlığında yaşamaya devam ediyordu: kimlik
    konumsal, ad kalıcı — biri diğerinin içinde duramaz. Yalnız görünende
    kesiliyor; slug'lar olduğu gibi kalıyor, çünkü adres kararlılığı
    düzgün görünmekten önce gelir.
    """
    name = re.sub(r"\s*\((?:bkz\.\s*)?G\d+(?:\s*,\s*G\d+)*\)\s*$", "", name)
    # "(21.09.2026 raporu)" de aynı kusur: ipliğin işini adın içinde yapan bir
    # geri atıf. O tarih artık iplik sayfasında açılış kaydı olarak duruyor.
    name = re.sub(r"\s*\(\d{2}\.\d{2}\.\d{4}\s+raporu\)\s*$", "", name)
    return name.strip(" .")


def watch_status(text):
    """Kalemin o günkü durum cümlesi: addan ve durum işaretinden sonra kalan düz metin.

    "XM30'da organik C-UAS şartı — *bekliyor.* Prototip teslim edildi, şart hâlâ
    tanımlı değil (G9)." → "Prototip teslim edildi, şart hâlâ tanımlı değil."

    Brifing bu cümleyi "→ bugün:" satırının sonunda basıyor (enrich.reading_path_shape);
    iplik sayfası aynı kuralla aynı cümleyi türetir. Durum işareti ("bekliyor",
    "ilerledi (G3)") bir işaret, cümle değil — atılır. Kimlikler (G#, K#) ve
    "(18.09.2026 raporu)" geri atıfları da. Geriye bir şey kalmazsa boş döner.
    """
    parts = re.split(r"\s—\s|\s–\s", text, maxsplit=1)
    if len(parts) < 2:
        return ""
    rest = parts[1].strip()
    # Baştaki italik durum işareti: *bekliyor.* · *ilerledi (G3).* · _…_
    rest = re.sub(r"^(\*{1,2}|_)[^*_]{0,60}?\1\s*", "", rest)
    rest = re.sub(r"[*_`]", "", rest)
    rest = re.sub(r"^\s*(?:ilerledi|bekliyor)\b\.?", "", rest, flags=re.I)
    rest = re.sub(r"\s*\((?:bkz\.\s*)?G\d+(?:\s*,\s*G\d+)*\)", "", rest)
    rest = re.sub(r"\s*\[K\d+\]", "", rest)
    rest = re.sub(r"\s*\(\d{2}\.\d{2}\.\d{4}\s+raporu\)", "", rest)
    rest = re.sub(r"\(\s*\)", "", rest)
    # "…için bkz. ALARMLAR." brifingin bir bölümüne geri atıf: iplik sayfasında o
    # bölüm yok ve Rev 6'dan beri bu cümleler kaldırılıyor. Cümlesiyle düşer.
    rest = " ".join(c for c in re.split(r"(?<=[.;])(?<!bkz\.)\s+", rest)
                    if not re.search(r"\bbkz\.\s*[A-ZÇĞİÖŞÜ]{3,}", c))
    rest = re.sub(r"\s+", " ", rest).strip(" .,;—–-")
    if not re.search(r"\w", rest):
        return ""
    return enrich.tr_upper_first(rest) + ("" if rest.endswith(("?", "!")) else ".")


def watch_opening(text):
    """Açılış kaydının satırı: ajanın o gün yazdığı izleme cümlesi.

    Ad değil satır: iplik sayfasının birinci kaydı "ne izlemeye başladık"
    sorusunu yanıtlıyor ve bunun cevabı başlığın tekrarı değil, o günkü
    gerekçe. Kimlikler Rev 11'den beri ekranda yok; burada da olmaz.
    """
    line = re.sub(r"[*_`]", "", text)
    line = re.sub(r"^\W*G\d+\s*·?\s*", "", line.strip())
    line = re.sub(r"\s*\((?:bkz\.\s*)?G\d+\)", "", line)
    line = re.sub(r"\s*\[K\d+\]", "", line)
    return re.sub(r"\s+", " ", line).strip(" .")


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


def thread_daybar(latest, report_days=(), news_days=()):
    """R27-P0-2: iplik sayfasının daybar'ı — gelinen günü gösterir.

    İplik sayfası günden bağımsız tek bir dosya; brifingden gelen bağlantı
    `?g=YYYY-MM-DD` taşır ve app.js şeridi o güne kurar (tarih, ‹/›, karşı ürün).
    JavaScript'siz ya da `?g=` olmadan açılınca şerit en son brifing gününü
    gösterir — sitenin "bugün"ü. ‹/› brifing günleri arasında gezer (Rev 0:
    ürün içinde); karşı ürün her zaman aynı güne gider, yoksa tıklanamaz.
    """
    days = sorted(report_days) or [latest]
    news = sorted(set(news_days))
    i = days.index(latest) if latest in days else len(days) - 1
    bar = daybar("report", days[i], days[i - 1] if i else None,
                 days[i + 1] if i + 1 < len(days) else None,
                 days[i] if days[i] in news else None)
    return bar.replace(
        '<nav class="daybar"',
        f'<nav class="daybar" data-rapor="{" ".join(days)}" data-medya="{" ".join(news)}"', 1)


def thread_status(th):
    """R27-P0-1: son hareketin durum cümlesi ve günü — yoksa None.

    Yalnız *son* hareket: daha eski bir hareketin cümlesini bugünkü durum diye
    basmak, ipliğin o günden beri kımıldamadığını gizler. Açılış bir hareket değil.
    """
    moves = [e for e in th["entries"] if not e.get("opening")]
    if not moves or not moves[-1].get("note"):
        return None
    return moves[-1]["note"], moves[-1]["day"]


def thread_page(th, latest, report_days=(), news_days=()):
    """Bir ipliğin kendi zaman çizgisi: ne oldu, şimdi ne durumda (Rev 27)."""
    import datetime as _dt
    opened = tr_date(th["opened"])
    moved = th["entries"]
    # Açılış bir hareket değil: sayı, açıldıktan sonra kaç kez kımıldadığı.
    moves = sum(1 for e in moved if not e.get("opening"))
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
    # İPLİK-DURUM'un kanıtı için bilerek kapatılabilir (IPLIK_BOZ=1).
    now = None if iplik_boz() else thread_status(th)
    now_html = ""
    if now:
        # Tarih cümlenin son kelimesiyle aynı satırda kalır: 375px'te tek başına
        # "· 23 Eylül" diye bir satıra düşünce yetim bir ayraç okunuyordu.
        bas, _, son = now[0].rpartition(" ")
        now_html = (f'<p class="thread-status">{html.escape(bas + " " if bas else "")}'
                    f'<span class="thread-status-end">{html.escape(son)} '
                    f'<span class="thread-status-day num">· {tr_short(now[1])}</span></span></p>\n  ')

    def row(e):
        day = f'<span class="thread-day num">{tr_date(e["day"])}</span>'
        if e.get("opening"):
            # Açılış satırı ayrı çizilir: bir hareket değil, bağlantısı yok (R27-P1-1).
            return ('<li class="thread-entry thread-entry--open">'
                    f'{day}<span class="thread-text"><span class="thread-tag">açıldı</span>'
                    f'<span class="thread-line">{html.escape(e["title"])}</span></span></li>')
        note = (f'<span class="thread-note">{html.escape(e["note"])}</span>'
                if e.get("note") else "")
        return (f'<li class="thread-entry"><a href="{day_url("report", e["day"], e["anchor"])}">'
                f'{day}<span class="thread-text"><span class="thread-line">'
                f'{html.escape(e["title"])}</span>{note}</span></a></li>')

    rows = "".join(row(e) for e in reversed(moved)) or (
        '<li class="thread-entry thread-entry--none">Açıldığından beri kayda geçen '
        "bir hareket olmadı.</li>")
    return (
        head(f'{th["name"]} — izleme — {SITE_NAME}')
        + masthead()
        + thread_daybar(latest, report_days, news_days)
        + f"""<main class="wrap thread">
  <p class="kicker">İzleme dosyası</p>
  <h1 class="report-title">{html.escape(th["name"])}</h1>
  {now_html}<p class="thread-meta"><span class="num">{opened}</span> tarihinde açıldı · {status}
    · <span class="num">{moves}</span> hareket</p>
  <ol class="thread-list">{rows}</ol>
  <nav class="endnav" aria-label="Devam">
    <span class="wrap endnav-inner">
      <a class="endnav-go" href="/izleme/index.html">Tüm izleme dosyaları</a>
      <a class="endnav-go" href="/arsiv.html">Tüm raporlar</a>
    </span>
  </nav>
</main>
"""
        + f'<script src="{asset("app.js")}" defer></script>\n'
        + FOOT
    )


def iplik_boz():
    """IPLIK_BOZ=1: durum satırı yalnız bu derlemede basılmaz (İPLİK-DURUM kanıtı)."""
    import os
    return os.environ.get("IPLIK_BOZ", "").strip().lower() not in ("", "0", "none", "false")


def iplik_durum_kurali(threads):
    """İPLİK-DURUM (Rev 27): son hareketinde durum cümlesi olan ipliğin sayfasında
    `.thread-status` yoksa Rev 30 kanalına uyarı. Derlenmiş HTML'e bakar — üretim
    kodunun niyetine değil, yayımlanan sayfaya."""
    import os
    beklenen, eksik, var = [], [], 0
    for th in threads.values():
        yol = THREAD_OUT / f'{th["slug"]}.html'
        try:
            metin = yol.read_text(encoding="utf-8")
        except OSError:
            metin = ""
        has = 'class="thread-status"' in metin
        var += has
        if thread_status(th):
            beklenen.append(th["slug"])
            if not has:
                eksik.append(th["slug"])
    boz = " (IPLIK_BOZ=1, bilerek)" if iplik_boz() else ""
    print(f"  · İPLİK-DURUM: {len(eksik)} eksik{boz} · {len(threads)} iplik, "
          f"{len(beklenen)} ipliğin son hareketinde durum cümlesi var, "
          f"{var} sayfada .thread-status, {len(threads) - len(beklenen)} ipliğin yok")
    summary = os.environ.get("GITHUB_STEP_SUMMARY")
    if summary:
        md = ["### İPLİK-DURUM — iplik sayfasında durum satırı (Rev 27)", "",
              f"**{'🟢' if not eksik else '🔴'} İPLİK-DURUM: {len(eksik)} eksik**{boz} · "
              f"{len(beklenen)}/{len(threads)} ipliğin son hareketinde durum cümlesi var", ""]
        if eksik:
            md += [f"- `izleme/{s}.html`" for s in eksik[:10]]
        try:
            with open(summary, "a", encoding="utf-8") as fh:
                fh.write("\n".join(md) + "\n\n")
        except OSError as exc:
            print(f"  ! İPLİK-DURUM: özet yazılamadı: {exc}")
    if eksik:
        from scripts import uyari
        uyari.ekle("İPLİK-DURUM", f"İPLİK-DURUM: {len(eksik)} iplik sayfasında durum satırı yok{boz} — "
                                  f"ilk: {', '.join(eksik[:3])}")
    return eksik


TR_ALPHABET = "abcçdefgğhıijklmnoöpqrsştuüvwxyz"


def tr_collate(text):
    """Türkçe harmanlama anahtarı: ç ç'de, ı i'den önce, Ş s'den sonra.

    Büyük I → ı, İ → i (Türkçe kural). Türk alfabesinde olmayan aksanlı
    harfler (Č, é) temel harflerine iner; harf dışı her şey harflerden önce.
    """
    import unicodedata
    low = text.replace("I", "ı").replace("İ", "i").lower()
    key = []
    for ch in low:
        if ch not in TR_ALPHABET:
            base = unicodedata.normalize("NFD", ch)[0]
            ch = base if base in TR_ALPHABET else ch
        key.append((1, TR_ALPHABET.index(ch)) if ch in TR_ALPHABET else (0, ord(ch)))
    return key


def players_page(hist, kap):
    """/oyuncular.html — kim, hangi segmentte; kapsam tamsa en son ne zaman, kaç gün.

    Tek liste. Bir süre üç başlık altında duruyordu — "Uluslararası rakipler",
    "Yerli rakipler", "Türk sanayi emsalleri" — ama Rev 18'de ray başlığı tam
    da bu yüzden kaldırılmıştı: ürünün kimin rakip olduğuna karar verme
    yetkisi yok.

    KAPSAM-SAYI (Rev 21): bir sayı bir iddiadır. Eşleştirici bir oyuncuyu
    bile güvenle göremiyorsa (alias_test kaldıysa) "Bugün N", "N gün", yaş
    jetonu ve sıklık sırası hep birlikte kalkar; üst satır yalnız "izlenen 64"
    — yapılandırmadan gelen, kapsamdan bağımsız tek sayı — ve sıra
    alfabetik. Oyuncu oyuncu açılma yok. 64'ün hepsi geçince hepsi birlikte
    döner. Sayfa her durumda üretilir.

    Kapsam tamken görülmemiş şirketin jetonu yok: boşluk ifadenin kendisi,
    "bu ada bakıyoruz ve bu ayda hiç geçmedi" — ve artık gerçekten bakılıyor.
    """
    import datetime as _dt
    config = rivals_config()
    if not config:
        return ""
    tam = kap["tam"]
    labels = segment_labels()
    order = {r["id"]: i for i, r in enumerate(config)}
    today = max((e.get("son") or "" for e in hist.values()), default="")

    def row(rival):
        e = hist.get(rival["id"], {})
        segs = e.get("segmentler") or rival.get("segments") or []
        # Ayıraçsız etiketler tek bir dizeye yapışıyordu: "Mühimmat Topçu Hava
        # savunma" üç segment değil bir cümle gibi okunuyor.
        tags = '<span class="ptag-sep">·</span>'.join(
            f'<span class="ptag">{html.escape(labels.get(sg, sg))}</span>' for sg in segs)
        name = (f'<a class="pname" href="/arsiv.html?oyuncu={rival["id"]}">'
                f'{html.escape(rival["name"])}</a><span class="ptags">{tags}</span>')
        if not tam:
            # Sayı yok, jeton yok, "hiç geçmedi" soluklaştırması da yok: o da
            # eşleştiricinin sonucundan türeyen bir iddia.
            return f'<li class="player-row" data-seg="{" ".join(segs)}">{name}</li>'
        son, n = e.get("son") or "", e.get("gun_30g") or 0
        gap = ((_dt.date.fromisoformat(today) - _dt.date.fromisoformat(son)).days
               if son and today else None)
        age = (f'<span class="page num">{age_words(gap)}</span>'
               if gap is not None else "")
        # "N gün": son 30 günün kaçında adı geçti. Eski "N kez" geçiş sayıyor
        # gibi okunuyordu, oysa gün sayıyordu.
        cnt = f'<span class="pcount num">{n} gün</span>' if n else ""
        return (
            f'<li class="player-row{"" if son else " player-row--quiet"}"'
            f' data-seg="{" ".join(segs)}"'
            f' data-today="{1 if gap == 0 else 0}" data-seen="{1 if n else 0}">'
            f'{name}{age}{cnt}</li>'
        )

    def sort_key(rival):
        e = hist.get(rival["id"], {})
        son = e.get("son") or ""
        return (-(e.get("gun_30g") or 0),
                -_dt.date.fromisoformat(son).toordinal() if son else 0,
                order[rival["id"]])

    ranked = (sorted(config, key=sort_key) if tam
              else sorted(config, key=lambda r: tr_collate(r["name"])))
    rows = "".join(row(r) for r in ranked)
    chips = "".join(
        f'<button class="chip pchip" type="button" data-seg="{k}">'
        f'{html.escape(v)}</button>' for k, v in labels.items())
    tracked = f'izlenen <strong data-tally="all">{len(config)}</strong>'
    if tam:
        seen_today = sum(1 for e in hist.values() if e.get("son") and e["son"] == today)
        seen_30 = sum(1 for e in hist.values() if e.get("gun_30g"))
        tally = (f'Bugün <strong data-tally="today">{seen_today}</strong> ·\n'
                 f'    son {WINDOW_DAYS} günde <strong data-tally="seen">{seen_30}</strong> ·\n'
                 f'    {tracked}')
    else:
        tally = tracked
    return (
        head(f"Oyuncular — {SITE_NAME}")
        + masthead()
        + f"""<main class="wrap thread">
  <p class="kicker">Referans</p>
  <h1 class="report-title">Oyuncular</h1>
  <p class="thread-meta num" id="ptally">{tally}</p>
  <nav class="devnav pchips" aria-label="Segment">
    <button class="chip pchip pchip--on" type="button" data-seg="">Tümü</button>{chips}
  </nav>
  <ul class="player-list" data-kapsam="{kap['gecen']}/{kap['toplam']}">{rows}</ul>
  <nav class="endnav" aria-label="Devam"><span class="wrap endnav-inner">
    <a class="endnav-go" href="/">Bugünün brifingi →</a>
    <a class="endnav-go" href="/arsiv.html">Tüm raporlar</a>
  </span></nav>
</main>
"""
        + f'<script src="{asset("app.js")}" defer></script>\n'
        + FOOT
    )


KAPSAM_RE = re.compile(r'class="player-list" data-kapsam="(\d+)/(\d+)"')


def kapsam_report(kap, previous_page):
    """KAPSAM-SAYI'nın operatör yüzü: (A) özeti her derlemede, uyarı yalnız geçişte.

    Önceki hâl yayındaki /oyuncular.html'in data-kapsam'ından okunur — okuyucunun
    gördüğü şeyin kendisi. İşaret yoksa (ilk derleme) önceki hâl bilinmiyor
    sayılır ve hangi hâldeysek o bir kez bildirilir.
    """
    import os
    n, total = kap["gecen"], kap["toplam"]
    m = KAPSAM_RE.search(previous_page or "")
    prev_tam = (m.group(1) == m.group(2)) if m else None
    kalan_adlar = ", ".join(ad for ad, _w in kap["kalanlar"])
    boz = f" (KAPSAM_BOZ={','.join(kap['boz'])}, bilerek)" if kap["boz"] else ""

    line = f"alias testi {n}/{total}" + (f" — kalanlar: {kalan_adlar}" if kalan_adlar else "")
    print(f"  · KAPSAM-SAYI: {line}{boz} · oyuncu sayıları "
          f"{'basıldı' if kap['tam'] else 'basılmadı'}")
    for ad, why in kap["kalanlar"]:
        print(f"      {ad}: {'; '.join(why[:3])}")
    summary = os.environ.get("GITHUB_STEP_SUMMARY")
    if summary:
        md = ["### KAPSAM-SAYI — oyuncu sayıları (Rev 21)", "",
              f"**{'🟢' if kap['tam'] else '🔴'} {line}**{boz}", "",
              ("/oyuncular.html: “Bugün N · son 30 günde N”, “N gün”, yaş jetonları basıldı."
               if kap["tam"] else
               "/oyuncular.html: hiçbir sayı ya da yaş jetonu basılmadı; üst satır "
               f"yalnız “izlenen {total}”, sıra alfabetik.")]
        for ad, why in kap["kalanlar"]:
            md.append(f"- {ad}: {'; '.join(why[:3])}")
        try:
            with open(summary, "a", encoding="utf-8") as fh:
                fh.write("\n".join(md) + "\n\n")
        except OSError as exc:
            print(f"  ! KAPSAM-SAYI: özet yazılamadı: {exc}")

    from scripts import uyari
    if not kap["tam"] and prev_tam is not False:
        uyari.ekle("KAPSAM-SAYI", f"KAPSAM-SAYI: {n}/{total} — kalanlar: {kalan_adlar}{boz}"
                   " · oyuncu sayıları basılmadı")
    elif kap["tam"] and prev_tam is not True:
        uyari.ekle("KAPSAM-SAYI", f"KAPSAM-SAYI: {n}/{total} — sayılar döndü (64/64'e varış)"
                   .replace("64/64", f"{total}/{total}"))


def kategori_isabeti(news):
    """S8 + İPUCU-YOK (Rev 25): son medya takibi gününde kategori başına iki sayı.

    "yalnız ipucuyla gelen": adı olan bir kategoride, ama başlığı o kategorinin kendi
    kuralına (kelime listesi; Oyuncu Duyuruları için S4) değmiyor — oraya ancak kaynak
    ipucuyla gelmiş olabilir. "hiçbir kelimeye değmeyen": başlık hiçbir kategorinin hiçbir
    kelimesine değmiyor. Kurallar scripts/collect_news.py'den okunur (tek kaynak).
    (A) özetine tablo, kayda satır; ipucuyla gelen >0 ise İPUCU-YOK uyarısı (Rev 30).
    """
    import os
    from scripts import collect_news as CN
    days = sorted(d for d, data in news.items() if data.get("items"))
    if not days:
        return None
    day = days[-1]
    counts = CN.s8_counts(news[day]["items"])
    order = [n for n in NEWS_ORDER if n in counts] + sorted(set(counts) - set(NEWS_ORDER))
    ipucu = sum(r["ipucu"] or 0 for r in counts.values())
    kelimesiz = sum(r["kelimesiz"] for r in counts.values())
    print(f"  · İPUCU-YOK / S8 {day}: yalnız ipucuyla gelen {ipucu} · hiçbir kelimeye değmeyen "
          f"{kelimesiz} · " + " · ".join(
              f"{news_label(n)} {counts[n]['n']}: {'—' if counts[n]['ipucu'] is None else counts[n]['ipucu']}"
              f"/{counts[n]['kelimesiz']}" for n in order))
    summary = os.environ.get("GITHUB_STEP_SUMMARY")
    if summary:
        md = [f"### Kategori isabeti · {day} (Rev 25 S8 · İPUCU-YOK)", "",
              f"**{'🟢' if not ipucu else '🔴'} yalnız ipucuyla gelen: {ipucu}** · hiçbir kelimeye "
              f"değmeyen: {kelimesiz} · {sum(r['n'] for r in counts.values())} kalem", "",
              "| Kategori | Kalem | Yalnız ipucuyla gelen | Hiçbir kelimeye değmeyen |",
              "|---|--:|--:|--:|"]
        for n in order:
            r = counts[n]
            md.append(f"| {news_label(n)} | {r['n']} | {'—' if r['ipucu'] is None else r['ipucu']} "
                      f"| {r['kelimesiz']} |")
        md += ["", "“—”: Genel'in kendi kelime listesi yok; oraya ipucuyla gelinmez."]
        try:
            with open(summary, "a", encoding="utf-8") as fh:
                fh.write("\n".join(md) + "\n\n")
        except OSError as exc:
            print(f"  ! İPUCU-YOK: özet yazılamadı: {exc}")
    if ipucu:
        from scripts import uyari
        ornek = next(n for n in order if counts[n]["ipucu"])
        uyari.ekle("İPUCU-YOK", f"{day} · {ipucu} kalem adı olan bir kategoriye başlığındaki bir "
                   f"kelime olmadan gelmiş — ör. {news_label(ornek)}: {counts[ornek]['ipucu']}")
    return day, counts


def redirect_page(title, target, note):
    """Taşınan adres: yönlendirir, ama sessizce değil."""
    return (
        head(f"{title} — {SITE_NAME}")
        .replace("</head>", f'<meta http-equiv="refresh" content="0; url={target}">\n</head>')
        + masthead()
        + f"""<main class="wrap thread">
  <p class="kicker">Taşındı</p>
  <h1 class="report-title">{html.escape(title)}</h1>
  <p class="thread-meta">{note} Yönlendirilmiyorsanız:
    <a href="{target}">{target}</a></p>
</main>
"""
        + FOOT
    )


def thread_redirect(old, th):
    """Birleştirilen ipliğin eski adresi: yeni sayfaya götürür, sessizce değil.

    GitHub Pages 301 veremiyor, o yüzden yönlendirme sayfanın içinde. Kendi
    kendine gitmeden önce ne olduğunu da yazıyor: adresi paylaşmış birinin
    bağlantısının neden başka bir başlık açtığını bilmeye hakkı var.
    """
    target = f'/izleme/{th["slug"]}.html'
    return (
        head(f'{th["name"]} — izleme — {SITE_NAME}')
        .replace("</head>", f'<meta http-equiv="refresh" content="0; url={target}">\n</head>')
        + masthead()
        + f"""<main class="wrap thread">
  <p class="kicker">İzleme dosyası taşındı</p>
  <h1 class="report-title">{html.escape(th["name"])}</h1>
  <p class="thread-meta">Bu dosya aynı konunun diğer kayıtlarıyla birleştirildi.
    Yönlendirilmiyorsanız: <a href="{target}">{html.escape(th["name"])}</a></p>
  <nav class="endnav" aria-label="Devam"><span class="wrap endnav-inner">
    <a class="endnav-go" href="/izleme/index.html">Tüm izleme dosyaları</a>
  </span></nav>
</main>
"""
        + FOOT
    )


def thread_index(threads, latest):
    import datetime as _dt
    rank = {"open": 0, "dormant": 1, "closed": 2}

    def moves(t):
        return sum(1 for e in t["entries"] if not e.get("opening"))

    # Aynı gün kımıldamış onlarca iplik keyfî sırada duruyordu: eşitlik
    # bozulmayınca sıra, listenin bir şey söylemediği yer oluyor.
    def key(t):
        return (rank.get(t.get("state", "open"), 0),
                -_dt.date.fromisoformat(t["last"]).toordinal(),
                -moves(t), t["name"].lower())
    rows = []
    for th in sorted(threads.values(), key=key):
        gap = (_dt.date.fromisoformat(latest) - _dt.date.fromisoformat(th["last"])).days
        state = th.get("state", "open")
        # "bugün"ü 29 satıra basmak, listedeki her şeyin zaten öyle olduğu bir
        # hâli 29 kez duyurmaktır. Yaş jetonu ancak bugün değilse bir şey söyler.
        age = ("kapandı " + tr_date(th["closed"]) if state == "closed"
               else "son kayıt " + tr_date(th["last"]) if state == "dormant"
               else "" if gap == 0 else age_words(gap))
        # Boş jeton boş kalmıyor: flex aralığı yine de 14px yer tutuyor.
        rows.append(
            f'<li class="thread-row thread-row--{state}">'
            f'<a href="/izleme/{th["slug"]}.html"><span class="thread-name">{html.escape(th["name"])}</span>'
            + (f'<span class="thread-age num">{age}</span>' if age else "")
            + f'<span class="thread-count num">{moves(th)} hareket</span></a></li>'
        )
    counts = {k: sum(1 for t in threads.values() if t.get("state", "open") == k)
              for k in ("open", "dormant", "closed")}
    open_n = counts["open"]
    return (
        head(f"İzleme dosyaları — {SITE_NAME}")
        + masthead()
        + f"""<main class="wrap thread">
  <h1 class="report-title">İzleme dosyaları</h1>
  <p class="thread-meta"><span class="num">{counts["open"]}</span> açık ·
    <span class="num">{counts["dormant"]}</span> listede görünmüyor ·
    <span class="num">{counts["closed"]}</span> kapanmış</p>
  <ul class="thread-index">{''.join(rows)}</ul>
  <nav class="endnav" aria-label="Devam"><span class="wrap endnav-inner">
    <a class="endnav-go" href="/arsiv.html">Tüm raporlar</a>
  </span></nav>
</main>
"""
        + f'<script src="{asset("app.js")}" defer></script>\n'
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


# Rev 31: {gün: o günün brifinginin yayın anı}. main() medya sayfalarından önce doldurur;
# brifingi olmayan günde anahtar yok, jeton da yok.
BRIEF_AT = {}


def brief_moment(day, hhmm):
    """published.json'daki 'HH:MM' (Europe/Istanbul) → saat dilimli an; okunamazsa None."""
    import datetime as _dt
    from zoneinfo import ZoneInfo
    m = re.fullmatch(r"(\d{1,2}):(\d{2})", hhmm or "")
    if not m:
        return None
    return _dt.datetime.fromisoformat(day).replace(
        hour=int(m[1]), minute=int(m[2]), tzinfo=ZoneInfo("Europe/Istanbul"))


def brifingden_sonra(item, day):
    """Kalemin ilk_goruldu damgası o günün brifinginden sonra mı? Damgasız: hayır."""
    import datetime as _dt
    brief = BRIEF_AT.get(day)
    try:
        seen = _dt.datetime.fromisoformat(item.get("ilk_goruldu") or "")
    except ValueError:
        return False
    return bool(brief and seen.tzinfo and seen > brief)


def clip_html(item, day, cited, sec=""):
    """Özetli satır açılır bir öğe, özetsiz satır tek bağlantı.

    Özet, İngilizce makaleyi *açmamak* için var; o yüzden özetli satırın birincil
    eylemi "özeti oku" oluyor ve kaynak bağlantısı gövdeye iniyor — iki hedefi olan
    bir yüzey tek bağlantı olamaz. Duruş hâlinde iki anatomi neredeyse özdeş görünür;
    farkı chevronun varlığı söyler.
    """
    # Rev 33: yabancı kaynak adı lang="en" ile sarılı — .clip-meta büyük harf, sayfa lang="tr".
    meta = [src_name(item.get("source", ""))]
    if norm_url(item.get("url")) in cited:
        meta.append('<span class="clip-cited">Brifingde</span>')
    elif brifingden_sonra(item, day):
        # Rev 31: aynı yuva, renksiz — brifing bu kalemi hiç görmedi. BRİFİNGDE ile birbirini dışlar.
        meta.append('<span class="clip-late">Brifingden sonra</span>')
    if item.get("published") and item["published"] != day:
        meta.append(tr_date(item["published"]))
    if item.get("also"):
        meta.append(f'+{len(item["also"])}')
    # Çapraz kategoride listelenen satır neden orada olduğunu kendi üstünde
    # söylüyor; okuyucu başlığa bakıp şirketi aramak zorunda kalmıyor.
    for tag in item.get("tr_tags") or []:
        meta.append(f'<span class="clip-tr">{html.escape(tag)}</span>')
    # Kapsam içindeyken özet gelmemişse söylenir; kapsam dışındaki 400+ satıra
    # konmaz, olmayan bir arızayı duyurmak olurdu. Bu sitede yokluk gizlenmez.
    if item.get("summary_scope") is True and not item.get("summary_tr"):
        meta.append('<span class="clip-nosum">özet alınamadı</span>')

    ids = item.get("oyuncu_ids") or []
    oyuncu = f' data-oyuncu="{" ".join(ids)}"' if ids else ""
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
            f'<li class="clip" data-sec="{sec}"{oyuncu} data-search="{haystack}">'
            f'<a href="{url}" target="_blank" rel="noopener">{row}</a></li>'
        )

    # İngilizce başlık bir doğrulama öğesi, tarama öğesi değil: gövdede duruyor.
    orig = (
        f'<p class="clip-orig">{html.escape(item["title"])}</p>'
        if item.get("title_tr") else ""
    )
    return (
        f'<li data-sec="{sec}"{oyuncu}><details class="clip" data-search="{haystack}">'
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


def clip_list(rows, day, cited, sec=""):
    return (
        '<ul class="clips">'
        + "".join(clip_html(r[2], day, cited, sec) for r in rows)
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
    sec = cat_id(name)
    if not rest:
        return head_html + clip_list(shown, day, cited, sec)
    return (
        head_html
        + clip_list(shown, day, cited, sec)
        + f'<details class="more"><summary>+{len(rest)} daha</summary>'
        + clip_list(rest, day, cited, sec)
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
        if (row[2].get("tier") != "A" or seen.get(source, 0) >= 3
                or row[2].get("savunma_terimi") is False):   # R25-P0-1: tam dökümde kalır
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
        + clip_list(worth, day, cited, cat_id(GENERAL))
        + f'<details class="more"><summary>Tam döküm ({len(rest)})</summary>'
        + clip_list(rest, day, cited, cat_id(GENERAL))
        + "</details></details>"
    )


def source_rows(data):
    """[(ad, başlık sayısı, yanıt verdi mi)] — o günün kaynak dökümü.

    Adlar iki yerden geliyor: başlık üreten kaynaklar kupürlerin kendisinden,
    yanıt vermeyenler `failures` listesinden. Yanıt verip hiçbir şey
    getirmeyen kaynakların adı veride yok — kaynaklar.json Drive'da duruyor
    ve toplayıcı roster'ı çıktıya yazmıyordu; collect_news artık yazıyor,
    yani eski günler eksik kalır, yeni günler tam olur. Eksik olduğunda
    sayfa sessizce yanlış olmasın diye fark build kaydında basılıyor.
    """
    items = data.get("items") or []
    if not items and not data.get("failures"):
        return []
    counts = {}
    for item in items:
        name = item.get("source") or "—"
        counts[name] = counts.get(name, 0) + 1
    failed = [f.get("source") for f in (data.get("failures") or []) if f.get("source")]
    roster = data.get("sources") or []
    quiet = [n for n in roster if n not in counts and n not in failed]
    rows = [(n, c, True) for n, c in sorted(counts.items(), key=lambda kv: (-kv[1], kv[0]))]
    rows += [(n, 0, True) for n in sorted(quiet)]
    rows += [(n, 0, False) for n in sorted(failed)]
    return rows


def sources_page(day, data, has_report):
    """/haberler/{gün}-kaynaklar.html — kapsamın kendisi."""
    rows = source_rows(data)
    if not rows:
        return ""
    # R28-P0-1: bir izlenen oyuncunun kendi kaynağıysa satırın yanında oyuncunun adı.
    # R28-P1-1: "yanıt vermedi" sütunu kalktı — satır soluk kalır (Rev 19), sebep build
    # kaydında; okuyucuya giden tek arıza brifingdeki KANIT-BOŞLUĞU satırı.
    oyuncu = oyuncu_kaynaklari()
    body = "".join(
        f'<li class="srow{"" if ok else " srow--off"}">'
        f'<span class="sname">{src_name(name)}</span>'
        + (f'<span class="scount soyuncu">oyuncu: {html.escape(oyuncu[name][0])}</span>' if name in oyuncu else "")
        + (f'<span class="scount num">{n}</span>' if ok and n
           else '<span class="scount num">—</span>' if ok
           else "")
        + "</li>"
        for name, n, ok in rows
    )
    read = data.get("scanned_sources", 0) - data.get("failed_sources", 0)
    return (
        head(f"Kaynaklar · {tr_date(day)} — {SITE_NAME}")
        + masthead()
        + daybar("news", day, None, None, day if has_report else None)
        + f"""<main class="wrap thread">
  <p class="kicker">Kapsam</p>
  <h1 class="report-title">Kaynaklar · {tr_date(day)}</h1>
  <p class="thread-meta num"><strong>{read}</strong> kaynak okundu</p>
  <ul class="slist">{body}</ul>
  <nav class="endnav" aria-label="Devam"><span class="wrap endnav-inner">
    <a class="endnav-go" href="{day_url("news", day)}">{tr_date(day)} medya takibi →</a>
    <a class="endnav-go" href="/arsiv.html">Tüm raporlar</a>
  </span></nav>
</main>
"""
        + FOOT
    )


TURK_CAT = "Türk savunma sanayii"
TURK_ID = "kat-turk"


def turkish_section(rows, day, cited):
    """Çapraz kategori: Türk sanayiine dair başlıklar, kendi kategorilerinde de kalır.

    Öne çıkanlar gibi: satır iki yerde birden durabilir. Bu kesit bir konu
    değil bir mercek — "bugün Türk sanayiinden ne çıktı" sorusu, kategorilerin
    hiçbirinin tek başına cevaplayamadığı bir soru.
    """
    return (
        f'<h2 class="kicker" id="{TURK_ID}">{html.escape(TURK_CAT)}'
        f' <span class="kicker-count num">{len(rows)}</span></h2>'
        + clip_list(rows, day, cited, TURK_ID)
    )


def build_news_page(day, data, prev_day, next_day, has_report, cited):
    items = data.get("items", [])
    # Etiketleme düzenden önce: clip_html satırın etiketini okuyor.
    tag_player_headlines(items)
    top, present = news_layout(items, day, cited)
    ranked_all = [r for _n, rows in present for r in rows]
    turk_rows = sorted((r for r in ranked_all if r[2].get("tr_tags")),
                       key=lambda r: (-r[0], r[1]))

    body = [
        '<section class="highlights" id="one-cikanlar">'
        '<h2 class="kicker">Öne çıkanlar'
        f' <span class="kicker-count num">{len(top)}</span></h2>'
        # Öne çıkanlar da kapalı başlar. Sayfa bir tarama yüzeyi: önce 12 başlık
        # görünür, özet isteyen açar. Açık başlayan blok ekranın ilk görüntüsünü
        # üç satıra düşürüyordu.
        + clip_list(top, day, cited, "one-cikanlar")
        + "</section>"
    ]
    for name, rows in present:
        body.append(general_section(rows, day, cited) if name == GENERAL
                    else news_section(name, rows, day, cited))
        if name == "MKE" and turk_rows:
            body.append(turkish_section(turk_rows, day, cited))
    if turk_rows and not any(n == "MKE" for n, _r in present):
        body.insert(1, turkish_section(turk_rows, day, cited))

    # aynı liste iki biçimde: dar ekranda yapışkan çip şeridi, geniş ekranda rail
    jumps = [("one-cikanlar", "Öne çıkanlar", len(top))]
    for name, rows in present:
        jumps.append((cat_id(name), news_label(name), len(rows)))
        if name == "MKE" and turk_rows:
            jumps.append((TURK_ID, TURK_CAT, len(turk_rows)))
    if turk_rows and not any(n == "MKE" for n, _r in present):
        jumps.insert(1, (TURK_ID, TURK_CAT, len(turk_rows)))
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

    # Kapsam satırı: ne taradık, ne kadar geriye baktık. Üç parça, üçü de
    # okuyucunun sorusuna cevap veriyor. Bir süre altı parçaydı ve üçü
    # üreticinin iç durumuydu — "80/89 özet", "16 kaynak yanıt vermedi",
    # "başlıklar Türkçe çeviriyle açılır". İlk ikisi hattın sağlığı, okuyucu
    # onlarla hiçbir şey yapamaz; üçüncüsü zaten dokununca görülen bir şeyi
    # önceden duyuruyordu. İkisi de build kaydında duruyor, sayfada değil.
    defined = data.get("scanned_sources", 0)
    unread = data.get("failed_sources", 0)
    read = defined - unread
    count = f'<span class="num">{data.get("unique_items", 0)}</span> başlık'
    # Kaynak sayısı bir kapı: hangi kaynaklar olduğunu görmek isteyen görsün.
    src = f'<span class="num">{read}</span> kaynak'
    if source_rows(data):
        src = f'<a href="{day_url("news", day)[:-5]}-kaynaklar.html">{src}</a>'
    stat = f'{count} · {src} · son <span class="num">{data.get("window_hours", 48)}</span> saat'

    return (
        head(f"Medya takibi · {tr_date(day)} — {SITE_NAME}")
        + masthead()
        + daybar("news", day, prev_day, next_day, day if has_report else None)
        + f"""<main class="wrap news">
  <div class="news-head">
    <h1 class="report-title">Medya takibi · {tr_date(day)}</h1>
    <p class="news-stat">{stat}</p>
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
        + endnav("news", day, prev_day, day if has_report else None)
        + PROMPTS
        + f'<script src="{asset("app.js")}" defer></script>\n'
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
   data-day="{r.get('date', '')}"
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
    # Rev 28 (deneme 2): bos_kesisim kanıtı — yalnız bu derlemenin belleğinde, veri dosyasına dokunmaz.
    bos_kesisim_duzenle(news, sorted(p.stem for p in SRC.glob("????-??-??.md")))
    news_days = sorted(news)
    kaynak_ulkeleri(news)   # Rev 33: src_name() kaynağın ülkesini buradan bilir
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
    # Rev 32: özet maddesi / H1 önceki 7 raporun bir gelişmesiyle eşleşiyor mu.
    tekrar = tekrar_eslesmeleri(sources)

    reports = []
    for i, (iso, meta, body) in enumerate(sources):
        developments = meta.get("developments") or []
        body_html = render_body(body, developments, bool(meta.get("alarm")), iso,
                                day_slugs.get(iso))
        body_html = ilk_jetonlari(body_html, tekrar[iso]["ozet"])   # Rev 32: "ilk: GG Aaa"
        page = build_report(
            meta, body_html, iso,
            sources[i - 1][0] if i else None,
            sources[i + 1][0] if i + 1 < len(sources) else None,
            news_counts,
            mke_counts.get(iso, 0),
            published.get(iso, ""),
            scan_counts.get(iso),
            rival_hits(body, developments),
            turkish_line(body, news.get(iso, {}).get("items", [])),
            iso in news,
            bosluk=[k for k, *_ in kanit_boslugu(news.get(iso))],
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
        print(f"  · reports/{iso}.html"
              + "".join(f" · özet {n} ilk: {tr_daybar(t['gun']).split(' · ')[0]} {t['gid'].upper()}"
                        for n, t in sorted(tekrar[iso]["ozet"].items())))
        kb = kanit_boslugu(news.get(iso))
        if kb:
            print(f"      KANIT-BOŞLUĞU: {kanit_cumlesi([k for k, *_ in kb])}")

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
        for day in news_days:
            at = brief_moment(day, published.get(day)) if day in report_days else None
            if at:
                BRIEF_AT[day] = at
        late_rows = {}
        for i, day in enumerate(news_days):
            cited = cited_urls(day)
            late_rows[day] = sum(1 for it in news[day].get("items", [])
                                 if norm_url(it.get("url")) not in cited and brifingden_sonra(it, day))
            page = build_news_page(
                day, news[day],
                news_days[i - 1] if i else None,
                news_days[i + 1] if i + 1 < len(news_days) else None,
                day in report_days, cited,
            )
            (NEWS_OUT / f"{day}.html").write_text(page, encoding="utf-8")
            src_page = sources_page(day, news[day], day in report_days)
            if src_page:
                (NEWS_OUT / f"{day}-kaynaklar.html").write_text(src_page, encoding="utf-8")
                # Kaynak listesi eksikse sessizce yanlış olmasın: roster
                # Drive'da, toplayıcı yazmadığı günlerde adsız kalanlar var.
                named = len(source_rows(news[day]))
                scanned = news[day].get("scanned_sources", 0)
                if named < scanned:
                    print(f"  ! {day}: kaynak sayfasında {named}/{scanned} ad "
                          f"({scanned - named} kaynak yanıt verdi ama başlık getirmedi, adı veride yok)")
            hits = sum(1 for it in news[day].get("items", []) if norm_url(it.get("url")) in cited)
            scope = [it for it in news[day].get("items", []) if it.get("summary_scope") is True]
            covered = sum(1 for it in scope if it.get("summary_tr"))
            if scope or news[day].get("failed_sources"):
                # Sayfadan kalkan iki sayı buraya taşındı: hattın sağlığı
                # okuyucunun belgesinde değil, hattın kendi kaydında durur.
                print(f"      özet {covered}/{len(scope)} · "
                      f"{news[day].get('failed_sources', 0)} kaynak yanıt vermedi")
            print(
                f'  · haberler/{day}.html ({news[day].get("unique_items", 0)} başlık'
                f" · {hits} brifing atıflı"
                + (f" · {late_rows[day]} brifingden sonra" if late_rows[day] else "") + ")"
            )
        gec_gelen_ozeti(news_days[-2:], late_rows)

    (ROOT / "arsiv.html").write_text(
        build_index(reports, version, news_counts), encoding="utf-8"
    )
    # Kök = bugünün brifingi. Kurulu uygulamayı açan okuyucu bir dizinle değil
    # o günün raporuyla karşılaşır; arşiv bir tık ötede durur.
    if sources:
        iso, meta, body = sources[-1]
        body_html = render_body(body, meta.get("developments") or [],
                                bool(meta.get("alarm")), iso,
                                day_slugs.get(iso))
        # Rev 23: ETİKET-BAŞLIK · KUR · H1-TEKRAR — yalnız günün raporu, uyarı verir, durdurmaz.
        r23_kurallari(iso, meta, body, body_html, news)
        # Rev 32: TEKRAR-MANŞET — H1 eşleşirse uyarı; özet maddelerine "ilk:" jetonu.
        tekrar_manset_kurali(iso, tekrar[iso])
        # Rev 28: KANIT-BOŞLUĞU — izlenen oyuncunun kendi kaynağı okunamadıysa uyarı.
        bosluk = kanit_boslugu_kurali(iso, news.get(iso))
        body_html = ilk_jetonlari(body_html, tekrar[iso]["ozet"])
        (ROOT / "index.html").write_text(
            build_report(meta, body_html, iso,
                         sources[-2][0] if len(sources) > 1 else None, None,
                         news_counts, mke_counts.get(iso, 0),
                         published.get(iso, ""), scan_counts.get(iso),
                         rival_hits(body, meta.get("developments") or []),
                         turkish_line(body, news.get(iso, {}).get("items", [])),
                         iso in news, depth=0, bosluk=bosluk),
            encoding="utf-8")
    # Oyuncular: rayın "bugün kim" sorusunun yanındaki "ne zamandan beri" sayfası.
    kategori_isabeti(news)   # Rev 25: S8 + İPUCU-YOK
    hist = player_history(sources, news)
    if hist:
        # KAPSAM-SAYI: testler her derlemede koşar; sayfa her durumda üretilir.
        kap = kapsam()
        players_file = ROOT / "oyuncular.html"
        previous = players_file.read_text(encoding="utf-8") if players_file.exists() else ""
        PLAYERS_JSON.write_text(
            json.dumps(players_json(hist, kap["tam"]), ensure_ascii=False, indent=1) + "\n",
            encoding="utf-8")
        players_file.write_text(players_page(hist, kap), encoding="utf-8")
        kapsam_report(kap, previous)
        # Eski adres ölü kalmasın: rayda haftalardır bu bağlantı duruyordu.
        (ROOT / "rakipler.html").write_text(
            redirect_page("Oyuncular", "/oyuncular.html",
                          "Bu sayfa /oyuncular.html adresine taşındı: liste artık "
                          "yalnız adları değil, hangi segmentte ve en son ne zaman "
                          "adı geçtiğini de taşıyor."),
            encoding="utf-8")
        print(f"  · oyuncular.html ({len(hist)} ad) · rakipler.html → yönlendirme")

    # İzleme dosyaları: bir ipliğin geçmişi başka hiçbir yerde durmuyor.
    if threads and sources:
        THREAD_OUT.mkdir(exist_ok=True)
        latest = sources[-1][0]
        for th in threads.values():
            (THREAD_OUT / f'{th["slug"]}.html').write_text(
                thread_page(th, latest, [iso for iso, _m, _b in sources], news_counts),
                encoding="utf-8")
        (THREAD_OUT / "index.html").write_text(
            thread_index(threads, latest), encoding="utf-8")
        # Birleştirilen ipliklerin eski adresleri ölü kalmasın: geçen haftadan
        # açık duran bir sekme, "hiçbir yerden bağlantı verilmiyor"un dışında
        # kalan yer. Yönlendirme sayfası da bir cevaptır.
        stubs = 0
        for old, new in thread_aliases().items():
            if old in threads or new not in threads:
                continue
            (THREAD_OUT / f"{old}.html").write_text(
                thread_redirect(old, threads[new]), encoding="utf-8")
            stubs += 1
        # Ajanın okuyacağı açık iplik listesi. Yapıştırılan metin ikinci gün
        # bayatlar; dosya her kurulumda tazelenir.
        THREADS_JSON.write_text(json.dumps(
            [{"id": t["slug"], "name": t["name"], "son_hareket": t["last"]}
             for t in sorted(threads.values(), key=lambda x: x["last"], reverse=True)
             if t.get("state", "open") != "closed"],
            ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
        st = {k: sum(1 for t in threads.values() if t.get("state", "open") == k)
              for k in ("open", "dormant", "closed")}
        print(f"  · izleme/ ({len(threads)} dosya + {stubs} yönlendirme · "
              f"{st['open']} açık · "
              f"{st['dormant']} uykuda · {st['closed']} kapalı)")
        # Rev 27: İPLİK-DURUM — son hareketin durum cümlesi sayfaya ulaştı mı.
        iplik_durum_kurali(threads)

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
    # Rev 33: NOKTALI-İ — derlenmiş HTML'in büyük harfli alanlarında sarmasız yabancı ad.
    noktali_i_kurali()
    # Rev 29: L1-DOLGU · ÇİZGİ-KONTRAST — app.css'in kendisi denetlenir.
    r29_kurallari()
    if check_links():
        sys.exit(1)


def check_links():
    """Üretilen her bağlantı gerçekten var mı? Yoksa yayın durur.

    Kırık bir bağlantı sayfanın geri kalanı çalıştığı için fark edilmiyor:
    kök sayfanın "önceki gün" oku haftalarca 404 verdi ve build her gün
    "tamam" dedi. Bir şeyi üretiyorsak doğrulayabiliriz de; doğrulamayan
    build, ürettiğini bilmiyor demektir.
    """
    import posixpath
    broken = []

    def anchors(text):
        """{id: gizli mi} — çapayı taşıyan etiketin kendisi hidden mı?

        "Çapa var" ile "çapaya gidilebilir" ayrı şeyler: hidden bir öğenin
        kutusu yok ve scrollIntoView sessizce hiçbir şey yapmıyor. Kaynaklar
        çipi tam bu yüzden haftalarca ölüydü ve denetim temiz rapor veriyordu,
        çünkü yalnız kimliğin varlığına bakıyordu.
        """
        found = {}
        for m in re.finditer(r"<(\w+)\b([^>]*)>", text):
            mid = re.search(r'\bid="([^"]+)"', m.group(2))
            if not mid:
                continue
            bare = re.sub(r'="[^"]*"', "=", m.group(2))   # değerleri at
            found[mid.group(1)] = bool(re.search(r"(?<![\w-])hidden(?![\w-])", bare))
        return found
    for f in sorted(ROOT.rglob("*.html")):
        if ".git" in f.parts:
            continue
        text = f.read_text(encoding="utf-8", errors="replace")
        page_anchors = anchors(text)
        page_ids = set(page_anchors)
        for href in re.findall(r'(?:href|src)="([^"]+)"', text):
            if href.startswith(("http://", "https://", "mailto:", "data:", "//")):
                continue
            path, _, frag = href.partition("#")
            path = path.split("?")[0]
            if not path:
                if frag and frag not in page_ids:
                    broken.append((f, href, "çapa yok"))
                elif frag and page_anchors.get(frag):
                    broken.append((f, href, "çapa gizli"))
                continue
            target = (ROOT / path.lstrip("/")) if path.startswith("/") else (
                ROOT / posixpath.normpath(posixpath.join(f.parent.relative_to(ROOT).as_posix(), path)))
            if target.is_dir():
                target = target / "index.html"
            if not target.exists():
                broken.append((f, href, "dosya yok"))
            elif frag and target.suffix == ".html":
                found = anchors(target.read_text(encoding="utf-8", errors="replace"))
                if frag not in found:
                    broken.append((f, href, "çapa yok"))
                elif found[frag]:
                    broken.append((f, href, "çapa gizli"))
    if broken:
        print(f"  ✗ {len(broken)} kırık bağlantı:")
        for f, href, why in broken[:15]:
            print(f"      {f.relative_to(ROOT)} → {href}  ({why})")
        if len(broken) > 15:
            print(f"      … ve {len(broken) - 15} tane daha")
    # Olmayan dosya build'in hatasıdır: her gün aynı şekilde çıkar, yayını
    # durdurmak onu sabah fark ettirir. Olmayan ya da gizli çapa ajanın
    # metninden de gelebilir; onun için günün raporunu hiç yayımlamamak,
    # kırık bir iç bağlantıdan daha büyük zarar — yüksek sesle söylenir,
    # durdurmaz. (app.js gizli çapada görünen ataya çıkıyor, yani bu bir
    # uyarı; JavaScript'siz tarayıcıda gerçek bir kırık.)
    return sum(1 for _f, _h, why in broken if why == "dosya yok")

# Oyuncu eşleştiricisi oyuncu_eslestir.py'de (Rev 25: toplama da kullanıyor).
from oyuncu_eslestir import (  # noqa: E402,F401
    RIVALS_JSON, SHORT_NAME, _haric, _word, headline_has, rival_in_body, rival_in_title,
    rival_patterns, rivals_config, tr_fold,
)


# ── KAPSAM-SAYI (Rev 21) ─────────────────────────────────────────────────────
# Oyunculardan türeyen her sayı ve jeton ancak 64 oyuncunun hepsi alias_test'i
# geçtiyse basılır. Tek oyuncu kalırsa hiçbiri. Oyuncu oyuncu açılma yok:
# bir tarafı sayılı, öbür tarafı sayısız bir tablo okuyucuya iki sözleşme sunar.

KAPSAM_BOZ_POS = "KAPSAM_BOZ: bu başlıkta izlenen hiçbir oyuncu yok"


def kapsam_boz():
    """KAPSAM_BOZ=<id>[,<id>…] — kanıt için bilerek bozulan oyuncular (yerel ya da CI)."""
    import os
    raw = (os.environ.get("KAPSAM_BOZ") or "").strip()
    if raw in ("", "none"):
        return ()
    ids = tuple(x.strip() for x in raw.split(",") if x.strip())
    known = {r["id"] for r in rivals_config()}
    unknown = [x for x in ids if x not in known]
    if unknown:
        sys.exit(f"KAPSAM_BOZ: bilinmeyen oyuncu {', '.join(unknown)} (data/rakipler.json id'leri)")
    return ids


def alias_test(rival, boz=False):
    """Bir oyuncunun alias_test'i: [] = geçti, yoksa sebepler."""
    why = []
    if not isinstance(rival.get("aliases"), list):
        why.append("aliases[] yok")
    t = rival.get("alias_test")
    if not isinstance(t, dict):
        return why + ["alias_test yok"]
    pos, pos_tr = list(t.get("pos") or []), list(t.get("pos_tr") or [])
    neg, neg_tr = list(t.get("neg") or []), list(t.get("neg_tr") or [])
    if boz:
        # Test yolu aynı: eşleşmeyecek bir pozitif eklenir ve test gerçekten kalır.
        pos.append(KAPSAM_BOZ_POS)
    if not pos and not pos_tr:
        why.append("pozitif örnek yok")
    rid = rival["id"]
    for text, tr in [(x, False) for x in pos] + [(x, True) for x in pos_tr]:
        if not rival_in_title(rid, text, tr=tr):
            why.append(f"eşleşmedi: “{text[:60]}”")
    for text, tr in [(x, False) for x in neg] + [(x, True) for x in neg_tr]:
        if rival_in_title(rid, text, tr=tr):
            why.append(f"yanlış eşleşti: “{text[:60]}”")
    negs = [tr_fold(x) for x in neg + neg_tr]
    for s in [rival["name"]] + list(rival.get("aliases") or []):
        if len(s) <= SHORT_NAME and not any(tr_fold(s) in x for x in negs):
            why.append(f"“{s}” kısa, onu içeren negatif örnek yok")
    return why


def kapsam():
    """{"gecen", "toplam", "kalanlar": [(ad, [sebep])], "tam", "boz"} — her derlemede."""
    config = rivals_config()
    boz = kapsam_boz()
    kalan = []
    for r in config:
        why = alias_test(r, boz=r["id"] in boz)
        if why:
            kalan.append((r["name"], why))
    n = len(config)
    return {"gecen": n - len(kalan), "toplam": n, "kalanlar": kalan,
            "tam": n > 0 and not kalan, "boz": boz}


def development_blocks(body):
    """[(sıra, çapa, başlık, gövde)] — raporun anlatı birimleri."""
    blocks = []
    # Sınır önemli: sonraki ## gelmezse son gelişmenin gövdesi dosyanın
    # sonuna kadar uzuyor ve alakasız metni de yutuyor.
    for m in re.finditer(r"^###\s*(G\d+)\s*·\s*([^\n]*)\n(.*?)(?=^#{2,3}\s|\Z)",
                         body, flags=re.S | re.M):
        blocks.append((int(m.group(1)[1:]), m.group(1).lower(), m.group(2), m.group(3)))
    # Rakip hareketleri maddeleri de birer gelişme (Rev 16).
    for m in re.finditer(r"^-\s*\*\*\s*(G\d+)\s*·\s*([^*]+?)\s*\*\*\s*—\s*([^\n]*)",
                         body, flags=re.M):
        blocks.append((int(m.group(1)[1:]), m.group(1).lower(), m.group(2), m.group(3)))
    blocks.sort()
    return blocks


def rival_hits(body, developments=()):
    """[(ad, çapa|"", rol)] — hangi rakip bugün hangi gelişmede geçiyor.

    Önce gelişme başlıklarında, sonra gövdelerinde aranıyor: başlıkta geçen
    ad o gelişmenin konusu, gövdede geçen ad ise anılan taraf. Aynı rakip
    birden çok gelişmede geçiyorsa g kimliği en küçük olanına bağlanır.

    Roller burada ayrılmıyor, yalnız taşınıyor: hangi rolün nereye çıktığı
    render kararı. Böylece "Türk emsallerini de rakip sayalım" dendiği gün
    eşleşme geçmişi kayıpsız duruyor.
    """
    blocks = development_blocks(body)
    out = []
    for rival in rivals_config():
        anchor = ""
        for b in blocks:
            if rival_in_title(rival["id"], b[2], tr=True):
                anchor = f"#{b[1]}"
                break
        if not anchor:
            for b in blocks:
                if rival_in_body(rival["id"], b[3]):
                    anchor = f"#{b[1]}"
                    break
        out.append((rival["name"], anchor, rival.get("role", "rakip")))
    return out


PLAYERS_JSON = DATA / "oyuncular.json"
WINDOW_DAYS = 30


def segment_labels():
    try:
        return json.loads(RIVALS_JSON.read_text(encoding="utf-8")).get("_segment_labels", {})
    except Exception:
        return {}


def player_history(sources, news):
    """id -> {ad, rol, segmentler, gunler[], son, gun_30g} — iki geçişin birleşik kaydı.

    Yeni eşleştirme yok: aynı iki geçiş, bu kez gün gün toplanıyor. Rayda
    "bugün kimin adı geçti" sorusunun cevabı var; burada "ne zamandan beri,
    kaç gün" sorusununki. İkinci geçiş Rev 21'den beri bütün rolleri
    kapsıyor: eskiden yalnız Türk adlarını arıyordu ve Thales'in satırı, o
    gün dört başlıkta geçmişken "bu ay hiç geçmedi" diyordu.

    `gun_30g` gün sayar, geçiş değil (eski adı sayi_30g; sayfada "N gün").
    """
    import datetime as _dt
    config = rivals_config()
    if not config or not sources:
        return {}
    by_name = {r["name"]: r for r in config}
    hist = {r["id"]: {"ad": r["name"], "rol": r.get("role", "rakip"),
                      "segmentler": r.get("segments") or [],
                      "gunler": []} for r in config}

    def record(name, iso, url, strong):
        rival = by_name.get(name)
        if not rival:
            return
        days = hist[rival["id"]]["gunler"]
        for d in days:
            if d["g"] == iso:
                if strong:          # gelişme çapası kupür adresinin önüne geçer
                    d["u"] = url
                return
        days.append({"g": iso, "u": url})

    for iso, _meta, body in sources:
        items = news.get(iso, {}).get("items", [])
        for name, anchor, _role in rival_hits(body):
            if anchor:
                record(name, iso, f"/reports/{iso}.html{anchor}", True)
        for name in tag_player_headlines(items):
            record(name, iso, f"/haberler/{iso}.html?oyuncu={by_name[name]['id']}", False)

    latest = _dt.date.fromisoformat(sources[-1][0])
    for entry in hist.values():
        entry["gunler"].sort(key=lambda d: d["g"], reverse=True)
        entry["son"] = entry["gunler"][0]["g"] if entry["gunler"] else ""
        entry["gun_30g"] = sum(
            1 for d in entry["gunler"]
            if (latest - _dt.date.fromisoformat(d["g"])).days < WINDOW_DAYS)
    return hist


def players_json(hist, tam):
    """data/oyuncular.json — (D) yüzeyi. KAPSAM-SAYI kalırsa türetilmiş sayı ve
    jeton (son, gun_30g) yazılmaz; gün listesi kalır, arşivin ?oyuncu= süzgeci onu okuyor."""
    if tam:
        return hist
    return {k: {f: v for f, v in e.items() if f not in ("son", "gun_30g")}
            for k, e in hist.items()}


TURKISH_ROLES = ("yerli-rakip", "emsal")


def tag_player_headlines(items):
    """Günün başlıklarını izlenen bütün oyuncularla etiketle; eşleşen adları döndür.

    Başlık taraması brifingden ayrı bir kanal: rapor yalnız o günün dokuz
    gelişmesini anlatıyor, medya takibinde 400+ satır var. Rev 17'de bu
    geçiş yalnız Türk rollerini arıyordu; Rev 21'de 64 oyuncunun hepsine
    genişledi — sayı ancak her oyuncuya bakıldıysa doğru olabilir.

    Satır iki etiket taşıyor, iki ayrı iş için:
    - `oyuncu_ids` (bütün roller) → `data-oyuncu`, ?oyuncu= süzgeci onu okur.
      Kimlik ayrı tutuluyor — süzme ada değil kimliğe bakmalı, yoksa
      "Bayraktar" başlığı Baykar süzgecinden kaçar.
    - `tr_tags` (yalnız Türk rolleri) → "Türk savunma sanayii" kesiti ve
      satırdaki şirket etiketi. Rol render'a ait (Rev 17): yabancı bir oyuncu
      Türk sanayii kesitine düşmez.
    """
    hit_names = []
    for rival in rivals_config():
        turkish = rival.get("role") in TURKISH_ROLES
        found = False
        for item in items:
            if not headline_has(rival["id"], item):
                continue
            ids = item.setdefault("oyuncu_ids", [])
            if rival["id"] not in ids:
                ids.append(rival["id"])
            if turkish:
                tags = item.setdefault("tr_tags", [])
                if rival["name"] not in tags:
                    tags.append(rival["name"])
            found = True
        if found:
            hit_names.append(rival["name"])
    return hit_names


def tag_turkish_headlines(items):
    """Türk sanayii satırı için: bugün başlıkta geçen Türk rollü adlar."""
    turkish = {r["name"] for r in rivals_config() if r.get("role") in TURKISH_ROLES}
    return [n for n in tag_player_headlines(items) if n in turkish]


def turkish_line(body, items):
    """[(ad, kimlik, vurdu mu)] — Türk sanayii satırı, iki geçiş birleşik.

    Gelişmelerde geçen ad da, günün başlıklarında geçen ad da aynı satıra
    çıkıyor: okuyucu için ikisi de "bugün adı geçti" demek.
    """
    config = [r for r in rivals_config() if r.get("role") in TURKISH_ROLES]
    if not config:
        return []
    from_dev = {name for name, anchor, role in rival_hits(body)
                if anchor and role in TURKISH_ROLES}
    from_news = set(tag_turkish_headlines(items))
    return [(r["name"], r["id"], r["name"] in from_dev or r["name"] in from_news)
            for r in config]



# ---------- Rev 23: bir olgu, bir ad, bir değer ----------
#
# Üç kural da yalnız günün raporunda (en yeni kaynak) uyarı verir: her derleme
# bütün arşivi yeniden kurar ve eski günlerin aynı uyarısı her sabah issue'ya
# düşseydi kanal %100 ateşleyen, sıfır bilgili bir kanal olurdu. Uyarı Rev 30
# kanalına gider, derlemeyi durdurmaz: rapor insan incelemesi olmadan yayımlanıyor
# ve durdurmak, yöneticiye o sabah hiç rapor gitmemesi demek.

def _duz(fragment):
    """HTML parçası → görünen düz metin (kopyala düğmesi hariç)."""
    fragment = re.sub(r"<button\b.*?</button>", "", fragment, flags=re.S)
    return " ".join(html.unescape(re.sub(r"<[^>]+>", "", fragment)).split())


def etiket_baslik(body_html, developments):
    """ETİKET-BAŞLIK: her gelişme başlığı kendi label'ı; her '→ bugün:' bağlantısı
    indiği başlığın metni. Döner: [uyarı metni]."""
    labels = {str(d.get("id", "")).lower(): " ".join(str(d.get("label", "")).split())
              for d in developments if d.get("id")}
    out = []
    heads = {m.group(1): _duz(m.group(2)) for m in
             re.finditer(r'<h3 id="(g\d+)"[^>]*>(.*?)</h3>', body_html, re.S)}
    for gid, text in heads.items():
        label = labels.get(gid)
        if not label:
            out.append(f"{gid.upper()} başlığı “{text}” — frontmatter'da label yok")
        elif text != label:
            out.append(f"{gid.upper()} başlığı “{text}” ≠ label “{label}”")
    # İnilen yer h3 ya da izleme kaleminin kalın adı (li#gN > strong.ganchor).
    landing = dict(heads)
    for m in re.finditer(r'<li id="(g\d+)"[^>]*><strong class="ganchor">(.*?)</strong>',
                         body_html, re.S):
        landing.setdefault(m.group(1), _duz(m.group(2)))
    for m in re.finditer(r'<li class="watch-move">.*?<span class="watch-arrow"> → bugün: </span>'
                         r'<a class="xref" href="#(g\d+)"[^>]*>(.*?)</a>', body_html, re.S):
        gid, text = m.group(1), _duz(m.group(2))
        if gid in landing and landing[gid] != text:
            out.append(f"→ bugün: “{text}” ≠ indiği başlık “{landing[gid]}” ({gid.upper()})")
    return out


# Para birimi: yazım biçimleri → tek kod. Build ağa çıkmaz; kur çevirmez, yalnız
# ajanın yazdığı değerin kaynağın medya özetinde geçip geçmediğine bakar.
_PARA = {
    "$": "USD", "dolar": "USD", "usd": "USD", "abd doları": "USD",
    "€": "EUR", "avro": "EUR", "euro": "EUR", "eur": "EUR",
    "£": "GBP", "sterlin": "GBP", "gbp": "GBP",
    "₺": "TRY", "tl": "TRY", "try": "TRY",
    "nok": "NOK", "norveç kronu": "NOK", "sek": "SEK", "isveç kronu": "SEK",
    "dkk": "DKK", "danimarka kronu": "DKK", "kron": "KRON",
    "pln": "PLN", "zloti": "PLN", "krw": "KRW", "won": "KRW", "jpy": "JPY", "yen": "JPY",
    "inr": "INR", "rupi": "INR", "aud": "AUD", "cad": "CAD", "chf": "CHF", "frank": "CHF",
    "rub": "RUB", "ruble": "RUB", "cny": "CNY", "yuan": "CNY",
}
# Uzun adlar Türkçe ek alabilir ("dolarlık"); kısa/çok anlamlılar ("yen" ~ "yeni") ekli geçmez.
_CUR = (r"(?:\$|€|£|₺|(?<![a-zçğıöşü])(?:abd doları|norveç kronu|isveç kronu|danimarka kronu|dolar|avro|euro|sterlin|zloti|ruble|yuan)"
        r"|(?<![a-zçğıöşü])(?:kron|won|yen|rupi|frank)(?![a-zçğıöşü])"
        r"|\b(?:USD|EUR|GBP|TRY|TL|NOK|SEK|DKK|PLN|KRW|JPY|INR|AUD|CAD|CHF|RUB|CNY)\b)")
_NUM = r"\d+(?:[.,]\d+)*"
_MAG = r"(?:bin|milyon|milyar|trilyon)"
_AMT = rf"(?:{_CUR}\s?{_NUM}(?:\s{_MAG})?|{_NUM}(?:\s{_MAG})?\s?{_CUR})"
_AMT_RE = re.compile(_AMT, re.I)
_KUR_RE = re.compile(rf"({_AMT})(?:'[a-zçğıöşü]+)?\s*\(\s*(?:yaklaşık\s+|~\s*)?({_AMT})\s*\)", re.I)
_CARPAN = {"bin": 1e3, "milyon": 1e6, "milyar": 1e9, "trilyon": 1e12}


def _tutar(text):
    """'1,5 milyar $' → (1.5e9, 'USD'); okunamazsa None."""
    cur = re.search(_CUR, text, re.I)
    num = re.search(_NUM, text)
    if not cur or not num:
        return None
    n = num.group(0)
    if "," in n:                                   # Türkçe: 1.500,5
        n = n.replace(".", "").replace(",", ".")
    elif re.fullmatch(r"\d{1,3}(?:\.\d{3})+", n):  # 1.500 binlik
        n = n.replace(".", "")
    try:
        val = float(n)
    except ValueError:
        return None
    mag = re.search(_MAG, text, re.I)
    val *= _CARPAN[mag.group(0).lower()] if mag else 1
    return val, _PARA.get(cur.group(0).lower(), cur.group(0).upper())


def _ayni(a, b):
    return a and b and a[1] == b[1] and abs(a[0] - b[0]) <= 0.005 * max(a[0], b[0])


def _ozet_index(news):
    """norm_url → medya özeti (summary_tr), bütün günlerden."""
    idx = {}
    for data in news.values():
        for it in data.get("items", []):
            if it.get("summary_tr"):
                idx.setdefault(norm_url(it.get("url")), it["summary_tr"])
    try:
        extra = json.loads((NEWS_DATA / "summaries.json").read_text(encoding="utf-8"))
        for u, s in extra.items():
            if isinstance(s, str):
                idx.setdefault(norm_url(u), s)
    except Exception:
        pass
    return idx


def kur_denetimi(body, developments, ozetler):
    """KUR: gövdede 'TUTAR (başka para birimiyle TUTAR)' varsa, iki değer de aynı
    [K#]'in medya özetinde geçmeli. Ayrıca atıflı özetlerden biri aynı olguya
    aynı para biriminde başka bir değer veriyorsa (kaynaklar çelişiyor, sayfa
    tek değer basıyor) uyarılır. Döner: [uyarı metni]."""
    kaynak_url = {}
    for m in re.finditer(r"(?m)^\s*[-*]\s*\[K(\d+)\](.*)$", body):
        urls = re.findall(r"https?://[^\s<>\")]+", m.group(2))
        if urls:
            kaynak_url[m.group(1)] = norm_url(urls[-1].rstrip(".,;"))
    gelisme_k = {b[1]: set(re.findall(r"\[K(\d+)\]", b[3])) for b in development_blocks(body)}
    labels = {str(d.get("id", "")).lower(): str(d.get("label", "")) for d in developments}
    govde = re.split(r"(?m)^##\s*KAYNAKLAR.*$", body)[0]
    out = []
    for blok in (b for b in govde.split("\n") if b.strip()):
        ks = set(re.findall(r"\[K(\d+)\]", blok))
        gids = [g.lower() for g in re.findall(r"\bG\d+\b", blok)]
        for g in gids:
            ks |= gelisme_k.get(g, set())
        for m in _KUR_RE.finditer(blok):
            v1, v2 = _tutar(m.group(1)), _tutar(m.group(2))
            if not v1 or not v2 or v1[1] == v2[1]:
                continue
            ozet = {k: ozetler.get(kaynak_url.get(k, ""), "") for k in sorted(ks, key=int)}
            tutarlar = {k: [(a.group(0), _tutar(a.group(0))) for a in _AMT_RE.finditer(s)]
                        for k, s in ozet.items()}
            destek = [k for k, ts in tutarlar.items()
                      if any(_ayni(t, v1) for _r, t in ts) and any(_ayni(t, v2) for _r, t in ts)]
            # Aynı olgunun başka değeri: aynı para birimi, aynı ölçek (×0,5–×2), farklı sayı.
            baska = [(k, r) for k, ts in tutarlar.items() for r, t in ts
                     if t and t[1] == v1[1] and 0.5 <= t[0] / v1[0] <= 2 and not _ayni(t, v1)]
            if destek and not baska:
                continue
            ad = re.match(r"\s*(?:'[a-zçğıöşü]+\s+)?((?:[A-ZÇĞİÖŞÜ0-9][A-ZÇĞİÖŞÜ0-9-]+\s*){1,4})",
                          blok[m.end():])
            ad = ad.group(1).strip() if ad else (labels.get(gids[0], "") if gids else "")
            ad = ad or " ".join(blok[:m.start()].split()[-4:])
            atif = "".join(f"[K{k}]" for k in sorted(ks, key=int)) or "atıf yok"
            if baska:
                k, r = baska[0]
                ek = (f"atıflı özetler çelişiyor; {m.group(1)}'i destekleyen: "
                      + (", ".join(f"[K{d}]" for d in destek) or "yok"))
                out.append(f"{ad} {m.group(1)} ↔ özet {r} [K{k}] · gövde “{m.group(0)}” · {ek}")
            else:
                out.append(f"{ad} {m.group(1)} ↔ özet — · gövde “{m.group(0)}” · iki değer de "
                           f"aynı özette geçmiyor ({atif})")
    return out


_DURAK = {"ve", "ile", "bir", "bu", "şu", "için", "da", "de", "ki", "mi", "olarak", "the",
          "of", "and", "a", "an", "in", "on", "to", "ya", "veya", "ise", "gibi", "daha"}


def _sozcukler(text):
    text = tr_fold(re.sub(r"\bG\d+\b|\[K\d+\]|[*_`]", " ", text))
    text = re.sub(r"['’][a-zçğıöşü]+", "", text)      # Archer'ı → archer
    return {w for w in re.findall(r"[\wçğıöşü]+", text) if w not in _DURAK and (len(w) > 1 or w.isdigit())}


def h1_tekrar(h1, body, esik=0.6):
    """H1-TEKRAR: H1 ile bir özet maddesinin sözcük örtüşmesi (ortak / kısa olanın
    sözcük sayısı) ≥ eşik. Döner: [uyarı metni]."""
    block = re.search(r"##\s*YÖNETİCİ ÖZETİ\s*\n(.*?)(?=\n##|\Z)", body, re.S)
    if not block or not h1:
        return []
    a = _sozcukler(h1)
    out = []
    n = 0
    for line in block.group(1).split("\n"):
        madde = re.match(r"\s*(?:\d+[.)]|[-*])\s+(.*)", line)
        if not madde:
            continue
        n += 1
        b = _sozcukler(madde.group(1))
        if not a or not b:
            continue
        oran = len(a & b) / min(len(a), len(b))
        if oran >= esik:
            metin = re.sub(r"^G\d+\s*[—-]\s*", "", madde.group(1).strip())
            out.append(f"özet {n} · örtüşme {oran:.2f}".replace(".", ",")
                       + f" · H1 “{h1}” ↔ “{metin[:90]}{'…' if len(metin) > 90 else ''}”")
    return out


def gec_gelen_ozeti(days, late_rows):
    """Rev 31 GEÇ-GELEN: son iki medya sayfasının BRİFİNGDEN SONRA jetonlu satır sayısı → (A)."""
    import os
    parts = [f"{d}: {late_rows.get(d, 0)}"
             + ("" if d in BRIEF_AT else " (brifing yok)") for d in days]
    print(f"  · GEÇ-GELEN: BRİFİNGDEN SONRA jetonlu satır · {' · '.join(parts)}")
    summary = os.environ.get("GITHUB_STEP_SUMMARY")
    if summary:
        try:
            with open(summary, "a", encoding="utf-8") as fh:
                fh.write("### GEÇ-GELEN — medya takibi (Rev 31)\n\n"
                         + "".join(f"- {d}: BRİFİNGDEN SONRA jetonlu satır **{late_rows.get(d, 0)}**"
                                   + (f" (brifing {BRIEF_AT[d]:%H:%M})" if d in BRIEF_AT else " (brifing yok)")
                                   + "\n" for d in days) + "\n")
        except OSError as exc:
            print(f"  ! GEÇ-GELEN: özet yazılamadı: {exc}")


def r23_kurallari(iso, meta, body, body_html, news):
    """Günün raporu için ETİKET-BAŞLIK · KUR · H1-TEKRAR → Rev 30 kanalı."""
    from scripts import uyari
    developments = meta.get("developments") or []
    bulgular = ([("ETİKET-BAŞLIK", u) for u in etiket_baslik(body_html, developments)]
                + [("KUR", u) for u in kur_denetimi(body, developments, _ozet_index(news))]
                + [("H1-TEKRAR", u) for u in h1_tekrar(guard_headline(meta.get("title"), iso), body)])
    for kural, metin in bulgular:
        uyari.ekle(kural, f"{iso} · {metin}")
    print(f"  · R23 {iso}: ETİKET-BAŞLIK {sum(k == 'ETİKET-BAŞLIK' for k, _ in bulgular)}"
          f" · KUR {sum(k == 'KUR' for k, _ in bulgular)}"
          f" · H1-TEKRAR {sum(k == 'H1-TEKRAR' for k, _ in bulgular)}")
    return bulgular


# ── Rev 33 — yabancı adlarda noktalı İ (NOKTALI-İ) ─────────────────────────────
# Sayfa <html lang="tr">; `text-transform: uppercase` taşıyan alanda tarayıcı Türkçe büyük
# harf kuralını uygular ve i → İ olur ("UNMANNED AİRSPACE"). Dönüşüm doğru, yanlış olan dil
# bilgisi: yabancı ad lang="en" ile sarılır, tarayıcı o adı İngilizce kuralla büyütür. CSS'e
# dokunulmaz; Türkçe etiketler ("MEDYA TAKİBİ") Türkçe kuralla kalır.

SRC_ULKE = {}   # kaynak adı → ülke kodu (kalemlerin `country` alanı); main() doldurur
TR_HARFLER = frozenset("çğıöşüÇĞİÖŞÜ")


def noktali_boz():
    """NOKTALI_BOZ=1: sarmal yalnız bu derlemede kapanır (build.yml `noktali_boz` kanıtı)."""
    import os
    return os.environ.get("NOKTALI_BOZ", "").strip().lower() not in ("", "0", "none", "false")


def kaynak_ulkeleri(news):
    """Bütün günlerin kalemlerinden ad → ülke. Aynı ad farklı günde farklı ülkeyle gelirse son gün kazanır."""
    SRC_ULKE.clear()
    for day in sorted(news):
        for item in news[day].get("items") or []:
            if item.get("source") and item.get("country"):
                SRC_ULKE[item["source"]] = item["country"]


def yabanci_kaynak(name):
    """Kaynağın ülkesi TR değil mi? Hiç kalem getirmemiş (ülkesi veride olmayan) kaynakta:
    adında Türkçe harf yoksa yabancı sayılır — roster'da yalnız ad var, ülke yok."""
    if not name:
        return False
    ulke = SRC_ULKE.get(name)
    if ulke:
        return ulke != "TR"
    return not (set(name) & TR_HARFLER)


def ad_parcalari(name):
    """(yabancı kısım, Türkçe kuyruk): "SCMP (Çin)" → ("SCMP", " (Çin)").

    Parantez içindeki Türkçe niteleme Türkçe kuralla büyümeli ("ÇİN"); sarmal yalnız
    özel adı kapsar. Türkçe harf taşımayan parantez ("Defence24 (PL)") adın parçasıdır.
    """
    m = re.fullmatch(r"(.+?)(\s*\([^()]*\))", name or "")
    if m and set(m.group(2)) & TR_HARFLER:
        return m.group(1), m.group(2)
    return name or "", ""


def yabanci_ad(name):
    """Yabancı özel ad → `<span lang="en">ad</span>` (+ Türkçe kuyruk sarmal dışında)."""
    if noktali_boz():
        return html.escape(name)
    bas, kuyruk = ad_parcalari(name)
    return f'<span lang="en">{html.escape(bas)}</span>{html.escape(kuyruk)}'


def src_name(name):
    """Kaynak adının tek kapısı: ülkesi TR değilse lang="en" sarmalı, TR ise düz metin."""
    return yabanci_ad(name) if yabanci_kaynak(name) else html.escape(name or "")


def kaynakca_sar(body_html):
    """Brifing kaynakçası (li.source): "… — {Kaynak}, GG.AA.YYYY" içindeki bilinen yabancı
    kaynak adını src_name()'den geçirir. Ajanın yazdığı, veride olmayan adlar (ör. şirket
    siteleri) bilinmediği için düz kalır — o satırlar büyük harfli değil."""
    adlar = sorted((a for a in SRC_ULKE if yabanci_kaynak(a)), key=len, reverse=True)
    if not adlar:
        return body_html

    def li(m):
        ic = m.group(2)
        for ad in adlar:
            esc = html.escape(ad, quote=False)
            if f" — {esc}," in ic:
                ic = ic.replace(f" — {esc},", f" — {src_name(ad)},", 1)
                break
        return m.group(1) + ic + m.group(3)

    return re.sub(r'(<li id="k\d+" class="source">)((?:(?!</li>).)*)(</li>)', li, body_html, flags=re.S)


# ── NOKTALI-İ denetimi ──

_VOID = frozenset("area base br col embed hr img input link meta param source track wbr".split())


def _secici(sel):
    """'.a b', '.a > summary', 'th' → [(etiket, {sınıflar}, çocuk mu)]; desteklenmeyen → None."""
    out, cocuk = [], False
    for tok in sel.replace(">", " > ").split():
        if tok == ">":
            cocuk = True
            continue
        m = re.fullmatch(r"([a-z][a-z0-9]*)?((?:\.[\w-]+)*)", tok)
        if not m or not tok:
            return None
        out.append((m.group(1) or "", frozenset(c for c in m.group(2).split(".") if c), cocuk))
        cocuk = False
    return out or None


def buyuk_harf_kurallari(css_text=None):
    """app.css'ten [(seçici, büyük harf mi, metin)] — dosyadaki sırayla (sonraki kazanır).

    Sözde öğeler (`.prose td::before` — metni data-label özniteliğinden gelir, sarılamaz)
    ve :hover gibi durumlar atlanır; `text-transform: none` kuralları da alınır ki
    miras kesilsin (.tagline). @media blokları koşulsuz sayılır.
    """
    css = css_text if css_text is not None else (ROOT / "assets" / "app.css").read_text(encoding="utf-8")
    css = re.sub(r"/\*.*?\*/", "", css, flags=re.S)
    kurallar = []
    for m in re.finditer(r"([^{}]+)\{([^{}]*)\}", css):
        d = re.search(r"text-transform\s*:\s*([\w-]+)", m.group(2))
        if not d:
            continue
        for sel in m.group(1).split(","):
            sel = sel.strip()
            if ":" in sel:
                continue
            p = _secici(sel)
            if p:
                kurallar.append((p, d.group(1) == "uppercase", sel))
    return kurallar


def _uyar(el, s):
    etiket, siniflar, _c = s
    return (not etiket or el[0] == etiket) and siniflar <= el[1]


def _eslesir(yigin, p):
    """yigin: [(etiket, sınıflar)], son öğe denenen; p: _secici çıktısı."""
    if not _uyar(yigin[-1], p[-1]):
        return False

    def geri(j, i):
        if j < 0:
            return True
        if p[j + 1][2]:
            return i >= 1 and _uyar(yigin[i - 1], p[j]) and geri(j - 1, i - 1)
        return any(_uyar(yigin[k], p[j]) and geri(j - 1, k) for k in range(i - 1, -1, -1))

    return geri(len(p) - 2, len(yigin) - 1)


def buyuk_harfli_metinler(page_html, kurallar):
    """[(sınıf, metin)] — büyük harfle çizilen her en dış öğenin, lang'lı alt ağaçları
    '\\x00' ile kesilmiş metni. <html lang="tr"> sayılmaz: soru, adın kendi lang'ı var mı."""
    from html.parser import HTMLParser

    class P(HTMLParser):
        def __init__(self):
            super().__init__(convert_charrefs=True)
            self.yigin, self.durum, self.kayitlar, self.acik = [], [], [], None

        def handle_starttag(self, tag, attrs):
            if tag in _VOID:
                return
            a = dict(attrs)
            el = (tag, frozenset((a.get("class") or "").split()))
            self.yigin.append(el)
            ust = self.durum[-1] if self.durum else {"buyuk": False, "lang": False}
            buyuk = ust["buyuk"]
            for p, deger, _s in kurallar:
                if _eslesir(self.yigin, p):
                    buyuk = deger
            lang = ust["lang"] or (tag != "html" and "lang" in a)
            self.durum.append({"buyuk": buyuk, "lang": lang})
            if buyuk and not ust["buyuk"] and self.acik is None:
                self.acik = [len(self.yigin), tag + "".join("." + c for c in sorted(el[1])), []]

        def handle_startendtag(self, tag, attrs):
            if tag not in _VOID:
                self.handle_starttag(tag, attrs)
                self.handle_endtag(tag)

        def handle_endtag(self, tag):
            if tag in _VOID or not any(e[0] == tag for e in self.yigin):
                return
            while self.yigin:
                if self.acik and len(self.yigin) == self.acik[0]:
                    self.kayitlar.append((self.acik[1], "".join(self.acik[2])))
                    self.acik = None
                e = self.yigin.pop()
                self.durum.pop()
                if e[0] == tag:
                    break

        def handle_data(self, data):
            if self.acik is None or not self.durum:
                return
            d = self.durum[-1]
            if not d["buyuk"]:
                self.acik[2].append("\x00")
            elif d["lang"]:
                self.acik[2].append("\x00")
            else:
                self.acik[2].append(data)

    p = P()
    p.feed(page_html)
    p.close()
    return p.kayitlar


def yabanci_adlar():
    """Denetimde aranan adlar: ülkesi TR olmayan kaynaklar (yabancı kısmı) + Türk rolü
    olmayan izlenen oyuncular. Tek kalıp, en uzun önce, harf duyarlı, sözcük sınırlı."""
    adlar = {ad_parcalari(a)[0] for a in SRC_ULKE if yabanci_kaynak(a)}
    try:
        adlar |= {r["name"] for r in rivals_config() if r.get("role") not in TURKISH_ROLES}
    except Exception:
        pass
    adlar = sorted((a for a in adlar if a.strip()), key=len, reverse=True)
    if not adlar:
        return None
    return re.compile(r"(?<![\w])(" + "|".join(re.escape(a) for a in adlar) + r")(?![\w])")


def noktali_i_tara(sayfalar, kurallar=None, kalip=None):
    """[(sayfa, sınıf, ad, bağlam)] — büyük harfli alanda lang'sız duran yabancı ad."""
    kurallar = kurallar if kurallar is not None else buyuk_harf_kurallari()
    kalip = kalip if kalip is not None else yabanci_adlar()
    ornekler = []
    if not kalip:
        return ornekler
    for yol in sayfalar:
        metin = yol.read_text(encoding="utf-8")
        for sinif, t in buyuk_harfli_metinler(metin, kurallar):
            for m in kalip.finditer(t):
                baglam = " ".join(t.replace("\x00", "·").split())
                ornekler.append((yol.relative_to(ROOT).as_posix(), sinif, m.group(1), baglam))
    return ornekler


def noktali_i_sayfalari():
    """Denetlenen sayfalar, medya takibi önce, en yeni gün önce."""
    out = []
    for d in ("haberler", "reports", "izleme"):
        out += sorted((ROOT / d).glob("*.html"), reverse=True)
    return out + sorted(ROOT.glob("*.html"))


def noktali_i_kurali():
    """NOKTALI-İ: her derlemede log + (A) satırı; örnek varsa Rev 30 kanalına uyarı."""
    import os
    kurallar = buyuk_harf_kurallari()
    sayfalar = noktali_i_sayfalari()
    ornekler = noktali_i_tara(sayfalar, kurallar)
    siniflar = sorted({s for _p, _b, s in kurallar if _b})
    boz = " (NOKTALI_BOZ=1, bilerek)" if noktali_boz() else ""
    sayfa_n = len({o[0] for o in ornekler})
    print(f"  · NOKTALI-İ: {len(ornekler)} örnek{boz} · {len(sayfalar)} sayfa, "
          f"{len(siniflar)} büyük harfli seçici (app.css)")
    for o in ornekler[:10]:
        print(f"      {o[0]} · {o[1]} · “{o[2]}” ← “{o[3][:70]}”")
    summary = os.environ.get("GITHUB_STEP_SUMMARY")
    if summary:
        md = ["### NOKTALI-İ — büyük harfli alanda yabancı ad (Rev 33)", "",
              f"**{'🟢' if not ornekler else '🔴'} NOKTALI-İ: {len(ornekler)} örnek**{boz}"
              + (f" · {sayfa_n} sayfada" if ornekler else "")
              + f" · {len(sayfalar)} sayfa tarandı · büyük harfli seçiciler (app.css): "
              + ", ".join(f"`{s}`" for s in siniflar), ""]
        if ornekler:
            md += ["İlk 10 örnek:", "", "| # | sayfa | öğe | ad | metin |", "|---|---|---|---|---|"]
            boru = "|"
            md += [f"| {i} | `{p}` | `{c}` | {a} | {b[:80].replace(boru, chr(92) + boru)} |"
                   for i, (p, c, a, b) in enumerate(ornekler[:10], 1)]
        try:
            with open(summary, "a", encoding="utf-8") as fh:
                fh.write("\n".join(md) + "\n\n")
        except OSError as exc:
            print(f"  ! NOKTALI-İ: özet yazılamadı: {exc}")
    if ornekler:
        from scripts import uyari
        tekil = list(dict.fromkeys((p, a) for p, _c, a, _b in ornekler))
        ilk = " · ".join(f"{p} “{a}”" for p, a in tekil[:3])
        uyari.ekle("NOKTALI-İ", f"NOKTALI-İ: büyük harfli alanda lang'sız yabancı ad {len(ornekler)} örnek, "
                                f"{sayfa_n} sayfada{boz} — ilk: {ilk}")
    return ornekler


# ── Rev 32 — tekrar eden manşet (TEKRAR-MANŞET) ──────────────────────────────
# Önceki bir raporda verilmiş gelişme yeni diye sunulmasın: özet maddesi (ya da H1)
# önceki 7 raporun bir gelişmesiyle eşleşirse maddenin sonuna "ilk: 19 Eyl" jetonu
# basılır ve o raporun gelişmesine bağlanır (atıf tek yönlü, eskiye doğru — Rev 6;
# kimlik değil tarih taşır — Rev 11; ajan değil build türetir — Rev 10). Madde
# silinmez: madde ajanın yargısı, build yalnız bağlamı ekler.
#
# Eşleşme: paylaşılan [K#] URL'si, ya da en az iki ortak özel ad (büyük harfle
# başlayan, sözlükte olmayan kelime) artı sözcük örtüşmesi ≥ 0,4 (ortak / kısa olanın
# sözcük sayısı — H1-TEKRAR'ın ölçüsü). "Sözlük" derlemin kendisi: raporlarda bir
# yerde küçük harfle geçen kelime özel ad değildir ("Savunma" cümle başında büyük
# yazılır ama "savunma" da geçer); ay ve gün adları Türkçede hep büyük yazıldığı için
# ayrıca sözlüktedir.

TEKRAR_PENCERE = 7          # önceki kaç rapor
TEKRAR_ORTUSME = 0.4
TEKRAR_OZEL_AD = 2
_TEKRAR_SOZLUK_EK = {tr_fold(w) for w in TR_MONTHS + TR_DAYS}
_BUYUK = "A-ZÇĞİÖŞÜ"
_OZEL_AD_RE = re.compile(rf"(?<![\w-])[{_BUYUK}][\w-]*")


def _ozet_maddeleri(body):
    """[(gid|None, metin)] — YÖNETİCİ ÖZETİ maddeleri, sırasıyla."""
    block = re.search(r"##\s*YÖNETİCİ ÖZETİ\s*\n(.*?)(?=\n##|\Z)", body, re.S)
    out = []
    if not block:
        return out
    for line in block.group(1).split("\n"):
        m = re.match(r"\s*(?:\d+[.)]|[-*])\s+(.*)", line)
        if not m:
            continue
        g = re.match(r"\s*\**(G\d+)\**\s*[—-]\s*(.*)", m.group(1))
        out.append((g.group(1).lower(), g.group(2).strip()) if g else (None, m.group(1).strip()))
    return out


def _kaynak_urlleri(body):
    """{K#: normalleştirilmiş URL} — KAYNAKLAR bölümünden."""
    out = {}
    for m in re.finditer(r"^\s*[-*]\s*\[(K\d+)\][^\n]*?(https?://\S+)", body, re.M):
        out[m.group(1)] = norm_url(m.group(2).rstrip(").,;"))
    return out


def _ilk_cumle(text):
    text = re.sub(r"\s*\[K\d+\]", "", text).strip()
    m = re.match(r"(.+?[.!?])(?:\s+(?=[{0}0-9\"“])|$)".format(_BUYUK), text, re.S)
    return (m.group(1) if m else text)[:400]


def _ozel_adlar(text, sozluk):
    """Büyük harfle başlayan, derlemde küçük harfle hiç geçmeyen kelimeler (katlanmış)."""
    text = re.sub(r"\bG\d+\b|\[K\d+\]", " ", text)
    out = set()
    for w in _OZEL_AD_RE.findall(text):
        w = re.split(r"['’]", w, maxsplit=1)[0].strip("-")
        f = tr_fold(w)
        if len(f) < 2 or f in sozluk or f in _TEKRAR_SOZLUK_EK:
            continue
        out.add(f)
    return out


def tekrar_sozlugu(sources):
    """Derlemde küçük harfle başlayarak geçen her kelime (katlanmış) — "sözlük"."""
    sozluk = set()
    for _iso, meta, body in sources:
        metin = body + " " + str(meta.get("summary", "")) + " " + str(meta.get("title", ""))
        for w in re.findall(r"(?<![\w-])[a-zçğıöşü][\wçğıöşü]*", metin):
            sozluk.add(tr_fold(w))
    return sozluk


def rapor_gelismeleri(body):
    """{gid: {"metinler": [...], "url": {...}, "etiket": str}} — bir raporun gelişmeleri.

    Karşılaştırma metni gelişmenin özet maddesi (varsa) ve etiket + gövdenin ilk
    cümlesi; URL kümesi gelişme bloğunun atıf verdiği [K#]'lerin adresleri.
    """
    urller = _kaynak_urlleri(body)
    ozet = {g: t for g, t in _ozet_maddeleri(body) if g}
    out = {}
    for _n, gid, etiket, govde in development_blocks(body):
        d = out.setdefault(gid, {"metinler": [], "url": set(), "etiket": etiket.strip()})
        d["metinler"].append(f"{etiket.strip()} — {_ilk_cumle(govde)}")
        d["url"] |= {urller[k] for k in re.findall(r"\[(K\d+)\]", govde) if k in urller}
    for gid, t in ozet.items():
        if gid in out:
            out[gid]["metinler"].insert(0, t)
    return out


def _eslesme(metin, url, onceki, sozluk):
    """(neden, örtüşme, ortak özel adlar) ya da None."""
    if url and url & onceki["url"]:
        return ("url", 1.0, [])
    a = _sozcukler(metin)
    oa = _ozel_adlar(metin, sozluk)
    en_iyi = None
    for t in onceki["metinler"]:
        b = _sozcukler(t)
        if not a or not b:
            continue
        ortak_ad = oa & _ozel_adlar(t, sozluk)
        oran = len(a & b) / min(len(a), len(b))
        if len(ortak_ad) >= TEKRAR_OZEL_AD and oran >= TEKRAR_ORTUSME:
            if en_iyi is None or oran > en_iyi[1]:
                en_iyi = ("ad", oran, sorted(ortak_ad))
    return en_iyi


def tekrar_eslesmeleri(sources):
    """{iso: {"ozet": {sıra: bulgu}, "h1": bulgu|None}} — bulgu: önceki 7 rapordaki en
    eski eşleşen gelişme ({"gun", "gid", "etiket", "neden", "oran", "adlar"})."""
    sozluk = tekrar_sozlugu(sources)
    gelismeler = [(iso, rapor_gelismeleri(body)) for iso, _m, body in sources]
    out = {}
    for i, (iso, meta, body) in enumerate(sources):
        onceki = gelismeler[max(0, i - TEKRAR_PENCERE):i]      # eskiden yeniye
        bugun = gelismeler[i][1]

        def ara(metin, url):
            for gun, devs in onceki:                              # en eski önce: "ilk"
                for gid, d in sorted(devs.items(), key=lambda kv: int(kv[0][1:])):
                    e = _eslesme(metin, url, d, sozluk)
                    if e:
                        return {"gun": gun, "gid": gid, "etiket": d["etiket"],
                                "neden": e[0], "oran": e[1], "adlar": e[2]}
            return None

        ozet = {}
        for n, (gid, metin) in enumerate(_ozet_maddeleri(body), 1):
            url = bugun.get(gid, {}).get("url", set()) if gid else set()
            b = ara(metin, url)
            if b:
                ozet[n] = dict(b, gid_bugun=gid, metin=metin)
        h1 = guard_headline(meta.get("title"), iso)
        out[iso] = {"ozet": ozet, "h1": ara(h1, set()) if h1 else None}
    return out


def ilk_jetonu(bulgu):
    gun = bulgu["gun"]
    return (f' <a class="ilk" href="{day_url("report", gun, "#" + bulgu["gid"])}"'
            f' title="{html.escape(tr_date(gun))} raporu: {html.escape(bulgu["etiket"])}">'
            f'ilk: {tr_daybar(gun).split(" · ")[0]}</a>')


def ilk_jetonlari(body_html, bulgular):
    """Özetin n. maddesinin sonuna (</li> önüne) "ilk: GG Aaa" jetonu."""
    if not bulgular:
        return body_html
    sec = re.search(r'(<h2 id="ozet">.*?</h2>\s*<ol>)(.*?)(</ol>)', body_html, re.S)
    if not sec:
        return body_html
    maddeler = re.split(r"(?=<li>)", sec.group(2))
    n = 0
    for i, parca in enumerate(maddeler):
        if not parca.startswith("<li>"):
            continue
        n += 1
        if n in bulgular:
            j = parca.rfind("</li>")
            if j >= 0:
                maddeler[i] = parca[:j] + ilk_jetonu(bulgular[n]) + parca[j:]
    return body_html[:sec.start(2)] + "".join(maddeler) + body_html[sec.end(2):]


def tekrar_manset_kurali(iso, eslesme):
    """TEKRAR-MANŞET: log satırı + (A); günün H1'i eşleşirse Rev 30 kanalına uyarı."""
    import os
    kisa = lambda g: tr_daybar(g).split(" · ")[0]
    h1 = eslesme.get("h1")
    ozet = eslesme.get("ozet", {})
    satirlar = [f"özet {n} ↔ {kisa(b['gun'])} {b['gid'].upper()} “{b['etiket']}” ({b['neden']}"
                + (f" {b['oran']:.2f}".replace(".", ",") + " · " + ", ".join(b["adlar"]) if b["neden"] == "ad" else "")
                + ")" for n, b in sorted(ozet.items())]
    print(f"  · TEKRAR-MANŞET {iso}: H1 {('↔ ' + kisa(h1['gun'])) if h1 else '—'}"
          f" · jetonlu özet maddesi {len(ozet)}")
    for s in satirlar:
        print(f"      {s}")
    summary = os.environ.get("GITHUB_STEP_SUMMARY")
    if summary:
        md = ["### TEKRAR-MANŞET — önceki 7 raporla eşleşen manşet ve özet (Rev 32)", "",
              f"**{'🔴' if h1 else '🟢'} H1:** "
              + (f"{kisa(iso)} H1 ↔ {kisa(h1['gun'])} ({h1['gid'].upper()} “{h1['etiket']}”)" if h1 else "yeni")
              + f" · **“ilk:” jetonlu özet maddesi {len(ozet)}**", ""]
        md += [f"- {s}" for s in satirlar]
        try:
            with open(summary, "a", encoding="utf-8") as fh:
                fh.write("\n".join(md) + "\n\n")
        except OSError as exc:
            print(f"  ! TEKRAR-MANŞET: özet yazılamadı: {exc}")
    if h1:
        from scripts import uyari
        uyari.ekle("TEKRAR-MANŞET", f"TEKRAR-MANŞET: {kisa(iso)} H1 ↔ {kisa(h1['gun'])}")
    return h1


# ── Rev 29 — görsel sistem: L1-DOLGU · ÇİZGİ-KONTRAST ───────────────────────

ZEMIN_BELIRTECLERI = ("--paper", "--paper-2")   # sayfanın zemin aileleri; --alarm-tint bir DURUM rengi
CIZGI_ESIK = 3.0


def _app_css(css_text=None):
    css = css_text if css_text is not None else (ROOT / "assets" / "app.css").read_text(encoding="utf-8")
    return re.sub(r"/\*.*?\*/", "", css, flags=re.S)


def css_belirtecleri(css_text=None):
    """{"açık": {ad: değer}, "koyu": {…}} — `:root {…}` ve prefers-color-scheme: dark içindeki
    `:root:not([data-theme="light"]) {…}`. Koyu tema açığın üzerine yazılır (miras)."""
    css = _app_css(css_text)

    def blok(sec_re, metin):
        m = re.search(sec_re + r"\s*\{([^{}]*)\}", metin)
        return dict(re.findall(r"(--[\w-]+)\s*:\s*([^;]+);", m.group(1))) if m else {}

    acik = blok(r"(?:^|\})\s*:root", css)
    koyu_m = re.search(r"@media\s*\(\s*prefers-color-scheme\s*:\s*dark\s*\)\s*\{(.*?\})\s*\}", css, re.S)
    koyu = {**acik, **(blok(r":root:not\(\[data-theme=\"light\"\]\)", koyu_m.group(1)) if koyu_m else {})}
    return {"açık": {k: v.strip() for k, v in acik.items()}, "koyu": {k: v.strip() for k, v in koyu.items()}}


def kontrast_orani(a, b):
    """WCAG 2 bağıl parlaklık oranı; #RGB / #RRGGBB."""
    def lum(h):
        h = h.strip().lstrip("#")
        if len(h) == 3:
            h = "".join(c * 2 for c in h)
        out = []
        for i in (0, 2, 4):
            c = int(h[i:i + 2], 16) / 255
            out.append(c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4)
        return 0.2126 * out[0] + 0.7152 * out[1] + 0.0722 * out[2]
    x, y = sorted((lum(a), lum(b)), reverse=True)
    return (x + 0.05) / (y + 0.05)


def cizgi_kontrast(css_text=None):
    """[(tema, --rule-2, --paper, oran)] — iki temada bölüm çizgisinin zemine karşı oranı."""
    out = []
    for tema, t in css_belirtecleri(css_text).items():
        out.append((tema, t.get("--rule-2", "?"), t.get("--paper", "?"),
                    kontrast_orani(t["--rule-2"], t["--paper"]) if "--rule-2" in t and "--paper" in t else 0.0))
    return out


def l1_dolgu_ihlalleri(css_text=None):
    """[(seçici, zemin, sol kenar)] — zemin belirteci (--paper*) ile aynı anda border-left.

    Her seçicinin bildirimleri dosya sırasıyla birleşir (sonraki kazanır; @media koşulsuz sayılır).
    Aynı öğeyi daha dar yazan seçici, sonu onunla biten temel seçiciden miras alır
    (`.report--alarm .prose h2#ozet + ol` ← `.prose h2#ozet + ol`; `.chip:hover` ← `.chip`), ki
    zemin bir kuralda, kenar başka kuralda gelince de yakalansın. `border:` kısayolu (dört kenarlı
    kutu, ör. çipler) sol kenar vurgusu sayılmaz."""
    css = _app_css(css_text)
    secici = {}
    for m in re.finditer(r"([^{}]+)\{([^{}]*)\}", css):
        bild = re.findall(r"([\w-]+)\s*:\s*([^;]+)", m.group(2))
        for sel in m.group(1).split(","):
            sel = re.sub(r"\s+", " ", sel).strip()
            if not sel or sel.startswith("@") or sel.startswith(":root") or re.fullmatch(r"[\d.%]+|from|to", sel):
                continue
            d = secici.setdefault(sel, {})
            for ad, deger in bild:
                d[ad.lower()] = deger.strip()

    def taban(sel):
        adaylar = []
        yalin = re.sub(r"(:(?:hover|active|focus|focus-visible|focus-within|visited))+$", "", sel)
        if yalin != sel:
            adaylar.append(yalin)
        for b in secici:
            if b != sel and (sel.endswith(" " + b) or sel.endswith("+ " + b) or sel.endswith("> " + b)):
                adaylar.append(b)
        return adaylar

    def etkin(sel, gorulen=()):
        d = {}
        for b in taban(sel):
            if b not in gorulen:
                d.update(etkin(b, gorulen + (sel,)))
        d.update(secici[sel])
        return d

    def sol_kenar(d):
        for ad in ("border-left", "border-inline-start", "border-left-width", "border-inline-start-width"):
            v = d.get(ad)
            if v is not None:
                if re.search(r"\b(none|hidden)\b", v) or re.fullmatch(r"0(px)?", v.strip()):
                    return None
                if ad.endswith("-width") and re.fullmatch(r"0(px)?", v.strip()):
                    return None
                return f"{ad}: {v}"
        return None

    out = []
    zemin_re = re.compile(r"var\(\s*(" + "|".join(re.escape(z) for z in ZEMIN_BELIRTECLERI) + r")\s*\)")
    for sel in secici:
        d = etkin(sel)
        zemin = next((f"{a}: {d[a]}" for a in ("background", "background-color")
                      if a in d and zemin_re.search(d[a])), None)
        kenar = sol_kenar(d)
        if zemin and kenar:
            out.append((sel, zemin, kenar))
    return out


def r29_kurallari(css_text=None):
    """L1-DOLGU + ÇİZGİ-KONTRAST: log satırı, (A)'da birer satır, ihlalde Rev 30 kanalı."""
    import os
    from scripts import uyari
    ihlal = l1_dolgu_ihlalleri(css_text)
    oranlar = cizgi_kontrast(css_text)
    dusuk = [o for o in oranlar if o[3] < CIZGI_ESIK]
    fmt = lambda x: f"{x:.2f}".replace(".", ",")
    oran_metni = " · ".join(f"{t} {fmt(o)}:1 ({r} / {z})" for t, r, z, o in oranlar)
    print(f"  · L1-DOLGU: {len(ihlal)} ihlal · zemin belirteci (--paper, --paper-2) + border-left")
    for sel, zemin, kenar in ihlal[:10]:
        print(f"      {sel} · {zemin} · {kenar}")
    print(f"  · ÇİZGİ-KONTRAST: --rule-2 / --paper · {oran_metni} · eşik {fmt(CIZGI_ESIK)}")
    summary = os.environ.get("GITHUB_STEP_SUMMARY")
    if summary:
        md = ["### L1-DOLGU · ÇİZGİ-KONTRAST — görsel sistem (Rev 29)", "",
              f"- **{'🟢' if not ihlal else '🔴'} L1-DOLGU: {len(ihlal)} ihlal** · zemin belirteci + `border-left`"
              + (" · " + ", ".join(f"`{s}`" for s, _z, _k in ihlal[:5]) if ihlal else ""),
              f"- **{'🟢' if not dusuk else '🔴'} ÇİZGİ-KONTRAST:** `--rule-2` / `--paper` · "
              + " · ".join(f"{t} **{fmt(o)}:1**" for t, _r, _z, o in oranlar) + f" (eşik {fmt(CIZGI_ESIK)})", ""]
        try:
            with open(summary, "a", encoding="utf-8") as fh:
                fh.write("\n".join(md) + "\n")
        except OSError as exc:
            print(f"  ! R29: özet yazılamadı: {exc}")
    if ihlal:
        uyari.ekle("L1-DOLGU", f"L1-DOLGU: {len(ihlal)} öğe zemin belirteciyle birlikte border-left taşıyor — "
                               + ", ".join(s for s, _z, _k in ihlal[:3]))
    if dusuk:
        uyari.ekle("ÇİZGİ-KONTRAST", "ÇİZGİ-KONTRAST: --rule-2 zemine karşı 3:1'in altında — "
                                     + " · ".join(f"{t} {fmt(o)}:1" for t, _r, _z, o in dusuk))
    return ihlal, oranlar


# ── Rev 28 — izlenen oyuncunun kendi kaynağı düştüğünde (KANIT-BOŞLUĞU) ───────────
# İnanç değiştiren tek arıza: bir izlenen oyuncunun kendi duyuru kaynağı okunamadıysa o
# oyuncunun bugünkü duyurusu eksik olabilir. Okuyucuya tek satır, operatöre tek uyarı.
# Tetik yalnız toplayıcının kaydı (data/news/<gün>.json failures[].source) ile
# rakipler.json `kaynak` alanının kesişimi — ajanın beyanı tetik olamaz (Rev 14).
# Kesişim boşsa satır basılmaz (Rev 9).

def oyuncu_kaynaklari():
    """{kaynak adı: (oyuncu adı, oyuncu id)} — `kaynak` alanı olan oyuncular."""
    return {r["kaynak"]: (r["name"], r["id"]) for r in rivals_config() if r.get("kaynak")}


def kanit_boslugu(data):
    """[(kaynak, oyuncu adı, oyuncu id, hata)] — bugün kendi kaynağı okunamayan oyuncular."""
    hatalar = {}
    for f in (data or {}).get("failures") or []:
        if f.get("source"):
            hatalar[f["source"]] = " ".join(str(f.get("error") or "").split())
    oyuncu = oyuncu_kaynaklari()
    return sorted(((k, ad, rid, hatalar[k]) for k, (ad, rid) in oyuncu.items() if k in hatalar),
                  key=lambda x: tr_fold(x[0]))


_UNLU = "aeıioöuü"


def _ilgi_eki(ad):
    """Tamlayan eki, kesme işaretiyle: Grumman → 'ın, Leonardo → 'nun, MBDA → 'nın."""
    kelime = re.sub(r"[^\w]", "", ad.split()[-1]) if ad.split() else ""
    if not kelime:
        return "'ın"
    if len(kelime) > 1 and kelime.isupper():
        # Kısaltma harf harf okunur: ünsüz harflerin adı e ile biter (be, de…), K ka'dır.
        son = kelime[-1].translate(str.maketrans("İI", "ii")).lower()
        ses = son if son in _UNLU else ("a" if son == "k" else "e")
        tampon = "n"
    else:
        k = kelime.translate(str.maketrans("İI", "iı")).lower()
        unluler = [c for c in k if c in _UNLU]
        ses = unluler[-1] if unluler else "e"
        tampon = "n" if k[-1] in _UNLU else ""
    ek = {"a": "ı", "ı": "ı", "e": "i", "i": "i", "o": "u", "u": "u", "ö": "ü", "ü": "ü"}[ses]
    return f"'{tampon}{ek}n"


def kanit_cumlesi(adlar):
    """"A ve B'nin kendi duyuruları bugün okunamadı." — neden, sayı, renk yok."""
    adlar = list(adlar)
    if not adlar:
        return ""
    liste = adlar[0] if len(adlar) == 1 else ", ".join(adlar[:-1]) + " ve " + adlar[-1]
    return f"{liste}{_ilgi_eki(adlar[-1])} kendi duyuruları bugün okunamadı."


def kanit_html(adlar):
    """Tarama bloğunun altındaki tek satır; kesişim boşsa hiçbir şey."""
    if not adlar:
        return ""
    return f'<span class="rail-not" data-kural="KANIT-BOŞLUĞU">{html.escape(kanit_cumlesi(adlar))}</span>'


def kanit_boslugu_kurali(iso, data):
    """Günün raporu: log satırı + (A); satır basılıyorsa Rev 30 kanalına uyarı. → [kaynak]"""
    import os
    kb = kanit_boslugu(data)
    adlar = [k for k, *_ in kb]
    kisa = tr_daybar(iso).split(" · ")[0]
    if data is None:
        durum = "medya takibi yok — satır yok"
    elif kb:
        durum = "satır: " + kanit_cumlesi(adlar)
    else:
        durum = f"kesişim boş ({len((data or {}).get('failures') or [])} başarısız kaynak, hiçbiri oyuncu kaynağı değil) — satır yok"
    if BOS_KESISIM_DURUM and BOS_KESISIM_DURUM[0] == iso:
        durum += (f" (BOS_KESISIM, bilerek: {', '.join(BOS_KESISIM_DURUM[1]) or '—'} bu derlemede"
                  " yanıt vermiş sayıldı; veri dosyası değişmedi)")
    print(f"  · KANIT-BOŞLUĞU {iso}: {durum}")
    for k, ad, _rid, hata in kb:
        print(f"      {k} ({ad}): {hata or 'hata metni yok'}")
    summary = os.environ.get("GITHUB_STEP_SUMMARY")
    if summary:
        md = ["### KANIT-BOŞLUĞU — izlenen oyuncunun kendi kaynağı (Rev 28)", "",
              f"**{'🔴' if kb else '🟢'} {kisa}:** {durum}", ""]
        md += [f"- {k} ({ad}): `{hata or '—'}`" for k, ad, _rid, hata in kb]
        try:
            with open(summary, "a", encoding="utf-8") as fh:
                fh.write("\n".join(md) + "\n\n")
        except OSError as exc:
            print(f"  ! KANIT-BOŞLUĞU: özet yazılamadı: {exc}")
    if kb:
        from scripts import uyari
        uyari.ekle("KANIT-BOŞLUĞU", f"KANIT-BOŞLUĞU: {kisa} · "
                   + " · ".join(f"{k} ({hata or 'hata metni yok'})" for k, _ad, _rid, hata in kb)
                   + " — okuyucuya satır basıldı, kaynağı onar")
    return adlar



# Rev 28 (deneme 2) — kesişimi boş günün kanıtı (build.yml `bos_kesisim`, yerelde BOS_KESISIM).
# Gerçek veride taranan her gün Elbit ve Northrop'un kaynağı düşmüş; "kesişim boşsa satır yok"
# yarısı hiçbir sayfada görünmüyordu. BOS_KESISIM açıkken yalnız bu derlemenin belleğinde, seçilen
# günün failures listesinden oyuncu kaynakları çıkarılır (o kaynaklar yanıt vermiş sayılır; öteki
# başarısız kaynaklar kalır). Kesişim gerçekten hesaplanır ve boş çıkar; data/news'e hiçbir şey
# yazılmaz. CI'da bu çalıştırma commit atmaz, uyarıları "[TEST] " önekli issue'ya gider.
BOS_KESISIM_DURUM = None   # (gün, [çıkarılan kaynaklar]) — yalnız BOS_KESISIM açıkken


def bos_kesisim():
    """BOS_KESISIM: boş/0/none → kapalı; 1 → son brifing günü; YYYY-MM-DD → o gün."""
    import os
    raw = (os.environ.get("BOS_KESISIM") or "").strip().lower()
    if raw in ("", "0", "none", "false"):
        return None
    if re.fullmatch(r"\d{4}-\d{2}-\d{2}", raw):
        return raw
    return "son"


def bos_kesisim_duzenle(news, report_days):
    """Seçilen günün kaydını bellekte düzenler; → (gün, [çıkarılan]) ya da None."""
    global BOS_KESISIM_DURUM
    import os
    secim = bos_kesisim()
    if not secim:
        return None
    if secim == "son":
        adaylar = [d for d in report_days if d in news]
        gun = adaylar[-1] if adaylar else None
    else:
        gun = secim if secim in news else None
    if not gun:
        sys.exit(f"BOS_KESISIM={os.environ.get('BOS_KESISIM')}: medya takibi olan brifing günü yok")
    veri = dict(news[gun])
    oyuncu = oyuncu_kaynaklari()
    fails = list(veri.get("failures") or [])
    cik = sorted({f.get("source") for f in fails if f.get("source") in oyuncu}, key=tr_fold)
    kalan = [f for f in fails if f.get("source") not in oyuncu]
    veri["failures"] = kalan
    veri["failed_sources"] = max(0, int(veri.get("failed_sources") or 0) - (len(fails) - len(kalan)))
    news[gun] = veri
    BOS_KESISIM_DURUM = (gun, cik)
    msg = (f"BOS_KESISIM (bilerek, yalnız bu derleme): {gun} — oyuncu kaynakları yanıt vermiş sayıldı: "
           f"{', '.join(cik) or '—'} · kalan {len(kalan)} başarısız kaynak "
           f"({', '.join(f.get('source') or '?' for f in kalan[:4])}{'…' if len(kalan) > 4 else ''}) · "
           "data/news değişmedi")
    print(f"  ⚠ {msg}")
    summary = os.environ.get("GITHUB_STEP_SUMMARY")
    if summary:
        try:
            with open(summary, "a", encoding="utf-8") as fh:
                fh.write(f"> ⚠️ **bos_kesisim** — {msg}. Bu çalıştırma commit atmaz.\n\n")
        except OSError as exc:
            print(f"  ! BOS_KESISIM: özet yazılamadı: {exc}")
    return BOS_KESISIM_DURUM


if __name__ == "__main__":
    main()
