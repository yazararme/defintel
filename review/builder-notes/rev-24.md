# Rev 24 — builder notes (the executive's first screen · İLK-EKRAN)

Branch `rev21-33`. Nothing is committed or pushed. No workflow was triggered, no secret was
created or read, and no `gh` write command was run. `worker/` and `sw.js` were not touched. The
tree is left in the normal build.

## What changed

| # | File | Change |
|---|---|---|
| R24-P0-1 | `assets/app.css` (the `max-width: 920px` block) | Below 920px, `.report-grid` becomes a one-column flex box (`align-items: stretch`, `gap: 0`, `max-width: var(--measure)`, centred). `article.column` and `.prose` get `display: contents`, so the rail and the prose children become siblings. The rail gets `order: 1` and everything after the summary list (`.prose > h2#ozet + ol ~ *`, plus anything after `.prose`) gets `order: 2`. The rail now sits after the summary and before PORTFÖYE ETKİSİ. The rail is not hidden. Above 920px nothing changes: the rail is in the left column. |
| R24-P0-1 (text block) | same | In a flex box, margins don't collapse and each item gets its own formatting context. Four rules restore the collapsed values, so the text block keeps the same vertical rhythm as before: `devnav` margin-bottom 0; `.prose > :has(+ h2, + h3, + .appendix, + .refs)` margin-bottom 0; `.watch` margin-top 0; the last `li` of a top-level list margin-bottom 0. I measured every top-level prose child on all 10 reports at 375 and 834, before and after the change. From PORTFÖYE ETKİSİ onward, offsets and widths are identical. The one exception is the `details.refs` box, which starts 48px higher because its inner h2 margin no longer collapses through it. Its content is at the same place (summary → kicker 92px, before and after). At 1440 nothing moved. |
| R24-P0-1 (alarm) | same | The old `.report-title { order: -1 }` had no effect in the grid, because the title is inside the article. Under the flex box it would have come alive and lifted the title above the alarm band, so `.report-grid .report-title { order: 0 }` keeps DOM order. On alarm days, ALARMLAR stays above the summary: it comes before `h2#ozet`. |
| R24-P0-2 | `assets/app.css` (the `max-width: 700px` block) | The briefing chip strip (`.report-grid .devnav`) is one row: `flex-wrap: nowrap`, `overflow-x: auto`, scrollbar hidden. It is not sticky (below 700px it was already static). The strip bleeds to the screen edge (`margin: 10px -18px 0; padding: 2px 18px 10px`), so the cut-off chip at the edge shows that more chips follow. Chrome trim: `.report-grid` margin-top goes 26→12 and the strip's top margin 18→10. The media page's `.catbar` is untouched. |
| R24-P1-1 | `build.py` `label_table_cells()` + `KART_ETIKET` | The cell under the header "İzlenecek gösterge" gets `data-kart="İzlenecek"`. The column is found by its header, not by position. |
| R24-P1-1 | `assets/app.css` (700px) | `.prose td[data-kart]::before { content: attr(data-kart); display: block; … color: var(--muted) }`. It inherits the shared label voice (`.prose td::before`: mono, 11.5px, uppercase), so under `lang="tr"` it renders **İZLENECEK** above each card's third field. At 1440 there is no label, because the column header says it. NOKTALI-İ skips pseudo selectors, and the word is Turkish anyway. The build still reports `NOKTALI-İ: 0 örnek`. |
| R24-P1-2 | `scripts/check_reports.py --ilk-ekran [--out DIR] [--base URL] [--gun G …] [--boz]` | The default day is the latest report. The check opens the report at 375×812 (tr-TR, service workers blocked, waits for `document.fonts.ready`) and takes a viewport screenshot `ilk-ekran-<gün>-375x812.png`. It measures the `h2#ozet` top (≤300) and the bottom of summary item 4 (≤812; if the summary has fewer than 4 items, the last item), plus the rail top and page overflow for information. It writes a table to `$GITHUB_STEP_SUMMARY`. For each failed day it calls `uyari.ekle("İLK-EKRAN", …)` and exits 1. `--boz` (or `ILK_EKRAN_BOZ=1`) swaps the marked line `/* İLK-EKRAN:ray */` in the browser's `app.css` via `page.route` (`order: -2`), which puts the rail back on top. Nothing is written to disk. If the marker is missing, the day turns red with "boz uygulanamadı". |
| orchestrator | `.github/workflows/build.yml` | New dispatch input **`ilk_ekran_boz`** (boolean, default false). It sets job env `ILK_EKRAN_BOZ=1`, adds `|| inputs.ilk_ekran_boz == true` to the `UYARI_TEST_ONEK: "[TEST] "` expression, and skips commit/push (`&& env.ILK_EKRAN_BOZ != '1'`). New steps come after KAPSAM-SAYI and before commit: `İLK-EKRAN` (`if: always() && steps.pw.outcome == 'success'`, `continue-on-error: true`, so it alerts but does not block), an artifact `ilk-ekran-<run>-<attempt>` with the 375×812 PNG, and the artifact link in (A) (Rev 22 pattern). `boz`, `kapsam_boz`, `uyari_test` and `noktali_boz` are unchanged. All workflow YAML files parse. |
| — | `review/tools/smoke.py` | Adds `r24_checks` (see Tests). |

