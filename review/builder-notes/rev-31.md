# Rev 31 — builder notes (news that arrives after the briefing · GEÇ-GELEN)

Branch `rev21-33`. Nothing committed or pushed. No workflow triggered. No network fetch,
Claude/translation call or Drive access. No secrets created or read. `worker/` not touched.

## Local-only file: do not commit

- **`data/news/2026-09-24-aday.md`**: the local (D) evidence only. It was produced offline from
  23 Sep data with `python3 scripts/test_collect.py yerel-aday 2026-09-23`. The real 24 Sep file
  will come from the morning pipeline. No `2026-09-24.json` was written to `data/news`.

## What changed

| File | Change |
|---|---|
| `scripts/collect_news.py` | **P0-1:** every item carries `ilk_goruldu`, the run's stamp in Europe/Istanbul ISO format. When the same day is re-collected, the new run is merged into the existing `data/news/<gün>.json`. Existing items are kept exactly as they are: stamp, `title_tr` and summary included, and none are deleted, even when they have dropped out of the feed. Items that are new by URL and title key are appended with this run's stamp. `toplamalar` records each run as `{at, yeni, yeniden}`. **P0-3:** the candidate file opens with `## Dünkü brifingden sonra gelenler (N)`, followed by one explanatory line. That section lists yesterday's items whose stamp is later than yesterday's briefing time in `data/published.json`, each with "ilk görüldü DD.MM HH:MM". It is first in `CANDIDATE_ORDER` and counts toward the 260-item limit, so the limit cannot cut it. When N is 0 the section is omitted (Rev 9). **P1-1 GEÇ-GELEN:** (1) the items on disk are compared with what is about to be written. A changed stamp or a lost item sends `uyari.ekle("GEÇ-GELEN", …)`. (2) After the candidate file is written, its first section is parsed. If any of yesterday's late items is missing, a warning is sent. (3) (A) gets `yeni: n · değişmedi: m · damga değişti: k`, plus the BRİFİNGDEN SONRA count for today and yesterday and "ilk bölümde x/N". **Offline path:** `--fixture F.json --out DIR [--date --now --published]`, where `--out` is required so nothing is written into `data/news`. `--sinama-damga-boz` works only with `--fixture`. `feedparser`, `requests` and `google-auth` are now imported lazily, so the fixture path runs on plain python. The real run's CLI (`--hours`, `--dry-run`) is unchanged. |
| `scripts/test_collect.py` | new, stdlib only, 21 checks. It collects 24 Sep twice (05:19 and 11:04; the second run drops one feed item and adds one new one). It checks: the count lines; existing items byte-identical, including a simulated `title_tr`; the dropped item kept; the new item's stamp; the first section holding the AA item and the 11:04 item but not the 05:19 items; the 260 limit leaving the first section whole; a missing late item being detected; a deliberately broken stamp producing GEÇ-GELEN; flag misuse rejected; `data/news` untouched. Each run is a separate process with its own `RUNNER_TEMP` and summary file, and with a `PYTHONPATH` that makes importing `requests`, `feedparser` or `google` fail. Subcommands: `hazirla DIR` (fixtures for the workflow) and `yerel-aday GÜN`. |
| `.github/workflows/gec-gelen-test.yml` | **new evidence workflow `gec-gelen-test`.** Triggers: `push` to `rev21-33` touching `scripts/collect_news.py`, `scripts/test_collect.py` or the workflow itself, plus `workflow_dispatch`. Permissions `issues: write, contents: read`. No secrets (`GITHUB_TOKEN` only). Uses `UYARI_TEST_ONEK: "[TEST] "`. Job **iki-toplama**: local test, two collections, first section appended to (A), flush with "uyarı yok". Job **damga-bozuk** (`needs:`): two collections, the second with `--sinama-damga-boz`, then the flush → GEÇ-GELEN line in the `[TEST]` issue (I). |
| `build.py` | `BRIEF_AT` / `brief_moment()` / `brifingden_sonra()`. A medya takibi row whose `ilk_goruldu` is later than that day's briefing publish time gets `<span class="clip-late">Brifingden sonra</span>`. It sits in the same slot as BRİFİNGDE, as an `elif`, so the two never appear together. No token on days with no briefing or items with no stamp. The build log per-day line gets "· N brifingden sonra", and `GEÇ-GELEN: BRİFİNGDEN SONRA jetonlu satır · <dün>: n · <bugün>: n` goes to the log and to (A). |
| `assets/app.css` | `.clip-late { color: var(--muted); }`. It inherits mono and uppercase from `.clip-meta`, and `lang="tr"` renders it as BRİFİNGDEN SONRA. No new colour; BRİFİNGDE stays the only coloured meta token. |
| `data/news/2026-09-23.json` | stamps backfilled, see below. |
| `review/tools/smoke.py` | `r31_checks`: test_collect; the build line (23 Sep: 89); Playwright 375px on `?oyuncu=roketsan` (AA row text `BRİFİNGDEN SONRA`, same colour as the meta line, different from BRİFİNGDE, the two never on one row); (D) served over HTTP with AA in the first section, skipped if the local file is absent. |

