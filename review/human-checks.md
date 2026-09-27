# İnsan kontrolleri — Rev 21–33 + K1–K7

Her maddede: **nerede**, **ne yapılacak**, **ne görülmeli**. Sırayla, birer birer.

## 1. Merge'den önce (sen)

1. **Google Drive → `defintel` → `kaynaklar.json`:** `"ad":"Defense Studies"` girdisini bul; aynı girdideki
   `"dil":"…"` değerini `"dil":"id"` yap. Başka hiçbir şeye dokunma.
   *Görmen gereken:* dosya Drive önizlemesinde hâlâ açılıyor (geçerli JSON). Yedek zaten var:
   `kaynaklar-yedek-2026-09-27.json` (27 Eylül, bu düzenlemeden önce) — onu düzenleme.
2. **Apps Script → `defintel-trigger` → `Code.gs`:**
   (a) 41. satır `res.getContentText());` ile bitiyor; (b) `check()` içinde toplayıcı tetiği
   (`tetikleToplayici_()`) `try { … } catch (e) { … }` içinde; (c) üstteki işlev menüsünden `testToplayici` seç → **Çalıştır**.
   *Görmen gereken:* (a) ve (b) öyle; (c) Yürütme günlüğünde kırmızı hata yok, "Execution completed".
3. **Telefonda yerel site, 10 dakika.** Mac'te terminale yapıştır (telefon aynı Wi-Fi'da olmalı):
   `cd ~/Documents/Projects/defintel-repo && echo "Telefonda aç: http://$(ipconfig getifaddr en0):8000" && python3 -m http.server 8000`
   Çıkan adresi telefonda aç; bitince terminalde Ctrl-C. Bak:
   - **Alarm günü:** `…:8000/reports/2026-09-14.html` — en üstte alarm bandı, altında manşet ve özet, ALARMLAR özetin altında.
     *Görmen gereken:* bandı ilk bakışta fark ediyor musun? Evet/hayır yaz.
   - **Uzunluk sınırları:** GitHub'da `review/verdicts/self-check.md` (dal `rev21-33`) — 10 gerçek özet maddesi ve 110 karaktere kısaltılmış hâlleri.
     *Görmen gereken:* kısaltmalar kabul edilebilir mi; **110 mu, 115 mi** (aşağıda karar 1).
   - **Oyuncular satırı:** `…:8000/reports/2026-09-18.html` ve `…/2026-09-21.html` brifinginde "Oyuncular" satırı.
     *Görmen gereken:* Türk şirketleri (yalnız başlıklarda geçenler) artık bu satırda yok, yalnız brifingde geçenler var; bu sana doğru geliyor mu?
4. **Claude masaüstü → "MKE Uluslararası Pazar İzleme Ajanı (Günlük)" → Instructions:** metnin tamamını kopyala,
   `review/builder-notes/instructions-backup.md` adlı yeni dosyaya ``` işaretleri arasına yapıştır, kaydet.
   *Görmen gereken:* dosyada "en fazla 14 kelime" cümlesi var (bugünkü talimat).
5. **Oku ve karar ver:** `review/verdicts/self-check.md` ve `review/builder-notes/trial-merge.md`.
   Sohbette yaz: aşağıdaki kararlar + **"merge onayı"**.
   *Görmen gereken:* benden "merge günü hazır" mesajı.

## 2. Merge günü (rapor yayımlandıktan sonra)

**Ne zaman:** sabah raporu her gün **06:16** civarı yayımlanıyor; ardından yedek toplama **10:40–11:40**
arasında main'e yazıyor. En güvenli pencere: **aynı gün 12:00–23:00**. Sırayla:

6. **Terminal (merge):**
   `cd ~/Documents/Projects/defintel-repo && cp review/tools/merge_day.sh /tmp/merge_day.sh && bash /tmp/merge_day.sh`
   *Görmen gereken:* `üretilmiş 23 dosyada çakışma → …` (sayı biraz farklı olabilir), `birleşik commit: …`,
   en sonda `TAMAM: main'e alındı`. `DUR:` ile başlayan satır görürsen dur, bana yapıştır. ~3 dk sonra
   sitede 23 Eylül medya takibi "628 başlık" der.
