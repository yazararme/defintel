## Revizyon 32 — tekrar eden manşet

**Hedef.** Önceki bir raporda verilmiş bir gelişme yeni diye sunulmasın; tekrar
geliyorsa neyin yeni olduğunu söyleyerek gelsin.
**Dosyalar.** `build.py` (karşılaştırma, özet maddesi jetonu), rapor promptu, `assets/app.css`.
**Build kuralı.** TEKRAR-MANŞET.

### R32.0 — Tanı

19 Eylül'ün H1'i: *"Letonya imzalı Archer niyet mektubunu bozup … Çek Morana'ya geçti"*.
23 Eylül'ün H1'i ve özetin 1. maddesi: *"Letonya … Archer'ı bırakıp Çek Morana'yı
seçti"*. Dört gün sonra aynı karar yeniden günün manşeti oldu. Yeni olan tek şey
bakanlığın 22 Eylül tarihli resmî açıklamasıydı, ama bu cümlenin hiçbir yerinde yazmıyor.
Dört dakikası olan okuyucu aynı haberi iki kez yeni diye okuyor. Bu, Rev 16'nın "tek
anlatı evi" ilkesinin günler arasına uzanan hâli.

### R32.1 — Karar

- **Prompt:** *"Önceki 7 raporda anlatılmış bir gelişme manşete ya da özete ancak neyin
  yeni olduğunu ilk cümlesinde söyleyerek girer ('resmîleşti', 'sözleşmeye döndü',
  'bedel açıklandı')."*
- **Build, geriye doğru bağlantıyı kendisi türetir.** Önceki 7 raporun herhangi bir
  gelişmesiyle eşleşen bir özet maddesi, sonunda mono bir jeton taşır: **"ilk: 19 Eyl"**.
  Jeton o raporun ilgili gelişmesine bağlanır. Rev 6'nın kuralına uyuyor: atıf tek yönlü,
  eskiye doğru, ve Rev 11'e göre bir kimlikten ibaret değil, tarih taşıyor. Rev 10'a da
  uyuyor: ajan değil build türetiyor.
- **Eşleşme:** paylaşılan `[K#]` URL'si, **ya da** en az iki ortak özel ad (büyük harfle
  başlayan, sözlükte olmayan kelimeler) artı sözcük örtüşmesi ≥0,4.

### Build kuralı — TEKRAR-MANŞET

> H1 ya da bir özet maddesi önceki 7 günle eşleşirse "ilk: {gün}" jetonu basılır. Eşleşen
> H1 için **Rev 30** kanalına uyarı gider: *"TEKRAR-MANŞET: 23 Eyl H1 ↔ 19 Eyl"*. Jeton
> sayfaya basılır, çünkü okuyucu için anlamı olan bir olgu. Uyarı operatöre gider, çünkü
> promptun tutmadığını gösteriyor.

### Uygulama listesi — Revizyon 32

| # | Dosya | Değişiklik | Kabul (ekran görüntüsü) |
|---|---|---|---|
| R32-P0-1 | `build.py`, `app.css` | "ilk:" jetonu | **(S)** 23 Eylül yeniden derlendi, 375px: özetin 1. maddesinin sonunda "ilk: 19 Eyl"; dokunulunca 19 Eylül raporunun Letonya gelişmesi açılıyor |
| R32-P0-2 | `build.py` | TEKRAR-MANŞET uyarısı | **(P)** "TEKRAR-MANŞET: 23 Eyl H1 ↔ 19 Eyl" |
| R32-P1-1 | rapor promptu | Yenilik cümlesi | Sonraki 5 raporda jetonlu her maddenin ilk cümlesinde bir yenilik fiili var (**(S)** özet görüntüsünden okunur) |

**Yapılmayacak:**
- Tekrar eden maddeyi build'in silmesi. Madde ajanın yargısı; build yalnızca bağlamı
  ekler.
- Eşiği URL eşleşmesine indirgemek. 19 ve 23 Eylül farklı kaynaklara atıf veriyor.

---

### Orkestratör notu (23 Eylül)

- **Rev 30 kanalı:** `uyari.ekle("TEKRAR-MANŞET", "…")`; **(P)** → **(I)** (issue satırı). `main`
  dışındaki dallarda issue ancak `UYARI_TEST_ONEK` ayarlıysa açılır; 23 Eylül'ün gerçek
  uyarısını dalda görmek için mevcut `uyari_test` dispatch girdisi kullanılır (kodu bozmaya
  gerek yok).
- **R32-P1-1 (prompt):** Rev 23'teki gibi, cümleyi müşterinin görev talimatına yapıştıracağı
  hâliyle `review/builder-notes/rev-32-prompt.md`'ye yaz (Rev 23'ün
  `rev-23-prompt.md`'siyle aynı bloğa eklenecek şekilde). "Sonraki 5 rapor" zamana bağlı;
  inceleyici PENDING-HUMAN sayar.
