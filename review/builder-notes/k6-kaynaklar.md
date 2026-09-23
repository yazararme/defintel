# K6 — kaynaklar.json'a yapıştırılacaklar

Drive → `defintel` klasörü → `kaynaklar.json`. İki değişiklik var; başka hiçbir girdiye dokunmayın.
Kod tarafı (`scripts/collect_news.py`) bu iki alanı okuyacak şekilde güncellendi; alanı olmayan
kaynaklar eskisi gibi toplanır.

## 1 · Northrop Grumman — var olan girdiye tek alan ekleyin

`"ad": "Northrop Grumman"` girdisini bulun. `url` **aynı kalır**
(`https://investor.northropgrumman.com/rss/news-releases.xml`). Girdiye şu alanı ekleyin (diğer
alanlar olduğu gibi kalır):

```json
{
  "ad": "Northrop Grumman",
  "istek_basligi": {"Accept-Language": "en-US,en;q=0.9"}
}
```

Neden: sitenin bot koruması (Akamai), tarayıcı kimliğiyle gelip dil başlığı göndermeyen isteği
403 ile reddediyor. Dil başlığıyla aynı adres 200 ve düzgün bir RSS döndürüyor.

Canlı deneme (24 Eylül 2026, 01:05 TSİ, toplayıcının istek biçimiyle + bu başlık): **HTTP 200,
RSS, 10 başlık.** Son üçü:

| Tarih | Başlık |
|---|---|
| 17 Eyl 2026 | Northrop Grumman Announces Date for Third Quarter 2026 Financial Results and Webcast — https://investor.northropgrumman.com/news-releases/news-release-details/northrop-grumman-announces-date-third-quarter-2026-financial |
| 14 Eyl 2026 | U.S. Air Force and Northrop Grumman Assemble Inert Missile, Progress Toward Sentinel Flight Testing — https://investor.northropgrumman.com/news-releases/news-release-details/us-air-force-and-northrop-grumman-assemble-inert-missile |
| 10 Eyl 2026 | Northrop Grumman to Participate in the 14th Annual Morgan Stanley Laguna Conference — https://investor.northropgrumman.com/news-releases/news-release-details/northrop-grumman-participate-14th-annual-morgan-stanley-laguna |

Aynı dakikada başlıksız istek: HTTP 403 "Access Denied" (17–23 Eylül'deki hatanın aynısı).

## 2 · Elbit Systems UK — yeni girdi ekleyin

Listeye aşağıdaki girdiyi **yeni kaynak olarak** ekleyin. Var olan `"ad": "Elbit Systems"` girdisini
**silmeyin, değiştirmeyin** (aşağıdaki not).

```json
{
  "ad": "Elbit Systems UK",
  "url": "https://www.elbitsystems-uk.com/media-events/recent-news",
  "tur": "html",
  "ayristirici": "elbitsystems-uk",
  "ulke": "GB",
  "dil": "en",
  "kademe": "A",
  "not": "Elbit Systems UK basın bültenleri sayfası (RSS yok); başlık+tarih+URL sayfadan okunur"
}
```

`kademe`yi var olan "Elbit Systems" girdisindeki değerle aynı yapabilirsiniz; "A" önerimizdir.

Canlı deneme (24 Eylül 2026, 01:07 TSİ): **HTTP 200, HTML sayfa, 20 başlık (tarihli).** Son üçü:

| Tarih | Başlık |
|---|---|
| 16 Eyl 2026 | Elbit Systems UK Showcases Latest Land and Autonomous Capabilities at DVD 2026 — https://www.elbitsystems-uk.com/media-events/recent-news/elbit-systems-uk-showcases-latest-land-and-autonomous-capabilities-at-dvd-2026 |
| 7 Eyl 2026 | Elbit Systems UK Plays Key Role in Landmark Live Virtual Constructive Training Exercise — https://www.elbitsystems-uk.com/media-events/recent-news/elbit-systems-uk-plays-key-role-in-landmark-live-virtual-constructive-training-exercise |
| 5 Ağu 2026 | Elbit Systems UK Achieves Gold Defence Employer Recognition Scheme Award — https://www.elbitsystems-uk.com/media-events/recent-news/elbit-systems-uk-achieves-gold-defence-employer-recognition-scheme-award |

**Not — bu, Elbit ana şirketinin yerini tutmaz.** Sayfa yalnız İngiltere iştirakinin duyurularını
taşır ve seyrektir (2026'da 4 duyuru). Ana şirketin siteleri (`elbitsystems.com`,
`ir.elbitsystems.com`) bu denemeyi yaptığımız Türkiye bağlantısından hiç açılmıyor (her adres 403
ya da 401). Bu yüzden:

- "Elbit Systems" girdisi yerinde kalır; ana şirket akışı onarılana kadar brifingdeki
  "…kendi duyuruları bugün okunamadı" satırı Elbit için basılmaya devam eder (Rev 28 kararı).
- Bize "Elbit Systems" girdisindeki **`url` değerini** iletin (repoda kaydı yok). Toplayıcı her gün o
  adresten 200 alıyor ama içinde akış bulamıyor; adresi görmeden ana şirket için onarım öneremeyiz.
