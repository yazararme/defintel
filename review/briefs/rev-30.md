## Revizyon 30 — operatör uyarı kanalı (günlük GitHub issue'su)

> 23 Eylül'de değişti. Plandaki push kanalı (`/alert`, `op:`, `OPERATOR_SECRET`) iptal.
> Gerekçe: aynı sonucu okuyucu altyapısına dokunmadan veriyor.

**Hedef.** Uyarı veren her build kuralı, uyarısını yalnızca operatöre iletsin. Tek bir okuyucu
bile bu uyarıları okuyucu kanalında (site, okuyucu push'u) görmesin.

**Kanal.** Uyarı üreten her çalıştırma o günün **tek** issue'sunu açar ya da günceller:

- Başlık: `DEFINTEL uyarıları · YYYY-MM-DD` (Türkiye saatiyle gün).
- Gövde: her uyarı bir satır: `- **KURAL** · metin · [çalıştırma](<Actions run URL>)`.
- Issue `yazararme` hesabına atanır (GitHub Mobile bildirimi bundan gelir). Etiket: `uyari`.
- İş akışının yerleşik `GITHUB_TOKEN`'ı (`permissions: issues: write`). Yeni sır yok.
- Aynı gün ikinci çalıştırma: aynı issue güncellenir, yalnızca **yeni** uyarı satırları eklenir
  (aynı kural + aynı metin aynı gün tekrar yazılmaz); yeni satır eklendiyse issue'ya kısa bir
  yorum düşülür ("+N uyarı · <iş akışı>") ki atanan kişi bildirim alsın. Kapalıysa yeniden açılır.
- Uyarı yoksa issue açılmaz, dokunulmaz.
- Uyarılar `main` dışındaki dallarda issue açmaz (build kaydında ve (A) özetinde kalır); yalnızca
  sınama iş akışı `[TEST] ` önekli başlıkla açabilir.
- Kural adları sabit (KAPSAM-SAYI, DÖRT-DURUM, ETİKET-BAŞLIK, KUR, H1-TEKRAR, İLK-EKRAN,
  SİLME-YOK, İPUCU-YOK, ÇEVİRİ-DEDEKTÖRÜ, İPLİK-DURUM, SLUG, KANIT-BOŞLUĞU, L1-DOLGU,
  ÇİZGİ-KONTRAST, TİP-BELİRTECİ, GEÇ-GELEN, TEKRAR-MANŞET, NOKTALI-İ). Bloklayıcı iki kural
  (DÖRT-DURUM, SİLME-YOK) da buraya yazar; iş kırmızı bitse de.

**Dosyalar.** `scripts/uyari.py` (yeni, ortak yardımcı: `uyari.ekle(KURAL, metin)` + çalıştırma
sonunda tek `python3 scripts/uyari.py` boşaltması), `.github/workflows/{build,collect-news,pull-drive}.yml`
(son adım, `if: always()`), `.github/workflows/uyari-test.yml` (sınama iş akışı). `worker.js` ve
`sw.js` **değişmez**.

### Build kuralı — OPERATÖR-YALNIZ

> Uyarı metni yalnızca issue'ya gider. Sitenin yayımlanan hiçbir dosyasına (HTML, `data/`)
> yazılmaz, okuyucu push'u (`/notify`) çağrılmaz. `uyari.py`'nin testi sahte GitHub API'siyle
> koşar: bir uyarılı, bir aynı-gün-tekrar, bir uyarısız çalıştırma; issue sayısı 1, tekrar satırı
> 0, uyarısız çalıştırmada API çağrısı 0 değilse test kırmızı. İş sonunda **(A)** özetine
> "OPERATÖR-YALNIZ: issue #N · +K satır · okuyucu push 0" satırı basılır.

### Uygulama listesi — Revizyon 30

| # | Dosya | Değişiklik | Kabul (ekran görüntüsü) |
|---|---|---|---|
| R30-P0-1 | `uyari.py` + üç iş akışı | Uyarılı çalıştırma günün issue'sunu açar | **(I)** Issue sayfası: başlık `[TEST] DEFINTEL uyarıları · <gün>`, açan `github-actions[bot]`, atanan `yazararme`, her uyarı bir satır ve kural adıyla başlıyor, satırda çalıştırma bağlantısı |
| R30-P0-2 | `uyari.py` | Aynı gün ikinci çalıştırma aynı issue'ya yalnızca yeni satırları ekler | **(I)** Aynı issue: ikinci çalıştırmanın yeni satırı eklenmiş, tekrarlanan uyarı bir kez; aynı gün için ikinci bir issue yok (issue listesi) |
| R30-P0-3 | `uyari.py` | Uyarısız çalıştırma issue'ya dokunmaz | **(A)** Uyarısız çalıştırmanın özeti "uyarı yok"; **(I)** issue'da o çalıştırmadan satır ya da yorum yok |
| R30-P1-1 | `uyari.py` testi | OPERATÖR-YALNIZ | **(A)** "OPERATÖR-YALNIZ: … okuyucu push 0" satırı yeşil; **(D)** `/data/*.json` içinde uyarı metni yok |

(I) = github.com'daki issue sayfasının ekran görüntüsü. Bu revizyonda telefon (P) ölçütü yok.

**Yapılmayacak:** uyarıyı sitede herkese açık bir dosyaya yazmak; okuyucu kanalını paylaşmak;
durum sayfası; her uyarıya ayrı issue ya da ayrı yorum (alarm yorgunluğu).
