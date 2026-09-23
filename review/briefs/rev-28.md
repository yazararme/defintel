## Revizyon 28 — izlenen oyuncunun kaynağı düştüğünde

**Hedef.** İnanç değiştiren tek arıza okuyucuya tek satırla söylensin. Başka hiçbir
arıza söylenmesin.
**Dosyalar.** `data/rakipler.json` (`kaynak` alanı), `build.py` (brifing rayı, Kaynaklar
sayfası).
**Build kuralı.** KANIT-BOŞLUĞU.

### R28.0 — Tanı

23 Eylül'de Elbit ve Northrop'un kendi kaynakları yanıt vermedi (F-04). Bu bilgi
yalnızca Kaynaklar sayfasında soluk bir satırdı.

### R28.1 — Karar

- Her oyuncunun `kaynak` alanı olur.
- Kesişim boş değilse Tarama satırının altında tek satır: *"Elbit Systems ve Northrop
  Grumman'ın kendi duyuruları bugün okunamadı."* Satırda neden, sayı ya da renk yok.
- Kesişim boşsa satır basılmaz (Rev 9: alışkanlığın kırılması sinyalin kendisidir).
- Kaynaklar sayfasındaki "yanıt vermedi" sütunu kalkar; satır soluk kalır (Rev 19).

### Build kuralı — KANIT-BOŞLUĞU

> Satırın tek tetiği `failed_sources ∩ {r.kaynak}` kesişimi. Ajanın beyanı tetik olamaz
> (Rev 14). Satır basıldığı gün **Rev 30** kanalına da bildirim gider: operatörün kaynağı
> onarması gerekebilir.

### Uygulama listesi — Revizyon 28

| # | Dosya | Değişiklik | Kabul (ekran görüntüsü) |
|---|---|---|---|
| R28-P0-1 | `rakipler.json` | `kaynak` alanı | **(S)** /haberler/…-kaynaklar.html: Elbit ve Northrop satırlarının yanında adları |
| R28-P0-2 | `build.py` | KANIT-BOŞLUĞU satırı | **(S)** 23 Eylül yeniden derlendi, 375px: Tarama altında iki adlı tek satır; kesişimi boş bir günde satır yok. **(P)** o gün bildirim |
| R28-P1-1 | `build.py` | Sütun kalkar | **(S)** Kaynaklar sayfasında "yanıt vermedi" yazısı yok |


### Orkestratör notu (23 Eylül)

- **Rev 30 kanalı:** `uyari.ekle("KANIT-BOŞLUĞU", "…")`; **(P)** → **(I)** (issue satırı). `main`
  dışındaki dallarda issue ancak `UYARI_TEST_ONEK` ayarlıysa açılır; 23 Eylül'ün gerçek
  bildirimini dalda görmek için mevcut `uyari_test` dispatch girdisi kullanılır.
- `data/rakipler.json` Rev 21'de alias'larla genişledi; `kaynak` alanını mevcut yapıya ekle,
  alias testlerini (64/64) bozma.
- Brifing sayfası ilk ekranı Rev 24'ün İLK-EKRAN kuralına tabi (375×812'de özet başlığı
  ≤300px, 4. madde ≤812px, CI'da da). Tarama altına eklenen satır bunu bozmamalı; CI'ın
  satır kırılımı yereldekinden farklı (bkz. `review/builder-notes/rev-32.md`, deneme 2).
