"""Smoke test: build, then the served site answers.

  python3 review/tools/smoke.py

Runs `python3 build.py`, then checks that the main pages and every top-level
/data/*.json answer 200 from http://localhost:8000 (python -m http.server from
the repo root) and that the key HTML files are non-empty. stdlib only; the Rev 22
DÖRT-DURUM and scope-line checks, and the Rev 21 KAPSAM-SAYI checks (64/64 state, then a
KAPSAM_BOZ=thales build for the <64 state, then a normal rebuild), need a Playwright python
(DEFINTEL_PW_PYTHON or ~/.local/share/defintel-shotenv/bin/python).
Rev 23: ETİKET-BAŞLIK · KUR · H1-TEKRAR — the build's alert lines for the day's report,
static label/heading equality on the latest report, rule controls on synthetic input, and a
1440px click-through from the watch list's "→ bugün:" link to its heading (Playwright).
Rev 31: GEÇ-GELEN — scripts/test_collect.py (offline twice-collect), the build's token-count
line, a 375px check that the AA row on /haberler/2026-09-23.html?oyuncu=roketsan carries
"BRİFİNGDEN SONRA" in --muted (never with BRİFİNGDE), and, when the local-only
data/news/2026-09-24-aday.md exists, that its first section is "Dünkü brifingden sonra gelenler"
and holds the AA row.
Rev 33: NOKTALI-İ — the build's "NOKTALI-İ: 0 örnek" line, src_name() unit cases, a 1440px
Turkish-locale check of the latest media page (Öne çıkanlar shows "UNMANNED AIRSPACE" and "DEFENSE
DAILY" with dotless I, "ANADOLU AJANSI" unchanged, no foreign source name rendered with İ anywhere
in .clip-meta) and of its Kaynaklar page; then a NOKTALI_BOZ=1 build (the alert fires with
examples, the browser shows "UNMANNED AİRSPACE") and a normal rebuild.
Rev 28 (attempt 2): KANIT-BOŞLUĞU empty intersection — `check_reports.py --kanit-boslugu` is
green on the normal build (line present, matches the record), then a BOS_KESISIM=1 build (player
feeds counted as answered in memory only): the latest day logs "kesişim boş (…)", no alert, no
.rail-not on its report or /, the previous day keeps its line, data/news/<day>.json is unchanged,
and `--kanit-boslugu` is green in that state too; then a normal rebuild.
Rev 24: İLK-EKRAN — every built report carries one data-kart="İzlenecek" cell per table row;
`check_reports.py --ilk-ekran` on the latest report is green (edges printed), and with
ILK_EKRAN_BOZ=1 (rail order undone in the browser only) it is red and emits the İLK-EKRAN alert;
a browser pass over every report at 375×812 and 1440×900, light and dark: at 375 the rail sits
after the summary list and before h2#portfoy, the chip strip is one row, each card's third field
shows "İZLENECEK" above it, no horizontal overflow; at 1440 the rail is in the left column,
level with the top of the article, and no card label shows.
Rev 32: TEKRAR-MANŞET — the build's per-report "ilk:" tokens and its TEKRAR-MANŞET line (on the
23 Sep build: summary item 1 "ilk: 19 Eyl" → 19 Sep G1, alert "TEKRAR-MANŞET: 23 Eyl H1 ↔ 19 Eyl"),
rule controls on synthetic input (shared URL → match; two shared proper nouns + overlap ≥0,4 →
match; one proper noun, dictionary words only, or another development → no match), and a 375×812
touch pass on /reports/2026-09-23.html and /: the token ends summary item 1, is mono and --muted,
one piece, its tap area is ≥44px high, the page does not scroll sideways, and tapping it lands on
/reports/2026-09-19.html#g1 with the Latvia heading in view.
Rev 32 (attempt 2): İLK-EKRAN worst case — CI (Ubuntu Chromium) breaks lines wider than macOS
Chrome, so on 23 Sep the token fell onto a line of its own there (item 4 at 817px). At 375×812 the
latest report is measured with every summary "ilk:" token forced onto its own line (a <br> before
it), bare and with 0.15px letter-spacing on the title and summary (which reproduces CI's wrap on
23 Sep); h2#ozet top must stay ≤300 and item 4's bottom ≤812 in every variant.
K2: two player lists, two labels — at 375×812 and 1440×900, light and dark, the latest report's
Oyuncular rail block carries "brifingde geçen" (mono, --muted, before the names) and the
/oyuncular.html top line reads "Bugün N başlıklarda geçen · son 30 günde N · izlenen N" with the
label right after the day's number, also with the Mühimmat chip on; every rail name links to a
#g anchor (briefing-body matches only) and "Bugün N" equals the day's headline-matched players; in the KAPSAM_BOZ=thales state
the top line is only "izlenen N" and "başlıklarda geçen" appears nowhere.
Rev 25: SİLME-YOK · İPUCU-YOK — scripts/test_silme_yok.py (offline collection over the nine
filter-noted sources: read == written; a deliberately broken run exits red with the alert), the
build's "İPUCU-YOK / S8" line for the latest day (hint-only 0), the offline re-categorisation of
23 Sep already applied (a dry run changes 0 items), summary scope and Öne çıkanlar never take a
`savunma_terimi: false` item, and a 375×812 / 1440×900 pass over /haberler/2026-09-23.html: rail
and chips say "Oyuncu Duyuruları", "Rakip Duyuruları" appears nowhere (text, HTML, or the address
bar after the rail click), C-UAS has no Tournai, Zipline or DroneXL row, İhale no Greenland row,
the Hanwha munitions-investment row is under Oyuncu Duyuruları, and a Genel full-dump title is
found by search.
Rev 27: İPLİK-DURUM — the build's "İPLİK-DURUM: 0 eksik" line, watch_status() unit cases, a
375×812 / 1440×900 pass: from /reports/2026-09-23.html the XM30 thread link opens with ?g=2026-09-23,
the daybar reads "23 Eyl · Çar", the status line under the h1 reads "Prototip teslim edildi, şart hâlâ
tanımlı değil. · 23 Eylül", 4 underlined link rows plus an unlinked, not-underlined "AÇILDI" opening
row; a thread opened from 20 Sep shows "20 Eyl · Paz" with both arrows live; an unknown ?g= leaves the
default day; then an IPLIK_BOZ=1 build (the alert fires) and a normal rebuild.
Rev 29: L1-DOLGU · ÇİZGİ-KONTRAST · bildirim kartı — the build's "L1-DOLGU: 0 ihlal" line and its
ÇİZGİ-KONTRAST line (--rule-2 / --paper ≥3:1 in both themes); rule controls on mutated app.css (the
summary box's old brand edge, an edge added by a longer selector or a :hover, and Rev 0's --rule-2
values each fire exactly their alert through uyari.ekle; a four-sided `border:` box does not); a
browser pass over the latest report and media page at 375×812 and 1440×900, light and dark (the
summary box has no left edge and a --paper-2 ground, no element with a --paper/--paper-2 ground has a
left border, the rule over each section heading is ≥3:1 against the page); and a first visit (clean
storage, service workers ALLOWED, 375×812) on the latest report: the notification card is in the
flow right above .endnav, the footer bell is visible and hit-testable while it is open and still
after the install bar appears, and "Şimdi değil" hides it for the next load.
Rev 28: KANIT-BOŞLUĞU — the build's "KANIT-BOŞLUĞU <gün>:" line (on the 23 Sep build: the sentence
"Elbit Systems ve Northrop Grumman'ın kendi duyuruları bugün okunamadı." and one alert naming both
sources), static checks over every built report (the .rail-not line is present exactly on the days
whose failures[] ∩ rakipler.json `kaynak` is non-empty, absent on days without a sweep), no
"yanıt vermedi" on any Kaynaklar page and "oyuncu: Elbit" / "oyuncu: Northrop Grumman" beside those
rows, rule controls on synthetic input (an empty intersection → no line and no alert; one player → one
line with the right genitive and one alert; the rail carries the line only when given), and a 375×812
pass: on /reports/2026-09-23.html and / the line sits directly under the Tarama row, --ink-2 mono, once
per page, no sideways scroll; the first report (no sweep) has none; the Kaynaklar page shows no
"yanıt vermedi".
Rev 26: ÇEVİRİ-DEDEKTÖRÜ — scripts/test_ceviri_dedektoru.py (no model call: the fixed test over
content.md §2's 16 defective items with today's translations must catch at least 7, plus the
retry/fallback flow with an injected fake translator and the CLI with --sahte-cevirmen: >10 left
original → alert, exactly 10 → none); the prompt is sentence case and carries Ö1/Ö2/Ö3; the
evidence workflow ceviri-dedektoru-test.yml has no secret, no Claude CLI install and no --refresh.
Later revisions extend CHECKS / PAGES. Exit 1 on any failure.
"""
import os
import pathlib
import re
import subprocess
import sys
import urllib.request

ROOT = pathlib.Path(__file__).resolve().parents[2]
BASE = "http://localhost:8000"


def latest(folder, pattern):
    files = sorted((ROOT / folder).glob(pattern))
    return f"/{folder}/{files[-1].name}" if files else None


def pw_python():
    """Playwright'lı bir python: DEFINTEL_PW_PYTHON, yerel shotenv ya da bu süreç."""
    for cand in (os.environ.get("DEFINTEL_PW_PYTHON"),
                 str(pathlib.Path.home() / ".local/share/defintel-shotenv/bin/python"),
                 sys.executable):
        if cand and pathlib.Path(cand).exists() and subprocess.run(
                [cand, "-c", "import playwright"], capture_output=True).returncode == 0:
            return cand
    return None


# Rev 22 R22-P1-2 + K1: ?oyuncu=<kimlik> ile kapsam satırı "{görünen benzersiz} / {toplam} başlık" olur,
# süzgeç kalkınca "{toplam} başlık"a döner. Kimlik sayfadaki ilk data-oyuncu'dan.
KAPSAM_JS = r"""
import re, sys
from playwright.sync_api import sync_playwright
url = sys.argv[1]
html = open(sys.argv[2], encoding="utf-8").read()
who = re.search(r'data-oyuncu="([^" ]+)', html).group(1)
# Görünen benzersiz başlık: satırın ilk bağlantısı başlığın kimliği (K1).
TEKIL = ("new Set(Array.from(document.querySelectorAll('[data-search]')).filter(e => !e.hidden)"
         ".map(e => { const a = e.querySelector('a[href]'); return a ? a.getAttribute('href')"
         " : e.getAttribute('data-search'); })).size")
with sync_playwright() as p:
    try: b = p.chromium.launch()
    except Exception: b = p.chromium.launch(channel="chrome")
    pg = b.new_context(service_workers="block").new_page()
    pg.goto(url + "?oyuncu=" + who); pg.wait_for_timeout(600)
    on = pg.inner_text(".news-stat > .num")
    gorunen = pg.evaluate(TEKIL)
    roket = None
    if 'roketsan' in html:
        pg.goto(url + "?oyuncu=roketsan"); pg.wait_for_timeout(600)
        roket = pg.inner_text(".news-stat > .num")
        pg.goto(url + "?oyuncu=" + who); pg.wait_for_timeout(600)
    pg.click(".pill-x"); pg.wait_for_timeout(200)
    off = pg.inner_text(".news-stat > .num")
    # K1: süzgeçsiz sayfada neredeyse bütün satırları eşleyen arama — pay yine paydayı aşmaz.
    pg.fill("#q", "a"); pg.wait_for_timeout(300)
    genis = pg.inner_text(".news-stat > .num")
    genis_tekil = pg.evaluate(TEKIL)
    b.close()
ok = re.fullmatch(r"\d+ / \d+", on) and re.fullmatch(r"\d+", off) and on.endswith("/ " + off)
# Pay = görünen benzersiz başlık (K1, Rev 22 deneme 2'nin satır sayısı yerine);
# roketsan kabulü "1 / {toplam}"; pay hiçbir süzgeçte paydayı aşmaz.
ok = ok and on.split(" / ")[0] == str(gorunen)
ok = ok and genis.split(" / ")[0] == str(genis_tekil)
for s_ in (on, genis) + ((roket,) if roket else ()):
    ok = ok and bool(re.fullmatch(r"\d+ / \d+", s_)) and int(s_.split(" / ")[0]) <= int(off)
if roket is not None:
    ok = ok and roket == "1 / " + off
print(f"{who}: '{on} başlık' (görünen benzersiz {gorunen}) → × → '{off} başlık'"
      + f" · 'a' araması: '{genis} başlık' (pay ≤ payda)"
      + (f" · roketsan: '{roket} başlık'" if roket is not None else ""))
sys.exit(0 if ok else 1)
"""


