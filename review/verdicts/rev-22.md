# Rev 22 — verdict: PASS

I checked the local site (http://localhost:8000) at 375×812 and 1440×900, in light and dark. My screenshots are in `review/shots/rev-22/reviewer/` and replace the earlier set there. The orchestrator's message had no builder rationale. (I) is not an evidence type in my instructions. The orchestrator substituted (I) for the (P) phone alert, so I judged it from the screenshot of the issue instead of marking it PENDING-HUMAN.

| # | Result | Evidence |
|---|---|---|
| R22-P0-1 (A) | PASS | `after/A-yesil-d2-artifact/dort-durum-35868516807-1/1-fetch.png` shows "Arama şu an çalışmıyor — sayfayı yenileyin." and no "kayıt yok". In the summary, row 1 reads "geçti" (`after/A-yesil-ozet-girisli.jpg`). |
| R22-P0-2 (S) | PASS | On medya takibi with "xyzzy" searched, all four viewport/theme combinations show "Bu aramayla eşleşen kupür yok." (#noresults is visible) and "0 / 536 başlık". Screenshots: `reviewer/haberler-xyzzy-375-light.png`, `-375-dark.png`, `-1440-light.png`, `-1440-dark.png`. This matches `after/A-yesil-d2-artifact/…/2-noresults.png`. |
| R22-P1-1 (A) | PASS | `after/A-yesil-d2-artifact/…/3-yukleniyor.png` shows "Aranıyor…". In the summary, row 3 reads "1 sn sonra panel: Aranıyor…" and "geçti". |
| R22-P1-2 (S) | PASS | `?oyuncu=roketsan` shows "2 / 536 başlık" in all four combinations: `reviewer/roketsan-375-light.png`, `-375-dark.png`, `-1440-light.png`, `-1440-dark.png`. The builder's `after/haberler-2026-09-23-oyuncu-roketsan-*.png` match. The `before/` shots show "536 başlık". |
| R22-P1-3 (A)+(I) | PASS | **Green run:** all four scenarios read "geçti", with "DÖRT-DURUM: 4/4 yeşil" and "uyarı yok" (`after/A-yesil-ozet-girisli.jpg`). All four d2 artifact images show the expected state. **Red run (boz=fetch):** row 1 reads "kaldı", with "1 senaryo kaldı — build durdu". The error annotation reads "Process completed with exit code 1", and the run links to issue #5 (`after/A-kirmizi-ozet-girisli.jpg`). **Issue #5:** it has the line "DÖRT-DURUM · fetch kaldı (boz=fetch, bilerek) …" (`after/I-issue-5-dort-durum.jpg`). |

## Regressions

- I found no regressions on the touched pages. Index, reports/2026-09-23, arsiv, medya takibi (unfiltered, `?oyuncu=roketsan`, and "xyzzy" searched) all return 200. None has horizontal overflow at 375 or 1440, and there were no page JS errors in either theme.

## Observations (not criterion failures)

- **"2 / 536" counts one headline twice.** Under `?oyuncu=roketsan` the same headline appears in two categories: "ASELSAN ile ROKETSAN arasında 1,2 milyar avroluk sözleşme imzalandı", from Anadolu Ajansı, under Türk savunma sanayii and İhale ve Sözleşmeler. The criterion asks for 2, and the page shows 2. But PRODUCT.md says "a count is a claim", and a reader will likely take this as two separate headlines. The duplicate listing is also in `before/`.
- **Evidence runs differ.** The green summary screenshot links the artifact of run 35867515608. The brief names 35868516807 (d2) as the latest normal run. Both artifact sets show the four expected states.
- **A banner appears that the builder's shots don't show.** In my fresh browser session, a fixed opt-in banner ("Yeni rapor çıkınca haber verelim mi? … AÇ / ŞİMDİ DEĞİL") appears at the bottom of medya takibi and covers about 150px of the 375 viewport. It is not in the builder's before/ or after/ shots, so I can't tell whether this revision introduced it.
