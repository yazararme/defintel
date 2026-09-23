# Rev 22 — verdict: FAIL

Reviewer checked the local site (http://localhost:8000) at 375×812 and 1440×900, light and dark. Own screenshots are in `review/shots/rev-22/reviewer/`. The orchestrator's message contained no builder rationale.

| # | Result | Evidence |
|---|---|---|
| R22-P0-1 (A) | PASS | `after/A-yesil-artifact/…/1-fetch.png` shows "Arama şu an çalışmıyor — sayfayı yenileyin." and no "kayıt yok". The green summary row 1 says "geçti" (`after/A-yesil-ozet-girisli.jpg`). |
| R22-P0-2 (S) | PASS | At 375 light and dark, and at 1440 light and dark, searching "xyzzy" on medya takibi shows "Bu aramayla eşleşen kupür yok." and "0 / 536 başlık" (`reviewer/haberler-xyzzy-375-light.png`, `reviewer/haberler-xyzzy-375-dark.png`, `-1440-*`). This matches `after/A-yesil-artifact/…/2-noresults.png`. |
| R22-P1-1 (A) | PASS | `after/A-yesil-artifact/…/3-yukleniyor.png` shows "Aranıyor…". Summary row 3: "1 sn sonra panel: Aranıyor…", geçti. |
| R22-P1-2 (S) | **FAIL** | `?oyuncu=roketsan` shows **"1 / 536 başlık"**, not "2 / 536 başlık". Same result at all four viewport/theme combinations (`reviewer/roketsan-375-light.png`, `reviewer/roketsan-1440-dark.png`, …) and in the builder's own `after/haberler-2026-09-23-oyuncu-roketsan-*.png`. The list shows one headline ("ASELSAN ile ROKETSAN arasında 1,2 milyar avroluk sözleşme imzalandı") twice, under two categories, and each category count reads 1. |
| R22-P1-3 (A)+(I) | PASS | Green run: all four scenarios "geçti", "DÖRT-DURUM: 4/4 yeşil", "uyarı yok" (`after/A-yesil-ozet-girisli.jpg`). Red run with boz=fetch: row 1 "kaldı", "1 senaryo kaldı — build durdu", error annotation "Process completed with exit code 1", link to issue #5 (`after/A-kirmizi-ozet-girisli.jpg`). The red artifact `1-fetch.png` shows the broken "kayıt yok" state. Issue #5 has the line "DÖRT-DURUM · fetch kaldı (boz=fetch, bilerek) …" (`after/I-issue-5-dort-durum.jpg`). Note: (I) is not an evidence type in my instructions, which say (P) should be PENDING-HUMAN. It was judged here from the screenshot because the orchestrator substituted (I) for (P). |

## Regressions

- None found on touched pages. Before and after screenshots of index, reports/2026-09-23 and arsiv are byte-identical. My own captures of those pages load with status 200, no JS errors and no horizontal overflow at 375 or 1440.
- Medya takibi (unfiltered, filtered, search) has no horizontal overflow and no page errors in either theme.
- Observation, not a new regression (also present in `before/`): under `?oyuncu=roketsan` the same headline appears twice, once per category. This is the double-count that makes the "N / 536" figure ambiguous. The criterion expects 2; the page computes 1.