# Rev 21 KAPSAM-SAYI: <64 hâlinde (KAPSAM_BOZ=thales ile üretilir) üst satır "izlenen 64",
# satırlarda sayı/jeton yok, ilk iki satır Anduril, Arsenal Bulgaria; "Mühimmat" çipi
# üst satırı "izlenen {o segmentteki sayı}" yapar. Ayrıca ?oyuncu=thales ≥1 kupür satırı.
KAPSAM_SAYI_JS = r"""
import json, re, sys
from playwright.sync_api import sync_playwright
base, root, kupur = sys.argv[1], sys.argv[2], sys.argv[3]
cfg = json.load(open(root + "/data/rakipler.json", encoding="utf-8"))["rakipler"]
muh = sum(1 for r in cfg if "muhimmat" in (r.get("segments") or []))
with sync_playwright() as p:
    try: b = p.chromium.launch()
    except Exception: b = p.chromium.launch(channel="chrome")
    pg = b.new_context(service_workers="block", viewport={"width": 375, "height": 812}).new_page()
    pg.goto(base + "/oyuncular.html"); pg.wait_for_timeout(300)
    tally = " ".join(pg.inner_text("#ptally").split())
    rows = pg.eval_on_selector_all(".player-row", "els => els.map(e => e.innerText)")
    names = pg.eval_on_selector_all(".player-row .pname", "els => els.map(e => e.innerText)")
    pg.click('.pchip[data-seg="muhimmat"]'); pg.wait_for_timeout(200)
    tally_m = " ".join(pg.inner_text("#ptally").split())
    pg.goto(base + kupur + "?oyuncu=thales"); pg.wait_for_timeout(600)
    thales = pg.evaluate("Array.from(document.querySelectorAll('[data-search]')).filter(e => !e.hidden && e.offsetParent !== null).length")
    b.close()
sayili = [r for r in rows if re.search(r"\d+ gün|önce|bugün|dün|kez", r)]
ok = (tally == f"izlenen {len(cfg)}" and not sayili and names[:2] == ["Anduril", "Arsenal Bulgaria"]
      and tally_m == f"izlenen {muh}" and thales >= 1)
print(f"<64: '{tally}' · sayılı satır {len(sayili)} · ilk iki {names[:2]} · Mühimmat → '{tally_m}' (beklenen {muh})"
      f" · ?oyuncu=thales {thales} satır")
sys.exit(0 if ok else 1)
"""


# K2 (S): iki oyuncu listesi, iki etiket — 375×812 ve 1440×900, açık/koyu. Brifing rayının
# Oyuncular bloğunda "brifingde geçen"; /oyuncular.html üst satırında günlük sayının hemen
# arkasında "başlıklarda geçen" (Mühimmat çipi açıkken de, sayı yeniden sayılmış hâlde). İkisi de
# mono ve --muted (rayda .rail-label'la aynı aile ve renk; sayfada .kicker'ın ailesi, --muted üst satırın rengi). argv: base,
# rapor yolu, hâl ("tam" | "boz"). "boz" (<64): üst satır yalnız "izlenen N", "başlıklarda geçen"
# hiçbir yerde yok; rayın etiketi durur.
K2_JS = r"""
import re, sys
from playwright.sync_api import sync_playwright
base, rapor, hal = sys.argv[1], sys.argv[2], sys.argv[3]
beklenen = int(sys.argv[4]) if len(sys.argv) > 4 else None
RAY = r'''() => {
  const lab = [...document.querySelectorAll('.rail-label')].find(e => e.textContent.trim() === 'Oyuncular');
  if (!lab) return null;
  const blok = lab.closest('.rail-block'), src = blok.querySelector('.rail-src');
  const r = src && src.getBoundingClientRect(), cs = src && getComputedStyle(src), ls = getComputedStyle(lab);
  const val = blok.querySelector('.rail-value');
  return {text: src ? src.innerText.trim() : '', gorunur: !!r && r.width > 0 && r.height > 0,
          mono: !!cs && cs.fontFamily === ls.fontFamily, renk: !!cs && cs.color === ls.color,
          once: !!src && !!val && (src.compareDocumentPosition(val) & 4) > 0,
          adlar: [...val.querySelectorAll('a:not(.rival-count)')].map(a => a.getAttribute('href')),
          tasma: document.documentElement.scrollWidth > innerWidth};
}'''
TALLY = r'''() => {
  const t = document.getElementById('ptally'), src = t.querySelector('.tally-src');
  const kick = getComputedStyle(document.querySelector('.kicker'));
  const cs = src && getComputedStyle(src);
  const bugun = t.querySelector('[data-tally="today"]');
  return {metin: t.innerText.replace(/\s+/g, ' ').trim(), src: src ? src.innerText.trim() : '',
          bitisik: !!src && !!bugun && bugun.nextElementSibling === src,
          mono: !!cs && cs.fontFamily === kick.fontFamily, renk: !!cs && cs.color === getComputedStyle(t).color,
          heryerde: document.body.innerText.includes('başlıklarda geçen'),
          tasma: document.documentElement.scrollWidth > innerWidth};
}'''
ok, out = True, []
with sync_playwright() as p:
    try: b = p.chromium.launch()
    except Exception: b = p.chromium.launch(channel="chrome")
    for w, h in ((375, 812), (1440, 900)):
        for tema in ("light", "dark"):
            pg = b.new_context(service_workers="block", viewport={"width": w, "height": h},
                               color_scheme=tema).new_page()
            pg.goto(base + rapor); pg.wait_for_timeout(300)
            r = pg.evaluate(RAY)
            k = (bool(r) and r["text"] == "brifingde geçen" and r["gorunur"] and r["mono"] and r["renk"]
                 and r["once"] and not r["tasma"] and all(h.startswith("#g") for h in r["adlar"]))
            pg.goto(base + "/oyuncular.html"); pg.wait_for_timeout(300)
            t = pg.evaluate(TALLY)
            pg.click('.pchip[data-seg="muhimmat"]'); pg.wait_for_timeout(200)
            tm = pg.evaluate(TALLY)
            if hal == "tam":
                rx = r"Bugün \d+ başlıklarda geçen · son 30 günde \d+ · izlenen \d+"
                k2 = (all(re.fullmatch(rx, x["metin"]) and x["src"] == "başlıklarda geçen" and x["bitisik"]
                          and x["mono"] and x["renk"] and not x["tasma"] for x in (t, tm))
                      and t["metin"] != tm["metin"]
                      and (beklenen is None or t["metin"].startswith(f"Bugün {beklenen} ")))
            else:
                k2 = all(re.fullmatch(r"izlenen \d+", x["metin"]) and not x["src"] and not x["heryerde"]
                         for x in (t, tm))
            ok = ok and k and k2
            out.append(f"{w}/{tema}: ray {len(r['adlar']) if r else 0} ad, hepsi #g {'✓' if k else '✗ ' + str(r)} · üst satır {'✓' if k2 else '✗ ' + str(t)}"
                       f" '{t['metin']}' → Mühimmat '{tm['metin']}'")
            pg.close()
    b.close()
print(" | ".join(out[::2]) if ok else "\n".join(out))
sys.exit(0 if ok else 1)
"""


# Rev 23 R23-P0-1 (S): 1440px, izleme listesindeki "→ bugün:" bağlantısı indiği başlığa eşit.
ETIKET_JS = r"""
import sys
from playwright.sync_api import sync_playwright
url, gid = sys.argv[1], sys.argv[2]
with sync_playwright() as p:
    try: b = p.chromium.launch()
    except Exception: b = p.chromium.launch(channel="chrome")
    pg = b.new_context(service_workers="block", viewport={"width": 1440, "height": 900}).new_page()
    pg.goto(url); pg.wait_for_timeout(400)
    link = pg.locator(f'li.watch-move a.xref[href="#{gid}"]').first
    metin = link.inner_text().strip()
    link.click(); pg.wait_for_timeout(400)
    baslik = pg.evaluate(f"(() => {{ const h = document.getElementById('{gid}'); const c = h.cloneNode(true);"
                         f" c.querySelectorAll('button').forEach(x => x.remove()); return c.innerText.trim(); }})()")
    gorunur = pg.evaluate(f"(() => {{ const r = document.getElementById('{gid}').getBoundingClientRect();"
                          f" return r.top >= 0 && r.top < innerHeight; }})()")
    hash_ = pg.evaluate("location.hash")
    b.close()
ok = metin == baslik and hash_ == "#" + gid and gorunur
print(f"1440px: '→ bugün: {metin}' → {hash_} başlık '{baslik}' (görünür {gorunur})")
sys.exit(0 if ok else 1)
"""


# Rev 32 R32-P0-1 (S): 375px dokunmatik — özetin 1. maddesinin sonunda "ilk: 19 Eyl"; dokununca
# 19 Eylül raporunun Letonya gelişmesi (h3#g1) ekranda. argv: url, beklenen metin, [görüntü öneki].
ILK_JS = r"""
import sys
from playwright.sync_api import sync_playwright
url, beklenen = sys.argv[1], sys.argv[2]
shot = sys.argv[3] if len(sys.argv) > 3 else ""
OLC = '''() => {
  const li = document.querySelector("h2#ozet + ol > li");
  const a = li && li.querySelector("a.ilk");
  if (!a) return null;
  const cs = getComputedStyle(a), rect = a.getBoundingClientRect();
  const son = li.lastElementChild === a && !(a.nextSibling && a.nextSibling.textContent.trim());
  const probe = document.createElement("span"); probe.style.color = "var(--muted)";
  li.appendChild(probe); const muted = getComputedStyle(probe).color; probe.remove();
  return {text: a.textContent.trim(), href: a.getAttribute("href"), son: son,
          mono: /Plex Mono|monospace/.test(cs.fontFamily), renk: cs.color === muted,
          h: Math.round(rect.height), rects: a.getClientRects().length,
          tasma: document.documentElement.scrollWidth - innerWidth};
}'''
VARIS = '''() => {
  const h = document.getElementById(location.hash.slice(1));
  if (!h) return null;
  const c = h.cloneNode(true); c.querySelectorAll("button").forEach(x => x.remove());
  const t = h.getBoundingClientRect();
  return {yol: location.pathname, hash: location.hash, baslik: c.innerText.trim(),
          gorunur: t.top >= 0 && t.bottom <= innerHeight};
}'''
with sync_playwright() as p:
    try: b = p.chromium.launch()
    except Exception: b = p.chromium.launch(channel="chrome")
    ctx = b.new_context(service_workers="block", viewport={"width": 375, "height": 812},
                        device_scale_factor=2, is_mobile=True, has_touch=True)
    pg = ctx.new_page()
    pg.goto(url); pg.wait_for_timeout(400)
    r = pg.evaluate(OLC)
    if r is None:
        print("375px: özet 1'de a.ilk yok"); b.close(); sys.exit(1)
    jeton = pg.locator("h2#ozet + ol > li a.ilk").first
    jeton.scroll_into_view_if_needed()
    if shot: pg.screenshot(path=shot + "-once.png")
    jeton.tap(); pg.wait_for_timeout(900)
    varis = pg.evaluate(VARIS)
    if shot: pg.screenshot(path=shot + "-sonra.png")
    b.close()
ok = bool(r["text"] == beklenen and r["son"] and r["mono"] and r["renk"] and r["h"] >= 44
          and r["rects"] == 1 and r["tasma"] <= 0 and varis
          and varis["yol"] + varis["hash"] == r["href"] and varis["gorunur"])
print(f"375px: özet 1 sonunda “{r['text']}” (son öğe {r['son']}, mono {r['mono']}, --muted {r['renk']}, "
      f"dokunma yüksekliği {r['h']}px, tek parça {r['rects'] == 1}, yatay taşma {r['tasma']}px) → dokununca "
      + (f"{varis['yol']}{varis['hash']} “{varis['baslik']}” (ekranda {varis['gorunur']})" if varis else "hedef yok"))
sys.exit(0 if ok else 1)
"""


# Rev 32 (deneme 2): İLK-EKRAN en kötü hâli — jeton kendi satırına düşse de (CI'da olduğu gibi)
# 4. madde 812'de kalır. argv: url. Çıktı: JSON [[etiket, h2 üst, 4. madde alt, jeton], …].
ILK_EKRAN_KOTU_JS = r"""
import sys, json
from playwright.sync_api import sync_playwright
url = sys.argv[1]
OLC = '''([ls, br]) => {
  if (ls) { const st = document.createElement("style");
    st.textContent = `.prose h2#ozet + ol, .report-title { letter-spacing: ${ls}px !important; }`;
    document.head.appendChild(st); }
  if (br) for (const a of document.querySelectorAll("h2#ozet + ol a.ilk")) a.before(document.createElement("br"));
  const h2 = document.querySelector(".prose h2#ozet");
  const lis = h2 ? Array.from(h2.nextElementSibling.children) : [];
  const li = lis[Math.min(4, lis.length) - 1];
  return [h2 ? h2.getBoundingClientRect().top : 9999, li ? li.getBoundingClientRect().bottom : 9999,
          document.querySelectorAll("h2#ozet + ol a.ilk").length];
}'''
out = []
with sync_playwright() as p:
    try: b = p.chromium.launch()
    except Exception: b = p.chromium.launch(channel="chrome")
    for etiket, ls, br in (("normal", 0, 0), ("jeton kendi satırında", 0, 1),
                           ("jeton kendi satırında + 0,15px harf aralığı", 0.15, 1)):
        ctx = b.new_context(viewport={"width": 375, "height": 812}, service_workers="block", locale="tr-TR")
        pg = ctx.new_page(); pg.goto(url, wait_until="load")
        pg.evaluate("document.fonts ? document.fonts.ready.then(() => 1) : 1"); pg.wait_for_timeout(200)
        h2, m, n = pg.evaluate(OLC, [ls, br])
        out.append([etiket, round(h2), round(m), n]); ctx.close()
    b.close()
print(json.dumps(out, ensure_ascii=False))
"""

