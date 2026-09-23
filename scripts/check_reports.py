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

    python3 scripts/check_reports.py --ilk-ekran [--out DIR] [--base URL] [--gun G ...] [--boz]

İLK-EKRAN (Rev 24, uyarı kuralı — bloklamaz): brifingi (varsayılan: reports/ altındaki son
gün) 375×812'de açar, ilk ekranın görüntüsünü `ilk-ekran-<gün>-375x812.png` olarak DIR'e
yazar ve (A) özetine ölçülen iki kenarı yazar: özet başlığının (`h2#ozet` — brifte
`h2#yonetici-ozeti` diye anılan, sayfadaki kimliği `ozet`) üst kenarı ≤300px, özetin 4.
maddesinin alt kenarı ≤812px (özet 4 maddeden kısaysa son maddesi). Uymazsa her gün için
`uyari.ekle("İLK-EKRAN", …)` ve çıkış 1. `--boz` (ya da ILK_EKRAN_BOZ=1) tarayıcıya giden
app.css'te `/* İLK-EKRAN:ray */` satırını yolda değiştirip rayı yeniden özetin üstüne
taşır — diske ve depoya hiçbir şey yazılmaz; işaret bulunmazsa gün kırmızı olur.

    python3 scripts/check_reports.py --ilk-ekran --tani [--base URL] [--gun G ...]

İLK-EKRAN tanı (K5, bilgi amaçlı — uyarı yazmaz, çıkış 0): son 10 brifingin (ya da --gun)
375×812'deki ilk ekran bütçesi — başlık satırı, alarm bandı ve ALARMLAR yüksekliği, ilk 4
maddenin satırları — ve günün taşma nedeni (metin / yapı), bir de rapor isteminin sınırları
(manşet ≤75, özet maddesi ≤110 karakter) uygulansaydı kenarlar: sayfa tarayıcıda kısaltılmış
sahte bir kopyayla ölçülür, yerel ve CI en kötü hâlde (0,15px harf aralığı + jeton kendi
satırında). Tablo (A) özetine.

    python3 scripts/check_reports.py --kanit-boslugu [--out DIR] [--base URL] [--gun G] [--bos-kesisim]

KANIT-BOŞLUĞU kanıtı (Rev 28): brifingi (varsayılan: son rapor) 375×812 ve 1440×900'de tam
sayfa, rayın kendisini ayrıca, ve günün Kaynaklar sayfasını 375'te çeker
(`kanit-boslugu-<gün>-…png`; BOS_KESISIM açıkken adlar `-bos-kesisim` ile biter). Beklenen
hâl sayfadan değil kayıttan hesaplanır: data/news/<gün>.json failures[].source ∩ rakipler.json
`kaynak`. `--bos-kesisim` (ya da BOS_KESISIM=1) build.py'nin aynı düzenlemesini beklentiye
uygular — oyuncu kaynakları yanıt vermiş sayılır, öteki başarısız kaynaklar kalır. Denetim:
Tarama bloğu var; kesişim doluysa bloğun içinde tek `.rail-not` ve cümlede her ad, boşsa hiç
`.rail-not` yok ve Kaynaklar sayfasında soluk (başarısız) satır ≥1 (gün gerçekten taranmış,
arızası var, ama hiçbiri oyuncu kaynağı değil). (A) özetine tablo; uymazsa çıkış 1.
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


# ── İLK-EKRAN (Rev 24) ───────────────────────────────────────────────────────

IE_EKRAN = (375, 812)
IE_H2_SINIR = 300        # özet başlığının üst kenarı ≤ bu
IE_MADDE = 4             # özetin bu maddesinin alt kenarı ≤ ekran yüksekliği
# boz: app.css'teki bu satır yolda değiştirilir — ray tek sütunda yeniden özetin
# (ve başlığın) önüne geçer. İşaret bulunmazsa gün "boz uygulanamadı" diye kırmızı
# olur; bozulmamış bir çalıştırma yeşil görünüp kanıt yerine geçemez.
IE_BOZ = ("  .report-grid > .rail { order: 1; margin: 0; }   /* İLK-EKRAN:ray */",
          "  .report-grid > .rail { order: -2; margin: 0 0 22px; }")

