## Revizyon 27 — iplik sayfası: ne oldu, şimdi ne durumda

**Hedef.** İplik sayfası iş 2'nin sorusunu ilk satırda cevaplasın ve okunan güne geri
götürsün.
**Dosyalar.** `build.py` (iplik sayfası, `thread_slug`), `assets/app.js` (daybar
`?g=`), `assets/app.css`.
**Build kuralları.** İPLİK-DURUM · SLUG.

### R27.0 — Tanı

- Günün durum cümlesi iplik sayfasına ulaşmıyor.
- Satırlar bağlantı ama öyle görünmüyor.
- Güne dönüş yok (F-09).
- "4 hareket" yazıyor ama 5 satır var (F-10).
- Slug'lar yarım kelimeyle bitiyor ya da tarih taşıyor.

### R27.1 — Karar

- Başlığın altında en son hareketin durum cümlesi, tarihiyle.
- Her hareket satırı o günün cümlesini taşır.
- İplikte daybar olur, gelinen günü gösterir (`?g=`).
- Açılış satırı ayrı biçimde çizilir: "açıldı" jetonu var, bağlantısı yok.
- Satırlar bağlantı gibi görünür.
- Slug'lar etiketten türer, kelime sınırında kesilir, tarih içermez. Eski adresler
  yönlendirilir.

### Build kuralları — R27

> **İPLİK-DURUM.** Son hareketinde durum cümlesi olan bir ipliğin sayfasında
> `.thread-status` yoksa **Rev 30** kanalına uyarı gider.
> **SLUG.** Slug yarım kelimeyle bitemez ve tarih içeremez. Yönlendirmesi eksik eski
> slug varsa **Rev 30** kanalına uyarı gider.

### Uygulama listesi — Revizyon 27

| # | Dosya | Değişiklik | Kabul (ekran görüntüsü) |
|---|---|---|---|
| R27-P0-1 | `build.py` | Durum satırı + satır cümleleri | **(S)** XM30 ipliği, 375px: başlığın altında "Prototip teslim edildi, şart hâlâ tanımlı değil. · 23 Eylül" |
| R27-P0-2 | `build.py`, `app.js` | Daybar | **(S)** brifingden açılan iplik sayfasının tepesinde "23 Eyl · Çar" daybar'ı |
| R27-P1-1 | `app.css` | Bağlantı görünümü; açılış satırı ayrı | **(S)** 4 satır altı çizili, açılış satırı "AÇILDI" jetonlu ve altı çizili değil |
| R27-P2-1 | `thread_slug` | Slug + yönlendirme | **(S)** eski `…-mut.html` adresi açıldığında adres çubuğunda yeni slug |


### Orkestratör notu (23 Eylül)

- **Kapsam P0 + P1.** **R27-P2-1 (slug + yönlendirme) ve ona bağlı SLUG kuralı bu turda
  yapılmaz** (müşteri: P2 atlanır). Slug'lara ve eski adreslere dokunma. İPLİK-DURUM kuralı
  uygulanır (`uyari.ekle("İPLİK-DURUM", "…")`; Rev 30 kanalı = günün GitHub issue'su).
- İplik sayfaları `izleme/` altında; `build.py` üretir.
