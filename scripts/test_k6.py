#!/usr/bin/env python3
"""K6 testi: Elbit ve Northrop kaynaklarının onarımı, ağsız, kayıtlı yanıtlarla.

    python3 scripts/test_k6.py        # tüm kontroller, çıkış 1 = kırmızı

Fixture'lar 24 Eylül 2026'da canlı alınmış ham yanıtlardır (scripts/fixtures/):
  k6-northrop-news-releases.xml       investor.northropgrumman.com/rss/news-releases.xml
                                      (Accept-Language ile 200; onsuz 403)
  k6-elbitsystems-uk-recent-news.html.txt  www.elbitsystems-uk.com/media-events/recent-news
                                      (tur: "html", ayristirici: "elbitsystems-uk")

Kırmızı koşullar:
  1. Northrop: kaynak girdisinin `istek_basligi` alanı isteğe Accept-Language koymuyor; Akamai
     taklidi (Accept-Language yoksa 403) eski girdiyle 403, yeni girdiyle 200 vermiyor; alanı
     olmayan kaynakların başlıkları değişti (User-Agent + Accept */*, başka hiçbir şey)
  2. Northrop RSS fixture'ı 10 kalem ve beklenen son 3 başlık/tarih/URL vermiyor (feedparser
     yüklüyse gerçek ayrıştırıcıyla; yoksa bu kontrol yerelde "atlandı" yazılır, CI'da kurulu)
  3. Elbit UK HTML ayrıştırıcısı fixture'dan 20 kalem ve beklenen son 3 başlık/tarih/URL
     vermiyor; boş/yabancı sayfa kalem uyduruyor; bilinmeyen ayristirici hata vermiyor
  4. ağsız toplama (collect_news.py --fixture, ağ kütüphanesi tuzağıyla) iki kaynağı okumuyor,
     arıza yazıyor, SİLME-YOK eşit değil ya da data/news'e dokunuyor
  5. tanı betiği (scripts/k6_tani.py, CI'da ağa çıkan "tani" işi) sahte yanıtlarla: yorum satırı
     2xx-HTML-sayfa / boş akış / bot doğrulaması / WAF 403 / yönlendirmeyi doğru adlandırmıyor;
     özet durum, Content-Type, zinciri ve ilk 500 baytı kaçışlı göstermiyor

Yalnızca stdlib (+ varsa feedparser). CI'da `$GITHUB_STEP_SUMMARY`'ye (A) tablosu ve 🟢/🔴 satırı.
"""
import json
import os
import pathlib
import sys
import tempfile
import types
import xml.etree.ElementTree as ET

ROOT = pathlib.Path(__file__).resolve().parents[1]
FX = ROOT / "scripts" / "fixtures"
sys.path.insert(0, str(ROOT / "scripts"))
import collect_news as C  # noqa: E402
import test_collect as T  # noqa: E402  (toplama(): ayrı süreç, ağ tuzağı)

NG_URL = "https://investor.northropgrumman.com/rss/news-releases.xml"
EUK_URL = "https://www.elbitsystems-uk.com/media-events/recent-news"
AL = {"Accept-Language": "en-US,en;q=0.9"}
# Drive'daki girdinin değişmeyen alanları repoda yok; testin ilgilendiği alanlar bunlar.
NORTHROP_ESKI = {"ad": "Northrop Grumman", "tur": "rss", "url": NG_URL, "ulke": "US", "dil": "en"}
NORTHROP = {**NORTHROP_ESKI, "istek_basligi": AL}
ELBIT_UK = {"ad": "Elbit Systems UK", "tur": "html", "ayristirici": "elbitsystems-uk",
            "url": EUK_URL, "ulke": "GB", "dil": "en"}

NG_BEKLENEN = [
    ("Northrop Grumman Announces Date for Third Quarter 2026 Financial Results and Webcast",
     "2026-09-17", "https://investor.northropgrumman.com/news-releases/news-release-details/"
     "northrop-grumman-announces-date-third-quarter-2026-financial"),
    ("U.S. Air Force and Northrop Grumman Assemble Inert Missile, Progress Toward Sentinel "
     "Flight Testing", "2026-09-14", "https://investor.northropgrumman.com/news-releases/"
     "news-release-details/us-air-force-and-northrop-grumman-assemble-inert-missile"),
    ("Northrop Grumman to Participate in the 14th Annual Morgan Stanley Laguna Conference",
     "2026-09-10", "https://investor.northropgrumman.com/news-releases/news-release-details/"
     "northrop-grumman-participate-14th-annual-morgan-stanley-laguna"),
]
EUK_BEKLENEN = [
    ("Elbit Systems UK Showcases Latest Land and Autonomous Capabilities at DVD 2026", "2026-09-16",
     "https://www.elbitsystems-uk.com/media-events/recent-news/"
     "elbit-systems-uk-showcases-latest-land-and-autonomous-capabilities-at-dvd-2026"),
    ("Elbit Systems UK Plays Key Role in Landmark Live Virtual Constructive Training Exercise",
     "2026-09-07", "https://www.elbitsystems-uk.com/media-events/recent-news/"
     "elbit-systems-uk-plays-key-role-in-landmark-live-virtual-constructive-training-exercise"),
    ("Elbit Systems UK Achieves Gold Defence Employer Recognition Scheme Award", "2026-08-05",
     "https://www.elbitsystems-uk.com/media-events/recent-news/"
     "elbit-systems-uk-achieves-gold-defence-employer-recognition-scheme-award"),
]