IE_OLC_JS = """(n) => {
    const h2 = document.querySelector('.prose h2#ozet');
    const lis = h2 && h2.nextElementSibling && h2.nextElementSibling.tagName === 'OL'
        ? Array.from(h2.nextElementSibling.children) : [];
    const li = lis[Math.min(n, lis.length) - 1];
    const ray = document.querySelector('.report-grid > .rail');
    const rr = ray && ray.getClientRects().length ? ray.getBoundingClientRect() : null;
    return {
      h2: h2 ? h2.getBoundingClientRect().top : null,
      madde: li ? li.getBoundingClientRect().bottom : null,
      madde_n: lis.length,
      ray: rr ? rr.top : null,
      ray_metin: rr ? ray.innerText.replace(/\\s+/g, ' ').trim().slice(0, 60) : '',
      tasma: document.documentElement.scrollWidth > window.innerWidth,
    };
}"""


def _son_rapor():
    files = sorted((ROOT / "reports").glob("????-??-??.html"))
    return files[-1].stem if files else None


async def _ie_kos(base, gunler, boz, out):
    from playwright.async_api import async_playwright
    async with async_playwright() as p:
        try:
            browser = await p.chromium.launch()
        except Exception:   # paketli chromium yok (yerel Mac): sistem Chrome'u
            browser = await p.chromium.launch(channel="chrome")
        sonuc = []
        try:
            for gun in gunler:
                w, h = IE_EKRAN
                ctx = await browser.new_context(viewport={"width": w, "height": h},
                                                service_workers="block", locale="tr-TR")
                page = await ctx.new_page()
                bulunamadi = []
                if boz:
                    async def app_css(route):
                        resp = await route.fetch()
                        body = await resp.text()
                        if IE_BOZ[0] not in body:
                            bulunamadi.append(IE_BOZ[0].strip())
                        await route.fulfill(response=resp, body=body.replace(*IE_BOZ),
                                            headers={**resp.headers, "cache-control": "no-store"})
                    await page.route("**/assets/app.css*", app_css)
                try:
                    await page.goto(f"{base}/reports/{gun}.html", wait_until="load")
                    await page.evaluate("document.fonts ? document.fonts.ready.then(() => 1) : 1")
                    await page.wait_for_timeout(200)
                    b = await page.evaluate(IE_OLC_JS, IE_MADDE)
                    resim = None
                    if out:
                        resim = out / f"ilk-ekran-{gun}-{w}x{h}{'-boz' if boz else ''}.png"
                        await page.screenshot(path=str(resim))
                    sonuc.append((gun, b, bulunamadi, resim))
                except Exception as e:   # noqa: BLE001 — sayfa açılamadıysa da kırmızı
                    sonuc.append((gun, {"hata": str(e).splitlines()[0][:160]}, bulunamadi, None))
                finally:
                    await ctx.close()
        finally:
            await browser.close()
        return sonuc


