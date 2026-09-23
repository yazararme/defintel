## Revizyon 23 — bir olgu, bir ad, bir değer

**Hedef.** Bir gelişmenin adı ve sayıları sayfanın her yerinde tek ve doğru olsun.
**Dosyalar.** `enrich.py`, `build.py`, rapor promptu (masaüstü görev talimatı; müşteri
yapıştırır).
**Build kuralları.** ETİKET-BAŞLIK · KUR · H1-TEKRAR.

### R23.0 — Tanı: yasa var, uygulanmıyor

1. **Etiket başlık olmadı.** `source/2026-09-23.md:9`'da G9'un etiketi "Lynx XM30 prototip
   teslimi", ama sayfa başlığı "American Rheinmetall". Aynı sorun G3 ve G8'de de var.
   İzleme listesindeki bağlantı "Lynx XM30 prototip teslimi" diyor, indiği başlık başka
   bir şey söylüyor.
2. **Ajan kur çevirdi ve yanıldı.** Brifing "1,5 milyar $ (16 milyar NOK)" diyor. Kaynak
   özetleri ise "NOK 16 milyar (yaklaşık 1,74 milyar dolar)" diyor
   (`data/news/2026-09-23.json:1179`).
3. **H1, özetin 1. maddesi.**
4. **Özetin 2. maddesinde özne yok.**

### R23.1 — Karar

- Gelişme başlığı **her zaman** `label`. Ajanın kalın yazdığı giriş kelimeleri gövdeden
  atılır (`enrich.py`, Rev 11'in yolu).
- Prompt'a üç cümle eklenir:
  - Kur: *"Tutarı kaynağın verdiği para biriminde yaz. Kaynak kendi çevirisini veriyorsa
    parantez içinde aynen aktar. Kendin kur çevirme."*
  - H1: *"Başlık günün tezidir, özet maddelerinden biri değildir."*
  - Özne: *"Her özet maddesi kimin ne yaptığını söyler."*

### Build kuralları — R23

> **ETİKET-BAŞLIK.** Her `h3.dev` kendi `label`'ına eşit olmalı. Her `→ bugün:` bağlantı
> metni de indiği başlığa eşit olmalı.
> **KUR.** Gövdede bir para birimi ve yanında parantez içinde başka bir para birimi varsa
> uyarı verilir, iki değer de aynı `[K#]`'in medya özetinde geçmiyorsa.
> **H1-TEKRAR.** H1 ile herhangi bir özet maddesinin sözcük örtüşmesi ≥0,6 ise uyarı
> verilir.
> Üçü de **Rev 30** kanalına uyarı gönderir, derlemeyi durdurmaz. Rapor insan incelemesi
> olmadan yayımlanıyor; durdurmak, yöneticiye o sabah hiç rapor gitmemesi demek.

### Uygulama listesi — Revizyon 23

| # | Dosya | Değişiklik | Kabul (ekran görüntüsü) |
|---|---|---|---|
| R23-P0-1 | `enrich.py` | Başlık `label`'dan | **(S)** 23 Eylül brifingi, 1440px: G9'un başlığı "Lynx XM30 prototip teslimi"; izleme listesindeki aynı adlı bağlantı bu başlığa iner |
| R23-P0-2 | rapor promptu | Kur, H1 ve özne cümleleri | Sonraki 3 raporda **(P)** KUR ve H1-TEKRAR uyarısı gelmez |
| R23-P1-1 | `build.py` | Üç kural | 23 Eylül yeniden derlendiğinde **(P)** "KUR: SAN CUAS 1,5 milyar $ ↔ özet 1,74" ve "H1-TEKRAR: özet 1" uyarıları gelir |

**Yapılmayacak:** kur çevirisini build'e yaptırmak (build ağa çıkmaz).

---

### Orkestratör notu (23 Eylül)

- **Rev 30 kanalı:** uyarılar günün GitHub issue'suna gider (`uyari.ekle("KUR", "…")`,
  `uyari.ekle("H1-TEKRAR", "…")`, `uyari.ekle("ETİKET-BAŞLIK", "…")`). **(P)** → **(I)**
  (issue satırı). `main` dışındaki dallarda issue ancak `UYARI_TEST_ONEK` ayarlıysa açılır.
- **R23-P1-1 kanıtı:** `build.yml`'e genel bir `workflow_dispatch` girdisi ekle (ör. `uyari_test:
  true`) — kodu bozmadan yalnızca `UYARI_TEST_ONEK: "[TEST] "` açar, böylece dal üzerindeki
  normal derlemenin gerçek uyarıları (23 Eylül'ün KUR ve H1-TEKRAR'ı) [TEST] issue'suna düşer.
  Mevcut `boz` / `kapsam_boz` girdilerini koru.
- **R23-P0-2 (prompt):** masaüstü görevinin gerçek talimatı bu repoda yok (Drive'daki
  `task-prompt.md` yetkisiz, eski bir kopya — okuma). Üç cümleyi, müşterinin görev talimatına
  yapıştıracağı hâliyle `review/builder-notes/rev-23-prompt.md` dosyasına yaz (yerleştirileceği
  yeri tarif et). "Sonraki 3 rapor" ölçütü zamana bağlı; inceleyici bunu PENDING-HUMAN sayar.
