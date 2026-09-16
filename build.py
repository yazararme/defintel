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

try:
    import markdown
    import yaml
except ImportError:
    sys.exit("missing deps: pip install markdown pyyaml --break-system-packages")

ROOT = pathlib.Path(__file__).parent
SRC = ROOT / "source"
OUT = ROOT / "reports"
DATA = ROOT / "data"

SITE_NAME = "DEFINTEL"
# Push service (Cloudflare Worker). Empty string hides the notification button.
PUSH_ENDPOINT = ""
VAPID_PUBLIC_KEY = "BLOHxsm23_gz-DmV0E9xyB3RVQTkCwv06uPv_pme7VApr61x_gnNGGPkTnEI3mNekR7lzZGxNL9hATzaaOYsEZo"
SITE_TAGLINE = "MKE stratejik pazar istihbaratı · günlük tarama"

TR_MONTHS = [
    "Ocak", "Şubat", "Mart", "Nisan", "Mayıs", "Haziran",
    "Temmuz", "Ağustos", "Eylül", "Ekim", "Kasım", "Aralık",
]
TR_DAYS = ["Pazartesi", "Salı", "Çarşamba", "Perşembe", "Cuma", "Cumartesi", "Pazar"]


def tr_date(iso, weekday=False):
    """2026-09-14 -> '14 Eylül 2026' (optionally with weekday)."""
    import datetime
    d = datetime.date.fromisoformat(str(iso))
    s = f"{d.day} {TR_MONTHS[d.month - 1]} {d.year}"
    return f"{s}, {TR_DAYS[d.weekday()]}" if weekday else s


def tr_short(iso):
    import datetime
    d = datetime.date.fromisoformat(str(iso))
    return f"{d.day} {TR_MONTHS[d.month - 1]}"


def split_frontmatter(text):
    if not text.startswith("---"):
        raise ValueError("no frontmatter")
    _, fm, body = text.split("---", 2)
    return yaml.safe_load(fm) or {}, body.lstrip("\n")


def render_body(md_text):
    md = markdown.Markdown(extensions=["tables", "fenced_code", "attr_list", "sane_lists"])
    out = md.convert(md_text)
    # tables need a horizontal scroll container on narrow screens
    out = out.replace("<table>", '<div class="table-scroll"><table>')
    out = out.replace("</table>", "</table></div>")
    # wrap the alarm section so it reads as a callout
    out = re.sub(
        r'(<h2[^>]*>\s*(?:⚠️\s*)?ALARM.*?)(?=<h2|$)',
        r'<div class="alarm-block">\1</div>',
        out,
        count=1,
        flags=re.S | re.I,
    )
    return out


def head(title, depth=0, stat=""):
    up = "../" * depth
    stat_html = f'<span class="masthead-right">{html.escape(stat)}</span>' if stat else ""
    return f"""<!DOCTYPE html>
<html lang="tr">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="robots" content="noindex, nofollow">
<title>{html.escape(title)}</title>
<link rel="stylesheet" href="{up}assets/app.css">
<link rel="icon" type="image/png" sizes="32x32" href="{up}assets/icons/favicon-32.png">
<link rel="apple-touch-icon" href="{up}assets/icons/apple-touch-icon.png">
<link rel="manifest" href="{up}manifest.webmanifest">
<meta name="theme-color" content="#17171A">
<meta name="apple-mobile-web-app-title" content="{SITE_NAME}">
<meta name="mobile-web-app-capable" content="yes">
<meta name="apple-mobile-web-app-capable" content="yes">
<script>if ("serviceWorker" in navigator) navigator.serviceWorker.register("{up}sw.js");</script>
</head>
<body>
<header class="masthead">
  <div class="wrap">
    <a class="wordmark" href="{up}index.html">{SITE_NAME}</a>
    <span class="tagline">{SITE_TAGLINE}</span>
    {stat_html}
  </div>
</header>
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


def build_report(meta, body_html, iso):
    title = meta.get("title") or f"{tr_date(iso)} raporu"
    bits = [f'<span class="datestamp">{tr_date(iso, weekday=True)}</span>']
    if meta.get("alarm"):
        bits.append('<span class="pill pill--alarm">Alarm</span>')
    else:
        bits.append('<span class="pill">Alarm yok</span>')
    if meta.get("decision_by"):
        bits.append(
            f'<span class="pill pill--decision">Karar: {tr_short(meta["decision_by"])}</span>'
        )

    tags = "".join(f"<span>{html.escape(str(t))}</span>" for t in meta.get("tags", []))
    tags = f'<div class="entry-tags report-tags">{tags}</div>' if tags else ""

    return (
        head(f"{title} — {SITE_NAME}", depth=1)
        + f"""<main class="wrap">
  <div class="report-head">
    <a class="backlink" href="../index.html">← Tüm raporlar</a>
    <h1 class="report-title">{html.escape(title)}</h1>
    <div class="report-meta">{''.join(bits)}</div>
    {tags}
  </div>
  <article class="prose">
{body_html}
  </article>