def ilk_ekran(base=None, gunler=None, boz=False, out=None):
    """İLK-EKRAN: 375×812'de özet başlığı ≤300px, özetin 4. maddesinin alt kenarı ≤812px.
    Kalırsa `uyari.ekle("İLK-EKRAN", …)` (Rev 30 kanalı, bloklamaz) ve çıkış 1."""
    import asyncio
    gunler = list(gunler or []) or [g for g in [_son_rapor()] if g]
    if not gunler:
        print("İLK-EKRAN: reports/ altında rapor yok")
        return 1
    out = pathlib.Path(out) if out else None
    if out:
        out.mkdir(parents=True, exist_ok=True)
    srv = None
    if not base:
        srv, base = _sun()
    try:
        sonuc = asyncio.run(_ie_kos(base.rstrip("/"), gunler, boz, out))
    finally:
        if srv:
            srv.shutdown()

    w, h = IE_EKRAN
    ozet = [f"### İLK-EKRAN — yöneticinin ilk ekranı, {w}×{h} (Rev 24)", ""]
    if boz:
        ozet += ["> ⚠️ **ilk_ekran_boz** — bu çalıştırmada ray sırası bilerek geri alındı"
                 " (app.css yolda değiştirildi; depoda bozuk kod yok).", ""]
    ozet += [f"| gün | `h2#ozet` üst kenarı (≤{IE_H2_SINIR}) | özetin {IE_MADDE}. maddesi alt kenarı"
             f" (≤{h}) | ray üst kenarı | sonuç | görüntü |", "|---|---|---|---|---|---|"]
    kalan = []
    for gun, b, bulunamadi, resim in sonuc:
        if "hata" in b:
            ok, neden = False, f"sayfa ölçülemedi: {b['hata']}"
            h2 = madde = ray = "—"
        else:
            sorun = []
            if b["h2"] is None:
                sorun.append("h2#ozet yok")
            elif b["h2"] > IE_H2_SINIR:
                sorun.append(f"özet başlığı {b['h2']:.0f}px > {IE_H2_SINIR}")
            if b["madde"] is None:
                sorun.append("özet listesi yok")
            elif b["madde"] > h:
                sorun.append(f"{min(IE_MADDE, b['madde_n'])}. madde alt kenarı {b['madde']:.0f}px > {h}")
            if b["tasma"]:
                sorun.append("sayfa yatay taşıyor")
            if bulunamadi:
                sorun = [f"boz uygulanamadı: app.css'te “{bulunamadi[0][:60]}” yok"]
            ok, neden = not sorun, "; ".join(sorun)
            h2 = f"{b['h2']:.0f}px" if b["h2"] is not None else "—"
            madde = (f"{b['madde']:.0f}px" if b["madde"] is not None else "—") + \
                (f" ({b['madde_n']} maddelik özet)" if b["madde_n"] < IE_MADDE else "")
            ray = f"{b['ray']:.0f}px" if b["ray"] is not None else "gizli"
        if not ok:
            kalan.append((gun, neden))
        ozet.append(f"| {gun} | {h2} | {madde} | {ray} | {'🟢 geçti' if ok else '🔴 ' + neden.replace('|', '/')}"
                    f" | {resim.name if resim else '—'} |")
    ozet += ["", f"**{'🟢 İLK-EKRAN: ' + str(len(sonuc)) + '/' + str(len(sonuc)) + ' gün geçti' if not kalan else f'🔴 İLK-EKRAN: {len(kalan)} gün kaldı — uyarı Rev 30 kanalına'}**", ""]
    metin = "\n".join(ozet) + "\n"
    print(metin)
    yol = os.environ.get("GITHUB_STEP_SUMMARY")
    if yol:
        with open(yol, "a", encoding="utf-8") as fh:
            fh.write(metin)
    if kalan:
        sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
        import uyari
        ek = " (ilk_ekran_boz, ray bilerek geri taşındı)" if boz else ""
        for gun, neden in kalan:
            uyari.ekle("İLK-EKRAN", f"{gun} brifingi {w}×{h}{ek}: {neden}")
        return 1
    return 0


# ── İLK-EKRAN tanı (K5) ──────────────────────────────────────────────────────
# Her gün için ilk ekranın piksel bütçesi ve taşmanın nedeni; bir de rapor isteminin
# sınırları (review/builder-notes/k5-prompt.md) uygulansaydı kenarların nerede olacağı.
# Tahmin tarayıcıdaki sahte bir kopyadır: başlık ve özet maddeleri sınıra (kelime
# sınırında) kısaltılır, "ilk:" jetonları yerinde kalır; yayımlanan sayfa ve veri değişmez.
# "CI en kötü": başlık, bant ve özette 0,15px harf aralığı + her jeton kendi satırında —
# Ubuntu Chromium'un daha geniş kırılımını yeniden üretir (Rev 32 deneme 2: 23 Eyl'de 817).

IE_BASLIK_KR = 75        # istem: manşet en fazla 75 karakter (375'te 3 satır; 4 satırlıklar 80–83)
IE_OZET_KR = 110         # istem: her özet maddesi en fazla 110 karakter
IE_TANI_GUN = 10
IE_SATIR_BUTCE_H2 = 280  # 3 satırlık başlıkla h2#ozet'in üst kenarı (masthead 49 + daybar 49 +
                         # ızgara 8 + başlık 9+3×31,9 + şerit 8+51 + 10)

