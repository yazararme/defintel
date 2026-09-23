"""Ekran görüntüsü: her sayfa × 375×812 / 1440×900 × açık / koyu.

Kullanım:
  <venv>/bin/python review/tools/shoot.py OUT_DIR [yol ...]

Yol verilmezse varsayılan sayfa kümesi çekilir. Site http://localhost:8000'de
çalışıyor olmalı. Her kombinasyon için iki dosya: ilk ekran (NAME.png) ve tam
sayfa (NAME-full.png). Playwright sistemdeki Chrome'u kullanır (channel="chrome").
"""
import re
import sys
from pathlib import Path

from playwright.sync_api import sync_playwright

BASE = "http://localhost:8000"
DEFAULT = [
    "/",
    "/reports/2026-09-23.html",
    "/haberler/2026-09-23.html",
    "/haberler/2026-09-23-kaynaklar.html",
    "/arsiv.html",
    "/oyuncular.html",
    "/rakipler.html",
    "/izleme/abd-ordusu-50-mm-namlulu-c-uas-arayisi.html",
]
SIZES = [(375, 812), (1440, 900)]
SCHEMES = ["light", "dark"]


def slug(path):
    s = re.sub(r"[^a-z0-9]+", "-", path.lower().replace(".html", "")).strip("-")
    return s or "index"


def main():
    out = Path(sys.argv[1])
    out.mkdir(parents=True, exist_ok=True)
    paths = sys.argv[2:] or DEFAULT
    with sync_playwright() as p:
        browser = p.chromium.launch(channel="chrome")
        for path in paths:
            for w, h in SIZES:
                for scheme in SCHEMES:
                    ctx = browser.new_context(
                        viewport={"width": w, "height": h},
                        color_scheme=scheme,
                        device_scale_factor=1,
                        is_mobile=(w < 600),
                        has_touch=(w < 600),
                        locale="tr-TR",
                        service_workers="block",
                    )
                    page = ctx.new_page()
                    try:
                        page.goto(BASE + path, wait_until="networkidle", timeout=20000)
                    except Exception as e:  # sayfa yine de çekilsin
                        print(f"uyarı {path}: {e}", file=sys.stderr)
                    page.wait_for_timeout(400)
                    name = f"{slug(path)}-{w}-{scheme}"
                    page.screenshot(path=str(out / f"{name}.png"))
                    page.screenshot(path=str(out / f"{name}-full.png"), full_page=True)
                    ctx.close()
            print(path)
        browser.close()


if __name__ == "__main__":
    main()
