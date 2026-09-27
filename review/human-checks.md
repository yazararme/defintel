# İnsan kontrolleri — Rev 21–33 + K1–K9

Her maddede: **nerede**, **ne yapılacak**, **ne görülmeli**. Sırayla, birer birer.

## 0. Tamamlananlar (27 Eylül gece)

- Drive `kaynaklar.json`: "Defense Studies" → `"dil":"id"` yapıldı; dosya geçerli JSON, yalnız bu alan değişti
  (bayt bayt doğrulandı). Önceki hâl: `kaynaklar-onceki-2026-09-27.json` ve `kaynaklar-yedek-2026-09-27.json`.
- Apps Script `defintel-trigger`: (a) atış satırı (42. satır) `res.getContentText());` ile bitiyor;
  (b) `check()` içinde `tetikleToplayici_()` 16. satırda `try { … } catch (e) { … }` içinde. Değişiklik gerekmedi,
  kaydedilmedi. `testToplayici` **çalıştırılmadı**: kaydetme olmadı, ve çalıştırmak main'e gerçek bir toplama
  (çeviri dahil) commit'letir. Tetikleyicinin çalıştığını her sabah 05:01 civarındaki collect-news çalıştırması gösteriyor.
- Instructions paneli yedeği: `review/builder-notes/instructions-backup.md`.

## 1. Merge'den önce (sen)

1. **Karar — manşet sınırı: 65 mi, 75 mi?** Oku: `review/verdicts/headline-check.md`.
   65'te son 10 günün en uzun 10 manşetinden 1'i kilit bilgi kaybediyor (20 Eyl "5,56 mm"); 75'te hiçbiri.
   Ama 75'te 20 Eylül ilk ekranı CI en kötü hâlinde 840px ile aşıyor (sınır 812); 65'te 10 günün hepsi geçiyor.
   *Görmen gereken:* sohbette "65" ya da "75" yaz.
