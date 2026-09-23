#!/usr/bin/env python3
"""ÇEVİRİ-DEDEKTÖRÜ testi (Rev 26): model çağırmadan, ağsız.

    python3 scripts/test_ceviri_dedektoru.py            # sabit test + akış, çıkış 1 = kırmızı
    python3 scripts/test_ceviri_dedektoru.py sabit      # yalnız sabit test (collect-news (A) satırı)
    python3 scripts/test_ceviri_dedektoru.py hazirla DIR  # iş akışı için sahte gün + sahte çevirmen

**Sabit test.** audit/content.md §2'nin 40 başlıklık örneği (scripts/fixtures/ceviri-ornegi-40.json, mevcut
kusurlu çevirileriyle) üç sınamadan geçer. §2 16 kusurlu kalemin 12'sini adlandırıyor: metinde
anılan 8 (KF-21, Care, Iran's military, wheeling auction, Commons, UK MoD/Rolls-Royce, 유해,
Hormuz) ve "cümle düzenindeki 7 başlığın 7'si de kusurlu" (3'ü ortak). Kalan 4 kusurlu kalem
§2'de adıyla yok; hepsi başlık düzenindeki 28 başlıklık havuzda. Test yakalananı iki biçimde
sayar: **kesin alt sınır** = adlandırılan 12'den yakalanan + (4 − havuzda HİÇBİR sınamanın
tutmadığı başlık sayısı) — 4 bilinmeyenin en kötü ihtimalle en temiz başlıklar olduğu varsayılır;
ve **beklenen** = 12'den yakalanan + 4 × (havuzda yakalanma oranı). Kırmızı: alt sınır < 7.

**Akış.** translate_news.cevir() sahte çevirmenle (enjekte edilen `cagir`; gerçek `claude`
çağrılırsa test patlar): temiz kalem bir çağrı; tutan kalem tek yeniden çeviri çağrısı, temizse o
yazılır ("…exiting power procurement" → "çekil"); yine tutarsa önbelleğe özgün yazılır; yeniden
çeviri hiç gelmezse önbelleğe hiçbir şey yazılmaz; Türkçe kaynak sınanmaz; hiçbir kalem üçüncü
kez çevrilmez. CLI (--news-dir, --sahte-cevirmen) ayrı süreçte, PATH'te sahte bir `claude` ile
(çağrılırsa iz bırakır): >10 özgün → ÇEVİRİ-DEDEKTÖRÜ uyarısı, tam 10 → uyarı yok, (A) tablosu
yazılır, data/news değişmez.

Yalnızca stdlib. CI'da `$GITHUB_STEP_SUMMARY`'ye tablo ve 🟢/🔴 satırı ekler.
"""
import hashlib
import json
import os
import pathlib
import subprocess
import sys
import tempfile

ROOT = pathlib.Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "translate_news.py"
ORNEK = ROOT / "scripts" / "fixtures" / "ceviri-ornegi-40.json"  # §2 örneği; audit/ git dışı
sys.path.insert(0, str(ROOT / "scripts"))
import translate_news as T  # noqa: E402

GUN = "2026-09-24"
# §2'nin metinde adlandırdığı 8 kusurlu kalem (özgünün başı → §2'deki kusur).
ADLI = {
    "Kebutuhan 40 MRF Filipina": "etken/edilgen ters (KF-21 özne değil)",
    "Care: Economic infrastructure": "Care → \"Dikkat:\"",
    "Iran’s military says": "atıf daraltıldı (İran ordusu → \"İran:\")",
    "Govt invites bids for first 400MW": "ikinci önerme silindi (exiting power procurement)",
    "New Commons committee": "Commons çevrilmedi (Avam Kamarası)",
    "UK Ministry of Defence says Rolls-Royce": "atıf silindi (bakanlık görüşü)",
    "6·25전쟁 영웅": "유해 → \"Kalıntıları\" (naaş)",
    "Iran's IRGC says it shot down": "Hürmüz → \"Hormuç\"",
}
KUSURLU_TOPLAM = 16
ESIK = 7
CEKIL = ("Hükümet ilk 400 MW'lık iletim ihalesine teklif çağrısı yaptı, elektrik "
         "tedarikinden çekildiğini açıkladı")


