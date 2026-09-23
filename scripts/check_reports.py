"""Structural check for the cross-linked report format — and DÖRT-DURUM (Rev 22).

Run: python3 scripts/check_reports.py [source/2026-09-16.md ...]
Exits non-zero and names the file if anything fails, so a bad report is never
published. Reports without a `developments` list are skipped, not failed.

    python3 scripts/check_reports.py --dort-durum [--out DIR] [--base URL] [--boz AD]

DÖRT-DURUM (bloklayıcı): arama ve süzme dört durumu ayrı söylemeli. Başsız bir
tarayıcıda (Playwright) dört senaryo koşar, her birinin ekran görüntüsü DIR'e
yazılır ve (A) özetine bir satır düşer:

    fetch       data/search.json reddedilir  → arşiv paneli "Arama şu an çalışmıyor"
    noresults   medya takibi, 375px, "xyzzy"  → #noresults görünür
    yukleniyor  search.json 3 sn gecikir      → panel "Aranıyor…"
    sonuc       arşivde "Hanwha"              → ≥1 sonuç satırı

Biri kalırsa çıkış 1 ve `uyari.ekle("DÖRT-DURUM", …)` (Rev 30 kanalı). Site, --base
verilmezse depo kökünden bu süreç içinde rastgele bir yerel porta sunulur.
`--boz AD` (ya da DORT_DURUM_BOZ) tarayıcıya giden app.js'i yolda değiştirip o senaryonun
eski hatasını geri getirir — diske ve depoya hiçbir şey yazılmaz; kırmızı çalıştırma kanıtı
bozuk commit atmadan böyle üretilir. Tarayıcı: Playwright'ın chromium'u, yoksa sistem
Chrome'u (channel="chrome").
"""
import http.server
import os
import pathlib
import re
import sys


ROOT = pathlib.Path(__file__).resolve().parent.parent
ANCHOR_PATTERNS = (
    r"^###\s+{gid}\s*·",           # GELİŞMELER heading
    r"^-\s+\*\*{gid}\s*·",         # RAKİP / İZLEME item
)


def check(path):
    import yaml   # yalnız yapı denetimi için; DÖRT-DURUM onsuz koşar

    text = path.read_text(encoding="utf-8")
    problems = []
    try:
        _, fm, body = text.split("---", 2)
        meta = yaml.safe_load(fm) or {}
    except Exception as exc:
        return [f"front matter parse failed: {exc}"]

    developments = meta.get("developments")
    if not developments:
        return []
    if not isinstance(developments, list):
        return ["developments is not a list"]

    for dev in developments:
        gid = str(dev.get("id", "")).strip()
        if not gid:
            problems.append("a development has no id")
            continue
        hits = sum(
            len(re.findall(p.format(gid=re.escape(gid)), body, re.M))
            for p in ANCHOR_PATTERNS
        )
        if hits != 1:
            problems.append(f"{gid}: expected exactly one anchor in the body, found {hits}")

    sources = set(re.findall(r"^-\s+\[K(\d+)\]", body, re.M))
    for cited in set(re.findall(r"\[K(\d+)\]", body)):
        if cited not in sources:
            problems.append(f"[K{cited}] cited but missing from KAYNAKLAR")

    return problems


# ── DÖRT-DURUM ───────────────────────────────────────────────────────────────

DD_SENARYOLAR = ("fetch", "noresults", "yukleniyor", "sonuc")
DD_BEKLENEN = {
    "fetch": "fetch reddedildi → “Arama şu an çalışmıyor”, “kayıt yok” değil",
    "noresults": "medya takibi 375px, “xyzzy” → #noresults görünür",
    "yukleniyor": "3 sn gecikme → “Aranıyor…”",
    "sonuc": "“Hanwha” → ≥1 sonuç",
}
# boz=AD: app.js'teki bu metin yolda eskisiyle değiştirilir (ilk öğe bulunmazsa senaryo
# "boz uygulanamadı" diye kırmızı olur — sessizce yeşil kalmaz).
DD_BOZ = {
    "fetch": ("throw err; /* DÖRT-DURUM:fetch */", "index = []; return index;"),
    "noresults": ('if (el.id === "noresults") break; /* DÖRT-DURUM:noresults */', ""),
    "yukleniyor": ("var SLOW_MS = 300; /* DÖRT-DURUM:yukleniyor */", "var SLOW_MS = 1e9;"),
    "sonuc": ("var hit = match(r, term); /* DÖRT-DURUM:sonuc */", "var hit = false;"),
}
HATA_METNI = "Arama şu an çalışmıyor"


