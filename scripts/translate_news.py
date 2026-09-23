"""Translate the day's headlines into Turkish with Claude Code.

Runs on the subscription token, not an API key: the workflow installs the
Claude Code CLI and this script shells out to `claude -p`.

Reads   : data/news/YYYY-MM-DD.json
Writes  : the same file, adding "title_tr" to each item
Cache   : data/news/translations.json keyed by URL, so a headline is only ever
          translated once — reruns and repeated stories cost nothing.
Usage   : python3 scripts/translate_news.py [--date …] [--batch 60] [--refresh]

Rev 26 — ÇEVİRİ-DEDEKTÖRÜ. Her çeviri önbelleğe yazılmadan önce üç sınamadan geçer
(`denetle`): **düzen** (muaf olmayan kelimelerin >%60'ı büyük harfle başlıyor), **uzunluk**
(çeviri < özgün × 0,6), **atıf** (özgünde says/said/according to var, çeviride dedi/göre/:
ya da eşdeğer bir atıf fiili yok). Biri tutan kalemler bir kez yeniden çevrilir; ikinci
deneme de tutarsa özgün başlık basılır (önbelleğe özgün yazılır → title_tr yok). Model
çağrısı enjekte edilebilir (`cevir(..., cagir=...)`): sınamada sahte çevirmen kullanılır,
`--sahte-cevirmen DOSYA` ile CLI da model çağırmadan koşar (scripts/test_ceviri_dedektoru.py).
(A) özetine sınama başına yakalanan sayısı yazılır; günde özgün bırakılan >10 ise
`uyari.ekle("ÇEVİRİ-DEDEKTÖRÜ", …)` (Rev 30 kanalı).
"""

import argparse
import datetime as dt
import json
import os
import pathlib
import re
import subprocess
import sys
import tempfile

ROOT = pathlib.Path(__file__).resolve().parent.parent
# Pinned so a CLI default change can't silently alter output quality.
MODEL = "sonnet"
NEWS_DIR = ROOT / "data" / "news"
CACHE = NEWS_DIR / "translations.json"
# Bunun altında bölmek anlamsız: hata artık uzunluk değil, o başlığın kendisidir.
MIN_BATCH = 8

PROMPT = """Aşağıdaki savunma sanayii haber başlıklarını Türkçeye çevir.

Kurallar:
- Özel isimler, şirket ve program adları, platform adları ve kısaltmalar olduğu gibi kalır: C-UAS, SHORAD, MADIS, HIMARS, NATO, Rheinmetall, Skyranger, Patriot gibi.
- Kalibre, para birimi ve sayılar korunur (30mm, 155 mm, $450 milyon).
- Aşağıdaki terimler savunma sanayiinde yerleşik karşılıklarıyla çevrilir; kelime
  kelime çevirme, İngilizcesini de olduğu gibi bırakma:
    Marines / Marine Corps = Deniz Piyadeleri (U.S. Marines = ABD Deniz Piyadeleri)
    Navy = Deniz Kuvvetleri  ·  Army = Kara Kuvvetleri  ·  Air Force = Hava Kuvvetleri
    Coast Guard = Sahil Güvenlik  ·  squadron = filo  ·  wing = kanat  ·  brigade = tugay
    howitzer = obüs  ·  towed = çekili  ·  self-propelled = kundağı motorlu
    loitering munition = dolanan mühimmat  ·  warhead = harp başlığı
    proximity fuze = yakınlık fünyesi  ·  airburst = havada infilak
    solicitation = ihale ilanı  ·  procurement = tedarik  ·  award = sözleşme
    counter-drone / counter-UAS = karşı-dron (C-UAS kısaltması aynen kalır)
    interceptor = önleyici  ·  propellant = sevk barutu  ·  small arms = hafif silah
    Strait of Hormuz = Hürmüz Boğazı  ·  Red Sea = Kızıldeniz  ·  Suez = Süveyş
    Bab el-Mandeb = Bab-ül Mendep  ·  House of Commons / Commons = Avam Kamarası
    House of Lords / Lords = Lordlar Kamarası  ·  Pentagon = Pentagon
    White House = Beyaz Saray  ·  remains (유해, fallen soldier) = naaş
    fallen / killed in action = şehit  ·  dignified transfer / casket ceremony = tabut töreni
    shipment = sevkiyat  ·  transit = transit  ·  pipeline capacity = boru hattı kapasitesi
  Ama bir terim ürün adının parçasıysa (Marine One gibi) çevrilmez, aynen kalır.
- Başlık dili kullan: haber başlığı tonunda, nokta koyma.
- Cümle düzeni: yalnızca ilk kelime ve özel isimler büyük harfle başlar, diğer bütün
  kelimeler küçük yazılır (Türkçe haber başlığı geleneği). Her kelimeyi büyük harfle
  başlatma.
- Hiçbir önermeyi atma: başlıktaki her bağımsız önerme çeviride yer alır; virgülle ya da
  "says/announces" ile bağlanmış ikinci cümle atılamaz. Başlık uzun geliyorsa kısaltma,
  olduğu gibi çevir.
- Atıf korunur: "X says…", "according to Y", "Y'ye göre" kalıplarında konuşan ve atıf
  fiili çeviride kalır ("dedi", "açıkladı", "…'e göre"). Konuşan daraltılmaz:
  "Iran's military says" → "İran ordusu … dedi", "İran:" değil; "UK Ministry of Defence
  says" → "İngiltere Savunma Bakanlığı: …" ya da "… Bakanlığı'na göre".
- Başlık zaten Türkçeyse aynen geri ver.
- Çeviremediğin bir başlık olursa özgün hâlini geri ver; boş bırakma, açıklama yazma.

Çıktı: yalnızca JSON. Her satır için {"n": numara, "tr": "çeviri"} nesnelerinden oluşan bir dizi. Başka hiçbir metin yazma.

Başlıklar:
{items}"""


