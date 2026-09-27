# K5 self-check: criterion fairness and summary-length limits

I am an independent checker. I did not build K5. Everything below comes from files on `origin/rev21-33` and `origin/main`, and from my own browser measurements in a separate worktree. I changed nothing in the repo apart from creating this file.

---

## a) Is the reworded K5-2 a fair test of the customer's goal?

**Verdict: WEAKER.** The rewording is understandable, because published text cannot be changed. It is still a weaker test than the one the customer asked for.

### The wording

| Where | Text |
|---|---|
| Customer decision (brief `review/briefs/k5.md`, "Karar") | "alarm günü muafiyeti **yok**; eşikler **değişmez**; kural kalır. Nedeni bul ve nedeni düzelt." |
| Original K5-2 (brief, acceptance table) | "**(S)** düzen kaynaklı taşan günler (ör. alarm günü 14 Eyl) düzeltmeden sonra 375×812'de özet başlığı ve 4 madde ilk ekranda; alarm bandı hâlâ özetin üstünde ve okunur" |
| Reworded K5-2 (only in `review/progress.md`, K5 row) | "Orkestratör K5-2 ölçütünü yayımlanmış metin değişemediği için **"yapısal neden kalktı + sınırla geçer"** olarak yeniden yazdı." |
| How the final review applied it (`review/verdicts/k5.md`) | PASS because "that structural cause is gone" and, with the text cut to the limits in the browser, 14 Sep "passes: 277 / 718". As published, 14 Sep still overflows at 331 / 903 (330 / 929 in CI). |

The brief's acceptance table was never changed. The reworded criterion exists only as a one-line paraphrase in `progress.md`.

### Why it is weaker

The original criterion checks an **outcome on the real page**: after the fix, the alarm day at 375×812 shows the summary heading and 4 items on the first screen. The reworded one checks two **proxies**:

1. the layout no longer pushes the summary down, and
2. a mock copy, with the text cut by machine to the prompt limits, would pass.

The published 14 Sep page still fails the rule. The fix now depends on the report agent keeping to the limits in the future. No check in this acceptance verifies that; K5-4 is PENDING-HUMAN.

**What the reworded test can detect**
- Any layout element that still sits between the headline and the summary. The (A) table's "ALARMLAR özetten önce 0px" catches this.
- Whether the chosen limits are enough on the pixel geometry of the 10 sample days, under the builder's simulated CI model.

**What it cannot detect**
- **Whether the agent will obey the limits.** The build does not count characters: `guard_headline()` warns only above 14 words. The first 4 days after the sample, 24–27 Sep, show how far current writing is from the limits. The prompt sentences have not been pasted yet, so these days are not a compliance failure.
  - All 10 headlines of 18–27 Sep are over 65 characters: the displayed headline runs 67–122 characters, and the full `title` field runs 129–182.
  - 36 of the 50 summary items are over 110.
- **Whether the limits can be met without dropping facts from the summary.** Section b) shows that at 110, 3 of the 10 longest items lose a key fact.
- **Whether the mock copy looks like real text.** The mock cuts sentences mid-thought at a word boundary. A real rewrite breaks into lines differently, and the margins are small: 17 Sep passes by 3px, and 20 Sep by 3px in b).
- **Real CI line breaks.** "CI worst case" is a synthetic model (0.3px letter spacing, and every "ilk:" token on its own line) measured locally. It is not a measurement taken in CI.

**What evidence would make it equivalent to the original.** After the prompt sentences are pasted on merge day:
- a run of new daily reports (for example, 10 consecutive days) that pass İLK-EKRAN as published, both locally and in the real CI run;
- at least one of those days is an alarm day;
- the headline, alarm_title and item lengths are recorded for each of those days, to show that the pass comes from the limits being kept.

Until then, the honest status of the original K5-2 is "layout cause removed; the outcome on real pages is not yet shown."

---

## b) Can a careful editor keep summary items within 110 characters without losing key facts?

### Method

- **Reports.** I used the 10 most recent reports on `origin/main`: 18–27 Sep 2026, from `source/*.md`.
  - 18–23 Sep are identical on both branches.
  - For 24–27 Sep, I copied the sources and news data into my own worktree of `origin/rev21-33` and built them there with the branch's `build.py`, so that they render with the K5 layout.
- **Counting.** Lengths are the displayed item text, counted the same way as `check_reports.py --ilk-ekran --tani`: spaces are included, and the "G1 —" prefix and "ilk: …" tokens are excluded. The agent's own count on the raw markdown line may differ by a few characters.
- **Key facts** mean numbers, company or programme names, countries, dates and amounts. A fact that moves to "its own block" counts as lost. I also note meaning that is weakened but falls outside these categories. That column is not included in the count.

