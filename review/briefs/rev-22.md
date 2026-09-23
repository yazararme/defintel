## Revizyon 22 — arama durumlarını ayırmak

**Hedef.** Arama ve süzme dört durumu ayrı ve doğru söylesin: yükleniyor, hata, sonuç
yok, N sonuç.
**Dosyalar.** `assets/app.js` (`load()`, `retally`/`sectionParts`, kapsam satırı),
`scripts/check_reports.py`, `.github/workflows/build.yml`.
**Build kuralı.** DÖRT-DURUM.

### R22.0 — Tanı

- Arşivde ağ hatası "sonuç yok" gibi görünüyor (F-01, P0): `load()` hatayı `[]` ile
  çözümlüyor.
- Medya takibinde sonuç yok durumu boş sayfa gibi görünüyor (F-02): `sectionParts()`
  `#noresults`'ı da gizliyor.
- Yükleme durumu yok (F-16).
- Kapsam satırı süzgeçle yeniden sayılmıyor (F-06). Rev 18b'nin yasası bu sayfada
  uygulanmamış.

Rev 7'nin kanunu: **bir yüzey, sonucunu bildiremediği bir eylemi tetikleyemez.**

### R22.1 — Kural

- `load()` hatayı asla boş diziyle çözümlemez. Hata durumunda panel *"Arama şu an
  çalışmıyor — sayfayı yenileyin."* yazar. Neden yazılmaz.
- `#noresults` bölüm yürüyüşünün dışına taşınır.
- 300ms'yi geçen yüklemede panel "Aranıyor…" yazar.
- Süzgeç açıkken kapsam satırı **"{görünen} / 536 başlık"** yazar.

### Build kuralı — DÖRT-DURUM

> `check_reports.py` başsız bir tarayıcıda dört senaryo koşar: `fetch` reddedilir →
> "çalışmıyor"; "xyzzy" → `#noresults` görünür; 3 sn gecikme → "Aranıyor…"; "Hanwha" → ≥1
> sonuç. Her senaryonun ekran görüntüsü **(A)** özetine eklenir. Biri kalırsa **build
> durur** ve **Rev 30** kanalına uyarı gider. Bu kural bloklayıcı, çünkü sessizce yanlış
> olan tek yüzey bu.

### Uygulama listesi — Revizyon 22

| # | Dosya | Değişiklik | Kabul (ekran görüntüsü) |
|---|---|---|---|
| R22-P0-1 | `assets/app.js:733` | Hata dalı ayrı çizilir | **(A)** "fetch reddedildi" senaryosunun görüntüsü "Arama şu an çalışmıyor" gösterir, "kayıt yok" göstermez |
| R22-P0-2 | `assets/app.js` | Yürüyüş `#noresults`'ta durur | **(S)** medya takibi, 375px, "xyzzy" arandı: "sonuç yok" metni görünür |
| R22-P1-1 | `assets/app.js` | Yükleniyor durumu | **(A)** 3 sn gecikme senaryosunda "Aranıyor…" |
| R22-P1-2 | `assets/app.js` | Kapsam satırı yeniden sayılır | **(S)** `?oyuncu=roketsan` → "2 / 536 başlık" |
| R22-P1-3 | `check_reports.py`, `build.yml` | DÖRT-DURUM | **(A)** dört görüntü yeşil; bir dal bilerek bozulduğunda kırmızı çalıştırma ve **(P)** uyarısı |

---

### Orkestratör notu (23 Eylül)

- **Rev 30 kanalı değişti:** uyarılar artık günün GitHub issue'suna gider (`scripts/uyari.py`,
  `uyari.ekle("DÖRT-DURUM", "…")`; iş sonunda `python3 scripts/uyari.py` boşaltır). Yukarıdaki
  **(P) uyarısı** ölçütü → **(I)**: issue sayfasında DÖRT-DURUM satırı. `main` dışındaki dallarda
  issue ancak `UYARI_TEST_ONEK` ayarlıysa (`[TEST] ` önekiyle) açılır.
- **(A) kanıtı** için "bir dal bilerek bozulduğunda" senaryosu, koda bozuk commit atmadan,
  `build.yml`'in `workflow_dispatch` girdisiyle (ör. `boz: fetch`) tetiklenebilmeli; o çalıştırma
  `UYARI_TEST_ONEK: "[TEST] "` ile koşar.