IE_TANI_JS = """([ls, brk, h1kr, kr]) => {
  const st = document.createElement('style');
  if (ls) st.textContent = `.prose h2#ozet + ol, .report-title, .alarmbar, .prose > p { letter-spacing: ${ls}px !important; }`;
  document.head.appendChild(st);
  const kes = (el, n) => {
    if (!el || !n) return;
    const jeton = Array.from(el.querySelectorAll('a.ilk'));
    jeton.forEach(a => a.remove());
    const t = el.textContent.replace(/\\s+/g, ' ').trim();
    if (t.length > n) {
      let s = '';
      for (const w of t.split(' ')) { if ((s + ' ' + w).trim().length > n) break; s = (s + ' ' + w).trim(); }
      el.textContent = s;
    }
    jeton.forEach(a => { el.append(' '); el.append(a); });
  };
  kes(document.querySelector('.report-title'), h1kr);
  const h2 = document.querySelector('.prose h2#ozet');
  const lis = h2 && h2.nextElementSibling && h2.nextElementSibling.tagName === 'OL'
      ? Array.from(h2.nextElementSibling.children) : [];
  lis.forEach(li => kes(li, kr));
  if (brk) document.querySelectorAll('h2#ozet + ol a.ilk').forEach(a => a.before(document.createElement('br')));
  const R = e => e.getBoundingClientRect();
  const satir = e => { const c = getComputedStyle(e);
    const ic = R(e).height - parseFloat(c.paddingTop) - parseFloat(c.paddingBottom)
               - parseFloat(c.borderTopWidth) - parseFloat(c.borderBottomWidth);
    return Math.round(ic / parseFloat(c.lineHeight)); };
  const metin = e => e.textContent.replace(/\\s+/g, ' ').replace(/ ?ilk: \\d+ \\S+/g, '').trim();
  const h1 = document.querySelector('.report-title');
  const bant = document.querySelector('.alarmbar');
  const al = document.querySelector('.prose h2#alarmlar');
  const ilk4 = lis.slice(0, 4);
  return {
    h2: h2 ? R(h2).top : null,
    madde: ilk4.length ? R(ilk4[ilk4.length - 1]).bottom : null,
    madde_n: lis.length,
    h1: [satir(h1), metin(h1).length],
    bant: bant ? [Math.round(R(bant).height + parseFloat(getComputedStyle(bant).marginBottom)), satir(bant)] : null,
    alarmlar: al && h2 ? Math.round(R(h2).top - R(al).top) : null,
    maddeler: ilk4.map(li => [satir(li), metin(li).length, li.querySelectorAll('a.ilk').length]),
  };
}"""


async def _tani_kos(base, gunler):
    from playwright.async_api import async_playwright
    async with async_playwright() as p:
        try:
            browser = await p.chromium.launch()
        except Exception:
            browser = await p.chromium.launch(channel="chrome")
        sonuc = []
        try:
            for gun in gunler:
                olc = {}
                for ad, arg in (("yerel", [0, 0, 0, 0]),
                                ("sinir", [0, 0, IE_BASLIK_KR, IE_OZET_KR]),
                                ("sinir_ci", [0.15, 1, IE_BASLIK_KR, IE_OZET_KR])):
                    ctx = await browser.new_context(viewport={"width": IE_EKRAN[0], "height": IE_EKRAN[1]},
                                                    service_workers="block", locale="tr-TR")
                    page = await ctx.new_page()
                    try:
                        await page.goto(f"{base}/reports/{gun}.html", wait_until="load")
                        await page.evaluate("document.fonts ? document.fonts.ready.then(() => 1) : 1")
                        await page.wait_for_timeout(150)
                        olc[ad] = await page.evaluate(IE_TANI_JS, arg)
                    except Exception as e:   # noqa: BLE001
                        olc[ad] = {"hata": str(e).splitlines()[0][:160]}
                    finally:
                        await ctx.close()
                sonuc.append((gun, olc))
        finally:
            await browser.close()
        return sonuc


def _tani_neden(b):
    """Günün taşma nedeni, ölçülen bütçeden. Eşikler İLK-EKRAN'ınkiyle aynı."""
    w, h = IE_EKRAN
    neden = []
    if b["bant"] or b["alarmlar"]:
        neden.append(f"yapı: alarm bandı {b['bant'][0] if b['bant'] else 0}px + ALARMLAR "
                     f"{b['alarmlar'] or 0}px özetten önce")
    if b["h1"][0] > 3:
        neden.append(f"metin: başlık {b['h1'][0]} satır ({b['h1'][1]} kr.)")
    # 4 madde, h2 3 satırlık başlığın yerinde (280) olsaydı sığar mıydı?
    if b["madde"] - b["h2"] > h - IE_SATIR_BUTCE_H2:
        uzun = max(m[1] for m in b["maddeler"])
        neden.append(f"metin: ilk 4 madde {sum(m[0] for m in b['maddeler'])} satır (en uzunu {uzun} kr.)")
    ok = b["h2"] <= IE_H2_SINIR and b["madde"] <= h
    return ok, ("; ".join(neden) if not ok else "—") or "—"


