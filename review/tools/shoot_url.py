"""Harici sayfa kanıtı (issue, Actions özeti): shoot_url.py OUT_DIR ad=URL ...
Her URL için 1440 ve 375 genişlik, açık ve koyu, tam sayfa."""
import sys
from pathlib import Path
from playwright.sync_api import sync_playwright

out = Path(sys.argv[1]); out.mkdir(parents=True, exist_ok=True)
with sync_playwright() as p:
    b = p.chromium.launch(channel="chrome")
    for arg in sys.argv[2:]:
        name, url = arg.split("=", 1)
        for w, h in [(1440, 900), (375, 812)]:
            for scheme in ["light", "dark"]:
                ctx = b.new_context(viewport={"width": w, "height": h}, color_scheme=scheme)
                pg = ctx.new_page()
                try:
                    pg.goto(url, wait_until="networkidle", timeout=30000)
                except Exception as e:
                    print("uyarı", name, e, file=sys.stderr)
                pg.wait_for_timeout(800)
                pg.screenshot(path=str(out / f"{name}-{w}-{scheme}.png"), full_page=True)
                ctx.close()
        print(name)
    b.close()
