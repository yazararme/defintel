# K6 — kaynaklar.json'a yapıştırılacaklar

Drive → `defintel` klasörü → `kaynaklar.json`. Üç değişiklik var: Northrop Grumman (1) ve Elbit
Systems (2) girdilerinde bul-değiştir, isteğe bağlı olarak Elbit Systems UK için yeni satır (3).
Başka hiçbir girdiye dokunmayın.

**Ne zaman:** `rev21-33` dalı main'e alındıktan sonra (merge günü), aynı gün. Bu alanları okuyan kod
şu an yalnız o daldadır; main'deki kod onları tanımaz. Erken yapıştırılırsa zarar vermez ama işe de
yaramaz (Northrop yine 403 alır; Elbit girdisi okunmaz ve "yanıt vermedi" sayılır; Elbit Systems UK
okunmaz). Üçü de aynı gün yapıştırılmalı.

## 1 · Northrop Grumman — var olan girdide tek değişiklik

`"ad":"Northrop Grumman"` girdisinde şu metni bulun (dosyada iki nokta üst üsteden sonra boşluk
varsa `"url": "…"` biçimindedir; aynı alandır):

```text
"url":"https://investor.northropgrumman.com/rss/news-releases.xml"
```

ve şununla değiştirin:

```text
"istek_basligi":{"Accept-Language":"en-US,en;q=0.9"},"url":"https://investor.northropgrumman.com/rss/news-releases.xml"
```

`url` aynı kalır; önüne tek alan eklenir. Satır sonundaki virgül (varsa) olduğu gibi kalır; girdinin
diğer alanlarına dokunmayın.

Neden: sitenin bot koruması (Akamai), tarayıcı kimliğiyle gelip dil başlığı göndermeyen isteği 403
ile reddediyor. Dil başlığıyla aynı adres 200 ve düzgün bir RSS döndürüyor.

