# Rev 22 — builder notes (arama durumları + DÖRT-DURUM)

Branch `rev21-33`, not committed or pushed. No workflow triggered, no secret read, no `gh`
write. `worker/` and `sw.js` not touched. The `sw.js` bump isn't needed because `app.js` is
served as `/assets/app.js?v=<hash>`, so the new file gets a new URL. The 69 built HTML files
differ only in that hash.

## What changed

| # | File | Change |
|---|---|---|
| R22-P0-1 | `assets/app.js` (archive content search) | `load()` no longer resolves an error with `[]`. `!r.ok` or a non-array body throws. The error is re-thrown and `loading` resets, so the next keystroke retries. `run()` draws the error branch separately: *"Arama şu an çalışmıyor — sayfayı yenileyin."* It gives no reason. While a search term is active the panel owns the state, so the title filter's `#noresults` ("eşleşen rapor yok") is hidden and no second verdict appears next to the panel. |
| R22-P0-2 | `assets/app.js` `sectionParts()` | The walk stops at `#noresults`. Before, when the last section emptied, the walk hid `#noresults` too, and the page went blank. |
| R22-P1-1 | `assets/app.js` | If `search.json` isn't loaded within `SLOW_MS = 300` ms, the panel says "Aranıyor…". The timer clears on success or error. |
| R22-P1-2 | `assets/app.js` (`rescope()`) | When a filter (text or pill) is on, the first `.news-stat > .num` reads `{görünen} / {toplam}`. It goes back to `{toplam}` when the filter clears. The numerator counts **unique headlines**, not rows (see below). |
| extra | `assets/app.js` `applyUrl()` | The pill scope now filters rows only on the clips page. On `arsiv.html?oyuncu=…` it was hiding every day card, because cards carry no `data-oyuncu`. `scopeDays()` then restored the right cards, but "Bu filtreyle eşleşen rapor yok" stayed on screen above them: a no-results message shown next to results. Found while testing. Fixed with one line. |
| R22-P1-3 | `scripts/check_reports.py` | New `--dort-durum [--out DIR] [--base URL] [--boz AD]`. It serves the repo root on a random local port (or uses `--base`) and runs 4 scenarios in headless Chromium (Playwright async). Service workers are blocked so routing works. Each scenario saves `N-<ad>.png`, writes a pass/fail table to `$GITHUB_STEP_SUMMARY`, and on any failure calls `uyari.ekle("DÖRT-DURUM", …)` once per failed scenario and exits 1. The browser is bundled Chromium, falling back to `channel="chrome"`. `yaml` is now imported inside `check()`, so the browser check runs without PyYAML. The structural check behaves the same as before. |
| R22-P1-3 | `.github/workflows/build.yml` | Adds a `workflow_dispatch` input `boz` (choice: `none`, `fetch`, `noresults`, `yukleniyor`, `sonuc`; default `none`). Job env: `DORT_DURUM_BOZ`, plus `UYARI_TEST_ONEK: "[TEST] "` only when `boz` ≠ none. Otherwise it is empty, which keeps the Rev 30 behaviour: an issue opens only on main. New steps after `build.py`: install Playwright, `DÖRT-DURUM`, an alert if Playwright fails to install, upload the screenshot artifact (`always()`), and add the artifact link to (A). The commit/push step is unchanged and runs only on success, so a red DÖRT-DURUM stops the build. The Rev 30 flush is still the last step. The push `paths` filter now also includes `scripts/check_reports.py`. |
| — | `review/tools/smoke.py` | Also runs DÖRT-DURUM against `localhost:8000` and a scope-line check: the first `data-oyuncu` id → `N / 536` → × → `536`. It needs a Playwright python (`DEFINTEL_PW_PYTHON`, the local shotenv, or the current interpreter). If none is found, the check fails; it is not skipped. |

**How the scenarios are broken.** `boz=AD` swaps one marked line of `app.js` inside the
browser, through `page.route`. Nothing is written to disk or to the repo, so the red run is
produced without committing broken code. Each break brings back that scenario's old bug:

