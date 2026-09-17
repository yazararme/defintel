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
