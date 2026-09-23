#!/usr/bin/env python3
"""GEÇ-GELEN testi (Rev 31): collect_news.py ağsız, kayıtlı başlıklarla.

    python3 scripts/test_collect.py                 # tüm senaryolar, çıkış 1 = kırmızı
    python3 scripts/test_collect.py hazirla DIR     # iş akışı adımları için sınama dosyaları
    python3 scripts/test_collect.py yerel-aday GÜN  # GÜN'ün verisinden GÜN+1 aday.md (yalnız yerel kanıt)

Aynı gün iki kez toplanır (05:19 ve 11:04, 24 Eylül); ikinci çalıştırmada akıştan bir kalem
düşer, bir yeni kalem gelir. Kırmızı koşullar:

  1. ikinci çalıştırma "yeni: 1 · değişmedi: 5 · damga değişti: 0" değil
  2. var olan kalemin damgası, çeviri alanı ya da kendisi değişti / akıştan düşen kalem silindi
  3. dünkü brifingden (23 Eylül 06:16) sonra gelen kalemler aday dosyasının ilk bölümünde değil
     ya da 260 sınırı o bölümü kesiyor
  4. damga bilerek değiştirilince GEÇ-GELEN uyarısı çıkmıyor; ilk bölümden kalem eksikken çıkmıyor
  5. sınama yolu requests/feedparser/google yüklüyor (ağa çıkabilir) ya da data/news'e yazıyor

Her çalıştırma ayrı süreç, kendi RUNNER_TEMP'i ve özet dosyasıyla: uyarılar işin gerçek
kanalına sızmaz. Yalnızca stdlib. CI'da `$GITHUB_STEP_SUMMARY`'ye 🟢/🔴 satırı ekler.
"""
import json
import os
import pathlib
import shutil
import subprocess
import sys
import tempfile

ROOT = pathlib.Path(__file__).resolve().parents[1]
COLLECT = ROOT / "scripts" / "collect_news.py"
sys.path.insert(0, str(ROOT / "scripts"))
import collect_news as C  # noqa: E402

GUN, DUN = "2026-09-24", "2026-09-23"
SABAH, OGLE = "2026-09-24T05:19:00+03:00", "2026-09-24T11:04:00+03:00"
AA_URL = ("https://www.aa.com.tr/tr/ekonomi/aselsan-ile-roketsan-arasinda-1-2-milyar-avroluk-"
          "sozlesme-imzalandi/4065836")

KAYNAKLAR = [
    {"ad": "Anadolu Ajansı — güncel", "tur": "rss", "ulke": "TR", "dil": "tr", "kademe": "C"},
    {"ad": "Defence Blog", "tur": "rss", "ulke": "US", "dil": "en", "kademe": "A"},
    {"ad": "Naval News", "tur": "rss", "ulke": "FR", "dil": "en", "kademe": "A"},
    {"ad": "Kırık Kaynak", "tur": "rss", "ulke": "XX", "dil": "en", "kademe": "C"},
    {"ad": "Kapalı Kaynak", "tur": "rss", "test": {"sonuc": "kapali"}},
]
SABAH_AKIS = {
    "Anadolu Ajansı — güncel": {"items": [
        {"title": "ASELSAN ile ROKETSAN arasında 1,2 milyar avroluk sözleşme imzalandı",
         "url": AA_URL, "published": "2026-09-23T10:40:00+03:00"}]},
    "Defence Blog": {"items": [
        {"title": "Israeli shoulder-fired missile moves toward U.S. qualification",
         "url": "https://defence-blog.com/israeli-shoulder-fired-missile/", "published": "2026-09-23"},
        {"title": "U.S. puts Ukraine-tested interceptor drones through border tests",
         "url": "https://defence-blog.com/interceptor-drones-border/", "published": "2026-09-23"},
        {"title": "Old artillery story outside the 48 hour window",
         "url": "https://defence-blog.com/old-artillery/", "published": "2026-09-20"}]},
    "Naval News": {"items": [
        {"title": "Belgium's second rMCM ship Tournai arrives in Zeebrugge",
         "url": "https://www.navalnews.com/tournai/", "published": "2026-09-23"},
        {"title": "Mk 48 torpedo launch from British underwater drone",
         "url": "https://www.navalnews.com/mk48-uuv/?utm=x", "published": "2026-09-23"}]},
    "Kırık Kaynak": {"error": "ConnectionError: sınama"},
}
# 11:04: Naval News akışından bir kalem düştü (silinmemeli), Defence Blog'a bir yeni kalem geldi.
OGLE_AKIS = json.loads(json.dumps(SABAH_AKIS))
OGLE_AKIS["Naval News"]["items"] = OGLE_AKIS["Naval News"]["items"][:1]
OGLE_AKIS["Defence Blog"]["items"].insert(0, {
    "title": "Roketsan unveils new 155 mm guided artillery round",
    "url": "https://defence-blog.com/roketsan-155-guided/", "published": "2026-09-24"})


