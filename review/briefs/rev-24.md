## Revizyon 24 — yöneticinin ilk ekranı

**Hedef.** Telefonda yöneticinin ilk ekranında özet olsun, üstveri değil.
**Dosyalar.** `assets/app.css`, `build.py` (tablo kartı), `scripts/check_reports.py`.
**Build kuralı.** İLK-EKRAN.

### R24.0 — Tanı

375×812'de ilk 470 piksel içerikten önce geliyor (F-15). İlk ekrana 5 özet maddesinden
2'si sığıyor. Ray tek sütunda özetin üstüne yığılıyor. Rev 6: **dönüş kromu değiştirir,
metin bloğunu asla.**

### R24.1 — Karar

- 920px'in altında ray, özetin arkasına (Portföy'den önce) taşınır.
- Çip şeridi tek satıra iner, taşarsa yatay kaydırılır. Yapışkan değildir.
- Mobil kartın üçüncü alanı "İzlenecek" etiketini taşır.

### Build kuralı — İLK-EKRAN

> `check_reports.py` 375×812'de brifingi açar ve **(A)** özetine ekran görüntüsünü ekler.
> `h2#yonetici-ozeti` üst kenarı ≤300px ve özetin 4. maddesinin alt kenarı ≤812px
> olmalı. Olmazsa **Rev 30** kanalına uyarı gider.

### Uygulama listesi — Revizyon 24

| # | Dosya | Değişiklik | Kabul (ekran görüntüsü) |
|---|---|---|---|
| R24-P0-1 | `assets/app.css` | Ray `order` ile özetin arkasına | **(S)** 375×812: ilk ekranda YÖNETİCİ ÖZETİ başlığı ve en az 4 madde; Oyuncular ilk ekranda yok. **(S)** 1440: ray solda, yerinde |
| R24-P0-2 | `assets/app.css` | Çipler tek satır | **(S)** 375px: çipler tek satırda |
| R24-P1-1 | `assets/app.css`, `build.py` | Kart etiketi | **(S)** 375px: her kartın üçüncü alanının üstünde "İZLENECEK" |
| R24-P1-2 | `check_reports.py` | İLK-EKRAN | **(A)** 375×812 görüntüsü; ray bilerek geri taşındığında **(P)** uyarı |

**Yapılmayacak:** rayı mobilde gizlemek; üçüncü bir yapışkan katman eklemek.

---

### Orkestratör notu (23 Eylül)

- **Rev 30 kanalı:** `uyari.ekle("İLK-EKRAN", "…")`; **(P)** → **(I)** (issue satırı). `main` dışındaki
  dallarda issue ancak `UYARI_TEST_ONEK` ayarlıysa açılır.
- **"Ray bilerek geri taşındığında" kanıtı:** kodu bozmadan, `build.yml`'deki mevcut dispatch
  kalıbıyla (`boz`, `kapsam_boz`, `noktali_boz`, `uyari_test`) yeni bir girdi (ör. `ilk_ekran_boz:
  true`) ray sırasını yalnız o çalıştırmanın tarayıcısında geri alır, `UYARI_TEST_ONEK: "[TEST] "`
  açar ve dala commit/push etmez. **(A)** özetinde 375×812 görüntüsü (artifact bağlantısı, Rev 22
  kalıbı) ve ölçülen iki kenar değeri.
- DÖRT-DURUM ve `--oyuncular` denetimleri de 375px'te koşuyor; ray taşıması onları bozmamalı.
