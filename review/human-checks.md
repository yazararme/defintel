# İnsan kontrolleri — Rev 21–33

Bir oturuşta yapılacak liste. Her maddede: nerede, ne yapılacak, ne görülmeli.

## Rev 23 — rapor promptu (R23-P0-2)

1. **Claude masaüstü uygulaması → "MKE Uluslararası Pazar İzleme Ajanı (Günlük)" görevi → Instructions paneli.**
   `review/builder-notes/rev-23-prompt.md` dosyasındaki üç cümleyi orada tarif edilen yere yapıştır, kaydet.
   *Görmen gereken:* panelde üç cümle (kur, H1, özne).
2. **Sonraki 3 raporun sabahı (dal main'e alındıktan sonra), GitHub Mobile / Issues.**
   O günlerin `DEFINTEL uyarıları · <tarih>` issue'sunda **KUR** ve **H1-TEKRAR** satırı olmamalı.
   *Görmen gereken:* üç gün boyunca bu iki kural adı yok (issue hiç açılmamışsa da geçer).

## Rev 31 — ertesi günün aday dosyası (R31-P0-3, canlı)

3. **Dal main'e alındıktan sonraki ilk sabah, tarayıcı:** `https://defintel.shadovi.com/data/news/<o gün>-aday.md`
   *Görmen gereken:* dosyanın ilk bölümü "## Dünkü brifingden sonra gelenler (N)"; Türkçe harfler düzgün.

## Rev 32 — yenilik cümlesi (R32-P1-1)

4. **Aynı Instructions paneli (1. maddeyle aynı oturuşta):** `review/builder-notes/rev-32-prompt.md`'deki cümleyi Rev 23 cümlelerinin yanına yapıştır.
   *Görmen gereken:* panelde yenilik cümlesi ("…neyin yeni olduğunu ilk cümlesinde söyleyerek girer").
5. **Sonraki 5 rapor, sitede brifing sayfası:** özet maddelerinde "ilk: <gün>" jetonu olan her maddenin ilk cümlesinde bir yenilik fiili ("resmîleşti", "sözleşmeye döndü", "bedel açıklandı" gibi).
   *Görmen gereken:* jetonlu hiçbir madde eski haberi yeni gibi anlatmıyor.

## Rev 25 — süzgeç artık düşürmüyor (R25-P0-1, canlı)

6. **Dal main'e alındıktan sonraki ilk sabah, telefon ya da tarayıcı:** o günün medya takibi sayfası → arama kutusuna `Trend` yaz.
   *Görmen gereken:* Trend.az'dan savunmayla ilgisiz en az bir başlık (ör. ekonomi/pamuk), Genel'in tam dökümünde, Türkçe başlıkla.

## Rev 26 — çeviri (R26-P1-3 ve canlı geçiş)

7. **Google Drive → `defintel` klasörü → `kaynaklar.json`:** "Defense Studies" kaynağının `dil` değerini `"id"` yap, kaydet.
   *Görmen gereken:* dosyada o satırda `"dil": "id"`.
8. **Dal main'e alındıktan sonraki ilk sabah, GitHub Mobile / Issues:** o günün `DEFINTEL uyarıları · <tarih>` issue'su.
   *Görmen gereken:* **ÇEVİRİ-DEDEKTÖRÜ** satırı ya hiç yok ya da "özgün bırakılan" sayısı küçük. Büyükse (ör. 30) model yeni cümle düzeni promptuna uymuyor demektir — bana söyle.

## main'e almadan önce (bir kez)

9. **Karar ver:** `review/progress.md` › "Açık" bölümündeki maddeler (özellikle 7: canlı pencere yeniden çevrilsin mi).
10. **Sınama iş akışları:** `.github/workflows/uyari-test.yml`, `gec-gelen-test.yml`, `silme-yok-test.yml`, `ceviri-dedektoru-test.yml` yalnız `rev21-33` dalında tetiklenir; main'e alınmadan silinsin mi, kalsın mı — bana söyle, ben silerim.
11. **Test issue'su:** https://github.com/yazararme/defintel/issues/5 (`[TEST]` önekli) — kapatabilirsin.
