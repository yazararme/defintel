# Rev 32 — verdict: FAIL

I judged this revision from PRODUCT.md, the acceptance table, review/shots/rev-32/, public issue #5 (read live through the GitHub API) and http://localhost:8000. I did not read diffs, source, history or builder notes. The orchestrator's message contained no builder rationale. I did not rebuild the site.

My screenshots are in `reviewer/`. They are headless Chrome captures (tr-TR locale, touch emulation at 375) at 375×812 and 1440×900, light and dark. I scanned every report day (1–23 Sep) for `ilk:` tokens and tapped each token I found.

I accepted (I) as evidence because PRODUCT.md names a GitHub issue as the operator channel. R32-P1-1 is an (S) criterion that cannot be checked until five more reports exist. My rules would treat an unverifiable (S) criterion as a FAIL, but the orchestrator told me to mark it PENDING-HUMAN, so I did. It is not the reason for this FAIL.

## Criteria

- **R32-P0-1 (S): PASS.** On 23 Sep at 375, the first summary item ends "…obüsü seçti (22 Eylül). ilk: 19 Eyl". The token is in small grey mono and sits on the item's last line. It looks the same at 1440 and in dark mode. When I tapped it at 375, it opened `/reports/2026-09-19.html#g1`, and the H3 "Letonya Morana 155 mm kararı" sat at the top of the viewport (top 69 px) with its paragraph. I got the same result at 1440 and in dark mode. The 19 Sep page is pixel-identical before and after this revision.
  - Evidence: `reviewer/reports-2026-09-23-{375,1440}-{light,dark}.png` and `reviewer/tap-2026-09-23-tok0-{375,1440}-{light,dark}.png`. Against `before/`, the only difference is the token's own box.
- **R32-P0-2 (I): PASS.** Issue #5 carries "**TEKRAR-MANŞET** · TEKRAR-MANŞET: 23 Eyl H1 ↔ 19 Eyl", linked to run 35891836966. It is a true positive: both headlines are about Latvia choosing Morana over Archer. I judged only lines from this revision.
  - Evidence: `after/I-issue-5-tekrar-manset.jpg`; I also checked it live.
- **R32-P1-1 (S): PENDING-HUMAN.** This criterion depends on the next five reports, which don't exist yet. The only token-bearing item on 23 Sep does open with a new-event verb ("seçti (22 Eylül)").

## Regressions

- **R24-P1-2 first-screen check (İLK-EKRAN) now fails in the normal CI build.** The Actions summary for run 35891692823 reports "4. madde alt kenarı 817px > 812 🔴", which means the 4th summary item's bottom edge is past the 812 px screen. It also sends an İLK-EKRAN operator alert, and issue #5 carries that line, linked to run 35891836966. In the Rev 24 normal run, the same measurement was 791 px and passed.
  - Cause: in the CI 375×812 capture, the token "ilk: 19 Eyl" wraps onto a line of its own, so item 1 gains a line and pushes item 4 below the fold.
  - Locally the token fits on the last line, and item 4 ends at 791 px. The operator's own gate still fails, though, and the 375 first screen the check protects no longer holds in CI.
  - Evidence: `after/A-normal-ozet-girisli.jpg`, `after/A-normal-ilk-ekran/…/ilk-ekran-2026-09-23-375x812.png`, `after/I-issue-5-tekrar-manset.jpg`.

I checked tokens on other days and all of them are real repeats. Each one lands on its target, which is visible at the top of the viewport at 375 and 1440.
- **15 Sep:** "ilk: 14 Eyl" goes to the USAF barrel-based air-defence market survey (14 Sep #g1).
- **18 Sep:** "ilk: 17 Eyl" goes to the DHS C-UAS Track One item (17 Sep #g9).
- **20 Sep, three tokens:**
  - Drone Round → 14 Sep #g16
  - XM30 organic C-UAS → 16 Sep #g5
  - SGT STOUT → 14 Sep #g5
- Evidence: `reviewer/tap-2026-09-{15,18,20}-tok*-375-light.png`.

Observations (not blocking):
- **Alarm tint on the landing target.** The heading a token lands on is briefly tinted with the alarm red (rgba(163,44,32,…)). PRODUCT.md reserves colour for alarm. I could not tell whether this revision introduced it.
- **Notification prompt covers the landing.** In a fresh browser profile, the "Yeni rapor çıkınca haber verelim mi?" bar covers the bottom of the page you land on at 375.