# Rev 31 R31-P0-2 (S): 375px, ?oyuncu=roketsan — AA satırı "BRİFİNGDEN SONRA", renksiz (--muted),
# BRİFİNGDE ile aynı satırda asla; atıflı bir satırın BRİFİNGDE jetonu hâlâ renkli.
GEC_JS = r"""
import sys
from playwright.sync_api import sync_playwright
url = sys.argv[1]
JS = '''() => {
  const vis = Array.from(document.querySelectorAll('[data-search]')).filter(e => !e.hidden && e.offsetParent !== null);
  const aa = vis.find(e => e.textContent.includes('Anadolu Ajans'));
  const late = aa && aa.querySelector('.clip-late');
  const meta = aa && aa.querySelector('.clip-meta');
  const cited = document.querySelector('.clip-cited');
  const both = Array.from(document.querySelectorAll('.clip-meta'))
    .filter(m => m.querySelector('.clip-late') && m.querySelector('.clip-cited')).length;
  return {aa: !!aa, text: late ? late.innerText : null,
          late_color: late ? getComputedStyle(late).color : null,
          meta_color: meta ? getComputedStyle(meta).color : null,
          cited_color: cited ? getComputedStyle(cited).color : null,
          both: both, total: document.querySelectorAll('.clip-late').length};
}'''
with sync_playwright() as p:
    try: b = p.chromium.launch()
    except Exception: b = p.chromium.launch(channel="chrome")
    pg = b.new_context(service_workers="block", viewport={"width": 375, "height": 812}).new_page()
    pg.goto(url + "?oyuncu=roketsan"); pg.wait_for_timeout(600)
    r = pg.evaluate(JS)
    b.close()
ok = (r["aa"] and r["text"] == "BRİFİNGDEN SONRA" and r["late_color"] == r["meta_color"]
      and r["cited_color"] != r["late_color"] and r["both"] == 0)
print(f"375px ?oyuncu=roketsan: AA satırı '{r['text']}' · renk {r['late_color']} (meta {r['meta_color']},"
      f" BRİFİNGDE {r['cited_color']}) · ikisi aynı satırda {r['both']} · sayfada jeton {r['total']}")
sys.exit(0 if ok else 1)
"""


# Rev 33 R33-P0-1/P0-2 (S): 1440px, tr-TR — büyük harfe çevrilmiş kaynak adları tarayıcının
# kendi çiziminden (innerText, text-transform uygulanmış) okunur.
NOKTALI_JS = r"""
import json, sys
from playwright.sync_api import sync_playwright
url, kaynak = sys.argv[1], sys.argv[2]
JS = '''() => {
  const h = Array.from(document.querySelectorAll('h2.kicker')).find(e => e.textContent.trim().startsWith('Öne çıkanlar'));
  const one = [];
  for (let n = h && h.nextElementSibling; n && !n.matches('h2.kicker, details.general'); n = n.nextElementSibling)
    n.querySelectorAll('.clip-meta').forEach(m => one.push(m.innerText));
  return {lang: document.documentElement.lang, one: one,
          all: Array.from(document.querySelectorAll('.clip-meta')).map(m => m.innerText)};
}'''
with sync_playwright() as p:
    try: b = p.chromium.launch(channel="chrome")
    except Exception: b = p.chromium.launch()
    pg = b.new_context(service_workers="block", viewport={"width": 1440, "height": 900}, locale="tr-TR").new_page()
    pg.goto(url); pg.wait_for_timeout(500)
    r = pg.evaluate(JS)
    pg.goto(kaynak); pg.wait_for_timeout(300)
    r["snames"] = pg.eval_on_selector_all(".sname", "els => els.map(e => [e.innerText, !!e.querySelector('[lang=en]')])")
    b.close()
print(json.dumps(r, ensure_ascii=False))
"""


# Rev 24 (S): ilk ekran düzeni, her rapor, iki genişlik, açık/koyu.
ILK_EKRAN_JS = r"""
import json, sys
from playwright.sync_api import sync_playwright
base, gunler = sys.argv[1], sys.argv[2].split(",")
JS = '''(w) => {
  const top = e => e.getBoundingClientRect().top + scrollY;
  const ray = document.querySelector('.report-grid > .rail');
  const ol = document.querySelector('.prose h2#ozet + ol');
  const pf = document.getElementById('portfoy');
  const h1 = document.querySelector('h1.report-title');
  const chips = Array.from(document.querySelectorAll('#devnav .chip'));
  const rows = Array.from(document.querySelectorAll('.prose tbody tr'));
  const lab = rows.map(tr => {
    const td = tr.querySelector('td[data-kart]');
    if (!td) return 'yok';
    const c = getComputedStyle(td, '::before');
    return c.content === 'none' ? 'none' : c.content.replace(/"/g, '') + '/' + c.textTransform;
  });
  const r = {tasma: document.documentElement.scrollWidth > innerWidth,
             cip_satir: new Set(chips.map(c => Math.round(c.getBoundingClientRect().top))).size,
             kart: lab, satir: rows.length};
  if (w < 900) {
    r.ray_sira = !!(ray && ol && pf && top(ray) >= top(ol) + ol.offsetHeight && top(ray) < top(pf));
    r.ray_gorunur = !!(ray && ray.getClientRects().length);
  } else {
    const col = document.querySelector('article.column').getBoundingClientRect();
    r.ray_sira = !!(ray && ray.getBoundingClientRect().right <= col.left && Math.abs(top(ray) - top(document.querySelector('article.column'))) < 2);
    r.ray_gorunur = true;
  }
  return r;
}'''
out = {}
with sync_playwright() as p:
    try: b = p.chromium.launch(channel="chrome")
    except Exception: b = p.chromium.launch()
    for w, h in ((375, 812), (1440, 900)):
        for tema in ("light", "dark"):
            ctx = b.new_context(service_workers="block", viewport={"width": w, "height": h},
                                locale="tr-TR", color_scheme=tema)
            pg = ctx.new_page()
            for g in gunler:
                pg.goto(f"{base}/reports/{g}.html", wait_until="load"); pg.wait_for_timeout(150)
                out[f"{g}@{w}/{tema}"] = pg.evaluate(JS, w)
            ctx.close()
    b.close()
print(json.dumps(out, ensure_ascii=False))
"""


def r24_checks(py, fails):
    """Rev 24: İLK-EKRAN — kart etiketi (statik), denetim iki yönde, tarayıcı düzeni."""
    import json
    raporlar = sorted((ROOT / "reports").glob("????-??-??.html"))
    eksik = []
    for f in raporlar:
        h = f.read_text(encoding="utf-8")
        tb = re.search(r"<tbody>.*?</tbody>", h, re.S)
        n_tr = len(re.findall(r"<tr>", tb.group(0))) if tb else 0
        n_k = h.count('data-kart="İzlenecek"')
        if n_tr != n_k:
            eksik.append(f"{f.stem}: {n_k}/{n_tr}")
    print(f"{'ok  ' if not eksik else 'FAIL'} R24 kart etiketi (data-kart) · {len(raporlar) - len(eksik)}/{len(raporlar)} rapor"
          + (f" · {eksik}" if eksik else ""))
    if eksik:
        fails.append("R24 kart etiketi")
    if not py:
        print("FAIL İLK-EKRAN · Playwright'lı python yok")
        fails.append("İLK-EKRAN")
        return
    env = {k: v for k, v in os.environ.items() if k not in ("ILK_EKRAN_BOZ", "RUNNER_TEMP", "GITHUB_STEP_SUMMARY")}
    ie = subprocess.run([py, "scripts/check_reports.py", "--ilk-ekran", "--base", BASE],
                        cwd=ROOT, capture_output=True, text=True, env=env)
    satir = [l for l in ie.stdout.splitlines() if l.startswith("| 20")]
    print(f"{'ok  ' if ie.returncode == 0 else 'FAIL'} İLK-EKRAN normal · {satir[0] if satir else ie.stderr[-300:]}")
    if ie.returncode:
        fails.append("İLK-EKRAN normal")
    bz = subprocess.run([py, "scripts/check_reports.py", "--ilk-ekran", "--base", BASE],
                        cwd=ROOT, capture_output=True, text=True, env={**env, "ILK_EKRAN_BOZ": "1"})
    uy = [l.strip() for l in bz.stdout.splitlines() if l.strip().startswith("! İLK-EKRAN")]
    ok = bz.returncode == 1 and bool(uy) and "boz uygulanamadı" not in bz.stdout
    print(f"{'ok  ' if ok else 'FAIL'} İLK-EKRAN ILK_EKRAN_BOZ=1 → uyarı · {uy[0] if uy else bz.stdout[-300:] + bz.stderr[-300:]}")
    if not ok:
        fails.append("İLK-EKRAN boz")
    tr = subprocess.run([py, "-c", ILK_EKRAN_JS, BASE, ",".join(f.stem for f in raporlar)],
                        cwd=ROOT, capture_output=True, text=True)
    try:
        sonuc = json.loads(tr.stdout)
    except ValueError:
        print(f"FAIL R24 tarayıcı · {tr.stderr[-400:]}")
        fails.append("R24 tarayıcı")
        return
    kotu = []
    for k, r in sonuc.items():
        mobil = "@375" in k
        beklenen = "İzlenecek/uppercase" if mobil else "none"
        if (r["tasma"] or not r["ray_sira"] or not r["ray_gorunur"] or r["cip_satir"] != 1
                or r["satir"] == 0 or any(x != beklenen for x in r["kart"])):
            kotu.append(f"{k}: {r}")
    print(f"{'ok  ' if not kotu else 'FAIL'} R24 tarayıcı (375/1440 × açık/koyu × {len(raporlar)} rapor) · "
          f"{len(sonuc) - len(kotu)}/{len(sonuc)}" + (f" · {kotu[:2]}" if kotu else
          " · 375: ray özet ile Portföy arasında, çipler tek satır, her kartta İZLENECEK; 1440: ray solda"))
    if kotu:
        fails.append("R24 tarayıcı")


def _tr_upper(text):
    return text.replace("i", "İ").upper()


def r33_checks(build_stdout, py, fails):
    """Rev 33: NOKTALI-İ — build satırı, src_name() birim durumları, tarayıcı (1440, tr-TR), bozuk derleme."""
    import json
    sys.path.insert(0, str(ROOT))
    import build as B
    satir = [l.strip() for l in build_stdout.splitlines() if "· NOKTALI-İ:" in l]
    ok = bool(satir) and "NOKTALI-İ: 0 örnek" in satir[0]
    print(f"{'ok  ' if ok else 'FAIL'} NOKTALI-İ build satırı · {satir[0].lstrip('· ') if satir else 'satır yok'}")
    if not ok:
        fails.append("NOKTALI-İ build satırı")

    B.kaynak_ulkeleri(B.load_news())
    birim = {
        "Unmanned Airspace": '<span lang="en">Unmanned Airspace</span>',
        "Anadolu Ajansı — güncel": "Anadolu Ajansı — güncel",
        "SCMP (Çin)": '<span lang="en">SCMP</span> (Çin)',
        "Defence24 (PL)": '<span lang="en">Defence24 (PL)</span>',
        "European Security & Defence": '<span lang="en">European Security &amp; Defence</span>',
        "Hartpunkt": '<span lang="en">Hartpunkt</span>',   # yalnız roster'da: ülke yok, Türkçe harf yok
        "Savunma Günlüğü": "Savunma Günlüğü",               # bilinmeyen + Türkçe harf → Türk sayılır
    }
    yanlis = {k: B.src_name(k) for k, v in birim.items() if B.src_name(k) != v}
    print(f"{'ok  ' if not yanlis else 'FAIL'} src_name() birim durumları · {len(birim) - len(yanlis)}/{len(birim)}"
          + (f" · yanlış: {yanlis}" if yanlis else ""))
    if yanlis:
        fails.append("src_name birim")

    yabanci = sorted({B.ad_parcalari(a)[0] for a in B.SRC_ULKE if B.yabanci_kaynak(a)})
    noktali = [_tr_upper(a) for a in yabanci if "i" in a]

    def tarayici(etiket):
        kupur = latest("haberler", "????-??-??.html")
        kaynak = kupur.replace(".html", "-kaynaklar.html")
        r = subprocess.run([py, "-c", NOKTALI_JS, BASE + kupur, BASE + kaynak], cwd=ROOT, capture_output=True, text=True)
        if r.returncode:
            print(f"FAIL NOKTALI-İ tarayıcı ({etiket}) · {r.stderr[-400:]}")
            return None
        return json.loads(r.stdout)

    if not py:
        print("FAIL NOKTALI-İ tarayıcı · Playwright'lı python yok")
        fails.append("NOKTALI-İ tarayıcı")
        return
    r = tarayici("normal")
    ok = bool(r)
    if r:
        one, tum = " | ".join(r["one"]), " | ".join(r["all"])
        hatali = sorted({n for n in noktali if n in tum})
        sn_hatali = [t for t, lang in r["snames"] if B.yabanci_kaynak(t) and t in B.SRC_ULKE and not lang]
        ok = (r["lang"] == "tr" and "UNMANNED AIRSPACE" in one and "DEFENSE DAILY" in one
              and "AİRSPACE" not in tum and "DAİLY" not in tum and "ANADOLU AJANSI" in tum
              and not hatali and not sn_hatali)
        print(f"{'ok  ' if ok else 'FAIL'} NOKTALI-İ 1440px tr-TR · lang={r['lang']} · Öne çıkanlar: "
              f"{'“UNMANNED AIRSPACE”' if 'UNMANNED AIRSPACE' in one else 'UNMANNED AIRSPACE yok'}, "
              f"{'“DEFENSE DAILY”' if 'DEFENSE DAILY' in one else 'DEFENSE DAILY yok'} · "
              f"{'“ANADOLU AJANSI” değişmedi' if 'ANADOLU AJANSI' in tum else 'ANADOLU AJANSI yok'} · "
              f"İ'li yabancı ad {len(hatali)}{' ' + str(hatali[:4]) if hatali else ''} · "
              f"Kaynaklar sayfasında sarmasız yabancı ad {len(sn_hatali)}")
    if not ok:
        fails.append("NOKTALI-İ tarayıcı")

    # Bozuk derleme: sarmal kapalı → uyarı örneklerle gelir, tarayıcı noktalı İ çizer; sonra normal derleme.
    boz = subprocess.run([sys.executable, "build.py"], cwd=ROOT, capture_output=True, text=True,
                         env={**os.environ, "NOKTALI_BOZ": "1"})
    try:
        bs = [l.strip() for l in boz.stdout.splitlines() if "· NOKTALI-İ:" in l]
        uy = [l.strip() for l in boz.stdout.splitlines() if l.strip().startswith("! NOKTALI-İ ·")]
        m = re.search(r"NOKTALI-İ: (\d+) örnek", bs[0]) if bs else None
        rb = tarayici("bozuk")
        one_b = " | ".join(rb["one"]) if rb else ""
        ok = bool(boz.returncode == 0 and m and int(m.group(1)) > 0 and uy
                  and "(NOKTALI_BOZ=1, bilerek)" in uy[0] and "UNMANNED AİRSPACE" in one_b)
        print(f"{'ok  ' if ok else 'FAIL'} NOKTALI-İ bozuk derleme (NOKTALI_BOZ=1) · "
              f"{bs[0].lstrip('· ') if bs else 'satır yok'} · uyarı {'var' if uy else 'yok'} · tarayıcı "
              f"{'“UNMANNED AİRSPACE”' if 'UNMANNED AİRSPACE' in one_b else 'noktalı İ görünmedi'}")
        if uy:
            print(f"       {uy[0][:220]}")
        if not ok:
            fails.append("NOKTALI-İ bozuk derleme")
    finally:
        back = subprocess.run([sys.executable, "build.py"], cwd=ROOT, capture_output=True, text=True,
                              env={k: v for k, v in os.environ.items() if k != "NOKTALI_BOZ"})
        if back.returncode or "NOKTALI-İ: 0 örnek" not in back.stdout:
            print("FAIL NOKTALI-İ: normal derlemeye dönüş")
            fails.append("rebuild (NOKTALI-İ)")


