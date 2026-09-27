# Headline check: 65 vs 75 characters

I am an independent checker. I did not build K5. Everything below comes from `origin/main` (report sources) and `origin/rev21-33` (layout and measuring script), measured in my own temporary worktree. I changed nothing in the repo apart from creating this file.

---

## Summary

| Headline limit | Headlines that lose ≥1 key fact (of 10) | İLK-EKRAN, 10 days, summary items ≤115 (local and CI worst) |
|---|---|---|
| 65 | **1 of 10** (20 Sep: "5,56 mm") | **passes on all 10**. Tightest: 20 Sep, 809px in CI worst (3px to spare) |
| 75 | **0 of 10** | **fails on 20 Sep** in CI worst (item 4 ends at 840px, 28px over). The other 9 pass |

Counted against the **full `title` field** instead of the displayed headline, all 10 lose facts at both limits (10 of 10 at 65 and 10 of 10 at 75), because every title carries a second development after ";". See "Which text counts as the headline" below.

---

## Method

- **Reports.** The 10 most recent reports on `origin/main`: 18–27 Sep 2026 (`source/<date>.md`). With 10 reports there are exactly 10 headlines, so "the 10 longest" is all of them.
- **Which text counts as the headline.** Every `title` field in this sample has two developments joined by ";" (129–182 characters). The build (`guard_headline()` in `build.py`) already shows only the part before ";" as the H1, and the headline rule keeps "one development". So I rewrote the **displayed H1** (the first development) and counted key facts against it. The second development is dropped by the build today, at any limit. A careful editor under the one-development rule would not bring it back.
- **Counting.** Characters include spaces, same as `check_reports.py --ilk-ekran --tani` (Python/JS string length). No rewrite contains ";", so the build would show it whole.
- **Key facts** (same strictness as `self-check.md`): numbers, company names, countries, dates, amounts, programme/product names. Swapping a name for its standard equivalent (Birleşik Krallık → İngiltere, karşı-dron → anti-dron) is not a loss. Lost product types, qualifiers and reasons are listed as "weakened"; they do not count.
- **İLK-EKRAN measurement.** Chrome at 375×812 (system Chrome 154, the repo script's own fallback). I built all 10 days with the `rev21-33` `build.py` in a temporary worktree (24–27 Sep sources and news data copied from `origin/main`, as the self-check did). Browser-only changes: I replaced the H1 text with my rewrite, then cut each summary item to ≤115 characters at a word boundary with the repo's own `IE_TANI_JS` (the self-check's "115 cut" approach; "ilk:" tokens stay in place). "CI worst" = 0.3px letter spacing plus every "ilk:" token on its own line (the model in `k5-prompt.md`). I also ran 0.45px as an extra check.
- **Pass** = `h2#ozet` top ≤300px **and** 4th summary item bottom ≤812px, both locally and in CI worst.
- **Sanity check.** My unmodified runs and the tool's own 65/110 mock reproduce the self-check's figures exactly (e.g. 20 Sep as published 326·846 / 326·898; 65+110 cut 730 / 782).

---

## Headline by headline

"Displayed H1" is what the page shows today. "Full title" is the front-matter field.

### 18 Sep
- **Full title (129):** ABD'nin 1,5 milyar $'lık DHS karşı-dron kanalı 9+7 firmayla kapandı; küçük kalibre mühimmat 2031'e kadar tek tedarikçiye bağlandı
- **Displayed H1 (67):** ABD'nin 1,5 milyar $'lık DHS karşı-dron kanalı 9+7 firmayla kapandı

| Limit | Rewrite | Length | Key facts lost |
|---|---|---|---|
| 65 | ABD'de 1,5 milyar $'lık DHS anti-dron kanalı 9+7 firmayla kapandı | 65 | none |
| 75 | ABD'nin 1,5 milyar $'lık DHS karşı-dron kanalı 9+7 firmayla kapandı (unchanged) | 67 | none |

### 19 Sep
- **Full title (179):** Letonya imzalı Archer niyet mektubunu bozup fiyat, teslim süresi ve yerli sanayi katılımı gerekçesiyle Çek Morana'ya geçti; 50 mm güdümlü yakınlık fünyeli mermi uçuş testini geçti
- **Displayed H1 (122):** Letonya imzalı Archer niyet mektubunu bozup fiyat, teslim süresi ve yerli sanayi katılımı gerekçesiyle Çek Morana'ya geçti

| Limit | Rewrite | Length | Key facts lost |
|---|---|---|---|
| 65 | Letonya Archer'dan döndü, fiyat ve süre için Çek Morana'yı seçti | 64 | none. Weakened: the signed letter of intent; the local-industry reason |
| 75 | Letonya fiyat, teslim ve yerli pay nedeniyle Archer'dan Çek Morana'ya geçti | 75 | none. Weakened: the signed letter of intent |

### 20 Sep
- **Full title (177):** ABD Deniz Piyadeleri 400 bin çok parçacıklı 5,56 mm anti-dron mermisi aldı ve 2027 için 1 milyon daha planlıyor; Pentagon 60 bin dronluk alımın ikinci eleme sonuçlarını açıkladı
- **Displayed H1 (111):** ABD Deniz Piyadeleri 400 bin çok parçacıklı 5,56 mm anti-dron mermisi aldı ve 2027 için 1 milyon daha planlıyor

| Limit | Rewrite | Length | Key facts lost |
|---|---|---|---|
| 65 | ABD Deniz Piyadesi 400 bin anti-dron mermi aldı, 2027'de 1 milyon | 64 | **5,56 mm.** Weakened: "çok parçacıklı"; "daha … planlıyor" (it is a plan, and it is additional) |
| 75 | ABD Deniz Piyadesi 400 bin 5,56 mm anti-dron mermi aldı, 2027'de +1 milyon | 74 | none. Weakened: "çok parçacıklı"; "planlıyor" |

At 65 I could not keep ABD, 400 bin, 5,56 mm, 2027 and 1 milyon together; the shortest full version I found was 73.

### 21 Sep
- **Full title (160):** ABD müfettiş raporu: Körfez'de Nisan–Haziran'da 6.000'i aşkın saldırı dronu önlendi; İngiltere üslerinde dron olayları 340'a çıktı, C-UAS'a 750 milyon £ ayrıldı
- **Displayed H1 (83):** ABD müfettiş raporu: Körfez'de Nisan–Haziran'da 6.000'i aşkın saldırı dronu önlendi

| Limit | Rewrite | Length | Key facts lost |
|---|---|---|---|
| 65 | ABD müfettişi: Körfez'de Nisan–Haziran'da 6.000+ dron önlendi | 61 | none. Weakened: "saldırı" (attack drones) |
| 75 | ABD müfettişi: Körfez'de Nisan–Haziran'da 6.000+ saldırı dronu önlendi | 70 | none |

### 22 Sep
- **Full title (182):** Hanwha ABD'deki 155 mm sevk barutu ve base bleed yatırımını 2,2 milyar $'a çıkardı; Leonardo 30 mm havada infilak mühimmatlı X-GUN'u Kongsberg'in çok katmanlı C-UAS sistemine veriyor
- **Displayed H1 (82):** Hanwha ABD'deki 155 mm sevk barutu ve base bleed yatırımını 2,2 milyar $'a çıkardı

| Limit | Rewrite | Length | Key facts lost |
|---|---|---|---|
| 65 | Hanwha ABD'deki 155 mm barut yatırımını 2,2 milyar $'a çıkardı | 62 | none by the categories. Weakened: **"base bleed"** (a product type, half of the investment); "sevk" |
| 75 | Hanwha ABD'de 155 mm barut ve base bleed yatırımını 2,2 milyar $'a çıkardı | 74 | none. Weakened: "sevk" (propellant) |

Borderline: if "base bleed" is treated as a product name, the 65 count becomes 2 of 10.

### 23 Sep
- **Full title (174):** Letonya araç üstü 155 mm obüste Archer'ı bırakıp Çek Morana'yı seçti; Leonardo 76 mm deniz topu üretimini Danimarka'ya taşıyor, Fransa Irak'a kinetik C-UAS önleyicisi veriyor
- **Displayed H1 (68):** Letonya araç üstü 155 mm obüste Archer'ı bırakıp Çek Morana'yı seçti

| Limit | Rewrite | Length | Key facts lost |
|---|---|---|---|
| 65 | Letonya araç üstü 155 mm obüste Archer yerine Çek Morana'yı seçti | 65 | none |
| 75 | unchanged | 68 | none |

### 24 Sep
- **Full title (170):** Falcon Peak 26.2 tamamlandı: 20'den fazla tedarikçi tek bir komuta-kontrol omurgasına bağlandı; Tayvan 178 adetlik 105 mm araç üstü top programını gerçek atışla sergiledi
- **Displayed H1 (94):** Falcon Peak 26.2 tamamlandı: 20'den fazla tedarikçi tek bir komuta-kontrol omurgasına bağlandı

| Limit | Rewrite | Length | Key facts lost |
|---|---|---|---|
| 65 | Falcon Peak 26.2'de 20+ tedarikçi tek komuta ağına bağlandı | 59 | none. Weakened: "tamamlandı"; "komuta-kontrol" → "komuta" |
| 75 | Falcon Peak 26.2'de 20'yi aşkın tedarikçi tek komuta-kontrol ağına bağlandı | 75 | none. Weakened: "tamamlandı" |

### 25 Sep
- **Full title (182):** Birleşik Krallık 105 mm Light Gun namlu üretimini yurda geri getiriyor; KNDS Fransa hard-kill katmanını önleyici drona bağlıyor, Etiyopya'da Çin yapımı 30 mm'lik FK-2000 görüntülendi
- **Displayed H1 (70):** Birleşik Krallık 105 mm Light Gun namlu üretimini yurda geri getiriyor

| Limit | Rewrite | Length | Key facts lost |
|---|---|---|---|
| 65 | İngiltere 105 mm Light Gun namlu üretimini yurda geri getiriyor | 63 | none |
| 75 | unchanged | 70 | none |

### 26 Sep
- **Full title (165):** ABD ve İngiltere, C-UAS elemesi FLYTRAP 6.0'ı dünya çapındaki firmalara açtı; Aralık'taki lazer atış elemesinin ardında 200 milyon $'lık değerlendirme sözleşmesi var
- **Displayed H1 (76):** ABD ve İngiltere, C-UAS elemesi FLYTRAP 6.0'ı dünya çapındaki firmalara açtı

| Limit | Rewrite | Length | Key facts lost |
|---|---|---|---|
| 65 | ABD-İngiltere C-UAS elemesi FLYTRAP 6.0 dünya firmalarına açıldı | 64 | none |
| 75 | ABD ve İngiltere, C-UAS elemesi FLYTRAP 6.0'ı dünya firmalarına açtı | 68 | none |

### 27 Sep
- **Full title (144):** ABD Ordusu uygun maliyetli önleyici yarışmasında 30 finalisti açıkladı; liste ABD dışı firmalara da açık ve 31 Aralık'ta kazananlar belli olacak
- **Displayed H1 (70):** ABD Ordusu uygun maliyetli önleyici yarışmasında 30 finalisti açıkladı

| Limit | Rewrite | Length | Key facts lost |
|---|---|---|---|
| 65 | ABD Ordusu ucuz önleyici yarışmasında 30 finalisti açıkladı | 59 | none. Weakened: "uygun maliyetli" → "ucuz" (slight change of tone) |
| 75 | unchanged | 70 | none |

### Counts

| | At 65 | At 75 |
|---|---|---|
| Lose ≥1 key fact (vs displayed H1) | **1 of 10** (20 Sep) | **0 of 10** |
| Same, if "base bleed" counted as a name | 2 of 10 | 0 of 10 |
| Have weakened meaning (not counted) | 6 of 10 | 4 of 10 |
| Lose ≥1 key fact vs the full `title` field | 10 of 10 | 10 of 10 |
| Rewrites that are the published H1 unchanged | 0 | 4 (18, 23, 25, 27 Sep) |

---

## İLK-EKRAN at 375×812 with summary items ≤115

Figures are `h2#ozet` top · 4th item bottom, in px. "H1 lines" = headline lines (local / CI worst).

### Headline at 75 (my 75 rewrites)

| Day | H1 length | H1 lines (local / CI) | Local | CI worst | Pass? |
|---|---|---|---|---|---|
| 18 Sep | 67 | 3 / 3 | 263 · 704 | 263 · 756 | ✅ |
| 19 Sep | 75 | 3 / 3 | 263 · 756 | 263 · 756 | ✅ |
| 20 Sep | 74 | 3 / **4** | 263 · 730 | 294 · **840** | ❌ (28px over) |
| 21 Sep | 70 | 3 / 3 | 263 · 651 | 263 · 651 | ✅ |
| 22 Sep | 74 | 3 / **4** | 263 · 651 | 294 · 709 | ✅ |
| 23 Sep | 68 | 3 / 3 | 263 · 704 | 263 · 756 | ✅ |
| 24 Sep | 75 | 3 / 3 | 263 · 651 | 263 · 677 | ✅ |
| 25 Sep | 70 | 3 / 3 | 263 · 677 | 263 · 730 | ✅ |
| 26 Sep | 68 | 3 / 3 | 263 · 704 | 263 · 730 | ✅ |
| 27 Sep | 70 | 3 / **4** | 263 · 677 | 294 · 762 | ✅ |
| **All pass?** | | | yes | **no (20 Sep)** | **9 of 10** |

### Headline at 65 (my 65 rewrites), for comparison

| Day | H1 length | H1 lines (local / CI) | Local | CI worst | Pass? |
|---|---|---|---|---|---|
| 18 Sep | 65 | 3 / 3 | 263 · 704 | 263 · 756 | ✅ |
| 19 Sep | 64 | 3 / 3 | 263 · 756 | 263 · 756 | ✅ |
| 20 Sep | 64 | 3 / 3 | 263 · 730 | 263 · 809 | ✅ (3px to spare) |
| 21 Sep | 61 | 3 / 3 | 263 · 651 | 263 · 651 | ✅ |
| 22 Sep | 62 | 3 / 3 | 263 · 651 | 263 · 677 | ✅ |
| 23 Sep | 65 | 3 / 3 | 263 · 704 | 263 · 756 | ✅ |
| 24 Sep | 59 | 3 / 3 | 263 · 651 | 263 · 677 | ✅ |
| 25 Sep | 63 | 3 / 3 | 263 · 677 | 263 · 730 | ✅ |
| 26 Sep | 64 | 3 / 3 | 263 · 704 | 263 · 730 | ✅ |
| 27 Sep | 59 | 3 / 3 | 263 · 677 | 263 · 730 | ✅ |
| **All pass?** | | | yes | yes | **10 of 10** |

### What drives the difference

- Locally, every 75 headline fits in 3 lines, and all 10 days pass at both limits.
- In the CI worst case, 3 of the 10 headlines at 70–74 characters (20, 22, 27 Sep) wrap to a 4th line. Each extra headline line pushes the summary down about 31px. The heading moves from 263 to 294px (6px under the 300px limit) and item 4 moves down by the same amount.
  - 27 Sep's **published** H1 (70 characters, unchanged) already wraps to 4 lines in CI worst. So does any headline around 70+ with long words: this matches the builder's note that the shortest 4-line cut was 70 characters.
  - 22 and 27 Sep have room for it (709 and 762). 20 Sep does not, because its summary items are the tallest in the sample.
- **20 Sep fails at 75 even with summary items at 110** (294 · 814, 2px over; extra check). At 115 it is 28px over.
- At 0.45px letter spacing (extra check), 19 Sep's 75 headline also wraps to 4 lines (294 · 788, still passes); 20 Sep stays at 840.
- A 4-line headline leaves `h2#ozet` at 294px. A 5th line would put it at about 326px and fail the heading test on its own; none of my rewrites reached 5 lines.

### The trade-off, for the customer

| Headline limit | Key facts lost (10 headlines) | Weakened meaning | İLK-EKRAN, 10 days (items ≤115, CI worst) |
|---|---|---|---|
| 65 | 1 of 10 (2 if "base bleed" counts) | 6 of 10 | all 10 pass; 20 Sep has 3px to spare |
| 75 | 0 of 10 | 4 of 10 | 9 of 10 pass; 20 Sep fails by 28px (by 2px even with items ≤110) |

At 75 the editor keeps every key fact, and 4 of the 10 published headlines need no change at all. The cost is that headlines of 70–75 characters can wrap to 4 lines under the CI worst-case model, and on a day with tall summary items (20 Sep) that pushes item 4 below the first screen. At 65 no headline wrapped to 4 lines, and all days pass, but with only 3px on 20 Sep.

---

## Limitations

- The rewrites are one editor's work (mine). "Key fact" is a judgment call; I applied the self-check's categories and listed borderline cases separately (base bleed, "Nisan–Haziran" kept as-is rather than "2. çeyrek").
- Whether a headline wraps to a 4th line depends on the exact words, not only the character count. A different 75-character rewrite of 20 Sep could stay at 3 lines, or one of the passing days could wrap. The 75 result is therefore sensitive to wording; the 65 result had a 5-character margin under the shortest known 4-line cut (70).
- Summary items were cut by machine at a word boundary to ≤115, which fills items almost to the limit (the self-check's "115 cut"). Real rewrites break lines differently. Small margins (3px, 6px) are not reliable in either direction.
- "CI worst" is the builder's synthetic model (0.3px letter spacing plus every "ilk:" token on its own line), measured on local Chrome 154. It is not a run in GitHub Actions, where Ubuntu Chromium's own line breaks are wider.
- Ten days, none of them an alarm day. On an alarm day the band sits above the headline, so the headline's 4th line would matter more; that is not tested here.
- 24–27 Sep were rebuilt with the `rev21-33` layout in my worktree. They are not the pages published on `main`, which still use the older layout.
