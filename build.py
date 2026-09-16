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
SITE_TAGLINE = "MKE stratejik pazar istihbaratı"
# Push service (Cloudflare Worker). Empty string hides the notification button.
PUSH_ENDPOINT = "https://defintel-push.yazararme-c30.workers.dev"
VAPID_PUBLIC_KEY = "BLOHxsm23_gz-DmV0E9xyB3RVQTkCwv06uPv_pme7VApr61x_gnNGGPkTnEI3mNekR7lzZGxNL9hATzaaOYsEZo"

TR_MONTHS = [
    "Ocak", "Şubat", "Mart", "Nisan", "Mayıs", "Haziran",
    "Temmuz", "Ağustos", "Eylül", "Ekim", "Kasım", "Aralık",
]
TR_DAYS = ["Pazartesi", "Salı", "Çarşamba", "Perşembe", "Cuma", "Cumartesi", "Pazar"]

# Three reading states, derived from front matter the agent already writes:
#   alarm: true                  -> alarm  (something fired)
#   a deadline still ahead of us -> izle   (watch it)
#   neither                      -> temiz  (nothing pending)
STATUS_LABEL = {"alarm": "Alarm", "izle": "İzle", "temiz": "Temiz"}


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


def status_note(meta, iso, status):
    if status == "alarm":
        return meta.get("alarm_title") or "Alarm eşiğini aşan gelişme var"
    if status == "izle":
        return f"Açık dış son tarih: {tr_short(meta['decision_by'])}"
    return "Alarm eşiğini aşan gelişme yok"


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


def render_body(md_text):
    md = markdown.Markdown(extensions=["tables", "fenced_code", "attr_list", "sane_lists"])
    out = md.convert(md_text)
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
<link rel="icon" type="image/svg+xml" href="{up}{asset("icons/favicon.svg")}">
<link rel="icon" type="image/png" sizes="32x32" href="{up}{asset("icons/favicon-32.png")}">
<link rel="icon" type="image/png" sizes="16x16" href="{up}{asset("icons/favicon-16.png")}">
<link rel="apple-touch-icon" sizes="180x180" href="{up}{asset("icons/apple-touch-icon.png")}">
<link rel="manifest" href="{up}manifest.webmanifest">
<meta name="theme-color" content="#17171A">
<meta name="apple-mobile-web-app-title" content="{SITE_NAME}">
<meta name="mobile-web-app-capable" content="yes">
<meta name="apple-mobile-web-app-capable" content="yes">
<script>if ("serviceWorker" in navigator) navigator.serviceWorker.register("{up}sw.js");</script>
</head>
<body>
"""


def masthead(up=""):
    return f"""<header class="masthead">
  <div class="wrap masthead-inner">
    <a class="wordmark" href="{up}index.html">{SITE_NAME}</a>
    <span class="tagline">{SITE_TAGLINE}</span>
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


def status_mark(status, extra=""):
    cls = f"status status--{status}" + (f" {extra}" if extra else "")
    return (
        f'<span class="{cls}"><span class="dot" aria-hidden="true"></span>'
        f"{STATUS_LABEL[status]}</span>"
    )


def tag_list(tags, cls="tags"):
    if not tags:
        return ""
    items = "".join(f"<span>{html.escape(str(t))}</span>" for t in tags)
    return f'<div class="{cls}">{items}</div>'


def build_report(meta, body_html, iso):
    title = meta.get("title") or f"{tr_date(iso)} raporu"
    status = status_of(meta, iso)

    rail = [
        '<div class="rail-block"><span class="rail-label">Tarih</span>'
        f'<span class="rail-value num">{tr_date(iso, weekday=True)}</span></div>'
    ]
    rail.append(
        '<div class="rail-block"><span class="rail-label">Durum</span>'
        f"{status_mark(status)}</div>"
    )
    if meta.get("tags"):
        rail.append(
            '<div class="rail-block"><span class="rail-label">Etiketler</span>'
            f'{tag_list(meta["tags"], "tags tags--stack")}</div>'
        )

    return (
        head(f"{title} — {SITE_NAME}", depth=1)
        + masthead(up="../")
        + f"""<main class="wrap report">
  <a class="backlink" href="../index.html">← Tüm raporlar</a>
  <div class="report-grid">
    <aside class="rail">{''.join(rail)}</aside>
    <article class="column">
      <h1 class="report-title">{html.escape(title)}</h1>
      <div class="statusbar statusbar--{status}">
        {status_mark(status)}
        <span class="statusbar-note">{html.escape(status_note(meta, iso, status))}</span>
      </div>
      <div class="prose">
{body_html}
      </div>
    </article>
  </div>
</main>
"""
        + FOOT
    )


