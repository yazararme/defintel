# Rev 27 — verdict: PASS

I judged this revision from PRODUCT.md, the acceptance table, review/shots/rev-27/ (before/, after/) and http://localhost:8000. I did not read diffs, source, history or builder notes, and I did not rebuild the site. The orchestrator's message contained no builder rationale.

My screenshots are in `reviewer/`. They are headless Chrome captures at 375×812 and 1440×900, light and dark. For each thread page I also read the rendered `innerText` and the computed `text-decoration-line` of every text node and its ancestors.

## Criteria

- **R27-P0-1 (S): PASS.** On the XM30 thread at 375, the line directly under the title reads "Prototip teslim edildi, şart hâlâ tanımlı değil. · 23 Eylül". The date is set as a small mono label. The same line appears at 1440 and in dark mode. Before this revision the line was absent.
  - Evidence: `reviewer/xm30-direct-375-light.png`, `-375-dark.png`, `-1440-light.png`, `-1440-dark.png`; `reviewer/2026-09-23-to-xm30-da-organik-c-uas-sarti-18-375-{light,dark}.png`; `after/` compared with `before/izleme-xm30-…-375-light.png`.
- **R27-P0-2 (S): PASS.** I opened /reports/2026-09-23.html and clicked the XM30 link, which goes to `…raporu.html?g=2026-09-23`. The thread page shows the daybar at the top: "‹ 23 Eyl · Çar ›" plus MEDYA TAKİBİ →. This holds at both widths and in both themes. For a second day I clicked the first thread link on /reports/2026-09-21.html, which opens the jet-motorlu-hedeflerin… thread. Its daybar correctly reads "21 Eyl · Pzt", and the › arrow is active there. All 48 thread pages render a daybar at both widths, with no horizontal overflow.
  - Evidence: `reviewer/2026-09-23-to-xm30-da-organik-c-uas-sarti-18-{375,1440}-{light,dark}.png`, `reviewer/2026-09-21-to-jet-motorlu-hedeflerin-ayri-he-{375,1440}-{light,dark}.png`.
- **R27-P1-1 (S): PASS.** The XM30 thread has five rows. The four movement rows (23, 20, 18 and 17 Eylül) link to their briefing anchors and have their `.thread-line` underlined. The 16 Eylül opening row carries the "AÇILDI" token and is plain text with no underline. Before this revision the opening row showed a right-floated "açıldı" and no row was underlined. Every other thread follows the same rule. Movement rows are underlined, and the one opening row per thread is plain text with the AÇILDI token.
  - Evidence: `reviewer/xm30-direct-1440-light.png`, `reviewer/xm30-direct-1440-dark-full.png`, `reviewer/xm30-direct-375-light-full.png`.

## Regressions

None found.
- **Briefing, 23 Sep.** The before and after captures are pixel-identical at both widths and in both themes.
- **Home, /izleme/index.html, /arsiv.html, /reports/2026-09-21.html, /haberler/2026-09-23.html.** All render normally, with no horizontal overflow at 375 or 1440 and no console errors (`reviewer/reg_*.png`).
- **abd-ordusu thread.** The page gains the daybar. Its opening row loses the awkward right-floated "açıldı" column, which becomes an AÇILDI token above the text. The page is otherwise unchanged.

Observations (not blocking):
- **Repeated sentence on XM30.** The new status line repeats the 23 Eylül row's note word for word, so "Prototip teslim edildi, şart hâlâ tanımlı değil." appears twice on the first screen. This sits against "say it once", but the criterion requires this exact line.
- **Daybar without a day.** A thread opened directly, with no `?g=`, shows today's daybar (23 Eyl).
- **No status line on some threads.** Many threads have no status line (for example 665-milyon, which has three movements). The criterion did not ask for one.
- **Notification prompt.** In a fresh browser profile the notification bar covers the bottom of the home page at 375. It is unchanged from earlier revisions.
