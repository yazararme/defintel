# DEFINTEL — UX incelemesi ve uygulama spesifikasyonu

Tarih: 2026-09-17 · İncelenen sürüm: `build.py` (507 satır), `assets/app.css` (693), `assets/app.js` (359),
`enrich.py` (225), `scripts/collect_news.py` (343); canlı sayfalar `/`, `/haberler/2026-09-17.html`,
`/reports/2026-09-17.html`; veri `data/news/2026-09-17.json` (528 kalem), `data/reports.json` (4 rapor).

İki okuyucu varsayılıyor:

- **Yönetici** — sabah 4 dakikası var, telefonda, tek soru soruyor: *bugün benim kararımı değiştiren bir şey var mı?*
- **Analist** — masaüstünde, günün tamamını taramak istiyor, hiçbir kalemin gizlenmesini kabul etmiyor.

Bu iki ihtiyaç çelişmiyor; şu anda aynı sayfada aynı ağırlıkta sunuldukları için ikisi de karşılanmıyor.

---

## 1. Teşhis

Sıralama etki × maliyet. Her madde tek cümle + neden önemli.

**T1 — Ürünler arası geçiş yanlış güne gidiyor.**
`masthead()` her sayfada `latest_news` ile çağrılıyor (`build.py:217, 300, 387`), yani 15 Eylül brifingini
okurken "Medya takibi"ne dokunan kişi sessizce 17 Eylül'ün kupür listesine düşüyor.
*Neden önemli:* bu bir düzen sorunu değil, bir doğruluk hatası — okuyucu yanlış günün verisiyle karar veriyor
ve fark etmiyor. Müşterinin "iki ürün arasında gidip gelmek kötü" şikâyetinin asıl sebebi bu.

**T2 — 528 kalem düz liste; sayfanın %66'sı (351 kalem) "Genel Savunma Gündemi".**
Bu kovanın tanımı gereği hiçbir kategori anahtar kelimesi tutmayan artıklar; tek başına TASS 85, Defence24 (PL) 47,
SCMP 27 kalem koyuyor ve içinde "iPhone 18 Pro Max hits Moscow black market" gibi kalemler var.
*Neden önemli:* yöneticinin ilk ekranında sinyal yok; analist de sıralaması olmayan 528 satırı tarayamıyor.
Sorun hacim değil, hacmin sıralanmamış olması.

**T3 — Bölüm başlıkları gövde metninden daha sessiz.**
`.prose h2` = 11,5px mono, `--muted`, `.kicker` = aynı; gövde ise 18px serif `--ink`.
ALARMLAR, YÖNETİCİ ÖZETİ ve GELİŞMELER, altlarındaki paragraflardan küçük ve soluk görünüyor.
*Neden önemli:* "her şey eşit derecede önemli görünüyor" şikâyetinin tam kaynağı — sayfada tipografik olarak
büyük tek şey başlık; yönetici özeti ile rakip hareketleri arasında görsel bir öncelik farkı yok.

**T4 — Telefonda masthead üç öğeyi tek `flex-wrap` satırına sıkıştırıyor.**
22px/`0.16em` wordmark + 17px tagline + mono "Medya takibi"; `@media (max-width:700px)` kuralı
`.masthead-link { margin-left: 0 }` yaparak bağlantıyı tagline'ın hemen altına/yanına düşürüyor.
*Neden önemli:* 375px'te ekranın üstünde ~110px yer kaplayan, hiçbir gezinme işlevi görmeyen bir blok;
katlamanın üstünde içerik kalmıyor.

**T5 — Kupür satırının anatomisi gürültülü ve dokunma hedefi küçük.**
`clip_html()` meta satırına dört jeton yazıyor: `kaynak · + yayın1, yayın2 · 17 Eylül 2026 · ZA`.
Tarih kalemlerin %48'inde sayfa günüyle aynı, ülke kodu okuyucuya hiçbir şey söylemiyor, `<a>` yalnızca başlığı
sarıyor (meta kardeş `<span>`), satır yüksekliği tek satırlık başlıklarda ~40px.
*Neden önemli:* her satırda sinyal ile gürültü aynı ağırlıkta; başparmakla ıskalanan bağlantılar.

**T6 — Uzun brifingden çıkış yolu yok.**
`← Geri` sayfanın en üstünde tek bir 11,5px bağlantı; ~3.000 kelimelik brifingin sonunda arşive,
önceki güne veya o günün kupürlerine dönmenin yolu yalnızca tarayıcı geri tuşu.
*Neden önemli:* PWA olarak kurulduğunda tarayıcı çubuğu da yok; okuyucu çıkmaz sokakta kalıyor.

**T7 — Alarm durumu, önemsediği yerde görünmüyor.**
Arşivde alarm = 10,5px dış çizgili rozet; brifingde = 2px sol kenarlı 15,5px paragraf.
`--watch` token'ı `:root`'ta tanımlı ama CSS'te hiçbir kural kullanmıyor.
*Neden önemli:* alarmlı gün ile temiz gün 375px'te aynı görünüyor; üç durumluk palet var, tek durum kullanılıyor.

**T8 — Tekilleştirme Latin dışı başlıkları yutuyor (veri hatası).**
`collect_news.py:100` `norm()` Latin olmayan karakterleri siliyor, dolayısıyla Korece/Çince/Kiril bir başlığın
dedupe anahtarı boş string oluyor; 17 Eylül'de tek bir Korece kalem `also[]` içine 38 başlık topladı ve
o 38 başlık sayfada hiç görünmüyor.
*Neden önemli:* "her şeyi tarıyoruz" vaadi bugün için 38 kalem eksik; ayrıca `also[]`'yu sıralama sinyali
olarak kullanacaksak önce güvenilir olması gerekiyor.

---

## 2. Bilgi mimarisi

### Karar

**Bir gün = iki yüzü olan tek dosya.** Brifing ve medya takibi ayrı ürünler değil, aynı günün analiz edilmiş ve
ham yüzü. Bunu taşıyan tek bileşen `daybar`; her iki sayfa tipinde de aynı yerde, aynı biçimde, **her zaman
okunmakta olan günün tarihiyle**. Arşiv (`/index.html`) üçüncü bir ürün değil, `daybar`'daki tarihe dokununca
açılan gün seçici.

### Bileşenler ve yerleri

