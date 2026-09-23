## Revizyon 29 — görsel sistem ve hijyen

**Hedef.** Kanun metne uysun: her sınır tek mekanizma, her yazı boyutu bir belirteç.
**Dosyalar.** `assets/app.css`, `assets/app.js` (bildirim kartı), `build.py` (masthead
metni), `scripts/check_reports.py`.
**Build kuralları.** L1-DOLGU · ÇİZGİ-KONTRAST · TİP-BELİRTECİ.

### R29.1 — Çizgiler (F-12)

Bölüm sınırı çizgisi (`--rule-2`) ≥3:1'e çekilir. İnce ayraçlar (`--rule`) kalır. Yeni
belirteç eklenmez, yalnızca değer değişir.

### R29.2 — Yazı boyutları

Yaklaşık 20 değer 7 belirtece iner: `--fs-meta 11` · `--fs-small 13` · `--fs-body 17` ·
`--fs-lead 18.5` · `--fs-h3 20` · `--fs-h2 23` · `--fs-h1 34`.

### R29.3 — Küçük maddeler

- **F-13:** ölü koruma `:root` olur. Tema anahtarı yapılmayacak (Rev 0 NOT).
- **F-03/F-14:** kart ilk ziyarette endnav'ın üstünde, akış içinde görünür. Footer'a 96px
  alt boşluk eklenir.
- **F-07:** masthead'e "· brifing" / "· medya takibi" eklenir.
- **F-08:** daybar çipine sayı eklenmez (88px yapışkan bütçe).
- **F-11:** Oyuncular ve İzleme dizini brifingin ızgarasına geçer.

### R29.4 — Özet kutusunun kenar çizgisi kalkar (müşterinin kararı)

PRODUCT.md'nin kanunu olduğu gibi kalıyor: *sınır çizgi alır, durum renk, içerik büyüklük
— asla ikisi birden.* Rev 0'ın L1 tanımı ("dolgu + kenar") bu kanunla çelişiyordu. Karar
kanun lehine: yönetici özeti yalnızca `--paper-2` zeminini taşır, 3px'lik `--brand` sol
kenar kalkar.

Özet kutusu artık tek bir mekanizmayla, zeminiyle ayrılıyor. Rev 0'ın gerekçesi ("yönetici
özeti görsel olarak ayrılmıyordu") zeminle karşılanmaya devam ediyor.

**Tersine dönüş kaydı:** Rev 0 → R29.4. DECISIONS.md › *Reversals* listesine 9. madde
olarak eklenecek: "L1 dolgu + kenar — Rev 0 belirledi, R29.4 kanuna uydurmak için kenarı
kaldırdı."

### Build kuralları — R29

> **L1-DOLGU.** Zemin belirteci taşıyan hiçbir öğe aynı anda `border-left` taşıyamaz.
> **ÇİZGİ-KONTRAST.** Build CSS belirteçlerinden `--rule-2`'nin iki temada da zemine
> karşı oranını hesaplar; <3:1 ise uyarı verilir.
> **TİP-BELİRTECİ.** `font-size:` yalnızca `var(--fs-*)` alabilir.
> Üçü de **(A)** özetinde bir satır, ihlalde **Rev 30** kanalına uyarı.

### Uygulama listesi — Revizyon 29

| # | Dosya | Değişiklik | Kabul (ekran görüntüsü) |
|---|---|---|---|
| R29-P0-1 | `app.css` | Özet kutusunun kenarı kalkar | **(S)** 375 ve 1440: YÖNETİCİ ÖZETİ kutusu zeminli, solda koyu yeşil çizgi yok |
| R29-P1-1 | `app.css` | `--rule-2` ≥3:1 | **(S)** 1440: bölüm başlıklarının üstündeki çizgi açık ve koyu temada seçilebilir. **(A)** ÇİZGİ-KONTRAST satırında iki oran ≥3 |
| R29-P1-2 | `app.js`, `app.css` | F-03/F-14 | **(S)** depolama temiz, ilk ziyaret, 375px: brifingin sonunda bildirim kartı; kart açıkken footer zili görünür |


### Orkestratör notu (23 Eylül)

- **Kapsam P0 + P1:** R29-P0-1, R29-P1-1, R29-P1-2. **Yapılmaz (P2/P3):** F-07 masthead,
  F-13 ölü koruma, R29.2 yazı belirteçleri, F-11 ızgara — ve belirteçlere bağlı
  **TİP-BELİRTECİ** kuralı (belirteçler olmadan her derlemede ateşler).
- **Uygulanan kurallar:** L1-DOLGU (R29-P0-1'i korur) ve ÇİZGİ-KONTRAST (R29-P1-1). **(A)**
  özetinde birer satır; ihlalde `uyari.ekle("L1-DOLGU"/"ÇİZGİ-KONTRAST", "…")`.
- **Tersine dönüş kaydı** (Rev 0 → R29.4) DECISIONS.md'ye ve review loguna orkestratör
  tarafından yazılır; DECISIONS.md'yi düzenleme.
- R29-P1-2 "depolama temiz, ilk ziyaret": sayfa bildirimi service worker/PushManager
  varlığına bağlıysa, yerel çekim aracı (`review/tools/shoot.py`) service worker'ları
  engelliyor — doğrulamayı gerçek tarayıcı bağlamında yap ve bunu notlarda belirt.