### The 10 longest items (from 50 items across 10 days) and my rewrites at 110

| # | Day · item | Orig. length | Original | My rewrite (≤110) | Length | Key facts lost |
|---|---|---|---|---|---|---|
| 1 | 27 Sep · 1 | 203 | ABD Ordusu, uygun maliyetli önleyici yarışması xTech\|Apex Intercept'te dört kategoride 30 finalist açıkladı; liste ABD dışında Avustralya ve Birleşik Krallık firmalarını da içeriyor (26 Eylül) (bkz. EK). | ABD Ordusu, xTech\|Apex Intercept'te 4 kategoride 30 finalist seçti; Avustralyalı ve İngiliz firmalar da var. | 108 | **Date (26 Eylül).** Also weakened: "uygun maliyetli" |
| 2 | 26 Sep · 5 | 182 | ABD Deniz Piyadeleri, amfibi muharebe araçlarına karıştırıcı takmak için 24 Eylül'de 15,7 milyon $'lık tek kaynak siparişi verdi; tam program yarışması 2027 mali yılında planlanıyor. | ABD Deniz Piyadeleri, amfibi araçlara karıştırıcı için 24 Eylül'de 15,7 milyon $'lık tek kaynak sipariş verdi. | 110 | **Full competition in FY2027** |
| 3 | 26 Sep · 2 | 180 | Aralık'ta Dugway'de yapılacak yüksek enerjili lazer atış elemesinin ardında, bir yıl içinde operasyonel değerlendirme sözleşmelerine ayrılacak 200 milyon $'a kadar bütçe bulunuyor. | Aralık'taki Dugway lazer elemesini bir yılda 200 milyon $'a kadar değerlendirme sözleşmeleri izleyebilir. | 105 | none. Weakened: "yüksek enerjili", "operasyonel" |
| 4 | 26 Sep · 1 | 173 | ABD ve İngiltere, Mayıs 2027'de yaklaşık 1.000 asker ve 50 km²'yi aşan sahada yapılacak FLYTRAP 6.0 karşı-dron elemesine başvuruyu dünya çapındaki firmalara açtı (25 Eylül). | ABD ve İngiltere, Mayıs 2027'deki 1.000 askerli FLYTRAP 6.0 karşı-dron elemesini tüm dünyaya açtı (25 Eylül). | 109 | **50 km² site** |
| 5 | 26 Sep · 3 | 173 | Romanya, 54 K9 obüs ve 36 K10 ikmal aracından oluşan yaklaşık 1 milyar $'lık siparişin ilk 18+12'lik partisini teslim aldı; üretimin %80'i Romanya sanayisinden hedefleniyor. | Romanya, 1 milyar $'lık 54 K9 ve 36 K10 siparişinin ilk 18+12'lik partisini aldı; hedef %80 yerli üretim. | 105 | none. Weakened: "obüs", "ikmal aracı" |
| 6 | 26 Sep · 4 | 163 | Anduril ile Estonyalı ORIGIN, BLAZE önleyici dronunu Lattice komuta-kontrol katmanına bağlamak ve Letonya'da ortak test yapmak için 25 Eylül'de mutabakat imzaladı. | Anduril ve Estonyalı ORIGIN, BLAZE'i Lattice'e bağlayıp Letonya'da test için 25 Eylül'de mutabakat imzaladı. | 108 | none. Weakened: what BLAZE and Lattice are |
| 7 | 27 Sep · 4 | 161 | İtalya, 132 tank ve 140 destek aracı için 5,14 milyar €'luk ana muharebe tankı kalemini 21 Eylül'de ilana çıkardı; teslimatlar yaklaşık 2035'e kadar öngörülüyor. | İtalya, 132 tank ve 140 destek aracı için 5,14 milyar €'luk kalemi 21 Eylül'de ilana çıkardı; teslimat ~2035. | 109 | none |
| 8 | 25 Sep · 3 | 159 | Etiyopya'ya Çin menşeli, 30 mm çift namlu ve 12 füze taşıyan FK-2000 hava savunma sisteminden en az iki adet geldiği görüntülerle iddia edildi (doğrulanmamış). | Görüntülere göre Etiyopya'ya en az iki Çin yapımı FK-2000 (30 mm çift namlu, 12 füze) geldi (doğrulanmamış). | 108 | none. Weakened: "hava savunma sistemi" |
| 9 | 23 Sep · 2 | 156 | Polonya'nın 18 bataryalık, yaklaşık 1,5 milyar $'lık SAN CUAS programında C-UAS istasyonlarının GPS'siz konumlanması için 18,5 milyon $'lık sipariş verildi. | Polonya'nın 1,5 milyar $'lık 18 bataryalık SAN C-UAS programında GPS'siz konum için 18,5 milyon $ sipariş. | 106 | none. The sentence loses its verb (weak style) |
| 10 | 25 Sep · 1 | 150 | Birleşik Krallık, 105 mm Light Gun desteği ve Sheffield'de 105/155 mm namlu üretiminin yeniden kurulması için dört yıllık anlaşma imzaladı (24 Eylül). | İngiltere, Light Gun desteği ve Sheffield'de 105/155 mm namlu üretimi için 4 yıllık anlaşma yaptı (24 Eylül). | 109 | none by the categories. Weakened: **"yeniden kurulması"** (reshoring), which is the day's headline point |