| Bileşen | Nerede | İçerik | Yapışkan mı |
|---|---|---|---|
| `masthead` | Üç sayfa tipinde de en üst | Yalnızca wordmark (≥560px'te tagline) | Hayır, kayıp gider |
| `daybar` | `masthead` altında | `‹ önceki gün` · **tarih** (→ arşiv) · `sonraki gün ›` · sağda karşı ürün bağlantısı | Evet, `top: 0` |
| `devnav` (mevcut) | Brifing sayfasında `daybar` altında | G1…Gn çip şeridi | Evet, `top: 48px` |
| `catbar` (yeni, `devnav` sınıflarını yeniden kullanır) | Medya sayfasında `daybar` altında | Kategori çipleri + sayılar | Evet, `top: 48px` |
| `endnav` | Her iki sayfa tipinde `footer`'dan hemen önce | Önceki gün · karşı ürün · arşiv | Hayır |

### Mobilde hareket

```
                 ┌──────────────────────────┐
  arşiv  ◄────── │  daybar tarihi (dokun)   │ ──────► arşiv
  /index.html    └──────────────────────────┘
                   ▲                      ▲
        ‹ / ›      │                      │      ‹ / ›
   önceki/sonraki  │                      │  önceki/sonraki
        gün        │                      │      gün
                   │                      │
   /reports/D.html ├──── "Medya takibi →" ─┤
                   │                      │
                   └──── "← Brifing" ──────┤ /haberler/D.html
```

Üç kural:

1. **Karşı ürün bağlantısı her zaman aynı `D` gününe gider.** O gün için karşı sayfa yoksa bağlantı
   `<span class="daybar-link daybar-link--off">Brifing yok</span>` olarak, tıklanamaz halde render edilir —
   gizlenmez, çünkü yokluğu da bilgidir.
2. **`‹` / `›` ürün içinde gezinir**, ürün değiştirmez: brifingdeyken önceki brifing gününe, kupürlerdeyken
   önceki kupür gününe. Uç günlerde ok `disabled` olarak durur, kaybolmaz (düzen zıplamasın).
3. **Arşiv tek dokunuş uzakta** ve daima aynı yerden: `daybar`'ın ortasındaki tarih. `← Geri` gövdeden kalkar.

Yapışkan bütçe 375px'te: `daybar` 48px + bağlam şeridi (`devnav`/`catbar`) 40px = 88px, ~660px'lik görünür
alanın %13'ü. Üçüncü bir yapışkan katman eklenmez; `masthead` bilinçli olarak kaydırılıp gider.

---

## 3. 530 kalemi sindirme stratejisi

### 3.1 Makinenin elindeki sinyaller (ölçülmüş)

`data/news/2026-09-17.json` üzerinde ölçülen gerçek dağılımlar — spesifikasyon bu sayılara göre yazıldı:

| Alan | Gerçek dağılım | Sıralama değeri |
|---|---|---|
| `tier` | A 245 · B 249 · C 34 | **Yüksek.** Müşterinin kendi `kaynaklar.json` yargısı. Genel kovada TASS/SCMP/Indian Defence News'ün tamamı B/C. |
| `category` | Genel 351 · C-UAS 77 · Rakip 33 · İhale 20 · Topçu 20 · Deniz 17 · Politika 8 · Hafif 2 | **Yüksek**, ama "Genel" bir kategori değil, artık kovası. |
| `source` | TASS 100 · Defence24 (PL) 50 · SCMP 30 · Indian Defence News 25 | **Yüksek — ama yalnızca ceza olarak.** Tek kaynak sayfanın %19'unu yazıyor. Kaynak başına tavan tek başına en büyük kazanç. |
| `also[]` | Yalnızca 7 kalemde dolu; biri hatalı olarak 38 | **Düşük.** T8 düzeltilene kadar ≤3 ile sınırlandırılıp küçük bir bonus olarak kullanılmalı, asıl sinyal sayılmamalı. |
| `country` | US 112 · RU 105 · PL 66 · GB 36 · HK 30 | **Düşük.** Ekranda gösterilmemeli; en fazla filtre olarak. |
| `lang` | en 422 · pl 50 · de 13 · it 10 | **Sıfır.** Okuyucuya gösterilecek bir şey değil. |
| `published` | sayfa günü 252 · dün 206 · 2 gün 60 · boş 10 | **Orta.** Yalnızca "sayfa gününden eski mi" ikili sinyali olarak. |
| Brifing atıfı | 17 Eylül'de `source/2026-09-17.md` içindeki 18 URL'den **1'i** kalem URL'iyle birebir eşleşiyor, 5'i alan adı düzeyinde | **En yüksek kalite, en düşük hacim.** Günde 1-5 kalem işaretler; rozet olarak değerlidir, sıralamanın tek belkemiği olamaz. |
| Anahtar kelime isabeti | `collect_news.py` içindeki mevcut sözlük | **Kategorinin kendisi zaten bu.** Genel kovada yeni bir sözlük denendi ve işe yaramadı (bkz. 3.4). |

### 3.2 Puanlama (`build.py` içinde, yeni bağımlılık yok)

```
score  = 100  kalem URL'i o günün source/D.md dosyasında geçiyorsa   (normalize: ?#, sondaki /)
       +  25  category ∈ {MKE, C-UAS ve Hava Savunma, Topçu ve Mühimmat,
                          İhale ve Sözleşmeler, Rakip Duyuruları}
       +  10  category ∈ {Deniz ve İnsansız Sistemler, Hafif Silah ve Mayın,
                          Tedarik Zinciri, Politika ve Regülasyon}
       +  12  tier == "A"        +4 tier == "B"        +0 tier == "C"
       +   6 × min(len(also), 3)
       +   6  published == sayfa günü        +2 published dolu ama eski
       -   8 × (o kaynaktan görülen kalem sayısı - 5)   # yalnızca 5'inciden sonrası
```

Bu puanlama gerçek veriyle çalıştırıldığında ÖNE ÇIKANLAR şöyle çıkıyor (kaynak başına en fazla 2 kuralıyla):

```
155  DroneShield completes C-UAS installation on US Army Infantry Squad Vehicles   ← brifingde atıflı
 83  Leonardo unveils containerised Falcon Shield C-UAS system
 83  Moog Debuts RIwP on Boxer for Air Defence Missions at DVD 2026
 83  Hanwha and Lockheed Martin unveil new fighting vehicle at DVD 2026
 83  Rheinmetall breaks ground to expand Quebec facility
 83  Lockheed Martin receives first GM Defense-made PAC-3 MSE components
 83  Nammo CEO warns European rupture with US risks 10-year capability gap
 79  Air defence turret shown on Boxer for the first time
 …
```

Bu liste o günün brifingindeki G2, G3, G5, G6 gelişmeleriyle örtüşüyor — yani puanlama analistin elle yaptığı
seçimi bağımsız olarak yeniden üretiyor. Kabul kriteri olarak kullanılabilir.

**◆ Uygulama notu (2026-09-17, yukarıdaki blok yeniden ölçülmeli).** Yukarıdaki mutlak puanlar taslak
uygulamadan geliyor ve son satırın iki ayrıntısında ondan ayrılındı:

1. **Ceza kırpılıyor:** `- 8 × max(0, n - 5)`. Kırpılmamış `- 8 × (n - 5)` biçimi, tek kalemlik bir kaynağa
   +40 *bonus* verir; §3.1 bu sinyali "**yalnızca ceza olarak**" kullanmayı şart koşuyor, satırdaki
   `# yalnızca 5'inciden sonrası` notu da bunu söylüyor. Normatif metin kazandı.
2. **Ceza sıra bağımsız dağıtılıyor:** kalemler önce cezasız puana göre sıralanıyor, `n` o sırada sayılıyor.
   Taslak, kalemleri dosyadaki sırayla sayıyordu; hangi TASS kaleminin cezalandırılacağı rastlantıydı.

Sonuç: mutlak puanlar düşüyor (DroneShield ISV 155 → **139**, diğerleri 83 → 43) ve sıra 1 numara dışında
değişiyor. Ölçüldü: kırpılmış biçimde yukarıdaki sekiz kalemden **1'i**, kırpılmamış biçimde **4'ü** ilk 12'ye
giriyor. Yani "analistin elle yaptığı seçimi yeniden üretiyor" iddiası kırpılmış biçimde bugünkü veriyle
**doğrulanmıyor**; §3.1'in kendi kuralına uyan biçim bu olduğu için kırpılmış biçim uygulandı ve iddia burada
işaretlendi. Beraberliklerin çokluğu (kalemlerin büyük kısmı 43'te eşitleniyor) asıl sebep; ayırt edici bir
terim eklemek §3.2'yi yeniden tasarlamak olur, bu uygulamanın kapsamı değil — kararı tasarımcı vermeli.

### 3.3 Üç katmanlı açılım

| Katman | Ne gösterilir | Varsayılan | Kim için |
|---|---|---|---|
| **1 · ÖNE ÇIKANLAR** | Puana göre ilk **12** kalem, kategoriler arası, kaynak başına en fazla 2 | Açık, sayfanın ilk bloğu | **Analist.** Kupür listesine giriş noktası. |
| **2 · Kategoriler** | 7 çalışan kategori, kendi içinde puana göre sıralı | ≤20 kalemliler tamamen açık; >20 olanlar ilk 15 + `+N daha` katlaması | Analist |
| **3 · Genel Savunma Gündemi** | 351 kalem | **Kapalı `<details>`**, içinde iki alt katman (3.4) | Analist, talep üzerine |

**ÖNE ÇIKANLAR yöneticinin görünümü değildir.** Yöneticinin görünümü brifingin kendisidir: analiz edilmiş,
gerekçelendirilmiş, beş maddelik yönetici özeti. ÖNE ÇIKANLAR, analistin 528 kalemlik listeye nereden
gireceğini gösterir — tarama sırasını verir, karar vermez. Bu blok hiçbir zaman "yöneticinin telefonuna
çıkacak sinyal" diye savunulmamalı; o işi brifing yapıyor ve iki ürünü birbirinin yerine koymak, medya
takibini analiz sanmak olur.

Varsayılan render'da görünen `<li class="clip">` sayısı: **≈110** (bugün 528). Açılınca ulaşılabilen: 528.
**Hiçbir kalem sayfadan silinmiyor** — analistin taleplerinden geri adım atmıyoruz, yalnızca varsayılanı
değiştiriyoruz.

Bir kalem hem ÖNE ÇIKANLAR'da hem kendi kategorisinde görünür; tekrar kabul edilir, `also`/`id` numaralandırması
gerekmez.

### 3.4 "Genel Savunma Gündemi" kuralı (351 kalem)

Denendi ve **reddedildi:** yeni bir sanayi/program sözlüğü ile filtrelemek. Sebep tautoloji — bu kova tanımı
gereği `collect_news.py`'nin hiçbir kategori terimini tutturamadığı kalemlerden oluşuyor, dolayısıyla mevcut
sözlükle 0 kalem geçiyor; genişletilmiş bir sözlük denendiğinde 16 kalem geçti ama içinde
"Agencies spent nearly $10 billion for feds not to work in 2025" gibi kalemler vardı ve iyi kalemler elendi.
Sözlük bakım maliyeti getiriyor, isabet getirmiyor.

**Kabul edilen kural — üç satır, sözlüksüz:**

> `Genel Savunma Gündemi` hiçbir zaman varsayılan olarak açılmaz. Açıldığında iki alt bölüm gösterilir:
>
> 1. **Taramaya değer (40)** — `tier == "A"` **ve** kaynak başına en fazla **3** kalem, puana göre sıralı.
> 2. **Tam döküm (311)** — ikinci bir `<details>`, kapalı; kalan her şey, kategori içi orijinal sırayla.

Gerçek veriyle ölçülen sonuç: 351 → 40. TASS'ın 85 kalemi 0'a, SCMP'nin 27'si 0'a iner (ikisi de B/C kademesi);
Defence24 (PL) 47'den 3'e iner. Kural müşterinin kendi kaynak kademelendirmesini kullanıyor, yeni bir yargı
icat etmiyor — bu yüzden savunulabilir ve `kaynaklar.json` düzenlendiğinde kendiliğinden güncellenir.

### 3.5 Tamamen kesilenler

- **Ülke kodu** (`ZA`, `GB`, `US`) meta satırından kaldırılır — 528 satırda tekrarlanan, hiçbir karara girmeyen bir jeton.
- **`+ yayın1, yayın2` listesi** kaldırılır, yerine `+3` sayacı gelir.
- **Tarih**, yalnızca `published != sayfa günü` olduğunda yazılır (bugün kalemlerin ~%48'inde gereksiz tekrar).
- **`lang`** hiçbir yerde gösterilmez.
- Gövdedeki **`← Geri`** kaldırılır (işlevi `daybar`'a geçer).
- Masthead'deki **`Medya takibi`** bağlantısı kaldırılır (işlevi `daybar`'a geçer).

---

## 4. Mobil düzen spesifikasyonu (375px)

`.wrap` kenar boşluğu 18px → kullanılabilir genişlik **339px**. Newsreader 16px'te satır başına ≈44 karakter;
başlık uzunluğu p50 = 72, p90 = 91, max = 155 karakter → p50 iki satır, p90 üç satır.

### 4.1 Header yığını

```
┌─────────────────────────────────────────┐
│ DEFINTEL                                │  masthead · 48px · sticky DEĞİL
├─────────────────────────────────────────┤
│  ‹   17 Eylül · Per   ›   MEDYA TAKİBİ →│  daybar  · 48px · sticky top:0
├─────────────────────────────────────────┤
│ [G1 · Jet motorlu…] [G2 · DVD…] [G4 …]  │  devnav  · 40px · sticky top:48px
└─────────────────────────────────────────┘
```

**masthead** — tek satır, 48px. Wordmark 18px/600/`0.14em`/`--brand`. `.tagline` `@media (max-width:559px)`
altında `display:none` (≥560px'te geri gelir). `flex-wrap` kalkar; hiçbir koşulda ikinci satıra taşmaz.

**daybar** — `display:flex; align-items:center; height:48px; background:var(--paper);
border-bottom:1px solid var(--rule-2)`.
- `‹` / `›`: `<a>`, 44×44px dokunma hedefi, ikon değil karakter (`‹`/`›`, 20px, `--ink-2`), `aria-label="Önceki gün"` / `"Sonraki gün"`. Uç günde `aria-disabled="true"` + `--rule-2` rengi, DOM'dan çıkarılmaz.
- Tarih: `<a class="daybar-date" href="…/index.html">`, mono 12px, `0.06em`, `--ink-2`, `17 Eyl · Per` (uzun ay adı 375px'te taşırıyor — `tr_short()` + kısa gün adı kullanılır). Dikey dokunma alanı 44px.
- Karşı ürün: `margin-left:auto`, mono 11px, `0.08em`, uppercase, `--brand`, metin `MEDYA TAKİBİ →` / `← BRİFİNG`. Dikey dokunma alanı 44px.

**devnav / catbar** — mevcut `.devnav` yapısı korunur; `top: 0` → `top: 48px`. `.chip` padding `5px 10px` →
`8px 12px` (yükseklik 26px → 38px, `min-height:38px`). Yatay kaydırma davranışı ve `chip--group` katlaması aynen kalır.

`scroll-margin-top`: `76px` → **`100px`** (48 + 40 + 12 nefes payı). `.prose h2[id], .prose h3[id], .prose li[id],
.appendix` ve yeni olarak `.news h2.kicker` bu değeri alır.

### 4.2 Kupür satırı anatomisi

```
┌─────────────────────────────────────────┐
│ DroneShield completes C-UAS             │  1. satır: başlık
│ installation on US Army Infantry        │  serif 16px / 1.30 / --ink / 600 değil 400
│ Squad Vehicles                          │  max 3 satır, -webkit-line-clamp:3
│ UNMANNED AIRSPACE · BRİFİNGDE           │  2. satır: meta
└─────────────────────────────────────────┘  mono 10.5px / 0.05em / uppercase / --muted
```

- Tüm satır bağlantıdır: `clip_html()` meta `<span>`'ını `<a>` **içine** alır, `.clip a { display:block; padding:11px 0 }`.
  Bu, tek satırlık başlıkta bile toplam yüksekliği `21 + 14 + 22 = 57px` yapar (≥44px koşulu sağlanır).
- **1. satır** yalnızca başlık. `line-clamp:3` ile 3 satırda kesilir (kalemlerin ~%2'sini etkiler), `overflow-wrap:anywhere`
  uzun URL benzeri başlıkları taşırmaz.
- **2. satır** en fazla 3 jeton, bu sırayla: `kaynak` · `tarih (yalnızca sayfa gününden eskiyse)` · `+N (yalnızca also varsa)`.
  Brifingde atıflıysa `kaynak`'tan sonra `BRİFİNGDE` jetonu `--brand` renginde eklenir — sayfadaki tek renkli meta jetonu budur.
- `max-width: 82ch` kuralı mobilde etkisiz, masaüstünde `72ch`'e çekilir (§5).
- Satır ayracı `border-bottom: 1px solid var(--rule)` aynen kalır.

### 4.3 Bölüm başlıkları (medya sayfası)

`h2.kicker` mono 12px → **`--ink-2`**, üstünde `border-top: 1px solid var(--rule-2)`, `padding-top: 10px`,
`margin-top: 40px`. Mevcut `::after` çizgisi kaldırılır (üst çizgi onun yerine geçer, ikisi birden gürültü).
`.kicker-count` `--rule-2` → `--muted`, 11px, tabular. Katlanan kategorilerde başlık `<summary>` olur ve sağında
`▸` işareti taşır.

### 4.4 Kaydırma davranışı

- `scroll-behavior` değişmez; `goTo()` mevcut smooth scroll'u kullanır.
- Yapışkan iki katman toplam 88px; üçüncü katman eklenmez.
- `<details>` açılışında sayfa zıplamaz: `<summary>` zaten görünür olduğu için ek JS gerekmez.
- Alt taraftaki `promptbar` (kurulum/bildirim) aynen kalır; `endnav`'a `padding-bottom: 96px` verilerek
  promptbar'ın altında kalan bağlantı olmaması sağlanır.

---

## 5. Masaüstü düzeni

**Brifing sayfasında iki sütun hak etmiyor, zaten var olan yapı doğru.** `.report-grid` = `172px rail + 66ch`
ölçüsü okunabilirlik açısından doğru; brifing baştan sona okunan bir belge, tarama belgesi değil. Yapılacak tek
şey `rail`'in içeriğini zenginleştirmek: mevcut `Tarih` + `Medya takibi` bloklarına **`Bu raporda`** bloğu eklenir
(G sayısı, fırsat/risk sayısı, kaynak sayısı — hepsi `developments` ve gövdeden sayılabilir) ve `--watch`
renginde `Dış son tarih` bloğu. `devnav` çip şeridi ≥861px'te de yapışkan kalır.

**Medya sayfasında iki sütun hak ediyor** — çünkü burada iş tarama, ve kategoriler arası atlama sürekli.
`.news` sarmalayıcısı `.report-grid` ile aynı gride alınır:

```css
.news-grid { display:grid; grid-template-columns: var(--rail) minmax(0, 1fr); gap:40px; align-items:start; }
```

Sol `rail` yapışkan kategori listesi: her satır `kategori adı` + sağda `sayı`, aktif olan `--ink`, diğerleri
`--muted`; "Genel Savunma Gündemi" listenin en altında ve `--rule-2` ile ayrılmış. Bu, mobildeki `catbar`'ın
masaüstü karşılığıdır — `@media (max-width:860px)` altında rail yatay çip şeridine döner (mevcut `.rail`
kuralının aynısı).

Sağ sütunda kupür ölçüsü `max-width: 72ch` (bugün 82ch — 1080px genişlikte satır başına ~85 karakter,
tarama için fazla uzun). ÖNE ÇIKANLAR bloğu ≥1000px'te iki sütuna açılır
(`.highlights { columns: 2; column-gap: 40px; }`) — 12 kalem tek ekrana sığar, analist taramaya nereden
başlayacağını tek bakışta görür. Kategori listeleri asla çoklu sütuna alınmaz (okuma sırası bozulur).

Arşiv sayfası değişmez; `.entry` grid'i (`172px rail + içerik`) doğru çalışıyor.

---

## 6. Hiyerarşi kuralları

Mevcut token'lar dışına çıkılmaz: `--paper`, `--paper-2`, `--ink`, `--ink-2`, `--muted`, `--rule`, `--rule-2`,
`--brand` (#2F4C3B), `--ok`, `--watch`, `--alarm`; `--serif` Newsreader, `--mono` IBM Plex Mono.
Yeni renk, yeni font, yeni token yok. Üç seviye, üç ayrı *mekanizma* ile kurulur — boyut tek başına yetmez.

### Seviye 1 — DURUM (4 saniyede görülmesi gereken)
Alarm bandı, rapor başlığı, yönetici özeti, ÖNE ÇIKANLAR bloğu. (ÖNE ÇIKANLAR buradadır çünkü kendi
sayfasının giriş noktasıdır — yöneticinin sinyali olduğu için değil; bkz. §3.3.)
- **Mekanizma:** büyük serif + dolu zemin (`--paper-2`) + 3px `--brand` sol kenar.
- Başlık: serif **27px** (mobil) / **34px** (masaüstü), 600, `-0.012em`, `--ink`.
- Yönetici özeti: `<ol>` `--paper-2` zemin, `border-left: 3px solid var(--brand)`, `padding: 14px 16px`,
  madde metni serif **17,5/18,5px**, `--ink`, satır aralığı 1,5. Bugün hiçbir görsel ayrımı yok; bu blok
  yöneticinin 4 dakikasının tamamıdır.
- Alarm bandı: mevcut `.alarmbar` korunur, sol kenar 2px → **3px**, metin `--ink`.

### Seviye 2 — YAPI (bölüm sınırları ve gezinme)
`h2` bölüm başlıkları, `h2.kicker` kategori başlıkları, `daybar`, `devnav`/`catbar`.
- **Mekanizma:** mono + **çizgi**. Sınırı çizgi kurar, büyüklük değil — böylece Seviye 1 ile yarışmaz.
- Mono **12px** (mobil) / **13px** (masaüstü), 500, `0.12em`, uppercase, **`--ink-2`** (bugün `--muted` — bu
  T3'ün tek satırlık sebebi).
- `border-top: 1px solid var(--rule-2)`, `padding-top: 10px`, `margin-top: 48px`. `::after` esnek çizgi kaldırılır.
- `h3` (G başlıkları) Seviye 2 ile Seviye 3 arasında köprüdür: serif 19/20px, 600, `--ink`, çizgisiz.

### Seviye 3 — DETAY (gövde ve meta)
Prose paragrafları, tablolar, kupür başlıkları, meta satırları, kaynaklar.
- **Mekanizma:** yalnızca boyut ve renk; hiçbir çerçeve, hiçbir zemin.
- Gövde serif 17px (mobil) / 18px, `--ink`.
- Kupür başlığı serif 16px/1,30, `--ink`, 400.
- Meta mono 10,5px, `--muted`, uppercase.
- Kaynaklar (`li.source`) serif 15,5px, `--ink-2`.

### Renk kullanım kuralları

| Token | Yalnızca şunlar için | Bugünkü ihlal |
|---|---|---|
| `--brand` | Bağlantılar, wordmark, yönetici özeti sol kenarı, `gbadge`, `BRİFİNGDE` jetonu | — |
| `--alarm` | Yalnızca gerçek alarm durumu: `alarmbar`, arşivde alarmlı satırın 3px sol kenarı, `daybar`'da 6px nokta | Arşivde yalnızca soluk bir dış çizgili rozet; alarmlı gün 375px'te temiz günden ayırt edilemiyor |
| `--watch` | `deadline-chip` kenarı ve metni, İZLEME LİSTESİ `h2`'sinin üst çizgisi, rail'deki "Dış son tarih" değeri | **CSS'te hiç kullanılmıyor** — token tanımlı, kural yok |
| `--ok` | `notify[aria-pressed=true]`, kopyalandı geri bildirimi | — |
| `--muted` | Yalnızca Seviye 3 meta. **Hiçbir bölüm sınırı `--muted` olamaz.** | `h2`, `.kicker`, `.backlink` hepsi `--muted` |
| `--paper-2` | Yalnızca Seviye 1 vurgusu ve `code`. Çip zemini olarak kalabilir. | — |

**Tek cümlelik kural:** *bir öğe sınırı belirliyorsa çizgi alır, durumu belirliyorsa renk alır, içeriği
taşıyorsa boyut alır — ikisini birden asla almaz.*

---

## 7. Uygulama listesi

Kısıtlar: statik çıktı, tek komut `python3 build.py`, çerçeve yok, harici JS kütüphanesi yok, `noindex` korunur,
PWA/service worker korunur, alttaki kurulum/bildirim çubukları korunur, Türkçe arayüz metni, mevcut font ve
renk token'ları.

**◆ işaretli kabul testleri 17 Eylül verisine sabitlenmiş tek seferlik kontrollerdir, regresyon testi değildir.**
`40`, `528`, `351`, `13 gelişme` ve "DroneShield ISV ilk 12'de" gibi sayılar o günün `data/news/2026-09-17.json`
ve `source/2026-09-17.md` dosyalarından çıkıyor; ertesi gün başka veriyle bunların yanlış olması beklenir ve
bir hatayı göstermez. Uygulama sırasında bir kez doğrulanır, sonra kuralın kendisi (puanlama, tier A + kaynak
başına ≤3, kaynak başına ≤2) korunur — sayı değil.

**Service worker notu:** `sw.js` değiştirilmesine gerek yok. `assets/` altındaki dosyalar `asset()` ile hash'li
URL alıyor (`build.py:128`), `sw.js` de `/assets/` yolunu stale-while-revalidate ile servis ediyor; hash değişince
URL değişiyor ve önbellek kendiliğinden tazeleniyor. Yeni bir asset eklenirse mutlaka `asset()` üzerinden
bağlanmalı. `CACHE = "defintel-v14"` sabiti yalnızca `sw.js` kendisi değişirse artırılır.

### P0 — bugün çıkar

| # | Dosya | Değişiklik | Kabul testi |
|---|---|---|---|
| P0-1 | `build.py` → `masthead()` | İmza `masthead(up="", latest_news=None)` → `masthead(up="")`. `.masthead-link` üretimi tamamen kaldırılır; sadece wordmark + tagline kalır. Üç çağrı yeri (`build_report`, `build_news_page`, `build_index`) güncellenir. | 375px'te `.masthead-inner` tek satır, yüksekliği ≤56px; `document.querySelectorAll('.masthead-link').length === 0`. |
| P0-2 | `build.py` → yeni `daybar(kind, day, prev, nxt, cross_day, up)` | `kind ∈ {"report","news"}`. Çıktı: `‹` (prev varsa bağlantı, yoksa `aria-disabled`), `<a class="daybar-date" href="{up}index.html">{tr_short(day)} · {kısa gün}</a>`, `›`, ve `cross_day` varsa `<a class="daybar-link">MEDYA TAKİBİ →</a>` / `← BRİFİNG`, yoksa `<span class="daybar-link daybar-link--off">Brifing yok</span>`. `build_report` `report_days` komşularını, `build_news_page` `news_days` komşularını verir. Gövdedeki `← Geri` ve `news-nav` bloğu kaldırılır. | ◆ `/reports/2026-09-15.html` içindeki karşı ürün bağlantısının `href`'i `../haberler/2026-09-15.html` — bugün `2026-09-17.html`. Dört brifing ve dört kupür sayfasının hepsinde `daybar` tarihinin sayfanın kendi tarihiyle eşleşmesi. |
| P0-3 | `assets/app.css` | `.masthead` tek satır (`flex-wrap:none`, wordmark 18px, `.tagline` `@media(max-width:559px){display:none}`). Yeni `.daybar` blok (48px, sticky `top:0`, 44px dokunma hedefleri). `.devnav { top: 0 }` → `top: 48px`. `scroll-margin-top: 76px` → `100px` ve seçiciye `.news .kicker` eklenir. `.chip` padding `5px 10px` → `8px 12px`. `.masthead-link` ve `.news-nav` kuralları silinir. | 375px'te G7 çipine dokununca `#g7` başlığı iki yapışkan çubuğun altında tamamen görünür (üst kenarı viewport'un 88px altından aşağıda). Çiplerin `getBoundingClientRect().height >= 38`. |
| P0-4 | `build.py` → `clip_html(item, day, cited)` | `<a>` blok haline gelir ve meta `<span>`'ı içine alır. Meta jetonları: `kaynak`, (`published != day` ise tarih), (`also` varsa `+N`), (`cited` ise `BRİFİNGDE`). `country` ve `also` isim listesi kaldırılır. | Hiçbir `.clip-meta` 3 jetondan fazla taşımaz; `haberler/2026-09-17.html` içinde `· ZA`, `· GB`, `· US` dizgeleri hiç geçmez; 375px'te `.clip a` yüksekliği ≥44px. |
| P0-5 | `build.py` → `build_news_page()` | Üç katmanlı açılım: `<section class="highlights">` (ilk 12, kaynak başına ≤2) + kategoriler (≤20 açık `<ul>`, >20 ise ilk 15 + `<details>` içinde kalanlar) + `Genel Savunma Gündemi` kapalı `<details>`. Kategori sırası `NEWS_ORDER` korunur, Genel en sonda. | ◆ Sayfa yüklendiğinde görünür `.clip` sayısı ≤120 (bugün 528); tüm `<details>` açıldığında tam olarak 528. İlk 12 içinde DroneShield ISV kalemi bulunur. |
| P0-6 | `assets/app.css` | Hiyerarşi geçişi: `.prose h2` ve `.kicker` → mono 12px, `--ink-2`, `border-top:1px solid var(--rule-2)`, `padding-top:10px`, `margin-top:48px`, `::after` kaldırılır. Yönetici özeti için `.prose h2#ozet + ol` (veya `.summary` sınıfı) → `--paper-2` zemin + 3px `--brand` sol kenar. `.alarmbar` sol kenar 3px. | `getComputedStyle($('.prose h2')).color` artık `--muted` değil; YÖNETİCİ ÖZETİ listesinin `background-color` değeri `--paper-2`. 375px'te sayfanın ilk ekranında başlık ve özet dışında hiçbir Seviye 1 öğesi yok. |

### P1 — bu hafta

| # | Dosya | Değişiklik | Kabul testi |
|---|---|---|---|
| P1-1 | `build.py` → yeni `news_score(item, day, cited, seen)` | §3.2'deki puanlama birebir. `cited` kümesi: `source/{day}.md` içindeki URL'lerin `?#` ve sondaki `/` atılmış, küçük harfe indirilmiş hali. | ◆ `python3 build.py` çıktısı `haberler/2026-09-17.html (528 başlık · 1 brifing atıflı)` satırını basar; puanı en yüksek kalem DroneShield ISV'dir. |
| P1-2 | `build.py` → `build_news_page()` Genel kovası | §3.4 kuralı: açıldığında `Taramaya değer (N)` (tier A + kaynak başına ≤3) + kapalı `Tam döküm (351-N)`. | ◆ 17 Eylül'de `Taramaya değer` tam olarak 40 kalem; içinde hiç TASS veya SCMP kalemi yok; iki bölümün toplamı 351. |
| P1-3 | `build.py` + `assets/app.css` | Medya sayfasına `catbar` (mevcut `.devnav`/`.chip` sınıflarıyla, kategori adı + sayı) ve masaüstünde `.news-grid` + yapışkan kategori rail'i (§5). | ◆ 1200px'te sol rail görünür ve kategori sayıları doğru; 860px'te yatay çip şeridine döner; çip → ilgili `h2`'ye atlar ve başlık tamamen görünür. |
| P1-4 | `assets/app.css` | `--watch` token'ı kullanıma girer: `.deadline-chip` kenar + metin rengi, rail'deki "Dış son tarih" değeri. `--alarm`: arşivde `.entry` alarmlıysa `border-left:3px solid var(--alarm); padding-left:12px`, `.badge--alarm` dolu zemin. | `grep -c "var(--watch)" assets/app.css` ≥ 2; 375px'te alarmlı arşiv satırı kaydırmadan ayırt edilir. |
| P1-5 | `build.py` → yeni `endnav(...)` | Her iki sayfa tipinde `FOOT`'tan önce: `← {önceki gün}` · `{karşı ürün} →` · `Tüm raporlar`. `padding-bottom: 96px`. | Sayfanın en altına inildiğinde promptbar'ın örtmediği üç bağlantı görünür; her biri ≥44px yüksekliğinde. |
| P1-6 | `build.py` → rail bloğu | Brifing rail'ine `Bu raporda` bloğu: `{n} gelişme · {n} fırsat · {n} risk · {n} kaynak` (hepsi `developments` ve `body_html` sayımından). | ◆ 17 Eylül raporunda rail `13 gelişme` yazar. |

### P2 — sırada

| # | Dosya | Değişiklik | Kabul testi |
|---|---|---|---|
| P2-1 | `scripts/collect_news.py` → `norm()` / dedupe | T8 düzeltmesi: `title_key` 10 karakterden kısaysa ham `title.casefold()[:70]` kullanılır. | ◆ 17 Eylül yeniden toplandığında hiçbir kalemin `also` uzunluğu 5'i geçmez; Korece kalem sayısı 5'ten fazla olur. |
| P2-2 | `assets/app.js` + `build.py` | Medya sayfasına arama kutusu: mevcut `#q` filtresi `[data-search]` taşıyan her öğeyi süzecek şekilde genelleştirilir (`.entry` sabit seçicisi kaldırılır); `clip_html` `data-search="{başlık} {kaynak}"` yazar. Filtre etkinken kapalı `<details>` otomatik açılır. | "rheinmetall" yazınca sayfa yalnızca eşleşen kupürlere iner, `Escape` temizler; arşiv sayfasındaki mevcut davranış bozulmaz. |
| P2-3 | `build.py` → `build_news_page()` stat satırı | `16 kaynak yanıt vermedi` → `<details>` içinde kaynak adı + hata özeti listesi (`data.failures` zaten dosyada). | Tek dokunuşla 16 kaynağın adı görünür. |
| P2-4 | `build.py` → `entry_html()` | Arşivde `entry-chips` en fazla 2 etiket + `+N`; `data-search` haystack'ine gelişme etiketleri de eklenir. | 375px'te hiçbir arşiv satırı 3 satır çipe taşmaz; "Redback" araması 17 Eylül raporunu bulur. |

### Yapılmayacaklar

- Sonsuz kaydırma, sanal liste veya istemci tarafı sayfalama — 528 satır statik HTML olarak zaten ~180KB ve
  service worker önbelleğinde; karmaşıklık kazanç getirmez.
- Kalem silme. Analistin sözleşmesi "her şey burada"; yalnızca varsayılan görünürlük değişir.
- Yeni renk, yeni font ailesi, yeni token, koyu/açık tema anahtarı.
- Backend, arama indeksi, kullanıcı tercihi saklama (mevcut `localStorage` snooze anahtarları dışında).

---

## Revizyon 1 — kart gezinmesi ve son tarih

P0 sonrası müşteri geri bildirimi (4 şikâyet + 1 karşı öneri) üzerine. Canlı sayfalar yeniden incelendi.

### R1.0 — Gözlem: müşteri haklı, ama sebep sandığı sebep değil

Arşivdeki **dört kartın dördü de aynı "9 Ekim" rozetini taşıyor** — çünkü `decision_by` aynı duran dış son
tarihi (USAF pazar araştırması, G8) her gün frontmatter'a taşınıyor. Yani rozet günler arasında hiçbir fark
üretmiyor, dört farklı günü birbirinin aynı gösteriyor.

Karşı ürün bağlantısı konusunda da: **P1-5'teki `endnav` hiç uygulanmadı.** Bugün "Medya takibi →"
sayfada *tek bir yerde* var — 3.000 kelimelik brifingin en üstünde, okumaya başladığın anda kaybolan
yapışkan şeritte. Sezgiye aykırı gelmesinin sebebi bağlantının yanlış yerde olması değil, **tek yerde
olması**: okuyucu niyeti üç ayrı anda kuruyor (okumaya başlamadan önce = arşiv kartı, okurken = `daybar`,
okuyup bitirince = sayfa sonu) ve bugün bunlardan yalnızca biri karşılanıyor.

### R1.1 — `decision_by`: yalnızca brifing gövdesinde kalır

**Karar: arayüzden tamamen çekilir; `reports.json` alanı ve `status_of()` kullanımı aynen korunur.**
Bir son tarih ancak *neyin* dolduğunu ve *kimin* sahibi olduğunu gördüğünde eyleme dönüşür; `deadline-chip`
ile arşiv rozeti bu ikisini de atıp geriye yalın bir tarih bırakıyor — müşterinin "bunun neyle ilgisi var"
sorusu birebir bu. Gövdedeki ALARMLAR bloğu ise doğru işi zaten yapıyor: *"Devam eden dış son tarih: ABD Hava
Kuvvetleri'nin … yanıt süresi 9 Ekim 2026'da doluyor (bkz. G8) … [K9]"* — gelişme bağlantısı, kaynak ve durum
bir arada. "Son N gün kalınca göster" varyantı da aynı yerden düşüyor: 8 Ekim'de kart yine yalnızca "9 Ekim"
diyecek, neyin dolduğunu yine söylemeyecek; üstelik gerçekten kritik olduğu gün analist onu zaten ALARMLAR'a
yazmış olacak. Kart düzeyinde işaretlenmeye değer tek durum `alarm` — onun da rozeti zaten var. Alan veride
kalır (bugün `status` alanını besliyor); ileride gerekirse doğru biçim ham tarih değil, durum işaretidir.

### R1.2 — `entry-chips` yerine ne gelir: kart iki kapılı olur

**Karar: müşterinin modeli bu noktada daha doğru, `daybar` da yerinde kalır — ikisi çelişmiyor.**
`daybar` bir günün *içinde* hareketi çözer (gün D'desin, D'nin öteki yüzünü istiyorsun); arşiv kartı ise
güne *girişi* çözer. Bugün kartın tamamı tek bir `<a href="reports/…">` olduğu için arşivden kupür listesine
giden hiçbir yol yok — önce brifingi açıp sonra `daybar`'ı bulmak gerekiyor. İlk incelemedeki
"arşiv sadece gün seçicidir" ifadesi eksikti: **iki yüzü olan bir günün seçicisi, yüzü de seçtirmek zorunda.**

Kart artık bütünüyle tıklanabilir olmaz — iki hedefi olan bir kartta tüm yüzeyi tek hedefe bağlamak yanlış
dokunuşları garantiler. Başlık birincil bağlantıdır (375px'te 3 satır ≈ 80px'lik hedef), alt satırdaki iki
etiketli bağlantı da forku görünür kılar. Geçersiz iç içe `<a>` ve overlay hilesi gerekmez.

**Kart anatomisi — 375px**

```
┌──────────────────────────────────────────┐
│ 17 EYLÜL 2026   [ALARM]                  │  rail · mono 11,5px · --ink-2
│                                          │       alarm rozeti varsa; son tarih rozeti YOK
│ Rusya'nın jet motorlu dron kullanımı     │  h2 > a · serif 21px/600/1.25 · --ink
│ beş ayda altı katına çıktı; DVD 2026'da  │  line-clamp: 3 · BRİFİNGE GİDER
│ araç üstü kısa menzilli hava savunma…    │
│                                          │
│ Yeni ihale ya da sözleşme kararı yok.    │  p · serif 16,5px · --ink-2
│ Rusya Ağustos'ta yaklaşık 2.850 jet…     │  line-clamp: 3 · bağlantı DEĞİL
│                                          │
│ ┌──────────┐ ┌────────────────────────┐  │  entry-nav · mono 11px · 0.08em
│ │BRİFİNG → │ │ MEDYA TAKİBİ · 528 →   │  │  kenarlıklı çip · min-height 40px
│ └──────────┘ └────────────────────────┘  │  tek satıra sığar (≈283px < 339px)
└──────────────────────────────────────────┘
```

- İki çip de gerçek `<a>`; `--brand` metin, `1px solid var(--rule-2)` kenar, `padding: 10px 12px`.
- Kupür çipi **başlık sayısını taşır** (`data/news/D.json` → `unique_items`) — dokunmak için somut bir
  sebep, boş bir etiket değil.
- **Kupür listesi olmayan gün** (bugün 14–16 Eylül, dört kartın üçü):
  `<span class="entry-go entry-go--off">Medya takibi yok</span>` — kenarlıksız, `--muted`, oksuz.
  Gizlenmez: satır satır beliren/kaybolan bir affordance bozuk görünür, ayrıca kupür hattının hangi günden
  itibaren çalıştığını dürüstçe belgeler. `daybar`'daki `--off` muamelesiyle birebir aynı.
- **Masaüstü** yalnızca şunda ayrışır: `.entry` grid'i `172px rail + 1fr`'ye döner, tarih ve alarm rozeti
  sol sütunda dikey yığılır, başlık 23px olur. `entry-nav` satırı birebir aynıdır — iki çip, aynı yerde,
  `entry-summary`'nin altında. İkinci bir masaüstü düzeni tanımlanmaz.
- Silinen `entry-chips` gelişme etiketleri **`data-search` haystack'ine eklenir**, yoksa arama zayıflar
  (eski P2-4'ün yarısı buraya taşındı).

### R1.3 — `daybar` kalır, üç şey değişir

Konumu ve yapısı doğru; sorun tek başına olması. Üç düzeltme:

1. **Karşı ürün bağlantısı çip olur.** Bugün `MEDYA TAKİBİ →` 11px uppercase mono, çıplak metin — başlık
   gibi okunuyor. `1px solid var(--rule-2)` + `padding: 6px 10px` ile `.chip` diline girer; kenarlıklı şey
   basılabilir okunur, çıplak büyük harf dizisi okunmaz.
2. **`endnav` nihayet uygulanır** (P1-5 hiç çıkmamıştı). Sayfa sonunda tam cümle için yer var:
   `← 16 Eylül brifingi` · `Bu günün medya takibi · 528 başlık →` · `Tüm raporlar`. Okuyucu niyeti asıl
   burada kuruyor — brifingi bitirdiği anda.
3. **Oklar aynen kalır.** `‹`/`›` etiketle değiştirilmez: 375px'te ortada tarih için ~86px, çipler için
   ~120px gidiyor, gün adı yazacak yer yok; `aria-label` zaten doğru ve oklar ürün içinde kalıyor.
   Anlaşılırlık sorunu okun kendisinde değil, tek affordance olmasındaydı — (1) ve (2) onu kapatıyor.

### R1.4 — Bildirim düğmesi: açıkken yalnızca ikon

**Karar: abone olunduğunda ikon-only, olunmadığında etiketli. Gizlenmez, taşınmaz.**
Etiket bir kazanım metni — "böyle bir şey var, açabilirsin" — ve yalnızca kapalı durumda iş görüyor. Açıkken
düğmenin tek görevi, nadiren ve bilinçli yapılan "kapat" eylemi için bulunabilir kalmak; `--ok` tonlu zil +
`aria-pressed="true"` + `title` bunu karşılıyor. Tamamen gizlemek yanlış: iptal edilemeyen abonelik karanlık
desendir. Başka yere (footer) taşımak daha da yanlış: **kapalı** durumda keşfedilemez hale gelir ki
benimsemeyi belirleyen durum odur. Not: bu düğme aslında her sayfada değil, yalnızca `build_index()` içinde —
yani açık durumun maliyeti tek sayfada tek satır, gizlemeye değecek bir kazanç yok.
`blocked` durumu etiketini korur ("Bildirimler kapalı"), çünkü o durumun açıklanması gerekir.

### Uygulama listesi — Revizyon 1

| # | Dosya | Değişiklik | Kabul testi |
|---|---|---|---|
| R1-P0-1 | `build.py` → `entry_html(r, news_counts)` | Kart `<a class="entry">` yerine `<article class="entry">` olur; `entry-title` içine `<a href="{r['path']}">` girer. `decision_by` rozeti ve `entry-chips` bloğu tamamen silinir. Sonuna `<div class="entry-nav">` eklenir: `<a class="entry-go" href="{r['path']}">Brifing →</a>` + gün için kupür varsa `<a class="entry-go" href="haberler/{d}.html">Medya takibi · {n} →</a>`, yoksa `<span class="entry-go entry-go--off">Medya takibi yok</span>`. Gelişme etiketleri `data-search` haystack'ine eklenir. | `index.html` içinde `entry-chips` ve `Son tarih ·` dizgeleri hiç geçmez; 17 Eylül kartında `Medya takibi · 528 →`, 14/15/16 Eylül kartlarında `Medya takibi yok` görünür; kart başına tam olarak 3 `<a>` (başlık + iki çip, ikincisi devre dışıysa 2). |
| R1-P0-2 | `build.py` → `main()` / `build_index()` | `news_counts = {day: data.get("unique_items", 0) for day, data in news.items()}` hesaplanır ve `build_index(reports, version, news_counts)` üzerinden `entry_html`'e geçer. | `python3 build.py` hatasız koşar; `index.html` içindeki sayı `data/news/2026-09-17.json`'daki `unique_items` ile birebir eşleşir. |
| R1-P0-3 | `build.py` → `build_report()` | `deadline` değişkeni ve `{deadline}` yerleşimi silinir. `status_of()`, `reports.json`'daki `decision_by` ve `status` alanları **değişmez**. | Dört brifing sayfasının hiçbirinde `deadline-chip` sınıfı geçmez; `data/reports.json` içinde `"decision_by": "2026-10-09"` hâlâ vardır. |
| R1-P0-4 | `assets/app.css` | `.entry-chips`, `.entry-chips span`, `.deadline-chip` ve alarm dışı `.badge` kuralları silinir (`.badge--alarm` kalır, `.badge` temel kuralı ona hizmet ettiği için korunur). `.entry:hover .entry-title` → `.entry-title a:hover`. `.entry-title a { color: inherit; text-decoration: none }`. Yeni `.entry-nav` (flex, gap 10px, margin-top 12px, wrap) ve `.entry-go` (mono 11px, `0.08em`, uppercase, `--brand`, `1px solid var(--rule-2)`, `padding: 10px 12px`, `min-height: 40px`) + `.entry-go--off { color: var(--muted); border-color: transparent; }`. | 375px'te iki `.entry-go` tek satıra sığar ve ikisinin de `getBoundingClientRect().height >= 40`; kart gövdesinde boş alana dokunmak hiçbir yere gitmez. |
| R1-P0-5 | `assets/app.css` | `.daybar-link` çipleşir: `border: 1px solid var(--rule-2); padding: 6px 10px; border-radius: 2px`. `.daybar-link--off` kenarlığı `transparent` olur. `daybar` yüksekliği 48px'te kalır. | 375px'te `daybar` tek satır, taşma yok; `.daybar-link` görünür kenarlık taşır ve yüksekliği ≥32px. |
| R1-P0-6 | `assets/app.js` → `paint()` + `assets/app.css` | `paint()` içine `btn.classList.toggle("notify--on", state === "on")` eklenir; `label.textContent` ataması aynen kalır (erişilebilir ad korunur). CSS: `.notify--on .notify-label { position:absolute; width:1px; height:1px; overflow:hidden; clip-path: inset(50%); }` ve `.notify--on { min-width:44px; min-height:44px; justify-content:center; }`. `blocked` durumu etiketli kalır. | Abone durumda `#notify` yalnızca zil gösterir, genişliği ≤48px, `aria-pressed="true"` ve erişilebilir adı hâlâ "Bildirimler açık"; abone değilken "Bildirimler" metni görünür. |
| R1-P1-1 | `build.py` → yeni `endnav(kind, day, prev, cross_day, cross_count, up)` | Her iki sayfa tipinde `PROMPTS`'tan önce: `← {tr_date(prev)} brifingi` · `Bu günün medya takibi · {n} başlık →` (yoksa `Bu gün için medya takibi yok`, `--off`) · `Tüm raporlar`. `padding-bottom: 96px` ile promptbar'ın altında kalmaz. | Brifing sayfasının en altına inildiğinde promptbar'ın örtmediği üç bağlantı görünür; her biri ≥44px; kupür bağlantısı sayfanın kendi gününe gider. |
| R1-P1-2 | `assets/app.js` → arşiv filtresi | `querySelectorAll(".entry")` seçicisi korunur (kart `<article class="entry">` olarak aynı sınıfı taşıdığı için değişiklik gerekmez) — yalnızca regresyon testi. | Arşivde "Redback" araması 17 Eylül kartını bulur, `Escape` temizler, `#noresults` doğru çalışır. |

Not: `assets/` dosyaları `asset()` ile hash'lendiği için bu revizyonda da `sw.js` dokunulmaz.

---

## Revizyon 2 — isimlendirme

### R2.0 — Önce bir düzeltme: tagline 375px'te zaten görünmüyor

P0-3 ile `.tagline` `@media (max-width: 559px)` altında `display: none` oldu (`app.css:116`). Yani bu dizginin
telefonda wordmark'ın yanına sığma derdi kalmadı; **asıl işi artık iki yerde:** `index.html`'in `<title>`'ı
(tarayıcı sekmesi, yer imi) ve `manifest.webmanifest`'in `name` alanı (Android kurulum sayfası, uygulama
listesi, uygulama bilgisi). Karar da buna göre verilmeli: "wordmark'ın yanında ne iyi durur" değil,
**"bu şey bir uygulama listesinde nasıl adlanmalı"**.

Bu yüzden "tagline'ı tamamen at" önerisi masada değil: masthead'den atılabilir (telefonda fiilen atılmış
durumda) ama `<title>` ve `manifest.name` bir şey yazmak zorunda — çıplak "DEFINTEL" altı ay sonra ana
ekrandaki yeşil ikonun ne olduğunu kimseye hatırlatmaz. Dizgi var olmak zorunda; soru yalnızca ne diyeceği.

`noindex` açık olduğu için bu dizginin arama motoruyla işi yok. Maruz kaldığı yüzeyler: telefonun ana ekranı,
uygulama değiştirici, kurulum sayfası ve omzunun üzerinden bakan kişi. "Bağırmasın" isteği tam olarak bu
yüzeyler için anlamlı.

### R2.1 — Tagline adayları

| # | Aday | Uzunluk | Gerekçe |
|---|---|---|---|
| A | **Savunma pazarı · günlük bülten** | 30 | *Ne* + *hangi sıklıkta*, başka hiçbir iddia yok. "Bülten" Türkçe kurumsal kullanımda düz ve nötr bir kelime; ne "analiz" ne "stratejik" der, uygulama listesinde de kendini açıklar. |
| B | Günlük savunma pazarı analizi | 29 | Değerle açılıyor, iyi okunuyor; ama "analiz" iddiası sitenin iki ürününden yalnızca birini karşılıyor — medya takibi sayfası makine üretimi, orada analiz yok. Masthead tüm siteyi adlandırdığı için fazla söz vermiş olur. |
| C | Savunma pazarı günlüğü | 22 | En kısası ve en masthead'vari olanı; ama Türkçede "günlük" ismi önce *diary* çağrıştırıyor ve sıklığı A kadar net söylemiyor. |

**Ship: A — "Savunma pazarı · günlük bülten".** Orta nokta wordmark'la aynı tipografik dili konuşuyor
(`daybar` ve `clip-meta` zaten `·` ile ayırıyor), 30 karakter ≥560px'te wordmark'ın yanına rahat sığıyor,
ve kurulum sayfasında tek başına okunduğunda da anlamlı: savunma pazarı, günlük.

Kaçınılan kalıplar: "Savunma pazarı takibi" — "Medya takibi" nav etiketiyle çakışıyor, okuyucu ikisini
karıştırır. "Her sabah masanızda", "sektörün nabzı" vb. — pazarlama tonu, bu okuyucu kitlesine yanlış ses.

### R2.2 — Dizgi envanteri

Arayüzde (rapor gövdesi dışında) şirket adının geçtiği ya da geçebileceği her yer:

| Yer | Dizgi | Karar | Gerekçe |
|---|---|---|---|
| `build.py:38` `SITE_TAGLINE` → masthead `.tagline` | "MKE stratejik pazar istihbaratı" | **Değiştir** → "Savunma pazarı · günlük bülten" | R2.1. Tek kaynak; masthead ve `<title>` aynı sabitten besleniyor. |
| `build.py:612` `head(f"{SITE_NAME} — {SITE_TAGLINE}")` → `index.html` `<title>` | aynı dizgi | **Kendiliğinden düzelir** | Sabit değişince sekme başlığı da düzelir; ayrı düzenleme gerekmez. |
| `manifest.webmanifest:2` `"name"` | "DEFINTEL — MKE stratejik pazar istihbaratı" | **Değiştir** → "DEFINTEL — Savunma pazarı · günlük bülten" | En çok maruz kalan ikinci dizgi: Android kurulum sayfası ve uygulama bilgisi burayı gösterir. Ayrı dosyada olduğu için `SITE_TAGLINE` ile elle eşlenmeli — ikisi kolayca ayrışır. |
| `manifest` `"short_name"` | "DEFINTEL" | **Kalsın** | Ana ekran etiketi; wordmark sabit. |
| `build.py:161` `apple-mobile-web-app-title` | "DEFINTEL" | **Kalsın** | iOS ana ekran etiketi; aynı gerekçe. |
| `build.py:300, 541` rapor ve medya sayfası `<title>` | "… — DEFINTEL" | **Kalsın** | Şirket adı geçmiyor; sekmede günün başlığı görünüyor, doğru davranış. |
| `build.py:270` footer | "MKE'nin resmî görüşünü yansıtmaz." | **Kalsın** | Sabit. Ayrıca doğru yer: adın geçmesi *gereken* tek yüzey yasal sorumluluk reddidir. |
| `build.py:329, 337` `NEWS_ORDER` / `NEWS_CORE` içindeki `"MKE"` kategorisi | kupür sayfasında `<h2 class="kicker">MKE</h2>` olarak render olur | **Görünen etiketi değiştir** → "Doğrudan ilgili" | Bugün 0 kalem düşüyor (`data/news/2026-09-17.json`), ama `collect_news.py` `MKE_TERMS` tuttuğu gün sayfaya büyük harflerle şirket adını basar — hem de en üstteki bölüm başlığı olarak. Veri anahtarı `"MKE"` kalsın (iki dosyada birden değişmesin), yalnızca render sırasında eşlensin — tablo başlıklarında uygulanan yöntemin aynısı. |
| `sw.js:31-44` bildirim metni | rapor başlığı + tarih (+ `alarm_title`) | **Kalsın** | Şirket adı zaten geçmiyor. En savunmasız yüzey burası — bildirim kilit ekranında, toplantıda görünür — ve bugün doğru davranıyor; `body`'ye kurum adı eklemek cazip gelirse eklenmemeli. |
| `build.py:209-234` `PROMPTS` kurulum/bildirim metinleri | "DEFINTEL'i uygulama olarak ekle.", "Yeni rapor çıkınca haber verelim mi?" | **Kalsın** | Şirket adı geçmiyor, ton zaten sade. |
| `README.md` | "MKE" geçiyor | **Kapsam dışı** | Depo belgesi, arayüz değil. |

### Uygulama listesi — Revizyon 2

| # | Dosya | Değişiklik | Kabul testi |
|---|---|---|---|
| R2-P0-1 | `build.py:38` | `SITE_TAGLINE = "Savunma pazarı · günlük bülten"` | `python3 build.py` sonrası `grep -rl "stratejik pazar istihbaratı" . --include=*.html` hiçbir şey döndürmez; `index.html` `<title>` = `DEFINTEL — Savunma pazarı · günlük bülten`. |
| R2-P0-2 | `manifest.webmanifest` | `"name": "DEFINTEL — Savunma pazarı · günlük bülten"` | Chrome DevTools → Application → Manifest'te `name` yeni dizgiyi gösterir; `short_name` hâlâ `DEFINTEL`. |
| R2-P1-1 | `build.py` → `build_news_page()` | Kategori başlığı yazılırken görünen etiket eşlemesi: `NEWS_LABELS = {"MKE": "Doğrudan ilgili"}`, `NEWS_LABELS.get(name, name)`. Veri anahtarı ve `collect_news.py` değişmez. | `MKE` kategorisinde en az bir kalem bulunan bir günde kupür sayfası `<h2 class="kicker">Doğrudan ilgili` basar; `NEWS_ORDER` sıralaması (en üstte) korunur. |

Kontrol: bu üç değişiklikten sonra üretilen HTML'de "MKE" dizgisi **yalnızca** footer'daki sorumluluk reddinde
ve rapor gövdesinde geçmeli — `grep -o "MKE" index.html | wc -l` = 1.

---

## Revizyon 3 — özet açılır kapanır

Yeni alan: `summary_tr` (bugün 20 kalemde deneme, hedef ~110/gün). `title_tr` zaten 533 kalemin 519'unda var.
Özet uzunluğu: min 245, medyan **405**, max 476 karakter.

### R3.0 — Müşteri haklı; ama sebep üç katmanlı yapının çökmesi değil

Ölçüm, 390px'te (`.wrap` iç genişliği 354px):

| Satır parçası | Yükseklik |
|---|---|
| `clip-title` (16px/1.3, ~2 satır) | 42px |
| `clip-orig` (13,5px/1.3, ~2 satır) | 35px |
| `clip-summary` (15px/1.45, 405 karakter ≈ **8,3 satır**) | **180px** |
| `clip-meta` + `padding` | 36px |
| **Toplam** | **~293px** — 844px'lik telefonda içerik alanının %42'si |

110 kalem × 293px = **~32.000px** kaydırma. Özetten önce aynı 110 kalem ≈ 8.600px'ti. Yani özet, varsayılan
görünümü **3,7 katına** çıkarıyor.

Üç katmanlı yapı *kalem sayısını* yönetiyordu (528 → ~110) ve o işi hâlâ yapıyor. Özet ise yeni bir eksen açtı:
**kalem başına maliyet** (78px → 293px). Yapının bu eksende hiçbir kolu yok — dolayısıyla bu "dikişlerin
görünür olması" değil, yapının hiç ölçmediği bir büyüklüğün 3,7 kat artması. Müşteri doğru şeyi görüyor.

Ama asıl bulgu şu: **özetin değeri, ekrandaki kalem sayısıyla ters orantılı.** Yöneticinin Öne çıkanlar'daki
12 kalemi için özet *ürünün kendisidir* — İngilizce makaleyi açmamasını sağlayan şey odur; 12 × 293px ≈ 5 ekran,
kabul edilebilir. Analistin kategori taramasında ise aynı özet satır başına gürültüdür; o başlıkları
*neyi okuyacağına karar vermek için* tarıyor. Dolayısıyla doğru cevap tek tip akordeon değil:

> **Duruş hâli katmana bağlıdır:** Öne çıkanlar'da özetler **açık**, kategorilerde ve Genel kovasında **kapalı.**

Bu, "mevcut uzunluk iyi" isteğini bozmadan karşılıyor: adamın gerçekten okuduğu yerde özet tam haliyle duruyor.

### R3.1 — Mekanizma: `<details>`, kendi yazdığımız hiçbir durum yok

`<details>`/`<summary>` bedavaya veriyor: odaklanabilir tetik, Enter/Space, `aria-expanded`'ın örtük karşılığı,
ekran okuyucuda "açılır öğe, kapalı/açık" duyurusu, JS kapalıyken çalışma. Sayfada zaten iki örneği var
(`.more`, `.general`). Yeni JS yazılmaz.

### R3.2 — Dokunma çatışması: satır artık bağlantı değil, açıcıdır

Bugün `<li class="clip">` tamamen tek bir `<a href="…" target="_blank">`. İçine açıcı koymak iç içe bağlantı
demek — hem geçersiz hem belirsiz. Çatışmayı **sıklıkla** çözüyorum: özet zaten *makaleyi açmamak için* var.
Kaynak İngilizce/Lehçe/Rusça, yeni sekmede açılıyor ve okuyucuyu uygulamadan çıkarıyor; özet ise ürünün kendisi.
O hâlde satırın birincil eylemi "özeti oku", ikincil eylemi "kaynağa git"tir.

**Karar:** `summary_tr` taşıyan satır `<details class="clip">` olur; `<summary>` başlık + meta taşır, gövde
özet + kaynak bağlantısını taşır. Bu, Revizyon 1'de arşiv kartına uygulanan ilkenin aynısı — *iki hedefi olan
bir yüzey tek bağlantı olamaz* — yani site içinde tutarlı.

```
KAPALI (~78px, özetten önceki maliyetin aynısı)
┌────────────────────────────────────────────┐
│ DroneShield, ABD Ordusu ISV'lerinde C-UAS  │  summary > .clip-title
│ kurulumunu tamamladı                       │  serif 16px/1.3 · --ink · clamp 3
│ UNMANNED AIRSPACE · BRİFİNGDE           ▾  │  .clip-meta + ::after chevron
└────────────────────────────────────────────┘

AÇIK
│ …aynı başlık…                              │
│ DroneShield completes C-UAS installation…  │  .clip-orig · 13,5px · --muted
│ DroneShield, JIATF-401 programı kapsamında │  .clip-summary · 15px/1.45 · --ink-2
│ ABD Ordusu Piyade Takım Araçlarına…        │
│ ┌──────────────────┐                       │
│ │ KAYNAĞA GİT ↗    │                       │  .entry-go (Rev 1'den) · ≥40px
│ └──────────────────┘                       │
```

- **`clip-orig` duruş hâlinden çıkar, gövdeye iner.** Türkçe başlığın İngilizce eşi bir *doğrulama* öğesi,
  tarama öğesi değil; kapalı satırda 35px yer yiyor ve hiçbir tarama kararına girmiyor.
- **Chevron `clip-meta`'nın sonunda**, `--muted`, `::after` ile: `▾` kapalı, `▴` açık. Sağ üst köşede yüzen bir
  ikon değil — "burada dahası var" bilgisinin yeri meta satırıdır. Tetik `<summary>`'nin tamamı (≥68px).
- **`summary_tr` olmayan satır bugünkü `<a>` olarak kalır** — chevronsuz, tek dokunuşta kaynağa gider.
  Boş açıcı gösterilmez. İki anatomi duruşta neredeyse özdeş görünür; farkı chevronun varlığı söyler.
- `.clip > summary` ile `.more > summary` görsel olarak ayrışmalı: `.more` bir *bölüm* kontrolü
  (mono, uppercase, tam genişlik), `.clip` bir *satır*.

### R3.3 — Otomatik kapanma: hayır

Müşterinin istediği "B açılınca A kapansın" davranışı iki nedenle reddediliyor:

1. **Tarayan okuyucu karşılaştırır.** Bu sayfanın işi aynı olayın farklı kaynaklardaki hallerini (`also[]`),
   ya da "Rakip Duyuruları"ndaki beş hamleyi yan yana tartmaktır. Tek-açık kuralı karşılaştırmayı imkânsız
   kılar ve okuyucuya aynı satırı ikinci kez açtırır.
2. **Kaydırma zıplaması.** Görüş alanının *üstünde* kalan A kapanınca sayfa parmağın altında ~215px yukarı
   sıçrar — klasik akordeon hatası, uzun sayfada daha da kötü. Tek çözümü JS ile kaydırma telafisi, o da kırılgan.

Not: bu davranış artık JS'siz de mümkün — `<details name="clips">` (Chrome 120+, Safari 17.4+, Firefox 130+)
tek-açık akordeon yapar. Bilerek kullanmıyoruz; aynı zıplama sorunu onda da var. Ama **karar tek öznitelikle
geri alınabilir**: müşteri gördükten sonra ısrar ederse `name="clips"` eklemek yeterli.

Asıl cevap şu: otomatik kapanma, kapalı duruş hâlinin zaten çözdüğü bir korkuyu çözüyor. Satırlar 78px'e
indiğinde sayfa onun korktuğu gibi büyüyemez; beş özet açmak 5 × ~215px ekler, istediğinde kapatır.

### R3.4 — Alternatif (2 satır kırpma + solma) neden seçilmedi

- Özetler **iki cümle** ve ilk cümle tek başına ~200 karakter ≈ **4-5 satır**. 2 satırlık kırpma tam cümle
  ortasından, üstelik sayı ve özel ad yoğun bir metinde keser — bu tür düzyazıda mümkün olan en kötü kesme.
- Sorunu ancak yarılar: 110 × 2 satır ≈ 4.800px yine eklenir.
- Solma (`linear-gradient(transparent, var(--paper))`) zayıf bir affordance ve zemin rengine bağlı — koyu temada
  ve `--paper-2` zeminli bloklarda ayrıca ayarlanması gerekir.
- Erişilebilir bir "devamı" tetiği için yine `<details>` ya da JS lazım; yani kırpma `<details>`'i ortadan
  kaldırmıyor, üstüne biniyor.

**Peek ihtiyacını Türkçe başlık zaten karşılıyor** — `title_tr` 519 kalemde var ve tam da bu iş için.

### R3.5 — Masaüstü: aynı davranış

Duruş hâli görünüm genişliğine göre değişmez. Sebep: `<details open>` bir öznitelik, CSS ile medya sorgusundan
kontrol edilemez; JS ile ≥1000px'te açmak ise aynı URL'yi aynı kişinin iki cihazında farklı davrandırır ve
açık/kapalı durumu düzenin değil okuyucunun kararıdır. Katman farkı (Öne çıkanlar açık, gerisi kapalı) işi
zaten yapıyor ve iki cihazda da aynı. Masaüstünde tek fark ölçüden geliyor: 72ch sütunda 405 karakter
~6 satıra iniyor, yani açmanın maliyeti kendiliğinden düşük.

### R3.6 — Klavye ve ekran okuyucu

`<details>` doğru kullanıldığında ek ARIA gerekmez. Üç kural:

1. **`<summary>` içine `<a>` konmaz.** Kaynak bağlantısı gövdededir; bu hem iç içe etkileşimi hem SR'de
   çift duyuruyu önler. (Tetik `<summary>`, hedef ayrı bir bağlantı — sekme sırası: özet tetiği → kaynak çipi.)
2. Varsayılan üçgen `list-style: none` + `::-webkit-details-marker { display: none }` ile gizlenir, yerine
   `::after` chevron gelir; öğe odaklanabilir kalır ve `:focus-visible { outline: 1px solid var(--brand);
   outline-offset: 2px }` görünür olur.
3. `role`, `tabindex`, elle `aria-expanded` **yazılmaz** — üçü de `<details>`'in kendi semantiğini bozar.

### Uygulama listesi — Revizyon 3

| # | Dosya | Değişiklik | Kabul testi |
|---|---|---|---|
| R3-P0-1 | `build.py` → `clip_html(item, day, cited, open_summary=False)` | `summary_tr` varsa satır `<details class="clip"{" open" if open_summary else ""}>` + `<summary>` (`clip-title` + `clip-meta`) + gövde (`clip-orig`, `clip-summary`, `<a class="entry-go" href=… target="_blank" rel="noopener">Kaynağa git ↗</a>`). `summary_tr` yoksa bugünkü `<a>` anatomisi aynen kalır. `clip-orig` artık duruş hâlinde değil. | 390px'te kapalı `.clip` yüksekliği ≤85px; açıkken özet ve kaynak çipi görünür; `summary_tr` olmayan satırda `<details>` ve chevron yok. |
| R3-P0-2 | `build.py` → `clip_list` / `highlights` çağrıları | Öne çıkanlar bloğu `open_summary=True`, kategori ve Genel listeleri `open_summary=False` ile çağrılır. | `haberler/2026-09-17.html` içinde `<details class="clip" open` sayısı = Öne çıkanlar'daki özetli kalem sayısı; kategori listelerinde 0. |
| R3-P0-3 | `assets/app.css` | Yeni `.clip > summary` (cursor:pointer, `list-style:none`, `::-webkit-details-marker{display:none}`, `padding:11px 0`, `:focus-visible` outline). `.clip-meta::after { content:" ▾" }` / `.clip[open] .clip-meta::after { content:" ▴" }`. `.clip-orig` `margin-top` gövde içi değere ayarlanır. `.clip > summary` ile `.more > summary` görsel olarak ayrışır. | Klavyeyle `Tab` → `<summary>` odaklanır ve görünür outline alır, `Enter`/`Space` açar/kapatır; VoiceOver "açılır öğe, kapalı" der. |
| R3-P0-4 | `assets/app.css` | `.clip-title { -webkit-line-clamp: 3 }` duruş hâlinde korunur; `.clip[open] .clip-title` kırpma kaldırılır (açıkken tam başlık görünür). | 155 karakterlik en uzun başlık kapalıyken 3 satır, açıkken tam görünür. |
| R3-P1-1 | `assets/app.js` → arama filtresi (R2/P2-2 ile birlikte) | Filtre etkinken eşleşen `.clip` `<details>`'i otomatik `open` yapılır ki eşleşme özette ise görünsün; filtre temizlenince eski hâle döner. | "Redback" araması sonucu eşleşen satırın özeti açık gelir; `Escape` sonrası tekrar kapanır. |
| R3-P1-2 | `build.py` → `clip_html` | `summary_tr` varsa `data-search` haystack'ine özet metni de eklenir. | Yalnızca özette geçen bir kelime (ör. "JIATF") aramada o satırı bulur. |

**Yapılmayacak:** `<details name="clips">` (tek-açık akordeon), 2 satır kırpma + solma, görünüm genişliğine
bağlı duruş hâli, özet için ayrı JS durum yönetimi.

---

## Revizyon 4 — kısmi kapsama

### R4.0 — Ölçüm: bu bir kapsama sorunu değil, tahsis sorunu

`data/news/2026-09-17.json`, 540 kalem, 123'ünde `summary_tr`. Özetlerin nereye gittiği:

| Dağılım | Sonuç |
|---|---|
| Dosya sırasındaki konum | Hepsi ilk **128** kalemin içinde (yayın zamanına göre baş taraf) |
| Kategoriye göre | **Genel Savunma Gündemi 107** · C-UAS 11 · Politika 3 · İhale 1 · Hafif Silah 1 |
| Kademeye göre | tier B **102** · tier A 21 |
| Öne çıkanlar (12 satır) | **4** |

Yani günlük bütçenin **%87'si, varsayılan olarak kapalı olan ve içinde ikinci bir katlama bulunan Genel
kovasına** harcanıyor; yöneticinin sayfasının tamamı olan 12 satıra 4 özet düşüyor. Bütçe zaten doğru
büyüklükte (123 ≈ varsayılan görünür satır sayısı) — **yanlış satırlara dönük.**

Bu, tartışmayı değiştiriyor: soru "kapsama nasıl %100'e çıkar" değil, "aynı 110 çağrı doğru satırlara nasıl
yönlendirilir". Sıralama düzeltilince Öne çıkanlar 4/12'den ~12/12'ye çıkar — **ek maliyet sıfır.**

### R4.1 — Asıl tasarım hatası: tek bir şekil iki anlam taşıyor

Bugün "chevron yok" iki ayrı şeyi anlatıyor ve okuyucu ikisini ayırt edemiyor:

- *"Bu satır hiçbir zaman özet kapsamında değildi"* → 417 satır, **normal**
- *"Bu satırın özeti olmalıydı, alamadık"* → ~2 satır, **arıza**

Bu ikisi aynı göründüğü sürece okuyucu haklı olarak "bilgi eksik / hata var" diyor. Çözüm chevronu her satıra
dağıtmak değil, **kapsamı görünür kılmak.**

**İlke: tekdüzelik blok içinde zorunludur, sayfa genelinde değil.** Bir blokta bazı satırlar açılıyor bazıları
açılmıyorsa bozuk görünür; bloktan bloğa şekil değişmesi ise derinlik farkı olarak okunur — yeter ki fark
okuyucunun görebildiği bir şeyle (sıra, katlama) ilişkili olsun. Bugünkü karışıklık *yayın zamanıyla*
ilişkili; yayın zamanı sayfada görünmüyor, o yüzden rastgele görünüyor.

### R4.2 — Kapsam tanımı: "katlama açmadan görebildiğin her satır"

> **Özet kapsamı = varsayılan görünür küme.** Öne çıkanlar'ın 12'si + her kategorinin ilk 15/20'si.
> "+N daha" arkasındaki kuyruk ve Genel kovasının tamamı **tasarım gereği kapsam dışıdır.**

Kendi kendini belgeleyen bir kural: *tıklamadan görüyorsan özeti vardır.* Sonucu şu — her blok kendi içinde
tekdüze olur:

| Blok | Şekil | Tekdüze mi |
|---|---|---|
| Öne çıkanlar | hepsi chevronlu | ✔ (± günlük ~2 arıza, işaretli) |
| Kategori ilk 15/20 | hepsi chevronlu | ✔ |
| "+N daha" içi | hiçbiri chevronsuz | ✔ |
| Genel kovası | hiçbiri chevronsuz | ✔ |

Bütçe değişmiyor: bugünkü 123 çağrı bu kümeyi zaten karşılıyor.

### R4.3 — Seçeneklerin sıralaması

1. **(c) Kaynakta düzelt — ama "%100'e çıkar" olarak değil, "kapsamı sıralamaya bağla" olarak.** Zorunlu ve
   tek başına sorunun büyük kısmını çözüyor (R4.0). Tavan ~%98 olduğu için tek başına yetmez.
2. **(b) Sessiz işaret — ama yalnızca kapsam içindeki arızaya.** Kapsamdaki bir satırın özeti alınamadıysa
   meta satırının sonuna `--muted` bir jeton: `özet alınamadı`. Günde ~2 satır. Bu, ürünün zaten kurduğu dile
   uyuyor: `Medya takibi yok`, `16 kaynak yanıt vermedi`, devre dışı `daybar` okları — **bu sitede yokluk
   gizlenmez, söylenir.** Kapsam dışı 417 satıra bu jeton **konmaz**; olmayan bir arızayı duyurmak olur.
3. **(d) Karışık şekilleri kabul et** — reddedildi: müşteri bir gün içinde fark etti, ampirik olarak yanlış.
4. **(a) Her satıra chevron** — reddedildi ve en kötüsü. Chevron içerik vaat eder; dokunup yalnızca kaynak
   bağlantısı bulan okuyucuya 400 satır boyunca "chevron değersizdir" öğretilir. Görünür bir tutarsızlığı,
   affordance'ın sistematik olarak yalan söylemesiyle takas etmek olur.

### R4.4 — Q1: katman kuralı yaşar, ama tekdüzelik şartına bağlanır

"Öne çıkanlar'da açık" okuma görevi için hâlâ doğru (Rev 3.0'daki gerekçe değişmedi). Bozan şey kuralın
kendisi değil, **yüklemin görünmez olması**: 12 satırın tamamı aynı katmanda ama dördü açık — okuyucu kuralı
göremediği için rastgelelik görüyor.

**Karar:** açıklık, katman + veri tekdüzeliğinin birlikte sağlandığı durumda verilir.

> Öne çıkanlar bloğundaki **her** satırın özeti varsa hepsi `open` render edilir; **bir tanesi bile eksikse
> hiçbiri açılmaz.** Build zamanında üç satırlık bir kontrol.

Kendi kendini iyileştiren bir kural: getirici bir sabah tökezlerse gün sessizce "hepsi kapalı"ya düşer,
"bazıları rastgele açık"a değil. İyi günlerin kolaylığı korunur, kötü günlerde tutarlılık hiç kaybedilmez —
ve müşterinin şikâyet ettiği karışık durum bir daha hiçbir koşulda yayınlanamaz. "Kapsama yakın-tam olana
kadar her şey kapalı" seçeneğine göre üstünlüğü bu: iyi günleri cezalandırmıyor.

### Uygulama listesi — Revizyon 4

| # | Dosya | Değişiklik | Kabul testi |
|---|---|---|---|
| R4-P0-1 | özetleyici (`scripts/…`) | Seçim sırası yayın zamanı yerine **R1-P1-1'deki `news_score`** olur; kapsam = varsayılan görünür küme (Öne çıkanlar 12 + her kategorinin ilk 15/20). Bütçe (~110-125 çağrı) değişmez. | 2026-09-17 yeniden koşturulduğunda Öne çıkanlar'ın 12 satırının ≥11'inde `summary_tr` bulunur; `Genel Savunma Gündemi`ne düşen özet sayısı 107'den ≤10'a iner. |
| R4-P0-2 | `build.py` → `clip_html` | Kalem kapsam içindeyse (`item["summary_scope"] is True`) ama `summary_tr` yoksa, meta satırının sonuna `<span class="clip-nosum">özet alınamadı</span>` eklenir. Kapsam dışı satıra hiçbir şey eklenmez. | Kapsam içi arızalı satırda jeton görünür; `Genel Savunma Gündemi` içindeki hiçbir satırda geçmez; `grep -c "özet alınamadı"` ≤ 5. |
| R4-P0-3 | `build.py` → Öne çıkanlar bloğu | `open_summary = all(r.get("summary_tr") for r in highlights)`; blok tek bir kararla ya tamamen açık ya tamamen kapalı render edilir. | Bir kalemin `summary_tr`'si elle silindiğinde üretilen sayfada `<details class="clip" open` sayısı 0 olur; geri konulduğunda 12 olur. Hiçbir çıktıda "bloğun bir kısmı açık" durumu oluşmaz. |
| R4-P0-4 | `assets/app.css` | `.clip-nosum { color: var(--muted); }` — mono 10,5px meta dilinde, ek vurgu yok. Meta jeton tavanı bu tek durumda 4'e çıkar. | Jeton meta satırının geri kalanıyla aynı ağırlıkta; renkli ya da ikonlu değil. |
| R4-P1-1 | `build.py` → medya sayfası başlık istatistiği | `stat` satırına kapsama eklenir: `… · {n}/{m} özet`. Sayfa üstündeki mevcut `50 kaynak okundu · 528 başlık…` diliyle aynı yerde. | 17 Eylül sayfası `· 123/125 özet` benzeri bir jeton gösterir; sayılar `data/news/*.json` ile eşleşir. |
| R4-P1-2 | `scripts/…` + `data/news/*.json` | Kaleme `summary_scope: true/false` alanı yazılır ki build hangi satırın kapsamda olduğunu bilsin (bugün çıkarsanamıyor). | `python3 build.py` alan yokken de hatasız koşar (eski günler için `summary_scope` yoksa kapsam dışı sayılır). |

**Yapılmayacak:** her satıra chevron; kapsam dışı satırlara "özet yok" jetonu; kapsamı %100'e zorlamak için
ödeme duvarı arkasındaki kaynakları zorlama; Öne çıkanlar'da kısmi açıklık.

---

## Revizyon 5 — çeviri vekili

### R5.0 — Karar: (a), üç şartla

Müşterinin baştan beri söylediği kullanıcı gerçeği belirleyici: **okuyucu İngilizce okumuyor.** Bu doğruysa
İngilizce özgün sayfa onun için bir "hedef" değil, bir *başarısızlık hâli*. O hâlde onu ikincil yapmak bir
indirgeme değil, bir düzeltme. Bugün sitenin her katmanı Türkçe — `title_tr` 519/533 satırda, özetler Türkçe,
arayüz Türkçe — ve İngilizceyi yalnızca **niyetin en yüksek olduğu anda**, dokunuşun hedefinde veriyoruz.

Ayrıca ~400 satırın gövdesi yok; (b) onlara hiçbir şey vermiyor. Ve "o hâlde her satır katlansın" yolu Rev 4'te
doğru gerekçeyle kapatıldı: chevron içerik vaat eder, boşa açılan chevron affordance'ı sistematik olarak
yalancı yapar. Yani (b) ile (a-dışı her şey) elenerek değil, kullanıcı gerçeğiyle doğrudan (a)'ya varıyoruz.

> **Her kupür bağlantısı vekil üzerinden gider. İstisna yok. Özgün metin, gövdesi olan satırlarda etiketli
> bir çip olarak durur.**

Üç şart:

1. **Kaynakça muaf.** Brifingdeki `[K1]…` bağlantıları (`enrich.py`) **hiçbir zaman** vekile çevrilmez.
   Kupür bir *okuma* nesnesi, kaynakça bir *delil* nesnesidir; delil kayıt kaynağını göstermek zorundadır.
   Dosya sınırı da net: `clip_html` çevirir, `enrich.add_source_anchors` çevirmez.
2. **Tek satırlık kapatma anahtarı.** `build.py` başında `TRANSLATE_PROXY = True`. Aşağıdaki maruziyet notu
   nedeniyle bu kararın tek satırda geri alınabilir olması şart.
3. **Sayfa düzeyinde beyan** (R5.2).

### R5.1 — Müşterinin bilerek alması gereken karar: maruziyet

Bugün okuyucunun dokunuşu doğrudan yayıncıya gidiyor. Vekille birlikte **her dışa açılan dokunuş Google'a
gider**: URL, zamanlama, okuyucunun IP'si. Sızan şey makalenin içeriği değil — o zaten kamuya açık — **seçim
örüntüsü**: bir Türk devlet savunma üreticisinin yöneticilerinin hangi başlıkları, hangi sırayla, hangi gün
okuduğu. Bu ürünün asıl değerli tarafı da tam olarak o örüntü (50 mm namlu, Malezya ihalesi, Hanwha).
Sitenin `noindex` + özel duruşuyla tutarlı olan şey, bunun sessizce varsayılan olması değil, **bilinerek
seçilmesidir.** Teknik bir veto değil; müşterinin bir kez bakıp onaylaması gereken bir madde — ve onaylamazsa
şart 2'deki anahtar bir satırda kapatır.

### R5.2 — Dürüstlük: bir kez söyle, her satırda değil

Google çubuğu dokunuştan *sonra* beliriyor ve dokunmadan önce nereye gidildiğini söylemiyor; yani kendiliğinden
yeterli değil. Ama satır başına jeton koymak Rev 4'te reddedilen hatanın aynısı olur — **normal bir durumu
400 kez duyurmak.** Doğru yer sayfa başındaki istatistik satırı, mevcut dille aynı yerde:

`50 kaynak okundu · 528 başlık · son 48 saat · başlıklar Türkçe çeviriyle açılır`

Gövdesi olan satırlarda beyan zaten somut: iki çip yan yana durur ve etiketlerin kendisi açıklar —
`Özgün metin ↗` (Rev 3'teki `Kaynağa git ↗` bu isme döner; artık ikisi de "kaynak" olduğu için o etiket
ayırt etmiyor). Satır başına ek işaret yok.

### R5.3 — 403: evet, ama alan adı başına, kalem başına değil

Engelleme yayıncı düzeyinde (Soldat und Technik kendi sitesinin tamamında vekili reddediyor), makale düzeyinde
değil. Dolayısıyla 540 kalemi değil, **~50 tekil alan adını** yoklamak yeter — haftada bir, sonucu
`data/translate-hosts.json`'da tutularak. Zaten ağ işi yapan toplayıcı/özetleyici tarafında, build.py'ye ağ
girmeden.

Bilinmeyen alan adı için varsayılan **iyimser** (vekil kullanılır): yanlış-iyimserin bedeli okuyucunun bir
Google hata sayfasına düşüp geri dönmesi; yanlış-kötümserin bedeli ise Türkçe okuyan birine sessizce İngilizce
sayfa vermek — ikincisi daha sinsi ve daha sık. Yoklama yapılıyorken iyimser varsayım doğru taraf.

P0'da bugün ölçülen tek engelli alan adı sabit bir listeye yazılır (stopgap); yoklama P1.

### R5.4 — Özetleri değersizleştiriyor mu? Hayır — ama kuyruğun değerini değiştiriyor

Değişen şey özetin işi değil, **özetsiz 400 satırın** değeri: dün onlar Türkçe okuyan için çıkmaz sokaktı,
bugün okunabilir hâle geliyor. Özetin işi değişmiyor, çünkü her iki tüketim yerinde de onu okuyan kişi
**sayfadan çıkmamayı seçmiş** kişidir: Öne çıkanlar'daki yönetici 12 makaleyi açmayacak (4 dakikası var),
kategorideki analist ise özeti zaten bilerek dokunup açtı. İkisi de teaser değil, muhteva istiyor.

**Prompta yapılacak tek değişiklik:** özet artık *kendi kendine yeterli* olmak zorunda değil, çünkü tam metin
bir dokunuş ötede. O hâlde dengeli kapsama yerine **karar verdiren tek sert veriyi öne alsın** (sayı, tarih,
aktör) ve "ayrıntı için kaynağa bakınız" türü bağlayıcı cümleleri bıraksın. **Kısaltılmasın** — iki cümle ve
mevcut yoğunluk korunur; teaser'a çevirmek yöneticinin birincil kullanımını kırar.

Yan fayda: Türkçe başlık → Türkçe makale artık tutarlı. Bugünkü `title_tr` → İngilizce sayfa sıçraması
kalkıyor.

### Uygulama listesi — Revizyon 5

| # | Dosya | Değişiklik | Kabul testi |
|---|---|---|---|
| R5-P0-1 | `build.py` → yeni `tr_url(url)` + `TRANSLATE_PROXY = True` | Host dönüşümü: `-` → `--`, `.` → `-`, sonuna `.translate.goog`; yol ve sorgu korunur, `?_x_tr_sl=auto&_x_tr_tl=tr&_x_tr_hl=tr` eklenir (var olan sorgu varsa `&` ile). `TRANSLATE_PROXY=False` iken fonksiyon URL'i olduğu gibi döndürür. | `tr_url("https://www.army-technology.com/news/x/")` == `https://www-army--technology-com.translate.goog/news/x/?_x_tr_sl=auto&_x_tr_tl=tr&_x_tr_hl=tr`; bayrak `False` iken üretilen HTML'de `translate.goog` hiç geçmez. |
| R5-P0-2 | `build.py` → `clip_html` | Satırın birincil `href`'i `tr_url(item["url"])` olur. Gövdesi olan satırda (Rev 3 `<details>`) `Kaynağa git ↗` çipi **`Özgün metin ↗`** olarak yeniden adlandırılır ve `item["url"]`'e (çevrilmemiş) gider. Gövdesiz satıra ek bağlantı konmaz. | Her `.clip` birincil bağlantısı `translate.goog` içerir; her açık `<details>` gövdesinde tam olarak bir `Özgün metin` bağlantısı vardır ve `translate.goog` **içermez**. |
| R5-P0-3 | `build.py` → `build_news_page()` stat satırı | Sona `· başlıklar Türkçe çeviriyle açılır` eklenir (yalnızca `TRANSLATE_PROXY` açıkken). | Medya sayfası başlığında dizgi görünür; `TRANSLATE_PROXY=False` iken görünmez. |
| R5-P0-4 | `enrich.py` → `add_source_anchors` | **Değişmez.** Kaynakça URL'leri vekile çevrilmez; bu bir "yapılmayacak" maddesi ve regresyon testidir. | `reports/2026-09-17.html` içinde `translate.goog` dizgisi **hiç** geçmez; 14 `[K…]` bağlantısının hepsi özgün alan adına gider. |
| R5-P0-5 | `build.py` → `TRANSLATE_BLOCK` sabiti | Bugün ölçülen engelli alan adları elle yazılır (`soldat-und-technik.de`); bu hostlardaki kalemler özgün URL'e bağlanır. Geçici çözüm. | Soldat und Technik kalemi `translate.goog` içermeyen bir bağlantı taşır. |
| R5-P1-1 | toplayıcı/özetleyici + `data/translate-hosts.json` | Tekil alan adı başına haftada bir HEAD yoklaması; sonuç dosyada tutulur, `build.py` yalnızca okur (build ağa çıkmaz). Bilinmeyen host iyimser (vekil kullanılır). `TRANSLATE_BLOCK` sabiti bu dosyayla değiştirilir. | ~50 yoklama ile dosya üretilir; engelli listelenen hostların kalemleri özgün URL alır; dosya yokken build hatasız koşar ve hepsi vekile gider. |
| R5-P1-2 | özetleyici promptu | "Kendi kendine yeterli olma" zorunluluğu kalkar: iki cümle ve mevcut yoğunluk korunur, ama en karar verdiren sert veri (sayı/tarih/aktör) ilk cümleye alınır; "ayrıntı için kaynağa bakınız" türü bağlayıcılar çıkarılır. | Yeni günün özetlerinde ilk cümle bir sayı ya da özel ad ile açılır; uzunluk medyanı 350-450 karakter bandında kalır. |

**Yapılmayacak:** kaynakçayı vekile çevirmek; her satıra "çeviri" jetonu; gövdesiz satıra ikinci bağlantı
sıkıştırmak; her satırı katlamak (Rev 4 gerekçesi geçerli); özetleri teaser'a kısaltmak; kalem başına 403
yoklaması.

---

## Revizyon 6 — çapa dili ve tablet

### A. ALARMLAR satırı

#### R6.1 — Önce hata: `enrich.py` varış işaretini siliyor

`add_item_anchors` yakaladığı `G12`'yi çıktıya yazmıyor; yalnızca ondan sonraki parçayı basıyor:

```python
return (f'<li id="{gid}"><strong class="ganchor">{m.group(2)}</strong>' …)
#                                                  ^^^^^^^^^^^ group(1) ("G12") düşüyor
```

Sonuç, dört günün hepsinde ve tüm RAKİP HAREKETLERİ / İZLEME LİSTESİ kalemlerinde:
`<li id="g12"><strong class="ganchor"> · Malezya MERAD (RMK-13)</strong>` — öksüz bir " · " ve varış işareti yok.
`add_heading_anchors` aynı işi doğru yapıyor (`{m.group(1)}` ile tam etiketi basıyor); yani iki yol tutarsız,
`<h3>` tarafı sağlam, `<li>` tarafı bozuk. **Tek satırlık düzeltme**, zevk meselesi değil.

#### R6.2 — `G#` nerede görünür, nerede görünmez

`G#` **konumsal** bir id: aynı `g10` 14 Eylül'de "Aselsan", 17 Eylül'de "ABD Ordusu 50 mm arayışı". Yani günler
arasında hiçbir anlamı yok — kopyalanan bir `#g10` bağlantısı ertesi gün başka bir şeye gider.

Ayrım şu: **`G#` bir gün içinde meşru bir kısa tutamaktır, ama hiçbir satırın tek yükü olamaz.**

| Yer | Görünür mü | Gerekçe |
|---|---|---|
| Hedefteki etiket (`<h3>`, `<li>`) | **Evet** — `G12 · Malezya MERAD` | Varış teyidi; R6.1'in bozduğu şey tam olarak bu |
| Gövde içi atıf (`bkz. G8`, tablo rozetleri) | **Evet, değişmiyor** | Okuyucu ilk hedefte eşleşmeyi öğrenir; kısa ve akıcı |
| **ALARMLAR satırı** | **Hayır** | Belgenin ilk satırı: okuyucu konvansiyonu henüz öğrenmedi ve orada id *tek yük*. `"G12 ne demek bilmiyorsun"` haklı. |
| Kopyalanan bağlantı (`#g12`) | Zaten görünmüyor | Ama günler arası kaymayı belgele (P1) |

#### R6.3 — Satır ne olmalı: (b), ama bağlantı yük değil bonus

Seçim **(b)** — bağlantı kalır, etiketi *şey* olur, id değil. Ama asıl kural: **satır bağlantıya dokunmadan
da kendi başına yeterli olmalı.** İşi "yangın yok, iki tarih geliyor" ise tarih + ad yeter; id hiçbir şey katmaz.

```
Alarm yok.

DIŞ SON TARİHLER
9 Ekim      USAF orta kalibre pazar araştırması →
24 Aralık   665 milyon $'lık C-UAS test siparişine itiraz →
```

- Tarih `--watch` renginde (Rev 1'de bu token'a verilen iş), ad bağlantının kendisi, hedef `#g10`.
- Her son tarih kendi satırında; virgüllü tek satır telefonda okunmuyor.
- **Satır elle yazılmaz, `developments[]`'ten üretilir.** Bunun için frontmatter'a isteğe bağlı `due` alanı:
  `{id: G10, label: "…", home: izleme, due: 2026-10-09}`. `decision_by` türetilir (`min(due)`), `status_of()`
  aynen çalışır. Kazanç: elle yazılmış id kalmaz, etiket hedefle **garantili** aynıdır, ölü çapa üretilemez.

#### R6.4 — Prompt kuralı: "tekrar etme" → "sahibi olsun, atıf tek yönlü olsun"

Bugünkü kural ("aynı olguyu iki kez yazma, çapraz atıf ver") olgunun **hiçbir yerde** yaşamamasına yol açıyor:
ALARMLAR "bkz. G10" diyor, G10 "yanıt süresi için bkz. ALARMLAR" diyor. Yerine:

> **Her olgunun tek bir sahip bölümü vardır. Atıf sahibe doğru tek yönlüdür; atıf yapan taraf sahibin tek
> ayırt edici verisini (tarih, sayı, aktör) tekrarlayabilir, açıklamasını tekrarlayamaz. Bir atıf, kendisini
> işaret eden bölüme geri işaret edemez.**

Son tarihler için uygulaması: **ALARMLAR tarihin ve adın sahibidir** (açıklama yok), **G# açıklamanın
sahibidir** (geri bağlantı yok). "Yanıt süresi için bkz. ALARMLAR" cümleleri kalkar.

### B. Tablet

#### R6.5 — Teşhis: iki uç da aynı hatanın iki yüzü — ölçü serbest bırakılmış

Ölçüm `--measure: 66ch ≈ 573px` (1024'te ölçülen sütun genişliği). Bugün:

- **768/820/834 (portre, <860):** rail gizleniyor, sütun **640-706px**'e kadar geriliyor — ölçünün %12-23 üstü.
  Tek sütun durumunda hiçbir şey ölçüyü sınırlamıyor.
- **1024/1180 (yatay, >860):** rail dönüyor ama `report-grid` sola dayalı; 785px'lik ızgara (172+40+573)
  976px'lik alanda sola yapışıyor, sağda büyüyen boşluk kalıyor (276/175 → 276/231).
- **Medya sayfasında asimetri:** `.clip { max-width: 72ch }` kalemi kırpıyor ama `<ul>` geriliyor, dolayısıyla
  boşluk hep sağda toplanıyor (43 sol / 78 sağ).

Ortak sebep: **ölçü hiçbir durumda ortalanmıyor.** Kırpma var, hizalama yok.

#### R6.6 — Kurallar

**Kural 1 (en yüksek getirili, tek satır) — tek sütun durumunda ölçü ortalanır.**
Rail gizliyken `article.column` ve medya listesi kabı `max-width: var(--measure)` / `72ch` + `margin-inline: auto`
alır. Kırpmayı kalemden (`.clip`) kaba taşı. 834'te 706px sol-dayalı yerine **573px ortalanmış**, boşluklar
~130/130 simetrik olur.

**Kural 2 — rail 860'ta değil, 920px'te döner.**
Izgara genişliği 172 + 40 + 573 = **785px**; artı `.wrap` dolgusu 48 = 833 (nefes payı sıfır). Rahat eşik
785 + 48 + ~87 pay = **920px**. Bu eşik iPad portreyi (834) tek sütunda, iPad yatayı (1024) rail'li durumda
bırakır — cihazın iki hâli iki farklı düzene temiz ayrılır.

**Kural 3 — rail'li durumda ızgaranın kendisi ortalanır.**
`.report-grid { max-width: calc(var(--rail) + 40px + var(--measure)); margin-inline: auto; }`.
1024'te ~120/120, 1180'de ~197/197 simetrik. Okuma sütunu sayfa merkezinin sağında kalır — iki sütunlu
editoryal düzende beklenen davranış, 276/231'den her koşulda iyi.

**Kural 4 — `@media (min-width: 1000px)` iki sütunlu Öne çıkanlar kuralı kaldırılır.**
Kendi hatamın düzeltmesi: o kural ilk incelemede, satırlar 293px'ken yazıldı. Rev 3 satırları **78px**'e
indirdi, 12 kalem ≈ 940px ≈ 1,2 ekran — çözdüğü sorun ortadan kalktı. Üstelik rail döndüğünde içerik sütunu
72ch'e (≈625px) kapalı; iki sütun = 292px, üç satırlık başlık + meta için fazla dar. Tek sütun kalır.

**Kural 5 — döndürme metin bloğunu değiştirmez.**
Kurallar 1-3'ten sonra 834 → 1180 dönüşünde sütun genişliği **her iki hâlde de 573px**; değişen yalnızca
rail'in varlığı ve boşluklar. Tabletin breakpoint sorusunun cevabı bu: *döndürme kromu değiştirir, metin
bloğunu asla.*

### Uygulama listesi — Revizyon 6

| # | Dosya | Değişiklik | Kabul testi |
|---|---|---|---|
| R6-P0-1 | `enrich.py` → `add_item_anchors` | `{m.group(2)}` → `{m.group(1)}{m.group(2)}`. | `reports/2026-09-20.html` içinde `<strong class="ganchor">G12 · ` geçer; hiçbir `ganchor` " · " ile başlamaz (`grep -c '"ganchor"> ·'` = 0). |
| R6-P0-2 | `assets/app.css` | **Kural 1:** tek sütun durumunda `article.column` `max-width: var(--measure)`, medya liste kabı `max-width: 72ch`, ikisi de `margin-inline: auto`; `.clip` üzerindeki `max-width` kaba taşınır. | 768/820/834'te sütun ≤580px ve sol/sağ boşluk farkı ≤4px. |
| R6-P0-3 | `assets/app.css` | **Kural 2:** `@media (max-width: 860px)` → `(max-width: 919px)`; rail'li kurallar `(min-width: 920px)`. | 834'te rail gizli, 1024'te görünür; 900px'te tek sütun. |
| R6-P0-4 | `assets/app.css` | **Kural 3:** `.report-grid` ve `.news-grid` → `max-width: calc(var(--rail) + 40px + var(--measure))` (medyada `72ch`) + `margin-inline: auto`. | 1024 ve 1180'de sol/sağ boşluk farkı ≤4px. |
| R6-P0-5 | `assets/app.css` | **Kural 4:** `@media (min-width: 1000px)` `.highlights { columns: 2 }` bloğu silinir. | Hiçbir genişlikte Öne çıkanlar iki sütun değil; `grep -c "columns: 2" assets/app.css` = 0. |
| R6-P0-6 | rapor promptu | R6.4'teki sahiplik kuralı; "bkz. ALARMLAR" geri bağlantıları kaldırılır; ALARMLAR satırı tarih + ad taşır, açıklama taşımaz. | Yeni günün raporunda `bkz. ALARMLAR` geçmez; ALARMLAR satırındaki her son tarih bir ada sahiptir. |
| R6-P1-1 | `build.py` + frontmatter şeması | `developments[]`'e isteğe bağlı `due`; ALARMLAR son tarih listesi bu alandan **üretilir** (tarih `--watch`, ad bağlantı, hedef `#g{id}`). `decision_by` = `min(due)` olarak türetilir, `status_of()` değişmez. | `due` taşıyan bir raporda liste otomatik doğar ve her ad gerçek bir çapaya gider (ölü `href` yok); `due` yoksa eski davranış korunur. |
| R6-P1-2 | `build.py` → `copylink` | Kopyalanan bağlantı gün bağlamı taşıdığı için zaten tam URL; `title` metnine "bu çapa yalnızca bu güne aittir" notu eklenir. | Kopyala düğmesinin `title`'ı gün-özgüllüğünü söyler. |

**Yapılmayacak:** `G#`'yi hedeften de kaldırmak (varış teyidi gider); gövde içi `G#` atıflarını etikete
çevirmek (28+ karakterlik adlar cümle ortasında okunmuyor); ölçüyü tablette genişletmek; ALARMLAR satırını
elle yazmaya devam etmek.

---

## Revizyon 7 — bildirim denetiminin yeri

### R7.0 — İhlal edilen değişmez

> **Hiçbir yüzey, sonucunu bildiremeyeceği bir eylemi tetikleyemez.**

Kusur bunun ihlali: kart üç sayfada da "Aç" düğmesi gösteriyor, `paint()` ise `if (!btn) return` ile iki
sayfada hiçbir şey yapmıyor. Aşağıdaki kararların hepsi bu tek cümleden türüyor ve kabul testi de bu olmalı.

### R7.1 — İki ayrı iş, iki ayrı yer

Bugün tek bir denetime iki farklı iş yükleniyor ve ikisi de aksıyor:

| İş | Ne zaman | Nerede olmalı |
|---|---|---|
| **Geçici sonuç** — "az önce dokundun, oldu mu?" | Dokunuştan hemen sonra, saniyeler | **Eylemin olduğu yerde** = kartın kendisi |
| **Kalıcı durum + kapatma** | Her zaman, nadiren bakılır | **Tek, sabit bir ev** = footer, üç sayfada da |

Bugünkü tasarım geçici sonucu kalıcı denetime bastırmaya çalışıyor. Bu, denetim ekranda olsa bile yanlış:
kart `position: fixed; bottom: 0` — okuyucunun gözü ekranın altında; zil nerede olursa olsun büyük olasılıkla
görüş alanı dışında. **Görünmeyen bir kontrole boya basmak, hiç boya basmamakla aynı şeydir.** Q3'ün cevabı bu.

### R7.2 — Q1: zil footer'a, üç sayfaya da

- **Daybar olmaz.** Daybar'ın işi gün gezinmesi; 375px'te zaten ~286/339px dolu (ok 40 + tarih 86 + ok 40 +
  karşı ürün çipi ~120). Rev 1'den beri uygulanan kural: *bir şeridin tek işi vardır.*
- **Masthead olmaz.** Künye. Rev 2'de içi boşaltıldı.
- **`.controls` olmaz** — ve bugün orada olması bir karışıklık: arama *bu sayfayı süzer*, zil *cihazı ayarlar*.
  Aynı şeritte iki farklı kapsam. Zil çıkınca arama alanı satırı tek başına alır, şerit tek işli olur.
- **Footer olur.** `.foot` zaten üç sayfa tipinde de var, yeni krom eklemiyor, ve zil bir *ürün ayarı* —
  okuduğun güne değil cihaza ait. Ayarların yeri sayfa kromu değil, tek ve sabit bir yerdir.

Footer "ölü metin bölgesi" itirazı, geçici sonuç kartta bildirildiği için düşüyor: zilin artık arıza anında
görülmesi gerekmiyor. Kalıcı durumun sakin bir yerde durması doğrudur. Net kazanç, keşfedilebilirlikte de
artı: 1 sayfa × kontrol şeridi yerine **3 sayfa × footer**.

Yerleşim: `.foot > .wrap` flex olur; zil önce (eylem), sorumluluk reddi sonra (hüküm). 375px'te alt alta.
Zil `.notify` sınıflarını korur, Rev 2'nin `.notify--on` ikon-only kuralı aynen geçerli. `endnav` (R1-P1-1)
çizginin üstünde kalır; zil çizginin altında, görsel olarak footer'ın parçası.

### R7.3 — Q2: kart kendi sonucunu kendi bildirir

Sunulan iki yoldan ikisi de değil. Kartı bildirim yapamayan sayfalarda bastırmak yanlış: brifing günün asıl
durağı ve sormak için en doğru an orası. Zili her sayfaya koymak gerekli ama yeterli değil (R7.1).

> Kart, **başarısızlıkta kapanmaz**: kendi metnini değiştirir, birincil düğme `Tekrar dene` olur, ikincil
> düğme `Kapat` kalır. **Başarıda kapanır** — durum artık zilde görünür, oyalanmaya gerek yok.

Ve bir hak düzeltmesi: **arıza asla 7 günlük erteleme tetiklemez.** Bugün "Aç" → hata → kart kapanır →
7 gün yok. Sunucu hatası için okuyucuyu cezalandırmak olur. Erteleme yalnızca açık `Şimdi değil`'de ve
başarıda devreye girer.

### R7.4 — Q4: keşfedilebilirlik eksikti, ama düşünülen yerden değil

Zil *kazanım* kanalı değil; kazanımı kart yapıyor (ve yalnızca uygulama kuruluyken; kurulmamış okuyucuda
push zaten çalışmıyor — iOS'ta kurulum şart). Zilin işi **durumu göstermek ve kapatmak.**

Asıl boşluk şuydu: kartı bir kez `Şimdi değil` ile kapatan okuyucunun 7 günlük karanlığı var ve üç sayfanın
ikisinde başka hiçbir yolu yok. Footer zili bunu üç sayfada da kapatıyor. Tek ek: kapalı durumdaki etiket bir
*isim* değil bir *teklif* olsun — `Bildirimler` → **`Yeni rapor bildirimi al`**. Açık durumda Rev 2 kuralı
(ikon-only) değişmez; `blocked` durumunda etiket ve açıklayıcı `title` korunur.

### Uygulama listesi — Revizyon 7

| # | Dosya | Değişiklik | Kabul testi |
|---|---|---|---|
| R7-P0-1 | `assets/app.js` → kart işleyicisi | Kart kendi sonucunu basar, `paint()`'e bağımlı değil. Başarı → kart gizlenir (+ `paint()` varsa çağrılır). Arıza → kart **açık kalır**, `.promptbar-text` "Bildirim açılamadı. Tekrar deneyelim mi?" olur, birincil düğme `Tekrar dene`, ikincil `Kapat`. Arızada `snooze()` **çağrılmaz**. | `/subscribe` 500 döndüğünde brifing sayfasında kart ekranda kalır ve arıza metnini gösterir; `localStorage["defintel:notify"]` yazılmaz; `Tekrar dene` yeniden abone olmayı dener. |
| R7-P0-2 | `build.py` → `FOOT` | Zil markup'ı (`#notify` + svg + `.notify-label`) `FOOT` içine taşınır; `.foot > .wrap` → `.foot-inner`, zil önce, sorumluluk reddi sonra. Üç sayfa tipi de aynı `FOOT`'u kullandığı için tek değişiklik yeter. | Üç sayfa tipinde de `#notify` tam olarak bir kez bulunur; `haberler/…` ve `reports/…` sayfalarında bugün 0. |
| R7-P0-3 | `build.py` → `build_index()` | Zil `.controls` satırından çıkarılır; satırda yalnızca arama kalır. | `index.html`'de `.controls` içinde `#notify` yok; arama alanı satırın tamamını kaplar ve 375px'te taşmaz. |
| R7-P0-4 | `assets/app.css` | `.foot-inner { display:flex; gap:18px; align-items:baseline; flex-wrap:wrap; justify-content:space-between }`; zil `flex: 0 0 auto`, dokunma hedefi ≥44px; 375px'te sorumluluk reddinin üstünde kendi satırında. Rev 2'nin `.notify--on` kuralı **değişmez**. | 375px'te zilin `getBoundingClientRect().height >= 44`; abone durumda yalnızca ikon görünür (Rev 2 regresyonu). |
| R7-P0-5 | `assets/app.js` → `paint()` | `if (!btn) return` guard'ı **kalır** (savunma amaçlı), ama artık hiçbir sonuç bildirimi ona bağlı değil. | Zil markup'ı elle silindiğinde kart yine de arızayı bildirir; JS hata vermez. |
| R7-P1-1 | `assets/app.js` → `paint()` etiket sözlüğü | `off: "Bildirimler"` → `off: "Yeni rapor bildirimi al"`. `on`, `blocked`, arıza etiketleri değişmez. | Kapalı durumda footer teklifi okunur; açık durumda etiket görsel olarak gizli kalır (Rev 2). |
| R7-P1-2 | `assets/app.js` | Arıza metni sunucu ile ağ hatasını ayırır: HTTP yanıtı geldiyse "Sunucu bildirimi kabul etmedi", ağ hatasıysa "Bağlantı kurulamadı". Aynı `Tekrar dene` akışı. | Çevrimdışıyken "Bağlantı kurulamadı" görünür; 500'de sunucu metni görünür. |

**Yapılmayacak:** zili daybar'a ya da masthead'e koymak; kartı brifing/medya sayfalarında bastırmak; arızada
erteleme yazmak; zili birden fazla yerde tutmak (Rev 4: tek şekil, tek anlam); arıza için ayrı bir modal
ya da yeni sabit şerit eklemek.