def _cumle_duzeni(tr):
    """§2'nin cümle düzeni ölçüsü (özgünden bağımsız): ilk kelimeden sonraki muaf olmayan,
    kısaltma olmayan kelimelerin en fazla yarısı büyük harfle başlıyor."""
    sayilan = buyuk = 0
    for w in T.KELIME_RE.findall(tr)[1:]:
        kok = w.split("'")[0].split("’")[0]
        if T._tr_lower(kok) in T.MUAF or not any(c.islower() for c in kok) or any(c.isupper() for c in kok[1:]):
            continue
        sayilan += 1
        buyuk += kok[0].isupper()
    return sayilan > 0 and buyuk / sayilan <= 0.5


def ornek():
    return json.loads(ORNEK.read_text(encoding="utf-8"))


def sabit():
    """Sabit test: (satırlar, sonuç sözlüğü)."""
    d = ornek()
    adli_idx = {i for i, x in enumerate(d) for bas in ADLI if x["ozgun"].startswith(bas)}
    # §2: cümle düzenindeki 7 başlık — bugünkü çevirilerde küçük harfle devam edenler.
    cumle_idx = {i for i, x in enumerate(d) if _cumle_duzeni(x["tr"])}
    bilinen = sorted(adli_idx | cumle_idx)
    havuz = [i for i in range(len(d)) if i not in bilinen]
    bilinmeyen = KUSURLU_TOPLAM - len(bilinen)
    tutan = {i: T.denetle(x["ozgun"], x["tr"]) for i, x in enumerate(d)}
    yakalanan = [i for i in bilinen if tutan[i]]
    havuz_yakalanan = [i for i in havuz if tutan[i]]
    havuz_temiz = len(havuz) - len(havuz_yakalanan)
    alt = len(yakalanan) + max(0, bilinmeyen - havuz_temiz)
    beklenen = len(yakalanan) + bilinmeyen * len(havuz_yakalanan) / max(1, len(havuz))
    sinama = {}
    for k in T.SINAMALAR:
        bil = sum(1 for i in bilinen if k in tutan[i])
        hv = sum(1 for i in havuz if k in tutan[i])
        sinama[k] = (bil, hv, bil + max(0, bilinmeyen - (len(havuz) - hv)))
    s = {"ornek": len(d), "adli": len(adli_idx), "cumle": len(cumle_idx), "bilinen": len(bilinen),
         "bilinmeyen": bilinmeyen, "havuz": len(havuz), "yakalanan": len(yakalanan),
         "havuz_yakalanan": len(havuz_yakalanan), "alt": alt, "beklenen": beklenen,
         "sinama": sinama, "tutan": tutan, "bilinen_idx": bilinen}
    satir = [f"### ÇEVİRİ-DEDEKTÖRÜ · sabit test (content.md §2, {KUSURLU_TOPLAM} kusurlu kalem, "
             "mevcut çeviriler)", "",
             f"§2'de tanımlı {len(bilinen)} kalem (adlı {len(adli_idx)} ∪ cümle düzenindeki "
             f"{len(cumle_idx)}) · tanımsız {bilinmeyen} kalem {len(havuz)} başlıklık havuzda", "",
             f"| sınama | tanımlı {len(bilinen)}'den yakalanan | havuzda tutan | {KUSURLU_TOPLAM} üzerinden kesin alt sınır |",
             "|---|---|---|---|"]
    for k in T.SINAMALAR:
        bil, hv, a = sinama[k]
        satir.append(f"| {k} | {bil} | {hv}/{len(havuz)} | {a} |")
    satir.append(f"| **en az biri** | **{len(yakalanan)}** | {len(havuz_yakalanan)}/{len(havuz)} | **{alt}** |")
    satir.append("")
    for i in bilinen:
        x = d[i]
        neden = next((v for b, v in ADLI.items() if x["ozgun"].startswith(b)), "cümle düzeninde (§2: 7/7 kusurlu)")
        satir.append(f"- {'✔' if tutan[i] else '·'} {'/'.join(tutan[i]) or '—'} · {x['ozgun'][:70]} — {neden}")
    satir += ["", f"{'🟢' if alt >= ESIK else '🔴'} sabit test: {KUSURLU_TOPLAM} kusurlu kalemden en az "
              f"**{alt}** yakalandı (eşik {ESIK}; beklenen ≈{beklenen:.1f})", ""]
    return satir, s