def r31_checks(build_stdout, py, fails):
    """Rev 31: GEÇ-GELEN — ağsız toplama testi, build satırı, jeton (375px), yerel aday dosyası."""
    t = subprocess.run([sys.executable, "scripts/test_collect.py"], cwd=ROOT, capture_output=True, text=True)
    son = t.stdout.strip().splitlines()[-1] if t.stdout.strip() else t.stderr[-300:]
    print(f"{'ok  ' if t.returncode == 0 else 'FAIL'} scripts/test_collect.py · {son}")
    if t.returncode:
        print(t.stdout[-2500:], t.stderr[-1500:])
        fails.append("test_collect.py")
    satir = [l.strip() for l in build_stdout.splitlines() if "GEÇ-GELEN: BRİFİNGDEN SONRA jetonlu satır" in l]
    ok = bool(satir) and "2026-09-23: 89" in satir[0]
    print(f"{'ok  ' if ok else 'FAIL'} GEÇ-GELEN build satırı · {satir[0].lstrip('· ') if satir else 'satır yok'}")
    if not ok:
        fails.append("GEÇ-GELEN build satırı")
    if py and (ROOT / "haberler" / "2026-09-23.html").exists():
        g = subprocess.run([py, "-c", GEC_JS, f"{BASE}/haberler/2026-09-23.html"],
                           cwd=ROOT, capture_output=True, text=True)
        print(f"{'ok  ' if g.returncode == 0 else 'FAIL'} BRİFİNGDEN SONRA jetonu · {g.stdout.strip() or g.stderr[-300:]}")
        if g.returncode:
            fails.append("BRİFİNGDEN SONRA jetonu")
    aday = ROOT / "data" / "news" / "2026-09-24-aday.md"
    if not aday.exists():
        print("ok   (D) 2026-09-24-aday.md yok (yalnız yerel kanıt; commit edilmez) — atlandı")
        return
    try:
        with urllib.request.urlopen(f"{BASE}/data/news/2026-09-24-aday.md", timeout=10) as r:
            metin = r.read().decode("utf-8")
    except Exception as exc:
        metin = ""
        print(f"       {exc}")
    sys.path.insert(0, str(ROOT / "scripts"))
    import collect_news as CN
    ilk = next((l for l in metin.splitlines() if l.startswith("## ")), "")
    ok = ilk.startswith("## Dünkü brifingden sonra gelenler (") and any(
        "aselsan-ile-roketsan" in u for u in CN.first_section_urls(metin))
    print(f"{'ok  ' if ok else 'FAIL'} (D) /data/news/2026-09-24-aday.md · ilk bölüm '{ilk}' · AA satırı "
          f"{'içinde' if ok else 'yok'}")
    if not ok:
        fails.append("(D) aday ilk bölüm")


# Rev 25: kategori ölçütleri (S) — 23 Eylül medya takibi, 375×812 ve 1440×900.
R25_JS = r"""
import sys
from playwright.sync_api import sync_playwright
url = sys.argv[1]
JS = '''() => {
  const rows = sec => Array.from(document.querySelectorAll('li[data-sec="' + sec + '"]'))
    .map(li => li.getAttribute('data-search')
               || (li.querySelector('[data-search]') || {getAttribute: () => ''}).getAttribute('data-search') || '');
  const has = (list, re) => list.filter(t => re.test(t)).length;
  const cuas = rows('kat-c-uas-ve-hava-savunma'), ihale = rows('kat-ihale-ve-sozlesmeler');
  const oyuncu = rows('kat-oyuncu-duyurulari');
  const rail = Array.from(document.querySelectorAll('.news-rail-row')).map(e => e.innerText);
  const chips = Array.from(document.querySelectorAll('.chip')).map(e => e.innerText);
  return {rail: rail.some(t => t.includes('Oyuncu Duyuruları')),
          chip: chips.some(t => t.includes('Oyuncu Duyuruları')),
          rakip: /Rakip Duyuru|rakip-duyuru/i.test(document.documentElement.outerHTML)
                 || /Rakip Duyuru/i.test(document.body.innerText),
          cuas: cuas.length, cuas_bad: has(cuas, /Tournai|Zipline|DroneXL/),
          ihale: ihale.length, ihale_bad: has(ihale, /Greenland|Grönland/),
          hanwha: has(oyuncu, /Hanwha.*Mühimmat Yatırım/)};
}'''
ARA = '''() => Array.from(document.querySelectorAll('[data-search]'))
  .filter(e => !e.hidden && e.offsetParent !== null && /Dolomites/.test(e.getAttribute('data-search'))
               && e.closest('li[data-sec="kat-genel-savunma-gundemi"]') && e.closest('details.more')).length'''
with sync_playwright() as p:
    try: b = p.chromium.launch()
    except Exception: b = p.chromium.launch(channel="chrome")
    out, ok = [], True
    for w, h in ((375, 812), (1440, 900)):
        pg = b.new_context(service_workers="block", viewport={"width": w, "height": h}).new_page()
        pg.goto(url); pg.wait_for_timeout(500)
        r = pg.evaluate(JS)
        link = pg.locator('.news-rail-row[href="#kat-oyuncu-duyurulari"], .chip[href="#kat-oyuncu-duyurulari"]')
        link.filter(visible=True).first.click(); pg.wait_for_timeout(300)
        r["hash"] = pg.evaluate("location.hash")
        pg.fill("#q", "Dolomites"); pg.wait_for_timeout(700)
        r["ara"] = pg.evaluate(ARA)
        ok = (ok and r["rail"] and r["chip"] and not r["rakip"] and r["cuas_bad"] == 0
              and r["ihale_bad"] == 0 and r["hanwha"] == 1 and r["hash"] == "#kat-oyuncu-duyurulari"
              and r["ara"] >= 1)
        out.append(f"{w}px: ray/çip 'Oyuncu Duyuruları' {r['rail']}/{r['chip']} · 'Rakip Duyuruları' {r['rakip']} · "
                   f"C-UAS {r['cuas']} satır, Tournai/Zipline/DroneXL {r['cuas_bad']} · İhale {r['ihale']} satır, "
                   f"Grönland {r['ihale_bad']} · Hanwha Oyuncu'da {r['hanwha']} · adres {r['hash']} · "
                   f"arama 'Dolomites' Genel tam dökümde {r['ara']}")
    b.close()
print(" | ".join(out))
sys.exit(0 if ok else 1)
"""


def r25_checks(build_stdout, py, fails):
    """Rev 25: SİLME-YOK / İPUCU-YOK testi, build'in S8 satırı, 23 Eylül yeniden kategorilemesi, (S)."""
    t = subprocess.run([sys.executable, "scripts/test_silme_yok.py"], cwd=ROOT, capture_output=True, text=True)
    son = t.stdout.strip().splitlines()[-1] if t.stdout.strip() else t.stderr[-300:]
    print(f"{'ok  ' if t.returncode == 0 else 'FAIL'} scripts/test_silme_yok.py · {son}")
    if t.returncode:
        print(t.stdout[-2500:], t.stderr[-1500:])
        fails.append("test_silme_yok.py")
    satir = [l.strip() for l in build_stdout.splitlines() if "İPUCU-YOK / S8" in l]
    ok = bool(satir) and "yalnız ipucuyla gelen 0 ·" in satir[0]
    print(f"{'ok  ' if ok else 'FAIL'} İPUCU-YOK / S8 build satırı · {satir[0].lstrip('· ')[:160] if satir else 'satır yok'}")
    if not ok:
        fails.append("İPUCU-YOK satırı")
    r = subprocess.run([sys.executable, "scripts/yeniden_kategorile.py", "2026-09-23"], cwd=ROOT,
                       capture_output=True, text=True)
    ilk = r.stdout.splitlines()[0] if r.stdout else r.stderr[-200:]
    ok = r.returncode == 0 and "· 0 kalemin kategorisi değişti" in ilk
    print(f"{'ok  ' if ok else 'FAIL'} 23 Eylül yeniden kategorilenmiş (kuru çalıştırma) · {ilk}")
    if not ok:
        fails.append("yeniden kategorileme")
    # Özet kapsamı ve Öne çıkanlar savunma dışı işaretli kalemi hiç almaz (müşteri kararı:
    # yalnız başlık çevirisi, özet yok). Bellekte, 23 Eylül'ün ilk 60 kalemi işaretlenir.
    kod = ("import build, json; d = json.load(open('data/news/2026-09-23.json'))['items'];"
           "d = [dict(i) for i in d]; [i.update(savunma_terimi=False) for i in d[:60]];"
           "v = build.default_visible(d, '2026-09-23', build.cited_urls('2026-09-23'));"
           "top, _ = build.news_layout(d, '2026-09-23', set());"
           "print(sum(1 for i in v if i.get('savunma_terimi') is False),"
           " sum(1 for r in top if r[2].get('savunma_terimi') is False), len(v))")
    k = subprocess.run([sys.executable, "-c", kod], cwd=ROOT, capture_output=True, text=True)
    parts = k.stdout.split()
    ok = k.returncode == 0 and parts[:2] == ["0", "0"]
    print(f"{'ok  ' if ok else 'FAIL'} özet kapsamı / Öne çıkanlar savunma dışı kalem almaz · "
          + ("kapsamda %s, öne çıkanlarda %s (kapsam %s)" % tuple(parts) if len(parts) == 3 else k.stderr[-200:]))
    if not ok:
        fails.append("savunma dışı özet kapsamı")
    if py and (ROOT / "haberler" / "2026-09-23.html").exists():
        g = subprocess.run([py, "-c", R25_JS, f"{BASE}/haberler/2026-09-23.html"],
                           cwd=ROOT, capture_output=True, text=True)
        print(f"{'ok  ' if g.returncode == 0 else 'FAIL'} R25 (S) 23 Eylül medya takibi · "
              f"{g.stdout.strip() or g.stderr[-300:]}")
        if g.returncode:
            fails.append("R25 (S)")


