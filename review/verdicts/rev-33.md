# Rev 33 — verdict: PASS

I judged this revision from PRODUCT.md, the acceptance table, review/shots/rev-33/, public issue #5 and http://localhost:8000. I did not read diffs, source, history or builder notes. The shared scratchpad contains builder files; I did not open them. The orchestrator's message contained no builder rationale.

My screenshots are in `reviewer/`. They are headless Chrome captures at 375×812 and 1440×900, light and dark, with the `tr-TR` locale, taken from localhost:8000 without rebuilding anything. I also pulled the rendered `innerText` from each page, which reflects CSS `text-transform`. I then listed every token that contains "İ". This covered the medya takibi and kaynaklar pages for 17–23 Sep, at both widths and in both themes.

## Criteria

- **R33-P0-1 (S): PASS.** In Öne çıkanlar on the 23 Sep medya takibi at 1440, the meta lines read "UNMANNED AIRSPACE · BRİFİNGDE" and "DEFENSE DAILY · BRİFİNGDE", both with a dotless I. The before screenshot shows "UNMANNED AİRSPACE" and "DEFENSE DAİLY". "ANADOLU AJANSI — GÜNCEL · BRİFİNGDEN SONRA · ASELSAN · ROKETSAN" is unchanged. The same holds at 375 and in dark mode.
  - Evidence: `reviewer/haberler-2026-09-23-1440-light.png`, `-1440-light-full.png`, `-1440-dark.png`, `-375-light.png`, `-375-dark.png`; `after/haberler-2026-09-23-1440-*.png` compared with `before/…`.
- **R33-P0-2 (S): PASS.** On the 23 Sep kaynaklar page, no foreign source name contains a dotted İ at either width or in either theme. The only rendered İ tokens are the Turkish UI labels "BRİFİNG" and "TAKİBİ". The same is true of the kaynaklar pages for 17–22 Sep.
  - Evidence: `reviewer/haberler-2026-09-23-kaynaklar-{375,1440}-{light,dark}.png`. These are pixel-identical to the matching `after/` captures.
- **R33-P1-1 (I): PASS.** Public issue #5 carries the line "**NOKTALI-İ** · büyük harfli alanda lang'sız yabancı ad 3212 örnek, 7 sayfada (NOKTALI_BOZ=1, bilerek) — ilk: …"Unmanned Airspace" · …"Defense Daily" · …"Defence Industry Europe" · çalıştırma". I confirmed this on github.com as well as in the screenshot. The run with the fix disabled reports 🔴 3212 örnek. The normal run reports 🟢 0 örnek. The alert sits in the operator channel only. I judged only the NOKTALI-İ line.
  - Evidence: `after/I-issue-5-noktali.jpg`, `after/A-noktali-boz-ozet-girisli.jpg`, `after/A-normal-ozet-girisli.jpg`.

## Regressions

None found.
- **Medya takibi, 23 Sep.** Before and after differ only in the meta-label column: the dotted İ in foreign names becomes a plain I. Layout and height are unchanged at 375 and 1440, in light and dark.
- **Kaynaklar, 23 Sep.** The only difference is a sub-pixel change on the "SCMP (Çin)" label, with no visible change.
- **Other days, 17–22 Sep.** Every remaining "İ" is correct Turkish: UI labels such as BRİFİNGDE, TÜRK SAVUNMA SANAYİİ and SCMP (ÇİN), and the Turkish source name SAVUNMASANAYİST. A few words in translated headline text, such as "İSR" and "İnterceptor", are written that way in the text itself. They are not uppercased by CSS, so they fall outside this revision.

Observations (not caused by this revision, and not blocking):
- **Notification prompt.** In a fresh browser profile the "Yeni rapor çıkınca haber verelim mi?" bar covers the bottom of the viewport, and it shows in my captures. The builder's captures have it dismissed.
- **Pipeline health on kaynaklar.** The page still reads "50 kaynak okundu · 16 yanıt vermedi" and lists the sources that did not respond. That is pipeline health shown to readers, which PRODUCT.md's core rule forbids. It is unchanged from before.
