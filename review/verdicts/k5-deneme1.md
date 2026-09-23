# K5 — design review verdict

**FAIL**

Measured by the reviewer on http://localhost:8000 at exactly 375×812 in Chrome, in light and dark mode. Each day was measured twice: as rendered, and with `letter-spacing:0.15px` forced on the page to stand in for CI's wider line breaks. 1440×900 was checked too. Screenshots are in `review/shots/k5/reviewer/`.

| day | h2 top (local) | item 4 bottom (local) | item 4 bottom (0.15px) | CI summary (A) h2 / item 4 |
|---|---|---|---|---|
| 14 Sep (alarm) | 840 | 1423 | 1449 | 840 / 1449 |
| 15 Sep | 280 | 904 | 957 | 280 / 931 |
| 16 Sep | 311 | 884 | 884 | 311 / 884 |
| 17 Sep | 280 | 773 | 826 | 280 / 826 |
| 18 Sep | 280 | 773 | 773 | 280 / 799 |
| 19 Sep | 343 | 837 | 837 | 343 / 837 |
| 20 Sep | 343 | 863 | 863 | 343 / 889 |
| 21 Sep | 311 | 700 | 700 | 311 / 700 |
| 22 Sep | 311 | 726 | 726 | 311 / 726 |
| 23 Sep | 280 | 773 | 799 | 280 / 799 |

Light and dark measured the same on every day. No page scrolls sideways at 375 or 1440.

- **K5-1 (A): PASS.** The İLK-EKRAN tanı table in the signed-in Actions summary lists all 10 days with these columns: day · h2 top · item 4 bottom · headline · alarm · lines · cause · estimate with limits. Its figures match my own measurements. Evidence: `after/A-tani-1-girisli.jpg`, `A-tani-2-girisli.jpg`, `A-tani-3-girisli.jpg`.
- **K5-2 (S): FAIL.** The alarm day, 14 Sep, is the example of a layout-caused day, and it is unchanged. The summary heading is at 840px and item 4 ends at 1423px. At 375×812 the whole first screen is the alarm band, the headline and the ALARMLAR block, and "YÖNETİCİ ÖZETİ" is not visible. My screenshot matches the before shot pixel for pixel. The alarm is still above the summary and readable. Evidence: `reviewer/reports-2026-09-14-375-light.png`, `reviewer/reports-2026-09-14-375-dark.png`, `before/reports-2026-09-14-375-light.png`. The (A) table itself marks this day red with the cause "yapı: alarm bandı 97px + ALARMLAR 431px", and even its estimate with the limits applied is red (808/1260).
- **K5-3 (S): FAIL.** 23 Sep passes locally (280/773) and in CI (280/799), and 18 Sep passes in both. 17 Sep did not fail before this change, but it now fails in CI: item 4 ends at 826px, over the 812px limit. My 0.15px run gives the same 826. The (A) table marks it red ("metin: ilk 4 madde 18 satır"). Evidence: `after/A-tani-2-girisli.jpg`, `reviewer/reports-2026-09-17-375-light.png`.
- **K5-4: PASS for the text; the effect on the next reports is PENDING-HUMAN.** `review/builder-notes/k5-prompt.md` has both limit sentences: headline ≤75 characters, each summary item ≤110 characters. One discrepancy to note. The file says "all nine days without an alarm pass" with the limits, and gives 280/747 as the CI worst case for 16 Sep. The (A) table for the CI run shows 16 Sep's estimate with the limits as red, at 311/805: the headline stays at 4 lines in CI.

**Regressions:** in CI, 17 Sep has gone from passing to failing (item 4 ends at 826px). I found no visual regression at 1440 in light or dark (`reviewer/*-1440-*.png`).

The builder's rationale in the prompt file ("the alarm day needs a decision, not a prompt limit") was ignored. The client has already ruled that there is no exemption for alarm days.