def r32_checks(build_stdout, py, fails):
    """Rev 32: TEKRAR-MANŞET — jeton satırları, uyarı, kural kontrolleri, 375px dokunma."""
    sys.path.insert(0, str(ROOT))
    import build as B
    iso = sorted((ROOT / "source").glob("????-??-??.md"))[-1].stem
    satirlar = [l.strip() for l in build_stdout.splitlines()]
    jeton = [l for l in satirlar if re.match(r"· reports/\S+\.html · özet \d+ ilk:", l)]
    ozet = [l for l in satirlar if l.startswith(f"· TEKRAR-MANŞET {iso}:")]
    uy = [l for l in satirlar if l.startswith("! TEKRAR-MANŞET ·")]
    if iso == "2026-09-23":   # R32 kabulü: özet 1 → 19 Eylül G1, H1 uyarısı
        ok = (any(l.startswith("· reports/2026-09-23.html · özet 1 ilk: 19 Eyl G1") for l in jeton)
              and any(l.endswith("TEKRAR-MANŞET: 23 Eyl H1 ↔ 19 Eyl") for l in uy))
    else:
        ok = bool(ozet)
    print(f"{'ok  ' if ok else 'FAIL'} TEKRAR-MANŞET · {ozet[0].lstrip('· ') if ozet else 'satır yok'}")
    for l in jeton + uy:
        print(f"       {l[:170]}")
    if not ok:
        fails.append("TEKRAR-MANŞET build")
    # Kural kontrolleri — sözlük: derlemde küçük harfle geçen kelimeler.
    sozluk = {"savunma", "bakanlık", "karar", "seçti", "obüsünü"}
    once = {"metinler": ["Letonya, Archer yerine Çek Morana obüsünü seçti."], "url": {"https://a.b/1"}, "etiket": "x"}
    url = B._eslesme("Pentagon 17 firmayı seçti.", {"https://a.b/1"}, once, sozluk)
    ad = B._eslesme("Letonya Archer'ı bırakıp Çek Morana obüsünü seçti.", set(), once, sozluk)
    tek_ad = B._eslesme("Letonya obüsünü seçti.", set(), once, sozluk)
    sozluk_ad = B._eslesme("Savunma Bakanlık Karar obüsünü seçti.", set(),
                           {"metinler": ["Savunma Bakanlık Karar obüsünü seçti."], "url": set(), "etiket": "x"},
                           sozluk)
    baska = B._eslesme("Leonardo ve Alkeon Danimarka'da top üretecek.", set(), once, sozluk)
    ok = bool(url and url[0] == "url" and ad and ad[0] == "ad" and not tek_ad and not sozluk_ad and not baska)
    print(f"{'ok  ' if ok else 'FAIL'} TEKRAR-MANŞET kural kontrolleri · ortak URL → {bool(url)} · "
          f"2+ özel ad + örtüşme → {bool(ad)} · tek özel ad → {bool(tek_ad)} · yalnız sözlük kelimesi → "
          f"{bool(sozluk_ad)} · başka gelişme → {bool(baska)}")
    if not ok:
        fails.append("TEKRAR-MANŞET kural kontrolleri")
    if iso != "2026-09-23":
        return
    if not py:
        print("FAIL TEKRAR-MANŞET 375px · Playwright'lı python yok")
        fails.append("TEKRAR-MANŞET 375px")
        return
    for sayfa in (f"/reports/{iso}.html", "/"):
        r = subprocess.run([py, "-c", ILK_JS, BASE + sayfa, "ilk: 19 Eyl"], cwd=ROOT, capture_output=True, text=True)
        print(f"{'ok  ' if r.returncode == 0 else 'FAIL'} TEKRAR-MANŞET 375px {sayfa} · {r.stdout.strip() or r.stderr[-300:]}")
        if r.returncode:
            fails.append(f"TEKRAR-MANŞET 375px {sayfa}")
    import json
    r = subprocess.run([py, "-c", ILK_EKRAN_KOTU_JS, f"{BASE}/reports/{iso}.html"], cwd=ROOT,
                       capture_output=True, text=True)
    try:
        olc = json.loads(r.stdout)
    except ValueError:
        olc = []
    ok = bool(olc) and all(h2 <= 300 and m <= 812 for _, h2, m, _n in olc) and olc[0][3] >= 1
    print(f"{'ok  ' if ok else 'FAIL'} İLK-EKRAN en kötü hâl (375×812, {olc[0][3] if olc else 0} jeton) · "
          + (" · ".join(f"{e}: h2 {h2}px, 4. madde {m}px" for e, h2, m, _n in olc) if olc else r.stderr[-300:]))
    if not ok:
        fails.append("İLK-EKRAN en kötü hâl")


# Rev 28: KANIT-BOŞLUĞU — 375×812, Tarama'nın altındaki tek satır ve Kaynaklar sayfası.
KANIT_JS = r"""
import sys, json
from playwright.sync_api import sync_playwright
base, sayfalar, kaynak = sys.argv[1], sys.argv[2].split(","), sys.argv[3]
OLC = '''() => {
  const n = document.querySelectorAll(".rail-not");
  const t = [...document.querySelectorAll(".rail-label")].find(e => e.textContent.trim() === "Tarama");
  const tasma = document.documentElement.scrollWidth - innerWidth;
  if (!n.length) return {adet: 0, tasma};
  const v = t ? t.parentElement.querySelector(".rail-value") : null;
  const rn = n[0].getBoundingClientRect(), rv = v ? v.getBoundingClientRect() : null;
  const ink = document.createElement("span"); ink.style.color = "var(--ink-2)"; document.body.appendChild(ink);
  const ink2 = getComputedStyle(ink).color; ink.remove();
  const cs = getComputedStyle(n[0]);
  return {adet: n.length, metin: n[0].innerText.trim(), ayni_blok: !!(t && t.parentElement.contains(n[0])),
          altinda: !!(rv && rn.top >= rv.bottom - 1), sol: t ? Math.round(rn.left - t.getBoundingClientRect().left) : null,
          renk: cs.color === ink2, mono: /Plex Mono|monospace/.test(cs.fontFamily), tasma};
}'''
out = {}
with sync_playwright() as p:
    try: b = p.chromium.launch(channel="chrome")
    except Exception: b = p.chromium.launch()
    ctx = b.new_context(service_workers="block", viewport={"width": 375, "height": 812}, is_mobile=True, has_touch=True)
    pg = ctx.new_page()
    for s in sayfalar:
        pg.goto(base + s, wait_until="load"); out[s] = pg.evaluate(OLC)
    pg.goto(base + kaynak, wait_until="load")
    govde = pg.inner_text("main")
    out["kaynak"] = {"yanit_vermedi": "yanıt vermedi" in govde.lower(),
                     "elbit": "oyuncu: Elbit" in govde, "northrop": "oyuncu: Northrop Grumman" in govde,
                     "tasma": pg.evaluate("document.documentElement.scrollWidth - innerWidth")}
    b.close()
print(json.dumps(out, ensure_ascii=False))
"""


def r28_checks(build_stdout, py, fails):
    """Rev 28: KANIT-BOŞLUĞU — build satırı, statik, kural kontrolleri, 375px."""
    import json
    sys.path.insert(0, str(ROOT))
    import build as B
    from scripts import uyari
    iso = sorted((ROOT / "source").glob("????-??-??.md"))[-1].stem
    cumle = "Elbit Systems ve Northrop Grumman'ın kendi duyuruları bugün okunamadı."
    satirlar = [l.strip() for l in build_stdout.splitlines()]
    ana = [l for l in satirlar if l.startswith(f"· KANIT-BOŞLUĞU {iso}:")]
    uy = [l for l in satirlar if l.startswith("! KANIT-BOŞLUĞU ·")]
    if iso == "2026-09-23":
        ok = (bool(ana) and ana[0].endswith(cumle) and len(uy) == 1
              and "Elbit Systems (" in uy[0] and "Northrop Grumman (" in uy[0])
    else:
        ok = bool(ana)
    print(f"{'ok  ' if ok else 'FAIL'} KANIT-BOŞLUĞU build · {ana[0].lstrip('· ') if ana else 'satır yok'}")
    for l in uy:
        print(f"       {l[:200]}")
    if not ok:
        fails.append("KANIT-BOŞLUĞU build")

    # Statik: satır tam olarak kesişimi boş olmayan günlerde.
    news = B.load_news()
    yanlis, gunler = [], []
    for f in sorted((ROOT / "reports").glob("????-??-??.html")):
        h = f.read_text(encoding="utf-8")
        beklenen = [k for k, *_ in B.kanit_boslugu(news.get(f.stem))]
        var = re.findall(r'<span class="rail-not"[^>]*>([^<]*)</span>', h)
        gunler.append(f"{f.stem[8:]}:{len(beklenen) if f.stem in news else '—'}")
        if (len(var) != (1 if beklenen else 0)
                or (beklenen and var[0].replace("&#x27;", "'") != B.kanit_cumlesi(beklenen))):
            yanlis.append(f.stem)
    kok = (ROOT / "index.html").read_text(encoding="utf-8")
    kok_ok = kok.count('class="rail-not"') == (1 if B.kanit_boslugu(news.get(iso)) else 0)
    sayfalar = sorted((ROOT / "haberler").glob("*-kaynaklar.html"))
    yv = [f.name for f in sayfalar if "yanıt vermedi" in f.read_text(encoding="utf-8")]
    son_k = ROOT / "haberler" / f"{iso}-kaynaklar.html"
    k_html = son_k.read_text(encoding="utf-8") if son_k.exists() else ""
    adlar = ("oyuncu: Elbit<" in k_html and "oyuncu: Northrop Grumman<" in k_html) if iso == "2026-09-23" else True
    ok = not yanlis and kok_ok and not yv and adlar
    print(f"{'ok  ' if ok else 'FAIL'} KANIT-BOŞLUĞU statik · satır = kesişim {len(gunler) - len(yanlis)}/{len(gunler)} rapor "
          f"(gün:ad, — = medya takibi yok: {' '.join(gunler)}) · index.html {kok_ok} · "
          f"“yanıt vermedi” {len(yv)}/{len(sayfalar)} Kaynaklar sayfasında · Elbit/Northrop satırında ad {adlar}"
          + (f" · yanlış: {yanlis}" if yanlis else ""))
    if not ok:
        fails.append("KANIT-BOŞLUĞU statik")

    # Kural kontrolleri: boş kesişim → satır yok, uyarı yok; tek oyuncu → tek satır, tek uyarı.
    # CI'da gerçek uyarı dosyasına ve (A)'ya yazmasın diye RUNNER_TEMP / GITHUB_STEP_SUMMARY gizlenir.
    gizli = {k: os.environ.pop(k) for k in ("RUNNER_TEMP", "GITHUB_STEP_SUMMARY") if k in os.environ}
    try:
        once = len(uyari._BELLEK)
        bos = {"failures": [{"source": "Hartpunkt", "error": "x"}, {"source": "AeroVironment", "error": "403"}]}
        bos_ad = B.kanit_boslugu_kurali("2026-09-30", bos)
        bos_uy = len(uyari._BELLEK) - once
        tek = {"failures": [{"source": "Elbit Systems", "error": "feed parsed but empty"}]}
        tek_ad = B.kanit_boslugu_kurali("2026-09-30", tek)
        tek_uy = len(uyari._BELLEK) - once - bos_uy
        yok = B.kanit_boslugu_kurali("2026-09-30", None)
    finally:
        os.environ.update(gizli)
    ekler = {a: B._ilgi_eki(a) for a in ("Northrop Grumman", "Leonardo", "MBDA", "Elbit Systems", "KNDS")}
    ek_ok = ekler == {"Northrop Grumman": "'ın", "Leonardo": "'nun", "MBDA": "'nın",
                      "Elbit Systems": "'in", "KNDS": "'nin"}
    ray_bos = B.build_report({"title": "t"}, "", "2026-09-30", scan=(1, 2))
    ray_dolu = B.build_report({"title": "t"}, "", "2026-09-30", scan=(1, 2), bosluk=["Leonardo"])
    ok = (bos_ad == [] and bos_uy == 0 and tek_ad == ["Elbit Systems"] and tek_uy == 1 and yok == []
          and B.kanit_html([]) == "" and ek_ok and "rail-not" not in ray_bos
          and "Leonardo&#x27;nun kendi duyuruları bugün okunamadı." in ray_dolu)
    print(f"{'ok  ' if ok else 'FAIL'} KANIT-BOŞLUĞU kural kontrolleri · boş kesişim → satır {bool(bos_ad)}, uyarı {bos_uy} · "
          f"Elbit tek → {B.kanit_cumlesi(tek_ad)!r}, uyarı {tek_uy} · medya takibi yok → satır {bool(yok)} · "
          f"ekler {' '.join(a + e for a, e in ekler.items())}")
    if not ok:
        fails.append("KANIT-BOŞLUĞU kural kontrolleri")

    if not py:
        print("FAIL KANIT-BOŞLUĞU 375px · Playwright'lı python yok")
        fails.append("KANIT-BOŞLUĞU 375px")
        return
    ilk = sorted((ROOT / "reports").glob("????-??-??.html"))[0].stem
    sayfa = [f"/reports/{iso}.html", "/", f"/reports/{ilk}.html"]
    r = subprocess.run([py, "-c", KANIT_JS, BASE, ",".join(sayfa), f"/haberler/{iso}-kaynaklar.html"],
                       cwd=ROOT, capture_output=True, text=True)
    try:
        o = json.loads(r.stdout)
    except ValueError:
        print(f"FAIL KANIT-BOŞLUĞU 375px · {r.stderr[-400:]}")
        fails.append("KANIT-BOŞLUĞU 375px")
        return
    beklenen = B.kanit_cumlesi([k for k, *_ in B.kanit_boslugu(news.get(iso))])
    kotu = []
    for s in sayfa[:2]:
        x = o[s]
        if not (x["adet"] == (1 if beklenen else 0) and (not beklenen or (
                x["metin"] == beklenen and x["ayni_blok"] and x["altinda"] and x["sol"] == 0
                and x["renk"] and x["mono"])) and x["tasma"] <= 0):
            kotu.append(f"{s}: {x}")
    if not B.kanit_boslugu(news.get(ilk)) and o[sayfa[2]]["adet"] != 0:
        kotu.append(f"{sayfa[2]}: {o[sayfa[2]]}")
    k = o["kaynak"]
    if k["yanit_vermedi"] or k["tasma"] > 0 or (iso == "2026-09-23" and not (k["elbit"] and k["northrop"])):
        kotu.append(f"kaynaklar: {k}")
    x = o[sayfa[0]]
    print(f"{'ok  ' if not kotu else 'FAIL'} KANIT-BOŞLUĞU 375px · {sayfa[0]} ve /: "
          + (f"“{x.get('metin')}” Tarama'nın altında {x.get('altinda')}, aynı sol kenar {x.get('sol') == 0}, "
             f"--ink-2 {x.get('renk')}, mono {x.get('mono')}, sayfada {x['adet']}" if x["adet"] else "satır yok")
          + f" · {sayfa[2]}: satır {o[sayfa[2]]['adet']}"
          + f" · Kaynaklar: “yanıt vermedi” {k['yanit_vermedi']}, oyuncu: Elbit {k['elbit']}, "
            f"oyuncu: Northrop Grumman {k['northrop']}"
          + (f" · {kotu}" if kotu else ""))
    if kotu:
        fails.append("KANIT-BOŞLUĞU 375px")