def entry_html(r):
    rail = [
        f'<time class="datestamp num">{tr_date(r["date"])}</time>',
        status_mark(r["status"]),
    ]

    haystack = " ".join(
        [r["date"], r.get("title", ""), r.get("summary", "")] + [str(t) for t in r.get("tags", [])]
    ).lower()

    return f"""<a class="entry" href="{r['path']}"
   data-tags="{html.escape('|'.join(str(t) for t in r.get('tags', [])))}"
   data-search="{html.escape(haystack)}">
  <div class="entry-rail">{''.join(rail)}</div>
  <div class="entry-main">
    <h2 class="entry-title">{html.escape(r.get('title', ''))}</h2>
    <p class="entry-summary">{html.escape(r.get('summary', ''))}</p>
    {tag_list(r.get('tags', []))}
  </div>
</a>"""


def build_index(reports, version):
    if not reports:
        body = '<p class="empty">Henüz rapor yok.</p>'
        tagbar = ""
    else:
        all_tags = sorted({str(t) for r in reports for t in r.get("tags", [])})
        tagbar = (
            '<nav class="tagbar" id="tagbar" aria-label="Etikete göre süz">'
            + "".join(
                f'<button class="tag" type="button" aria-pressed="false" '
                f'data-tag="{html.escape(t)}">{html.escape(t)}</button>'
                for t in all_tags
            )
            + "</nav>"
        )
        lead, rest = reports[0], reports[1:]
        body = '<h2 class="kicker">Son rapor</h2><div class="feed">' + entry_html(lead) + "</div>"
        if rest:
            body += (
                '<h2 class="kicker">Arşiv</h2><div class="feed">'
                + "".join(entry_html(r) for r in rest)
                + "</div>"
            )
        body += '<p class="empty" id="noresults" hidden>Bu filtreyle eşleşen rapor yok.</p>'

    return (
        head(f"{SITE_NAME} — {SITE_TAGLINE}")
        + masthead()
        + f"""<main class="wrap">
  <div class="controls">
    <input class="search" id="q" type="search" placeholder="Ara: konu, tarih, etiket…" autocomplete="off">
    <button class="notify" type="button" id="notify" hidden aria-pressed="false"
            data-push="{PUSH_ENDPOINT}" data-vapid="{VAPID_PUBLIC_KEY}">
      <svg class="notify-bell" viewBox="0 0 16 16" width="15" height="15" aria-hidden="true">
        <path d="M8 1.6a3.6 3.6 0 0 0-3.6 3.6c0 2.5-.5 3.7-1.1 4.5-.3.4 0 1 .5 1h8.4c.5 0 .8-.6.5-1-.6-.8-1.1-2-1.1-4.5A3.6 3.6 0 0 0 8 1.6Z"
              fill="none" stroke="currentColor" stroke-width="1.3" stroke-linejoin="round"/>
        <path d="M6.6 12.2a1.5 1.5 0 0 0 2.8 0" fill="none" stroke="currentColor" stroke-width="1.3" stroke-linecap="round"/>
      </svg>
      <span class="notify-label">Bildirimler</span>
    </button>
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
<script src="{asset("app.js")}" defer></script>
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
        (OUT / f"{iso}.html").write_text(build_report(meta, body_html, iso), encoding="utf-8")

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
    print("  · data/reports.json")


if __name__ == "__main__":
    main()
