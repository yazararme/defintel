# Revizyon 21–33 — denetim sonrası plan

Kaynaklar: `audit/findings.md` (F-01…F-17), `audit/content.md` (Ö1–Ö7, S1–S8),
`review/blind.md`, `review/reconcile.md` (C1–C10) ve müşterinin 23 Eylül'deki iki tur
kararı. Biçim `design-review-log-TR.md` ile aynı. Bu metin henüz loga eklenmedi; onaydan
sonra Rev 20'nin arkasına eklenecek. (Dosyanın adı değişmedi; kapsamı Rev 33'e kadar
genişledi.)

**Müşterinin seçtikleri — birinci tur**

1. **Genel / süzgeç.** Kapı şartı: rastgele 100 elenmiş kalemde en fazla 2 ilgili kalem
   olacak ve bunu taze bir alt ajan değerlendirecek. Elenen kalemler aranabilir kalacak.
   → **Kapı geçilmedi** (Rev 25).
2. **Başlık düzeni:** cümle düzeni.
3. **Rakip Duyuruları:** izlenen 64 oyuncuyla sınırlanacak, adı nötr olacak.
4. **Oyuncu sayıları:** sayı yok, yalnızca adlar. Eşleştirici 64 oyuncuya alias testleriyle
   genişletilecek. "N kez" de aynı muameleyi görecek.

**Müşterinin seçtikleri — ikinci tur**