def r28_bos_kesisim_checks(py, fails):
    """Rev 28 (deneme 2): bos_kesisim — kesişimi boş günün kanıtı; önce normal, sonra düzenli derleme."""
    import hashlib
    env = {k: v for k, v in os.environ.items() if k not in ("BOS_KESISIM", "RUNNER_TEMP", "GITHUB_STEP_SUMMARY")}
    iso = sorted((ROOT / "source").glob("????-??-??.md"))[-1].stem
    veri = ROOT / "data" / "news" / f"{iso}.json"
    once = hashlib.sha256(veri.read_bytes()).hexdigest() if veri.exists() else None
    if py:
        kb = subprocess.run([py, "scripts/check_reports.py", "--kanit-boslugu", "--base", BASE],
                            cwd=ROOT, capture_output=True, text=True, env=env)
        son = [l for l in kb.stdout.splitlines() if "KANIT-BOŞLUĞU:" in l or l.startswith("Kayıt:")]
        print(f"{'ok  ' if kb.returncode == 0 else 'FAIL'} KANIT-BOŞLUĞU --kanit-boslugu normal hâl · "
              f"{' · '.join(x.strip('* ') for x in son) or kb.stderr[-300:]}")
        if kb.returncode:
            fails.append("KANIT-BOŞLUĞU --kanit-boslugu normal")
    bz = subprocess.run([sys.executable, "build.py"], cwd=ROOT, capture_output=True, text=True,
                        env={**env, "BOS_KESISIM": "1"})
    try:
        satirlar = [l.strip() for l in bz.stdout.splitlines()]
        isaret = [l for l in satirlar if l.startswith("⚠ BOS_KESISIM")]
        ana = [l for l in satirlar if l.startswith(f"· KANIT-BOŞLUĞU {iso}:")]
        uy = [l for l in satirlar if l.startswith("! KANIT-BOŞLUĞU ·")]
        say = {f: (ROOT / f).read_text(encoding="utf-8").count('class="rail-not"')
               for f in (f"reports/{iso}.html", "index.html")}
        onceki = sorted((ROOT / "reports").glob("????-??-??.html"))
        onceki = [f for f in onceki if f.stem < iso][-1:]
        onceki_say = onceki[0].read_text(encoding="utf-8").count('class="rail-not"') if onceki else None
        sonra = hashlib.sha256(veri.read_bytes()).hexdigest() if veri.exists() else None
        ok = (bz.returncode == 0 and bool(isaret) and bool(ana) and "kesişim boş (" in ana[0]
              and "BOS_KESISIM, bilerek" in ana[0] and not uy and not any(say.values())
              and onceki_say in (None, 1) and once == sonra)
        print(f"{'ok  ' if ok else 'FAIL'} KANIT-BOŞLUĞU düzenli derleme (BOS_KESISIM=1) · "
              f"{ana[0].lstrip('· ')[:150] if ana else 'satır yok'} · uyarı {len(uy)} · satır {say} · "
              f"önceki gün ({onceki[0].stem if onceki else '—'}) satır {onceki_say} · veri dosyası değişmedi {once == sonra}")
        if not ok:
            fails.append("KANIT-BOŞLUĞU düzenli derleme")
        if py:
            kb = subprocess.run([py, "scripts/check_reports.py", "--kanit-boslugu", "--base", BASE],
                                cwd=ROOT, capture_output=True, text=True, env={**env, "BOS_KESISIM": "1"})
            son = [l for l in kb.stdout.splitlines() if "KANIT-BOŞLUĞU:" in l or l.startswith("Kayıt:")]
            print(f"{'ok  ' if kb.returncode == 0 else 'FAIL'} KANIT-BOŞLUĞU --kanit-boslugu düzenli hâl · "
                  f"{' · '.join(x.strip('* ') for x in son) or kb.stderr[-300:]}")
            if kb.returncode:
                fails.append("KANIT-BOŞLUĞU --kanit-boslugu düzenli")
    finally:
        back = subprocess.run([sys.executable, "build.py"], cwd=ROOT, capture_output=True, text=True, env=env)
        geri = (ROOT / "reports" / f"{iso}.html").read_text(encoding="utf-8").count('class="rail-not"')
        if back.returncode or "BOS_KESISIM" in back.stdout or (iso == "2026-09-23" and geri != 1):
            print("FAIL KANIT-BOŞLUĞU: normal derlemeye dönüş")
            fails.append("rebuild (BOS_KESISIM)")


# Rev 29: tarayıcıda L1-DOLGU / ÇİZGİ-KONTRAST — hesaplanan stil, açık ve koyu, 375 ve 1440.
R29_JS = r"""
import sys, json
from playwright.sync_api import sync_playwright
base, sayfalar = sys.argv[1], sys.argv[2].split(",")
JS = '''() => {
  const rgb = s => (s.match(/[\\d.]+/g) || []).slice(0, 4).map(Number);
  const lum = c => { const v = c.slice(0, 3).map(x => { x /= 255; return x <= 0.04045 ? x / 12.92 : ((x + 0.055) / 1.055) ** 2.4; });
                     return 0.2126 * v[0] + 0.7152 * v[1] + 0.0722 * v[2]; };
  const oran = (a, b) => { const x = lum(a), y = lum(b); return (Math.max(x, y) + 0.05) / (Math.min(x, y) + 0.05); };
  const tok = n => { const d = document.createElement("i"); d.style.backgroundColor = `var(${n})`; document.body.appendChild(d);
                     const c = getComputedStyle(d).backgroundColor; d.remove(); return c; };
  const zemin = new Set([tok("--paper"), tok("--paper-2")]);
  const ihlal = [];
  for (const el of document.querySelectorAll("body *")) {
    const s = getComputedStyle(el);
    if (zemin.has(s.backgroundColor) && s.borderLeftStyle !== "none" && parseFloat(s.borderLeftWidth) > 0)
      ihlal.push(el.tagName.toLowerCase() + (el.id ? "#" + el.id : "") + (el.className ? "." + String(el.className).split(" ")[0] : ""));
  }
  const ol = document.querySelector(".prose h2#ozet + ol");
  const kutu = ol ? [getComputedStyle(ol).borderLeftWidth, getComputedStyle(ol).backgroundColor === tok("--paper-2")] : null;
  const zem = rgb(getComputedStyle(document.body).backgroundColor);
  const h2 = Array.from(document.querySelectorAll(".prose h2, .kicker")).filter(e => e.offsetParent);
  const oranlar = h2.map(e => oran(rgb(getComputedStyle(e).borderTopColor), zem));
  return {ihlal, kutu, h2: h2.length, min: oranlar.length ? Math.min(...oranlar) : null};
}'''
out = {}
with sync_playwright() as p:
    try: b = p.chromium.launch(channel="chrome")
    except Exception: b = p.chromium.launch()
    for sayfa in sayfalar:
        for w, h in ((375, 812), (1440, 900)):
            for cs in ("light", "dark"):
                ctx = b.new_context(service_workers="block", viewport={"width": w, "height": h}, color_scheme=cs)
                pg = ctx.new_page(); pg.goto(base + sayfa, wait_until="load")
                out[f"{sayfa}@{w}/{cs}"] = pg.evaluate(JS); ctx.close()
    b.close()
print(json.dumps(out, ensure_ascii=False))
"""

# Rev 29 R29-P1-2 (S): ilk ziyaret, temiz depolama, service worker AÇIK (shoot.py onları engeller;
# kart serviceWorker.ready + PushManager'a bağlı), 375×812.
R29_KART_JS = r"""
import sys, json
from playwright.sync_api import sync_playwright
url = sys.argv[1]
M = '''() => {
  const c = document.getElementById("notifycard"), b = document.getElementById("notify"),
        ib = document.getElementById("installbar");
  const br = b && !b.hidden ? b.getBoundingClientRect() : null;
  const hit = br ? document.elementFromPoint(br.left + br.width / 2, br.top + br.height / 2) : null;
  return {kart: !c.hidden, konum: getComputedStyle(c).position,
          sonraki: c.nextElementSibling ? c.nextElementSibling.className : "",
          zil: !!(br && br.top >= 0 && br.bottom <= innerHeight && hit && b.contains(hit)),
          zil_ust: br ? Math.round(br.top) : null, kurulum: !ib.hidden,
          kurulum_ust: ib.hidden ? null : Math.round(ib.getBoundingClientRect().top)};
}'''
DIP = "window.scrollTo(0, document.documentElement.scrollHeight)"
with sync_playwright() as p:
    try: b = p.chromium.launch(channel="chrome")
    except Exception: b = p.chromium.launch()
    ctx = b.new_context(service_workers="allow", viewport={"width": 375, "height": 812},
                        is_mobile=True, has_touch=True, locale="tr-TR")
    pg = ctx.new_page(); pg.goto(url, wait_until="load")
    try:
        pg.wait_for_function("!document.getElementById('notifycard').hidden", timeout=15000)
    except Exception:
        pass
    pg.evaluate(DIP); pg.wait_for_timeout(300)
    ilk = pg.evaluate(M)
    pg.wait_for_timeout(2500)               # kurulum çubuğu: kaydırma > 400px → 1,2 s
    pg.evaluate(DIP); pg.wait_for_timeout(300)
    cubuk = pg.evaluate(M)
    if ilk["kart"]:
        pg.click("#notifycard [data-action=later]")
    kapali = pg.evaluate("document.getElementById('notifycard').hidden")
    pg.reload(wait_until="load"); pg.wait_for_timeout(2500)
    sonra = pg.evaluate("document.getElementById('notifycard').hidden")
    b.close()
print(json.dumps({"ilk": ilk, "cubuk": cubuk, "simdi_degil": kapali, "yeniden": sonra}, ensure_ascii=False))
"""


