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
