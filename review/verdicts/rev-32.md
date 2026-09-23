# Rev 32 — verdict: PASS

**Sources.** I judged this revision from:
- PRODUCT.md and the acceptance table
- the screenshots in `review/shots/rev-32/`
- public issue #5, read live
- the public log of CI run 35899581570
- http://localhost:8000

I did not read diffs, source, git history or builder notes, and I did not rebuild the site. The orchestrator's message contained no builder rationale.

**My captures.** My screenshots are in `reviewer/` and replace the earlier attempt's set. They are headless Chrome captures with tr-TR locale, with touch emulation at 375. I captured index and every report day (14–23 Sep) at 375×812, 834×1112 and 1440×900, in light and dark, first screen and full page. I tapped every `ilk:` token I found.

**Evidence rules.**
- **(I) issue page:** not an evidence type in my instructions. PRODUCT.md names a GitHub issue as the operator channel, and the orchestrator put (I) in place of the (P) phone alert, so I judged the alert from the issue.
- **R32-P1-1:** an (S) criterion that cannot be checked until five more reports exist. My rules would count it as a FAIL. The orchestrator told me to mark it PENDING-HUMAN, so I did.

## Criteria

| # | Result | Evidence |
|---|---|---|
| R32-P0-1 (S) | PASS | **Token.** On 23 Sep at 375, summary item 1 ends "…obüsü seçti (22 Eylül). ilk: 19 Eyl". The token is small grey mono on the item's last line, in light and dark. It looks the same at 834 and 1440, and index shows the same (`reviewer/reports-2026-09-23-{375,834,1440}-{light,dark}.png`, `reviewer/index-375-light.png`). **Tap.** Tapping it opens `/reports/2026-09-19.html#g1`. The H3 "Letonya Morana 155 mm kararı" appears with its Latvia/Morana paragraph, at 69 px at 375 and at 122 px at 1440, below the sticky nav (`reviewer/tap-2026-09-23-tok0-{375,1440}-{light,dark}.png`). **CI.** The CI first screen (run 35899581570) shows the token too, wrapped onto its own line (`after/A-d2-ilk-ekran/…/ilk-ekran-2026-09-23-375x812.png`). |
| R32-P0-2 (I) | PASS | **Issue #5.** It carries "**TEKRAR-MANŞET** · TEKRAR-MANŞET: 23 Eyl H1 ↔ 19 Eyl", linked to run 35891836966 (`after/I-issue-5-tekrar-manset.jpg`; I also checked it live). It is a true positive: both headlines report Latvia choosing Morana over Archer. **Latest run.** Run 35899581570 raises the same warning, and its summary lists it under Operatör uyarıları (`after/A-d2-normal-ozet-girisli.jpg`). |
| R32-P1-1 (S) | PENDING-HUMAN | Depends on the next five reports, which don't exist yet. For reference, the only item with a token on 23 Sep ends in a new-event verb: "seçti (22 Eylül)". |

## Regressions

**None found.**

The İLK-EKRAN regression that failed the earlier attempt is gone:
- **CI:** run 35899581570 reports "özetin 4. maddesi alt kenarı 799px ≤ 812 · 🟢 İLK-EKRAN: 1/1 gün geçti" (`after/A-d2-normal-ozet-girisli.jpg`, `after/A-d2-ilk-ekran/`).
- **Local:** item 4 ends at 773 px.

The earlier revisions' checks in the same run all pass:

| Check | Result in run 35899581570 |
|---|---|
| DÖRT-DURUM | 4/4 green |
| KAPSAM-SAYI | alias test 64/64; Tümü and Mühimmat rows green at 375/1440, light and dark |
| NOKTALI-İ | 0 examples |
| OPERATÖR-YALNIZ | +0 lines, reader push 0 |

The KUR and H1-TEKRAR warnings on 23 Sep are the same ones already on issue #5 from earlier runs, not new ones.

**All report days, 375 / 834 / 1440, light and dark:**
- **Overflow:** none. scrollWidth equals the viewport on every page.
- **19 Sep target page:** unchanged apart from the header spacing noted below.
- **Tokens on other days:** each one lands on the heading or item it names.
  - 15 Sep: → 14 Sep #g1
  - 18 Sep: → 17 Sep #g9
  - 20 Sep: → 14 Sep #g16, 16 Sep #g5 and 14 Sep #g5
  - Evidence: `reviewer/tap-2026-09-{15,18,20}-tok*-375-light.png`

## Observations (not criterion failures)

- **Header spacing at 375.** At 375 the space between the header and "YÖNETİCİ ÖZETİ" is about 14–15 px tighter than in `before/`, on every report day (compare `before/reports-2026-09-19-375-light.png` with `reviewer/reports-2026-09-19-375-light.png`). It still reads cleanly. 1440 is unchanged.
- **Stale alert on issue #5.** Issue #5 still carries the earlier attempt's red "İLK-EKRAN … 4. madde alt kenarı 817px > 812" line (run 35891836966), although the latest run passes. An operator reading the issue sees an open alarm that no longer holds.
- **20 Sep first screen.** On 20 Sep at 375, three tokens each add height, and item 4 ends at 863 px, below the 812 fold. İLK-EKRAN checks only the latest day, and that day would be past the fold even without the tokens.
- **Carry-overs from earlier reviews.** The landing heading is tinted with the alarm red (rgba(163,44,32,…) in light). The "uygulama olarak ekle" bar covers the bottom of the landing page in a fresh profile.
