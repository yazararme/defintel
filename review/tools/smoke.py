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


# Rev 22 R22-P1-2: ?oyuncu=<kimlik> ile kapsam satırı "{görünen} / {toplam} başlık" olur,
# süzgeç kalkınca "{toplam} başlık"a döner. Kimlik sayfadaki ilk data-oyuncu'dan.
KAPSAM_JS = r"""
import re, sys
from playwright.sync_api import sync_playwright
url = sys.argv[1]
html = open(sys.argv[2], encoding="utf-8").read()
who = re.search(r'data-oyuncu="([^" ]+)', html).group(1)
with sync_playwright() as p:
    try: b = p.chromium.launch()
    except Exception: b = p.chromium.launch(channel="chrome")
    pg = b.new_context(service_workers="block").new_page()
    pg.goto(url + "?oyuncu=" + who); pg.wait_for_timeout(600)
    on = pg.inner_text(".news-stat > .num")
    gorunen = pg.evaluate("Array.from(document.querySelectorAll('[data-search]')).filter(e => !e.hidden).length")
    roket = None
    if 'roketsan' in html:
        pg.goto(url + "?oyuncu=roketsan"); pg.wait_for_timeout(600)
        roket = pg.inner_text(".news-stat > .num")
        pg.goto(url + "?oyuncu=" + who); pg.wait_for_timeout(600)
    pg.click(".pill-x"); pg.wait_for_timeout(200)
    off = pg.inner_text(".news-stat > .num")
    b.close()
ok = re.fullmatch(r"\d+ / \d+", on) and re.fullmatch(r"\d+", off) and on.endswith("/ " + off)
# Pay = görünen satır sayısı (Rev 22 attempt 2); roketsan kabulü "2 / {toplam}".
ok = ok and on.split(" / ")[0] == str(gorunen)
if roket is not None:
    ok = ok and roket == "2 / " + off
print(f"{who}: '{on} başlık' (görünen satır {gorunen}) → × → '{off} başlık'"
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

    # Rev 31: GEÇ-GELEN
    r31_checks(build.stdout, py, fails)

    # Rev 33: NOKTALI-İ
    r33_checks(build.stdout, py, fails)

    # Rev 32: TEKRAR-MANŞET
    r32_checks(build.stdout, py, fails)

    # Rev 24: İLK-EKRAN
    r24_checks(py, fails)

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