7. **Instructions paneli:** `review/builder-notes/merge-day-prompt.md`'deki bloğu yapıştır (yeri dosyada), kaydet.
   *Görmen gereken:* "en fazla 14 kelime" yerine "Manşet en fazla 65 karakterdir"; 7 yeni cümle.
8. **Drive `kaynaklar.json`:** `review/builder-notes/k6-kaynaklar.md`'deki bul/değiştir adımları (Northrop, Elbit, isteğe bağlı Elbit Systems UK).
   *Görmen gereken:* dosya hâlâ geçerli JSON; yalnız bu girdiler değişmiş.

Bir şey ters giderse: `review/builder-notes/rollback.md`.

## 3. Merge'den sonra

**İlk sabah (merge'den sonraki ilk 06:00–07:30)**

9. **Telefon, GitHub Mobile:** günün `DEFINTEL uyarıları · <tarih>` issue'su (uyarı varsa).
   *Görmen gereken:* **ÇEVİRİ-DEDEKTÖRÜ** "özgün bırakılan" sayısı küçük (≤10). Büyükse bana söyle.
10. **Tarayıcı:** `https://defintel.shadovi.com/data/news/<bugün>-aday.md`
    *Görmen gereken:* ilk bölüm "## Dünkü brifingden sonra gelenler (N)"; Türkçe harfler düzgün.
11. **Telefon, o günün medya takibi → arama:** `Trend`
    *Görmen gereken:* Trend.az'dan savunmayla ilgisiz en az bir başlık, Türkçe.
12. **Telefon, o günün brifingi, Tarama satırının altı.**
    *Görmen gereken:* Northrop "okunamadı" satırında yok; Elbit de yoksa ikisi de onarıldı.

**Sonraki 3 rapor**

13. **GitHub Mobile / Issues:** o günlerin uyarı issue'ları.
    *Görmen gereken:* **KUR** ve **H1-TEKRAR** yok; **İLK-EKRAN** yok ya da seyrek. Aynı gün için **tek** issue.

**Sonraki 5 rapor**

14. **Telefon, brifing özeti:** "ilk: <gün>" jetonu taşıyan maddeler.
    *Görmen gereken:* her birinin ilk cümlesinde yenilik fiili ("resmîleşti", "sözleşmeye döndü" gibi).

**Yeniden çeviri — yalnız yeni bir oturumda ve senin onayınla**

15. **Sohbet (yeni oturum):** "yeniden çeviri denemesi" yaz. Bir gün yerelde yeniden çevrilir, 20 başlıklık
    önce/sonra tablosu gösterilir; senin "devam" onayın olmadan hiçbir çeviri yayımlanmaz.

## Senin kararın gereken konular

1. **Özet maddesi sınırı:** 110'da kalsın mı, 115 mi olsun? (self-check: 110'da 10 maddenin 3'ü kilit bilgi kaybediyor; 115'te 1'i, ilk ekran 10 günün hepsinde geçiyor ama 20 Eylül'de yalnız 3px payla; 120 ve üstü ilk ekranı bozuyor.)
2. **K5-2 ölçütü:** bağımsız kontrol yeniden yazılmış ölçütü "daha zayıf" buldu. Kabul mü, yoksa K5 ancak merge'den sonra ilk alarm günü gerçek sayfada geçince mi kapansın?
3. **Ortak kilit:** collect-news ve pull-drive eskiden ortak bir kilit paylaşıyordu; senin "iş akışı başına bir grup" kararınla ayrıldı. Artık ikisi aynı anda koşabilir: nadiren push çakışması (rapor gecikir, kaybolmaz) ya da aynı gün iki uyarı issue'su. Böyle mi kalsın, ortak kilit geri mi gelsin?
4. **24–27 Eylül kategorileri:** eski toplayıcıyla toplandılar (eski kategoriler, 17–22 gibi). 23 Eylül gibi yeniden kategorilensin mi, yoksa kalsın mı?
5. **23 Eylül yinelenen başlık:** geri gelen Euro-SD "FQ-42 Vengeance…" ile mevcut Armada kalemi aynı başlık. A gereği tutuldu (628). Kalsın mı, düşsün mü (627)?