## 23 Sep backfill

Source: git history. `6fa289a` (2026-09-23 02:19:10Z = **05:19:10 TR**, first collection, 539
items) and `73c7cf9` (08:04:23Z = **11:04:23 TR**, backup cron, 536 items, whose file overwrote
the first). The current file is identical to `73c7cf9` by URL. Of the 536 items, the **447**
that were also in the 05:19 file → `2026-09-23T05:19:10+03:00`; the **89** that first appeared
at 11:04 → `2026-09-23T11:04:23+03:00`. These are commit times, so they are upper bounds on the
collection time, and they are on the correct side of 06:16 either way. `toplamalar` is filled
from the same two commits. No other field changed (JSON round-trip checked).

**AA item** ("ASELSAN ile ROKETSAN arasında 1,2 milyar avroluk sözleşme imzalandı"):
`ilk_goruldu` **2026-09-23T11:04:23+03:00**; 23 Sep briefing `published.json` → **06:16** TR.
It therefore carries BRİFİNGDEN SONRA. The same token appears on 89 items, 90 rows (the AA item
also sits in the Türk savunma sanayii cross-section).

**Finding, not acted on:** 92 items from the 05:19 file (the one the briefing's candidate list
came from) disappeared when 11:04 overwrote it. They are not in today's 536. Under the Rev 31
merge rule they would be kept, and Rev 0 says no item is deleted. I did not restore them: the
brief only asks for the stamp backfill, and restoring them would change the visible count of
the 23 Sep medya page (536 → 628). The orchestrator decides.

## Test results (local, 23 Sep)

- `python3 build.py`: exit 0. `haberler/2026-09-23.html (536 başlık · 13 brifing atıflı · 89 brifingden sonra)`.
- `python3 scripts/test_collect.py`: **21/21 green**. Second run: `yeni: 1 · değişmedi: 5 · damga değişti: 0`.
  Mutation (restoring the old overwrite behaviour) → 3 red checks, with `damga değişti: 4` and a GEÇ-GELEN warning. Reverted.
- Workflow steps simulated locally with `RUNNER_TEMP` and `GITHUB_STEP_SUMMARY`: (A) of iki-toplama shows
  `🟢 yeni: 1 · değişmedi: 5 · damga değişti: 0`, then "2/2" in the first section and "uyarı yok". damga-bozuk shows
  `🔴 yeni: 1 · değişmedi: 4 · damga değişti: 1` and the flush lists
  `GEÇ-GELEN · SINAMA (fixture) — gerçek uyarı değil: … ilk_goruldu damgası değişti …`. It was flushed without a token, so no API call was made. YAML parses.
- (D) local: `2026-09-24-aday.md` first section is `## Dünkü brifingden sonra gelenler (89)`, with the AA row at line 90, 89/89.
- `check_reports.py --dort-durum` 🟢 4/4. `--oyuncular` 🟢. `test_uyari.py` 🟢 33/33.
- `python3 review/tools/smoke.py`: **SMOKE OK**, including `BRİFİNGDEN SONRA jetonu · 375px … AA satırı 'BRİFİNGDEN SONRA' · renk rgb(113,116,122) (meta aynı, BRİFİNGDE rgb(47,76,59)) · ikisi aynı satırda 0`.

## Not done / for the reviewer

- The (A) and (I) evidence requires pushing `rev21-33` so that `gec-gelen-test` runs. That is outside my limits.
- `collect-news.yml` was not changed: its collect step already runs inside a job that flushes to uyari last. Its (A) now carries the Rev 31 section. Delete `gec-gelen-test.yml` before merging to main (it only runs on this branch).
- On a re-collection, an existing item's `also` list is not extended with new outlets, because that would edit an existing item.
- The candidate file itself (`<gün>-aday.md`) is still rewritten by the 11:04 run, but the existing lines are unchanged and new items are added. The brief says nothing about freezing it.
- Old days (before 23 Sep) have no stamps and get no token (unknown ≠ late).
