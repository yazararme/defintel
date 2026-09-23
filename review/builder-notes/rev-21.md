# Rev 21 — builder notes (oyuncu sayıları + KAPSAM-SAYI)

Branch `rev21-33`. Nothing committed or pushed, no workflow triggered, no secrets read, no `gh` write.
`worker/` and `sw.js` not touched. The tree is left built in the normal state (alias testi 64/64).

## What changed

| # | File | Change |
|---|---|---|
| R21-P0-1 | `build.py` `players_page(hist, kap)` | Below 64/64: the top line is only `izlenen <strong data-tally="all">64</strong>`. Rows carry the name and segment tags only: no `pcount`, no age token, no `player-row--quiet` fade (the fade is also a claim the matcher makes), no `data-today`/`data-seen`. Order is alphabetical with Turkish collation (`tr_collate`: ç after c, ı before i, I→ı, İ→i; accented foreign letters fall back to their base letter). First two rows: Anduril, Arsenal Bulgaria. |
| R21-P0-2 | `build.py` | The top line keeps `data-tally="all"`, and the existing `app.js` segment code already recounts it. With "Mühimmat" on it reads `izlenen 23`. `app.js` did not need changing. |
| R21-P1-1 | `data/rakipler.json` | All 64 players have `aliases[]` and `alias_test{pos[], neg[]}`, plus optional `pos_tr[]`/`neg_tr[]` (examples tested as Turkish text) and `pos_kaynak` (`veri` means at least one positive is copied verbatim from `data/news/` or `source/`; `kurgu` means there is no headline in the data yet, so the example was written). 28 players are `veri` and 36 are `kurgu`. There are two new optional matcher fields: `tr_disi` (aliases not matched in Turkish text) and `haric` (regexes blanked out before matching). `_schema` documents all of these. |
| R21-P1-2 | `build.py` | `tag_player_headlines(items)` scans headlines for all 64 roles. Each row gets `oyuncu_ids` (all roles, which become `data-oyuncu`) and `tr_tags` (Turkish roles only, so the "Türk savunma sanayii" cross-section and the row label are unchanged, following Rev 17). `tag_turkish_headlines` is now a filter on top of it. `player_history` uses the widened pass, and its headline links changed from `?q=<ad>` to `?oyuncu=<id>`. `/haberler/2026-09-23.html?oyuncu=thales` shows 3 rows. |
| R21-P1-3 | `build.py` | KAPSAM-SAYI (see below). `sayi_30g` is renamed `gun_30g`, and the page shows `N gün`. At 64/64 the top line reads `Bugün N · son 30 günde N · izlenen 64` and the rows go back to age token + `N gün`, sorted by frequency. |
| — | `scripts/check_reports.py` | New `--oyuncular [--out DIR] [--base URL]` option. It takes full-page screenshots of `/oyuncular.html` at 375×812 and 1440×900 (`1-oyuncular-375.png`, `2-oyuncular-1440.png`), checks the page against its own `data-kapsam` state, and writes a table to (A). |
| — | `.github/workflows/build.yml` | New dispatch input **`kapsam_boz`** (choice `none`, `thales`, `iai`, `csg`; default `none`) → job env `KAPSAM_BOZ`. `UYARI_TEST_ONEK: "[TEST] "` is now set when `boz` **or** `kapsam_boz` ≠ none. New steps come after DÖRT-DURUM: `KAPSAM-SAYI görüntüleri` (runs `--oyuncular` on every run, `continue-on-error`), artifact **`kapsam-sayi-<run>-<attempt>`**, and a link to that artifact in (A). The commit/push step is skipped when `KAPSAM_BOZ != none`, so the page with no numbers never goes live. `data/rakipler.json` is added to the push `paths`. |
| — | `review/tools/smoke.py` | Adds 3 checks: the build log says `alias testi 64/64`; the 64/64 state passes `--oyuncular`; the <64 state (a `KAPSAM_BOZ=thales` build) shows `izlenen 64`, no counted rows, Anduril and Arsenal Bulgaria first, Mühimmat → `izlenen 23`, and at least 1 row for `?oyuncu=thales`. It then rebuilds normally. |

`assets/app.css` is unchanged: the rows lay out correctly with and without tokens at both widths.

## KAPSAM-SAYI mechanics

- `kapsam()` runs `alias_test()` for all 64 players on every build. A player passes only if all of these hold: `aliases` is a list; there is at least one pos/pos_tr; every pos matches; every neg fails to match; and **every match string of ≤4 characters (name or alias) has a neg/neg_tr that contains it** (checked case-folded). That last rule means a short alias can't pass on a negative that never touches it. The rule has been seen to bite. Removing IAI's negatives gives "“IAI” kısa, onu içeren negatif örnek yok". A broken `haric` regex, found while building, gives "Aselsan: yanlış eşleşti: “Korkut Özal anıldı”" and 63/64.
- `KAPSAM_BOZ=<id>[,<id>]` appends a positive that cannot match ("KAPSAM_BOZ: bu başlıkta izlenen hiçbir oyuncu yok") to that player's test. The failure therefore comes out of the real test path, not a flag. An unknown id exits 1.
- Log and (A) show `alias testi N/64 — kalanlar: …` on every build, with the reasons for each failure. The page is always produced.
- Alert (Rev 30 channel, `uyari.ekle("KAPSAM-SAYI", …)`): the previous state is read from the published `/oyuncular.html` (`<ul class="player-list" data-kapsam="N/64">`) before it is overwritten.
  - Falling below 64/64: `KAPSAM-SAYI: 63/64 — kalanlar: Thales (KAPSAM_BOZ=thales, bilerek) · oyuncu sayıları basılmadı`
  - Reaching 64/64: `KAPSAM-SAYI: 64/64 — sayılar döndü (64/64'e varış)`
  - If there is no marker (the first build under this rule), the current state is reported once.