| `boz` | What changes in the browser's `app.js` |
|---|---|
| `fetch` | The error resolves with `[]` again |
| `noresults` | The walk no longer stops at `#noresults` |
| `yukleniyor` | The threshold becomes 1e9 ms |
| `sonuc` | The match is always false |

If a marker is missing, the scenario turns red with "boz uygulanamadı", so a failed break
can't pass silently. The markers are `/* DÖRT-DURUM:<ad> */` comments in `app.js`, and
editing those lines has to keep `DD_BOZ` in sync.

## Screenshots in (A): what I chose

GitHub's summary sanitizer strips `data:` URIs from `<img>`, and has since about 2014 (community
discussions #101814, #35932; C. Kerr, 2025). Relative paths don't resolve either. Only absolute
external URLs render. I first wrote a step that pushed the PNGs to a `kanit-dort-durum` branch
with git plumbing and embedded them in the summary via SHA-pinned `raw.githubusercontent.com`
URLs. The repo is public, so this would render. The permission classifier blocked that
workflow change, as a CI push to a new shared branch. So (A) now carries the **pass/fail
table**: scenario, expected result, 🟢/🔴, what was observed, and the image file name. The
PNGs are uploaded as the **artifact** `dort-durum-<run>-<attempt>`, and its link is written
into (A). The reviewer sees the table on the summary page and the images one click away.
Inline images need operator approval for the branch-push variant (about 30 lines, ready to
re-add).

## Test results (local, 23 Sep, system Chrome)

- Before the fix, the new check against the current code: **3 red** (fetch showed ""Hanwha"
  için kayıt yok."; `#noresults` not visible; loading panel empty) and 1 green. This confirms
  F-01, F-02 and F-16.
- After the fix: **4/4 green** (fetch shows "Arama şu an çalışmıyor — sayfayı yenileyin.";
  `#noresults` visible at 375px showing "Bu aramayla eşleşen kupür yok."; "Aranıyor…" after
  1 s; Hanwha returns 6 results).
- With `--boz` set to each of the four values: exactly that scenario goes red, the other three
  stay green, and the exit code is 1.
- Simulated CI (`RUNNER_TEMP` and `GITHUB_STEP_SUMMARY` in scratch, `boz=fetch`,
  `UYARI_TEST_ONEK`, no token): the table is written, the `DÖRT-DURUM · fetch kaldı (boz=fetch,
  bilerek) …` line reaches the uyari flush, and no API call is made because there is no token.
- `python3 build.py`: exit 0. `python3 scripts/check_reports.py`: all reports ok.
- `python3 review/tools/smoke.py`: **SMOKE OK** (DÖRT-DURUM 4/4, and the scope line
  `baykar: '2 / 536 başlık' → × → '536 başlık'`).

## For the reviewer / not done

- **R22-P1-2 acceptance says `?oyuncu=roketsan` → "2 / 536".** Today it shows **"1 / 536"**,
  which I believe is correct. Roketsan's only headline (ASELSAN–ROKETSAN contract) appears in two
  rows, *İhale ve sözleşmeler* and *Türk savunma sanayii*. The 536 is a count of unique
  headlines; there are 551 rows. Counting rows would give 2 here, and 551 / 536 for a filter
  that matches everything. `baykar` shows 2 / 536.
- **R22-P0-2 acceptance says a "sonuç yok" text is visible.** The visible text is the existing
  "Bu aramayla eşleşen kupür yok." (built by `build.py`, which is outside this revision's file
  list). I didn't change the wording.
- (A) and (I) evidence needs a push plus a dispatch with `boz=fetch` (for example). That is
  outside my limits. The first CI run also checks Playwright's `--with-deps` install on
  `ubuntu-latest`. Locally I only used system Chrome.
- A dispatch with `boz=none` on a non-main branch commits and pushes the build to that branch.
  That was already true before.
