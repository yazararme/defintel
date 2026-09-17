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
import json
import pathlib
import re
import sys

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
SITE_TAGLINE = "MKE stratejik pazar istihbaratı"
# Push service (Cloudflare Worker). Empty string hides the notification button.
PUSH_ENDPOINT = "https://defintel-push.yazararme-c30.workers.dev"
VAPID_PUBLIC_KEY = "BLOHxsm23_gz-DmV0E9xyB3RVQTkCwv06uPv_pme7VApr61x_gnNGGPkTnEI3mNekR7lzZGxNL9hATzaaOYsEZo"

TR_MONTHS = [
    "Ocak", "Şubat", "Mart", "Nisan", "Mayıs", "Haziran",
    "Temmuz", "Ağustos", "Eylül", "Ekim", "Kasım", "Aralık",
]
TR_DAYS = ["Pazartesi", "Salı", "Çarşamba", "Perşembe", "Cuma", "Cumartesi", "Pazar"]

# Reading state, kept in data/reports.json for downstream use; not shown on the page.
#   alarm: true                  -> alarm
#   a deadline still ahead of us -> izle
#   neither                      -> temiz


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


def status_of(meta, iso):
    if meta.get("alarm"):
        return "alarm"
    deadline = meta.get("decision_by")
    if deadline and str(deadline) >= str(iso):
        return "izle"
    return "temiz"


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


def masthead(up="", latest_news=None):
    link = (
        f'<a class="masthead-link" href="{up}haberler/{latest_news}.html">Medya takibi</a>'
        if latest_news
        else ""
    )
    return f"""<header class="masthead">
  <div class="wrap masthead-inner">
    <a class="wordmark" href="{up}index.html">{SITE_NAME}</a>
    <span class="tagline">{SITE_TAGLINE}</span>
    {link}
  </div>
</header>
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
      <strong>Yeni rapor çıkınca haber verelim mi?</strong>
      <span>Her sabah rapor yayınlandığında tek bildirim; istediğinde kapatırsın.</span>
    </p>
    <span class="promptbar-actions">
      <button class="pbtn" type="button" data-action="enable">Aç</button>
      <button class="pbtn pbtn--quiet" type="button" data-action="later">Şimdi değil</button>
    </span>
  </div>
</div>
"""

FOOT = """<footer class="foot">
  <div class="wrap">
    Yalnızca kamuya açık kaynaklara dayanır; doğrulanmamış iddialar raporda ayrıca işaretlenir.
    MKE'nin resmî görüşünü yansıtmaz.
  </div>
</footer>
</body>
</html>
"""


def build_report(meta, body_html, iso, news_days=(), latest_news=None):
    title = meta.get("title") or f"{tr_date(iso)} raporu"

    banner = (
        f'<p class="alarmbar">{html.escape(str(meta.get("alarm_title") or "Alarm"))}</p>'
        if meta.get("alarm")
        else ""
    )
    deadline = (
        f'<p class="deadline-chip">Dış son tarih: {tr_date(meta["decision_by"])}</p>'
        if meta.get("decision_by")
        else ""
    )

    rail = [
        '<div class="rail-block"><span class="rail-label">Tarih</span>'
        f'<span class="rail-value num">{tr_date(iso, weekday=True)}</span></div>'
    ]
    if iso in news_days:
        rail.append(
            '<div class="rail-block"><span class="rail-label">Medya takibi</span>'
            f'<a class="rail-value" href="../haberler/{iso}.html">O günün tam listesi →</a></div>'
        )

    return (
        head(f"{title} — {SITE_NAME}", depth=1)
        + masthead(up="../", latest_news=latest_news)
        + f"""<main class="wrap report">
  <a class="backlink" href="../index.html">← Geri</a>
  <div class="report-grid">
    <aside class="rail">{''.join(rail)}</aside>
    <article class="column">
      {banner}
      <h1 class="report-title">{html.escape(title)}</h1>
      {deadline}
      {enrich.nav(meta.get("developments") or [])}
      <div class="prose">
{body_html}
      </div>
    </article>
  </div>
</main>
"""
        + PROMPTS
        + f'<script src="../{asset("app.js")}" defer></script>\n'
        + FOOT
    )