5. Aselsan–Roketsan sözleşmesinin brifinge ulaşmamasının nedeni bulunacak ve giderilecek
   → **Rev 31**. Çerçeve sorusu (MKE'ye) ayrı tutulacak.
6. Oyuncu sayıları **ya hep ya hiç**: 64 oyuncunun hepsi alias testini geçmeden hiçbir
   oyuncuya sayı basılmayacak (Rev 21 buna göre değişti).
7. Uyarı veren her build kuralı uyarısını müşterinin push alarmına gönderecek → **Rev 30**.
8. Günler arası tekrarlanan manşet → **Rev 32**. İngilizce kaynak adlarındaki noktalı İ
   → **Rev 33**.
9. Özet kutusunun kenar çizgisi kalkacak; "asla ikisi birden" kuralı olduğu gibi kalacak
   → R29.4.
10. Tutulan savunma dışı başlıkların (yalnızca başlık, özet yok) günlük çeviri maliyeti
    → R25.1.

### Her revizyonun taşıması gerekenler

Her revizyon dört şey taşır: **Hedef**, **Dosyalar**, adıyla bir **build kuralı** ve bir
inceleyicinin **yalnızca ekran görüntüsünden** kontrol edebileceği kabul ölçütleri.

Kabul edilen ekran görüntüsü yüzeyleri:

- **(S)** canlı sitenin sayfası, 375×812 ya da 1440×900
- **(P)** operatörün telefonuna gelen push uyarısı (Rev 30)
- **(A)** GitHub Actions çalıştırmasının özet sayfası (`$GITHUB_STEP_SUMMARY`)
- **(D)** sitenin tarayıcıda açılan herkese açık bir veri dosyası (`/data/…`)

Kaynak kod, JSON içeriği ya da terminal çıktısı kabul ölçütü olamaz.

---

## R21–33.0 — Puanlar

| Boyut | Puan | 7 nasıl görünür | 10 nasıl görünür |
|---|---|---|---|
| **Hiyerarşi** | 6 | Her gelişmenin başlığı kendi etiketi; H1 özet maddesini tekrar etmiyor; bölüm çizgileri seçilebilir (≥3:1) | Sayfadaki her yazı boyutu 6–7 belirteçten biri; her sınır tek mekanizmayla işaretli |
| **4 dakikalık okuma** | 5 | 375×812'de YÖNETİCİ ÖZETİ 300px'ten önce başlıyor ve 5 maddenin 4'ü ilk ekranda; her madde kimin ne yaptığını söylüyor; önceden verilmiş bir haber yeni diye sunulmuyor | İlk ekran = tarih + 5 madde; her sayı ve adın tek değeri var ve build'in çapraz denetiminden geçmiş |
| **Gezinme** | 5 | İplik sayfası okunan güne dönüyor; `→ bugün:` bağlantısının indiği başlık bağlantı metniyle aynı | Her bağlantı nereye gittiğini söylüyor; her iniş, tıklanan şeyin adını gösteriyor; kalıcı URL'ler hiç kırılmıyor |
| **Süzme / arama** | 4 | Ağ hatası "kayıt yok" demiyor; sıfır sonuç açıkça söyleniyor; yükleme görünüyor; süzülmüş listenin üstündeki sayılar yeniden sayılıyor | Arama, kategori ve oyuncu hapı birlikte çalışıyor; dört durumun her birinin kendi dürüst ekranı var ve testleri build'de koşuyor |
| **Mobil** | 6 | Taşma yok, ilk ekran doğru, kart alanları etiketli | Telefon birincil tasarım: 88px yapışkan bütçe içinde bölüm gezinmesi, her kart alanı adıyla |
| **İçerik güveni (çeviri + kategori)** | 3 | Adı olan kategorilerde isabet ≥%70; çeviri kusuru ≤%15; sessiz eksiltme sıfır; tek başlık düzeni; yabancı adlar doğru harflerle | Build her gün isabeti ve dedektörleri ölçüyor, eşik aşılınca operatöre haber veriyor; ajanın yazdığı hiçbir sayı kaynağıyla çelişmiyor |
| **Üretici durumu sızıntısı** | 5 | Okuyucuya basılan her sayı yazıldığı biçimde doğru; ağ arızası içerik olgusu olarak görünmüyor | İnanç değiştiren tek arıza tek satırla söyleniyor; geri kalan her şey sayfaya değil yalnızca operatöre gidiyor |

---

## R21–33.1 — Sıralama: kullanıcı etkisi ÷ emek

Etki 1–5: kaç okuyucuyu ne kadar yanıltıyor ya da durduruyor. Emek 1–5: 1 = tek dosyada
bir öğleden sonra. Yukarıdan aşağı uygulanır. Bağımlılıklar parantez içinde.

**Rev 30 birinci sırada.** Kendi etkisi düşük, ama sonraki bütün uyarı kuralları ona
bağlı. O olmadan bir uyarı kuralı, okunmayan bir build kaydına yazmaktan ibaret
(PRODUCT.md: *açılmayan sayfa denetim değildir*).

| Sıra | Madde | Rev | Etki | Emek | Oran |
|---|---|---|---|---|---|
| 0 | Operatör uyarı kanalı (bütün uyarı kurallarının ön şartı) | 30 | — | 2 | ön şart |
| 1 | Ağ hatası "kayıt yok" demesin | 22 | 5 | 1 | 5.0 |
| 2 | Oyuncu sayıları kalksın, yalnız adlar kalsın | 21 | 5 | 1 | 5.0 |
| 3 | Ajan para birimi çevirmesin | 23 | 4 | 1 | 4.0 |
| 4 | Brifingden sonra gelen haber işaretlensin ve ertesi güne taşınsın | 31 | 4 | 1 | 4.0 |
| 5 | Gelişme başlığı = etiket | 23 | 3 | 1 | 3.0 |
| 6 | Sıfır sonuç görünsün | 22 | 3 | 1 | 3.0 |
| 7 | Yabancı adlarda noktalı İ | 33 | 3 | 1 | 3.0 |
| 8 | Yöneticinin ilk ekranı | 24 | 5 | 2 | 2.5 |
| 9 | Tekrar eden manşet işaretlensin | 32 | 4 | 2 | 2.0 |
| 10 | Kategori kuralları: S2 + S3 + S6 | 25 | 4 | 2 | 2.0 |
| 11 | İplik sayfası: durum satırı, güne dönüş | 27 | 4 | 2 | 2.0 |
| 12 | Süzgeç altında kapsam satırı yeniden sayılsın | 22 | 2 | 1 | 2.0 |
| 13 | Arama yükleniyor durumu | 22 | 2 | 1 | 2.0 |
| 14 | H1 özet maddesini tekrar etmesin | 23 | 2 | 1 | 2.0 |
| 15 | Mobil kartta "İzlenecek" etiketi | 24 | 2 | 1 | 2.0 |
| 16 | Bölüm çizgisi ≥3:1 | 29 | 2 | 1 | 2.0 |
| 17 | Özet kutusunun kenar çizgisi kalksın | 29 | 2 | 1 | 2.0 |
| 18 | Kaynaklar'da "yanıt vermedi" sütunu kalksın | 28 | 2 | 1 | 2.0 |
| 19 | Kategori isabeti ölçülsün | 25 | 2 | 1 | 2.0 |
| 20 | Yanlış `dil` etiketli kaynağın düzeltilmesi (Ö6'nın ucuz yarısı) | 26 | 2 | 1 | 2.0 |
| 21 | Çeviri: cümle düzeni + dedektörler + Ö1/Ö2/Ö3 | 26 | 5 | 3 | 1.7 |
| 22 | Mevcut süzgeç düşürmesin, işaretlesin | 25 | 3 | 2 | 1.5 |
| 23 | "Oyuncu Duyuruları", 64 ile sınırlı (← 25) | 25 | 3 | 2 | 1.5 |
| 24 | İzlenen oyuncunun kaynağı düştüğünde uyarı satırı | 28 | 4 | 3 | 1.3 |
| 25 | Eşleştirici 64 oyuncuya, alias testleriyle | 21 | 4 | 3 | 1.3 |
| 26 | Bildirim teklifi ilk ziyarette, kart zili örtmesin | 29 | 2 | 2 | 1.0 |
| 27 | Ölü tema koruması, F-07, F-08 | 29 | 1 | 1 | 1.0 |
| 28 | Dili metinden tespit et (Ö6'nın tamamı) | 26 | 2 | 2 | 1.0 |
| 29 | İngilizce dışı kaynaklar için geri çeviri (Ö7) | 26 | 3 | 4 | 0.75 |
| 30 | Yazı boyutu belirteçleri | 29 | 2 | 3 | 0.7 |
| 31 | Slug'lar | 27 | 1 | 2 | 0.5 |
| 32 | Masaüstü genişlikleri tek ızgara | 29 | 1 | 2 | 0.5 |

### S2/S3/S6 ve çeviri düzeltmeleri — teyit

- **S2, S3, S6** Rev 25'te, **P0** olarak var. Ertelenmedi; sıra 10.
- **Çeviri:** cümle düzeni, Ö1, Ö2 ve ÇEVİRİ-DEDEKTÖRÜ Rev 26'da **P0**, Ö3 **P1**, hepsi
  sıra 21'de. Ertelenmedi. Tek satırlık bir düzeltme değil: prompt değişiyor, dedektörler
  yazılıyor ve canlı pencere yeniden çevriliyor, bu yüzden oranı 1.7.
- **Ertelenen iki madde:**
  - **Ö6** ikiye bölündü. Ucuz yarısı (bilinen yanlış `dil` etiketini Drive'daki
    `kaynaklar.json`'da düzeltmek) sıra 20'ye çıktı. Tamamı (dili metinden tespit etmek)
    sıra 28'de kaldı. Gerekçe: denetim yalnızca bir yanlış etiketli kaynak buldu; önce
    etiketi düzeltmek aynı hatayı sıfır kodla kapatıyor.
  - **Ö7** (geri çeviri) sıra 29'da, P3. Gerekçe: İngilizce dışı her başlık için ikinci bir
    model çağrısı gerekiyor, yani çağrı sayısı o kaynaklar için ikiye katlanıyor. Hedeflediği
    hataların (anlam kayması, eksiltme) büyük kısmını Ö1, Ö2 ve ÇEVİRİ-DEDEKTÖRÜ zaten
    yakalamaya çalışıyor. Önce onların etkisi ölçülecek; İngilizce dışı kusur oranı hâlâ
    İngilizcenin 1,5 katından fazlaysa Ö7 açılacak.

**Yapılmayacak:** S1, süzgeci herkese varsayılan açmak (kapı geçilmedi, Rev 25). S7,
sıralamayı değiştirmek (yalnızca %2,2 kalemde belirleyici).

---

## Revizyon 21 — sayı bir iddiadır: oyuncu sayıları

**Hedef.** Okuyucuya basılan hiçbir oyuncu sayısı, eşleştiricinin görmediği oyuncular
yüzünden yanlış olmasın.
**Dosyalar.** `build.py` (`players_page`, `player_history`, `tag_turkish_headlines`),
`data/rakipler.json`, `assets/app.css`.
**Build kuralı.** KAPSAM-SAYI.

### R21.0 — Tanı: eşleştirici oyuncuların yarısını görüyor, sayılar hepsini görüyormuş gibi konuşuyor

23 Eylül'de ray "Bugün 9" diyor. İzlenen 64 adı günün 536 satırında sözcük sınırıyla
aradım. Sayılmayan dokuz izlenen oyuncu daha çıktı: Thales 4, PGZ 3, Northrop Grumman 3,
Anduril 2, KNDS 1, Hanwha 1, Rafael 1, IAI 1, Munitions India 1.

Nedeni yapısal. Birinci geçiş (`rival_hits`) yalnızca brifing gövdesine bakıyor. İkinci
geçiş (`tag_turkish_headlines`) yalnızca Türk rollerini arıyor. PRODUCT.md'ye göre bu
durumda sayı eksik değil, **yanlış**.

**"N kez" aynı eşleştiriciyi kullanıyor.** `player_history()` (`build.py:1972`) aynı iki
geçişi gün gün topluyor ve `sayi_30g` oradan geliyor. "son 30 günde 22" (`build.py:1033`)
de oradan. `sayi_30g` ayrıca **gün** sayıyor, geçiş sayısı değil.

Rev 18b'nin "boşluk ifadenin kendisidir" kuralı da bugün yalan söylüyor: Thales'in
satırındaki boşluk "bu ay hiç geçmedi" diyor, oysa bugün dört kez geçti.

### R21.1 — Sayılar gider, adlar kalır

- **Ray:** adlar olduğu gibi kalıyor. Bir ad listedeyse o oyuncu gerçekten geçmiş demektir.
  Listenin sonuna "hepsi bu" diye okunacak bir işaret konmayacak.
- **/oyuncular.html üst satırı:** yalnızca **"izlenen 64"**. Bu, yapılandırmadan gelen,
  kapsamdan bağımsız tek sayı.
- **Satırlar:** `N kez` ve yaş jetonları (`bugün / dün / N gün önce`) **hep birlikte**
  kalkıyor.
- **Sıra:** alfabetik, Türkçe harmanlamayla.
- Segment çipleri ve arşiv bağlantısı kalıyor. Eşleştiriciye dayanmıyorlar.

### R21.2 — Sayılar ya hep ya hiç (müşterinin kararı)

Eşleştirici iki geçişte de 64 oyuncunun hepsini kapsayacak, yabancılar dahil. Rev 17'nin
"rol render'a aittir" kuralı değişmiyor. `data/rakipler.json` içindeki her oyuncuya
`aliases[]` ve `alias_test{pos[],neg[]}` eklenecek: en az bir pozitif örnek, ≤4 harfli her
alias için en az bir negatif örnek (`IAI` ↛ "sa**iai**d", `CSG` ↛ "C**SG**O").

**Oyuncu oyuncu açılma yok.** 64'ün 64'ü testi geçene kadar hiçbir satırda sayı ya da yaş
jetonu basılmaz, üst satır da "izlenen 64" olarak kalır. 64'ün hepsi geçtiğinde şunlar
birlikte döner: üst satırdaki "Bugün N · son 30 günde N", satırdaki `N gün` (eski adı
`N kez`), yaş jetonu ve sıklığa göre sıralama.

Gerekçe: bir tarafta sayısı olan, öbür tarafta sayısı olmayan bir tablo okuyucuya iki ayrı
sözleşme sunar. Sayısız satır da "az geçti" diye okunur.

### Build kuralı — KAPSAM-SAYI

> Oyunculardan türeyen herhangi bir sayı ya da jeton, **64 oyuncunun tamamı**
> `alias_test`'i geçtiyse basılır. Bir oyuncu bile kalırsa hiçbiri basılmaz. `build.py`
> testleri her derlemede koşar. Sonuç **(A)** özetine "alias testi 57/64 — kalanlar: …"
> olarak yazılır. 64/64'ten aşağı düşüş (ya da 64/64'e ilk varış) **Rev 30** kanalına
> uyarı gönderir. Sayfa her durumda üretilir.

### Uygulama listesi — Revizyon 21

| # | Dosya | Değişiklik | Kabul (ekran görüntüsü) |
|---|---|---|---|
| R21-P0-1 | `build.py` `players_page` | Üst satır "izlenen {n}"; `pcount` ve yaş jetonu kalkar; alfabetik sıra | **(S)** /oyuncular.html, 375px: üst satır yalnızca "izlenen 64"; hiçbir satırda "kez" ya da "önce" yok; ilk iki satır Anduril, Arsenal Bulgaria |
| R21-P0-2 | `build.py` | Segment süzgecinde üst satır yeniden sayılır | **(S)** "Mühimmat" çipi açıkken üst satır "izlenen {o segmentteki sayı}" |
| R21-P1-1 | `data/rakipler.json` | 64 oyuncuya `aliases` + `alias_test` | **(A)** özet: "alias testi 64/64" |
| R21-P1-2 | `build.py` | Başlık geçişi bütün rollere genişler (`tag_player_headlines`) | **(S)** `/haberler/2026-09-23.html?oyuncu=thales` en az 1 satır gösterir |
| R21-P1-3 | `build.py` | KAPSAM-SAYI; `N kez` → `N gün` | **(P)** Bir oyuncunun testi bilerek bozulduğunda "KAPSAM-SAYI: 63/64" uyarısı gelir. **(S)** O derlemede hiçbir satırda sayı yok. 64/64'te **(S)** "Bugün N", "N gün" ve yaş jetonları görünür |

**Yapılmayacak:** sayıyı dipnotla kurtarmak; sayıyı yalnızca Türk oyuncular için bırakmak;
testi geçen oyuncuları tek tek açmak (müşterinin kararı).

---

## Revizyon 22 — arama durumlarını ayırmak

**Hedef.** Arama ve süzme dört durumu ayrı ve doğru söylesin: yükleniyor, hata, sonuç
yok, N sonuç.
**Dosyalar.** `assets/app.js` (`load()`, `retally`/`sectionParts`, kapsam satırı),
`scripts/check_reports.py`, `.github/workflows/build.yml`.
**Build kuralı.** DÖRT-DURUM.

### R22.0 — Tanı

- Arşivde ağ hatası "sonuç yok" gibi görünüyor (F-01, P0): `load()` hatayı `[]` ile
  çözümlüyor.
- Medya takibinde sonuç yok durumu boş sayfa gibi görünüyor (F-02): `sectionParts()`
  `#noresults`'ı da gizliyor.
- Yükleme durumu yok (F-16).
- Kapsam satırı süzgeçle yeniden sayılmıyor (F-06). Rev 18b'nin yasası bu sayfada
  uygulanmamış.

Rev 7'nin kanunu: **bir yüzey, sonucunu bildiremediği bir eylemi tetikleyemez.**

### R22.1 — Kural

- `load()` hatayı asla boş diziyle çözümlemez. Hata durumunda panel *"Arama şu an
  çalışmıyor — sayfayı yenileyin."* yazar. Neden yazılmaz.
- `#noresults` bölüm yürüyüşünün dışına taşınır.
- 300ms'yi geçen yüklemede panel "Aranıyor…" yazar.
- Süzgeç açıkken kapsam satırı **"{görünen} / 536 başlık"** yazar.

### Build kuralı — DÖRT-DURUM

> `check_reports.py` başsız bir tarayıcıda dört senaryo koşar: `fetch` reddedilir →
> "çalışmıyor"; "xyzzy" → `#noresults` görünür; 3 sn gecikme → "Aranıyor…"; "Hanwha" → ≥1
> sonuç. Her senaryonun ekran görüntüsü **(A)** özetine eklenir. Biri kalırsa **build
> durur** ve **Rev 30** kanalına uyarı gider. Bu kural bloklayıcı, çünkü sessizce yanlış
> olan tek yüzey bu.

### Uygulama listesi — Revizyon 22

| # | Dosya | Değişiklik | Kabul (ekran görüntüsü) |
|---|---|---|---|
| R22-P0-1 | `assets/app.js:733` | Hata dalı ayrı çizilir | **(A)** "fetch reddedildi" senaryosunun görüntüsü "Arama şu an çalışmıyor" gösterir, "kayıt yok" göstermez |
| R22-P0-2 | `assets/app.js` | Yürüyüş `#noresults`'ta durur | **(S)** medya takibi, 375px, "xyzzy" arandı: "sonuç yok" metni görünür |
| R22-P1-1 | `assets/app.js` | Yükleniyor durumu | **(A)** 3 sn gecikme senaryosunda "Aranıyor…" |
| R22-P1-2 | `assets/app.js` | Kapsam satırı yeniden sayılır | **(S)** `?oyuncu=roketsan` → "2 / 536 başlık" |
| R22-P1-3 | `check_reports.py`, `build.yml` | DÖRT-DURUM | **(A)** dört görüntü yeşil; bir dal bilerek bozulduğunda kırmızı çalıştırma ve **(P)** uyarısı |

---

## Revizyon 23 — bir olgu, bir ad, bir değer

**Hedef.** Bir gelişmenin adı ve sayıları sayfanın her yerinde tek ve doğru olsun.
**Dosyalar.** `enrich.py`, `build.py`, rapor promptu (masaüstü görev talimatı; müşteri
yapıştırır).
**Build kuralları.** ETİKET-BAŞLIK · KUR · H1-TEKRAR.

### R23.0 — Tanı: yasa var, uygulanmıyor

1. **Etiket başlık olmadı.** `source/2026-09-23.md:9`'da G9'un etiketi "Lynx XM30 prototip
   teslimi", ama sayfa başlığı "American Rheinmetall". Aynı sorun G3 ve G8'de de var.
   İzleme listesindeki bağlantı "Lynx XM30 prototip teslimi" diyor, indiği başlık başka
   bir şey söylüyor.
2. **Ajan kur çevirdi ve yanıldı.** Brifing "1,5 milyar $ (16 milyar NOK)" diyor. Kaynak
   özetleri ise "NOK 16 milyar (yaklaşık 1,74 milyar dolar)" diyor
   (`data/news/2026-09-23.json:1179`).
3. **H1, özetin 1. maddesi.**
4. **Özetin 2. maddesinde özne yok.**

### R23.1 — Karar

- Gelişme başlığı **her zaman** `label`. Ajanın kalın yazdığı giriş kelimeleri gövdeden
  atılır (`enrich.py`, Rev 11'in yolu).
- Prompt'a üç cümle eklenir:
  - Kur: *"Tutarı kaynağın verdiği para biriminde yaz. Kaynak kendi çevirisini veriyorsa
    parantez içinde aynen aktar. Kendin kur çevirme."*
  - H1: *"Başlık günün tezidir, özet maddelerinden biri değildir."*
  - Özne: *"Her özet maddesi kimin ne yaptığını söyler."*

### Build kuralları — R23

> **ETİKET-BAŞLIK.** Her `h3.dev` kendi `label`'ına eşit olmalı. Her `→ bugün:` bağlantı
> metni de indiği başlığa eşit olmalı.
> **KUR.** Gövdede bir para birimi ve yanında parantez içinde başka bir para birimi varsa
> uyarı verilir, iki değer de aynı `[K#]`'in medya özetinde geçmiyorsa.
> **H1-TEKRAR.** H1 ile herhangi bir özet maddesinin sözcük örtüşmesi ≥0,6 ise uyarı
> verilir.
> Üçü de **Rev 30** kanalına uyarı gönderir, derlemeyi durdurmaz. Rapor insan incelemesi
> olmadan yayımlanıyor; durdurmak, yöneticiye o sabah hiç rapor gitmemesi demek.

### Uygulama listesi — Revizyon 23

| # | Dosya | Değişiklik | Kabul (ekran görüntüsü) |
|---|---|---|---|
| R23-P0-1 | `enrich.py` | Başlık `label`'dan | **(S)** 23 Eylül brifingi, 1440px: G9'un başlığı "Lynx XM30 prototip teslimi"; izleme listesindeki aynı adlı bağlantı bu başlığa iner |
| R23-P0-2 | rapor promptu | Kur, H1 ve özne cümleleri | Sonraki 3 raporda **(P)** KUR ve H1-TEKRAR uyarısı gelmez |
| R23-P1-1 | `build.py` | Üç kural | 23 Eylül yeniden derlendiğinde **(P)** "KUR: SAN CUAS 1,5 milyar $ ↔ özet 1,74" ve "H1-TEKRAR: özet 1" uyarıları gelir |

**Yapılmayacak:** kur çevirisini build'e yaptırmak (build ağa çıkmaz).

---

## Revizyon 24 — yöneticinin ilk ekranı

**Hedef.** Telefonda yöneticinin ilk ekranında özet olsun, üstveri değil.
**Dosyalar.** `assets/app.css`, `build.py` (tablo kartı), `scripts/check_reports.py`.
**Build kuralı.** İLK-EKRAN.

### R24.0 — Tanı

375×812'de ilk 470 piksel içerikten önce geliyor (F-15). İlk ekrana 5 özet maddesinden
2'si sığıyor. Ray tek sütunda özetin üstüne yığılıyor. Rev 6: **dönüş kromu değiştirir,
metin bloğunu asla.**

### R24.1 — Karar

- 920px'in altında ray, özetin arkasına (Portföy'den önce) taşınır.
- Çip şeridi tek satıra iner, taşarsa yatay kaydırılır. Yapışkan değildir.
- Mobil kartın üçüncü alanı "İzlenecek" etiketini taşır.

### Build kuralı — İLK-EKRAN

> `check_reports.py` 375×812'de brifingi açar ve **(A)** özetine ekran görüntüsünü ekler.
> `h2#yonetici-ozeti` üst kenarı ≤300px ve özetin 4. maddesinin alt kenarı ≤812px
> olmalı. Olmazsa **Rev 30** kanalına uyarı gider.

### Uygulama listesi — Revizyon 24

| # | Dosya | Değişiklik | Kabul (ekran görüntüsü) |
|---|---|---|---|
| R24-P0-1 | `assets/app.css` | Ray `order` ile özetin arkasına | **(S)** 375×812: ilk ekranda YÖNETİCİ ÖZETİ başlığı ve en az 4 madde; Oyuncular ilk ekranda yok. **(S)** 1440: ray solda, yerinde |
| R24-P0-2 | `assets/app.css` | Çipler tek satır | **(S)** 375px: çipler tek satırda |
| R24-P1-1 | `assets/app.css`, `build.py` | Kart etiketi | **(S)** 375px: her kartın üçüncü alanının üstünde "İZLENECEK" |
| R24-P1-2 | `check_reports.py` | İLK-EKRAN | **(A)** 375×812 görüntüsü; ray bilerek geri taşındığında **(P)** uyarı |

**Yapılmayacak:** rayı mobilde gizlemek; üçüncü bir yapışkan katman eklemek.

---

## Revizyon 25 — Genel: süzgeç kapısı, kategoriler, çeviri maliyeti

**Hedef.** Adı olan kategoriler konu vaatlerini tutsun, ve hiçbir kalem sessizce
düşürülmesin.
**Dosyalar.** `scripts/collect_news.py`, `build.py` (kategori görünen adı), Drive'daki
`kaynaklar.json` (değişiklik yok, yalnızca okundu).
**Build kuralları.** SİLME-YOK · İPUCU-YOK.

### R25.0 — Kapı geçilmedi

content.md'nin "536 → 208" rakamı süzgeci yalnızca Genel'e uyguluyor. Süzgeç **her
kaynağa** uygulandığında 23 Eylül'de **405 kalem elenir, 131 kalır**. Elenenlerin 77'si
adı olan kategorilerden gelir.

Bu 405 kalemden sabit tohumla (`20260923`) 100'lük bir örneklem çekildi
(`review/filtre-orneklem-100.tsv`). Sonucu beklenen şartı bilmeyen taze bir alt ajan
değerlendirdi: **İLGİLİ 49 · SINIRDA 23 · İLGİSİZ 28.** Şart ≤2 idi.

Elenen ilgili kalemlerden örnekler: günün manşeti (*"Morana statt Archer…"*), Norveç'in
WiSENT 2 siparişi, PGZ'nin geleceği tartışması.

**Rev 0'ın NOT'u yerinde kalıyor ve artık bir ölçümü var.** S1 uygulanmayacak.

### R25.1 — Süzgeç düşürüyor. Tutmanın maliyeti

`collect_news.py:288-294`: notunda `filtre` yazan kaynaklarda süzgeçten geçemeyen kalem
`continue` ile atlanıyor. Kalem toplanmıyor, yazılmıyor, aranamıyor. Bu, Rev 0'ın
"hiçbir kalem silinmez" sözleşmesine aykırı.

**Karar:** süzgeç düşürmez, **işaretler** (`savunma_terimi: false`). Kalem Genel'in kapalı
tam dökümünde durur ve aranabilir.

**Maliyet ölçümü (23 Eylül).** Drive'daki `kaynaklar.json`'da 126 kaynağın 9'u filtre
notlu: Trend.az, Report.az, Dawn, AA güncel, AA analiz, Al Jazeera, Al Arabiya, Arab News,
Middle East Monitor. Dokuz akış bugün okundu. 48 saatlik pencerede süzgecin düşüreceği
kalem sayısı **226**, geçen kalem 13. Al Arabiya boş döndü, yani bu bir alt sınır. Ortalama
başlık uzunluğu 69 karakter.

| | |
|---|---|
| Günde yeni başlık | ~200–350 (akışlar 48 saatten azını tutuyor, bu yüzden çoğu her gün yeni; yedek ikinci çalıştırma üst ucu artırır) |
| Çağrı | `translate_news.py`, 60'lık partiler: günde **4–6 `claude -p` çağrısı** |
| Çağrı başına jeton | girdi ~2,1 bin (prompt ~600 + 60 başlık ~1.500), çıktı ~2,4 bin |
| API karşılığı (Sonnet 5: 2 $ / 10 $ milyon jeton) | günde **~0,11–0,17 $**, ayda ~3,5–5 $. Claude Code CLI'nın her çağrıya eklediği sabit sistem istemi ölçülmedi; o eklenince tahmin **günde ≤0,30 $, ayda ≤10 $** |
| **Gerçek nakit maliyet** | **~0 $.** Çeviri API anahtarıyla değil abonelik jetonuyla çalışıyor (`translate_news.py:3`). Gerçek bedel abonelik kotasından günde 4–6 ek çağrı |

Özetler hariç (müşterinin sınırı).

Karar müşterinin: bu kalemler (a) çevrilsin mi, (b) özgün dilinde aranabilir mi kalsın?
Her iki seçenekte de kalem düşürülmez.

### R25.2 — Kategoriler

- **S2** `SOURCE_HINTS` kalkar.
- **S3** Çıplak dron kelimeleri C-UAS'tan çıkar ve "Deniz ve İnsansız Sistemler"e gider.
- **S6** İhale kümesi tedarik olayına özgü ifadelerle sınırlanır.
- **S8** Kategori başına "yalnızca ipucuyla gelen" ve "hiçbir kelimeye değmeyen" sayıları
  **(A)** özetine yazılır.

### R25.3 — Rakip Duyuruları → "Oyuncu Duyuruları"

Kapsam izlenen 64 oyuncu. Ad **"Oyuncu Duyuruları"**. "Oyuncu" Rev 18'de bir gözlem
olarak tanımlandı, bir sınıflandırma olarak değil. "Duyuru" da S4'ün kuralını
adlandırıyor: öznesi oyuncunun kendisi olan eylem.

- "Oyuncu Hareketleri" elendi, çünkü "hareket" iplik sayfasında zaten kullanılıyor.
- "Şirket Haberleri" elendi, çünkü roster'la bağı yok.

Veri anahtarı değişmez (Rev 2 emsali). **S4** Rev 21'in alias'lı eşleştiricisini kullanır
(← R21-P1).

### Build kuralları — R25

> **SİLME-YOK.** `collect_news.py` okuduğu ve zaman penceresine giren her kalemi yazar.
> Kaynak başına `okunan == yazılan` eşitliği **(A)** özetinde tablo olarak basılır. Eşitlik
> bozulursa iş kırmızıya döner ve **Rev 30** kanalına uyarı gider.
> **İPUCU-YOK.** Kategori ataması yalnızca başlıktaki kelime eşleşmesinden gelir.
> "Yalnızca ipucuyla gelen" sayısı >0 ise **Rev 30** kanalına uyarı gider.

### Uygulama listesi — Revizyon 25

| # | Dosya | Değişiklik | Kabul (ekran görüntüsü) |
|---|---|---|---|
| R25-P0-1 | `collect_news.py:293` | `continue` → işaretle | **(A)** SİLME-YOK tablosunda 9 filtre notlu kaynağın okunan ve yazılan sayısı eşit. **(S)** medya takibinde Trend.az'dan savunma dışı bir başlık arandığında bulunuyor |
| R25-P0-2 | `collect_news.py` | S2 | **(S)** medya takibinde C-UAS bölümünde "Tournai" ve "Zipline" yok |
| R25-P0-3 | `collect_news.py` | S3, S6 | **(S)** C-UAS bölümünde DroneXL satırı yok; İhale'de "Grönland Güvenlik Anlaşması" yok |
| R25-P1-1 | `build.py` | Görünen ad | **(S)** medya takibinin kategori rayında "Oyuncu Duyuruları"; "Rakip Duyuruları" hiçbir yerde yok |
| R25-P1-2 | `collect_news.py` | S4 (← R21-P1) | **(S)** "Hanwha mühimmat yatırımını…" Oyuncu Duyuruları altında |
| R25-P1-3 | `collect_news.py`, `build.py` | S8, İPUCU-YOK | **(A)** kategori başına iki sayı; "ipucuyla gelen" sütunu 0 |
| R25-P2-1 | — | İsabet yeniden ölçülür | Bir inceleyici **(S)** her kategorinin ilk 20 satırının görüntüsünden isabeti sayar; hedef ≥%70 |

**Yapılmayacak:** S1; sözlüğü büyütüp kapıyı yeniden denemek; S7.

---

## Revizyon 26 — çeviri: cümle düzeni ve üç dedektör

**Hedef.** Başlıklar tek düzende olsun ve hiçbir başlık bir önermesini ya da konuşanını
sessizce kaybetmesin.
**Dosyalar.** `scripts/translate_news.py` (prompt, sözlük, dedektörler), Drive'daki
`kaynaklar.json` (`dil` düzeltmesi; müşteri yapar).
**Build kuralı.** ÇEVİRİ-DEDEKTÖRÜ.

### R26.0 — Tanı

İki prompt kuralı çelişiyor: "Türkçeyse aynen ver" ve "her kelime büyük". En tehlikeli
kusur sınıfı sessiz eksiltme ve atıf silme.

### R26.1 — Karar: cümle düzeni

- `translate_news.py:48` cümle düzenine döner. Çelişki böylece kalkar.
- **Ö5 tersine döner:** her kelimesi büyük harfle çıkan bir çeviri kusur işareti sayılır.
- **Ö1** (önerme koruma) ve **Ö2** (atıf koruma) prompt'a eklenir.
- **Ö3** sözlük eklemeleri yapılır.
- **Ö6 ucuz yarısı:** "Defense Studies" için `dil: "id"` Drive'da düzeltilir.
- **Geçiş:** canlı pencere yeniden çevrilir. Arşivdeki günler eski düzende kalır. Rev 4:
  tekdüzelik blok içinde zorunludur, sayfalar arasında değil.

### Build kuralı — ÇEVİRİ-DEDEKTÖRÜ

> Her çıktı yayımlanmadan önce üç sınamadan geçer: **düzen** (muaf olmayan kelimelerin
> >%60'ı büyük harfle başlıyor), **uzunluk** (çeviri < özgün × 0,6), **atıf** (özgünde
> says/according to var, çeviride dedi/göre/: yok). Biri tutarsa kalem bir kez yeniden
> çevrilir. İkinci deneme de tutarsa özgün başlık basılır.
> **(A)** özetine sınama başına yakalanan sayısı ve content.md §2'nin 16 kusurlu kalemiyle
> koşan sabit testin sonucu yazılır. Bir günde özgün bırakılan başlık sayısı >10 ise
> **Rev 30** kanalına uyarı gider.

### Uygulama listesi — Revizyon 26

| # | Dosya | Değişiklik | Kabul (ekran görüntüsü) |
|---|---|---|---|
| R26-P0-1 | `translate_news.py` | Cümle düzeni, Ö1, Ö2 | **(S)** medya takibi, 1440px, Öne çıkanlar: 12 satırın hepsi cümle düzeninde |
| R26-P0-2 | `translate_news.py` | ÇEVİRİ-DEDEKTÖRÜ | **(A)** sabit testte 16 kalemden en az 7'si yakalanmış; "…exiting power procurement" satırının yeniden çevirisi "çekil" kökünü içeriyor |
| R26-P1-1 | sözlük | Ö3 | **(S)** medya takibinde "Hürmüz" araması "Hürmüz Boğazı" gösterir, "Hormuç" göstermez |
| R26-P1-2 | `translate_news.py` | Canlı pencere yeniden çevrilir | **(S)** 23 ve 24 Eylül medya sayfalarının her birinde tek düzen |
| R26-P1-3 | Drive `kaynaklar.json` | Ö6 ucuz yarısı | **(S)** "KF-21 Berbagi dengan F-16V?" satırının çevirisinde KF-21 özne |
| R26-P2-1 | `translate_news.py` | Ö6 tamamı | **(A)** özette "dil etiketiyle metin uyuşmuyor: n" |
| R26-P3-1 | `translate_news.py` | Ö7 | Ertelendi; açılma şartı yukarıda (sıralama teyidi) |

---

## Revizyon 27 — iplik sayfası: ne oldu, şimdi ne durumda

**Hedef.** İplik sayfası iş 2'nin sorusunu ilk satırda cevaplasın ve okunan güne geri
götürsün.
**Dosyalar.** `build.py` (iplik sayfası, `thread_slug`), `assets/app.js` (daybar
`?g=`), `assets/app.css`.
**Build kuralları.** İPLİK-DURUM · SLUG.

### R27.0 — Tanı

- Günün durum cümlesi iplik sayfasına ulaşmıyor.
- Satırlar bağlantı ama öyle görünmüyor.
- Güne dönüş yok (F-09).
- "4 hareket" yazıyor ama 5 satır var (F-10).
- Slug'lar yarım kelimeyle bitiyor ya da tarih taşıyor.

### R27.1 — Karar

- Başlığın altında en son hareketin durum cümlesi, tarihiyle.
- Her hareket satırı o günün cümlesini taşır.
- İplikte daybar olur, gelinen günü gösterir (`?g=`).
- Açılış satırı ayrı biçimde çizilir: "açıldı" jetonu var, bağlantısı yok.
- Satırlar bağlantı gibi görünür.
- Slug'lar etiketten türer, kelime sınırında kesilir, tarih içermez. Eski adresler
  yönlendirilir.

### Build kuralları — R27

> **İPLİK-DURUM.** Son hareketinde durum cümlesi olan bir ipliğin sayfasında
> `.thread-status` yoksa **Rev 30** kanalına uyarı gider.
> **SLUG.** Slug yarım kelimeyle bitemez ve tarih içeremez. Yönlendirmesi eksik eski
> slug varsa **Rev 30** kanalına uyarı gider.

### Uygulama listesi — Revizyon 27

| # | Dosya | Değişiklik | Kabul (ekran görüntüsü) |
|---|---|---|---|
| R27-P0-1 | `build.py` | Durum satırı + satır cümleleri | **(S)** XM30 ipliği, 375px: başlığın altında "Prototip teslim edildi, şart hâlâ tanımlı değil. · 23 Eylül" |
| R27-P0-2 | `build.py`, `app.js` | Daybar | **(S)** brifingden açılan iplik sayfasının tepesinde "23 Eyl · Çar" daybar'ı |
| R27-P1-1 | `app.css` | Bağlantı görünümü; açılış satırı ayrı | **(S)** 4 satır altı çizili, açılış satırı "AÇILDI" jetonlu ve altı çizili değil |
| R27-P2-1 | `thread_slug` | Slug + yönlendirme | **(S)** eski `…-mut.html` adresi açıldığında adres çubuğunda yeni slug |

---

## Revizyon 28 — izlenen oyuncunun kaynağı düştüğünde

**Hedef.** İnanç değiştiren tek arıza okuyucuya tek satırla söylensin. Başka hiçbir
arıza söylenmesin.
**Dosyalar.** `data/rakipler.json` (`kaynak` alanı), `build.py` (brifing rayı, Kaynaklar
sayfası).
**Build kuralı.** KANIT-BOŞLUĞU.

### R28.0 — Tanı

23 Eylül'de Elbit ve Northrop'un kendi kaynakları yanıt vermedi (F-04). Bu bilgi
yalnızca Kaynaklar sayfasında soluk bir satırdı.

### R28.1 — Karar

- Her oyuncunun `kaynak` alanı olur.
- Kesişim boş değilse Tarama satırının altında tek satır: *"Elbit Systems ve Northrop
  Grumman'ın kendi duyuruları bugün okunamadı."* Satırda neden, sayı ya da renk yok.
- Kesişim boşsa satır basılmaz (Rev 9: alışkanlığın kırılması sinyalin kendisidir).
- Kaynaklar sayfasındaki "yanıt vermedi" sütunu kalkar; satır soluk kalır (Rev 19).

### Build kuralı — KANIT-BOŞLUĞU

> Satırın tek tetiği `failed_sources ∩ {r.kaynak}` kesişimi. Ajanın beyanı tetik olamaz
> (Rev 14). Satır basıldığı gün **Rev 30** kanalına da bildirim gider: operatörün kaynağı
> onarması gerekebilir.

### Uygulama listesi — Revizyon 28

| # | Dosya | Değişiklik | Kabul (ekran görüntüsü) |
|---|---|---|---|
| R28-P0-1 | `rakipler.json` | `kaynak` alanı | **(S)** /haberler/…-kaynaklar.html: Elbit ve Northrop satırlarının yanında adları |
| R28-P0-2 | `build.py` | KANIT-BOŞLUĞU satırı | **(S)** 23 Eylül yeniden derlendi, 375px: Tarama altında iki adlı tek satır; kesişimi boş bir günde satır yok. **(P)** o gün bildirim |
| R28-P1-1 | `build.py` | Sütun kalkar | **(S)** Kaynaklar sayfasında "yanıt vermedi" yazısı yok |

---

## Revizyon 29 — görsel sistem ve hijyen

**Hedef.** Kanun metne uysun: her sınır tek mekanizma, her yazı boyutu bir belirteç.
**Dosyalar.** `assets/app.css`, `assets/app.js` (bildirim kartı), `build.py` (masthead
metni), `scripts/check_reports.py`.
**Build kuralları.** L1-DOLGU · ÇİZGİ-KONTRAST · TİP-BELİRTECİ.

### R29.1 — Çizgiler (F-12)

Bölüm sınırı çizgisi (`--rule-2`) ≥3:1'e çekilir. İnce ayraçlar (`--rule`) kalır. Yeni
belirteç eklenmez, yalnızca değer değişir.

### R29.2 — Yazı boyutları

Yaklaşık 20 değer 7 belirtece iner: `--fs-meta 11` · `--fs-small 13` · `--fs-body 17` ·
`--fs-lead 18.5` · `--fs-h3 20` · `--fs-h2 23` · `--fs-h1 34`.

### R29.3 — Küçük maddeler

- **F-13:** ölü koruma `:root` olur. Tema anahtarı yapılmayacak (Rev 0 NOT).
- **F-03/F-14:** kart ilk ziyarette endnav'ın üstünde, akış içinde görünür. Footer'a 96px
  alt boşluk eklenir.
- **F-07:** masthead'e "· brifing" / "· medya takibi" eklenir.
- **F-08:** daybar çipine sayı eklenmez (88px yapışkan bütçe).
- **F-11:** Oyuncular ve İzleme dizini brifingin ızgarasına geçer.

### R29.4 — Özet kutusunun kenar çizgisi kalkar (müşterinin kararı)

PRODUCT.md'nin kanunu olduğu gibi kalıyor: *sınır çizgi alır, durum renk, içerik büyüklük
— asla ikisi birden.* Rev 0'ın L1 tanımı ("dolgu + kenar") bu kanunla çelişiyordu. Karar
kanun lehine: yönetici özeti yalnızca `--paper-2` zeminini taşır, 3px'lik `--brand` sol
kenar kalkar.

Özet kutusu artık tek bir mekanizmayla, zeminiyle ayrılıyor. Rev 0'ın gerekçesi ("yönetici
özeti görsel olarak ayrılmıyordu") zeminle karşılanmaya devam ediyor.

**Tersine dönüş kaydı:** Rev 0 → R29.4. DECISIONS.md › *Reversals* listesine 9. madde
olarak eklenecek: "L1 dolgu + kenar — Rev 0 belirledi, R29.4 kanuna uydurmak için kenarı
kaldırdı."

### Build kuralları — R29

> **L1-DOLGU.** Zemin belirteci taşıyan hiçbir öğe aynı anda `border-left` taşıyamaz.
> **ÇİZGİ-KONTRAST.** Build CSS belirteçlerinden `--rule-2`'nin iki temada da zemine
> karşı oranını hesaplar; <3:1 ise uyarı verilir.
> **TİP-BELİRTECİ.** `font-size:` yalnızca `var(--fs-*)` alabilir.
> Üçü de **(A)** özetinde bir satır, ihlalde **Rev 30** kanalına uyarı.

### Uygulama listesi — Revizyon 29

| # | Dosya | Değişiklik | Kabul (ekran görüntüsü) |
|---|---|---|---|
| R29-P0-1 | `app.css` | Özet kutusunun kenarı kalkar | **(S)** 375 ve 1440: YÖNETİCİ ÖZETİ kutusu zeminli, solda koyu yeşil çizgi yok |
| R29-P1-1 | `app.css` | `--rule-2` ≥3:1 | **(S)** 1440: bölüm başlıklarının üstündeki çizgi açık ve koyu temada seçilebilir. **(A)** ÇİZGİ-KONTRAST satırında iki oran ≥3 |
| R29-P1-2 | `app.js`, `app.css` | F-03/F-14 | **(S)** depolama temiz, ilk ziyaret, 375px: brifingin sonunda bildirim kartı; kart açıkken footer zili görünür |
| R29-P2-1 | `build.py` | F-07 | **(S)** masthead'de "· brifing" |
| R29-P2-2 | `app.css` | F-13 | Görsel değişiklik yok; **(A)** L1-DOLGU ve TİP-BELİRTECİ satırları yeşil |
| R29-P3-1 | `app.css` | Yazı belirteçleri | **(A)** TİP-BELİRTECİ: 0 ihlal |
| R29-P3-2 | `app.css` | F-11 | **(S)** 1440: brifing ve /oyuncular.html'de içerik sol kenarı aynı x noktasında |

---

## Revizyon 30 — operatör uyarı kanalı

**Hedef.** Uyarı veren her build kuralı, uyarısını operatörün telefonuna push olarak
iletsin. Tek bir okuyucu bile bu uyarıları görmesin.
**Dosyalar.** `worker/worker.js` (yeni `/alert` uç noktası, operatör aboneliği), `sw.js`
(uyarı bildirimini gösterme), `scripts/uyari.py` (yeni, ortak yardımcı), `build.py`,
`scripts/collect_news.py`, `scripts/translate_news.py`, `scripts/check_reports.py`,
`.github/workflows/{build,collect-news,pull-drive}.yml`.
**Build kuralı.** OPERATÖR-YALNIZ.

### R30.0 — Tanı: bugün tek bir push var, o da okuyuculara gidiyor

`worker.js`'in `/notify`'ı KV'deki her `sub:` aboneliğine içeriksiz bir push gönderiyor.
Servis çalışanı (`sw.js:26`) sitenin rapor listesini okuyup "yeni rapor" duyuruyor. Bu
kanal MKE yöneticilerine gidiyor. Build uyarısını oraya göndermek, PRODUCT.md'nin çekirdek
kuralını en yüksek sesle çiğnemek olurdu: üreticinin iç durumu okuyucunun telefonunda
görünürdü.

PRODUCT.md "operatöre doğrudan" diyor ve "eşik alarmı henüz kurulmadı" diye yazıyor. Bu
revizyon o alarmın da kanalı.

### R30.1 — Karar

- **Ayrı abonelik anahtarı.** Operatörün cihazı `op:` önekiyle kaydedilir. Kayıt
  `/subscribe?rol=operator` üzerinden, `NOTIFY_SECRET`'tan ayrı bir `OPERATOR_SECRET` ile
  yapılır. Okuyucu kaydı `sub:` önekinde kalır.
- **Yeni uç nokta `/alert`.** Yalnızca `op:` anahtarlarına gönderir. `/notify`
  değişmez.
- **İçerik şifreli payload'la gider** (Web Push, RFC 8291). Okuyucu push'ları içeriksiz
  kalır. Uyarı metni sitenin herkese açık bir dosyasına **yazılmaz**, çünkü site herkese
  açık.
- **Bir çalıştırma, bir push.** Her iş (build, collect, pull-drive) uyarılarını
  `uyari.py` ile toplar ve sonunda tek bir push gönderir: *"DEFINTEL · 23 Eyl · 3 uyarı:
  KUR, H1-TEKRAR, TEKRAR-MANŞET"*. Bildirime dokunulunca o çalıştırmanın Actions özet
  sayfası açılır.
- **Aynı gün aynı uyarı bir kez gider.** Tekrarı KV'de gün anahtarıyla bastırılır.
- **Kural adları sabit.** Push'ta kural adı geçer (KAPSAM-SAYI, KUR, …), böylece plan ile
  uyarı aynı dili konuşur.

**Bu kanala uyarı gönderen kurallar:** KAPSAM-SAYI, DÖRT-DURUM, ETİKET-BAŞLIK, KUR,
H1-TEKRAR, İLK-EKRAN, SİLME-YOK, İPUCU-YOK, ÇEVİRİ-DEDEKTÖRÜ, İPLİK-DURUM, SLUG,
KANIT-BOŞLUĞU, L1-DOLGU, ÇİZGİ-KONTRAST, TİP-BELİRTECİ, GEÇ-GELEN, TEKRAR-MANŞET,
NOKTALI-İ. Bloklayıcı iki kural (DÖRT-DURUM, SİLME-YOK) da buraya gönderir, çünkü kırmızı
bir çalıştırma da kimse bakmazsa görünmez.

### Build kuralı — OPERATÖR-YALNIZ

> `/alert` yalnızca `op:` önekli anahtarlara gönderir. `worker.js`'in testi bir `sub:` ve
> bir `op:` aboneliğiyle koşar; `sub:` bir push alırsa test kırmızıya döner. Ayrıca her
> `/alert` çağrısının yanıtı gönderilen `op:` sayısını döndürür. Sayı 0 ise (operatör
> kaydı düşmüş) iş **(A)** özetinde kırmızı bir satır basar. Bu kanalın kendi arızasını
> bildirebileceği tek yer burası.

### Uygulama listesi — Revizyon 30

| # | Dosya | Değişiklik | Kabul (ekran görüntüsü) |
|---|---|---|---|
| R30-P0-1 | `worker.js` | `op:` kaydı, `/alert`, şifreli payload | **(P)** operatör telefonunda "DEFINTEL · test uyarısı". Aynı dakikada okuyucu olarak kayıtlı ikinci telefonun bildirim ekranı boş |
| R30-P0-2 | `sw.js` | Payload'lı push'u göster, dokununca Actions sayfasını aç | **(P)** bildirim metninde kural adları; dokunulunca **(A)** özet sayfası açılıyor |
| R30-P0-3 | `uyari.py` + üç iş akışı | Toplama, çalıştırma başına tek push, aynı gün tekrar bastırma | Aynı uyarıyı üreten iki derlemeden sonra telefonda **(P)** tek bildirim |
| R30-P1-1 | `worker.js` testi | OPERATÖR-YALNIZ | **(A)** "OPERATÖR-YALNIZ: sub 0 push · op 1 push" satırı yeşil |

**Yapılmayacak:**
- Uyarıyı sitede herkese açık bir dosyaya yazmak.
- Okuyucu kanalını paylaşmak.
- Bir durum sayfası açmak (PRODUCT.md: planlanmıyor).
- Her uyarıya ayrı push göndermek (alarm yorgunluğu, Rev 9: her zaman ateşleyen kanal
  sıfır bilgi taşır).

---

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

## Revizyon 33 — yabancı adlarda noktalı İ

**Hedef.** Büyük harfe çevrilen yabancı adlar kendi dilinin harfleriyle yazılsın.
**Dosyalar.** `build.py` (kaynak adı yardımcısı, medya satırı, Kaynaklar sayfası),
`assets/app.css` (değişiklik yok, doğrulama için).
**Build kuralı.** NOKTALI-İ.

### R33.0 — Tanı

Sayfa `<html lang="tr">`. `.clip-meta` (`app.css:1153`) `text-transform: uppercase`
taşıyor. Tarayıcı Türkçe büyük harf kuralını uyguluyor ve `i` → `İ` oluyor. 23 Eylül
medya takibinde: **"UNMANNED AİRSPACE"**, **"DEFENSE DAİLY"**. Yabancı her kaynak adında
`i` varsa aynı şey oluyor. Türkçe etiketler ("MEDYA TAKİBİ") doğru, çünkü onlarda
istenen şey bu.

### R33.1 — Karar

- Kaynak adları tek bir yardımcıdan (`src_name()`) geçer. Yardımcı, kaynağın ülkesi TR
  değilse adı `<span lang="en">` ile sarar. Tarayıcı o zaman İngilizce büyük harf kuralını
  uygular.
- Aynısı büyük harfe çevrilen bir alanda duran her yabancı özel ad için geçerli (ör.
  kaynakça jetonları, oyuncu adları).
- CSS'e dokunulmaz. Büyük harf dönüşümü doğru; yanlış olan dil bilgisi.

### Build kuralı — NOKTALI-İ

> Derlenmiş HTML'de `text-transform: uppercase` taşıyan sınıfların (liste `app.css`'ten
> türetilir) içinde, `lang` özniteliği olmadan duran ve ülkesi TR olmayan bir kaynağın adı
> bulunursa **Rev 30** kanalına uyarı gider. Build, sayfanın ilk 10 örneğini **(A)**
> özetine yazar.

### Uygulama listesi — Revizyon 33

| # | Dosya | Değişiklik | Kabul (ekran görüntüsü) |
|---|---|---|---|
| R33-P0-1 | `build.py` `src_name()` | `lang="en"` sarmalı | **(S)** medya takibi, 1440px, Öne çıkanlar: "UNMANNED AIRSPACE", "DEFENSE DAILY" noktasız I ile; "ANADOLU AJANSI" değişmemiş |
| R33-P0-2 | `build.py` | Kaynakça ve diğer büyük harfli alanlar | **(S)** /haberler/…-kaynaklar.html: yabancı adlarda noktalı İ yok |
| R33-P1-1 | `build.py` | NOKTALI-İ | Sarmal bilerek kaldırıldığında **(P)** "NOKTALI-İ" uyarısı |

---

## Açık — müşterinin kararı gerekiyor

1. ~~**Tutulan savunma dışı başlıklar çevrilsin mi?**~~ **Karar (müşteri, 23 Eylül): evet,
   yalnızca başlık çevrilir, özet yok.** (R25.1) Nakit maliyeti ~0 $; bedeli abonelik
   kotasından günde 4–6 ek çağrı.
2. **Aselsan–Roketsan: çerçeve sorusu.** Ajan kalemi görseydi brifinge alır mıydı? Bu,
   DECISIONS'taki Türk emsal çerçeve sorusu ve MKE'ye gider. Rev 31 yalnızca ajanın kalemi
   görmesini güvenceye alıyor.