**Count at 110: 3 of 10 lose at least one key fact** (items 1, 2 and 4). If weakened meaning also counted, it would be 4 of 10 (adding item 10). Items 1 and 2 cannot keep every fact within 110 without jargon ("MY2027") or cutting the programme name. My best full versions were 116 and 118 characters.

### Headline and alarm title across the 10 days

| | Result |
|---|---|
| Headline ≤65 | **10 of 10 exceed.** The displayed headline (the build shows the part before ";") runs 67–122 characters: 67, 122, 111, 83, 82, 68, 94, 70, 76 and 70. The full `title` field runs 129–182. |
| alarm_title ≤70 | Not testable. None of 18–27 Sep is an alarm day, so the alarm_title field is empty on every day. |

These reports were written before the prompt sentences are pasted (merge day), so they show current habits, not rule-breaking.

### Looser limit: the smallest that loses a key fact on at most 2 of 10

Following the steps you asked for (120, 130, …), the answer is **120**. I redid all 10 rewrites at 120:

| # | Rewrite at ≤120 | Length | Key facts lost |
|---|---|---|---|
| 1 | ABD Ordusu xTech\|Apex Intercept'te 4 kategoride 30 finalist seçti; Avustralyalı, İngiliz firmalar da var (26 Eylül). | 116 | none |
| 2 | ABD Deniz Piyadeleri amfibi araca karıştırıcı için 15,7 milyon $ tek kaynak sipariş verdi (24 Eylül); yarışma 2027'de. | 118 | **"mali yıl" (fiscal-year) qualifier.** "2027" is kept, but FY2027 starts in Oct 2026. Counted as lost to be strict |
| 3 | Aralık'taki Dugway lazer elemesini, bir yılda 200 milyon $'a kadar operasyonel değerlendirme sözleşmeleri izleyebilir. | 118 | none |
| 4 | ABD ve İngiltere, 1.000 askerli, 50 km²'lik FLYTRAP 6.0 karşı-dron elemesini (Mayıs 2027) dünyaya açtı (25 Eylül). | 114 | none |
| 5 | Romanya, 1 milyar $'lık 54 K9 obüs ve 36 K10 siparişinin ilk 18+12'lik partisini aldı; hedef %80 yerli üretim. | 110 | none |
| 6 | Anduril ve Estonyalı ORIGIN, BLAZE önleyicisini Lattice'e bağlayıp Letonya'da test için 25 Eylül'de mutabakat imzaladı. | 119 | none |
| 7 | İtalya, 132 tank ve 140 destek aracı için 5,14 milyar €'luk kalemi 21 Eylül'de ilana çıkardı; teslimatlar 2035'e kadar. | 119 | none |
| 8 | Görüntülere göre Etiyopya'ya en az iki Çin yapımı FK-2000 (30 mm çift namlu, 12 füze) geldi (doğrulanmamış). | 108 | none |
| 9 | Polonya'nın 1,5 milyar $'lık 18 bataryalık SAN C-UAS programında GPS'siz konumlama için 18,5 milyon $ sipariş verildi. | 118 | none |
| 10 | İngiltere, Light Gun desteği ve Sheffield'de 105/155 mm namlu üretimini yeniden kuran 4 yıllık anlaşma yaptı (24 Eylül). | 120 | none (the reshoring point is back) |

**Count at 120: 1 of 10.**

I also tested **115**, which is between the steps. Items 1 and 4 keep every fact at 113 and 114 characters. Item 2 loses the FY2027 competition. Items 6, 9 and 10 fall back to their shorter 110-style forms: item 10 loses "yeniden", and item 6 loses "önleyici". **Count at 115: 1 of 10.**

### İLK-EKRAN with the looser limits (375×812, headline cut to 65)

I used the K5 builder's method: a browser-only mock copy, with each item cut at a word boundary to the limit and the "ilk:" tokens kept. I reused the repo's own measuring script (`IE_TANI_JS`).
- "Local" means as rendered.
- "CI worst" means 0.3px letter spacing, plus every "ilk:" token on its own line.
- "+rewrites" means my rewrites above are placed in the page first, and the other items are then cut by machine.

My unmodified run reproduces the (A) tool's own output for these pages exactly.