Canlı deneme (24 Eylül 2026, 01:25 TSİ, toplayıcının istek biçimi + bu alan): **HTTP 200, RSS,
10 başlık.** Aynı dakikada alansız istek: **HTTP 403** (17–23 Eylül'deki hatanın aynısı). Son üçü:

| Tarih | Başlık |
|---|---|
| 17 Eyl 2026 | Northrop Grumman Announces Date for Third Quarter 2026 Financial Results and Webcast — https://investor.northropgrumman.com/news-releases/news-release-details/northrop-grumman-announces-date-third-quarter-2026-financial |
| 14 Eyl 2026 | U.S. Air Force and Northrop Grumman Assemble Inert Missile, Progress Toward Sentinel Flight Testing — https://investor.northropgrumman.com/news-releases/news-release-details/us-air-force-and-northrop-grumman-assemble-inert-missile |
| 10 Eyl 2026 | Northrop Grumman to Participate in the 14th Annual Morgan Stanley Laguna Conference — https://investor.northropgrumman.com/news-releases/news-release-details/northrop-grumman-participate-14th-annual-morgan-stanley-laguna |

## 2 · Elbit Systems — var olan girdide iki bul-değiştir

Neden: `https://elbitsystems.com/feed/` artık akış değil. Adres iki kez yönlendirilip
(301 → 301) `https://www.elbitsystems.com/news` haber **sayfasına** gidiyor (HTTP 200, HTML).
Toplayıcı o sayfada akış kaydı bulamadığı için 17–23 Eylül'de "feed parsed but empty" yazdı. Akış
sitede kaldırılmış; yerine haber sayfası okunur (başlık + tarih + URL).

`"ad":"Elbit Systems"` girdisinde (yalnız bu girdide) şu metni bulun:

```text
"url":"https://elbitsystems.com/feed/"
```

ve şununla değiştirin:

```text
"url":"https://www.elbitsystems.com/news","ayristirici":"elbitsystems-news"
```

Aynı girdide şu metni bulun (diğer girdilerde de geçer — **yalnız Elbit Systems girdisindekini**
değiştirin):

```text
"tur":"rss"
```

ve şununla değiştirin:

```text
"tur":"html"
```

(Dosyada iki nokta üst üsteden sonra boşluk varsa aranan metin `"url": "…"` / `"tur": "rss"`
biçimindedir; aynı alanlardır.) `ad`, `site` ve diğer alanlar olduğu gibi kalır.

Canlı deneme (24 Eylül 2026, 01:31 TSİ, toplayıcının çalıştığı GitHub Actions ortamından,
toplayıcının istek biçimiyle; eski adres istendi, yönlendirme sonrası gelen sayfa yeni ayrıştırıcıyla
okundu — buradan bu site 403 veriyor): **HTTP 200, HTML sayfa, 10 başlık
(tarihli).** Son üçü:

| Tarih | Başlık |
|---|---|
| 18 Eyl 2026 | Elbit Systems Files a Shelf Prospectus in Israel — https://www.elbitsystems.com/news/elbit-systems-files-shelf-prospectus-israel-0 |
| 14 Eyl 2026 | Successful Live Demonstration of the Loitering System: Diehl Defence and Elbit Systems successfully demonstrated SkyStriker’s Capabilities — https://www.elbitsystems.com/news/successful-live-demonstration-loitering-system-diehl-defence-and-elbit-systems-successfully |
| 9 Eyl 2026 | One2Many: Elbit Systems’ FUSE Introduces Military-Grade Autonomous Systems Built for Scale — https://www.elbitsystems.com/news/one2many-elbit-systems-fuse-introduces-military-grade-autonomous-systems-built-scale |

Bu değişiklikten sonra brifingdeki "…kendi duyuruları bugün okunamadı" satırı Elbit için de
kendiliğinden düşer (Northrop'unki 1. değişiklikle düşer).

## 3 · Elbit Systems UK — isteğe bağlı yeni satır (önerimiz: ekleyin)

Dosyanın başındaki açılış `[` işaretinden hemen sonra yeni bir satır açın ve şu satırı yapıştırın
(sondaki virgül dahil — ardından sizin ilk girdiniz gelir):

```text
{"ad":"Elbit Systems UK","url":"https://www.elbitsystems-uk.com/media-events/recent-news","tur":"html","ayristirici":"elbitsystems-uk","ulke":"GB","dil":"en","kademe":"A","not":"Elbit Systems UK basın bültenleri sayfası (RSS yok); başlık+tarih+URL sayfadan okunur"},
```

Bu satır 2. değişikliğin yerini tutmaz, ona ektir; 2. değişiklik ne olursa olsun yapılır.

Canlı deneme (24 Eylül 2026, 01:26 TSİ, toplayıcının istek biçimiyle): **HTTP 200, HTML sayfa,
20 başlık (tarihli).** (Bir dakika önceki denemede bir kez HTTP 500 geldi; toplayıcı her kaynağı iki
kez dener.) Son üçü:

| Tarih | Başlık |
|---|---|
| 16 Eyl 2026 | Elbit Systems UK Showcases Latest Land and Autonomous Capabilities at DVD 2026 — https://www.elbitsystems-uk.com/media-events/recent-news/elbit-systems-uk-showcases-latest-land-and-autonomous-capabilities-at-dvd-2026 |
| 7 Eyl 2026 | Elbit Systems UK Plays Key Role in Landmark Live Virtual Constructive Training Exercise — https://www.elbitsystems-uk.com/media-events/recent-news/elbit-systems-uk-plays-key-role-in-landmark-live-virtual-constructive-training-exercise |
| 5 Ağu 2026 | Elbit Systems UK Achieves Gold Defence Employer Recognition Scheme Award — https://www.elbitsystems-uk.com/media-events/recent-news/elbit-systems-uk-achieves-gold-defence-employer-recognition-scheme-award |

**Neden isteğe bağlı ama önerilir:** ana şirketin haber sayfası İngiltere iştirakinin duyurularının
yalnız bir kısmını taşıyor. Yukarıdaki 16 ve 7 Eylül duyuruları ana sayfada yok; oradaki tek
Elbit Systems UK duyurusu 17 Temmuz (Farnborough). Sayfa seyrektir (2026'da 4 duyuru). Aynı haber
iki sayfada da çıkarsa toplayıcı aynı başlığı bir kez yazar.
