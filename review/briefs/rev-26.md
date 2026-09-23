## Revizyon 26 — çeviri: cümle düzeni ve üç dedektör

**Hedef.** Başlıklar tek düzende olsun ve hiçbir başlık bir önermesini ya da konuşanını
sessizce kaybetmesin.
**Dosyalar.** `scripts/translate_news.py` (prompt, sözlük, dedektörler), Drive'daki
`kaynaklar.json` (`dil` düzeltmesi; müşteri yapar).
**Build kuralı.** ÇEVİRİ-DEDEKTÖRÜ.

### R26.0 — Tanı

İki prompt kuralı çelişiyor: "Türkçeyse aynen ver" ve "her kelime büyük". En tehlikeli
kusur sınıfı sessiz eksiltme ve atıf silme.

### R26.1 — Karar: cümle düzeni

- `translate_news.py:48` cümle düzenine döner. Çelişki böylece kalkar.
- **Ö5 tersine döner:** her kelimesi büyük harfle çıkan bir çeviri kusur işareti sayılır.
- **Ö1** (önerme koruma) ve **Ö2** (atıf koruma) prompt'a eklenir.
- **Ö3** sözlük eklemeleri yapılır.
- **Ö6 ucuz yarısı:** "Defense Studies" için `dil: "id"` Drive'da düzeltilir.
- **Geçiş:** canlı pencere yeniden çevrilir. Arşivdeki günler eski düzende kalır. Rev 4:
  tekdüzelik blok içinde zorunludur, sayfalar arasında değil.

### Build kuralı — ÇEVİRİ-DEDEKTÖRÜ

> Her çıktı yayımlanmadan önce üç sınamadan geçer: **düzen** (muaf olmayan kelimelerin
> >%60'ı büyük harfle başlıyor), **uzunluk** (çeviri < özgün × 0,6), **atıf** (özgünde
> says/according to var, çeviride dedi/göre/: yok). Biri tutarsa kalem bir kez yeniden
> çevrilir. İkinci deneme de tutarsa özgün başlık basılır.
> **(A)** özetine sınama başına yakalanan sayısı ve content.md §2'nin 16 kusurlu kalemiyle
> koşan sabit testin sonucu yazılır. Bir günde özgün bırakılan başlık sayısı >10 ise
> **Rev 30** kanalına uyarı gider.

### Uygulama listesi — Revizyon 26

| # | Dosya | Değişiklik | Kabul (ekran görüntüsü) |
|---|---|---|---|
| R26-P0-1 | `translate_news.py` | Cümle düzeni, Ö1, Ö2 | **(S)** medya takibi, 1440px, Öne çıkanlar: 12 satırın hepsi cümle düzeninde |
| R26-P0-2 | `translate_news.py` | ÇEVİRİ-DEDEKTÖRÜ | **(A)** sabit testte 16 kalemden en az 7'si yakalanmış; "…exiting power procurement" satırının yeniden çevirisi "çekil" kökünü içeriyor |
| R26-P1-1 | sözlük | Ö3 | **(S)** medya takibinde "Hürmüz" araması "Hürmüz Boğazı" gösterir, "Hormuç" göstermez |
| R26-P1-2 | `translate_news.py` | Canlı pencere yeniden çevrilir | **(S)** 23 ve 24 Eylül medya sayfalarının her birinde tek düzen |
| R26-P1-3 | Drive `kaynaklar.json` | Ö6 ucuz yarısı | **(S)** "KF-21 Berbagi dengan F-16V?" satırının çevirisinde KF-21 özne |


### Orkestratör notu (23 Eylül)

- **Kapsam P0 + P1.** P2 (Ö6 tamamı) ve P3 (Ö7) yapılmaz.
- **Model çağrısı yok.** Çeviri `claude -p` çağırır (abonelik kotası) ve yayımlanan veriyi
  yeniden yazar; bu turda buna izin yok (müşteri kararı gerekiyor → "Açık"). Bu yüzden:
  - **Yapılır:** `translate_news.py` promptunun cümle düzenine dönmesi, Ö1/Ö2 prompt
    eklemeleri, Ö3 sözlük eklemeleri, ÇEVİRİ-DEDEKTÖRÜ'nün üç sınaması + "bir kez yeniden
    çevir, yine tutarsa özgünü bas" akışı (model çağrısı enjekte edilebilir bir fonksiyon
    olsun ki testte sahte çevirmen kullanılabilsin), günde >10 özgün bırakılan → `uyari.ekle`.
  - **Sabit test (R26-P0-2'nin ilk yarısı):** content.md §2'deki 16 kusurlu kalem (yalnız
    `audit/content.md` §2'yi oku) — dedektörler **mevcut kusurlu çevirilere** çevrimdışı
    uygulanır; yakalanan sayısı **(A)** özetine yazılır (build.yml ya da ayrı bir sınama iş
    akışı; sır yok, ağ yok).
  - **Yapılmaz, "Açık"a:** canlı pencerenin yeniden çevrilmesi (R26-P1-2), "…exiting power
    procurement" satırının gerçek yeniden çevirisi (R26-P0-2 ikinci yarısı), ve bunlara
    dayanan R26-P0-1 / R26-P1-1 (S) görünümü — veri yeniden çevrilmeden sayfa değişmez.
    Mevcut `data/news/*.json` çevirilerine **dokunma**.
  - **R26-P1-3 (Drive `kaynaklar.json`, `dil` düzeltmesi)** müşteri yapar → human-checks.