def _dun_kalemi(title, url, stamp, source="Defence Blog"):
    return {"title": title, "url": url, "source": source, "country": "", "lang": "en",
            "tier": "A", "published": DUN, "category": "Genel Savunma Gündemi", "also": [],
            "ilk_goruldu": stamp}


DUN_DOSYASI = {"date": DUN, "window_hours": 48, "scanned_sources": 4, "failed_sources": 0,
               "unique_items": 4, "items": [
    _dun_kalemi("Early item seen by the briefing", "https://ex.com/early-1", "2026-09-23T05:19:10+03:00"),
    _dun_kalemi("Another early item seen by the briefing", "https://ex.com/early-2", "2026-09-23T05:19:10+03:00"),
    _dun_kalemi("ASELSAN ile ROKETSAN arasında 1,2 milyar avroluk sözleşme imzalandı", AA_URL,
                "2026-09-23T11:04:23+03:00", "Anadolu Ajansı — güncel"),
    _dun_kalemi("Britain forms squadron to strike threats in orbit", "https://ex.com/late-2",
                "2026-09-23T11:04:23+03:00"),
]}
YAYIN = {DUN: "06:16"}


def hazirla(d):
    """Sınama dosyaları: sabah.json, ogle.json, published.json ve out/ içinde dünün dosyası."""
    d = pathlib.Path(d)
    (d / "out").mkdir(parents=True, exist_ok=True)
    (d / "sabah.json").write_text(json.dumps({"sources": KAYNAKLAR, "feeds": SABAH_AKIS},
                                             ensure_ascii=False, indent=1), encoding="utf-8")
    (d / "ogle.json").write_text(json.dumps({"sources": KAYNAKLAR, "feeds": OGLE_AKIS},
                                            ensure_ascii=False, indent=1), encoding="utf-8")
    (d / "published.json").write_text(json.dumps(YAYIN), encoding="utf-8")
    (d / "out" / f"{DUN}.json").write_text(json.dumps(DUN_DOSYASI, ensure_ascii=False, indent=1),
                                           encoding="utf-8")
    return d


def toplama(d, fixture, now, *extra):
    """collect_news.py'yi ayrı süreçte, ağ kütüphaneleri yüklenemez hâlde koştur."""
    d = pathlib.Path(d)
    tuzak = d / "tuzak"
    tuzak.mkdir(exist_ok=True)
    for mod in ("requests", "feedparser", "google"):
        (tuzak / f"{mod}.py").write_text(f"raise ImportError('sınama yolu {mod} yükledi — ağa çıkabilir')\n")
    rt = d / "rt"
    rt.mkdir(exist_ok=True)
    ozet = d / "ozet.md"
    ozet.write_text("")
    env = {**os.environ, "PYTHONPATH": str(tuzak), "RUNNER_TEMP": str(rt),
           "GITHUB_STEP_SUMMARY": str(ozet)}
    r = subprocess.run([sys.executable, str(COLLECT), "--fixture", str(d / fixture),
                        "--out", str(d / "out"), "--date", GUN, "--now", now,
                        "--published", str(d / "published.json"), *extra],
                       capture_output=True, text=True, env=env)
    uyari = (rt / "defintel-uyari.jsonl")
    kayit = [json.loads(l) for l in uyari.read_text().splitlines()] if uyari.exists() else []
    if uyari.exists():
        uyari.unlink()
    return r, ozet.read_text(encoding="utf-8"), kayit


def kalemler(d):
    return json.loads((pathlib.Path(d) / "out" / f"{GUN}.json").read_text(encoding="utf-8"))["items"]


