# Rev 26 — verdict: PASS

I judged this revision from PRODUCT.md, the acceptance table, `review/shots/rev-26/` (before/, after/), the public run 35913238627 (`gh run view`), issue #5 and http://localhost:8000. I did not read diffs, source code, history or builder notes, and I did not rebuild the site. The orchestrator's message had no builder rationale.

(I) is not an evidence type in my instructions. The alert criterion accepts (A) or (I), so I judged it from the (A) run summary and its annotation, and used issue #5 as supporting evidence only.

I rendered the medya takibi pages in headless Chromium at exact viewports, 375×812 and 1440×900, each in light and dark (`prefers-color-scheme`). My screenshots are in `review/shots/rev-26/reviewer/`.

## Criteria

| # | Result | Evidence |
|---|---|---|
| R26-P0-2 (first half) (A) | PASS | The summary of run 35913238627 has the table "ÇEVİRİ-DEDEKTÖRÜ · sabit test (content.md §2, 16 kusurlu kalem, mevcut çeviriler)". Its "en az biri" row gives 6 of the 12 defined items caught, and "16 üzerinden kesin alt sınır" 8. The item list shows 6 ticks out of 12 (4 düzen, 2 atıf). The green result line reads "sabit test: 16 kusurlu kalemden en az 8 yakalandı (eşik 7; beklenen ≈9.7)". The job line reads "ÇEVİRİ-DEDEKTÖRÜ testi: 20/20 kontrol … model çağrısı 0". 8 ≥ 7. Evidence: `after/A-sabit-test-ozet-girisli.jpg`. |
| ÇEVİRİ-DEDEKTÖRÜ alert (A)/(I) | PASS | The run belongs to the test workflow "ceviri-dedektoru-test", job sabit-ve-akis, and uses the fake day 2026-09-24. Its result line is red: "sınanan 40 · yeniden çevrilen 32 · düzelen 1 · özgün bırakılan 31 (uyarı eşiği >10)". The "Operatör uyarıları" section lists "ÇEVİRİ-DEDEKTÖRÜ · 2026-09-24: 31 başlık özgün bırakıldı (>10) — ilk çeviride düzen 30 · uzunluk 0 · atıf 2". The same text appears as a warning annotation, which I confirmed with `gh run view`. The job also reports "OPERATÖR-YALNIZ: issue #5 · +1 satır · okuyucu push 0". Issue #5 carries the same ÇEVİRİ-DEDEKTÖRÜ line, which links to run 35913238627 (issue updated 2026-09-23T20:02Z). Evidence: `after/A-uyari-ozet-girisli.jpg`, `after/I-issue-5-ceviri.jpg`. |
| R26-P0-1 | SKIPPED (kapsam dışı) | — |
| R26-P0-2 (second half: re-translating "…exiting power procurement") | SKIPPED (kapsam dışı) | — |
| R26-P1-1 | SKIPPED (kapsam dışı) | — |
| R26-P1-2 | SKIPPED (kapsam dışı) | — |
| R26-P1-3 | SKIPPED (kapsam dışı) | — |

## Regressions

None found on /haberler/2026-09-21, -22 and -23 at 375×812 and 1440×900, light and dark.
- No page overflows horizontally: scrollWidth equals the viewport width.
- Backgrounds and text follow the theme.
- There are no console errors.
- Evidence: `reviewer/haberler-2026-09-2{1,2,3}-{375,1440}-{light,dark}{,-full}.png`.

**23 Sep compared with before/.** The viewport captures differ only by anti-aliasing (maximum channel difference 28, with no pixel above 40). The full-page captures are 23 px taller at 1440 and 54 px taller at 375. The extra height is the footer "BİLDİRİMLER KAPALI" button. That button is in the static HTML and is shown whenever the browser exposes the Notification API. With that API removed, my captures match before/ in size, with no pixel difference above 28 (`reviewer/haberler-2026-09-23-*-full-bildirimsiz.png`). The difference therefore comes from the capture environment, not from this revision.

## Observations (not failures)

- **The fixed-test pass rests on a lower bound derived from a detector that flags nearly everything.** The 8 is built from the 6 defined items plus a deduction from the pool, where 26 of 28 headlines are flagged by düzen. On the fake day, düzen also flagged 30 of 40 headlines on first translation. Despite this, düzen missed 4 of the 7 §2 "cümle düzeni" items (each marked "§2: 7/7 kusurlu"). The detector looks unselective rather than precise.
- **The uzunluk check caught nothing.** It scored 0 everywhere: 0 of 12 defined items, 0 of 28 in the pool, and 0 on the fake day.
- **The test workflow made model calls.** The fake-day line reports "model çağrısı 2", while the fixed test reports 0.