NEWS_ORDER = [
    "MKE", "C-UAS ve Hava Savunma", "Topçu ve Mühimmat", "Rakip Duyuruları",
    "İhale ve Sözleşmeler", "Deniz ve İnsansız Sistemler", "Hafif Silah ve Mayın",
    "Tedarik Zinciri", "Politika ve Regülasyon", "Genel Savunma Gündemi",
]


def load_news():
    """One file per day, written by scripts/collect_news.py."""
    days = {}
    for path in sorted(NEWS_DATA.glob("*.json")):
        try:
            days[path.stem] = json.loads(path.read_text(encoding="utf-8"))
        except Exception as exc:
            print(f"  ! skipped {path.name}: {exc}")
    return days


def clip_html(item):
    meta = [html.escape(item.get("source", ""))]
    if item.get("also"):
        meta.append("+ " + html.escape(", ".join(item["also"][:3])))
    if item.get("published"):
        meta.append(tr_date(item["published"]))
    if item.get("country"):
        meta.append(html.escape(item["country"]))
    return (
        '<li class="clip">'
        f'<a href="{html.escape(item["url"], quote=True)}" target="_blank" rel="noopener">'
        f'{html.escape(item["title"])}</a>'
        f'<span class="clip-meta">{" · ".join(meta)}</span></li>'
    )


def build_news_page(day, data, prev_day, next_day, has_report, latest_news):
    buckets = {}
    for item in data.get("items", []):
        buckets.setdefault(item.get("category") or "Genel Savunma Gündemi", []).append(item)

    body = []
    for name in NEWS_ORDER + sorted(set(buckets) - set(NEWS_ORDER)):
        items = buckets.get(name)
        if not items:
            continue
        body.append(
            f'<h2 class="kicker">{html.escape(name)} <span class="kicker-count">{len(items)}</span></h2>'
            '<ul class="clips">' + "".join(clip_html(i) for i in items) + "</ul>"
        )

    nav = []
    if prev_day:
        nav.append(f'<a class="backlink" href="{prev_day}.html">← {tr_date(prev_day)}</a>')
    if has_report:
        nav.append(f'<a class="backlink" href="../reports/{day}.html">O günün brifingi →</a>')
    if next_day:
        nav.append(f'<a class="backlink" href="{next_day}.html">{tr_date(next_day)} →</a>')

    # "66 kaynak" okunan değil tanımlı kaynak sayısıydı; okunanı yaz, farkı da göster
    defined = data.get("scanned_sources", 0)
    unread = data.get("failed_sources", 0)
    read = defined - unread
    stat = (
        f'{read} kaynak okundu · {data.get("unique_items", 0)} başlık'
        f' · son {data.get("window_hours", 48)} saat'
        + (f' · {unread} kaynak yanıt vermedi' if unread else "")
    )
    return (
        head(f"Medya takibi · {tr_date(day)} — {SITE_NAME}", depth=1)
        + masthead(up="../", latest_news=latest_news)
        + f"""<main class="wrap news">
  <div class="news-head">
    <h1 class="report-title">Medya takibi · {tr_date(day)}</h1>
    <p class="news-stat num">{stat}</p>
    <nav class="news-nav">{" ".join(nav)}</nav>
  </div>
  {"".join(body) or '<p class="empty">Bu gün için kayıt yok.</p>'}
</main>
"""
        + PROMPTS
        + f'<script src="../{asset("app.js")}" defer></script>\n'
        + FOOT
    )