def main():
    sonuc, sayim2 = [], "—"

    def kontrol(ad, ok, ayrinti=""):
        sonuc.append(bool(ok))
        print(f"{'ok  ' if ok else 'FAIL'} {ad}" + (f" · {ayrinti}" if ayrinti else ""))

    data_news_once = sorted(p.name for p in C.OUT_DIR.iterdir())
    with tempfile.TemporaryDirectory() as tmp:
        d = hazirla(tmp)

        # 1 · sabah toplaması (günün ilki)
        r1, ozet1, u1 = toplama(d, "sabah.json", SABAH)
        kontrol("1. toplama çıkış 0", r1.returncode == 0, r1.stderr[-300:])
        kontrol("1. toplama sayımı", "yeni: 5 · değişmedi: 0 · damga değişti: 0" in r1.stdout,
                next((l.strip() for l in r1.stdout.splitlines() if "yeni:" in l), "satır yok"))
        k1 = kalemler(d) if r1.returncode == 0 else []
        kontrol("1. toplama: her kalem 05:19 damgalı",
                k1 and all(i.get("ilk_goruldu") == "2026-09-24T05:19:00+03:00" for i in k1))
        kontrol("1. toplama: 48 saat dışı kalem alınmadı",
                not any("old-artillery" in i["url"] for i in k1))
        kontrol("1. toplama: uyarı yok", not u1, str(u1))

        # çeviri adımı bir alan eklemiş olsun — ikinci toplama onu ezmemeli
        f = d / "out" / f"{GUN}.json"
        veri = json.loads(f.read_text(encoding="utf-8"))
        for i in veri["items"]:
            i["title_tr"] = "ÇEVİRİ · " + i["title"]
        f.write_text(json.dumps(veri, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
        once = {C.url_key(i["url"]): json.dumps(i, sort_keys=True) for i in veri["items"]}

        # 2 · öğle yedeği (aynı gün, bir kalem düştü, bir kalem yeni)
        r2, ozet2, u2 = toplama(d, "ogle.json", OGLE)
        satir = next((l.strip() for l in r2.stdout.splitlines() if "yeni:" in l), "satır yok")
        sayim2 = satir.split(": ", 1)[-1].split(" (")[0] if "yeni:" in satir else satir
        kontrol("2. toplama sayımı (A)", "yeni: 1 · değişmedi: 5 · damga değişti: 0" in r2.stdout
                and "yeni: 1 · değişmedi: 5 · damga değişti: 0" in ozet2, satir)
        k2 = kalemler(d) if r2.returncode == 0 else []
        sonra = {C.url_key(i["url"]): json.dumps(i, sort_keys=True) for i in k2}
        kontrol("2. toplama: var olan 5 kalem bayt bayt aynı (damga + çeviri)",
                all(sonra.get(k) == v for k, v in once.items()))
        kontrol("2. toplama: akıştan düşen kalem silinmedi",
                any("mk48-uuv" in i["url"] for i in k2))
        yeni = [i for i in k2 if "roketsan-155" in i["url"]]
        kontrol("2. toplama: yeni kalem kendi damgasıyla",
                len(yeni) == 1 and yeni[0].get("ilk_goruldu") == "2026-09-24T11:04:00+03:00")
        veri2 = json.loads(f.read_text(encoding="utf-8"))
        kontrol("2. toplama: toplamalar kaydı", [t["yeni"] for t in veri2.get("toplamalar", [])] == [5, 1])
        kontrol("2. toplama: uyarı yok", not u2, str(u2))

        # 3 · dünkü brifingden sonra gelenler: aday dosyasının ilk bölümü
        aday = (d / "out" / f"{GUN}-aday.md").read_text(encoding="utf-8")
        ilk = next((l for l in aday.splitlines() if l.startswith("## ")), "")
        kontrol("aday: ilk bölüm", ilk == "## Dünkü brifingden sonra gelenler (2)", ilk)
        urls = C.first_section_urls(aday)
        kontrol("aday: ilk bölümde AA ve 11:04 kalemi, 05:19 kalemleri yok",
                C.url_key(AA_URL) in urls and "https://ex.com/late-2" in urls
                and not any("early" in u for u in urls))
        kontrol("(A) jetonlu satır", "dünkü (2026-09-23) brifing: 06:16 · BRİFİNGDEN SONRA jetonlu satır: 2"
                " · aday dosyasının ilk bölümünde 2/2" in ozet2)

        # 260 sınırı ilk bölümü kesemez
        cok = {"MKE": [dict(DUN_DOSYASI["items"][0], url=f"https://ex.com/m{n}") for n in range(300)]}
        yuk = {"scanned_sources": 1, "failed_sources": 0, "window_hours": 48, "unique_items": 300}
        sinir = C.write_candidates(GUN, yuk, cok, DUN_DOSYASI["items"][2:],
                                   DUN, C.brief_time(DUN, d / "published.json"), d)
        metin = sinir.read_text(encoding="utf-8")
        kontrol("260 sınırı: ilk bölüm tam, MKE kesildi",
                len(C.first_section_urls(metin)) == 2 and "- … bu kategoride 42 kalem daha var" in metin)
        # ilk bölümde eksik kalem → GEÇ-GELEN (işlev düzeyi: sınır 1'e inerse)
        eski = C.CANDIDATE_LIMIT
        C.CANDIDATE_LIMIT = 1
        try:
            dar = C.write_candidates(GUN, yuk, {}, DUN_DOSYASI["items"][2:], DUN,
                                     C.brief_time(DUN, d / "published.json"), d)
            eksik = [i for i in DUN_DOSYASI["items"][2:]
                     if C.url_key(i["url"]) not in C.first_section_urls(dar.read_text(encoding="utf-8"))]
        finally:
            C.CANDIDATE_LIMIT = eski
        kontrol("ilk bölümden eksik kalem saptanır", len(eksik) == 1)

        # 4 · damga bilerek değiştirildi → GEÇ-GELEN
        r3, ozet3, u3 = toplama(d, "ogle.json", OGLE, "--sinama-damga-boz")
        gg = [u for u in u3 if u["kural"] == "GEÇ-GELEN"]
        kontrol("damga bozuk: (A) damga değişti: 1", "damga değişti: 1" in ozet3 and "🔴" in ozet3)
        kontrol("damga bozuk: GEÇ-GELEN uyarısı", len(gg) == 1 and "damgası değişti" in gg[0]["metin"]
                and gg[0]["metin"].startswith("SINAMA"), gg[0]["metin"][:120] if gg else "uyarı yok")

        # 5 · sınır: --fixture --out olmadan reddedilir; data/news'e dokunulmadı
        r4 = subprocess.run([sys.executable, str(COLLECT), "--fixture", str(d / "sabah.json")],
                            capture_output=True, text=True)
        kontrol("--fixture --out'suz reddedilir", r4.returncode != 0)
        r5 = subprocess.run([sys.executable, str(COLLECT), "--sinama-damga-boz"],
                            capture_output=True, text=True)
        kontrol("--sinama-damga-boz gerçek toplamada reddedilir", r5.returncode != 0)
    kontrol("data/news değişmedi", sorted(p.name for p in C.OUT_DIR.iterdir()) == data_news_once)

    ok = all(sonuc)
    son = (f"{'🟢' if ok else '🔴'} GEÇ-GELEN testi: {sum(sonuc)}/{len(sonuc)} kontrol · "
           f"ikinci toplama “{sayim2}” · ağ kütüphanesi 0")
    print(son)
    if os.environ.get("GITHUB_STEP_SUMMARY"):
        with open(os.environ["GITHUB_STEP_SUMMARY"], "a", encoding="utf-8") as fh:
            fh.write(son + "\n\n")
    return 0 if ok else 1


def yerel_aday(gun):
    """GÜN'ün kaydedilmiş verisinden, ağsız yolla GÜN+1'in aday dosyası → data/news/.

    Yalnız yerel kanıt içindir (commit edilmez): gerçek dosyayı sabah hattı üretir.
    GÜN+1'in .json dosyası data/news'e yazılmaz; yalnızca -aday.md kopyalanır.
    """
    import datetime as dt
    kaynak = json.loads((C.OUT_DIR / f"{gun}.json").read_text(encoding="utf-8"))
    ertesi = (dt.date.fromisoformat(gun) + dt.timedelta(days=1)).isoformat()
    kaynaklar, akis = {}, {}
    for i in kaynak["items"]:
        kaynaklar.setdefault(i["source"], {"ad": i["source"], "tur": "rss", "ulke": i.get("country", ""),
                                           "dil": i.get("lang", ""), "kademe": i.get("tier", "")})
        akis.setdefault(i["source"], {"items": []})["items"].append(
            {"title": i["title"], "url": i["url"], "published": i.get("published")})
    with tempfile.TemporaryDirectory() as tmp:
        fx = pathlib.Path(tmp) / "fixture.json"
        fx.write_text(json.dumps({"sources": list(kaynaklar.values()), "feeds": akis},
                                 ensure_ascii=False), encoding="utf-8")
        env = {k: v for k, v in os.environ.items() if k not in ("GITHUB_STEP_SUMMARY", "RUNNER_TEMP")}
        r = subprocess.run([sys.executable, str(COLLECT), "--fixture", str(fx), "--out", tmp,
                            "--date", ertesi, "--now", f"{ertesi}T05:19:00+03:00"],
                           capture_output=True, text=True, env=env)
        print(r.stdout[-1500:], r.stderr[-1500:])
        if r.returncode:
            return r.returncode
        hedef = C.OUT_DIR / f"{ertesi}-aday.md"
        shutil.copyfile(pathlib.Path(tmp) / f"{ertesi}-aday.md", hedef)
        print(f"yerel kanıt: {hedef.relative_to(ROOT)} (commit edilmez)")
    return 0


if __name__ == "__main__":
    if sys.argv[1:2] == ["hazirla"] and len(sys.argv) == 3:
        print(hazirla(sys.argv[2]))
        sys.exit(0)
    if sys.argv[1:2] == ["yerel-aday"] and len(sys.argv) == 3:
        sys.exit(yerel_aday(sys.argv[2]))
    sys.exit(main())
