## Revizyon 31 — brifingden sonra gelen haber

**Hedef.** Brifingin kesim saatinden sonra gelen hiçbir haber iki gün arasında
kaybolmasın, ve medya takibi hangi kalemin brifingden sonra geldiğini söylesin.
**Dosyalar.** `scripts/collect_news.py` (`ilk_goruldu`, aday dosyasının ilk bölümü),
`build.py` (medya satırı jetonu), `assets/app.css`.
**Build kuralı.** GEÇ-GELEN.

### R31.0 — Tanı: Aselsan–Roketsan sözleşmesi neden brifinge ulaşmadı

Bu bir yargı hatası değil, bir zamanlama boşluğu. Kanıt git geçmişinde:

| saat (TR) | olay | AA kalemi |
|---|---|---|
| 05:19 | `collect-news` (Apps Script tetiği): 539 başlık, **AA akışı okundu, 0 AA kalemi** | yok |
| 06:00 | Ajan `…-aday.md`'yi okur | yok |
| 06:16 | Brifing yayımlanır | — |
| 11:04 | GitHub'ın beş saat gecikmeli `40 2` cron'u, yedek: 536 başlık, **aynı dosyaların üzerine yazar** | **var** (aday.md satır 112) |

Anadolu Ajansı'nın akışı 05:19'da sorunsuz okundu; haber henüz yayımlanmamıştı. 11:04'teki
yedek çalıştırma günün dosyalarını sessizce değiştirdi. Medya takibi artık brifingin hiç
görmediği bir haberi aynı günün "ham yüzü" olarak gösteriyor. Rev 0'ın sözü ("bir gün, iki
yüzü olan tek dosya") bu satır için tutmuyor. Brifingin Oyuncular rayındaki "Roketsan" da
bu geç kalemden geliyor.

Ertesi gün, 24 Eylül'ün aday listesi 48 saatlik pencere sayesinde kalemi yeniden
taşıyacak. Ama onu dünden kalan *yeni bir şey* olarak işaretleyen hiçbir şey yok. Ayrıca
260'lık sınır onu Genel ve İhale arasında kesebilir.

**Ayrı tutulan soru:** Ajan kalemi görseydi brifinge alır mıydı? Bu, DECISIONS › Açık
maddesindeki Türk emsal çerçeve sorusu. MKE'ye gider ve bu revizyonun parçası değil.
Bu revizyon yalnızca *görme* koşulunu düzeltiyor.

### R31.1 — Karar

- Her kalem `ilk_goruldu` zaman damgasını taşır. Aynı gün yeniden toplandığında var olan
  kalemin damgası **değişmez**. Yeni kalem kendi damgasıyla eklenir, var olanların üzerine
  yazılmaz.
- Medya takibinde `ilk_goruldu` brifingin yayın saatinden sonra olan satır **"BRİFİNGDEN
  SONRA"** jetonunu taşır. Jeton `BRİFİNGDE` ile aynı yuvada, mono ve `--muted` renkte
  durur. İkisi birbirini dışlar. Rev 0'ın "tek renkli meta jetonu BRİFİNGDE" kuralı
  korunuyor: yeni jeton renksiz.
- Ertesi günün `…-aday.md`'si **"## Dünkü brifingden sonra gelenler (N)"** bölümüyle
  başlar. `CANDIDATE_ORDER`'da bu bölüm birinci sıradadır, böylece 260 sınırı onu kesemez.

### Build kuralı — GEÇ-GELEN

> Bir kalemin `ilk_goruldu` değeri yeniden toplamada değişirse **Rev 30** kanalına uyarı
> gider. Önceki günün brifinginden sonra ilk görülen her kalem bugünkü aday dosyasının
> ilk bölümünde bulunmak zorunda. Eksikse uyarı gider. Çalıştırma, jetonlu satır sayısını
> **(A)** özetine yazar.

### Uygulama listesi — Revizyon 31

| # | Dosya | Değişiklik | Kabul (ekran görüntüsü) |
|---|---|---|---|
| R31-P0-1 | `collect_news.py` | `ilk_goruldu`; yeniden toplamada var olan kalemin üzerine yazılmaz | **(A)** ikinci çalıştırmanın özetinde "yeni: n · değişmedi: m · damga değişti: 0" |
| R31-P0-2 | `build.py`, `app.css` | "BRİFİNGDEN SONRA" jetonu | **(S)** `/haberler/2026-09-23.html?oyuncu=roketsan`, 375px: AA satırında "BRİFİNGDEN SONRA" |
| R31-P0-3 | `collect_news.py` | Aday dosyasının ilk bölümü | **(D)** `/data/news/2026-09-24-aday.md` tarayıcıda: ilk bölüm "Dünkü brifingden sonra gelenler" ve AA satırını içeriyor |
| R31-P1-1 | `collect_news.py` | GEÇ-GELEN | Damga bilerek değiştirildiğinde **(P)** "GEÇ-GELEN" uyarısı |

**Yapılmayacak:**
- Yedek cron'u kaldırmak (memory'deki gerekçe: GitHub cron'u beş saat geç çalışıyor;
  yedek tek güvence).
- Geç kalemi gizlemek (Rev 0: hiçbir kalem silinmez).
- Brifingi geç kalem için yeniden yazdırmak (brifing günde bir kez, insan incelemesi
  olmadan yayımlanıyor; ikinci bir sürüm, okuyucunun okuduğunun değiştiği anlamına gelir).

---

### Orkestratör notu (23 Eylül)

- **Sabah hattı çalıştırılmaz.** `collect-news.yml`'i dispatch etmek, ağa çıkmak, Claude/çeviri
  çağrısı yapmak ya da Drive'a dokunmak **yasak** (müşteri kuralı: dal push'u sabah hattını
  çalıştıramaz). Bu yüzden:
  - `collect_news.py`'ye ağsız bir sınama yolu ekle (ör. `--fixture <dizin>` ya da bir
    fonksiyon düzeyi test): kaydedilmiş başlıklarla aynı günü **iki kez** toplar; ikinci
    çalıştırma bir yeni kalem ekler. Model/çeviri/Drive çağrısı yok.
  - Bunu `push` ile yalnız `rev21-33` dalında tetiklenen ayrı bir sınama iş akışında koştur
    (Rev 30'un `uyari-test.yml` kalıbı; `permissions: issues: write, contents: read`, sır
    yok). **(A)** kanıtı: ikinci çalıştırmanın özetinde "yeni: n · değişmedi: m · damga
    değişti: 0". Aynı iş akışında bir iş damgayı bilerek değiştirir → `UYARI_TEST_ONEK:
    "[TEST] "` ile **(I)** issue'da GEÇ-GELEN satırı (planın **(P)**'si → **(I)**).
- **23 Eylül'ün `ilk_goruldu` değerleri:** bugünkü veride alan yok. Git geçmişinden
  (`git log -p -- data/news/2026-09-23.json` ve aday.md; 05:19 ve 11:04 TR çalıştırmaları)
  geriye doldur, böylece AA satırı gerçekten "BRİFİNGDEN SONRA" olur. Brifingin yayın saati
  için var olan veriyi kullan (ör. `data/published.json`).
- **(D) `/data/news/2026-09-24-aday.md`:** henüz yok. Yalnız **yerel kanıt** olarak,
  ağsız yolla 23 Eylül verisinden üret; dosyayı `review/builder-notes/rev-31.md`'de adıyla
  belirt — orkestratör onu **commit etmeyecek** (gerçek 24 Eylül dosyasını sabah hattı üretir).
