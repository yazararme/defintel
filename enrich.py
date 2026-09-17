"""Turn a rendered report into a cross-linked document.

The agent writes plain Markdown with three conventions:

    ### G1 · etiket                      a development, in GELİŞMELER
    - **G3 · Firma** — …                 a development, in RAKİP HAREKETLERİ
    - **G6 · etiket** — *durum.* …       a development, in İZLEME LİSTESİ
    - [K1] başlık — yayın, tarih — URL   a source

Everything here is derived from those: anchors (#g1, #k1), copy-link buttons,
citation links for G#, [K#], "bkz. EK" and "bkz. ALARMLAR", badges in the
opportunity/risk tables, a collapsed appendix and clickable source URLs.

Reports written before this convention simply have nothing to match, so every
step is a no-op and they keep rendering as they always did.
"""

import html
import re

COPY = (
    '<button class="copylink" type="button" data-anchor="{aid}"'
    ' title="Bağlantıyı kopyala" aria-label="Bağlantıyı kopyala">#</button>'
)
URL = re.compile(r"https?://[^\s<>\"]+")
SKIP_TAGS = {"a", "code", "pre", "button", "h3"}


def section_id(heading_text):
    t = heading_text.upper()
    if t.startswith("EK"):
        return "ek"
    if "ALARM" in t:
        return "alarmlar"
    return None


def add_heading_anchors(text):
    """### G1 · etiket  ->  <h3 id="g1"> + copy button, plus ids for EK/ALARMLAR."""

    def h3(m):
        gid = m.group(2).lower()
        return f'<h3 id="{gid}">{m.group(1)}{COPY.format(aid=gid)}</h3>'

    text = re.sub(r"<h3>((G(\d+))\s*·[^<]*)</h3>", h3, text)

    def h2(m):
        sid = section_id(re.sub(r"<[^>]+>", "", m.group(1)))
        return f'<h2 id="{sid}">{m.group(1)}</h2>' if sid else m.group(0)

    return re.sub(r"<h2>(.*?)</h2>", h2, text, flags=re.S)


def add_item_anchors(text):
    """- **G3 · Firma** — …  ->  <li id="g3"> + copy button."""

    def li(m):
        gid = m.group(1).lower()
        return (
            f'<li id="{gid}"><strong class="ganchor">{m.group(2)}</strong>'
            f"{COPY.format(aid=gid)}"
        )

    return re.sub(r"<li>\s*<strong>((?:G\d+))(\s*·[^<]*)</strong>", li, text)


def add_source_anchors(text):
    """- [K1] …  ->  <li id="k1">, links live, background sources dimmed."""

    def li(m):
        kid = "k" + m.group(1)
        return f'<li id="{kid}" class="source">[K{m.group(1)}]'

    text = re.sub(r"<li>\s*\[K(\d+)\]", li, text)

    def link(m):
        url = m.group(0).rstrip(".,;")
        tail = m.group(0)[len(url):]
        return (
            f'<a href="{html.escape(url, quote=True)}" target="_blank" rel="noopener">'
            f"{html.escape(url)}</a>{tail}"
        )

    text = URL.sub(link, text)
    return text.replace("(arka plan)", '<span class="background-tag">(arka plan)</span>')


def add_table_badges(text, dev_ids):
    """A leading "G1 — " in the first cell becomes a small badge linking to #g1."""

    def cell(m):
        gid = m.group(2)
        if gid.lower() not in dev_ids:
            return m.group(0)
        return (
            f'{m.group(1)}<a class="gbadge" href="#{gid.lower()}">{gid}</a> '
        )

    return re.sub(r"(<td[^>]*>)\s*(G\d+)\s*—\s*", cell, text)