**Pass** needs `h2#ozet` top ≤300 and the 4th item's bottom ≤812, both locally and in CI worst. With the limits applied, `h2` is at 263px on every day. Figures below are the 4th item's bottom, local / CI worst, in px.

| Day | As published (h2 · item 4, local / CI worst) | 110 (current limit) | 120 cut | 120 +rewrites | 115 cut | 115 +rewrites |
|---|---|---|---|---|---|---|
| 18 Sep | 263·756 / 263·809 ✅ | 677 / 756 ✅ | 756 / 782 ✅ | 756 / 782 ✅ | 704 / 756 ✅ | 704 / 756 ✅ |
| 19 Sep | 326·820 / 326·820 ❌ | 730 / 730 ✅ | 756 / 756 ✅ | 756 / 756 ✅ | 756 / 756 ✅ | 756 / 756 ✅ |
| 20 Sep | 326·846 / 326·898 ❌ | 730 / 782 ✅ | 756 / **835 ❌** | 756 / **835 ❌** | 730 / 809 ✅ | 730 / 809 ✅ |
| 21 Sep | 294·683 / 294·683 ✅ | 651 / 651 ✅ | 651 / 651 ✅ | 651 / 651 ✅ | 651 / 651 ✅ | 651 / 651 ✅ |
| 22 Sep | 294·709 / 294·735 ✅ | 651 / 677 ✅ | 677 / 704 ✅ | 677 / 704 ✅ | 651 / 677 ✅ | 651 / 677 ✅ |
| 23 Sep | 263·756 / 263·782 ✅ | 704 / 730 ✅ | 730 / 756 ✅ | 730 / 756 ✅ | 704 / 756 ✅ | 730 / 756 ✅ |
| 24 Sep | 294·735 / 326·793 ❌ | 651 / 677 ✅ | 677 / 704 ✅ | 677 / 704 ✅ | 651 / 677 ✅ | 651 / 677 ✅ |
| 25 Sep | 263·809 / 263·809 ✅ | 677 / 730 ✅ | 704 / 756 ✅ | 677 / 756 ✅ | 677 / 730 ✅ | 677 / 730 ✅ |
| 26 Sep | 294·893 / 294·945 ❌ | 704 / 730 ✅ | 704 / 756 ✅ | 704 / 730 ✅ | 704 / 730 ✅ | 677 / 704 ✅ |
| 27 Sep | 263·835 / 294·867 ❌ | 651 / 651 ✅ | 730 / 756 ✅ | 704 / 756 ✅ | 677 / 730 ✅ | 677 / 730 ✅ |
| **All 10 pass?** | 5 of 10 | **yes** | **no** (20 Sep) | **no** (20 Sep) | **yes** | **yes** |

- **120 fails İLK-EKRAN** in the CI worst case on 20 Sep: 835px, 23px over. This matches the K5 builder's own note that 120 fails on 20 Sep. 130 fails on the same day (835), so I did not test 140 and above.
  - The failing day is not one of the 10 longest items. At 120, three of 20 Sep's ordinary 124–130-character items still wrap to 5 lines each at 0.3px.
- **115 passes on all 10 days**, locally and in the CI worst case, and also at 0.45px.
  - 116 passes as well; 117 and 118 fail on 20 Sep (835).
  - 20 Sep at 115 has **3px** to spare (809). One extra wrapped line adds 26px and would turn it red. Its safety margin is the same as 17 Sep's today.

### The trade-off, for the customer

| Item limit | Key fact lost (10 longest items) | İLK-EKRAN, 10 days (CI worst) |
|---|---|---|
| 110 (current) | 3 of 10 | passes on all 10, with a 30px margin on the worst day |
| 115 | 1 of 10 | passes on all 10, with only 3px on 20 Sep |
| 120 | 1 of 10 | fails on 20 Sep (835) |

No limit from the 120/130/140 steps passes İLK-EKRAN. 115 meets both tests on this sample, but only just. The choice is between a few more facts moving out of the summary at 110 and a first-screen rule that is likely to flicker red at 115.

### Limitations

- The rewrites are one editor's work (mine), and "key fact" is a judgment call. I applied it strictly and listed borderline cases separately.
- Ten days, and none of them an alarm day. The alarm_title limit and the alarm-day geometry are not exercised here.
- "CI worst" is the builder's synthetic model, measured on local Chrome. I used the system Chrome channel, the same fallback the repo script uses, because the venv's headless Chromium is not installed. It is not a real CI run.
- The machine cut fills each item almost to the limit. A real writer at the same limit would break lines differently, so small margins (3px) are not reliable in either direction.
- 24–27 Sep were rebuilt with the branch's layout in my worktree. They are not the pages published on `main`, which still use the older layout.
