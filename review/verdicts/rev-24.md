# Rev 24 — verdict: PASS

I judged this revision from PRODUCT.md, the acceptance table, `review/shots/rev-24/`, the public issue #5 and http://localhost:8000. I did not read diffs, source code, history or builder notes. The orchestrator's message had no builder rationale.

(I) is not an evidence type in my instructions. The orchestrator substituted (I) for the (P) phone alert, so I judged R24-P1-2's alert half from issue #5 instead of marking it PENDING-HUMAN.

I rendered pages in headless Chrome at exact viewports: 375×812, 834×1112 and 1440×900, each in light and dark (`prefers-color-scheme`). My screenshots are in `review/shots/rev-24/reviewer/`.

## Criteria

| # | Result | Evidence |
|---|---|---|
| R24-P0-1 (S) | PASS | **375×812, 23 Sep and home page:** the first screen shows the masthead, day bar, title and chip row. The YÖNETİCİ ÖZETİ heading sits at 294 px. Items 1–4 are fully visible and item 5 starts at the bottom edge. OYUNCULAR is not on the first screen: the rail (TARAMA + OYUNCULAR) now starts at 942 px, below the summary. Light and dark are identical in layout. **1440×900:** the rail is in the left column (x=287, top 124) with TARİH, TARAMA and OYUNCULAR, where it was before. The builder's before/after 1440 shots are byte-identical. Screenshots: `reviewer/reports-2026-09-23-375-light.png`, `-375-dark.png`, `index-375-light.png`, `reports-2026-09-23-1440-light.png`, `-1440-dark.png`, `-375-dark-ray.png`; builder's `after/reports-2026-09-23-375-*.png`. |
| R24-P0-2 (S) | PASS | **375px:** all chips (Portföy, Gelişmeler, İzleme, Kaynaklar, EK) sit on one row at the same top (227 px). The row scrolls sideways inside its own strip (468 px content in 375 px). The page itself does not overflow (document width 375). The 14, 17, 20 and 22 Sep reports behave the same way, including 14 Sep, which has six chips. Before this revision the chips wrapped to two rows (`before/reports-2026-09-23-375-light.png`). Screenshots: `reviewer/reports-2026-09-23-375-light.png`, `-375-dark.png`. |
| R24-P1-1 (S) | PASS | **375px:** there are 8 portfolio cards on 23 Sep, 8 on 17 Sep and 7 on 14 Sep. Each card has the Etki tag, the Gelişme title, then three text fields. The third field, the watch indicator, carries a mono "İZLENECEK" label directly above it. The label is present in every card, light and dark. The 1440 table keeps its "İZLENECEK GÖSTERGE" column header. Screenshots: `reviewer/cards-2026-09-23-375-light.png`, `-dark.png`, `cards-2026-09-17-375-*.png`, `cards-2026-09-14-375-*.png`. |
| R24-P1-2 (A)+(I) | PASS | **Normal run 35889572520:** the run summary has an İLK-EKRAN table: özet top 294 px (≤300), 4th item bottom 791 px (≤812), rail top 942 px, result "geçti". It links the 375×812 image, which matches what I see locally. Evidence: `after/A-normal-ozet-girisli.jpg`, `after/A-35889572520-ilk-ekran/…/ilk-ekran-2026-09-23-375x812.png`. **Deliberately broken run 35889721553:** the rail is back above the title; özet top 401 px and 4th item bottom 898 px. The summary shows the failure (red) and adds an İLK-EKRAN operator-alert line. Evidence: `after/A-ilk-ekran-boz-ozet-girisli.jpg`, `after/A-35889721553-ilk-ekran/…-boz.png`. **Issue #5:** I checked it live. It carries "İLK-EKRAN · 2026-09-23 brifingi 375×812 (ilk_ekran_boz, ray bilerek geri taşındı): özet başlığı 401px > 300; 4. madde alt kenarı 898px > 812", linked to that run. Evidence: `after/I-issue-5-ilk-ekran.jpg`. |

## Regressions

I checked the home page and the 14, 17, 20, 22 and 23 Sep reports at 375, 834 and 1440, light and dark. I found no regressions.
- Every page has one h1 and no horizontal page overflow.
- At 834 (below the 920 px breakpoint) the rail moves under the summary as a single TARAMA · OYUNCULAR line, and the portfolio table stays tabular. See `reviewer/reports-2026-09-20-834-dark.png`.
- At 1440 every page keeps the left rail.

## Observations (not failures)

- **The chip strip gives no sign that it scrolls.** At 375 the strip cuts "Kaynaklar" mid-word and EK is off-screen. Nothing shows that more chips are hidden other than the clipped word.
- **Summary below the fold on alarm days.** On 14 Sep, a day with an alarm, the red alarm callout and the ALARMLAR section fill the 375 first screen, and YÖNETİCİ ÖZETİ starts at 854 px. That follows the rule that colour marks alarm, and the criterion names 23 Sep. But the CI İLK-EKRAN check (özet ≤300) would flag such a day.