class Sahte:
    """Sahte çevirmen: {özgün: [ilk, yeniden]} ve her çağrının kaydı."""

    def __init__(self, tablo):
        self.tablo, self.cagrilar = tablo, []

    def __call__(self, prompt):
        self.cagrilar.append(prompt)
        ikinci = "önceki çevirisi denetimden geçemedi" in prompt
        out = []
        for n, line in enumerate(prompt.rsplit("Başlıklar:\n", 1)[1].splitlines(), 1):
            title = line.split(". ", 1)[1]
            secenek = self.tablo.get(title, [title, title])
            tr = secenek[1] if ikinci else secenek[0]
            if tr is not None:
                out.append({"n": n, "tr": tr})
        return json.dumps(out, ensure_ascii=False)


def _kalem(title, n, lang="en"):
    return {"title": title, "url": f"https://ornek.test/{n}", "lang": lang, "source": "Sınama"}


def _hash_news():
    h = hashlib.sha256()
    for p in sorted((ROOT / "data" / "news").iterdir()):
        if p.is_file():
            h.update(p.name.encode() + p.read_bytes())
    return h.hexdigest()


def hazirla(d):
    """Sahte gün: §2'nin 40 başlığı; sahte çevirmen ilk turda mevcut (kusurlu) çeviriyi, yeniden
    çeviride de aynısını verir — yalnız wheeling auction kalemi "çekil" köklü çeviriye düzelir."""
    d = pathlib.Path(d)
    (d / "news").mkdir(parents=True, exist_ok=True)
    items = [_kalem(x["ozgun"], i, x["dil"]) for i, x in enumerate(ornek())]
    (d / "news" / f"{GUN}.json").write_text(json.dumps({"date": GUN, "items": items}, ensure_ascii=False, indent=1))
    tablo = {x["ozgun"]: [x["tr"], CEKIL if x["ozgun"].startswith("Govt invites bids") else x["tr"]]
             for x in ornek()}
    (d / "sahte.json").write_text(json.dumps(tablo, ensure_ascii=False, indent=1))
    return d


def cli(d, tablo, items, iz):
    """translate_news.py'yi ayrı süreçte, sahte çevirmenle; PATH'te iz bırakan sahte `claude`."""
    d = pathlib.Path(d)
    (d / "news").mkdir(parents=True, exist_ok=True)
    for f in (d / "news").iterdir():
        f.unlink()
    (d / "news" / f"{GUN}.json").write_text(json.dumps({"date": GUN, "items": items}, ensure_ascii=False))
    (d / "sahte.json").write_text(json.dumps(tablo, ensure_ascii=False))
    bin_ = d / "bin"
    bin_.mkdir(exist_ok=True)
    (bin_ / "claude").write_text(f"#!/bin/sh\necho cagrildi >> '{iz}'\nexit 1\n")
    (bin_ / "claude").chmod(0o755)
    rt = d / "rt"
    rt.mkdir(exist_ok=True)
    ozet = d / "ozet.md"
    ozet.write_text("")
    env = {**os.environ, "PATH": f"{bin_}{os.pathsep}{os.environ.get('PATH', '')}",
           "RUNNER_TEMP": str(rt), "GITHUB_STEP_SUMMARY": str(ozet)}
    env.pop("GITHUB_ACTIONS", None)
    r = subprocess.run([sys.executable, str(SCRIPT), "--date", GUN, "--news-dir", str(d / "news"),
                        "--sahte-cevirmen", str(d / "sahte.json")], capture_output=True, text=True, env=env)
    u = rt / "defintel-uyari.jsonl"
    kayit = [json.loads(l) for l in u.read_text().splitlines()] if u.exists() else []
    if u.exists():
        u.unlink()
    gun = json.loads((d / "news" / f"{GUN}.json").read_text(encoding="utf-8"))
    return r, ozet.read_text(encoding="utf-8"), kayit, gun


