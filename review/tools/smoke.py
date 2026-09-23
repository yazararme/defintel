"""Smoke test: build, then the served site answers.

  python3 review/tools/smoke.py

Runs `python3 build.py`, then checks that the main pages and every top-level
/data/*.json answer 200 from http://localhost:8000 (python -m http.server from
the repo root) and that the key HTML files are non-empty. stdlib only; the Rev 22
DÖRT-DURUM and scope-line checks need a Playwright python (DEFINTEL_PW_PYTHON or
~/.local/share/defintel-shotenv/bin/python).
Later revisions extend CHECKS / PAGES. Exit 1 on any failure.
"""
import os
import pathlib
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
    pg.click(".pill-x"); pg.wait_for_timeout(200)
    off = pg.inner_text(".news-stat > .num")
    b.close()
ok = re.fullmatch(r"\d+ / \d+", on) and re.fullmatch(r"\d+", off) and on.endswith("/ " + off)
print(f"{who}: '{on} başlık' → × → '{off} başlık'")
sys.exit(0 if ok else 1)
"""


def main():
    fails = []
    build = subprocess.run([sys.executable, "build.py"], cwd=ROOT, capture_output=True, text=True)
    print(f"{'ok  ' if build.returncode == 0 else 'FAIL'} build.py (exit {build.returncode})")
    if build.returncode:
        print(build.stdout[-2000:], build.stderr[-2000:])
        fails.append("build.py")

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
