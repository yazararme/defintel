# Rev 31 — verdict: PASS

Reviewer judged from PRODUCT.md, the acceptance table, review/shots/rev-31/, public issue #5 (as captured in the builder's screenshot) and http://localhost:8000. I did not read diffs, source, history or builder notes. The orchestrator's message contained no builder rationale.

Reviewer screenshots are in `reviewer/`. They are headless Chromium captures at 375×812 and 1440×900, light and dark, taken from localhost:8000 without rebuilding anything.

## Criteria

- **R31-P0-1 (A): PASS.** The second "Toplama · 2026-09-24 · GEÇ-GELEN (Rev 31)" block reads **"yeni: 1 · değişmedi: 5 · damga değişti: 0"** with a green mark. The first run reads "yeni: 5 · değişmedi: 0 · damga değişti: 0 — günün ilk toplaması". The test header reads "ikinci toplama "yeni: 1 · değişmedi: 5 · damga değişti: 0"". Evidence: `after/A-gec-gelen-test-ozet-girisli.jpg`.
- **R31-P0-2 (S): PASS.** On `/haberler/2026-09-23.html?oyuncu=roketsan` at 375 px, both instances of the AA row ("ASELSAN ile ROKETSAN arasında 1,2 milyar avroluk sözleşme imzalandı", under Türk savunma sanayii and under İhale ve Sözleşmeler) show the meta line "ANADOLU AJANSI — GÜNCEL · BRİFİNGDEN SONRA · ASELSAN · ROKETSAN". It renders the same way at 1440 px and in both themes. The label uses the grey mono meta voice, with no new colour. Evidence: `reviewer/haberler-2026-09-23-oyuncu-roketsan-375-light.png`, `-375-dark.png`, `-1440-light.png`, `-1440-dark.png`, and `after/haberler-2026-09-23-oyuncu-roketsan-375-*.png`.
- **R31-P0-3 (D): PASS, with a stand-in caveat.** The file's first section is "## Dünkü brifingden sonra gelenler (89)", followed by "2026-09-23 brifingi 06:16'de yayımlandı; …". The AA line ("ASELSAN ile ROKETSAN … — Anadolu Ajansı — güncel, 2026-09-23, ilk görüldü 23.09 11:04 — https://www.aa.com.tr/…/4065836") sits inside that section, before the next heading ("## C-UAS ve Hava Savunma").
  - Caveat: as served by localhost:8000, the browser shows mojibake ("DÃ¼nkÃ¼ brifingden…", "baÅŸlÄ±klar"), and the builder's `after/D-2026-09-24-aday-*.png` show the same. The cause is the stand-in server: it sends `Content-type: text/markdown` with no charset. The file itself is valid UTF-8. Production sends `text/markdown; charset=utf-8` for the sibling files 2026-09-22-aday.md and 2026-09-23-aday.md. I re-served the same bytes with that header on a throwaway local port, and they render correctly in both themes and at both widths. Evidence: `reviewer/D-2026-09-24-aday-utf8-375-light.png`, `-375-dark.png`, `-1440-light.png`, `-1440-dark.png`. The raw stand-in captures are `reviewer/D-2026-09-24-aday-*.png`. When the first real 24 Sep file is published, confirm it renders correctly on the live host.
- **R31-P1-1 (I): PASS.** Issue #5 contains the line **GEÇ-GELEN** · "SINAMA (fixture) — gerçek uyarı değil: 2026-09-24 · yeniden toplamada 1 kalemin ilk_goruldu damgası değişti — ör. "Belgium's second rMCM ship Tournai arrives in Zeebrugge" 2026-09-24T05:19:00+03:00 → 2026-09-24T11:04:00+03:00 · çalıştırma". It sits in the operator channel, not on any reader surface. Evidence: `after/I-issue-5-gec-gelen.jpg`. I judged only the GEÇ-GELEN line.

## Regressions

None found.
- The unfiltered medya takibi for 23 Sep at viewport size is pixel-identical before and after, at 375 and 1440, light and dark. My captures match the builder's.
- On the full page (1440), the only differences are 11 meta lines that gained "· BRİFİNGDEN SONRA". At 375 the full page is 85 px taller because those meta lines wrap. The roketsan-filtered page differs only in the two AA meta lines.

Observations (not caused by this revision, and not blocking):
- The roketsan filter lists the same AA story twice, once per category, and the count reads "2 / 536 başlık". The duplication is unchanged from the before screenshots.
- "ÖZET ALINAMADI" still appears in a reader-facing meta line (Indian Defence News row). This is producer state shown to readers, per PRODUCT.md's core rule. It is unchanged from before.
- The stand-in candidate file lists 89 items after the briefing. The 23 Sep page marks 11 rows "BRİFİNGDEN SONRA". The two are built from different item sets (107 unique vs 536 in 48 h), so I did not treat this as a count mismatch. Recheck once real 24 Sep data exists.
