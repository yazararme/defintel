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

**Yapılmayacak:** S1; sözlüğü büyütüp kapıyı yeniden denemek; S7.


### Orkestratör notu (23 Eylül)

- **Müşteri kararı (R25.1):** tutulan savunma dışı başlıklar **çevrilir — yalnız başlık, özet
  yok**. `savunma_terimi: false` kalemler başlık çevirisine girer, özet çağrısına girmez.
- **S-kodlarının tanımı:** S2, S3, S4, S6, S8 için yalnızca `audit/content.md`'deki o maddeleri
  oku (başka bir şey değil).
- **Sabah hattı çalıştırılmaz** (ağ, Claude/çeviri çağrısı, Drive yasak). Bu yüzden:
  - SİLME-YOK **(A)**: Rev 31'in `gec-gelen-test.yml` / `--fixture` kalıbıyla, 9 filtre notlu
    kaynağı temsil eden fixture'la çevrimdışı; okunan == yazılan tablosu özet sayfasında.
    Eşitliği bilerek bozan bir iş → `[TEST] ` issue'da SİLME-YOK satırı ve kırmızı iş.
  - Kategori ölçütleri (P0-2, P0-3, P1-1, P1-2, P1-3) için **ağsız yeniden kategorileme**:
    saklı günlük veriye (`data/news/<gün>.json`) yeni kuralları uygulayan bir yol ekle ve 23
    Eylül'e uygula; hangi günlere uyguladığını notlarda yaz. Kalem eklenmez/silinmez, yalnız
    kategori alanları değişir.
  - **R25-P0-1'in (S) yarısı** (Trend.az'dan savunma dışı bir başlığın aranabilmesi) 23 Eylül'de
    doğrulanamaz: o kalemler toplanırken düşürüldü, veride yok. Bu yarı canlıda, dal main'e
    alındıktan sonraki ilk toplamada kontrol edilir → inceleyici PENDING-HUMAN sayar.
- **İPUCU-YOK** ve **S8 (A)**: normal `build.yml` çalıştırmasının özetinde kategori başına iki
  sayı. SİLME-YOK bloklayıcıdır (Rev 30: `uyari.BLOKLAYICI`).
