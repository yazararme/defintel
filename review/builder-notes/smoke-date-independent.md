# smoke.py: date-independent (27 Sep 2026)

Changed: `review/tools/smoke.py` and `scripts/check_reports.py`. In check_reports.py only
`IE_OZET_KR` changed (110 → **115**, the customer's new summary-item limit) and the docstring line
that quotes it. The headline limit stays 65 and the alarm title limit stays 70. No product code, data,
workflow or page was changed. Nothing is committed.

## New knobs in smoke.py

- `DEFINTEL_BASE` sets the site URL. Default: `http://localhost:8000`.
- `KABUL_GUNU = "2026-09-23"`. Checks whose acceptance criteria are 23 Sep content now load that page
  explicitly, not "the newest day". The page exists on the branch and on main after the merge.
- `eski_toplayici(data)` decides from the data, not from a date, whether main's old collector
  collected a day. That is true when the day's JSON has no `toplamalar` key and no item carries an
  `ilk_goruldu` stamp. The Rev 31 collector stamps every item, and 23 Sep was backfilled with both.
  So main's old collector can keep writing 28 Sep and later days before the merge. (The first version
  had a date pin, `ESKI_TOPLAYICI_SON`; it is removed.)

## The 10 checks

| Check | Before | Now | Why it is not weaker |
|---|---|---|---|
| NOKTALI-İ 1440 browser | Newest media page: Öne çıkanlar has "UNMANNED AIRSPACE" and "DEFENSE DAILY", "ANADOLU AJANSI" present, no İ in any foreign name, Kaynaklar names wrapped | Everything from before, run on `/haberler/2026-09-23.html`. It FAILs if that page is missing. The newest page is also checked for the general property: lang=tr, no İ in any foreign name, no "AJANSİ", Kaynaklar names wrapped | The 23 Sep acceptance is unchanged, and the newest day gets an extra check. On the newest day "ANADOLU AJANSI" is not required, because there the AA row can sit in the closed Genel list, where innerText is not uppercased. |
| NOKTALI-İ broken build | Newest media page shows "UNMANNED AİRSPACE" | The 23 Sep page shows it | The same assertion on the page that actually has that source in Öne çıkanlar |
| R27 375/1440 unknown `?g=` | daybar == "23 Eyl · Çar" | daybar == `tr_daybar(newest report)` | What the rule means is "an unknown `?g=` keeps the default day", and the default is the newest report. On the branch that is still "23 Eyl · Çar". The XM30 and 20 Sep thread checks are unchanged. |
| (D) `2026-09-24-aday.md` first section | If the file exists, its first section must be "Dünkü brifingden sonra gelenler" and contain the AA row | Same for the untracked local evidence file (the branch case). If the file is **tracked in git** (main's real file) and `eski_toplayici()` is true for `2026-09-24.json`, the old collector wrote it. The check then says so and asserts that the Rev 31 section is absent. In every other case the file is checked for the section, including when that JSON is missing. | The evidence check is unchanged. The merged-tree case is stated and asserted, not skipped. |
| K5 tanı | Last 10 reports, which had to include 17, 18, 21, 22 and 23 Sep passing as published | Runs `--tani --gun` over the last 10 reports **plus** those five named days. All the old conditions hold for every row. | 17 Sep no longer drops out of the window, so its evidence stays in. Merged tree: 11 days. |
| GEÇ-GELEN build line | Summary line contains "2026-09-23: 89" | 23 Sep's own page line must say 89 "brifingden sonra". The summary must list exactly the last two media days, and each count must equal that day's page line. A 0 is accepted only if that day's data has no `ilk_goruldu` stamps (old collector). | The 89 is still asserted, from the line the build prints for every day. The summary gets an extra consistency check. A stamped day showing 0 fails. |
| ETİKET-BAŞLIK click | Fixed 0.4 s wait, then heading in view | Polls `scrollY` every 100 ms until three reads in a row are equal (up to 8 s). Settling at 0 counts only after 1.5 s. Not settling is a FAIL. | The same assertion (label == heading, hash, heading in view), taken once the scroll has finished |
| İPUCU-YOK / S8 line | Newest day: "yalnız ipucuyla gelen 0" | See the next section | See the next section |
| İLK-EKRAN normal | Newest report green | See the next section | See the next section |
| K5 istem sınırları (not failing, updated) | Numbers in k5-prompt.md | Now also merge-day-prompt.md. The set of "en fazla N karakter" numbers must equal {65, 70, 115}. | Stricter |

### İPUCU-YOK / S8 line

**Before:** the newest day's build line had to read "yalnız ipucuyla gelen 0".

**Now:**
- The build line's day and number must equal a fresh `s8_counts` of the newest day.
- **Every** day that is not an old-collector day (see `eski_toplayici()`) must recompute to 0.
- At least one such day must exist.
- If the newest day is an old-collector day, the build must have raised `! İPUCU-YOK · <day>` for it.

**Why it is not weaker:** on the branch it is as strict as before. On main the newest days are old-collector days, which the customer decided to leave as they are. They are named as such, and the alert has to fire for them. Every day collected under the new rules is held to 0.

### İLK-EKRAN normal

**Before:** the newest report had to be green.

**Now:**
1. `--ilk-ekran --gun 2026-09-23` must be green. This is the rule's green path on a known-passing day.
2. The newest report must be green, with one exception. It may be red only if all of these hold:
   - It breaks a prompt limit, read from the tanı table: headline over 65, one of the first 4 items over 115, or the alarm title over 70.
   - The cause is text only, never structure.
   - With the limits applied it passes, locally and in the CI worst case.
   - The rule emitted the İLK-EKRAN alert for that day.
3. `ILK_EKRAN_BOZ` now runs on 23 Sep, a green day. On a newest day that is already red, the boz run proved nothing.

**Why it is not weaker:** 27 Sep's real overflow must still be detected. The layout is still proven by the limits simulation, and a report within the limits must still be green.

## Also pinned (passing, but they had silently shrunk on newer days)

TEKRAR-MANŞET 375px and the İLK-EKRAN worst case used to run only when the newest day was 23 Sep. They
now always run on `/reports/2026-09-23.html`. The `/` page is checked only when 23 Sep is the newest
day. The R23, TEKRAR-MANŞET and KANIT-BOŞLUĞU build-line checks still check the exact 23 Sep alerts
only when 23 Sep is the newest day, because the build prints those lines only for the newest day.
Otherwise they check that the line is present. This is unchanged.

## Literal dates left in smoke.py

None of these is a cut-off date. Each one names a fixture that exists on both trees:

- **`KABUL_GUNU` = 23 Sep.** The acceptance page for R23, R25, R27, R31, R32 and R33 (the Öne çıkanlar strings, 89 late rows, the XM30 thread, "ilk: 19 Eyl", the Hanwha row and others). The `iso == "2026-09-23"` branches only add the exact 23 Sep alert text when 23 Sep is the newest day. The build prints those lines only for the newest day.
- **19 Sep and 20 Sep.** The targets of the 23 Sep acceptance: the "ilk:" token jumps to 19 Sep, and the thread is opened from 20 Sep.
- **14 Sep and 17 Sep.** The K5 alarm-day geometry pair: 14 Sep is the only alarm day and 17 Sep is a normal day.
- **17, 18, 21, 22 and 23 Sep (`GECEN`).** K5-3's named "pass as published" days.
- **`2026-09-24-aday.md` / `2026-09-24.json`.** The Rev 31 (D) evidence file has this name.
- **30 Sep.** A synthetic date in the KANIT-BOŞLUĞU rule controls. No data is read for it.

## Runs

- Branch (`rev21-33`, :8000): `ok` 92, `FAIL` 0. **SMOKE OK**
- Merged (`origin/main` fa6d27b + `rev21-33`, conflicts `--theirs`, `build.py`, :8014 with
  `DEFINTEL_BASE`): `ok` 93, `FAIL` 0. **SMOKE OK**. This run had a **fake 28 Sep**: 27 Sep's JSON
  copied with `date` changed, in the throwaway worktree only. It simulates the old collector writing
  another day before the merge. The worktree was removed and the 8014 server stopped.

Notable merged-tree lines:
- İLK-EKRAN newest report (27 Sep): red, as it should be ("manşet 70 > 65, madde 203 > 115"). With the limits applied: 263/677 · 263/730. The alert fired.
- İPUCU-YOK: the newest day, the fake 28 Sep, is an old-collector day with 53 hint-only items, and the alert fired. The Rev 31 collector's 23 Sep has 0.
- GEÇ-GELEN: 23 Sep: 89. 27 and 28 Sep: 0, and both are unstamped.