class _Sessiz(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *a):
        pass


def _sun():
    """Depo kökünü rastgele bir yerel porttan sun (ayrı iş parçacığı)."""
    import functools
    import threading
    srv = http.server.ThreadingHTTPServer(
        ("127.0.0.1", 0), functools.partial(_Sessiz, directory=str(ROOT)))
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    return srv, f"http://127.0.0.1:{srv.server_address[1]}"


def _son_kupur():
    files = sorted((ROOT / "haberler").glob("????-??-??.html"))
    return f"/haberler/{files[-1].name}" if files else None


async def _dd_senaryo(browser, base, ad, boz, out):
    import asyncio
    mobil = ad == "noresults"
    ctx = await browser.new_context(
        viewport={"width": 375, "height": 812} if mobil else {"width": 1440, "height": 900},
        service_workers="block", locale="tr-TR")
    page = await ctx.new_page()
    boz_bulunamadi = []
    try:
        if boz == ad:
            eski, yeni = DD_BOZ[ad]

            async def app_js(route):
                resp = await route.fetch()
                body = await resp.text()
                if eski not in body:
                    boz_bulunamadi.append(eski)
                await route.fulfill(response=resp, body=body.replace(eski, yeni),
                                    headers={**resp.headers, "cache-control": "no-store"})
            await page.route("**/assets/app.js*", app_js)
        if ad == "fetch":
            await page.route("**/data/search.json*", lambda route: route.abort("failed"))
        if ad == "yukleniyor":
            async def gecik(route):
                await asyncio.sleep(3)
                await route.continue_()
            await page.route("**/data/search.json*", gecik)

        yol = _son_kupur() if mobil else "/arsiv.html"
        if not yol:
            return False, "medya takibi sayfası yok", None
        await page.goto(base + yol, wait_until="load")
        await page.wait_for_timeout(300)
        terim = {"noresults": "xyzzy"}.get(ad, "Hanwha")
        await page.fill("#q", terim)

        if ad == "yukleniyor":
            await page.wait_for_timeout(1000)          # eşik 300ms, gecikme 3 sn
        elif ad == "sonuc":
            try:
                await page.wait_for_selector(".found-row, .found-none", timeout=8000)
            except Exception:
                pass
        else:
            await page.wait_for_timeout(1200)

        gorunen = await page.evaluate("document.body.innerText")
        panel = await page.evaluate(
            "(document.querySelector('.found') || {}).innerText || ''")
        if ad == "fetch":
            ok = HATA_METNI in gorunen and "kayıt yok" not in gorunen \
                and "eşleşen" not in gorunen
            detay = f"panel: “{panel.strip()[:80]}”"
        elif ad == "noresults":
            ok = await page.is_visible("#noresults")
            if ok:
                await page.evaluate(
                    "document.getElementById('noresults').scrollIntoView({block:'center'})")
            metin = (await page.inner_text("#noresults")).strip() if ok else ""
            detay = f"#noresults {'görünür' if ok else 'görünmüyor'}" + (f": “{metin}”" if ok else "")
        elif ad == "yukleniyor":
            ok = "Aranıyor…" in panel
            detay = f"1 sn sonra panel: “{panel.strip()[:80]}”"
        else:
            n = await page.locator(".found-row").count()
            ok = n >= 1
            detay = f"{n} sonuç satırı"
        if boz_bulunamadi:
            ok, detay = False, f"boz uygulanamadı: app.js'te “{boz_bulunamadi[0][:50]}” yok"
        resim = None
        if out:
            resim = out / f"{DD_SENARYOLAR.index(ad) + 1}-{ad}.png"
            await page.screenshot(path=str(resim))
        return ok, detay, resim
    finally:
        await ctx.close()