2. **Telefonda yerel site, 10 dakika.**
   - Mac'te Terminal'e yapıştır (telefon ve Mac aynı Wi-Fi'da):
     `cd ~/Documents/Projects/defintel-repo && echo "Telefonda aç: http://$(ipconfig getifaddr en0):8000" && python3 -m http.server 8000`
   - macOS "gelen bağlantılara izin ver" sorarsa **İzin Ver**.
   - Terminalde çıkan adresi telefonun tarayıcısında aç. Bitince terminalde Ctrl-C.
   Üç şeye bak:
   - **Alarm günü:** `…:8000/reports/2026-09-14.html` — en üstte alarm bandı, altında manşet ve özet, ALARMLAR özetin altında.
     *Görmen gereken:* bandı ilk bakışta fark ediyor musun? (evet/hayır)
   - **Oyuncular satırı:** `…:8000/reports/2026-09-18.html` ve `…/2026-09-21.html`, brifingdeki "Oyuncular" satırı.
     *Görmen gereken:* yalnız brifingde geçen şirketler var; yalnız başlıklarda geçen Türk şirketleri artık bu satırda değil. Doğru geliyor mu?
   - **23 Eylül medya takibi:** `…:8000/haberler/2026-09-23.html`.
     *Görmen gereken:* "627 başlık"; aramaya `Divyastra` yaz → 1 sonuç.
3. **Oku ve onay ver:** `review/builder-notes/trial-merge.md`, `review/builder-notes/smoke-date-independent.md`.
   *Görmen gereken:* sohbette "merge onayı" yazarsın; ben "merge günü hazır" derim.

## 2. Merge günü (rapor yayımlandıktan sonra)

**Ne zaman:** rapor her gün **06:16** civarı yayımlanıyor; yedek toplama **10:40–11:40** arası main'e yazıyor.
Pencere: **aynı gün 12:00–23:00**. Sırayla:

4. **Terminal (merge):**
   `cd ~/Documents/Projects/defintel-repo && cp review/tools/merge_day.sh /tmp/merge_day.sh && bash /tmp/merge_day.sh`
   *Görmen gereken:* `üretilmiş … dosyada çakışma → …`, `birleşik commit: …`, en sonda `TAMAM: main'e alındı`.
   `DUR:` ile başlayan satır görürsen dur, bana yapıştır. ~3 dk sonra 23 Eylül medya takibi "627 başlık" der.
5. **Instructions paneli:** `review/builder-notes/merge-day-prompt.md`'deki 7 cümlelik blok, 3. bölümde
   **"Teslimden önce kalite kontrolü."** paragrafının hemen üstüne, **"Ek kurallar (Eylül 2026)."** başlığıyla. Kaydet.
   (Manşet kararın 75 olursa bloktaki "65" bu tarihten önce güncellenmiş olur.)
   *Görmen gereken:* panelde yeni başlık ve altında 7 cümle; başka satır değişmemiş.
6. **Drive `kaynaklar.json`:** `review/builder-notes/k6-kaynaklar.md`'deki bul/değiştir (Northrop, Elbit, isteğe bağlı Elbit Systems UK).
   *Görmen gereken:* dosya hâlâ geçerli JSON; yalnız bu girdiler değişmiş.

Bir şey ters giderse: `review/builder-notes/rollback.md`.

## 3. Merge'den sonra

Not: yeni kategoriler **merge gününden itibaren** toplanan günlere uygulanır; 24–27 Eylül toplandığı gibi (eski kategoriler) kalır.

**İlk sabah (merge'den sonraki ilk 06:00–07:30)**

7. **Telefon, GitHub Mobile:** günün `DEFINTEL uyarıları · <tarih>` issue'su (uyarı varsa).
   *Görmen gereken:* **ÇEVİRİ-DEDEKTÖRÜ** "özgün bırakılan" sayısı küçük (≤10). Büyükse bana söyle.
8. **Tarayıcı:** `https://defintel.shadovi.com/data/news/<bugün>-aday.md`
   *Görmen gereken:* ilk bölüm "## Dünkü brifingden sonra gelenler (N)"; Türkçe harfler düzgün.
9. **Telefon, o günün medya takibi → arama:** `Trend`
   *Görmen gereken:* Trend.az'dan savunmayla ilgisiz en az bir başlık, Türkçe.
10. **Telefon, o günün brifingi, Tarama satırının altı.**
    *Görmen gereken:* Northrop "okunamadı" satırında yok; Elbit de yoksa ikisi de onarıldı.

**Sonraki 3 rapor**

11. **GitHub Mobile / Issues:** o günlerin uyarı issue'ları.
    *Görmen gereken:* **KUR** ve **H1-TEKRAR** yok; **İLK-EKRAN** yok ya da seyrek; aynı gün için **tek** issue.

**Sonraki 5 rapor**

12. **Telefon, brifing özeti:** "ilk: <gün>" jetonu taşıyan maddeler.
    *Görmen gereken:* her birinin ilk cümlesinde yenilik fiili ("resmîleşti", "sözleşmeye döndü" gibi).

**İlk gerçek alarm günü (K5 açık — bu kontrol kapatır)**

13. **Telefon (375 genişlik), o günün brifingi:** ilk ekran, kaydırmadan.
    *Görmen gereken:* en üstte alarm bandı; altında manşet, "Yönetici özeti" başlığı ve özetin ilk 4 maddesi ekranda.
    Aynı gün uyarı issue'sunda **İLK-EKRAN** satırı yok. İkisi de tamamsa "K5 kapandı" yaz; değilse ekran görüntüsü gönder.

**Yeniden çeviri — yalnız yeni bir oturumda ve senin onayınla**

14. **Sohbet (yeni oturum):** "yeniden çeviri denemesi" yaz. Bir gün yerelde yeniden çevrilir, 20 başlıklık
    önce/sonra tablosu gösterilir; senin "devam" onayın olmadan hiçbir çeviri yayımlanmaz.
