# K6 — kaynaklar.json'a yapıştırılacaklar

Drive → `defintel` klasörü → `kaynaklar.json`. İki değişiklik var; başka hiçbir girdiye dokunmayın.

**Ne zaman:** `rev21-33` dalı main'e alındıktan sonra (merge günü), aynı gün. Bu alanları okuyan kod
şu an yalnız o daldadır; main'deki kod onları tanımaz. Erken yapıştırılırsa zarar vermez ama işe de
yaramaz (Northrop yine 403 alır, Elbit Systems UK okunmaz).

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

## 2 · Elbit Systems UK — yeni satır ekleyin

Dosyanın başındaki açılış `[` işaretinden hemen sonra yeni bir satır açın ve şu satırı yapıştırın
(sondaki virgül dahil — ardından sizin ilk girdiniz gelir):

```text
{"ad":"Elbit Systems UK","url":"https://www.elbitsystems-uk.com/media-events/recent-news","tur":"html","ayristirici":"elbitsystems-uk","ulke":"GB","dil":"en","kademe":"A","not":"Elbit Systems UK basın bültenleri sayfası (RSS yok); başlık+tarih+URL sayfadan okunur"},
```

Var olan `"ad":"Elbit Systems"` girdisini **silmeyin, değiştirmeyin** (aşağıdaki not).

Canlı deneme (24 Eylül 2026, 01:26 TSİ, toplayıcının istek biçimiyle): **HTTP 200, HTML sayfa,
20 başlık (tarihli).** (Bir dakika önceki denemede bir kez HTTP 500 geldi; toplayıcı her kaynağı iki
kez dener.) Son üçü:

| Tarih | Başlık |
|---|---|
| 16 Eyl 2026 | Elbit Systems UK Showcases Latest Land and Autonomous Capabilities at DVD 2026 — https://www.elbitsystems-uk.com/media-events/recent-news/elbit-systems-uk-showcases-latest-land-and-autonomous-capabilities-at-dvd-2026 |
| 7 Eyl 2026 | Elbit Systems UK Plays Key Role in Landmark Live Virtual Constructive Training Exercise — https://www.elbitsystems-uk.com/media-events/recent-news/elbit-systems-uk-plays-key-role-in-landmark-live-virtual-constructive-training-exercise |
| 5 Ağu 2026 | Elbit Systems UK Achieves Gold Defence Employer Recognition Scheme Award — https://www.elbitsystems-uk.com/media-events/recent-news/elbit-systems-uk-achieves-gold-defence-employer-recognition-scheme-award |

**Not — bu, Elbit ana şirketinin yerini tutmaz.** Sayfa yalnız İngiltere iştirakinin duyurularını
taşır ve seyrektir (2026'da 4 duyuru).

## Elbit Systems (ana şirket) — şimdilik değişiklik yok

Girdideki adres (`https://elbitsystems.com/feed/`) bizim bağlantımızdan hiç açılmıyor (HTTP 403,
sitenin güvenlik duvarı); sabah toplayıcısı ise aynı adresten yanıt alıyor ama içinde haber
bulamıyor. Nedenini toplayıcının çalıştığı yerden bakan bir tanı ile görüyoruz; sonucuna göre bu
girdi için ayrıca yazacağız. O zamana kadar brifingdeki "…kendi duyuruları bugün okunamadı"
satırı Elbit için basılmaya devam eder.