def r29_checks(build_stdout, py, fails):
    """Rev 29: L1-DOLGU · ÇİZGİ-KONTRAST (build satırı, kural kontrolleri, tarayıcı) + ilk ziyaret kartı."""
    import contextlib
    import io
    import json
    sys.path.insert(0, str(ROOT))
    import build as B
    from scripts import uyari
    satirlar = [l.strip() for l in build_stdout.splitlines()]
    l1 = [l for l in satirlar if l.startswith("· L1-DOLGU:")]
    ck = [l for l in satirlar if l.startswith("· ÇİZGİ-KONTRAST:")]
    oranlar = [float(x.replace(",", ".")) for x in re.findall(r"(?:açık|koyu) (\d+,\d+):1", ck[0])] if ck else []
    uy = [l for l in satirlar if l.startswith("! L1-DOLGU") or l.startswith("! ÇİZGİ-KONTRAST")]
    ok = bool(l1) and l1[0].startswith("· L1-DOLGU: 0 ihlal") and len(oranlar) == 2 and min(oranlar) >= 3 and not uy
    print(f"{'ok  ' if ok else 'FAIL'} R29 build · {l1[0].lstrip('· ') if l1 else 'L1-DOLGU satırı yok'} · "
          f"{ck[0].lstrip('· ') if ck else 'ÇİZGİ-KONTRAST satırı yok'}")
    if not ok:
        fails.append("R29 build")

    # Kural kontrolleri: bozulmuş app.css kopyası (dosyaya yazılmaz) → uyari.ekle.
    css = (ROOT / "assets" / "app.css").read_text(encoding="utf-8")
    yedek = {k: os.environ.pop(k) for k in ("GITHUB_STEP_SUMMARY", "RUNNER_TEMP") if k in os.environ}
    try:
        durumlar = []
        for etiket, metin, beklenen in (
                ("özet kutusuna marka kenarı", css + "\n.prose h2#ozet + ol { border-left: 3px solid var(--brand); }", "L1-DOLGU"),
                ("daha uzun seçici kenar ekler", css + "\n.report .prose h2#ozet + ol { border-left: 3px solid var(--brand); }", "L1-DOLGU"),
                (":hover kenar ekler", css + "\n.chip:hover { border-left: 2px solid var(--brand); }", "L1-DOLGU"),
                ("dört kenarlı kutu (border:)", css + "\n.x { background: var(--paper-2); border: 1px solid var(--rule-2); }", None),
                ("Rev 0 --rule-2 değerleri", css.replace("#908E88", "#CAC6BC").replace("#62656B", "#3B4048"), "ÇİZGİ-KONTRAST")):
            del uyari._BELLEK[:]
            with contextlib.redirect_stdout(io.StringIO()):
                B.r29_kurallari(metin)
            kurallar = [k["kural"] for k in uyari._BELLEK]
            durumlar.append((etiket, kurallar, (kurallar == [beklenen]) if beklenen else not kurallar))
        del uyari._BELLEK[:]
    finally:
        os.environ.update(yedek)
    ok = all(d[2] for d in durumlar)
    print(f"{'ok  ' if ok else 'FAIL'} R29 kural kontrolleri · "
          + " · ".join(f"{e} → {', '.join(k) or 'uyarı yok'}" for e, k, _ok in durumlar))
    if not ok:
        fails.append("R29 kural kontrolleri")

    if not py:
        print("FAIL R29 tarayıcı · Playwright'lı python yok")
        fails.append("R29 tarayıcı")
        return
    rapor = latest("reports", "????-??-??.html")
    sayfalar = [rapor, latest("haberler", "????-??-??.html")]
    r = subprocess.run([py, "-c", R29_JS, BASE, ",".join(sayfalar)], cwd=ROOT, capture_output=True, text=True)
    try:
        sonuc = json.loads(r.stdout)
    except ValueError:
        sonuc = {}
    kotu = [f"{k}: {v}" for k, v in sonuc.items()
            if v["ihlal"] or (v["kutu"] is not None and (v["kutu"][0] != "0px" or not v["kutu"][1]))
            or (k.startswith(rapor + "@") and v["kutu"] is None) or v["min"] is None or v["min"] < 3]
    en_dusuk = min((v["min"] for v in sonuc.values() if v["min"]), default=0)
    ok = bool(sonuc) and not kotu
    print(f"{'ok  ' if ok else 'FAIL'} R29 tarayıcı (rapor + medya × 375/1440 × açık/koyu) · "
          + (f"{len(sonuc)}/{len(sonuc)} · özet kutusu kenarsız, --paper-2 zemin · zeminli öğede border-left yok · "
             + f"bölüm çizgisi en düşük {en_dusuk:.2f}:1".replace(".", ",") if ok else str(kotu[:2] or r.stderr[-400:])))
    if not ok:
        fails.append("R29 tarayıcı")

    r = subprocess.run([py, "-c", R29_KART_JS, BASE + rapor], cwd=ROOT, capture_output=True, text=True)
    try:
        k = json.loads(r.stdout)
    except ValueError:
        k = None
    ok = bool(k) and k["ilk"]["kart"] and k["ilk"]["konum"] == "static" and k["ilk"]["sonraki"] == "endnav" \
        and k["ilk"]["zil"] and k["cubuk"]["zil"] and k["simdi_degil"] and k["yeniden"]
    print(f"{'ok  ' if ok else 'FAIL'} R29 ilk ziyaret kartı (375×812, temiz depolama, SW açık) {rapor} · "
          + (f"kart {'görünür' if k['ilk']['kart'] else 'YOK'}, akışta ({k['ilk']['konum']}), ardından "
             f".{k['ilk']['sonraki']} · zil {'görünür' if k['ilk']['zil'] else 'ÖRTÜLÜ'} (üst {k['ilk']['zil_ust']}px) · "
             f"kurulum çubuğu {'açık' if k['cubuk']['kurulum'] else 'kapalı'} (üst {k['cubuk']['kurulum_ust']}px) "
             f"iken zil {'görünür' if k['cubuk']['zil'] else 'ÖRTÜLÜ'} (üst {k['cubuk']['zil_ust']}px) · Şimdi değil → "
             f"{'gizli' if k['simdi_degil'] else 'AÇIK'}, yeniden yüklemede {'gizli' if k['yeniden'] else 'GÖRÜNÜR'}"
             if k else r.stdout[-300:] + r.stderr[-400:]))
    if not ok:
        fails.append("R29 ilk ziyaret kartı")

def r23_checks(build_stdout, fails):
    """Rev 23: kuralların uyarı satırları, etiket = başlık, kural kontrolleri."""
    sys.path.insert(0, str(ROOT))
    import build as B
    src = sorted((ROOT / "source").glob("????-??-??.md"))[-1]
    iso = src.stem
    meta, body = B.split_frontmatter(src.read_text(encoding="utf-8"))
    devs = meta.get("developments") or []
    satir = [l.strip() for l in build_stdout.splitlines() if l.strip().startswith(f"· R23 {iso}")]
    kur = [l.strip() for l in build_stdout.splitlines() if l.strip().startswith("! KUR ·")]
    h1 = [l.strip() for l in build_stdout.splitlines() if l.strip().startswith("! H1-TEKRAR ·")]
    etk = [l.strip() for l in build_stdout.splitlines() if l.strip().startswith("! ETİKET-BAŞLIK ·")]
    if iso == "2026-09-23":   # R23-P1-1 kabulü: bu günün iki uyarısı, etiket uyarısı yok
        ok = (any("SAN CUAS 1,5 milyar $ ↔ özet 1,74" in l for l in kur)
              and any(f"H1-TEKRAR · {iso} · özet 1 " in l for l in h1) and not etk)
    else:
        ok = bool(satir)
    print(f"{'ok  ' if ok else 'FAIL'} R23 uyarıları · {satir[0] if satir else 'satır yok'}")
    for l in kur + h1 + etk:
        print(f"       {l[:170]}")
    if not ok:
        fails.append("R23 uyarıları")
    # Etiket = başlık, yayımlanan sayfanın kendisinde (reports/<gün>.html ve index.html).
    for page in (f"reports/{iso}.html", "index.html"):
        text = (ROOT / page).read_text(encoding="utf-8")
        bulgu = B.etiket_baslik(text, devs)
        heads = len(re.findall(r'<h3 id="g\d+"', text))
        ok = not bulgu and heads > 0
        print(f"{'ok  ' if ok else 'FAIL'} ETİKET-BAŞLIK {page} · {heads} başlık = label"
              + (f" · {bulgu[:2]}" if bulgu else ""))
        if not ok:
            fails.append(f"ETİKET-BAŞLIK {page}")
    # Kural kontrolleri: tetiklemesi gereken tetikler, gerekmeyen susar.
    kb = "### G1 · x\nA 2 milyar $'lık (20 milyar NOK) iş. [K1]\n## KAYNAKLAR\n- [K1] a — https://x.y/z\n"
    iki = B.kur_denetimi(kb, [], {"https://x.y/z": "Anlaşma 20 milyar NOK (2 milyar dolarlık)."})
    tek = B.kur_denetimi(kb, [], {"https://x.y/z": "Anlaşma 20 milyar NOK."})
    celiski = B.kur_denetimi(kb.replace("[K1]\n##", "[K1][K2]\n##") + "- [K2] b — https://x.y/w\n", [],
                             {"https://x.y/z": "20 milyar NOK (2 milyar dolar).", "https://x.y/w": "2,3 milyar dolarlık iş."})
    h1_sus = B.h1_tekrar("Letonya Morana'yı seçti", "## YÖNETİCİ ÖZETİ\n\n1. G1 — Pentagon 17 firmayı seçti.\n")
    h1_ot = B.h1_tekrar("Letonya Morana'yı seçti", "## YÖNETİCİ ÖZETİ\n\n1. G1 — Letonya, Morana obüsünü seçti.\n")
    ok = not iki and len(tek) == 1 and len(celiski) == 1 and "özet 2,3 milyar dolar" in celiski[0] \
        and not h1_sus and len(h1_ot) == 1 and h1_ot[0].startswith("özet 1 ")
    print(f"{'ok  ' if ok else 'FAIL'} R23 kural kontrolleri · KUR (iki değer aynı özette → sus {not iki}, "
          f"biri yok → {len(tek)}, özetler çelişiyor → {len(celiski)}) · H1-TEKRAR (sus {not h1_sus}, örtüşen → {len(h1_ot)})")
    if not ok:
        fails.append("R23 kural kontrolleri")
    return iso, devs


R27_EVAL = ("() => { const q = s => document.querySelector(s), st = q('.thread-status');"
            " const ar = document.querySelectorAll('.daybar-arrow');"
            " return {url: location.pathname + location.search, daybar: q('.daybar-date').innerText,"
            " arrows: [...ar].map(a => a.tagName), status: st ? st.innerText : null,"
            " under: st ? st.getBoundingClientRect().top >= q('h1').getBoundingClientRect().bottom : false,"
            " rows: [...document.querySelectorAll('.thread-entry')].map(li => ({link: !!li.querySelector('a'),"
            " ul: getComputedStyle(li.querySelector('.thread-line')).textDecorationLine,"
            " tag: (li.querySelector('.thread-tag') || {}).innerText || ''})),"
            " overflow: document.documentElement.scrollWidth > innerWidth}; }")

R27_JS = r"""
import json, sys
from playwright.sync_api import sync_playwright
B, EV = sys.argv[1], sys.argv[2]
out = []
with sync_playwright() as p:
    br = p.chromium.launch(channel="chrome")
    for w, h in ((375, 812), (1440, 900)):
        pg = br.new_page(viewport={"width": w, "height": h}, locale="tr-TR")
        for day, needle in (("2026-09-23", "xm30"), ("2026-09-20", None)):
            pg.goto(f"{B}/reports/{day}.html")
            a = pg.locator(f'a.thread-link[href*="{needle}"]' if needle else "li.watch-move a.thread-link").first
            a.scroll_into_view_if_needed(); a.click(); pg.wait_for_load_state("load")
            r = pg.evaluate(EV)
            r["w"], r["from"] = w, day
            out.append(r)
        pg.goto(f"{B}/izleme/xm30-da-organik-c-uas-sarti-18-09-2026-raporu.html?g=1999-01-01")
        out.append({"w": w, "bogus": pg.inner_text(".daybar-date")})
    br.close()
print(json.dumps(out, ensure_ascii=False))
"""


def r27_checks(build_stdout, py, fails):
    """Rev 27: İPLİK-DURUM — build satırı, watch_status() birim, tarayıcı (375/1440), bozuk derleme."""
    import json
    sys.path.insert(0, str(ROOT))
    import build as B
    satir = [l.strip() for l in build_stdout.splitlines() if "· İPLİK-DURUM:" in l]
    ok = bool(satir) and "İPLİK-DURUM: 0 eksik" in satir[0]
    print(f"{'ok  ' if ok else 'FAIL'} İPLİK-DURUM build satırı · {satir[0].lstrip('· ') if satir else 'satır yok'}")
    if not ok:
        fails.append("İPLİK-DURUM build satırı")
    birim = {
        "XM30'da organik C-UAS şartı — *bekliyor.* Prototip teslim edildi, şart hâlâ tanımlı değil (G9).":
            "Prototip teslim edildi, şart hâlâ tanımlı değil.",
        "XM30'da organik C-UAS şartı — *ilerledi (G3).*": "",
        "**G12 · 665 milyon** — *bekliyor.* GAO karar tarihi için bkz. ALARMLAR. [K15]": "",
        "**X (18.09.2026 raporu)** — *bekliyor.* ihale açılmadı (G4).": "İhale açılmadı.",
    }
    yanlis = {k: B.watch_status(k) for k, v in birim.items() if B.watch_status(k) != v}
    print(f"{'ok  ' if not yanlis else 'FAIL'} watch_status() birim durumları · {len(birim) - len(yanlis)}/{len(birim)}"
          + (f" · yanlış: {yanlis}" if yanlis else ""))
    if yanlis:
        fails.append("watch_status birim")
    if not py:
        print("FAIL İPLİK-DURUM tarayıcı · Playwright'lı python yok")
        fails.append("İPLİK-DURUM tarayıcı")
    elif (ROOT / "reports" / "2026-09-23.html").exists():
        r = subprocess.run([py, "-c", R27_JS, BASE, R27_EVAL], cwd=ROOT, capture_output=True, text=True)
        if r.returncode:
            print(f"FAIL İPLİK-DURUM tarayıcı · {r.stderr[-400:]}")
            fails.append("İPLİK-DURUM tarayıcı")
        else:
            for x in json.loads(r.stdout):
                if "bogus" in x:
                    ok = x["bogus"] == "23 Eyl · Çar"
                    print(f"{'ok  ' if ok else 'FAIL'} R27 {x['w']}px bilinmeyen ?g= · daybar “{x['bogus']}”")
                elif x["from"] == "2026-09-23":
                    links = [e for e in x["rows"] if e["link"]]
                    opn = [e for e in x["rows"] if not e["link"]]
                    ok = (x["url"].endswith("?g=2026-09-23") and x["daybar"] == "23 Eyl · Çar" and x["under"]
                          and x["status"] == "Prototip teslim edildi, şart hâlâ tanımlı değil. · 23 Eylül"
                          and len(links) == 4 and all(e["ul"] == "underline" for e in links)
                          and len(opn) == 1 and opn[0]["tag"] == "AÇILDI" and opn[0]["ul"] == "none"
                          and not x["overflow"])
                    print(f"{'ok  ' if ok else 'FAIL'} R27 {x['w']}px XM30 · {x['url'].split('/')[-1]} · daybar "
                          f"“{x['daybar']}” · durum “{x['status']}” · {len(links)} altı çizili bağlantı · "
                          f"açılış {[e['tag'] for e in opn]} altı çizili değil: {all(e['ul'] == 'none' for e in opn)}")
                else:
                    ok = (x["url"].endswith("?g=2026-09-20") and x["daybar"] == "20 Eyl · Paz"
                          and x["arrows"] == ["A", "A"] and not x["overflow"])
                    print(f"{'ok  ' if ok else 'FAIL'} R27 {x['w']}px 20 Eylül'den iplik · {x['url'].split('/')[-1]} · "
                          f"daybar “{x['daybar']}” · oklar {x['arrows']}")
                if not ok:
                    fails.append(f"R27 tarayıcı {x['w']}px")
    boz = subprocess.run([sys.executable, "build.py"], cwd=ROOT, capture_output=True, text=True,
                         env={**os.environ, "IPLIK_BOZ": "1"})
    try:
        uy = [l.strip() for l in boz.stdout.splitlines() if l.strip().startswith("! İPLİK-DURUM ·")]
        ok = boz.returncode == 0 and bool(uy) and "(IPLIK_BOZ=1, bilerek)" in uy[0]
        print(f"{'ok  ' if ok else 'FAIL'} İPLİK-DURUM bozuk derleme (IPLIK_BOZ=1) · {uy[0][:200] if uy else 'uyarı yok'}")
        if not ok:
            fails.append("İPLİK-DURUM bozuk derleme")
    finally:
        back = subprocess.run([sys.executable, "build.py"], cwd=ROOT, capture_output=True, text=True,
                              env={k: v for k, v in os.environ.items() if k != "IPLIK_BOZ"})
        if back.returncode or "İPLİK-DURUM: 0 eksik" not in back.stdout:
            print("FAIL İPLİK-DURUM: normal derlemeye dönüş")
            fails.append("rebuild (İPLİK-DURUM)")


