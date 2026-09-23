#!/usr/bin/env python3
"""K6 tanı: Elbit ve Northrop akışları CI'ın (GitHub runner) IP'sinden ne döndürüyor?

    python3 scripts/k6_tani.py          # ağa çıkar; yalnız k6-kaynak-test.yml'in "tani" işi

Her yoklama tek bir düz HTTP GET'tir, `collect_news.py`'nin istek biçimiyle
(`request_headers()`: aynı User-Agent, `Accept: */*`, kaynağın `istek_basligi`'ı; aynı zaman aşımı;
yönlendirmeler `requests` varsayılanı gibi izlenir). Yalnız Elbit Systems ve Northrop Grumman'ın
kendi herkese açık adresleri. Sır yok, yazma yok (data/news, Drive, repo), Claude/çeviri yok.

Her yoklama için (A) özetine: HTTP durumu, Content-Type, Server, gövde boyu, yönlendirme zinciri,
ayrıştırılan kayıt sayısı, gövdenin ilk 500 baytı (kaçışlı) ve tek satır yorum. Gövdenin tamamı
(en çok 300 KB) iş günlüğüne basılır — HTML ayrıştırıcı gerekirse oradan alınır.
Çıkış her zaman 0: tanı, sonuç ne olursa olsun kırmızı olmaz (yorum satırı konuşur).
"""
import datetime as dt
import html
import os
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import collect_news as C  # noqa: E402

AL = {"Accept-Language": "en-US,en;q=0.9"}
ELBIT_FEED = "https://elbitsystems.com/feed/"            # Drive kaynaklar.json'daki girdi (24 Eyl)
ELBIT_NEWS = "https://www.elbitsystems.com/news"          # /feed/ → 301 → 301 → burası (CI tanısı, 23 Eyl 22:31Z)
NG_FEED = "https://investor.northropgrumman.com/rss/news-releases.xml"

# (etiket, kaynak girdisi — request_headers()/parse_body()'ye aynen verilir)
YOKLAMALAR = [
    ("Elbit Systems · /feed/ · bugünkü girdi (CI'daki 'feed parsed but empty' isteğinin aynısı)",
     {"ad": "Elbit Systems", "tur": "rss", "url": ELBIT_FEED}),
    ("Elbit Systems · /news · html `elbitsystems-news` (K6 onarımı: /feed/ buraya yönleniyor)",
     {"ad": "Elbit Systems", "tur": "html", "ayristirici": "elbitsystems-news", "url": ELBIT_NEWS}),
    ("Elbit Systems · /feed/ · + Accept-Language",
     {"ad": "Elbit Systems", "tur": "rss", "url": ELBIT_FEED, "istek_basligi": AL}),
    ("Northrop Grumman · RSS · bugünkü girdi (başlıksız; 17–23 Eyl'de 403)",
     {"ad": "Northrop Grumman", "tur": "rss", "url": NG_FEED}),
    ("Northrop Grumman · RSS · + istek_basligi Accept-Language (K6 onarımı)",
     {"ad": "Northrop Grumman", "tur": "rss", "url": NG_FEED, "istek_basligi": AL}),
    ("Elbit aday · IR RSS · + Accept-Language",
     {"ad": "Elbit IR", "tur": "rss", "url": "https://ir.elbitsystems.com/rss/news-releases.xml",
      "istek_basligi": AL}),
    ("Elbit Systems UK · HTML (K6 ek kaynağı)",
     {"ad": "Elbit Systems UK", "tur": "html", "ayristirici": "elbitsystems-uk",
      "url": "https://www.elbitsystems-uk.com/media-events/recent-news"}),
]

# Gövdede görülürse 2xx'in akış değil bir doğrulama/engel sayfası olduğunu söyleyen izler.
ENGEL_IZLERI = [
    ("Just a moment", "Cloudflare bot doğrulaması"), ("challenge-platform", "Cloudflare bot doğrulaması"),
    ("cf-chl", "Cloudflare bot doğrulaması"), ("_Incapsula_Resource", "Imperva/Incapsula doğrulaması"),
    ("awswaf", "AWS WAF doğrulaması"), ("aws-waf-token", "AWS WAF doğrulaması"),
    ("sgcaptcha", "SiteGround CAPTCHA"), ("captcha", "CAPTCHA sayfası"),
    ("Access Denied", "Akamai 'Access Denied'"), ("Request unsuccessful", "Imperva engeli"),
]


def kayit_sayisi(kaynak, govde):
    """(ayrıştırılan kalemler | None, ham <item>/<entry> sayısı, ayrıştırma hatası)."""
    ham = len(re.findall(rb"<(?:item|entry)[\s>]", govde or b""))
    if kaynak["tur"] not in ("rss", "html"):
        return None, ham, None
    try:
        return C.parse_body(kaynak, govde or b""), ham, None
    except Exception as exc:  # noqa: BLE001
        return [], ham, f"{type(exc).__name__}: {exc}"[:120]


