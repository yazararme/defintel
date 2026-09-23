# K5: design review verdict (attempt 2)

**FAIL**

I measured each page myself on http://localhost:8000 in headless Chromium at exactly 375×812, and checked 834 and 1440 as well, in light and dark mode. Each 375 page was measured twice: once as rendered, and once with `letter-spacing:0.3px` forced on the page to stand in for CI. I also cut the text to the prompt limits in the browser to check the "with limits applied" column myself: headline ≤65, alarm band ≤70 and each summary item ≤110 characters, each cut at a word boundary. Screenshots are in `review/shots/k5/reviewer/deneme2/`. Light and dark measured the same on every day, and no page scrolls sideways at 375, 834 or 1440.

| day | local h2 / item 4 | 0.3px h2 / item 4 | (A) CI h2 / item 4 | my check with limits (0.3px) |
|---|---|---|---|---|
| 14 Sep (alarm) | 331 / 903 | 331 / 929 | 330 / 929 | 277 / 718 |
| 15 Sep | 263 / 887 | 263 / 940 | 263 / 914 | 263 / 704 |
| 16 Sep | 294 / 867 | 294 / 893 | 294 / 867 | 263 / 756 |
| 17 Sep | 263 / 756 | 263 / 809 | 263 / 809 | 263 / 704 |
| 18 Sep | 263 / 756 | 263 / 782 | not legible | 263 / 730 |
| 19 Sep | 326 / 820 | 326 / 820 | 326 / 820 | 263 / 730 |
| 20 Sep | 326 / 846 | 326 / 872 | 326 / 872 | 263 / 704 |
| 21 Sep | 294 / 683 | 294 / 683 | 294 / 683 | 263 / 651 |
| 22 Sep | 294 / 709 | 294 / 735 | 294 / 709 | 263 / 677 |
| 23 Sep | 263 / 756 | 263 / 782 | 263 / 782 | 263 / 704 |

- **K5-1 (A): FAIL (cannot be verified).** The İLK-EKRAN tanı table has the required columns: gün, h2 üst, 4. madde alt and neden. It also shows the CI worst case and the estimate with limits. Nine of its rows agree with my measurements. The 18 Sep row, however, falls on the break between the two screenshots. `A-tani-d2-1-girisli.jpg` ends partway into the row and `A-tani-d2-2-girisli.jpg` starts at 19 Sep. As a result, 18 Sep's h2 top, item 4 bottom and cause cannot be read, so the evidence does not show a 10-day table.
- **K5-2 (S): PASS.** The structural cause on 14 Sep is gone. ALARMLAR now comes after the summary, at 1260px, and the (A) table shows "ALARMLAR özetten önce 0px". The alarm band is still the first thing on the page (104–181px). It is readable in light and dark mode. Tapping it lands on the ALARMLAR heading, 69px down the viewport, below the daybar. What still overflows (331 / 903) is caused by text: the band wraps to 3 lines (91 characters), the headline to 4 lines (83 characters), and the first four items take 20 lines. With the limits applied the day passes: 277 / 718 in (A), and I got the same figure myself. 19 and 20 Sep, where the headline takes 5 lines, and 15 and 16 Sep also pass with the limits, in (A) and in my own check. Evidence: `deneme2/reports-2026-09-14-375-light.png`, `-375-dark.png`, `-375-{light,dark}-after-tap.png`, and `after/A-tani-d2-1-girisli.jpg`.
- **K5-3 (S): PASS.** 23 Sep is at 263 / 756 locally and 263 / 782 in CI, down from 280 / 799 in attempt 1. 17 Sep is back under the limit: 809 in CI, against 826 in attempt 1, although only 3px under. 18, 21 and 22 Sep pass as well, both locally and at 0.3px. Evidence: `deneme2/reports-2026-09-{17,18,21,22,23}-375-*.png` and `after/A-tani-d2-2-girisli.jpg`.
- **K5-4: PASS for the text; the effect on future reports is PENDING-HUMAN.** `review/builder-notes/k5-prompt.md` contains the three sentences: headline ≤65 characters, alarm_title ≤70 characters, each summary item ≤110 characters. One point to note: the file's "as published: CI worst" column does not match the (A) table's "CI en kötü" column. For example, 16 Sep is 893 in the file and 919 in (A), 17 Sep is 809 against 835, and 23 Sep is 782 against 809. The "with limits" figures do match.

**Regressions:** none against the thresholds. One layout change to note: on the alarm day only, the section chips at 375 have moved from under the headline to below the summary (at 1163px). On other days they stay under the headline. At 1440 the chips are unchanged.

I ignored the builder's rationale in the prompt file and judged only on measurements.