def link_citations(text, dev_ids):
    """Link G# and [K#] mentions in running text only.

    Walks the markup instead of blind-replacing so that ids inside headings,
    anchors, badges and code are left alone.
    """
    out = []
    depth = {t: 0 for t in SKIP_TAGS}
    skip_anchor_label = False

    for token in re.split(r"(<[^>]+>)", text):
        if token.startswith("<") and token.endswith(">"):
            name = re.match(r"</?\s*([a-zA-Z0-9]+)", token)
            tag = name.group(1).lower() if name else ""
            if tag in SKIP_TAGS:
                depth[tag] += -1 if token.startswith("</") else 1
            if 'class="ganchor"' in token:
                skip_anchor_label = True
            elif token == "</strong>" and skip_anchor_label:
                skip_anchor_label = False
            out.append(token)
            continue

        if not token.strip() or any(depth.values()) or skip_anchor_label:
            out.append(token)
            continue

        def g(m):
            gid = m.group(0).lower()
            if gid not in dev_ids:
                return m.group(0)
            return f'<a class="xref" href="#{gid}">{m.group(0)}</a>'

        token = re.sub(r"\bG\d+\b", g, token)
        token = re.sub(
            r"\[K(\d+)\]",
            lambda m: f'<a class="xref" href="#k{m.group(1)}">[K{m.group(1)}]</a>',
            token,
        )
        token = re.sub(
            r"(bkz\. EK|EK'te|EK'de|EK'e)",
            lambda m: f'<a class="xref" href="#ek">{m.group(1)}</a>',
            token,
        )
        token = token.replace(
            "bkz. ALARMLAR", '<a class="xref" href="#alarmlar">bkz. ALARMLAR</a>'
        )
        out.append(token)

    return "".join(out)


def fold_appendix(text):
    """EK: Katılımcı listeleri — collapsed, with the count taken from its first (n)."""
    m = re.search(r'<h2 id="ek">(.*?)</h2>', text, re.S)
    if not m:
        return text
    rest = text[m.end():]
    label = re.sub(r"<[^>]+>", "", m.group(1)).strip()
    count = re.search(r"\((\d+)\)", rest)
    summary = f"{label} ({count.group(1)})" if count and "(" not in label else label
    return (
        text[: m.start()]
        + f'<details class="appendix" id="ek"><summary>{html.escape(summary)}</summary>'
        + rest
        + "</details>"
    )


def enrich(text, developments):
    dev_ids = {str(d.get("id", "")).lower() for d in developments if d.get("id")}
    text = add_heading_anchors(text)
    text = add_item_anchors(text)
    text = add_source_anchors(text)
    text = add_table_badges(text, dev_ids)
    text = link_citations(text, dev_ids)
    return fold_appendix(text)


def nav(developments):
    """The sticky chip strip: main developments open, other groups collapsed."""
    if not developments:
        return ""

    groups = {"gelismeler": [], "rakip": [], "izleme": []}
    for d in developments:
        gid = str(d.get("id", "")).strip()
        if not gid:
            continue
        home = str(d.get("home", "gelismeler")).strip().lower()
        if home not in groups:
            home = "gelismeler"
        label = str(d.get("label", "")).strip()
        if len(label) > 28:
            label = label[:27].rstrip() + "…"
        groups[home].append((gid, label))

    def chip(gid, label):
        text = f"{gid} · {label}" if label else gid
        return f'<a class="chip" href="#{gid.lower()}">{html.escape(text)}</a>'

    parts = [chip(*c) for c in groups["gelismeler"]]
    toggles = []
    for key, title in (("rakip", "Rakipler"), ("izleme", "İzleme")):
        if not groups[key]:
            continue
        # the toggle stays pinned on the right; its chips open inside the track
        toggles.append(
            f'<button class="chip chip--group" type="button" data-group="{key}"'
            f' aria-expanded="false">{title} +{len(groups[key])}</button>'
        )
        parts.append(
            f'<span class="chip-set" data-group="{key}" hidden>'
            + "".join(chip(*c) for c in groups[key])
            + "</span>"
        )

    if not parts and not toggles:
        return ""
    pinned = f'<div class="devnav-groups">{"".join(toggles)}</div>' if toggles else ""
    return (
        '<nav class="devnav" id="devnav" aria-label="Gelişmeler">'
        '<div class="devnav-track">' + "".join(parts) + "</div>" + pinned + "</nav>"
    )
