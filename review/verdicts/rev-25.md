# Rev 25 — verdict: FAIL (the only open item is the R25-P0-1 (S) half, which cannot be checked offline)

I judged this revision from PRODUCT.md, the acceptance table, `review/shots/rev-25/`, the public run 35902549021, issue #5 and http://localhost:8000. I did not read diffs, source code, history or builder notes. The orchestrator's message had no builder rationale.

**Why FAIL.** My instructions say to FAIL when any criterion that is not a (P) criterion cannot be verified. The (S) half of R25-P0-1 is an (S) criterion. The Trend.az search cannot be shown on the 23 Sep page, because those items were dropped at collection time and are not in the stored data. As the orchestrator asked, I marked that half PENDING-HUMAN. Under my rules, though, an unverified (S) half still blocks a PASS. Every other criterion and sub-criterion passes. If the orchestrator accepts the deferral to the first live collection, nothing else blocks this revision.

(I) is not an evidence type in my instructions. The orchestrator substituted (I) for the (P) phone alert. No criterion is (I), so I used issue #5 only as supporting evidence for the broken-case alert.

I rendered pages in headless Chrome at exact viewports, 375×812 and 1440×900, each in light and dark (`prefers-color-scheme`). On `/haberler/2026-09-23.html` I did the following at every viewport:
- I clicked the rail/chip for C-UAS, Oyuncu Duyuruları and İhale.
- I searched for "Trend.az", "Hanwha" and "Oyuncu" with the page's search box.

My screenshots are in `review/shots/rev-25/reviewer/`.

## Criteria

| # | Result | Evidence |
|---|---|---|
| R25-P0-1 (A) | PASS | **Normal case, run 35902549021, job "esit":** the SİLME-YOK · 2026-09-24 table lists 9 sources with the "filtre" note: Al Arabiya English, Al Jazeera, AA analiz, AA güncel, Arab News, Dawn, Middle East Monitor, Report.az and Trend.az. For each one the okunan count equals the yazılan count (for example Trend.az 3 = 3), and each is marked "eşit". The header reads "okunan == yazılan: 11/11 kaynak eşit · filtre notlu 9 kaynak: okunan 15 · yazılan 15". The job is green. Evidence: `after/A-silme-yok-esit-ozet-girisli.jpg`. **Broken case, job "bozuk":** the header is red: "10/11 kaynak eşit · okunan 15 · yazılan 14" (`after/A-silme-yok-bozuk-ozet-girisli.jpg`). The screenshot is cropped above the failing row. I confirmed the rest with `gh run view`: the job ended red (the collection step exited 1). Its annotation, and the SİLME-YOK line in issue #5, both read "Trend.az: okunan 3, yazılan 2, düşen 'Azerbaijan and Uzbekistan agree to expand cotton trade corridor'" (`after/I-issue-5-silme-yok.jpg`). |
| R25-P0-1 (S) | PENDING-HUMAN | The 23 Sep page has no Trend.az items. Searching "Trend.az" returns 0 results in all four viewport/theme combinations (`reviewer/haberler-2026-09-23-{375,1440}-{light,dark}-q-Trendaz.png`). As the orchestrator stated, this is expected for stored data that predates the change. It must be checked on the first real collection. |
| R25-P0-2 (S) | PASS | The C-UAS ve Hava Savunma section has 14 rows. None contains "Tournai" or "Zipline". Both names now appear only under Genel Savunma Gündemi. Evidence: `reviewer/haberler-2026-09-23-{375,1440}-{light,dark}-kat-c-uas-ve-hava-savunma.png`. |
| R25-P0-3 (S) | PASS | No C-UAS row has DroneXL as its source. İhale ve Sözleşmeler has 1 row (the CAE USA C-130 contract). "Trump, … Grönland Güvenlik Anlaşmasını İmzaladı" is in Genel, not İhale. Evidence: `reviewer/…-kat-c-uas-ve-hava-savunma.png`, `reviewer/haberler-2026-09-23-{375,1440}-{light,dark}-kat-ihale-ve-sozlesmeler.png`. |
| R25-P1-1 (S) | PASS | "Oyuncu Duyuruları 12" appears in the 1440 rail and in the 375 chip row. I searched the page text of the home page, arsiv, every medya takibi page (17–23 Sep), every kaynaklar page and every report (14–23 Sep) for "Rakip Duyuruları". It appears nowhere. Evidence: `reviewer/haberler-2026-09-23-1440-light.png`, `reviewer/haberler-2026-09-23-375-dark-kat-oyuncu-duyurulari.png`. Before this revision the rail read "Rakip Duyuruları 14" (`before/haberler-2026-09-23-1440-light.png`). |
| R25-P1-2 (S) | PASS | "Hanwha, Pine Bluff'taki Mühimmat Yatırımını $2,2 Milyar'a Çıkardı" (Defense Daily) is the 6th row under OYUNCU DUYURULARI. Searching "Hanwha" returns only that row. Evidence: `reviewer/haberler-2026-09-23-375-dark-kat-oyuncu-duyurulari.png`, `reviewer/…-q-Hanwha.png`. |
| R25-P1-3 (A) | PASS | Normal build run 35902548911 has a table titled "Kategori isabeti · 2026-09-23". For each category it gives the item count plus two numbers: "Yalnız ipucuyla gelen" and "Hiçbir kelimeye değmeyen". The ipucuyla column is 0 in every category, and the header reads "yalnız ipucuyla gelen: 0". Genel shows "—", which the footnote explains: Genel has no word list of its own. The item counts (14 / 4 / 12 / 1 / 39 / 2 / 2 / 5 / 457 = 536) match the rail on the page. Evidence: `after/A-build-kategori-isabeti-girisli.jpg`. |

## Regressions

I checked the 23, 22 and 17 Sep medya takibi pages and arsiv at 375 and 1440, light and dark. I found no regressions:
- No page overflows horizontally.
- Backgrounds and text follow the theme.
- Older days show the renamed "Oyuncu Duyuruları" category.
- The arsiv shows no "Rakip" text anywhere on the page. A "Rakip" tag exists only in the hidden filter data.

Evidence: `reviewer/arsiv-*.png`, `reviewer/haberler-2026-09-22-*.png`, `reviewer/haberler-2026-09-17-*.png`.

## Observations (not failures)

- **Civil-drone noise moved into Deniz ve İnsansız Sistemler.** That section grew from 16 to 39 items. It now holds civil drone-delivery headlines, including two DroneXL items (the ABZ factory, the Belvedere/Wing delivery), Zimbabwe BVLOS approvals and Matternet OTCQB. The same kind of noise that left C-UAS is now in this section.
- **Issue #5 is older than the run.** The issue was last edited about 5 hours before run 35902549021 was triggered. Its SİLME-YOK line is word-for-word the same as the bozuk job's annotation, so it most likely came from an earlier run of the same fixture. The screenshot does not show that this particular run posted it.
- **The broken-case screenshot stops above the failing row.** `after/A-silme-yok-bozuk-ozet-girisli.jpg` ends before the Trend.az row. The red job status and the Trend.az row come from the run page itself (`gh run view`), not from the screenshot.
