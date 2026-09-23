# İnsan kontrolleri — Rev 21–33 + K1–K6

Her maddede: **nerede**, **ne yapılacak**, **ne görülmeli**. Bitenler çıkarıldı.

## 1. Merge'den önce

1. **Sohbet:** K4 için seçimini yaz — **A** (92 kalem etiketsiz geri gelir), **B** (doğru başka etiketle),
   **C** (yine de BRİFİNGDEN SONRA). K4 bu cevap gelmeden yapılmıyor.
   *Görmen gereken:* benden "K4 PASS" mesajı.

## 2. Merge günü (bir sabah çalıştırmasından hemen sonra — rapor yayımlandıktan sonra, ertesi 05:00'ten önce)

2. **Terminal:** `cd ~/Documents/Projects/defintel-repo && git switch main && git pull && git merge --no-ff rev21-33 && git push`
   *Görmen gereken:* `Merge made by the 'ort' strategy` ve push özeti; ~3 dk sonra site yeni hâliyle açılır
   (brifingde "brifingde geçen" etiketi, alarm günü bandı en üstte).
3. **Claude masaüstü → "MKE Uluslararası Pazar İzleme Ajanı (Günlük)" → Instructions paneli:**
   `review/builder-notes/merge-day-prompt.md`'deki bloğu yapıştır (yeri dosyada), kaydet.
   *Görmen gereken:* panelde 7 yeni cümle; "en fazla 14 kelime" kuralının yerinde "Manşet en fazla 65 karakterdir".
4. **Google Drive → `defintel` → `kaynaklar.json`:** `review/builder-notes/k6-kaynaklar.md`'deki bul/değiştir
   adımlarını uygula (Northrop'a istek başlığı; Elbit Systems'i `/news` sayfasına çevir; isteğe bağlı Elbit Systems UK satırı).
   *Görmen gereken:* dosya hâlâ geçerli JSON (Drive önizlemesi açılıyor); yalnız bu girdiler değişmiş.

## 3. Merge'den sonra

**İlk sabah (merge'den sonraki ilk 06:00–07:30 arası)**

5. **Telefon, GitHub Mobile:** günün `DEFINTEL uyarıları · <tarih>` issue'su bildirimi (uyarı varsa).
   *Görmen gereken:* bildirim geldi; issue'da **ÇEVİRİ-DEDEKTÖRÜ** "özgün bırakılan" sayısı küçük (≤10). Büyükse bana söyle.
6. **Tarayıcı:** `https://defintel.shadovi.com/data/news/<bugün>-aday.md`
   *Görmen gereken:* ilk bölüm "## Dünkü brifingden sonra gelenler (N)"; Türkçe harfler düzgün.
7. **Telefon, o günün medya takibi sayfası → arama:** `Trend`
   *Görmen gereken:* Trend.az'dan savunmayla ilgisiz en az bir başlık, Türkçe.
8. **Telefon, o günün brifingi:** Tarama satırının altı.
   *Görmen gereken:* Northrop artık "okunamadı" satırında yok. Elbit de yoksa iki onarım tuttu; satır hiç yoksa ikisi de tuttu.

**Sonraki 3 rapor**

9. **GitHub Mobile / Issues:** o günlerin uyarı issue'ları.
    *Görmen gereken:* **KUR** ve **H1-TEKRAR** satırı yok; **İLK-EKRAN** satırı yok ya da seyrek.

**Sonraki 5 rapor**

10. **Telefon, brifing özeti:** "ilk: <gün>" jetonu taşıyan maddeler.
    *Görmen gereken:* her birinin ilk cümlesinde yenilik fiili ("resmîleşti", "sözleşmeye döndü", "bedel açıklandı" gibi).

**Yeniden çeviri denemesi (merge'den sonra, sen "başla" deyince)**

11. **Sohbet:** "yeniden çeviri denemesi" yaz. Ben bir günü yerelde yeni promptla yeniden çeviririm ve 20 başlıklık
    önce/sonra örneği gösteririm; senin "devam" onayın olmadan hiçbir çeviri yayımlanmaz.
    *Görmen gereken:* 20 satırlık tablo (özgün · eski çeviri · yeni çeviri), cümle düzeninde.