def ilk3(items):
    s = sorted(items, key=lambda i: i["published"], reverse=True)[:3]
    return [(i["title"], i["published"].date().isoformat(), i["url"]) for i in s]


def ng_stdlib():
    """Northrop fixture'ı stdlib ile (feedparser'sız): ağsız toplamaya kalem olarak verilir."""
    root = ET.parse(FX / "k6-northrop-news-releases.xml").getroot()
    return [{"title": " ".join((i.findtext("title") or "").split()), "url": i.findtext("link"),
             "published": C.parse_date(i.findtext("pubDate")).isoformat()} for i in root.iter("item")]


class _Yanit:
    def __init__(self, url, status, content):
        self.url, self.status_code, self.content = url, status, content

    def raise_for_status(self):
        if self.status_code >= 400:
            raise _HTTPError(f"{self.status_code} Client Error: Forbidden for url: {self.url}")


class _HTTPError(Exception):
    pass


_HTTPError.__name__ = "HTTPError"


def sahte_requests(gonderilen):
    """Akamai taklidi: Chrome User-Agent + Accept-Language yok → 403 (canlıda ölçülen)."""
    govde = {NG_URL: (FX / "k6-northrop-news-releases.xml").read_bytes(),
             EUK_URL: (FX / "k6-elbitsystems-uk-recent-news.html.txt").read_bytes()}

    def get(url, headers=None, timeout=None):
        gonderilen.append(dict(headers or {}))
        if url == NG_URL and "Chrome/" in (headers or {}).get("User-Agent", "") \
                and "Accept-Language" not in (headers or {}):
            return _Yanit(url, 403, b"<HTML><HEAD><TITLE>Access Denied</TITLE></HEAD></HTML>")
        return _Yanit(url, 200, govde[url])
    return types.SimpleNamespace(get=get)


