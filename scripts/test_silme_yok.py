#!/usr/bin/env python3
"""SİLME-YOK ve İPUCU-YOK testi (Rev 25): collect_news.py ağsız, kayıtlı başlıklarla.

    python3 scripts/test_silme_yok.py               # tüm kontroller, çıkış 1 = kırmızı
    python3 scripts/test_silme_yok.py hazirla DIR   # iş akışı adımları için sınama dosyaları

Fixture, Drive'daki kaynaklar.json'un filtre notlu dokuz kaynağını (ad, dil, kademe, not
aynen) ve iki özel akışı temsil eder: Trend.az, Report.az, Dawn, AA güncel, AA analiz,
Al Jazeera, Al Arabiya English (boş döner, 23 Eylül'deki gibi), Arab News, Middle East
Monitor. Filtre notlu akışların çoğu başlığı savunma dışıdır. Kırmızı koşullar:

  1. eşit çalıştırmada bir kaynağın okunan ≠ yazılan, ya da (A) tablosunda dokuz filtre
     notlu kaynak eşit görünmüyor
  2. savunma dışı başlık düştü, `savunma_terimi: false` taşımıyor ya da Genel dışında
  3. bilerek bozulan çalıştırma (--sinama-silme-boz) çıkış 0 veriyor, (A)'da 🔴 satır yok ya
     da SİLME-YOK uyarısı çıkmıyor
  4. S2/S3/S4/S6 kuralları örnek başlıklarda tutmuyor; S8 ipucu sayacı ipucuyla gelen
     kalemi saymıyor
  5. sınama yolu ağ kütüphanesi yüklüyor ya da data/news'e yazıyor

Yalnızca stdlib. CI'da `$GITHUB_STEP_SUMMARY`'ye 🟢/🔴 satırı ekler.
"""
import json
import os
import pathlib
import subprocess
import sys
import tempfile

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import collect_news as C  # noqa: E402
import test_collect as T  # noqa: E402  (toplama(): ayrı süreç, ağ tuzağı, kendi RUNNER_TEMP'i)

GUN, SIMDI = T.GUN, T.SABAH   # 24 Eylül 05:19
NOT = "Genel haber akışı; filtre gerekir"


def _k(ad, ulke, dil, kademe):
    return {"ad": ad, "tur": "rss", "ulke": ulke, "dil": dil, "kademe": kademe, "not": NOT}


FILTRELI = [
    _k("Trend.az", "AZ", "en", "B"), _k("Report.az", "AZ", "en", "B"), _k("Dawn", "PK", "en", "B"),
    _k("Anadolu Ajansı — güncel", "TR", "tr", "C"), _k("Anadolu Ajansı — analiz", "TR", "tr", "C"),
    _k("Al Jazeera", "QA", "en", "C"), _k("Al Arabiya English", "SA", "en", "C"),
    _k("Arab News", "SA", "en", "C"), _k("Middle East Monitor", "GB", "en", "C"),
]
OZEL = [
    # Eski SOURCE_HINTS bu kapsamı C-UAS'a çekiyordu (S2): kaynak ipucu artık yok.
    {"ad": "DroneXL", "tur": "rss", "ulke": "US", "dil": "en", "kademe": "B",
     "kapsam": "İnsansız sistemler, dron savunma"},
    {"ad": "Defense Daily", "tur": "rss", "ulke": "US", "dil": "en", "kademe": "A"},
]
TREND_DISI = "Azerbaijan and Uzbekistan agree to expand cotton trade corridor"


def _i(title, slug, published="2026-09-23"):
    return {"title": title, "url": f"https://ex.test/{slug}", "published": published}