def yorumla(s):
    """Bir yoklamanın sonucu (dict) → tek satır Türkçe yorum. Saf fonksiyon (ağsız test edilir)."""
    if s.get("istisna"):
        return f"İstek yanıt almadı ({s['istisna']}): sunucu bağlantıyı kesti ya da zaman aşımı — engel ya da ağ sorunu."
    kod, tip = s["durum"], (s.get("tip") or "").lower()
    govde = s.get("govde") or b""
    metin = govde[:20000].decode("utf-8", "replace")
    iz = next((ad for anahtar, ad in ENGEL_IZLERI if anahtar.lower() in metin.lower()), None)
    sunucu = (s.get("sunucu") or "").lower()
    kalem, ham = s.get("kalem"), s.get("ham", 0)
    yon = f" ({len(s['zincir'])} yönlendirme sonrası {s['son_url']})" if s.get("zincir") else ""
    if kod in (401, 403, 429) or kod >= 500:
        kim = iz or ("AWS yük dengeleyici/WAF (awselb)" if "awselb" in sunucu else
                     "Akamai" if "akamai" in sunucu or "Reference #" in metin else s.get("sunucu") or "sunucu")
        return f"HTTP {kod}{yon}: {kim} isteği reddediyor — bu IP'den/bu istek biçimiyle erişim engelli, akış okunamaz."
    if not 200 <= kod < 300:
        return f"HTTP {kod}{yon}: beklenmeyen durum; raise_for_status() bunu hata sayar."
    if kalem:
        en_yeni = max(kalem, key=lambda i: i["published"] or dt.datetime.min.replace(tzinfo=dt.timezone.utc))
        tarih = en_yeni["published"].date().isoformat() if en_yeni["published"] else "tarihsiz"
        return (f"ÇALIŞIYOR{yon}: {len(kalem)} kayıt ayrıştırıldı, en yenisi {tarih} "
                f"“{en_yeni['title'][:80]}”.")
    if kalem is None:  # ayrıştırıcısı olmayan aday sayfa
        return (f"HTTP {kod}{yon}, {tip or 'tip yok'}, {len(govde)} B: sayfa açılıyor"
                + (f" ama {iz}" if iz else "; tam gövde iş günlüğünde — HTML ayrıştırıcı (yol c) buradan yazılabilir") + ".")
    if not govde.strip():
        return f"HTTP {kod}{yon} ama gövde BOŞ: 'feed parsed but empty'nin nedeni boş yanıt."
    if iz:
        return f"HTTP {kod}{yon} ama gövde akış değil, {iz}: tarayıcısız istek geçemiyor — 'feed parsed but empty'nin nedeni bu."
    xml = "xml" in tip or metin.lstrip().startswith("<?xml") or "<rss" in metin[:2000] or "<feed" in metin[:2000]
    if xml and ham == 0:
        return f"HTTP {kod}{yon}, geçerli akış kabuğu ama içinde HİÇ kayıt yok: akış yayıncı tarafından boşaltılmış/terk edilmiş."
    if xml and ham:
        return f"HTTP {kod}{yon}, {ham} <item>/<entry> var ama ayrıştırılamadı ({s.get('hata') or 'başlık/bağlantı eksik'}): akış bozuk."
    yonlendirme = re.search(r'http-equiv=["\']?refresh|window\.location|location\.href', metin, re.I)
    if yonlendirme:
        return f"HTTP {kod}{yon} ama gövde HTML ve sayfa içi (meta/JS) yönlendirme içeriyor: akış adresi başka yere taşınmış."
    return (f"HTTP {kod}{yon} ama gövde akış değil, {tip or 'tip yok'} HTML sayfa ({len(govde)} B): "
            "akış adresi artık sıradan bir sayfa döndürüyor (URL taşınmış/kaldırılmış) — 'feed parsed but empty'nin nedeni bu.")


def yokla(kaynak, get):
    basliklar = C.request_headers(kaynak)
    s = {"url": kaynak["url"], "basliklar": basliklar}
    try:
        r = get(kaynak["url"], headers=basliklar, timeout=C.TIMEOUT)
    except Exception as exc:  # noqa: BLE001
        s["istisna"] = f"{type(exc).__name__}: {exc}"[:200]
        return s
    s.update(durum=r.status_code, tip=r.headers.get("Content-Type", ""), sunucu=r.headers.get("Server", ""),
             govde=r.content or b"", son_url=r.url,
             zincir=[(h.status_code, h.url, h.headers.get("Location", "")) for h in r.history])
    s["kalem"], s["ham"], s["hata"] = kayit_sayisi(kaynak, s["govde"]) if 200 <= r.status_code < 300 else (None, 0, None)
    return s


def kacisli(b, n=500):
    """İlk n bayt → okunur, kaçışlı metin (kontrol karakterleri \\xNN, HTML kaçışlı)."""
    t = b[:n].decode("utf-8", "backslashreplace")
    t = "".join(c if c in "\n\t" or c.isprintable() else f"\\x{ord(c):02x}" for c in t)
    return html.escape(t)