def main():
    sonuc, satirlar = [], []

    def kontrol(ad, ok, ayrinti=""):
        sonuc.append(bool(ok))
        print(f"  {'🟢' if ok else '🔴'} {ad}" + (f" — {ayrinti}" if ayrinti and not ok else ""))

    data_news_once = sorted(p.name for p in C.OUT_DIR.iterdir())
    try:
        import feedparser  # noqa: F401
        fp = True
    except ImportError:
        fp = False

    # 1 · Northrop: istek başlığı ve Akamai taklidi
    kontrol("alanı olmayan kaynak: başlıklar değişmedi",
            C.request_headers({"ad": "X", "tur": "rss"}) == {"User-Agent": C.UA, "Accept": "*/*"})
    kontrol("Northrop girdisi: Accept-Language isteğe eklenir",
            C.request_headers(NORTHROP) == {"User-Agent": C.UA, "Accept": "*/*", **AL})
    gonderilen = []
    gercek = sys.modules.get("requests")
    sys.modules["requests"] = sahte_requests(gonderilen)
    try:
        _, eski_kalem, eski_hata = C.read_feed(NORTHROP_ESKI)
        _, ng_kalem, ng_hata = C.read_feed(NORTHROP)
        _, euk_kalem, euk_hata = C.read_feed(ELBIT_UK)
    finally:
        if gercek is None:
            sys.modules.pop("requests", None)
        else:
            sys.modules["requests"] = gercek
    kontrol("eski Northrop girdisi: 403 (17–23 Eylül'deki hata aynen)",
            eski_hata == f"HTTPError: 403 Client Error: Forbidden for url: {NG_URL}"[:110], eski_hata)
    kontrol("yeni Northrop girdisi: istekte Accept-Language, HTTP hatası yok",
            gonderilen[-2].get("Accept-Language") == AL["Accept-Language"]
            and not (ng_hata or "").startswith("HTTPError"), ng_hata)

    # 2 · Northrop RSS ayrıştırma
    ng_std = ng_stdlib()
    kontrol("Northrop fixture: 10 kalem (stdlib)", len(ng_std) == 10, str(len(ng_std)))
    if fp:
        kontrol("Northrop: read_feed 10 kalem, son 3 başlık/tarih/URL (feedparser)",
                ng_hata is None and len(ng_kalem) == 10 and ilk3(ng_kalem) == NG_BEKLENEN, str(ng_hata or ilk3(ng_kalem)))
        ng_uc = ilk3(ng_kalem)
    else:
        print("  ⚪ Northrop feedparser ayrıştırması atlandı (feedparser yüklü değil; CI'da kurulu)")
        ng_uc = ilk3([{**i, "published": C.parse_date(i["published"])} for i in ng_std])
        kontrol("Northrop: son 3 başlık/tarih/URL (stdlib)", ng_uc == NG_BEKLENEN, str(ng_uc))

    # 3 · Elbit UK HTML ayrıştırıcısı
    sayfa = (FX / "k6-elbitsystems-uk-recent-news.html.txt").read_text(encoding="utf-8")
    euk = C.parse_body(ELBIT_UK, sayfa)
    kontrol("Elbit UK: 20 kalem, hepsi tarihli ve mutlak URL'li",
            len(euk) == 20 and all(i["published"] and i["url"].startswith("https://www.elbitsystems-uk.com/")
                                   for i in euk), str(len(euk)))
    kontrol("Elbit UK: son 3 başlık/tarih/URL", ilk3(euk) == EUK_BEKLENEN, str(ilk3(euk)))
    kontrol("Elbit UK: read_feed aynı sonucu verir (sahte ağ)",
            euk_hata is None and ilk3(euk_kalem) == EUK_BEKLENEN, str(euk_hata))
    kontrol("başka sayfa / boş gövde → 0 kalem (uydurma yok)",
            C.parse_body(ELBIT_UK, "<html><body><h1>403 Forbidden</h1></body></html>") == []
            and C.parse_body(ELBIT_UK, b"") == [])
    try:
        C.parse_body({**ELBIT_UK, "ayristirici": "yok"}, sayfa)
        bilinmeyen = False
    except ValueError:
        bilinmeyen = True
    kontrol("bilinmeyen ayristirici → hata", bilinmeyen)

    # 4 · ağsız toplama: tuzakla (requests/feedparser/google yüklenemez), 24 Eylül 05:19, 480 saat (4 Eylül sonrası)
    with tempfile.TemporaryDirectory() as tmp:
        d = pathlib.Path(tmp)
        (d / "out").mkdir()
        (d / "published.json").write_text("{}", encoding="utf-8")
        (d / "k6.json").write_text(json.dumps({
            "sources": [ELBIT_UK, NORTHROP],
            "feeds": {"Elbit Systems UK": {"body": sayfa}, "Northrop Grumman": {"items": ng_std}},
        }, ensure_ascii=False), encoding="utf-8")
        r, ozet, uyari = T.toplama(d, "k6.json", T.SABAH, "--hours", "480")
        gun = json.loads((d / "out" / f"{T.GUN}.json").read_text(encoding="utf-8")) if not r.returncode else {}
        kaynak = {}
        for i in gun.get("items") or []:
            kaynak.setdefault(i["source"], []).append(i)
        kontrol("ağsız toplama: çıkış 0, ağ kütüphanesi yüklenmedi", r.returncode == 0,
                (r.stderr or r.stdout)[-300:])
        kontrol("ağsız toplama: iki kaynak okundu, arıza 0",
                gun.get("sources") == ["Elbit Systems UK", "Northrop Grumman"]
                and gun.get("failures") == [], str(gun.get("failures")))
        kontrol("ağsız toplama: pencere içi kalemler yazıldı (Elbit UK 2, Northrop 3)",
                len(kaynak.get("Elbit Systems UK", [])) == 2 and len(kaynak.get("Northrop Grumman", [])) == 3,
                str({k: len(v) for k, v in kaynak.items()}))
        kontrol("ağsız toplama: SİLME-YOK 2/2 eşit, uyarı yok",
                "2/2 kaynak eşit" in ozet and not uyari, str(uyari)[:200])
    kontrol("data/news değişmedi", sorted(p.name for p in C.OUT_DIR.iterdir()) == data_news_once)

    # 5 · tanı betiği, ağsız (sahte get)
    import k6_tani as K

    def yanit(url, durum, govde, tip="text/html", sunucu="", gecmis=()):
        return types.SimpleNamespace(url=url, status_code=durum, content=govde, history=list(gecmis),
                                     headers={"Content-Type": tip, "Server": sunucu})

    def tani(kaynak, r):
        return K.yokla(kaynak, lambda url, headers=None, timeout=None: r)

    rss = {"ad": "Elbit Systems", "tur": "rss", "url": K.ELBIT_FEED}
    kabuk = b'<?xml version="1.0"?><rss version="2.0"><channel><title>Elbit</title></channel></rss>'
    durumlar = {
        "ana sayfa": (tani(rss, yanit("https://elbitsystems.com/", 200, b"<!doctype html><html><body>Home</body></html>",
                                      gecmis=[yanit(K.ELBIT_FEED, 301, b"")])), "HTML sayfa"),
        "boş kabuk": (tani(rss, yanit(K.ELBIT_FEED, 200, kabuk, "application/rss+xml")), "HİÇ kayıt yok"),
        "cloudflare": (tani(rss, yanit(K.ELBIT_FEED, 200, b"<html><title>Just a moment...</title></html>")), "Cloudflare"),
        "awselb 403": (tani(rss, yanit(K.ELBIT_FEED, 403, b"<h1>403 Forbidden</h1>", sunucu="awselb/2.0")), "awselb"),
        "boş gövde": (tani(rss, yanit(K.ELBIT_FEED, 200, b"")), "gövde BOŞ"),
    }
    if not fp:  # feedparser'sız parse_body(rss) ImportError verir; yorum yolları kalem=[] ile aynı
        for s_, _ in durumlar.values():
            s_["kalem"], s_["hata"] = [], None
    yanlis = {ad: K.yorumla(s_) for ad, (s_, beklenen) in durumlar.items() if beklenen not in K.yorumla(s_)}
    kontrol("tanı yorumu: HTML sayfa / boş akış / Cloudflare / awselb 403 / boş gövde doğru adlandırılır",
            not yanlis, str(yanlis)[:300])
    kontrol("tanı yorumu: yönlendirme zinciri yoruma girer",
            "1 yönlendirme sonrası https://elbitsystems.com/" in K.yorumla(durumlar["ana sayfa"][0]))
    euk_t = tani(ELBIT_UK, yanit(EUK_URL, 200, (FX / "k6-elbitsystems-uk-recent-news.html.txt").read_bytes()))
    kontrol("tanı: Elbit UK fixture'ı → ÇALIŞIYOR, 20 kayıt", K.yorumla(euk_t).startswith("ÇALIŞIYOR: 20 kayıt"),
            K.yorumla(euk_t))
    ozet_md = "\n".join(K.ozet([(e, durumlar["ana sayfa"][0]) for e, _ in K.YOKLAMALAR], "sınama"))
    kontrol("tanı özeti: durum, Content-Type, zincir, ilk 500 bayt kaçışlı, yorum",
            "| 200 | text/html |" in ozet_md and "301 https://elbitsystems.com/feed/" in ozet_md
            and "&lt;!doctype html&gt;" in ozet_md and "<!doctype" not in ozet_md
            and ozet_md.count("**Yorum:**") == len(K.YOKLAMALAR))
    kontrol("tanı: yalnız Elbit ve Northrop'un kendi adresleri",
            all(k["url"].split("/")[2].endswith(("elbitsystems.com", "elbitsystems-uk.com", "northropgrumman.com"))
                for _, k in K.YOKLAMALAR))

    ok = all(sonuc)
    satirlar = [f"### K6 · Elbit ve Northrop akışları — ayrıştırıcı testi (ağsız, fixture)", "",
                f"**{'🟢' if ok else '🔴'} {sum(sonuc)}/{len(sonuc)} kontrol** · "
                f"Northrop RSS ayrıştırması: {'feedparser' if fp else 'stdlib (feedparser yok)'} · "
                "ağ kütüphanesi 0 · fixture'lar 24 Eylül 2026'da canlı alındı", "",
                "| Kaynak | Tür | İstek düzeltmesi | Ayrıştırılan | Son 3 başlık (tarih) |",
                "|---|---|---|--:|---|"]
    for ad, tur, duz, n, uc in [
            ("Northrop Grumman", "rss", "`Accept-Language: en-US,en;q=0.9` (onsuz 403)", len(ng_std), ng_uc),
            ("Elbit Systems UK", "html · `elbitsystems-uk`", "—", len(euk), ilk3(euk))]:
        satirlar.append(f"| {ad} | {tur} | {duz} | {n} | "
                        + "<br>".join(f"{t} ({g})" for t, g, _ in uc) + " |")
    son = satirlar[2]
    print(son)
    if os.environ.get("GITHUB_STEP_SUMMARY"):
        with open(os.environ["GITHUB_STEP_SUMMARY"], "a", encoding="utf-8") as fh:
            fh.write("\n".join(satirlar) + "\n\n")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
