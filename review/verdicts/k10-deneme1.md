# K10 verdict — FAIL

Inputs: PRODUCT.md, review/briefs/k10.md (Kabul table), review/shots/k10/{before,after}, evidence site http://localhost:8000.
No builder rationale was supplied in the orchestrator message; none read. Reviewer shots: review/shots/k10/reviewer/.

| # | Result | Evidence |
|---|---|---|
| K10-1 | PASS | `/reports/2026-10-15.html` KAYNAKLAR is folded (`details#kaynaklar`, count reads 21) and opens to one `<ul>` of 21 `li.source` items, ids k1–k21, same markup/look as a bulleted day; at 375×812 and 1440×900, light (body rgb 252,251,249) and dark (rgb 18,19,22). Before = run-on paragraph with count "0". `1015-kaynaklar-{375,1440}-{light,dark}.png`, `1015-kaynaklar-section-{375,1440}-{light,dark}.png`; before: `before/reports-2026-10-15-kaynaklar-1440-light.png` |
| K10-2 | PASS | Clicking in-text [K1], [K10], [K21] opens the fold, sets hash, and after scroll settles the target row is on screen (top 69px at 375, 122/284px at 1440; below the sticky bar/chips) in all 4 variants. `1015-click-{k1,k10,k21}-{375,1440}-{light,dark}.png` |
| K10-3 | PASS | `/reports/2026-09-23.html` KAYNAKLAR markup is byte-identical to the published page in the main checkout (13857 chars), and section screenshots of the evidence vs. baseline page are pixel-identical in all 4 variants. `0923-evidence-kaynaklar-*.png` vs `0923-baseline-kaynaklar-*.png` |
| K10-4 | FAIL | `DEFINTEL_BASE=http://localhost:8000 python3 review/tools/smoke.py` (main checkout) exited 1. Final line: `SMOKE FAIL: (D) aday ilk bölüm, NOKTALI-İ bozuk derleme, TEKRAR-MANŞET 375px /, KANIT-BOŞLUĞU 375px, KANIT-BOŞLUĞU --kanit-boslugu düzenli, R27 tarayıcı 375px, R27 tarayıcı 1440px, K2 tam, KAPSAM-SAYI <64, K2 boz`. The new fixed test itself is green (`scripts/test_kaynak_bicim.py · KAYNAK-BİÇİM testi: yeşil · 21 çapa · 47 atıf`). `merge_day.sh DRY=1`: orchestrator to verify. |

## Notes on K10-4
- Several failures look like a mismatch between the main checkout and the evidence site, not a K10 defect: e.g. R27 expects the newest report to be 2026-09-23 ("23 Eyl · Çar"), but the evidence site's newest is 15 Eki. I can't separate those from real failures with the evidence I'm allowed to use. Smoke has to be green on the branch before this criterion can pass.
- The smoke line `KAYNAK-BİÇİM build satırları · yok (bütün günler madde işaretli)` reads the main checkout's corrected source, so it doesn't show the operator warning firing for the unbulleted 15 Ekim. Brief item 3 isn't a Kabul row; this is for information only.

## Regressions
- None found on the pages touched (2026-10-15, 2026-09-23).
- These were already there and also show in the before shots: the "Israel Aerospace Industries (IAI)" link spills out of the 1440 sidebar, and the full-section element shots catch the sticky daybar/chips mid-image (the baseline shots show the same thing).