The built HTML changes only by the `data-kart` attribute on report table cells and the
`app.css?v=` hash. I checked this: the removed and added lines in `reports/` are identical once
`data-kart` and the hash are stripped.

## Measured edges, 375×812 (`--ilk-ekran --gun …`, system Chrome, light)

| day | h2#ozet top | item 4 bottom | rail top | İLK-EKRAN | before Rev 24 (h2 / item 4) |
|---|---|---|---|---|---|
| 14 Sep (alarm) | 854 | 1441 | 1618 | 🔴 both | 984 / 1571 |
| 15 Sep | 294 | 922 | 958 | 🔴 item 4 | 405 / 1034 |
| 16 Sep | 325 | 902 | 938 | 🔴 both | 437 / 1013 |
| 17 Sep | 294 | 791 | 916 | 🟢 | 452 / 949 |
| 18 Sep | 294 | 791 | 942 | 🟢 | 452 / 949 |
| 19 Sep | 357 | 855 | 1006 | 🔴 both | 534 / 1032 |
| 20 Sep | 357 | 855 | 1006 | 🔴 both | 497 / 994 |
| 21 Sep | 325 | 718 | 843 | 🔴 h2 | 465 / 857 |
| 22 Sep | 325 | 744 | 869 | 🔴 h2 | 483 / 902 |
| **23 Sep (latest)** | **294** | **791** | 942 | 🟢 | 471 / 968 |
| 23 Sep, `ILK_EKRAN_BOZ=1` | 401 | 898 | 110 | 🔴 + alert | — |

The CI step checks only the latest day. The rows for other days come from `--gun`.

## Tests (local)

- `python3 build.py`: exit 0, `NOKTALI-İ: 0 örnek`. Structural `check_reports.py`: all ok.
- İLK-EKRAN normal: 🟢 294 / 791, exit 0. İLK-EKRAN with the rail moved back, simulating CI
  (`RUNNER_TEMP` and `GITHUB_STEP_SUMMARY` in scratch, `UYARI_TEST_ONEK="[TEST] "`, no
  token/repo): 🔴 401 / 898, exit 1. The alert line reached `defintel-uyari.jsonl`, and the
  `uyari.py` flush listed it in (A): `İLK-EKRAN · 2026-09-23 brifingi 375×812 (ilk_ekran_boz,
  ray bilerek geri taşındı): özet başlığı 401px > 300; 4. madde alt kenarı 898px > 812`. No API
  call was made, because there was no token.
- `--dort-durum` 🟢 4/4. `--oyuncular` 🟢 all 6 rows. `test_uyari.py` 33/33. `test_collect.py` 21/21.
- `python3 review/tools/smoke.py`: **SMOKE OK**. It adds 4 checks:
  - `data-kart` on every table row, 10/10 reports
  - İLK-EKRAN normal is green
  - İLK-EKRAN with `ILK_EKRAN_BOZ=1` is red and raises the alert
  - a browser pass over all 10 reports × 375/1440 × light/dark (40/40): at 375 the rail sits between the summary list and `h2#portfoy`, chips are one row, every card shows `İzlenecek/uppercase`, and nothing overflows; at 1440 the rail is left of the article and level with it, with no card label
- Screenshots (session scratchpad, not in `review/`): 14, 19, 21 and 23 Sep at 375×812 and
  1440×900, light and dark. They show the 375 first screen with the title, one chip row, YÖNETİCİ
  ÖZETİ and items 1–4 on 23 Sep. After scrolling, the TARAMA/OYUNCULAR strip sits under item 5,
  then PORTFÖYE ETKİSİ, with cards showing İZLENECEK. At 1440 the layout is unchanged. At 834
  (tablet, one column) the sticky chip strip still pins at 48px, and a chip tap lands its heading
  at 122px.

## For the reviewer / not done

- **Selector name.** The brief says `h2#yonetici-ozeti`. On the page the heading is
  `<h2 id="ozet">YÖNETİCİ ÖZETİ</h2>`, and CSS and anchors use `#ozet`. I measured
  `h2#ozet` and did not rename the id.
- **The rule will fire on many days.** Only 3 of 10 reports pass. There are three causes, none
  of them chrome:
  - Four-line titles push h2 to 325–357. The build already warns "manşet 17/19 kelime (üst
    sınır 14)" on 19 and 20 Sep.
  - Long summary items push item 4 past 812 on 15 and 16 Sep.
  - On alarm days, the alarm band and ALARMLAR come first (Rev 9), so 14 Sep can never pass.
  I did not shrink the title, the summary type or the masthead, because the text block and the
  colophon are outside this brief. An alarm day will always raise İLK-EKRAN; whether it should is
  the orchestrator's call.
- **23 Sep passes with 6px to spare on h2.** CI uses bundled Chromium on Ubuntu with the same
  Google Fonts. A line-wrap difference in the title could still turn a normal run red.
- `:has()` is used for one margin rule. On a browser without it, the only effect is extra space
  above h2/h3 below 920px.
- The (A), (I) and live (S) evidence needs a push plus a `build.yml` dispatch with
  `ilk_ekran_boz=true` on `rev21-33`, which is outside my limits.