def r26_checks(fails):
    """Rev 26: ÇEVİRİ-DEDEKTÖRÜ — model çağırmayan test, istem, kanıt iş akışı."""
    t = subprocess.run([sys.executable, "scripts/test_ceviri_dedektoru.py"], cwd=ROOT, capture_output=True, text=True)
    son = t.stdout.strip().splitlines()[-1] if t.stdout.strip() else t.stderr[-300:]
    print(f"{'ok  ' if t.returncode == 0 else 'FAIL'} scripts/test_ceviri_dedektoru.py · {son}")
    if t.returncode:
        print(t.stdout[-2500:], t.stderr[-1500:])
        fails.append("test_ceviri_dedektoru.py")
    src = (ROOT / "scripts" / "translate_news.py").read_text(encoding="utf-8")
    ok = ("Cümle düzeni" in src and "her kelimenin ilk harfi büyük" not in src
          and "Hiçbir önermeyi atma" in src and "Konuşan daraltılmaz" in src and "Hürmüz Boğazı" in src)
    print(f"{'ok  ' if ok else 'FAIL'} ÇEVİRİ-DEDEKTÖRÜ istem: cümle düzeni, Ö1, Ö2, Ö3")
    if not ok:
        fails.append("ÇEVİRİ-DEDEKTÖRÜ istem")
    wf = (ROOT / ".github" / "workflows" / "ceviri-dedektoru-test.yml").read_text(encoding="utf-8")
    ok = ("secrets." not in wf and "claude-code" not in wf and "--refresh" not in wf
          and "--sahte-cevirmen" in wf and "UYARI_TEST_ONEK" in wf)
    print(f"{'ok  ' if ok else 'FAIL'} ceviri-dedektoru-test.yml: sır yok, Claude CLI yok, sahte çevirmen")
    if not ok:
        fails.append("ceviri-dedektoru-test.yml")


def k2_check(py, hal, fails):
    """K2: iki oyuncu listesinin etiketleri — "tam" (64/64) ya da "boz" (KAPSAM_BOZ, <64)."""
    rapor = latest("reports", "????-??-??.html")
    # "Bugün N" = günün başlıklarında eşleşen oyuncu sayısı (brifing gövdesi değil).
    sys.path.insert(0, str(ROOT))
    import build as _b, json
    gun = pathlib.Path(rapor).stem
    items = json.loads((ROOT / "data" / "news" / f"{gun}.json").read_text(encoding="utf-8")).get("items", [])
    beklenen = len(set(_b.tag_player_headlines(items)))
    k = subprocess.run([py, "-c", K2_JS, BASE, rapor, hal, str(beklenen)], cwd=ROOT, capture_output=True, text=True)
    print(f"{'ok  ' if k.returncode == 0 else 'FAIL'} K2 etiketler ({hal}, başlıkta eşleşen {beklenen}) · "
          f"{k.stdout.strip() or k.stderr[-400:]}")
    if k.returncode:
        fails.append(f"K2 {hal}")


def main():
    fails = []
    build = subprocess.run([sys.executable, "build.py"], cwd=ROOT, capture_output=True, text=True)
    print(f"{'ok  ' if build.returncode == 0 else 'FAIL'} build.py (exit {build.returncode})")
    if build.returncode:
        print(build.stdout[-2000:], build.stderr[-2000:])
        fails.append("build.py")

    # Rev 23: ETİKET-BAŞLIK · KUR · H1-TEKRAR
    r23_iso, r23_devs = r23_checks(build.stdout, fails)

    # Rev 30: OPERATÖR-YALNIZ — uyari.py sahte GitHub API testi
    t = subprocess.run([sys.executable, "scripts/test_uyari.py"], cwd=ROOT, capture_output=True, text=True)
    print(f"{'ok  ' if t.returncode == 0 else 'FAIL'} scripts/test_uyari.py · {t.stdout.strip().splitlines()[-1] if t.stdout.strip() else ''}")
    if t.returncode:
        print(t.stdout[-2000:], t.stderr[-2000:])
        fails.append("test_uyari.py")

    # Rev 22: DÖRT-DURUM (CI'da bloklayıcı) + kapsam satırı — başsız tarayıcı gerekir
    py = pw_python()
    if not py:
        print("FAIL DÖRT-DURUM · Playwright'lı python yok (DEFINTEL_PW_PYTHON)")
        fails.append("DÖRT-DURUM")
    else:
        dd = subprocess.run([py, "scripts/check_reports.py", "--dort-durum", "--base", BASE],
                            cwd=ROOT, capture_output=True, text=True, env={**os.environ, "DORT_DURUM_BOZ": "none"})
        son = [l for l in dd.stdout.splitlines() if "DÖRT-DURUM:" in l]
        print(f"{'ok  ' if dd.returncode == 0 else 'FAIL'} DÖRT-DURUM · {son[-1].strip('* ') if son else dd.stderr[-300:]}")
        if dd.returncode:
            print(dd.stdout[-2500:], dd.stderr[-1500:])
            fails.append("DÖRT-DURUM")
        kupur = latest("haberler", "????-??-??.html")
        ks = subprocess.run([py, "-c", KAPSAM_JS, BASE + kupur, str(ROOT / kupur.lstrip("/"))],
                            cwd=ROOT, capture_output=True, text=True)
        print(f"{'ok  ' if ks.returncode == 0 else 'FAIL'} kapsam satırı süzgeçle · {ks.stdout.strip() or ks.stderr[-300:]}")
        if ks.returncode:
            fails.append("kapsam satırı")

    # Rev 23 R23-P0-1: 1440px tıklama — izleme bağlantısı → başlık (23 Eylül'de G9)
    if py:
        gid = "g9" if r23_iso == "2026-09-23" else None
        if not gid:
            html_ = (ROOT / "reports" / f"{r23_iso}.html").read_text(encoding="utf-8")
            m = re.search(r'<li class="watch-move">.*?href="#(g\d+)"', html_, re.S)
            gid = m.group(1) if m else None
        if gid:
            et = subprocess.run([py, "-c", ETIKET_JS, f"{BASE}/reports/{r23_iso}.html", gid],
                                cwd=ROOT, capture_output=True, text=True)
            print(f"{'ok  ' if et.returncode == 0 else 'FAIL'} ETİKET-BAŞLIK tıklama · {et.stdout.strip() or et.stderr[-300:]}")
            if et.returncode:
                fails.append("ETİKET-BAŞLIK tıklama")

    # Rev 26: ÇEVİRİ-DEDEKTÖRÜ (model çağrısı yok)
    r26_checks(fails)

    # Rev 31: GEÇ-GELEN
    r31_checks(build.stdout, py, fails)

    # Rev 25: SİLME-YOK · İPUCU-YOK · kategoriler
    r25_checks(build.stdout, py, fails)

    # Rev 33: NOKTALI-İ
    r33_checks(build.stdout, py, fails)

    # Rev 32: TEKRAR-MANŞET
    r32_checks(build.stdout, py, fails)

    # Rev 28: KANIT-BOŞLUĞU
    r28_checks(build.stdout, py, fails)
    r28_bos_kesisim_checks(py, fails)

    # Rev 27: İPLİK-DURUM · iplik sayfası (durum satırı, ?g= daybar, satırlar)
    r27_checks(build.stdout, py, fails)

    # Rev 24: İLK-EKRAN
    r24_checks(py, fails)

    # Rev 29: L1-DOLGU · ÇİZGİ-KONTRAST · ilk ziyaret bildirim kartı
    r29_checks(build.stdout, py, fails)

    # Rev 21: KAPSAM-SAYI — alias testi 64/64 (normal build'in çıktısından)
    m = [l for l in build.stdout.splitlines() if "KAPSAM-SAYI: alias testi" in l]
    ok = bool(m) and "alias testi 64/64" in m[0]
    print(f"{'ok  ' if ok else 'FAIL'} KAPSAM-SAYI · {m[0].strip(' ·') if m else 'satır yok'}")
    if not ok:
        fails.append("KAPSAM-SAYI alias testi")
    if py:
        # 64/64 hâli: sayılar, "N gün", yaş jetonları görünür (check_reports --oyuncular)
        ks = subprocess.run([py, "scripts/check_reports.py", "--oyuncular", "--base", BASE],
                            cwd=ROOT, capture_output=True, text=True)
        satir = [l for l in ks.stdout.splitlines() if l.startswith("| 375px")]
        print(f"{'ok  ' if ks.returncode == 0 else 'FAIL'} KAPSAM-SAYI 64/64 hâli · {satir[0] if satir else ks.stderr[-300:]}")
        if ks.returncode:
            fails.append("KAPSAM-SAYI 64/64")
        k2_check(py, "tam", fails)
        # <64 hâli: bilerek bozulan derleme, denetim, sonra normal derlemeye dönüş
        boz = subprocess.run([sys.executable, "build.py"], cwd=ROOT, capture_output=True, text=True,
                             env={**os.environ, "KAPSAM_BOZ": "thales"})
        try:
            kupur = latest("haberler", "????-??-??.html")
            kk = subprocess.run([py, "-c", KAPSAM_SAYI_JS, BASE, str(ROOT), kupur],
                                cwd=ROOT, capture_output=True, text=True)
            ok = boz.returncode == 0 and "alias testi 63/64" in boz.stdout and kk.returncode == 0
            print(f"{'ok  ' if ok else 'FAIL'} KAPSAM-SAYI <64 hâli (KAPSAM_BOZ=thales) · {kk.stdout.strip() or kk.stderr[-300:]}")
            if not ok:
                fails.append("KAPSAM-SAYI <64")
            # attempt 2: the pipeline's own evidence check in the <64 state — it also opens the
            # Mühimmat chip (R21-P0-2: "izlenen {segment}") and checks the active chip's contrast
            # with the pointer still on it, light and dark.
            ks2 = subprocess.run([py, "scripts/check_reports.py", "--oyuncular", "--base", BASE],
                                 cwd=ROOT, capture_output=True, text=True)
            satir2 = [l for l in ks2.stdout.splitlines() if "Mühimmat" in l and "375px" in l]
            print(f"{'ok  ' if ks2.returncode == 0 else 'FAIL'} KAPSAM-SAYI <64 --oyuncular (Tümü + Mühimmat, açık/koyu) · "
                  f"{satir2[0] if satir2 else ks2.stdout[-300:] + ks2.stderr[-300:]}")
            if ks2.returncode:
                fails.append("KAPSAM-SAYI <64 --oyuncular")
            k2_check(py, "boz", fails)
        finally:
            back = subprocess.run([sys.executable, "build.py"], cwd=ROOT, capture_output=True, text=True,
                                  env={k: v for k, v in os.environ.items() if k != "KAPSAM_BOZ"})
            if back.returncode or "alias testi 64/64" not in back.stdout:
                print("FAIL normal derlemeye dönüş")
                fails.append("rebuild")

    pages = ["/", "/index.html", "/arsiv.html", "/oyuncular.html", "/rakipler.html", "/sw.js",
             "/manifest.webmanifest", latest("reports", "????-??-??.html"),
             latest("haberler", "????-??-??.html"), latest("izleme", "*.html")]
    pages += [f"/data/{p.name}" for p in sorted((ROOT / "data").glob("*.json"))]
    for path in filter(None, pages):
        try:
            with urllib.request.urlopen(BASE + path, timeout=10) as r:
                code, size = r.status, len(r.read())
        except Exception as exc:  # HTTPError, connection refused …
            code, size = getattr(exc, "code", str(exc)), 0
        ok = code == 200 and size > 0
        print(f"{'ok  ' if ok else 'FAIL'} {code} {path} ({size} B)")
        if not ok:
            fails.append(path)

    for name in ("index.html", "arsiv.html", "oyuncular.html", latest("reports", "????-??-??.html")):
        f = ROOT / name.lstrip("/") if name else None
        ok = bool(f) and f.exists() and f.stat().st_size > 0
        print(f"{'ok  ' if ok else 'FAIL'} non-empty {name}")
        if not ok:
            fails.append(f"empty {name}")

    print(f"\n{'SMOKE OK' if not fails else 'SMOKE FAIL: ' + ', '.join(fails)}")
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