def ilk_ekran_tani(base=None, gunler=None):
    """K5: son 10 brifingin ilk ekran bütçesi, nedeni ve istem sınırlarıyla tahmini — (A) özetine.
    Bilgi amaçlı: uyarı yazmaz, çıkış 0 (sayfa açılamadıysa 1)."""
    import asyncio
    gunler = list(gunler or []) or [f.stem for f in sorted((ROOT / "reports").glob("????-??-??.html"))[-IE_TANI_GUN:]]
    srv = None
    if not base:
        srv, base = _sun()
    try:
        sonuc = asyncio.run(_tani_kos(base.rstrip("/"), gunler))
    finally:
        if srv:
            srv.shutdown()
    w, h = IE_EKRAN
    ozet = [f"### İLK-EKRAN tanı — son {len(gunler)} brifing, {w}×{h} (K5)", "",
            f"Eşikler değişmedi: `h2#ozet` üst ≤{IE_H2_SINIR}px, 4. madde alt ≤{h}px. Bütçe: masthead + "
            f"daybar 98px, 3 satırlık başlıkla özet başlığı {IE_SATIR_BUTCE_H2}px; her başlık satırı +32px, "
            "her özet satırı +26px. Son sütun, rapor istemindeki sınırlar (manşet ≤"
            f"{IE_BASLIK_KR}, özet maddesi ≤{IE_OZET_KR} karakter) uygulansaydı: tarayıcıda kısaltılmış "
            "sahte kopya; \"CI\" = 0,15px harf aralığı + her \"ilk:\" jetonu kendi satırında.", "",
            "| gün | h2 üst | 4. madde alt | başlık | alarm (bant · ALARMLAR) | ilk 4 madde (satır · en uzun) "
            "| neden | sınır uygulansaydı (yerel · CI en kötü) |",
            "|---|---|---|---|---|---|---|---|"]
    hata = 0
    for gun, o in sonuc:
        b, s, c = o.get("yerel", {}), o.get("sinir", {}), o.get("sinir_ci", {})
        if any("hata" in x or not x or x.get("h2") is None for x in (b, s, c)):
            hata += 1
            ozet.append(f"| {gun} | — | — | — | — | — | 🔴 ölçülemedi | — |")
            continue
        ok, neden = _tani_neden(b)
        alarm = (f"{b['bant'][0] if b['bant'] else 0}px · {b['alarmlar'] or 0}px"
                 if (b["bant"] or b["alarmlar"]) else "—")
        maddeler = (f"{sum(m[0] for m in b['maddeler'])} satır "
                    f"({'+'.join(str(m[0]) for m in b['maddeler'])}) · {max(m[1] for m in b['maddeler'])} kr.")
        tahmin = all(x["h2"] <= IE_H2_SINIR and x["madde"] <= h for x in (s, c))
        ozet.append(
            f"| {gun} | {b['h2']:.0f}px | {b['madde']:.0f}px | {b['h1'][0]} satır · {b['h1'][1]} kr. | {alarm} "
            f"| {maddeler} | {'🟢 geçti' if ok else '🔴 ' + neden} "
            f"| {'🟢' if tahmin else '🔴'} {s['h2']:.0f}/{s['madde']:.0f} · {c['h2']:.0f}/{c['madde']:.0f} |")
    ozet.append("")
    metin = "\n".join(ozet) + "\n"
    print(metin)
    yol = os.environ.get("GITHUB_STEP_SUMMARY")
    if yol:
        with open(yol, "a", encoding="utf-8") as fh:
            fh.write(metin)
    return 1 if hata else 0


# ── KANIT-BOŞLUĞU (Rev 28) ───────────────────────────────────────────────────

KB_JS = """() => {
    const t = [...document.querySelectorAll('.rail-label')].find(e => e.textContent.trim() === 'Tarama');
    const blok = t ? t.parentElement : null;
    const n = [...document.querySelectorAll('.rail-not')];
    return {
      tarama: blok ? ('Tarama ' + ((blok.querySelector('.rail-value') || {}).innerText || '')).replace(/\\s+/g, ' ').trim() : null,
      adet: n.length,
      metin: n.map(e => e.innerText.trim()),
      blokta: n.length ? !!(blok && blok.contains(n[0])) : null,
      soluk: document.querySelectorAll('.srow--off').length,
      tasma: document.documentElement.scrollWidth > window.innerWidth,
    };
}"""