AKIS = {
    "Trend.az": {"items": [
        _i(TREND_DISI, "trend-cotton"),
        _i("Baku hosts regional energy ministers ahead of COP talks", "trend-energy"),
        _i("Azerbaijan's army holds joint drills with Turkish troops", "trend-drill"),
        _i("Old Trend story outside the 48 hour window", "trend-old", "2026-09-20")]},
    "Report.az": {"items": [
        _i("Central bank keeps refinancing rate unchanged", "report-rate"),
        _i("Azerbaijan Airlines opens new route to Milan", "report-route")]},
    "Dawn": {"items": [
        _i("Pakistan navy commissions new offshore patrol vessel", "dawn-navy"),
        _i("Karachi records heaviest September rainfall in decade", "dawn-rain")]},
    "Anadolu Ajansı — güncel": {"items": [
        _i("ASELSAN ile ROKETSAN arasında 1,2 milyar avroluk sözleşme imzalandı", "aa-aselsan"),
        _i("İstanbul'da toplu taşıma ücretlerine yeni düzenleme", "aa-ulasim")]},
    "Anadolu Ajansı — analiz": {"items": [
        _i("Küresel emtia fiyatlarında yeni dönem", "aa-emtia")]},
    "Al Jazeera": {"items": [
        _i("World Cup qualifiers: five things to watch", "aj-football"),
        _i("Israeli air defence intercepts rocket fired from Gaza", "aj-airdef")]},
    "Al Arabiya English": {"items": []},
    "Arab News": {"items": [
        _i("Saudi Arabia launches tourism visa for GCC residents", "an-visa")]},
    "Middle East Monitor": {"items": [
        _i("UN rapporteur calls for humanitarian corridor", "mem-un"),
        _i("Egypt signs deal to buy wheat from Russia", "mem-wheat")]},
    "DroneXL": {"items": [
        _i("DJI Neo 3 Leak Is Recycled Box Art, and the Vents Gave It Away", "dxl-dji"),
        _i("Dolomites Parks Ban Hobby Drones, DJI Mini 5 Pro Included", "dxl-dolomites"),
        _i("ABZ Opens Hungary Drone Plant, Its FCC Pass Hinges on a US Factory", "dxl-abz")]},
    "Defense Daily": {"items": [
        _i("Hanwha Ups Munitions Investment At Pine Bluff To $2.2 Billion", "dd-hanwha"),
        _i("Trump signs Greenland security agreement, defusing allied tensions", "dd-greenland"),
        _i("Army issues RFP for next counter-drone interceptor", "dd-rfp")]},
}


def hazirla(d):
    """Sınama dosyaları: silme.json ve published.json (dünün dosyası yok: günün ilk toplaması)."""
    d = pathlib.Path(d)
    (d / "out").mkdir(parents=True, exist_ok=True)
    (d / "silme.json").write_text(json.dumps({"sources": FILTRELI + OZEL, "feeds": AKIS},
                                             ensure_ascii=False, indent=1), encoding="utf-8")
    (d / "published.json").write_text(json.dumps(T.YAYIN), encoding="utf-8")
    return d


