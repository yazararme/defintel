"""Smoke test: build, then the served site answers.

  python3 review/tools/smoke.py

Runs `python3 build.py`, then checks that the main pages and every top-level
/data/*.json answer 200 from http://localhost:8000 (python -m http.server from
the repo root) and that the key HTML files are non-empty. stdlib only.
Later revisions extend CHECKS / PAGES. Exit 1 on any failure.
"""
import pathlib
import subprocess
import sys
import urllib.request

ROOT = pathlib.Path(__file__).resolve().parents[2]
BASE = "http://localhost:8000"


def latest(folder, pattern):
    files = sorted((ROOT / folder).glob(pattern))
    return f"/{folder}/{files[-1].name}" if files else None


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
