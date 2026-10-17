#!/usr/bin/env python3
"""K10 testi: KAYNAKLAR satırları madde işaretli de işaretsiz de gelse aynı sayfa, ağsız.

    python3 scripts/test_kaynak_bicim.py        # tüm kontroller, çıkış 1 = kırmızı

Fixture: scripts/fixtures/k10-2026-10-15-isaretsiz.md — 15 Ekim 2026'nın özgün raporu; 21 KAYNAKLAR
satırı `[K#] …` ile başlıyor, önlerinde `- ` yok. İşaretli biçim aynı dosyadan, yalnız KAYNAKLAR
bölümündeki o satırlara `- ` eklenerek üretilir (build.py'nin kendi işlevi kullanılmadan).

Kırmızı koşullar:
  1. iki biçim build.render_body'den aynı HTML'i vermiyor; KAYNAKLAR listesi K1…K21 çapalarını
     (id="k1"…id="k21") taşımıyor; sayfadaki bir href="#kN" çapasız kalıyor
  2. KAYNAKLAR dışındaki bir satır başı [K#] (ör. GELİŞMELER'de) değişiyor
  3. scripts/check_reports.py iki biçimden birinde kırmızı
  4. KAYNAK-BİÇİM uyarısı işaretsizde tam bir satır ("21 kaynak satırı") değil, ya da işaretlide var
"""
import os
import pathlib
import re
import sys
import tempfile

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
os.environ.pop("RUNNER_TEMP", None)       # uyarılar bellekte kalsın, dosyaya yazılmasın
os.environ.pop("GITHUB_ACTIONS", None)

import build                               # noqa: E402
from scripts import check_reports, uyari   # noqa: E402

FX = ROOT / "scripts" / "fixtures" / "k10-2026-10-15-isaretsiz.md"
ISO = "2026-10-15"
kirmizi = []


def kontrol(ad, ok, ayrinti=""):
    print(f"{'ok  ' if ok else 'FAIL'} {ad}" + (f" · {ayrinti}" if ayrinti else ""))
    if not ok:
        kirmizi.append(ad)


def isaretle(text):
    """Bağımsız başvuru: KAYNAKLAR başlığı ile sonraki ## arasında `[K` ile başlayan satıra `- `."""
    out, icinde = [], False
    for line in text.split("\n"):
        if line.startswith("## "):
            icinde = line.strip() == "## KAYNAKLAR"
        out.append("- " + line if icinde and line.startswith("[K") else line)
    return "\n".join(out)


def derle(body, meta):
    uyari._BELLEK.clear()
    body = build.kaynak_bicimi(ISO, body)
    html = build.render_body(body, meta.get("developments") or [], bool(meta.get("alarm")), ISO)
    return html, [k for k in uyari._BELLEK if k["kural"] == "KAYNAK-BİÇİM"]


def main():
    isaretsiz = FX.read_text(encoding="utf-8")
    isaretli = isaretle(isaretsiz)
    n_satir = len(re.findall(r"(?m)^\[K\d+\]", isaretsiz))
    kontrol("fixture: 21 işaretsiz kaynak satırı, işaretli kopyada 0",
            n_satir == 21 and not re.search(r"(?m)^\[K\d+\]", isaretli), f"{n_satir}")

    meta, body_y = build.split_frontmatter(isaretsiz)
    _, body_i = build.split_frontmatter(isaretli)

    # 0 · düzeltmesiz derleme gerçekten bozuk (testin kendisi bir şey ölçüyor)
    ham = build.render_body(body_y, meta.get("developments") or [], bool(meta.get("alarm")), ISO)
    kontrol("0 · düzeltmesiz işaretsiz biçim: id=\"kN\" çapası yok",
            not re.search(r'id="k\d+"', ham), f"{len(re.findall(r'id=\"k\\d+\"', ham))} çapa")

    html_y, uy_y = derle(body_y, meta)
    html_i, uy_i = derle(body_i, meta)

    # 1 · aynı HTML, 21 çapa, her #kN çözülüyor
    kontrol("1 · iki biçim aynı HTML", html_y == html_i,
            f"{len(html_y)} / {len(html_i)} karakter")
    refs = re.search(r'<details class="refs" id="kaynaklar">.*?</details>', html_y, re.S)
    ids = re.findall(r'<li id="(k\d+)" class="source">', refs.group(0)) if refs else []
    kontrol("1 · KAYNAKLAR listesi k1…k21", ids == [f"k{i}" for i in range(1, 22)], f"{len(ids)} çapa")
    tum_id = set(re.findall(r'\bid="([^"]+)"', html_y))
    hrefs = re.findall(r'href="#(k\d+)"', html_y)
    asili = sorted(set(h for h in hrefs if h not in tum_id))
    kontrol("1 · her href=\"#kN\" bir çapaya gidiyor", hrefs and not asili,
            f"{len(hrefs)} atıf, {len(set(hrefs))} hedef, çapasız {asili or 0}")

    # 2 · yalnız KAYNAKLAR bölümü değişir
    sahte = body_y.replace("## FIRSATLAR", "[K3] gövdede satır başı atıf\n\n## FIRSATLAR", 1)
    yeni, n = build.kaynak_maddele(sahte)
    kontrol("2 · KAYNAKLAR dışı satır başı [K#] dokunulmadı, 21 satır çevrildi",
            "\n[K3] gövdede satır başı atıf\n" in yeni and n == 21 and yeni == isaretle(sahte), f"n={n}")
    kontrol("2 · işaretli biçimde hiçbir şey değişmez", build.kaynak_maddele(body_i) == (body_i, 0))

    # 3 · check_reports iki biçimde de yeşil
    with tempfile.TemporaryDirectory() as d:
        for ad, text in (("işaretsiz", isaretsiz), ("işaretli", isaretli)):
            p = pathlib.Path(d) / f"{ISO}.md"
            p.write_text(text, encoding="utf-8")
            sorun = check_reports.check(p)
            kontrol(f"3 · check_reports {ad}: yeşil", sorun == [], "; ".join(sorun[:3]) or "0 sorun")

    # 4 · KAYNAK-BİÇİM yalnız işaretsizde, tek satır
    kontrol("4 · KAYNAK-BİÇİM işaretsizde tek satır",
            len(uy_y) == 1 and uy_y[0]["metin"] == f"{ISO} · 21 kaynak satırı madde işaretsiz; build listeye çevirdi",
            uy_y[0]["metin"] if uy_y else "satır yok")
    kontrol("4 · KAYNAK-BİÇİM işaretlide yok", not uy_i, f"{len(uy_i)} satır")

    print(f"\nKAYNAK-BİÇİM testi: {'yeşil' if not kirmizi else 'KIRMIZI: ' + ', '.join(kirmizi)}"
          f" · 21 çapa · {len(hrefs)} atıf")
    return 1 if kirmizi else 0


if __name__ == "__main__":
    sys.exit(main())
