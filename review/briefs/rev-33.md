## Revizyon 33 — yabancı adlarda noktalı İ

**Hedef.** Büyük harfe çevrilen yabancı adlar kendi dilinin harfleriyle yazılsın.
**Dosyalar.** `build.py` (kaynak adı yardımcısı, medya satırı, Kaynaklar sayfası),
`assets/app.css` (değişiklik yok, doğrulama için).
**Build kuralı.** NOKTALI-İ.

### R33.0 — Tanı

Sayfa `<html lang="tr">`. `.clip-meta` (`app.css:1153`) `text-transform: uppercase`
taşıyor. Tarayıcı Türkçe büyük harf kuralını uyguluyor ve `i` → `İ` oluyor. 23 Eylül
medya takibinde: **"UNMANNED AİRSPACE"**, **"DEFENSE DAİLY"**. Yabancı her kaynak adında
`i` varsa aynı şey oluyor. Türkçe etiketler ("MEDYA TAKİBİ") doğru, çünkü onlarda
istenen şey bu.

### R33.1 — Karar

- Kaynak adları tek bir yardımcıdan (`src_name()`) geçer. Yardımcı, kaynağın ülkesi TR
  değilse adı `<span lang="en">` ile sarar. Tarayıcı o zaman İngilizce büyük harf kuralını
  uygular.
- Aynısı büyük harfe çevrilen bir alanda duran her yabancı özel ad için geçerli (ör.
  kaynakça jetonları, oyuncu adları).
- CSS'e dokunulmaz. Büyük harf dönüşümü doğru; yanlış olan dil bilgisi.

### Build kuralı — NOKTALI-İ

> Derlenmiş HTML'de `text-transform: uppercase` taşıyan sınıfların (liste `app.css`'ten
> türetilir) içinde, `lang` özniteliği olmadan duran ve ülkesi TR olmayan bir kaynağın adı
> bulunursa **Rev 30** kanalına uyarı gider. Build, sayfanın ilk 10 örneğini **(A)**
> özetine yazar.

### Uygulama listesi — Revizyon 33

| # | Dosya | Değişiklik | Kabul (ekran görüntüsü) |
|---|---|---|---|
| R33-P0-1 | `build.py` `src_name()` | `lang="en"` sarmalı | **(S)** medya takibi, 1440px, Öne çıkanlar: "UNMANNED AIRSPACE", "DEFENSE DAILY" noktasız I ile; "ANADOLU AJANSI" değişmemiş |
| R33-P0-2 | `build.py` | Kaynakça ve diğer büyük harfli alanlar | **(S)** /haberler/…-kaynaklar.html: yabancı adlarda noktalı İ yok |
| R33-P1-1 | `build.py` | NOKTALI-İ | Sarmal bilerek kaldırıldığında **(P)** "NOKTALI-İ" uyarısı |


### Orkestratör notu (23 Eylül)

- **Rev 30 kanalı:** `uyari.ekle("NOKTALI-İ", "…")`; **(P)** → **(I)** (issue satırı). `main`
  dışındaki dallarda issue ancak `UYARI_TEST_ONEK` ayarlıysa açılır.
- **"Sarmal bilerek kaldırıldığında" kanıtı:** kodu bozmadan, `build.yml`'deki mevcut `boz` /
  `kapsam_boz` kalıbıyla bir `workflow_dispatch` girdisi (ör. `noktali_boz: true`) sarmalı
  yalnız o çalıştırmada kapatır ve `UYARI_TEST_ONEK: "[TEST] "` açar. O çalıştırma dala
  commit/push etmemeli (Rev 21'in `kapsam_boz`'u gibi).
- **(A)**: NOKTALI-İ satırı normal çalıştırmada "0 örnek", bozuk çalıştırmada ilk 10 örnek.