def load(path, default):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return default


def claude(prompt):
    """One `claude -p` call. Returns the assistant's text, or None on failure.

    Runs from a scratch directory: inside a repo the CLI wants to establish
    trust for the project first, which it cannot do without a terminal.
    """
    try:
        run = subprocess.run(
            ["claude", "-p", prompt, "--output-format", "json",
             "--model", MODEL, "--dangerously-skip-permissions"],
            capture_output=True, text=True, timeout=600, cwd=tempfile.gettempdir(),
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        print(f"  ! claude çağrısı başarısız: {exc}")
        return None
    if run.returncode != 0:
        envelope = load_json_text(run.stdout) or {}
        detail = " | ".join(
            str(envelope.get(k)) for k in ("subtype", "is_error", "result", "error")
            if envelope.get(k) is not None
        ) or (run.stderr.strip() or run.stdout.strip())
        print(f"  ! claude çıkış kodu {run.returncode}: {detail[:400]}")
        return None
    envelope = load_json_text(run.stdout)
    if isinstance(envelope, dict):
        return envelope.get("result") or ""
    return run.stdout


def load_json_text(text):
    try:
        return json.loads(text)
    except Exception:
        return None


def parse_pairs(text):
    """The model is asked for bare JSON; tolerate a fenced block around it."""
    if not text:
        return []
    block = re.search(r"\[[\s\S]*\]", text)
    data = load_json_text(block.group(0)) if block else None
    if not isinstance(data, list):
        return []
    pairs = []
    for row in data:
        if isinstance(row, dict) and "n" in row and row.get("tr"):
            try:
                pairs.append((int(row["n"]), str(row["tr"]).strip()))
            except (TypeError, ValueError):
                continue
    return pairs


def translate_chunk(chunk, cache, depth=0, cagir=None, prompt=None):
    """Bir partiyi çevirip önbelleğe yaz; kaç başlık geldiğini döndür.

    Boş dönen parti sessizce kaybolmamalı: 20 Eylül'de iki parti boş döndü ve
    120 başlık İngilizce kaldı — kayıp yalnızca sayfada görüldü. Boş dönerse
    bir kez daha denenir, yine boşsa parti ikiye bölünür. Bölmek işe yarıyor
    çünkü en olası sebep çıktının uzunluktan kesilip JSON'un kapanmaması;
    yarısı kesilmiyor. Önbellek URL bazlı olduğu için tekrar bedava.

    `cagir` model çağrısıdır (varsayılan `claude`); sınamada sahte çevirmen verilir.
    """
    cagir = cagir or claude
    prompt = prompt or PROMPT
    if not chunk:
        return 0
    listing = "\n".join(f'{n}. {i["title"]}' for n, i in enumerate(chunk, 1))
    pairs = parse_pairs(cagir(prompt.replace("{items}", listing)))
    got = 0
    for n, turkish in pairs:
        if 1 <= n <= len(chunk):
            cache[chunk[n - 1]["url"]] = turkish
            got += 1
    if got:
        return got
    if depth == 0:
        print(f"    ! {len(chunk)} başlık boş döndü, tekrar deneniyor")
        return translate_chunk(chunk, cache, depth + 1, cagir, prompt)
    if len(chunk) > MIN_BATCH:
        half = len(chunk) // 2
        print(f"    ! yine boş, {len(chunk)} başlık ikiye bölünüyor")
        return (translate_chunk(chunk[:half], cache, depth + 1, cagir, prompt)
                + translate_chunk(chunk[half:], cache, depth + 1, cagir, prompt))
    print(f"    ! {len(chunk)} başlık çevrilemedi, özgün hâlleriyle kalacak")
    return 0


# ── Rev 26 · ÇEVİRİ-DEDEKTÖRÜ ────────────────────────────────────────────────

SINAMALAR = ("düzen", "uzunluk", "atıf")
DUZEN_ESIK = 0.60        # muaf olmayan kelimelerin bu oranından fazlası büyükse → düzen
UZUNLUK_ORAN = 0.60      # çeviri, özgünün bu katından kısaysa → uzunluk
OZGUN_UYARI_ESIGI = 10   # bir günde bundan fazla özgün bırakılan → Rev 30 uyarısı
# Başlık düzeninde de küçük kalan bağlaç/edatlar: sayılmaz ("Ve", "İçin" yine muaf).
MUAF = {"ve", "ile", "için", "de", "da", "ki", "mi", "mı", "mu", "mü", "veya", "ya",
        "ama", "ancak", "gibi", "ya da"}
KELIME_RE = re.compile(r"[^\W\d_][\w'’.\-]*")
KAYNAK_ATIF_RE = re.compile(r"\b(says|said|according to)\b", re.I)
# Özetin saydığı üçü (dedi / göre / ":") ve aynı işi gören atıf fiilleri.
TR_ATIF_RE = re.compile(r"dedi|diyor|göre|:|söyledi|açıkladı|bildirdi|belirtti|iddia")
YENIDEN_NOTU = """Not: bu başlıkların önceki çevirisi denetimden geçemedi (önerme ya da konuşan
eksik, ya da her kelime büyük harfle başlıyor). Her önermeyi ve konuşanı koru, cümle düzeni
kullan.

Başlıklar:
{items}"""
YENIDEN_PROMPT = PROMPT.replace("Başlıklar:\n{items}", YENIDEN_NOTU)


def _tr_lower(text):
    return text.replace("I", "ı").replace("İ", "i").lower()


def _duzen(ozgun, tr):
    """Başlık düzeni mi? İlk kelime, muaf kelime, kısaltma/rakamlı (NATO, F-35A, WiSENT) ve
    özgünde aynen büyük geçen özel isim (Lockheed) sayılmaz; en az 3 kelime kalmalı."""
    ozgun_kelime = {w.split("'")[0].split("’")[0] for w in KELIME_RE.findall(ozgun)}
    sayilan = buyuk = 0
    for i, w in enumerate(KELIME_RE.findall(tr)):
        kok = re.split(r"['’]", w)[0].rstrip(".-")
        if i == 0 or not kok or _tr_lower(kok) in MUAF:
            continue
        if not any(c.islower() for c in kok) or any(c.isupper() for c in kok[1:]):
            continue
        if kok in ozgun_kelime and kok[0].isupper():
            continue
        sayilan += 1
        buyuk += kok[0].isupper()
    return sayilan >= 3 and buyuk / sayilan > DUZEN_ESIK


def denetle(ozgun, tr):
    """Tutan sınamaların adları (boş liste = temiz). Özgünü aynen dönen (Türkçe kaynak,
    çevrilemeyen) kalem sınanmaz: ortada çeviri yok."""
    ozgun = re.sub(r"\s+", " ", ozgun or "").strip()
    tr = re.sub(r"\s+", " ", tr or "").strip()
    if not tr or tr == ozgun:
        return []
    tutan = []
    if _duzen(ozgun, tr):
        tutan.append("düzen")
    if len(tr) < len(ozgun) * UZUNLUK_ORAN:
        tutan.append("uzunluk")
    if KAYNAK_ATIF_RE.search(ozgun) and not TR_ATIF_RE.search(_tr_lower(tr)):
        tutan.append("atıf")
    return tutan


def bos_istatistik():
    return {"ilk": {k: 0 for k in SINAMALAR}, "ikinci": {k: 0 for k in SINAMALAR},
            "sinanan": 0, "yeniden": 0, "duzelen": 0, "ozgun": 0, "ozgun_kalemler": [],
            "cagri": 0}


def cevir(pending, cache, batch, cagir=None, ist=None):
    """Partiler hâlinde çevir, ÇEVİRİ-DEDEKTÖRÜ'nden geçir, önbelleğe yaz.

    Temiz çeviri → önbellek. Tutan kalemler partinin sonunda tek çağrıyla bir kez yeniden
    çevrilir; yeniden çeviri temizse o yazılır, yine tutarsa özgün başlık yazılır (sayfa
    özgünü basar). Yeniden çeviri hiç gelmezse önbelleğe bir şey yazılmaz: bugün özgün
    basılır, yarınki çalıştırma yeniden dener. `ist` sayaçlarını döndürür.
    """
    cagir = cagir or claude
    ist = ist or bos_istatistik()

    def sayan(prompt):
        ist["cagri"] += 1
        return cagir(prompt)

    for start in range(0, len(pending), batch):
        chunk = pending[start:start + batch]
        taze = {}
        got = translate_chunk(chunk, taze, cagir=sayan)
        isaretli = []
        for item in chunk:
            tr = taze.get(item["url"])
            if tr is None:
                continue
            tutan = denetle(item["title"], tr)
            ist["sinanan"] += 1
            for k in tutan:
                ist["ilk"][k] += 1
            if tutan:
                isaretli.append(item)
                print(f"    ? {'/'.join(tutan)} · {item['title'][:70]} → {tr[:70]}")
            else:
                cache[item["url"]] = tr
        ikinci = {}
        if isaretli:
            ist["yeniden"] += len(isaretli)
            listing = "\n".join(f'{n}. {i["title"]}' for n, i in enumerate(isaretli, 1))
            for n, turkish in parse_pairs(sayan(YENIDEN_PROMPT.replace("{items}", listing))):
                if 1 <= n <= len(isaretli):
                    ikinci[isaretli[n - 1]["url"]] = turkish
        for item in isaretli:
            tr2 = ikinci.get(item["url"])
            tutan2 = denetle(item["title"], tr2) if tr2 else []
            for k in tutan2:
                ist["ikinci"][k] += 1
            if tr2 and not tutan2:
                cache[item["url"]] = tr2
                ist["duzelen"] += 1
                continue
            ist["ozgun"] += 1
            ist["ozgun_kalemler"].append(item["url"])
            if tr2:
                cache[item["url"]] = item["title"]
            print(f"    ! özgün basılacak ({'/'.join(tutan2) or 'yeniden çeviri gelmedi'}) · {item['title'][:80]}")
        print(f"  · {start + 1}-{start + len(chunk)}: {got}/{len(chunk)} çevrildi"
              f" · dedektör {len(isaretli)} · özgün {sum(1 for i in isaretli if i['url'] in ist['ozgun_kalemler'])}")
    return ist


def ozet_satirlari(gun, ist):
    """(A) özeti: sınama başına yakalanan sayısı ve yeniden çeviri sonucu."""
    satir = [f"### ÇEVİRİ-DEDEKTÖRÜ · {gun}", "",
             "| sınama | ilk çeviride yakalanan | yeniden çeviride yine tutan |", "|---|---|---|"]
    for k in SINAMALAR:
        satir.append(f"| {k} | {ist['ilk'][k]} | {ist['ikinci'][k]} |")
    isaret = "🔴" if ist["ozgun"] > OZGUN_UYARI_ESIGI else "🟢"
    satir += ["", f"{isaret} sınanan {ist['sinanan']} · yeniden çevrilen {ist['yeniden']} · "
                  f"düzelen {ist['duzelen']} · özgün bırakılan {ist['ozgun']} "
                  f"(uyarı eşiği >{OZGUN_UYARI_ESIGI}) · model çağrısı {ist['cagri']}", ""]
    return satir


def bitir(gun, ist):
    """Özet + gerekirse Rev 30 uyarısı. Uyarı gönderildiyse True."""
    satir = ozet_satirlari(gun, ist)
    print("\n".join(satir))
    ozet = os.environ.get("GITHUB_STEP_SUMMARY")
    if ozet:
        with open(ozet, "a", encoding="utf-8") as fh:
            fh.write("\n".join(satir) + "\n")
    if ist["ozgun"] > OZGUN_UYARI_ESIGI:
        import uyari
        uyari.ekle("ÇEVİRİ-DEDEKTÖRÜ",
                   f"{gun}: {ist['ozgun']} başlık özgün bırakıldı (>{OZGUN_UYARI_ESIGI}) — ilk çeviride "
                   + " · ".join(f"{k} {ist['ilk'][k]}" for k in SINAMALAR))
        return True
    return False


def sahte_cevirmen(yol):
    """--sahte-cevirmen: {özgün başlık: [ilk çeviri, yeniden çeviri]} → model çağırmayan `cagir`.
    Yeniden çeviri istemi YENIDEN_NOTU taşır; listede olmayan başlık özgün döner."""
    tablo = json.loads(pathlib.Path(yol).read_text(encoding="utf-8"))

    def cagir(prompt):
        ikinci = "önceki çevirisi denetimden geçemedi" in prompt
        liste = prompt.rsplit("Başlıklar:\n", 1)[1]
        cikti = []
        for satir in liste.splitlines():
            m = re.match(r"(\d+)\. (.*)$", satir)
            if not m:
                continue
            secenek = tablo.get(m.group(2))
            tr = (secenek[1] if ikinci else secenek[0]) if secenek else m.group(2)
            if tr:
                cikti.append({"n": int(m.group(1)), "tr": tr})
        return json.dumps(cikti, ensure_ascii=False)
    return cagir


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--date", default=dt.datetime.now(dt.timezone.utc).date().isoformat())
    ap.add_argument("--batch", type=int, default=60)
    ap.add_argument("--limit", type=int, help="yalnızca ilk N başlığı çevir (deneme)")
    ap.add_argument("--refresh", action="store_true",
                    help="o günün başlıklarını önbelleğe bakmadan yeniden çevir "
                         "(istem değiştiğinde eski çeviriler kendiliğinden düzelmez)")
    ap.add_argument("--news-dir", help="data/news yerine bu dizin (sınama; önbellek de orada)")
    ap.add_argument("--sahte-cevirmen", metavar="DOSYA",
                    help="model çağırma: {özgün: [ilk, yeniden]} JSON'undan çevir (sınama)")
    args = ap.parse_args()

    news_dir = pathlib.Path(args.news_dir) if args.news_dir else NEWS_DIR
    cache_file = news_dir / CACHE.name
    cagir = sahte_cevirmen(args.sahte_cevirmen) if args.sahte_cevirmen else claude

    day_file = news_dir / f"{args.date}.json"
    if not day_file.exists():
        sys.exit(f"{day_file.name} yok; önce toplayıcı çalışmalı")

    day = json.loads(day_file.read_text(encoding="utf-8"))
    cache = load(cache_file, {})
    items = day.get("items", [])

    pending = items if args.refresh else [i for i in items if i["url"] not in cache]
    print(f"{len(items)} başlık · önbellekte {len(items) - len(pending)} · çevrilecek {len(pending)}")
    if args.limit and args.limit > 0:
        pending = pending[: args.limit]
        print(f"  (deneme: ilk {len(pending)} başlık)")

    ist = cevir(pending, cache, args.batch, cagir=cagir)

    ozgun = set(ist["ozgun_kalemler"])
    for item in items:
        turkish = cache.get(item["url"])
        if item["url"] in ozgun:
            item.pop("title_tr", None)   # dedektör: özgün basılır (--refresh'te eski çeviri de kalkar)
        elif turkish and turkish != item["title"]:
            item["title_tr"] = turkish

    day_file.write_text(json.dumps(day, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    cache_file.write_text(json.dumps(cache, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    translated = sum(1 for i in items if i.get("title_tr"))
    print(f"  · {translated}/{len(items)} başlık Türkçe · önbellek {len(cache)} kayıt")
    bitir(args.date, ist)


if __name__ == "__main__":
    main()