def main(yalniz_sabit=False):
    sonuc = []

    def kontrol(ad, ok, ayrinti=""):
        sonuc.append(bool(ok))
        print(f"{'ok  ' if ok else 'FAIL'} {ad}{' · ' + ayrinti if ayrinti else ''}")

    satir, s = sabit()
    print("\n".join(satir))
    kontrol("sabit test: örnek 40, §2'nin 8 adlı kalemi ve 7 cümle düzeni bulundu",
            s["ornek"] == 40 and s["adli"] == 8 and s["cumle"] == 7 and s["bilinen"] == 12,
            f"örnek {s['ornek']} · adlı {s['adli']} · cümle {s['cumle']} · tanımlı {s['bilinen']}")
    kontrol(f"sabit test: 16 kalemden en az {ESIK}'si yakalandı", s["alt"] >= ESIK,
            f"alt sınır {s['alt']} · beklenen ≈{s['beklenen']:.1f} · " + " · ".join(
                f"{k} {v[0]}+{v[2] - v[0]}" for k, v in s["sinama"].items()))

    if not yalniz_sabit:
        news_once = _hash_news()
        gercek = T.claude

        def patla(prompt):
            raise AssertionError("gerçek claude çağrıldı")
        T.claude = patla
        try:
            # 1) istem
            p = T.PROMPT
            kontrol("istem cümle düzeninde, başlık düzeni kuralı yok",
                    "Cümle düzeni" in p and "her kelimenin ilk harfi büyük" not in p)
            kontrol("istem Ö1 (önerme) ve Ö2 (atıf, konuşan daraltılmaz) taşıyor",
                    "Hiçbir önermeyi atma" in p and "Konuşan daraltılmaz" in p)
            o3 = ("Hürmüz Boğazı", "Kızıldeniz", "Süveyş", "Bab-ül Mendep", "Avam Kamarası",
                  "Lordlar Kamarası", "Pentagon", "Beyaz Saray", "naaş", "şehit", "tabut töreni",
                  "sevkiyat", "transit", "boru hattı kapasitesi")
            eksik = [t for t in o3 if t not in p]
            kontrol("istem Ö3 sözlük eklemelerini taşıyor", not eksik, ", ".join(eksik))
            kontrol("yeniden çeviri istemi aynı kurallar + yeniden notu",
                    T.YENIDEN_PROMPT.startswith(p.split("Başlıklar:")[0]) and "denetimden geçemedi" in T.YENIDEN_PROMPT)

            # 2) akış
            w = "Govt invites bids for first 400MW wheeling auction, says it is exiting power procurement"
            uk = ("UK Ministry of Defence says Rolls-Royce will build every Australian SSN-AUKUS nuclear "
                  "reactor at its Derby facility")
            temiz = "Lockheed Martin presents Germany’s first F-35A jet"
            trk = "Eurofighter’da Yeni Adım: Türk Heyet İngiltere’de"
            iran = "Iran’s military says US preparing to resume strikes"
            tablo = {
                temiz: ["Lockheed Martin, Almanya'nın ilk F-35A uçağını tanıttı", None],
                w: ["Hükümet ilk 400MW taşıyıcılık müzayedesine çağrı yaptı", CEKIL],
                uk: ["Rolls-Royce tüm Avustralya SSN-AUKUS nükleer reaktörlerini Derby'de inşa edecek",
                     "Rolls-Royce tüm Avustralya SSN-AUKUS reaktörlerini Derby'de yapacak"],
                trk: [trk, None],
                iran: ["İran Ordusu: ABD Saldırılara Yeniden Başlamaya Hazırlanıyor", None],
            }
            items = [_kalem(t, n, "tr" if t == trk else "en") for n, t in enumerate(tablo)]
            sahte, cache = Sahte(tablo), {}
            ist = T.cevir(items, cache, 60, cagir=sahte)
            u = {t: f"https://ornek.test/{n}" for n, t in enumerate(tablo)}
            kontrol("temiz kalem ilk çeviriyle yazıldı", cache.get(u[temiz]) == tablo[temiz][0])
            kontrol("Türkçe kaynak sınanmadı, aynen yazıldı", cache.get(u[trk]) == trk)
            kontrol("wheeling auction: atıf tuttu, yeniden çeviri 'çekil' kökünü taşıyor ve yazıldı",
                    "çekil" in cache.get(u[w], "") and ist["ilk"]["atıf"] >= 1, cache.get(u[w], "")[:60])
            kontrol("UK MoD: iki denemede de atıf tuttu → önbellekte özgün (sayfa özgünü basar)",
                    cache.get(u[uk]) == uk)
            kontrol("Iran's military: düzen tuttu, yeniden çeviri gelmedi → önbelleğe yazılmadı",
                    u[iran] not in cache and "düzen" in T.denetle(iran, tablo[iran][0]))
            kontrol("tek yeniden çeviri çağrısı (toplam 2 çağrı), hiçbir kalem üçüncü kez çevrilmedi",
                    len(sahte.cagrilar) == 2 and ist["cagri"] == 2
                    and "denetimden geçemedi" in sahte.cagrilar[1]
                    and len(sahte.cagrilar[1].rsplit("Başlıklar:\n", 1)[1].splitlines()) == 3,
                    f"çağrı {len(sahte.cagrilar)}")
            kontrol("sayaçlar: yeniden 3 · düzelen 1 · özgün 2",
                    (ist["yeniden"], ist["duzelen"], ist["ozgun"]) == (3, 1, 2),
                    f"{ist['yeniden']}/{ist['duzelen']}/{ist['ozgun']}")
            sahte2 = Sahte({temiz: tablo[temiz]})
            T.cevir([items[0]], {}, 60, cagir=sahte2)
            kontrol("temiz partide yeniden çeviri çağrısı yok", len(sahte2.cagrilar) == 1)

            # 3) CLI, ayrı süreç: >10 özgün → uyarı; tam 10 → yok
            with tempfile.TemporaryDirectory() as td:
                iz = pathlib.Path(td) / "claude-iz"
                bozuk = {f"Ministry says item {n} will be delivered by the end of the year to the navy":
                         [f"Kalem {n} Yıl Sonuna Kadar Deniz Kuvvetleri'ne Teslim Edilecek"] * 2 for n in range(11)}
                it11 = [_kalem(t, n) for n, t in enumerate(bozuk)]
                r, ozet, kayit, gun = cli(pathlib.Path(td) / "a", bozuk, it11, iz)
                kontrol("CLI: 11 özgün → ÇEVİRİ-DEDEKTÖRÜ uyarısı",
                        r.returncode == 0 and [k["kural"] for k in kayit] == ["ÇEVİRİ-DEDEKTÖRÜ"]
                        and "11 başlık özgün bırakıldı" in kayit[0]["metin"],
                        kayit[0]["metin"] if kayit else (r.stdout[-300:] + r.stderr[-300:]))
                kontrol("CLI: (A) tablosu sınama başına sayı taşıyor",
                        "| düzen | 11 | 11 |" in ozet and "| atıf | 11 | 11 |" in ozet and "özgün bırakılan 11" in ozet)
                kontrol("CLI: özgün bırakılanlarda title_tr yok", not any(i.get("title_tr") for i in gun["items"]))
                on = dict(list(bozuk.items())[:10])
                on["Navy says it is exiting the programme"] = ["Deniz Kuvvetleri programdan çekildiğini söyledi", None]
                it10 = [_kalem(t, n) for n, t in enumerate(on)]
                r, ozet, kayit, gun = cli(pathlib.Path(td) / "b", on, it10, iz)
                kontrol("CLI: tam 10 özgün → uyarı yok, temiz kalem title_tr aldı",
                        r.returncode == 0 and not kayit and "özgün bırakılan 10" in ozet
                        and sum(1 for i in gun["items"] if i.get("title_tr")) == 1)
                kontrol("CLI: gerçek claude hiç çağrılmadı", not iz.exists())
        finally:
            T.claude = gercek
        kontrol("data/news değişmedi", _hash_news() == news_once)

    ok = all(sonuc)
    son = (f"{'🟢' if ok else '🔴'} ÇEVİRİ-DEDEKTÖRÜ testi: {sum(sonuc)}/{len(sonuc)} kontrol · "
           f"sabit test en az {s['alt']}/{KUSURLU_TOPLAM} (" + " · ".join(
               f"{k} ≥{v[2]}" for k, v in s["sinama"].items()) + ") · model çağrısı 0")
    print(son)
    if os.environ.get("GITHUB_STEP_SUMMARY"):
        with open(os.environ["GITHUB_STEP_SUMMARY"], "a", encoding="utf-8") as fh:
            fh.write("\n".join(satir) + "\n" + son + "\n\n")
    return 0 if ok else 1


if __name__ == "__main__":
    if sys.argv[1:2] == ["hazirla"]:
        print(hazirla(sys.argv[2]))
        sys.exit(0)
    sys.exit(main(yalniz_sabit=sys.argv[1:2] == ["sabit"]))
