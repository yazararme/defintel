# Rev 23 — verdict: PASS (R23-P0-2 PENDING-HUMAN)

I judged this revision from PRODUCT.md, the acceptance table, `review/shots/rev-23/`, the public issue #5 and http://localhost:8000. I did not read diffs, source code, history or builder notes. The orchestrator's message had no builder rationale.

(I) is not an evidence type in my instructions. The orchestrator substituted (I) for the (P) phone alert, so I judged the alert criteria from issue #5 instead of marking them PENDING-HUMAN. That applies to every alert criterion except R23-P0-2, which cannot be checked yet.

My screenshots are in `review/shots/rev-23/reviewer/`.

**Viewport note.** The browser window would not resize to exact sizes:
- At "1440" the page actually ran at 1547 CSS px (Chrome window at DPR 2). The builder's `after/` shots are at a true 1440.
- For 375 I loaded the page in a same-origin iframe exactly 375 px wide.
- For dark mode I applied the site's own `prefers-color-scheme: dark` rules.

## Criteria

| # | Result | Evidence |
|---|---|---|
| R23-P0-1 (S) | PASS | **Heading:** G9 (`#g9`) reads "Lynx XM30 prototip teslimi". **Click-through:** in İZLEME LİSTESİ, the entry "XM30'da organik C-UAS şartı → bugün: Lynx XM30 prototip teslimi" links to `#g9`. Clicking it lands with the G9 heading at the top of the viewport, just below the sticky bar, in all four combinations. **Other links:** every "bugün:" link in the watch list has the same text as the heading it targets, and no in-page anchor is broken. Screenshots: `reviewer/reports-2026-09-23-1440-light-g9.jpg`, `-1440-dark-g9.jpg`, `-375-light-g9.jpg`, `-375-dark-g9.jpg`. The builder's `after/reports-2026-09-23-*-full.png` agree. |
| R23-P0-2 (I) | PENDING-HUMAN | This needs the next three daily reports, which do not exist yet. |
| R23-P1-1 (I) | PASS | Issue #5 has two new lines dated 2026-09-23 with real content, as the criterion requires. **KUR line:** "KUR · 2026-09-23 · SAN CUAS 1,5 milyar $ ↔ özet 1,74 milyar dolar [K2] …". **H1-TEKRAR line:** "H1-TEKRAR · 2026-09-23 · özet 1 · örtüşme 0,73 · H1 "Letonya araç üstü 155 mm obüste Archer'ı bırakıp Çek Morana'yı seçti" ↔ …". Evidence: `after/I-issue-5-kur-h1.jpg`, `reviewer/I-issue-5-1456.jpg`, `reviewer/I-issue-5-kur-h1-zoom.png`. One defect in the KUR line is described below. |

## Regressions

- **Site:** none found.
  - All before/after viewport shots are byte-identical. The only differences are in the full-page shots, where the Gelişmeler headings were renamed. For example, "Leonardo / Alkeon" became "Leonardo–Alkeon 76 mm Danimarka üretimi". At 375, the longer headings wrap and the page grows by 33 px. The layout is intact.
  - The page has one h1, no horizontal overflow at 375, and every in-page anchor resolves.
  - The index shots are identical to the 23 Sep briefing shots, so the same findings apply to the index page.

## Defect in the alert channel (not a site regression)

- **The KUR alert line is garbled on GitHub.** The line contains two "$" signs: "1,5 milyar $ ↔" and the quoted body "…1,5 milyar $'lık (16 milyar NOK)… 1,5 milyar $'i…". GitHub renders the text between them as inline math. On the live issue, the rest of the quote shows as italic math, with the spaces gone: "′lık(16milyarNOK)”·atıfliözetlerçelişiyor;1,5milyar". See `reviewer/I-issue-5-kur-h1-zoom.png`.
  - The part the criterion requires is still readable, so R23-P1-1 passes. But the operator cannot read the evidence text in the second half of the line.
  - The builder's `after/I-issue-5-kur-h1.jpg` looks like it was captured before the math rendered, so it hides this problem.
  - Any alert that carries a "$" amount will hit the same problem.

## Observations

- **The "install as app" banner covers part of the screen.** A fixed bottom banner appears in my session: at 1440, "DEFINTEL'i uygulama olarak ekle … YÜKLE / KAPAT"; at 375, "Yeni rapor çıkınca haber verelim mi? … AÇ / ŞİMDİ DEĞİL". At 375 it covers about 150 px of the viewport. It is not in the builder's shots and was already noted in rev 22, so it is not attributed to this revision.
- **A stray "#" in headings.** At 375, the heading anchor "#" wraps onto a line by itself under long headings, for example "Fransa–Irak C-UAS önleyici mutabakatı". This is also visible in `before/`.