- `data/oyuncular.json` (D) omits `son` and `gun_30g` below 64/64. It keeps `gunler`, which the archive's `?oyuncu=` filter reads.
- A local CI simulation (`RUNNER_TEMP`, `GITHUB_STEP_SUMMARY`, `UYARI_TEST_ONEK`, `KAPSAM_BOZ=thales`, no token) wrote (A) as 🔴 `alias testi 63/64 — kalanlar: Thales`, the screenshot table, and the operator-alert line. No API call was made because there is no token.

## Alias decisions (matcher behaviour changes)

- **BAE** is `tr_disi`. In Turkish text "BAE" means the UAE. This fixed two real false positives: a sweep row "…Güney Afrika ve BAE'ye açılıyor", and `reports/2026-09-19.html`, where the rail linked BAE Systems to **G3 "Hanwha ve EDGE Group (BAE)"** (an Abu Dhabi deal). It now links to G1, where BAE Systems Bofors actually appears. That is the only change to report HTML. Development titles are now matched as Turkish text (`tr=True`).
- Removed as ambiguous: `Gökberk` (a first name), `CBC` (the broadcaster), `FN` (Scandinavian "UN"), `PPU` (power processing unit), `MIL`/`OFB`/`Ordnance Factory` (spread across India's DPSUs), `Arsenal AD` ("Arsenal ad…"), bare `Oerlikon` (OC Oerlikon), and bare `Kalyani` (city/surname). Replacements: `Oerlikon Contraves`, `Kalyani Strategic Systems`, `Arsenal Kazanlak`, `FN America`, three MIL factory names, `Colt Canada`, `Colt's Manufacturing`, `Northrop`, `SAAB`, `Junghans Microtec`, `China North Industries`.
- `KORKUT` is kept: G7 on 23 Sep is about Korkut 150/35, and dropping it moved Aselsan's rail anchor. It is guarded by `haric` for "Dede Korkut" and "Korkut Özal/Eken/Ata". Its negatives include a real headline ("Rusya'nın Korkutulmasının…").
- `haric` is also used for Hanwha Qcells/Solutions/Life, `CSG-<digit>` (carrier strike group), POF-USA, Leonardo da Vinci/DiCaprio, Rafael Grossi/Nadal, Olin College/Business School, BMC Software/Medicine, and Canik Belediye/ilçe/kaymakam.

## Results (local, 23 Sep)

- Alias test: **64/64**. `python3 build.py` exits 0.
- `check_reports.py --dort-durum`: 4/4 green. The structural check: 10 ok. `test_uyari.py`: 28/28.
- `review/tools/smoke.py`: **SMOKE OK**, including the 3 new KAPSAM-SAYI lines. The Rev 22 scope-line check now picks `kongsberg` (the first `data-oyuncu` on the page, because foreign rows are now tagged): `5 / 536`, and roketsan is still `2 / 536`.
- Rendered HTML diff against HEAD: the `haberler/*.html` changes are only extra ids in `data-oyuncu`. The Türk savunma sanayii counts are unchanged (09-22: 1, 09-23: 3).

## Local evidence commands

- Below 64 (numbers hidden): `KAPSAM_BOZ=thales python3 build.py`
- 64/64 (normal): `python3 build.py`
- Screenshots of the current state: `~/.local/share/defintel-shotenv/bin/python scripts/check_reports.py --oyuncular --out <dir>`

## For the reviewer / not done

- The (I), (A) and CI (S) evidence needs a push plus a `build.yml` dispatch with `kapsam_boz=thales`, which is outside my limits. If the committed `oyuncular.html` is at 64/64 (as left here), that run posts the fall alert to the `[TEST]` issue. If there is no marker, it posts too. Because this tree was already built locally at 64/64, the first normal CI build on main will **not** send the "reached 64/64" alert. That alert fired locally instead.
- 36 of the 64 players have no headline in the current data, so their positives are written examples (`pos_kaynak: kurgu`). They test the matcher honestly, but they are not observed headlines.
- Known residual ambiguity, not covered by a test: CSG as "Nimitz CSG" (carrier strike group without a number), SAGE (UK advisory group), Epirus (Greek region), Junghans (watches), Bayraktar (a surname), Canik outside the listed contexts.
- The rail is unchanged, as the brief asks: foreign players who appear only in headlines are not added to it. The rail still names a foreign player only when a development mentions it.