def entry_html(r):
    rail = [f'<time class="datestamp num">{tr_date(r["date"])}</time>']
    if r["alarm"]:
        rail.append('<span class="badge badge--alarm">Alarm</span>')
    if r.get("decision_by"):
        rail.append(f'<span class="badge num">Son tarih · {tr_short(r["decision_by"])}</span>')

    heads = [d for d in (r.get("developments") or [])
             if str(d.get("home", "gelismeler")).lower() == "gelismeler"]
    chips = ""
    if heads:
        shown = [html.escape(str(d.get("label") or d.get("id") or "")) for d in heads[:3]]
        more = len(heads) - len(shown)
        chips = (
            '<div class="entry-chips">'
            + "".join(f"<span>{t}</span>" for t in shown)
            + (f"<span>+{more}</span>" if more > 0 else "")
            + "</div>"
        )

    haystack = " ".join(
        [r["date"], tr_date(r["date"]), tr_short(r["date"]), r.get("title", ""),
         r.get("summary", "")] + [str(t) for t in r.get("tags", [])]
    ).lower()

    return f"""<a class="entry" href="{r['path']}"
   data-tags="{html.escape('|'.join(str(t) for t in r.get('tags', [])))}"
   data-search="{html.escape(haystack)}">
  <div class="entry-rail">{''.join(rail)}</div>
  <div class="entry-main">
    <h2 class="entry-title">{html.escape(r.get('title', ''))}</h2>
    <p class="entry-summary">{html.escape(r.get('summary', ''))}</p>
    {chips}
  </div>
</a>"""


def build_index(reports, version, latest_news=None):
    if not reports:
        body = '<p class="empty">Henüz rapor yok.</p>'
    else:
        body = '<div class="feed">' + "".join(entry_html(r) for r in reports) + "</div>"
        body += '<p class="empty" id="noresults" hidden>Bu filtreyle eşleşen rapor yok.</p>'

    return (
        head(f"{SITE_NAME} — {SITE_TAGLINE}")
        + masthead(latest_news=latest_news)
        + f"""<main class="wrap">
  <div class="controls">
    <input class="search" id="q" type="search" placeholder="Ara: konu ya da tarih…" autocomplete="off">
    <button class="notify" type="button" id="notify" hidden aria-pressed="false">
      <svg class="notify-bell" viewBox="0 0 16 16" width="15" height="15" aria-hidden="true">
        <path d="M8 1.6a3.6 3.6 0 0 0-3.6 3.6c0 2.5-.5 3.7-1.1 4.5-.3.4 0 1 .5 1h8.4c.5 0 .8-.6.5-1-.6-.8-1.1-2-1.1-4.5A3.6 3.6 0 0 0 8 1.6Z"
              fill="none" stroke="currentColor" stroke-width="1.3" stroke-linejoin="round"/>
        <path d="M6.6 12.2a1.5 1.5 0 0 0 2.8 0" fill="none" stroke="currentColor" stroke-width="1.3" stroke-linecap="round"/>
      </svg>
      <span class="notify-label">Bildirimler</span>
    </button>
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
    latest_news = news_days[-1] if news_days else None

    reports = []
    for path in sorted(SRC.glob("*.md")):
        iso = path.stem
        try:
            meta, body = split_frontmatter(path.read_text(encoding="utf-8"))
        except Exception as exc:
            print(f"  ! skipped {path.name}: {exc}")
            continue

        developments = meta.get("developments") or []
        body_html = render_body(body, developments)
        (OUT / f"{iso}.html").write_text(
            build_report(meta, body_html, iso, news_days, latest_news), encoding="utf-8"
        )

        reports.append(
            {
                "date": iso,
                "title": meta.get("title", ""),
                "summary": meta.get("summary", ""),
                "alarm": bool(meta.get("alarm")),
                "alarm_title": meta.get("alarm_title", ""),
                "status": status_of(meta, iso),
                "decision_by": str(meta["decision_by"]) if meta.get("decision_by") else None,
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
            page = build_news_page(
                day, news[day],
                news_days[i - 1] if i else None,
                news_days[i + 1] if i + 1 < len(news_days) else None,
                day in report_days, latest_news,
            )
            (NEWS_OUT / f"{day}.html").write_text(page, encoding="utf-8")
            print(f"  · haberler/{day}.html ({news[day].get('unique_items', 0)} başlık)")

    (ROOT / "index.html").write_text(build_index(reports, version, latest_news), encoding="utf-8")
    (ROOT / ".nojekyll").touch()

    print(f"  · index.html  ({len(reports)} rapor)")
    print("  · data/reports.json")


if __name__ == "__main__":
    main()