def ozet(sonuclar, saat):
    nereden = "GitHub Actions runner IP'si" if os.environ.get("GITHUB_ACTIONS") else "yerel makine (CI değil)"
    def bul(parca):
        return next(((n, s) for n, (e, s) in enumerate(sonuclar, 1) if parca in e), (0, {}))

    def son3(s):
        k = sorted(s.get("kalem") or [], key=lambda i: i["published"] or dt.datetime.min.replace(
            tzinfo=dt.timezone.utc), reverse=True)[:3]
        return "; ".join(f"{i['published'].date() if i['published'] else 'tarihsiz'} “{i['title']}”" for i in k) or "—"

    (n1, s1), (n2, s2), (n3, s3) = bul("bugünkü girdi (CI"), bul("/news"), bul("istek_basligi")
    satir = [f"### K6 · tanı — Elbit ve Northrop, canlı GET · {nereden}", "",
             f"**Elbit — CI'daki arızanın nedeni ({n1}):** {yorumla(s1) if s1 else '—'}", "",
             f"**Elbit — K6 onarımı /news ({n2}):** {yorumla(s2) if s2 else '—'} Son 3: {son3(s2)}", "",
             f"**Northrop — K6 onarımı bu IP'den ({n3}):** {yorumla(s3) if s3 else '—'} Son 3: {son3(s3)}", "",
             f"{saat} · istek biçimi `collect_news.request_headers()` (User-Agent `{C.UA}`, `Accept: */*`, "
             f"+ kaynağın `istek_basligi`), zaman aşımı {C.TIMEOUT} sn, yönlendirmeler izlenir. "
             "Sır yok, yazma yok. Tam gövdeler iş günlüğünde.", "",
             "| # | Yoklama | Durum | Content-Type | Kayıt | Yorum |", "|--:|---|--:|---|--:|---|"]
    for n, (etiket, s) in enumerate(sonuclar, 1):
        kayit = "—" if s.get("kalem") is None else len(s["kalem"])
        satir.append(f"| {n} | {etiket} | {s.get('durum', 'yok')} | {s.get('tip') or '—'} | {kayit} | "
                     f"{yorumla(s).replace('|', '/')} |")
    satir.append("")
    for n, (etiket, s) in enumerate(sonuclar, 1):
        satir += [f"#### {n} · {html.escape(etiket)} — {s.get('durum', 'yanıt yok')}", "", "<pre>" + html.escape(
                      f"GET {s['url']}\n"
                      + "".join(f"{k}: {v}\n" for k, v in s["basliklar"].items())
                      + (f"\nistisna: {s['istisna']}\n" if s.get("istisna") else
                         f"\nHTTP {s['durum']} · Content-Type: {s['tip'] or '—'} · Server: {s['sunucu'] or '—'}"
                         f" · {len(s['govde'])} B · son URL: {s['son_url']}\n"
                         + "yönlendirme zinciri: " + (" → ".join(f"{k} {u} (Location: {l})" for k, u, l in s['zincir'])
                                                      or "yok") + "\n"
                         + f"ham <item>/<entry>: {s['ham']}" + (f" · ayrıştırma hatası: {s['hata']}" if s.get('hata') else "")
                         + "\n\nilk 500 bayt:\n"))
                  + ("" if s.get("istisna") else kacisli(s["govde"])) + "</pre>", "",
                  f"**Yorum:** {html.escape(yorumla(s))}"
                  + (f" · son 3: {html.escape(son3(s))}" if s.get("kalem") else ""), ""]
    return satir


def main():
    import requests
    sonuclar = []
    for etiket, kaynak in YOKLAMALAR:
        s = yokla(kaynak, requests.get)
        sonuclar.append((etiket, s))
        print(f"\n===== {etiket} — {kaynak['url']}")
        print(yorumla(s))
        if not s.get("istisna"):
            print(f"HTTP {s['durum']} {s['tip']} Server={s['sunucu']} {len(s['govde'])} B zincir={s['zincir']}")
            print(s["govde"][:300_000].decode("utf-8", "backslashreplace"))
    saat = dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    metin = "\n".join(ozet(sonuclar, saat)) + "\n\n"
    if os.environ.get("GITHUB_STEP_SUMMARY"):
        with open(os.environ["GITHUB_STEP_SUMMARY"], "a", encoding="utf-8") as fh:
            fh.write(metin)
    else:
        print(metin)
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as exc:  # noqa: BLE001 — tanı işi kırmızı olmaz; hata özete yazılır
        msg = f"### K6 · tanı\n\n🔴 tanı betiği çöktü: `{type(exc).__name__}: {exc}`\n"
        print(msg)
        if os.environ.get("GITHUB_STEP_SUMMARY"):
            with open(os.environ["GITHUB_STEP_SUMMARY"], "a", encoding="utf-8") as fh:
                fh.write(msg)
        sys.exit(0)