</main>
"""
        + FOOT
    )


def entry_html(r, lead=False):
    cls = "entry"
    if r["alarm"]:
        cls += " entry--alarm"
    elif lead:
        cls += " entry--lead"
    if lead:
        cls += " entry--lead"

    meta = [f'<span class="datestamp">{tr_date(r["date"])}</span>']
    if r["alarm"]:
        meta.append('<span class="pill pill--alarm">Alarm</span>')
    if r.get("decision_by"):
        meta.append(
            f'<span class="pill pill--decision">Karar: {tr_short(r["decision_by"])}</span>'
        )

    tags = "".join(f"<span>{html.escape(str(t))}</span>" for t in r.get("tags", []))
    tags = f'<div class="entry-tags">{tags}</div>' if tags else ""

    haystack = " ".join(
        [r["date"], r.get("title", ""), r.get("summary", "")] + [str(t) for t in r.get("tags", [])]
    ).lower()

    return f"""<a class="{cls}" href="{r['path']}"
   data-tags="{html.escape('|'.join(str(t) for t in r.get('tags', [])))}"
   data-search="{html.escape(haystack)}">
  <div class="entry-meta">{''.join(meta)}</div>
  <h2 class="entry-title">{html.escape(r.get('title', ''))}</h2>
  <p class="entry-summary">{html.escape(r.get('summary', ''))}</p>
  {tags}
</a>"""


def build_index(reports, version):
    if not reports:
        body = '<div class="empty">Henüz rapor yok.</div>'
        tagbar = ""
    else:
        lead, rest = reports[0], reports[1:]
        all_tags = sorted({str(t) for r in reports for t in r.get("tags", [])})
        tagbar = (
            '<div class="tagbar" id="tagbar">'
            + "".join(
                f'<button class="tag" type="button" aria-pressed="false" data-tag="{html.escape(t)}">{html.escape(t)}</button>'
                for t in all_tags
            )
            + "</div>"
        )
        body = (
            '<div class="section-label">Son rapor</div>'
            + entry_html(lead, lead=True)
        )
        if rest:
            body += '<div class="section-label">Arşiv</div>' + "".join(
                entry_html(r) for r in rest
            )
        body += '<div class="empty" id="noresults" hidden>Bu filtreyle eşleşen rapor yok.</div>'

    alarm_days = sum(1 for r in reports if r["alarm"])
    stat = (
        f"{len(reports)} rapor · {alarm_days} alarm günü"
        if reports
        else "arşiv boş"
    )

    return (
        head(f"{SITE_NAME} — {SITE_TAGLINE}", stat=stat)
        + f"""<main class="wrap">
  <div class="controls">
    <input class="search" id="q" type="search" placeholder="Ara: konu, tarih, etiket…" autocomplete="off">
    <button class="tag notify" type="button" id="notify" hidden
            data-push="{PUSH_ENDPOINT}" data-vapid="{VAPID_PUBLIC_KEY}">Bildirimleri aç</button>
  </div>
  {tagbar}
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
<script src="assets/app.js" defer></script>
"""
        + FOOT
    )


def main():
    OUT.mkdir(exist_ok=True)
    DATA.mkdir(exist_ok=True)
    SRC.mkdir(exist_ok=True)

    reports = []
    for path in sorted(SRC.glob("*.md")):
        iso = path.stem
        try:
            meta, body = split_frontmatter(path.read_text(encoding="utf-8"))
        except Exception as exc:
            print(f"  ! skipped {path.name}: {exc}")
            continue

        body_html = render_body(body)
        target = OUT / f"{iso}.html"
        target.write_text(build_report(meta, body_html, iso), encoding="utf-8")

        reports.append(
            {
                "date": iso,
                "title": meta.get("title", ""),
                "summary": meta.get("summary", ""),
                "alarm": bool(meta.get("alarm")),
                "alarm_title": meta.get("alarm_title", ""),
                "decision_by": str(meta["decision_by"]) if meta.get("decision_by") else None,
                "tags": [str(t) for t in meta.get("tags", [])],
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
    (ROOT / "index.html").write_text(build_index(reports, version), encoding="utf-8")
    (ROOT / ".nojekyll").touch()

    print(f"  · index.html  ({len(reports)} rapor)")
    print(f"  · data/reports.json")


if __name__ == "__main__":
    main()
