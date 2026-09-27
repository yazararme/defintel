# Trial merge — rev21-33 into origin/main (27 Sep 2026, not pushed)

Throwaway branch `trial-merge-throwaway` from `origin/main` (`fa6d27b`), in a separate worktree;
merged `rev21-33` at `1c2a576` (K7). Worktree and branch deleted afterwards; nothing pushed.

## What main has that the branch doesn't

Only the daily pipeline: 4 `report:` commits (24–27 Sep) and 8 `news:` commits (two per day,
05:xx and the ~11:00 backstop). No code or workflow change on main since the branch was cut.

## Conflicts: 23 files, all generated output

| Files | Why | Resolution |
|---|---|---|
| 20 × `izleme/*.html`, `index.html`, `oyuncular.html`, `data/oyuncular.json` | Both sides rebuilt the same pages: main with the old `build.py` from new daily data, the branch with the new `build.py` from old data | Take either side (the branch's), then run the branch's `build.py` on the merged tree, which regenerates every page from the merged sources |

No conflict in any source file: `source/*.md`, `data/news/*.json`, scripts, workflows,
`build.py`, assets. `data/news/2026-09-23.json` (K4) merged cleanly because main never touched it
after the 23rd. **No conflict needed a decision.**

## Results on the merged tree

- `build.py`: **exit 0**. 14 reports; `haberler/2026-09-23.html` 628 headlines; 24–27 Sep
  pages 541 / 516 / 526 / 391. NOKTALI-İ 0, L1-DOLGU 0, ÇİZGİ-KONTRAST passes.
  The only alert is **KANIT-BOŞLUĞU** (Elbit + Northrop), which is expected until the K6 Drive
  edits on merge day.
- **Rule checks and test suites all green:** DÖRT-DURUM 4/4, KAPSAM-SAYI 64/64, KANIT-BOŞLUĞU
  (all modes), test_uyari 33/33, test_collect 21/21, test_silme_yok 22/22,
  test_ceviri_dedektoru 20/20, test_k6 27/27, scope line with filter.
- **smoke.py: 79 ok, 10 FAIL.** All 10 are explained below. None is a defect in the product.

| Failing smoke check | Cause | Real problem? |
|---|---|---|
| NOKTALI-İ 1440 (browser), NOKTALI-İ broken build, R27 375/1440 (`daybar "23 Eyl"`), (D) `2026-09-24-aday.md` first section, K5 tanı (`2026-09-17` no longer in the 10-day window), GEÇ-GELEN build line (26/27: 0) | The test hard-codes "the newest day is 23 Sep", or expects the local Rev 31 evidence file | No. The tests are pinned to a date. They will fail on every new day after merge until they are made date-agnostic |
| ETİKET-BAŞLIK click (27 Sep) | The page smooth-scrolls, and 27 Sep is a long page. The test checks after 0.4 s, when the heading is still off-screen. It lands in view (top 122px) after about 2 s. The live site today does the same | No. Test timing |
| İPUCU-YOK / S8 line (27 Sep: 53 items categorised by source hint only) | 24–27 Sep were collected by main's **old** collector, so they use the old categories, like 17–22 Sep. From the first post-merge collection, days use the new rules | Not a regression. **Decision:** re-categorise 24–27 Sep as was done for 23 Sep, or leave them like 17–22 |
| İLK-EKRAN normal (27 Sep: 4th item bottom 835 > 812) | The 27 Sep report was written without the K5 length limits (19, 20 and 26 Sep also overflow). With the limits applied, all 10 days pass | Expected until the Instructions paste. The rule only warns and never blocks publishing (`continue-on-error`, and it runs only in `build.yml`, after publication) |

## Merge-day consequences found here

1. **A plain `git merge rev21-33 && git push` will stop** on the 23 conflicts above. Also:
   - Local `main` has diverged from `origin/main`. It holds the baseline commit `322e66c`, which `rev21-33` also contains.
   - The untracked local `data/news/2026-09-24-aday.md` (Rev 31 evidence) would block switching to main.

   → `review/tools/merge_day.sh` handles all three:
   - It works on a detached `origin/main`.
   - It removes the local evidence file.
   - It takes the branch side **only** for generated paths, then rebuilds. On any other conflict it aborts and changes nothing.
   - Tested with `DRY=1`, which does everything except the push: 23 conflicts resolved, build OK, merge commit created, and the repo was returned to its prior state.
2. The rollback has the same problem in reverse: later daily builds rewrite generated pages. → `review/tools/rollback.sh` handles it the same way. It was tested on a simulated merge plus a later day, without a push.
3. smoke.py needs its date-pinned checks made relative to the newest day before it is useful on main. This is a test-tool change only, suggested for after the merge.