def main():
    sonuc = []

    def kontrol(ad, ok, ayrinti=""):
        sonuc.append(bool(ok))
        print(f"{'ok  ' if ok else 'FAIL'} {ad}" + (f" · {ayrinti}" if ayrinti else ""))

    # 4 · kurallar (işlev düzeyi)
    cat = C.categorise
    kontrol("S2: kaynak ipucu yok (Tournai → Genel)",
            cat("Belgium’s second rMCM ship ‘Tournai’ Arrives in Zeebrugge") == C.GENERAL
            and not hasattr(C, "SOURCE_HINTS"))
    kontrol("S3: çıplak dron → İnsansız, mücadele ifadesi → C-UAS",
            cat("ABZ Opens Hungary Drone Plant") == "Deniz ve İnsansız Sistemler"
            and cat("Poland buys new counter-drone jammers") == "C-UAS ve Hava Savunma"
            and cat("DJI Neo 3 Leak Is Recycled Box Art") == C.GENERAL)
    kontrol("S6: diplomatik 'signs … agreement' İhale değil, RFP İhale",
            cat("Trump signs Greenland security agreement") == C.GENERAL
            and cat("Army issues RFP for new trucks") == "İhale ve Sözleşmeler")
    kontrol("S4: oyuncu öznesi + eylem → Oyuncu Duyuruları; nesne olan oyuncu değil",
            cat("Hanwha Ups Munitions Investment At Pine Bluff To $2.2 Billion") == C.PLAYER_CATEGORY
            and cat("Pentagon taps Northrop Grumman for recon satellites") != C.PLAYER_CATEGORY
            and cat("Rheinmetall shares fall after results") != C.PLAYER_CATEGORY)
    s8 = C.s8_counts([
        {"title": "Belgium’s second rMCM ship ‘Tournai’ Arrives", "category": "C-UAS ve Hava Savunma"},
        {"title": "Poland buys counter-drone jammers", "category": "C-UAS ve Hava Savunma"},
        {"title": "Karachi rainfall", "category": C.GENERAL}])
    kontrol("S8: ipucuyla gelen ve kelimesiz sayılır",
            s8["C-UAS ve Hava Savunma"] == {"n": 2, "ipucu": 1, "kelimesiz": 1}
            and s8[C.GENERAL] == {"n": 1, "ipucu": None, "kelimesiz": 1}, str(s8))

    data_news_once = sorted(p.name for p in C.OUT_DIR.iterdir())
    okunan = {ad: [i for i in f["items"] if i["published"] >= "2026-09-22"] for ad, f in AKIS.items()}
    with tempfile.TemporaryDirectory() as tmp:
        d = hazirla(tmp)

        # 1–2 · eşit çalıştırma
        r1, ozet1, u1 = T.toplama(d, "silme.json", SIMDI)
        kontrol("eşit: çıkış 0", r1.returncode == 0, r1.stderr[-300:])
        kontrol("eşit: (A) 🟢 okunan == yazılan", "🟢 okunan == yazılan: 11/11 kaynak eşit" in ozet1,
                next((l for l in ozet1.splitlines() if "okunan == yazılan" in l), "satır yok")[:140])
        satirlar = [l for l in ozet1.splitlines() if l.startswith("| ") and "| filtre |" in l]
        kontrol("eşit: (A) tabloda 9 filtre notlu kaynak, hepsi eşit",
                len(satirlar) == 9 and all("🟢 eşit" in l for l in satirlar), f"{len(satirlar)} satır")
        items = T.kalemler(d) if r1.returncode == 0 else []
        by_url = {i["url"]: i for i in items}
        eksik = [i["title"] for f in okunan.values() for i in f if i["url"] not in by_url]
        kontrol("eşit: okunan her kalem günün dosyasında", not eksik, "; ".join(eksik)[:120])
        disi = by_url.get("https://ex.test/trend-cotton") or {}
        kontrol("eşit: Trend.az savunma dışı başlık yazıldı, işaretli, Genel'de",
                disi.get("title") == TREND_DISI and disi.get("savunma_terimi") is False
                and disi.get("category") == C.GENERAL, str({k: disi.get(k) for k in
                                                            ("savunma_terimi", "category")}))
        savunma = by_url.get("https://ex.test/aj-airdef") or {}
        kontrol("eşit: filtre notlu kaynağın savunma başlığı savunma_terimi: true, kategorili",
                savunma.get("savunma_terimi") is True and savunma.get("category") == "C-UAS ve Hava Savunma")
        kontrol("eşit: özel akış kalemi savunma_terimi taşımaz",
                all("savunma_terimi" not in i for i in items if i["source"] in ("DroneXL", "Defense Daily")))
        kontrol("eşit: 48 saat dışı kalem alınmadı", "https://ex.test/trend-old" not in by_url)
        kontrol("eşit: DroneXL C-UAS'ta değil (S2+S3)",
                not any(i["source"] == "DroneXL" and i["category"] == "C-UAS ve Hava Savunma" for i in items))
        kontrol("eşit: uyarı yok", not u1, str(u1)[:200])
        aday = (d / "out" / f"{GUN}-aday.md").read_text(encoding="utf-8")
        genel = aday.split(f"## {C.GENERAL}", 1)[-1]
        kontrol("aday: savunma dışı kalemler Genel'in sonunda",
                genel.find("heaviest September rainfall") > genel.find("Greenland security agreement") > 0)

        # 3 · bilerek bozulan çalıştırma
        (d / "out" / f"{GUN}.json").unlink()
        (d / "out" / f"{GUN}-aday.md").unlink()
        r2, ozet2, u2 = T.toplama(d, "silme.json", SIMDI, "--sinama-silme-boz")
        sy = [u for u in u2 if u["kural"] == "SİLME-YOK"]
        kontrol("bozuk: çıkış ≠ 0 (iş kırmızı)", r2.returncode != 0, f"çıkış {r2.returncode}")
        kontrol("bozuk: (A) 🔴 ve EŞİT DEĞİL satırı", "🔴 okunan == yazılan: 10/11" in ozet2
                and "🔴 EŞİT DEĞİL" in ozet2)
        kontrol("bozuk: SİLME-YOK uyarısı (SINAMA önekli)",
                len(sy) == 1 and sy[0]["metin"].startswith("SINAMA") and "Trend.az" in sy[0]["metin"],
                sy[0]["metin"][:140] if sy else "uyarı yok")
        kontrol("bozuk: SİLME-YOK bloklayıcı", "SİLME-YOK" in __import__("uyari").BLOKLAYICI)

        # 5 · sınırlar
        r3 = subprocess.run([sys.executable, str(T.COLLECT), "--sinama-silme-boz"],
                            capture_output=True, text=True)
        kontrol("--sinama-silme-boz gerçek toplamada reddedilir", r3.returncode != 0)
    kontrol("data/news değişmedi", sorted(p.name for p in C.OUT_DIR.iterdir()) == data_news_once)

    ok = all(sonuc)
    son = (f"{'🟢' if ok else '🔴'} SİLME-YOK / İPUCU-YOK testi: {sum(sonuc)}/{len(sonuc)} kontrol · "
           f"9 filtre notlu kaynak · ağ kütüphanesi 0")
    print(son)
    if os.environ.get("GITHUB_STEP_SUMMARY"):
        with open(os.environ["GITHUB_STEP_SUMMARY"], "a", encoding="utf-8") as fh:
            fh.write(son + "\n\n")
    return 0 if ok else 1


if __name__ == "__main__":
    if sys.argv[1:2] == ["hazirla"] and len(sys.argv) == 3:
        print(hazirla(sys.argv[2]))
        sys.exit(0)
    sys.exit(main())