async def _dd_kos(base, boz, out):
    from playwright.async_api import async_playwright
    async with async_playwright() as p:
        kanal = os.environ.get("DORT_DURUM_KANAL")
        try:
            browser = await (p.chromium.launch(channel=kanal) if kanal else p.chromium.launch())
        except Exception:   # paketli chromium yok (yerel Mac): sistem Chrome'u
            browser = await p.chromium.launch(channel="chrome")
        try:
            sonuc = {}
            for ad in DD_SENARYOLAR:
                try:
                    sonuc[ad] = await _dd_senaryo(browser, base, ad, boz, out)
                except Exception as e:   # noqa: BLE001 — senaryo çökmesi de kırmızıdır
                    sonuc[ad] = (False, f"senaryo çöktü: {str(e).splitlines()[0][:160]}", None)
            return sonuc
        finally:
            await browser.close()


def dort_durum(base=None, boz="none", out=None):
    import asyncio
    boz = (boz or "none").strip() or "none"
    if boz != "none" and boz not in DD_SENARYOLAR:
        print(f"--boz: bilinmeyen senaryo {boz!r} ({', '.join(DD_SENARYOLAR)} ya da none)")
        return 2
    out = pathlib.Path(out) if out else None
    if out:
        out.mkdir(parents=True, exist_ok=True)
    srv = None
    if not base:
        srv, base = _sun()
    try:
        sonuc = asyncio.run(_dd_kos(base.rstrip("/"), boz, out))
    finally:
        if srv:
            srv.shutdown()

    kalan = [ad for ad in DD_SENARYOLAR if not sonuc[ad][0]]
    ozet = ["### DÖRT-DURUM — arama durumları (Rev 22, bloklayıcı)", ""]
    if boz != "none":
        ozet += [f"> ⚠️ **boz={boz}** — bu çalıştırmada `{boz}` senaryosu bilerek bozuldu"
                 " (app.js yolda değiştirildi; depoda bozuk kod yok).", ""]
    ozet += ["| # | senaryo | beklenen | sonuç | gözlenen | görüntü |", "|---|---|---|---|---|---|"]
    for i, ad in enumerate(DD_SENARYOLAR, 1):
        ok, detay, resim = sonuc[ad]
        ozet.append(f"| {i} | `{ad}` | {DD_BEKLENEN[ad]} | {'🟢 geçti' if ok else '🔴 kaldı'}"
                    f" | {detay.replace('|', '/')} | {resim.name if resim else '—'} |")
    ozet += ["", f"**{'🟢 DÖRT-DURUM: 4/4 yeşil' if not kalan else f'🔴 DÖRT-DURUM: {len(kalan)} senaryo kaldı — build durdu'}**", ""]
    metin = "\n".join(ozet) + "\n"
    print(metin)
    yol = os.environ.get("GITHUB_STEP_SUMMARY")
    if yol:
        with open(yol, "a", encoding="utf-8") as fh:
            fh.write(metin)
    if kalan:
        sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
        import uyari
        for ad in kalan:
            ek = f" (boz={boz}, bilerek)" if boz != "none" else ""
            uyari.ekle("DÖRT-DURUM", f"{ad} kaldı{ek}: {DD_BEKLENEN[ad]} — gözlenen: {sonuc[ad][1]}")
        return 1
    return 0


def main(argv):
    if "--dort-durum" in argv:
        import argparse
        ap = argparse.ArgumentParser()
        ap.add_argument("--dort-durum", action="store_true")
        ap.add_argument("--out")
        ap.add_argument("--base")
        ap.add_argument("--boz", default=os.environ.get("DORT_DURUM_BOZ", "none"))
        a = ap.parse_args(argv)
        return dort_durum(a.base, a.boz, a.out)
    paths = [pathlib.Path(a) for a in argv] or sorted((ROOT / "source").glob("*.md"))
    failed = False
    for path in paths:
        problems = check(path)
        status = "ok" if not problems else "FAIL"
        print(f"{path.name}: {status}")
        for p in problems:
            print(f"    - {p}")
            failed = True
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