def _kb_beklenen(gun, bos_kesisim):
    """(yol listesi: [oyuncu kaynağı], kalan başarısız kaynak sayısı) — kayıttan."""
    import json
    yol = ROOT / "data" / "news" / f"{gun}.json"
    if not yol.exists():
        return None, 0
    veri = json.loads(yol.read_text(encoding="utf-8"))
    kaynaklar = {r["kaynak"] for r in json.loads((ROOT / "data" / "rakipler.json").read_text(encoding="utf-8"))["rakipler"]
                 if r.get("kaynak")}
    failed = [f.get("source") for f in veri.get("failures") or [] if f.get("source")]
    if bos_kesisim:
        failed = [f for f in failed if f not in kaynaklar]
    return sorted(set(failed) & kaynaklar), len(failed)


async def _kb_kos(base, gun, ek, out):
    from playwright.async_api import async_playwright
    async with async_playwright() as p:
        try:
            browser = await p.chromium.launch()
        except Exception:   # paketli chromium yok (yerel Mac): sistem Chrome'u
            browser = await p.chromium.launch(channel="chrome")
        sonuc = []
        try:
            for yol, ad, (w, h) in ((f"/reports/{gun}.html", "brifing", (375, 812)),
                                    (f"/reports/{gun}.html", "brifing", (1440, 900)),
                                    (f"/haberler/{gun}-kaynaklar.html", "kaynaklar", (375, 812))):
                ctx = await browser.new_context(viewport={"width": w, "height": h},
                                                service_workers="block", locale="tr-TR")
                page = await ctx.new_page()
                resimler = []
                try:
                    r = await page.goto(base + yol, wait_until="load")
                    await page.evaluate("document.fonts ? document.fonts.ready.then(() => 1) : 1")
                    await page.wait_for_timeout(200)
                    b = await page.evaluate(KB_JS)
                    b["durum"] = r.status if r else None
                    if out:
                        onek = f"kanit-boslugu-{gun}" + ("-kaynaklar" if ad == "kaynaklar" else "") + f"-{w}"
                        resim = out / f"{onek}{ek}.png"
                        await page.screenshot(path=str(resim), full_page=True)
                        resimler.append(resim)
                        ray = page.locator(".report-grid > .rail")
                        if ad == "brifing" and await ray.count():
                            resim = out / f"kanit-boslugu-{gun}-ray-{w}{ek}.png"
                            await ray.first.screenshot(path=str(resim))
                            resimler.append(resim)
                    sonuc.append((ad, w, b, resimler))
                except Exception as e:   # noqa: BLE001 — açılamadıysa da kırmızı
                    sonuc.append((ad, w, {"hata": str(e).splitlines()[0][:160]}, resimler))
                finally:
                    await ctx.close()
        finally:
            await browser.close()
        return sonuc


