# Rev 29 — verdict: PASS

I judged this revision from PRODUCT.md, the acceptance table, review/shots/rev-29/ and http://localhost:8000. I did not read diffs, source, history or builder notes. The orchestrator's message contained no builder rationale; it only noted that the builder's captures blocked service workers.

My screenshots are in `reviewer/`. They are headless Chrome (Chrome for Testing) captures at 375×812 and 1440×900, light and dark, `tr-TR` locale, each in a fresh context with clean storage and service workers allowed, taken from localhost:8000 without rebuilding. Pages: the 23 Sep briefing, home, the 23 Sep medya takibi and one thread page. I also read computed styles in the browser for the summary box and section-heading rules.

## Criteria

- **R29-P0-1 (S): PASS.** The YÖNETİCİ ÖZETİ list sits on a filled panel (light `rgb(245,243,238)` on a `rgb(252,251,249)` page; dark `rgb(26,28,32)` on `rgb(18,19,22)`). It has no left border, and no green rule shows. The before capture shows the dark-green left rule. The result holds at 375 and 1440, in light and dark. My first-screen captures are pixel-identical to the builder's `after/` captures.
  - Evidence: `reviewer/reports-2026-09-23-375-light.png`, `-375-dark.png`, `-1440-light.png`, `-1440-dark.png`; `before/reports-2026-09-23-375-light.png` compared with `after/…`.
- **R29-P1-1 (S+A): PASS.** At 1440, the rule above PORTFÖYE ETKİSİ, GELİŞMELER, İZLEME LİSTESİ and KAYNAKLAR is clearly visible in both themes. It is a 1px rule, `rgb(144,142,136)` in light and `rgb(98,101,107)` in dark. I computed the contrast against the page background: 3.17:1 in light and 3.18:1 in dark. The build summary's ÇİZGİ-KONTRAST line reads "açık 3,17:1 · koyu 3,18:1 (eşik 3,00)". Both ratios are at least 3, and they match my measurement.
  - Evidence: `reviewer/reports-2026-09-23-1440-light.png`, `-1440-dark.png`, `-1440-light-bottom.png`; `after/A-normal-ozet-girisli.jpg`.
- **R29-P1-2 (S): PASS.** On a first visit with clean storage, service workers allowed (one registration) and notification permission "default", the 375 briefing shows the "Yeni rapor çıkınca haber verelim mi?" card in the page flow. It sits after EK and before the end-nav buttons, so it no longer overlays the first screen. While the card is open, the footer bell "YENİ RAPOR BİLDİRİMİ AL" is visible. After "Şimdi değil", the card hides and the bell remains. This is the same in light and dark.
  - Evidence: `reviewer/notifycard-375-light.png`, `notifycard-375-dark-sayfa-sonu.png`, `notifycard-375-{light,dark}-kapatildi.png`, `reports-2026-09-23-375-{light,dark}-bottom.png`.

## Regressions

- **Minor, 375 only.** The bottom rule of the notification card runs directly into the first end-nav button ("← 22 EYLÜL 2026 BRİFİNGİ"), with a 1px gap. This happens on the briefing and on the medya takibi page. At 1440 the same gap is about 18px.
  - Evidence: `reviewer/notifycard-375-light.png`, `haberler-2026-09-23-375-light-bottom.png`, `reports-2026-09-23-1440-light-bottom.png`.
- **No other regressions found.**
  - The first screens of home, the briefing and medya takibi are pixel-identical to the builder's `after/` captures at both widths and in both themes. The one exception is the medya takibi 1440 dark capture, which differs at sub-pixel level with no visible change.
  - On medya takibi, Öne çıkanlar also moved from a green left rule to a filled panel. This is consistent with R29-P0-1.
  - Full-page heights grew by 62px compared with before. This comes from the spacing of the summary panel and rules; I saw no layout break.

Observation (not attributable to this revision, because there is no before capture): on the thread page, the end-nav buttons are indented about 18–24px from the content's left edge at both widths, while the briefing's end-nav is flush (`reviewer/izleme-155mm-375-dark-full.png`, `izleme-155mm-1440-light.png`).
