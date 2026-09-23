# Rev 21 — verdict: FAIL

I checked the local site (http://localhost:8000, in the 64/64 state) at 375×812 and 1440×900, light and dark. My screenshots are in `review/shots/rev-21/reviewer/`. For the below-64 state I used the builder's `after-alt64/` shots and the CI artifact of run 35871351691, as instructed; I did not rebuild. The orchestrator's message contained no builder rationale. (I) is not an evidence type in my instructions; the orchestrator substituted it for the (P) phone alert, so I judged it from the issue screenshot instead of marking PENDING-HUMAN.

| # | Result | Evidence |
|---|---|---|
| R21-P0-1 (S) | PASS | Below-64 state, 375: top line is only "izlenen 64", no row carries "kez", "önce" or any count/age token, and the first two rows are Anduril, Arsenal Bulgaria. Seen in `after-alt64/oyuncular-375-light.png`, `-375-dark-full.png`, `-1440-light.png`, and independently in CI `after/A-boz-thales-artifact/kapsam-sayi-35871351691-1/1-oyuncular-375.png`. |
| R21-P0-2 (S) | FAIL — not verifiable | The criterion is about the below-64 state with the Mühimmat chip open. No evidence shows that: `after-alt64/` and both CI artifacts only show the "Tümü" state, and the local site is 64/64. On the local site the chip does recompute the segment count ("Bugün 6 · son 30 günde 9 · izlenen 23"; 23 matches the Mühimmat rows I counted), `reviewer/oyuncular-muhimmat-*-{light,dark}.png`. But I could not see that the below-64 top line becomes only "izlenen 23". |
| R21-P1-1 (A) | PASS | `after/A-normal-ozet-girisli.jpg`: "alias testi 64/64". The KAPSAM-SAYI table shows 64/64 at 375 and 1440. |
| R21-P1-2 (S) | PASS | `?oyuncu=thales` shows "3 / 536 başlık" and three Thales rows under Rakip Duyuruları in all four combinations: `reviewer/haberler-thales-375-light.png`, `-375-dark.png`, `-1440-light.png`, `-1440-dark.png`. |
| R21-P1-3 (I)+(S) | PASS | **(I)** `after/I-issue-5-kapsam.jpg`, issue #5: "KAPSAM-SAYI · KAPSAM-SAYI: 63/64 — kalanlar: Thales (KAPSAM_BOZ=thales, bilerek) · oyuncu sayıları basılmadı". The broken run's summary links issue #5 (`after/A-boz-thales-ozet-girisli.jpg`). **(S), broken build:** no counts or age tokens on any row, top line "izlenen 64", alphabetical order (`after/A-boz-thales-artifact/kapsam-sayi-35871351691-1/1-oyuncular-375.png`; summary reads "0 satırda sayı/jeton"). **(S), 64/64:** "Bugün 15 · son 30 günde 27 · izlenen 64", "N gün" and age tokens ("bugün", "dün", "3 gün önce") appear, and the list is in frequency order (Rheinmetall, Hanwha, …) in `reviewer/oyuncular-375-light.png`, `-375-dark.png`, `-1440-light.png`, `-1440-dark.png`. |

## Regressions

- I found none. oyuncular, index, reports/2026-09-23 and haberler/2026-09-23?oyuncu=thales all return 200 at both widths and in both themes. None has horizontal overflow, and there are no page JS errors.

## Observations (not criterion failures)

- **The active chip label disappears under hover or focus.** Right after a click, while the pointer is still over it, the active "Mühimmat" chip's label is almost invisible: dark on dark green in dark mode, light on a light fill in light mode (`reviewer/oyuncular-muhimmat-375-dark.png`, `reviewer/oyuncular-muhimmat-1440-light.png`). Once the pointer moves away, the label reads correctly (`reviewer/oyuncular-muhimmat-nohover-*.png`). Phones can keep the hover state after a tap, so a 375 reader may see a blank active chip. I can't tell from before/ whether this is new in this revision.