def kanit_boslugu(base=None, gun=None, bos_kesisim=False, out=None):
    """KANIT-BOŞLUĞU (S) kanıtı: brifing 375/1440 + ray + Kaynaklar; hâl kayda uymalı."""
    import asyncio
    gun = gun or _son_rapor()
    if not gun:
        print("KANIT-BOŞLUĞU: reports/ altında rapor yok")
        return 1
    beklenen, kalan_hata = _kb_beklenen(gun, bos_kesisim)
    out = pathlib.Path(out) if out else None
    if out:
        out.mkdir(parents=True, exist_ok=True)
    ek = "-bos-kesisim" if bos_kesisim else ""
    srv = None
    if not base:
        srv, base = _sun()
    try:
        sonuc = asyncio.run(_kb_kos(base.rstrip("/"), gun, ek, out))
    finally:
        if srv:
            srv.shutdown()
    ozet = [f"### KANIT-BOŞLUĞU — {gun} brifingi ve Kaynaklar (Rev 28)", ""]
    if bos_kesisim:
        ozet += ["> ⚠️ **bos_kesisim** — bu derlemede oyuncu kaynakları yanıt vermiş sayıldı (yalnız bellekte;"
                 " data/news değişmedi). Kesişim hesaplandı ve boş; satır basılmamalı.", ""]
    if beklenen is None:
        ozet += [f"🔴 {gun}: medya takibi yok — kesişim hesaplanamaz", ""]
        kalan = [("—", "medya takibi yok")]
    else:
        ozet += [f"Kayıt: {kalan_hata} başarısız kaynak · oyuncu kaynaklarıyla kesişim: "
                 f"{', '.join(beklenen) if beklenen else '∅ (boş)'} → satır {'1' if beklenen else 'yok'}", "",
                 "| sayfa | genişlik | Tarama bloğu | satır | denetim | görüntü |", "|---|---|---|---|---|---|"]
        kalan = []
        for ad, w, b, resimler in sonuc:
            sorun = []
            if "hata" in b:
                sorun.append(f"açılamadı: {b['hata']}")
            elif b.get("durum") != 200:
                sorun.append(f"HTTP {b.get('durum')}")
            elif ad == "brifing":
                if not b["tarama"]:
                    sorun.append("Tarama bloğu yok")
                if beklenen:
                    if b["adet"] != 1 or not b["blokta"] or not all(k in b["metin"][0] for k in beklenen):
                        sorun.append(f"satır beklenen 1 (Tarama bloğunda, {', '.join(beklenen)}), bulunan {b['adet']}")
                elif b["adet"]:
                    sorun.append(f"kesişim boş ama {b['adet']} satır var")
            else:
                if not beklenen and b["soluk"] < 1:
                    sorun.append("soluk (başarısız) satır yok — boş kesişim arızasız bir gün değil")
            if "hata" not in b and b.get("tasma"):
                sorun.append("yatay taşma")
            if sorun:
                kalan.append((f"{ad} {w}", "; ".join(sorun)))
            satir = ("—" if ad != "brifing" or "hata" in b else
                     (f"“{b['metin'][0]}”" if b["adet"] else "yok"))
            tarama = b.get("tarama") if ad == "brifing" else f"{b.get('soluk', '—')} soluk satır"
            ozet.append(f"| {ad} | {w}px | {tarama or '—'} | {satir} | "
                        f"{'🟢' if not sorun else '🔴 ' + '; '.join(sorun).replace('|', '/')} | "
                        f"{', '.join(r.name for r in resimler) or '—'} |")
        ozet.append("")
    ozet += [f"**{'🟢 KANIT-BOŞLUĞU: sayfa kayda uyuyor' if not kalan else f'🔴 KANIT-BOŞLUĞU: {len(kalan)} denetim kaldı'}**", ""]
    metin = "\n".join(ozet) + "\n"
    print(metin)
    yol = os.environ.get("GITHUB_STEP_SUMMARY")
    if yol:
        with open(yol, "a", encoding="utf-8") as fh:
            fh.write(metin)
    return 1 if kalan else 0


def main(argv):
    if "--kanit-boslugu" in argv:
        import argparse
        ap = argparse.ArgumentParser()
        ap.add_argument("--kanit-boslugu", action="store_true")
        ap.add_argument("--out")
        ap.add_argument("--base")
        ap.add_argument("--gun", help="YYYY-MM-DD (varsayılan: reports/ altındaki son rapor)")
        ap.add_argument("--bos-kesisim", action="store_true",
                        default=(os.environ.get("BOS_KESISIM") or "").strip().lower()
                        not in ("", "0", "none", "false"))
        a = ap.parse_args(argv)
        env_gun = (os.environ.get("BOS_KESISIM") or "").strip()
        if not a.gun and a.bos_kesisim and re.fullmatch(r"\d{4}-\d{2}-\d{2}", env_gun):
            a.gun = env_gun   # build.py'nin düzenlediği gün
        return kanit_boslugu(a.base, a.gun, a.bos_kesisim, a.out)
    if "--ilk-ekran" in argv:
        import argparse
        ap = argparse.ArgumentParser()
        ap.add_argument("--ilk-ekran", action="store_true")
        ap.add_argument("--out")
        ap.add_argument("--base")
        ap.add_argument("--gun", nargs="*", default=[],
                        help="YYYY-MM-DD (varsayılan: reports/ altındaki son rapor)")
        ap.add_argument("--boz", action="store_true",
                        default=os.environ.get("ILK_EKRAN_BOZ", "0") == "1")
        ap.add_argument("--tani", action="store_true")
        a = ap.parse_args(argv)
        if a.tani:
            return ilk_ekran_tani(a.base, a.gun)
        return ilk_ekran(a.base, a.gun, a.boz, a.out)
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
