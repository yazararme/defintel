# Geri alma planı — rev21-33 merge'ü

Üç şey ayrı ayrı geri alınır: **site/kod** (git), **görev talimatı** (Instructions paneli),
**kaynak listesi** (Drive `kaynaklar.json`). Hangisi sorunluysa yalnız onu geri al; üçü birbirine
bağlı değil. Emin değilsen üçünü de bu sırayla geri al.

## 1 · Site ve kod (merge'ü geri al)

Terminalde, tek satır olarak yapıştır:

```
cd ~/Documents/Projects/defintel-repo && cp review/tools/rollback.sh /tmp/rollback.sh && bash /tmp/rollback.sh
```

**Görmen gereken:** `geri alınacak: <kod> Merge rev21-33 into main …` ve en sonda
`TAMAM: merge geri alındı → <kod>`. Satır `DUR:` ile başlarsa hiçbir şey değişmemiştir; satırı bana
yapıştır. `push reddedildi` görürsen (o sırada bir sabah çalıştırması main'e yazmıştır) birkaç dakika
sonra aynı satırı yeniden yapıştır.

Betik ne yapar: main'deki merge commit'ini bulur ve tersine çevirir; merge'den sonra sabah
çalıştırmalarının yeniden yazdığı üretilmiş sayfalarda çakışma olursa merge öncesi hâli alır ve
sayfaları eski `build.py` ile yeniden üretir; başka bir dosyada çakışma olursa dokunmadan durur.
27 Eylül'de, merge + sonraki bir gün benzetimiyle push'suz denendi.

- **Site ne zaman eski hâline döner:** push'tan yaklaşık **1–3 dakika** sonra (GitHub Pages yayını;
  son haftada 30–60 sn sürdü). Telefonda uygulama eski sayfayı önbellekten gösterebilir: sayfayı iki kez
  yenile ya da uygulamayı kapatıp aç.
- **Ne kaybolmaz:** merge'den sonra gelen günlük raporlar ve haber verileri (`report:` / `news:`
  commit'leri) yerinde kalır; geri alma yalnız dalın getirdiği değişiklikleri çıkarır.
- **Ne geri gider:** dalın getirdiği her şey — alarm düzeni, uyarı issue'ları, 23 Eylül'ün geri gelen
  92 başlığı (sayfa yine 536 der), Elbit/Northrop ayrıştırıcısı. Sabah hattı merge öncesi gibi çalışır.
- **Bilinen yan etki:** merge'den sonra toplanan günlerin veri dosyalarında yeni alanlar (ör. "ilk
  görüldü" damgası) kalır; eski kod bunları okumaz, zararı yok.
- **Sonra yeniden almak istersen:** doğrudan `git merge rev21-33` **çalışmaz** (git onu zaten alınmış
  sayar). Bana "merge'ü yeniden al" yaz; "geri almayı geri al" adımıyla yaparım.

## 2 · Görev talimatı (Instructions paneli)

Merge'den önce panelin metnini `review/builder-notes/instructions-backup.md`'ye kopyalamış olacaksın.

1. Claude masaüstü → "MKE Uluslararası Pazar İzleme Ajanı (Günlük)" → **Instructions**.
2. Paneldeki tüm metni seç (⌘A) ve sil.
3. `instructions-backup.md`'yi aç, `~~~~` işaretleri arasındaki metnin tamamını kopyala, panele yapıştır, kaydet.

**Görmen gereken:** panelde "Ek kurallar (Eylül 2026)" başlığı ve altındaki cümleler **yok**; metin `instructions-backup.md` ile aynı.
Ertesi sabahın raporu eski kurallarla yazılır. (Drive'daki `task-prompt.md`'ye dokunma — görev onu okumaz.)

## 3 · Kaynak listesi (Drive `kaynaklar.json`)

**Yedek alındı:** Drive → `defintel` klasörü → **`kaynaklar-yedek-2026-09-27.json`** (27 Eylül 2026,
merge öncesi hiçbir düzenleme yapılmadan; boyutu özgünle aynı, 38.608 bayt). Toplayıcı yalnız tam adı
`kaynaklar.json` olan dosyayı okur; yedek bu hâliyle hiçbir şeyi etkilemez.

Geri yüklemek için, Drive'da:

1. `kaynaklar.json` → sağ tık → **Yeniden adlandır** → `kaynaklar-bozuk-<bugünün tarihi>.json`
2. `kaynaklar-yedek-2026-09-27.json` → sağ tık → **Yeniden adlandır** → `kaynaklar.json`

**Görmen gereken:** klasörde tam adı `kaynaklar.json` olan **tek** dosya var. Sonraki toplamadan
(05:10 civarı) itibaren eski liste kullanılır.

**Dikkat:** yedek, merge öncesi "Defense Studies" `dil` düzeltmesinden de **önce** alındı. Geri
yüklersen o düzeltme de geri gider; istersen yeniden yap (`"dil": "id"`). Kod geri alındıysa (1. adım)
Elbit/Northrop girdilerini geri yüklemek gerekmez ama zararı da yok: eski kod yeni alanları okumaz,
yalnız Elbit yine "yanıt vermedi" görünür.
