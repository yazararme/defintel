#!/usr/bin/env python3
"""Ağsız yeniden kategorileme (Rev 25): saklı günlük veriye bugünkü sınıflandırma kuralları.

    python3 scripts/yeniden_kategorile.py 2026-09-23          # yalnız göster (dosyaya dokunmaz)
    python3 scripts/yeniden_kategorile.py 2026-09-23 --yaz    # data/news/<gün>.json'a yaz

Kurallar collect_news.py'deki categorise() — İPUCU-YOK (S2: kaynak ipucu yok), S3, S4, S6.
Ağ, Drive, Claude çağrısı yok. Kalem eklenmez, silinmez, sırası ve başka hiçbir alanı
değişmez: yalnız her kalemin `category` alanı ve günün `categories` sayımı yeniden yazılır.
Savunma dışı işaretli (`savunma_terimi: false`) kalem Genel'de kalır, toplamadaki gibi.
Dosya biçimi toplayıcınınkiyle aynı (indent=1, ensure_ascii=False, sonda satır sonu).
"""
import collections
import json
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import collect_news as C  # noqa: E402


def yeni_kategori(item):
    if item.get("savunma_terimi") is False:
        return C.GENERAL
    return C.categorise(item.get("title") or "", item.get("lang") or "")


def yeniden(day, yaz=False, out=sys.stdout):
    path = C.OUT_DIR / f"{day}.json"
    text = path.read_text(encoding="utf-8")
    data = json.loads(text)
    items = data.get("items") or []
    once = collections.Counter(i.get("category") for i in items)
    tasinan = []
    for item in items:
        yeni = yeni_kategori(item)
        if yeni != item.get("category"):
            tasinan.append((item.get("category"), yeni, item))
            item["category"] = yeni
    sonra = collections.Counter(i.get("category") for i in items)
    print(f"# {day} · {len(items)} kalem · {len(tasinan)} kalemin kategorisi değişti", file=out)
    print(f"{'kategori':32} önce  sonra", file=out)
    for name in C.CANDIDATE_ORDER[1:]:
        print(f"{name:32} {once.get(name, 0):4}  {sonra.get(name, 0):5}", file=out)
    akis = collections.Counter((a, b) for a, b, _ in tasinan)
    print("taşıma (önce → sonra: adet)", file=out)
    for (a, b), n in akis.most_common():
        print(f"  {a} → {b}: {n}", file=out)
    for a, b, i in tasinan:
        print(f"  - [{a} → {b}] {i.get('source')} · {i.get('title', '')[:100]}", file=out)
    if yaz and tasinan:
        data["categories"] = {k: v for k, v in sorted(sonra.items())}
        yeni_metin = json.dumps(data, ensure_ascii=False, indent=1) + "\n"
        # güvenlik: yalnız kategori alanları değişmiş olmalı
        eski, yeni_ = json.loads(text), json.loads(yeni_metin)
        assert len(eski["items"]) == len(yeni_["items"])
        for a, b in zip(eski["items"], yeni_["items"]):
            assert {k: v for k, v in a.items() if k != "category"} == \
                {k: v for k, v in b.items() if k != "category"}
        assert {k: v for k, v in eski.items() if k not in ("items", "categories")} == \
            {k: v for k, v in yeni_.items() if k not in ("items", "categories")}
        path.write_text(yeni_metin, encoding="utf-8")
        print(f"yazıldı: {path.relative_to(ROOT)}", file=out)
    return once, sonra, tasinan


if __name__ == "__main__":
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    if not args:
        sys.exit(__doc__)
    for day in args:
        yeniden(day, yaz="--yaz" in sys.argv)
