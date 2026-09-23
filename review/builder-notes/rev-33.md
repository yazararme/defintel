# Rev 33 — builder notes (yabancı adlarda noktalı İ · NOKTALI-İ)

Branch `rev21-33`. Nothing is committed or pushed. No workflow was triggered, no secret was
created or read, and no `gh` write command was run. `worker/`, `sw.js` and `assets/app.css`
were not touched.

## What changed

| # | File | Change |
|---|---|---|
| R33-P0-1 | `build.py` `src_name()` (new "Rev 33" section at the end) | Every source name now goes through `src_name()`. If the source's country is not TR, the name is wrapped in `<span lang="en">`. `SRC_ULKE` is a name → country map built by `kaynak_ulkeleri(news)` at the start of `main()` from every day's `items[].country`. `clip_html()` (`.clip-meta`) calls it. |
| R33-P0-2 | `build.py` | `sources_page()` (`.sname` on `/haberler/<gün>-kaynaklar.html`) calls `src_name()`. The report bibliography gets the same wrap: `render_body()` → `kaynakca_sar()` wraps a known foreign source in `… — {Kaynak}, GG.AA.YYYY` inside `li.source`. |
| R33-P1-1 | `build.py` `noktali_i_kurali()` | This is NOKTALI-İ. It runs on every build, after all pages are written. It prints a log line and writes the (A) section. If it finds any example, it sends one alert via `uyari.ekle("NOKTALI-İ", …)`. |
| orchestrator | `.github/workflows/build.yml` | New dispatch input **`noktali_boz`** (boolean, default false). It sets job env `NOKTALI_BOZ=1`, adds `|| inputs.noktali_boz == true` to the `UYARI_TEST_ONEK: "[TEST] "` expression, and skips the commit/push step (`if: env.KAPSAM_BOZ == 'none' && env.NOKTALI_BOZ != '1'`). `boz`, `kapsam_boz` and `uyari_test` still work as before. On push events the input is null, so the env is `'0'`. All workflow YAML files parse. |
| — | `review/tools/smoke.py` | Adds `r33_checks` (see Tests). |

The site's HTML changes only by the added `<span lang="en">…</span>` wrappers. I checked this
by stripping the spans from each of the 25 changed pages: the result is byte-identical to
`HEAD`. A `NOKTALI_BOZ=1` build reproduces `HEAD` exactly.

## Decisions a reviewer should know

- **"SCMP (Çin)"** becomes `<span lang="en">SCMP</span> (Çin)`. `ad_parcalari()` keeps a
  trailing parenthesis that contains Turkish letters outside the wrap. Otherwise `lang="en"`
  would render "(ÇIN)". The browser now shows "SCMP (ÇİN)". A parenthesis with no Turkish
  letters, such as "Defence24 (PL)", stays inside the wrap.
- **Sources with no country in the data.** These are failed or quiet roster names, which carry
  a name but no `ulke`. They count as foreign unless the name contains a Turkish letter
  (`çğıöşü`). Known TR sources in the data are AA, SavunmaSanayiST and DefenseHere, and they
  stay plain. The fallback only matters on the Kaynaklar page.
- **Scope of the rule.** The uppercase selector list is parsed from `app.css`. It currently has
  24 selectors, and `text-transform: none` overrides such as `.tagline` are honoured. Pseudo
  selectors are skipped: `.prose td::before` takes its text from `data-label`, so it can't be
  wrapped. `@media` blocks are treated as always on. The rule checks every built page:
  `haberler/`, `reports/`, `izleme/` and the root `*.html`. It searches for names
  case-sensitively and on word boundaries. The names are the foreign part of every non-TR
  source, plus every tracked player whose role is not Turkish. Text inside any element with a
  `lang` attribute is ignored; `<html lang="tr">` does not count.
- **Player names.** Today no foreign player name is rendered in an uppercase field. `clip-tr`
  tags are Turkish roles only, and the rail and `/oyuncular.html` names are not uppercase. So
  there was nothing to wrap. NOKTALI-İ still scans foreign player names, so a future uppercase
  site would alert.
- **Bibliography and Kaynaklar `.sname`.** Neither is uppercase in `app.css`. They are wrapped
  for correct language metadata, not to fix a visible bug. Bibliography sources that the agent
  names but that are not in the data (for example "Kongsberg") are not wrapped.
- **(A) and the alert.** The (A) section is "### NOKTALI-İ — büyük harfli alanda yabancı ad
  (Rev 33)". In a normal run it reads **🟢 NOKTALI-İ: 0 örnek**. In a run with examples it
  reads 🔴 N örnek plus a table of the first 10 (page, element, name, text). The issue line is
  `NOKTALI-İ: büyük harfli alanda lang'sız yabancı ad N örnek, K sayfada (NOKTALI_BOZ=1,
  bilerek) — ilk: <3 distinct page/name pairs>`.

## Tests (local, 23 Sep)

- `python3 build.py`: exit 0, `· NOKTALI-İ: 0 örnek · 90 sayfa, 24 büyük harfli seçici (app.css)`.
- Broken build, simulating CI (`NOKTALI_BOZ=1`, `RUNNER_TEMP`/`GITHUB_STEP_SUMMARY` in scratch,
  `UYARI_TEST_ONEK="[TEST] "`, no token): the log shows `NOKTALI-İ: 3212 örnek (NOKTALI_BOZ=1,
  bilerek)` across 7 media pages. (A) has the 🔴 line and the 10-row table, starting with
  Unmanned Airspace ×2, Defense Daily, Defence Industry Europe…. The alert reached the uyari
  file, and the flush listed it. No API call was made because there was no token.
- Browser check (system Chrome, `locale=tr-TR`, 1440×900, `/haberler/2026-09-23.html`):
  - Öne çıkanlar shows **"UNMANNED AIRSPACE"** and **"DEFENSE DAILY"** with a dotless I.
  - **"ANADOLU AJANSI — GÜNCEL"** is unchanged, and SAVUNMASANAYİST keeps its Turkish İ.
  - No `.clip-meta` on the page renders any foreign source name with İ.
  - With the broken build the same row shows "UNMANNED AİRSPACE".
- Kaynaklar page (`/haberler/2026-09-23-kaynaklar.html`): 0 foreign `.sname` without `lang="en"`.
- `check_reports.py --dort-durum`: 🟢 4/4. `--oyuncular`: 🟢 all shots. Structural
  `check_reports.py`: all ok.
- `scripts/test_uyari.py`: 33/33. `scripts/test_collect.py`: 21/21.
- `python3 review/tools/smoke.py`: **SMOKE OK**. New lines:
  - build line
  - `src_name()` 7/7 unit cases
  - the 1440 tr-TR browser check
  - the broken build (alert present, browser shows "UNMANNED AİRSPACE"), followed by a normal
    rebuild

The tree is left in the normal build.

## Not done / for the reviewer

- The (I), (A) and live (S) evidence needs a push plus a `build.yml` dispatch with
  `noktali_boz=true` on `rev21-33`, which is outside my limits. That run posts one NOKTALI-İ
  line to the `[TEST] DEFINTEL uyarıları · <gün>` issue, writes the first 10 examples to (A),
  and commits nothing. A normal run's (A) shows "0 örnek".
- The 1440 screenshot I took (Öne çıkanlar, tr-TR) is in the session scratchpad, not in
  `review/`. My limits allow creating only this notes file there.
