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

### Orkestratör notu (23 Eylül)

- **Rev 30 kanalı:** uyarılar günün GitHub issue'suna gider (`scripts/uyari.py`,
  `uyari.ekle("KAPSAM-SAYI", "…")`; `build.py` içinden `from scripts import uyari`; iş sonunda
  son adım boşaltır). Yukarıdaki **(P)** ölçütü → **(I)**: issue sayfasında
  "KAPSAM-SAYI: 63/64" satırı. `main` dışındaki dallarda issue ancak `UYARI_TEST_ONEK`
  ayarlıysa (`[TEST] ` önekiyle) açılır.
- **"Bilerek bozulduğunda" kanıtı** koda bozuk commit atmadan `build.yml`'in
  `workflow_dispatch` girdisiyle üretilmeli. `build.yml`'de zaten `boz` girdisi var
  (DÖRT-DURUM, Rev 22); aynı kalıbı izle (ör. yeni bir girdi ya da seçenek). Bozuk
  çalıştırma `UYARI_TEST_ONEK: "[TEST] "` ile koşar, ve o çalıştırmanın ürettiği sayfa
  (sayı basılmamış hali) (S) kanıtı olarak artifact'e yüklenir.
- **64/64 hâli (S):** yerelde, testler 64/64 geçtiğinde /oyuncular.html'de "Bugün N", "N gün"
  ve yaş jetonları görünmeli.
- **İki hâl, iki kanıt:** R21-P0-1 ve R21-P0-2'nin (S) ölçütleri (sayı yok, alfabetik sıra,
  "izlenen 64") **64/64'ün altındaki** hâlin ölçütleri. R21-P1-3'ün 64/64 ölçütü sayıları ve
  sıklık sırasını geri getirir. İki hâlin de sayfası kanıt olarak üretilebilmeli: yerelde bir
  bayrak/ortam değişkeniyle bir oyuncunun testini bozarak (`build.py` ör. `KAPSAM_BOZ=<oyuncu>`)
  ve CI'da dispatch girdisiyle.
