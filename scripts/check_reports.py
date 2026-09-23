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

    python3 scripts/check_reports.py --oyuncular [--out DIR] [--base URL]

KAPSAM-SAYI kanıtı (Rev 21): /oyuncular.html'i 375×812 ve 1440×900'de (tam sayfa)
çeker, `1-oyuncular-375.png` / `2-oyuncular-1440.png` olarak DIR'e yazar ve sayfanın
kendi hâline (data-kapsam) uyup uymadığını (A) özetine yazar: 64/64'ün altındaysa üst
satır yalnız "izlenen N", hiçbir satırda "gün"/"önce"/"bugün" yok, sıra alfabetik;
64/64'te "Bugün N" ve "N gün" görünür. Ayrıca (R21-P0-2) "Mühimmat" çipi açıkken açık ve
koyu temada `3-…6-oyuncular-muhimmat-*.png` çeker: üst satırdaki "izlenen N" ekrandaki
satır sayısına ve o segmentteki oyuncu sayısına eşit olmalı; imleç çipin üstündeyken
etkin çipin yazı/zemin kontrastı ≥ 4.5:1 olmalı. Uymazsa çıkış 1.
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


OY_SEG = ("muhimmat", "Mühimmat")   # R21-P0-2 kanıtı: bu çip açıkken üst satır yeniden sayılır

OY_BILGI_JS = """() => {
    const on = document.querySelector('.pchip.pchip--on');
    const cs = on ? getComputedStyle(on) : null;
    return {
    kapsam: (document.querySelector('.player-list') || {dataset: {}}).dataset.kapsam || '',
    tally: (document.getElementById('ptally') || {}).innerText || '',
    rows: Array.from(document.querySelectorAll('.player-row')).filter(r => !r.hidden).map(r => r.innerText),
    names: Array.from(document.querySelectorAll('.player-row')).filter(r => !r.hidden)
                .map(r => (r.querySelector('.pname') || {}).innerText || ''),
    toplam: document.querySelectorAll('.player-row').length,
    segde: Array.from(document.querySelectorAll('.player-row'))
                .filter(r => (r.dataset.seg || '').split(/\\s+/).includes(%r)).length,
    cip: on ? on.innerText.trim() : '',
    cip_renk: cs ? [cs.color, cs.backgroundColor] : [],
}}""" % OY_SEG[0]


async def _oyuncular_kos(base, out):
    """Her genişlikte: (1) açılış hâli, açık tema; (2) "Mühimmat" çipi açık, açık ve koyu tema.
    Çipe tıklandıktan sonra imleç çipin üstünde bırakılır — telefonda dokunuştan sonra
    kalan :hover hâli budur; etkin çipin yazısı o hâlde de okunmalı."""
    from playwright.async_api import async_playwright
    async with async_playwright() as p:
        try:
            browser = await p.chromium.launch()
        except Exception:   # paketli chromium yok (yerel Mac): sistem Chrome'u
            browser = await p.chromium.launch(channel="chrome")
        sonuc = []
        genislik = ((375, 812), (1440, 900))
        try:
            for tur, tema, no in (("tumu", "light", 1), ("seg", "light", 3), ("seg", "dark", 5)):
                for i, (w, h) in enumerate(genislik):
                    ctx = await browser.new_context(viewport={"width": w, "height": h},
                                                    service_workers="block", locale="tr-TR",
                                                    color_scheme=tema)
                    page = await ctx.new_page()
                    await page.goto(base + "/oyuncular.html", wait_until="load")
                    await page.wait_for_timeout(300)
                    ad = f"oyuncular-{w}" if tur == "tumu" else \
                        f"oyuncular-{OY_SEG[0]}-{w}" + ("-koyu" if tema == "dark" else "")
                    if tur == "seg":
                        await page.click(f'.pchip[data-seg="{OY_SEG[0]}"]')
                        await page.wait_for_timeout(250)   # renk geçişi (.12s) bitsin
                    bilgi = await page.evaluate(OY_BILGI_JS)
                    resim = None
                    if out:
                        resim = out / f"{no + i}-{ad}.png"
                        await page.screenshot(path=str(resim), full_page=True)
                    sonuc.append((w, tur, tema, bilgi, resim))
                    await ctx.close()
        finally:
            await browser.close()
        return sonuc


def _renk(css):
    m = re.findall(r"[\d.]+", css or "")
    return tuple(float(x) for x in m[:3]) if len(m) >= 3 else None


def _kontrast(a, b):
    def lum(c):
        v = [x / 255 for x in c]
        v = [x / 12.92 if x <= 0.03928 else ((x + 0.055) / 1.055) ** 2.4 for x in v]
        return 0.2126 * v[0] + 0.7152 * v[1] + 0.0722 * v[2]
    la, lb = sorted((lum(a), lum(b)), reverse=True)
    return (la + 0.05) / (lb + 0.05)


_TR_KOLAT = None


def _tr_anahtar(ad):
    """build.py'nin tr_collate'i — sayfayı sıralayan fonksiyonun kendisi. build.py'yi içe
    aktarmadan (markdown/yaml gerektirir) yalnız TR_ALPHABET ve tr_collate çekilir."""
    global _TR_KOLAT
    if _TR_KOLAT is None:
        import ast
        agac = ast.parse((ROOT / "build.py").read_text(encoding="utf-8"))
        parca = [d for d in agac.body
                 if (isinstance(d, ast.FunctionDef) and d.name == "tr_collate")
                 or (isinstance(d, ast.Assign) and any(getattr(t, "id", "") == "TR_ALPHABET" for t in d.targets))]
        ad_alani = {}
        exec(compile(ast.Module(body=parca, type_ignores=[]), "build.py", "exec"), ad_alani)
        _TR_KOLAT = ad_alani["tr_collate"]
    return _TR_KOLAT(ad)


def oyuncular(base=None, out=None):
    """KAPSAM-SAYI (S) kanıtı: iki genişlikte ekran görüntüsü + hâl denetimi."""
    import asyncio
    out = pathlib.Path(out) if out else None
    if out:
        out.mkdir(parents=True, exist_ok=True)
    srv = None
    if not base:
        srv, base = _sun()
    try:
        sonuc = asyncio.run(_oyuncular_kos(base.rstrip("/"), out))
    finally:
        if srv:
            srv.shutdown()
    ozet = ["### KAPSAM-SAYI — /oyuncular.html görüntüleri (Rev 21)", "",
            "| genişlik | çip | kapsam | üst satır | ilk iki satır | denetim | görüntü |",
            "|---|---|---|---|---|---|---|"]
    kalan = 0
    for w, tur, tema, b, resim in sonuc:
        m = re.fullmatch(r"(\d+)/(\d+)", b["kapsam"])
        tam = bool(m) and m.group(1) == m.group(2)
        tally = " ".join(b["tally"].split())
        sayili = [r for r in b["rows"] if re.search(r"\d+ gün|önce|bugün|dün|\bkez\b", r)]
        gorunen = len(b["rows"])
        notlar = [f"{len(sayili)} satırda sayı/jeton"]
        if not m:
            ok, notlar = False, ["data-kapsam yok"]
        elif tam:
            ok = tally.startswith("Bugün ") and "son 30 günde" in tally and bool(sayili)
        else:
            ok = (re.fullmatch(r"izlenen \d+", tally) is not None and not sayili)
            if tur == "tumu":   # R21-P0-1: alfabetik sıra
                ok = ok and b["names"] == sorted(b["names"], key=_tr_anahtar)
        # "izlenen N" her iki hâlde de ekrandaki satırları sayar (R21-P0-2)
        iz = re.search(r"izlenen (\d+)$", tally)
        if tur == "seg":
            fg, bg = _renk((b["cip_renk"] or [None, None])[0]), _renk((b["cip_renk"] or [None, None])[1])
            k = _kontrast(fg, bg) if fg and bg else 0
            ok = (ok and iz is not None and int(iz.group(1)) == gorunen == b["segde"] < b["toplam"]
                  and b["cip"] == OY_SEG[1] and k >= 4.5)
            notlar.append(f"izlenen = görünen {gorunen} = segmentte {b['segde']} / {b['toplam']}")
            notlar.append(f"etkin çip “{b['cip']}” kontrast {k:.1f}:1 (imleç üstünde)")
        else:
            ok = ok and iz is not None and int(iz.group(1)) == gorunen == b["toplam"]
        kalan += not ok
        cip = "Tümü" if tur == "tumu" else f"{OY_SEG[1]} ({'koyu' if tema == 'dark' else 'açık'})"
        ozet.append(f"| {w}px | {cip} | {b['kapsam'] or '—'} | {tally} | {', '.join(b['names'][:2])}"
                    f" | {'🟢' if ok else '🔴'} {'; '.join(notlar)} | {resim.name if resim else '—'} |")
    ozet.append("")
    metin = "\n".join(ozet) + "\n"
    print(metin)
    yol = os.environ.get("GITHUB_STEP_SUMMARY")
    if yol:
        with open(yol, "a", encoding="utf-8") as fh:
            fh.write(metin)
    return 1 if kalan else 0


def main(argv):
    if "--oyuncular" in argv:
        import argparse
        ap = argparse.ArgumentParser()
        ap.add_argument("--oyuncular", action="store_true")
        ap.add_argument("--out")
        ap.add_argument("--base")
        a = ap.parse_args(argv)
        return oyuncular(a.base, a.out)
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
