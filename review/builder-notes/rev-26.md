# Rev 26 — builder notes (çeviri: cümle düzeni ve üç dedektör)

Branch `rev21-33`. Nothing was committed or pushed, no workflow was triggered, and no `gh` write
was made. **No model was called:** no `claude -p` and no API. No Drive, no secrets, `worker/` not
touched. **No translation in `data/news/*.json` was changed.** The test checks this by hashing
every file in `data/news` before and after it runs.

## What changed

| File | Change |
|---|---|
| `scripts/translate_news.py` | **Prompt:** the title-case rule is replaced with sentence case, so it no longer conflicts with "Türkçeyse aynen ver". **Ö1** added: no independent clause may be dropped, and a long headline is not shortened. **Ö2** added: attribution is kept and the speaker is not narrowed ("İran ordusu", not "İran:"). **Ö3** glossary entries added: Hürmüz Boğazı, Kızıldeniz, Süveyş, Bab-ül Mendep, Avam/Lordlar Kamarası, Pentagon, Beyaz Saray, naaş, şehit, tabut töreni, sevkiyat, transit, boru hattı kapasitesi. **ÇEVİRİ-DEDEKTÖRÜ:** `denetle(ozgun, tr)` runs the three checks (details below). `cevir(pending, cache, batch, cagir=…)` handles the flow: translate a batch, test each item, retranslate flagged items **once** in a single call per batch using `YENIDEN_PROMPT` (the same rules plus a note), then write the result. If the second attempt is still flagged, the cache gets the **original title**, so no `title_tr` is written and the page prints the original. If the second attempt returns nothing, nothing is cached: today the original prints and tomorrow's run tries again. `bitir()` writes the (A) table (per-check counts for the first pass and the retry) and calls `uyari.ekle("ÇEVİRİ-DEDEKTÖRÜ", …)` when more than 10 items were left in the original. The model call is injectable (`cagir`). New CLI flags, mirroring collect_news `--fixture/--out`: `--sahte-cevirmen FILE` takes a JSON map `{original: [first, retry]}` and makes no model call, and `--news-dir DIR`. Defaults and existing flags (`--date/--batch/--limit/--refresh`) are unchanged. |
| `scripts/test_ceviri_dedektoru.py` | new, stdlib only. Runs the fixed test and the flow test, 20 checks; exit 1 = red. `sabit` runs the fixed test only. `hazirla DIR` builds a fake day for the workflow. |
| `.github/workflows/ceviri-dedektoru-test.yml` | new evidence workflow (details below). |
| `.github/workflows/collect-news.yml` | one step added before translation: `test_ceviri_dedektoru.py sabit \|\| echo`. It is offline, uses the same `if:` as translation, and cannot fail the job. Inputs and the other steps are unchanged. |
| `review/tools/smoke.py` | `r26_checks`: runs the test, checks the prompt markers, and checks that the workflow has no secret, no Claude CLI and no `--refresh`. |

### The three checks (`denetle`)
- **düzen:** more than 60% of the non-exempt words start with a capital. Not counted: the first word, exempt words (ve/ile/için/de/da/ki/mi…/veya/ya/ama/ancak/gibi), acronyms and words with digits or inner capitals (NATO, F-35A, WiSENT), and proper nouns that appear capitalised in the original. At least 3 words must be counted.
- **uzunluk:** `len(tr) < len(original) × 0.6`, counted in characters after whitespace is collapsed.
- **atıf:** the original contains `says|said|according to` and the translation has no attribution marker. I went beyond the brief's `dedi/göre/:` and also accept diyor, söyledi, açıkladı, bildirdi, belirtti and iddia. Without these, a correct "…düşürdüğünü söyledi" would be retried every day.
- A translation identical to the original is not checked, because nothing was translated (Turkish source, or the model returned the original).

## Fixed test: the 16 defective items, run offline on today's translations

`audit/content.md` §2 names only **12 of the 16**: 8 are named in the text, plus "cümle düzenindeki 7 başlığın 7'si", with 3 overlapping. The per-item verdicts are not in the repo. The items and today's translations come from `audit/ceviri-ornegi.json`, the 40-item sample behind §2, and the test re-derives the 8 named + 7 sentence-case items from it. The other 4 defects are somewhere in the remaining 28-item pool. So the test reports a **guaranteed lower bound**: it assumes the 4 unknowns are the pool items no check catches. It also reports an expected value.

| check | caught of the 12 identified | fires in the 28-item pool | guaranteed of 16 |
|---|---|---|---|
| düzen | 4 (Care, Iran's military, Commons, 유해) | 26/28 | ≥6 |
| uzunluk | 0 | 0/28 | 0 |
| atıf | 2 (wheeling auction, UK MoD) | 0/28 | 2 |
| **any** | **6** | 26/28 | **≥8/16** (expected ≈9.7) — threshold 7 ✔ |

What the numbers mean:
- **düzen** fires on almost every item in the pool, because today's data was produced under the title-case prompt. Under R26 every title-case output is a defect flag, so this is by design, but it is not a semantic signal.
- The 7 items that are already sentence case, including KF-21 and Hormuç, **are not caught by any check.** Ö5 has been reversed, and none of the three checks can detect a wrong term or an active/passive swap.
- **uzunluk** misses wheeling auction narrowly: the ratio is 0.61 against a 0.60 threshold. **atıf** catches it instead.
- "Iran's military → İran:" passes atıf because of the colon (the colon marker comes from the brief). It is caught only by düzen.

## How retry/fallback is tested without a model

`cevir(..., cagir=Sahte(...))`: during the test, the real `claude` is replaced with a function that raises. The test checks:
- a clean item takes 1 call;
- wheeling auction trips atıf, and the fake retry, which contains "çekil", gets written;
- UK MoD fails twice, so the cache holds the original;
- when no retry comes back, nothing is cached;
- a Turkish source is not checked;
- exactly 2 calls are made in total (the retry contains only the 3 flagged items);
- a clean batch makes no retry call.

The CLI is also run as a subprocess with `--sahte-cevirmen`, with a `claude` on PATH that leaves a marker file if anyone calls it:
- 11 left in the original → one ÇEVİRİ-DEDEKTÖRÜ alert, the (A) table is present, and no `title_tr` is written;
- exactly 10 → no alert;
- no marker file → the real claude was never called.

Mutation checks were run and then reverted. Raising the düzen threshold to 1.0 → red, lower bound 2/16. Raising the alert threshold to 11 → red. Caching the flagged retry instead of the original → red.

## Where (A) comes from
- **`ceviri-dedektoru-test`** (`.github/workflows/ceviri-dedektoru-test.yml`). Trigger: a push to `rev21-33` that touches `translate_news.py`, the test, or the workflow, or `workflow_dispatch`. Permissions are `issues: write`, `contents: read`, and `UYARI_TEST_ONEK: "[TEST] "`. There are no secrets and no Claude CLI. The job runs three steps and then flushes: the local test (writes the fixed-test table and `🟢 … en az 8/16`), `hazirla`, and a fake day. The fake day puts the 40 sample items through `translate_news.py --sahte-cevirmen`, using today's translation for both passes except wheeling, which becomes "çekil". That writes the daily table (düzen 30/30 · uzunluk 0/0 · atıf 2/1 · fixed 1 · original 31) and raises an alert, so a ÇEVİRİ-DEDEKTÖRÜ line appears in the `[TEST]` issue.
- **`collect-news`** (daily cron and dispatch): the `sabit` line plus `translate_news.py`'s own table for the real day.

## Skipped (per the orchestrator note) — for "Açık"
- R26-P1-2: the live window is not retranslated.
- The second half of R26-P0-2: the real retranslation of "…exiting power procurement". The "çekil" text in the test and workflow is **fake**, not model output.
- The (S) views for R26-P0-1 and R26-P1-1: the page does not change until the data is retranslated. Once the data is retranslated, run `translate_news.py --refresh --date 2026-09-23/24`. That uses the model and needs the customer's decision.
- R26-P1-3: the `dil` fix in Drive `kaynaklar.json` belongs to the customer (human-checks).
- P2 and P3 (Ö6 in full, Ö7).
- The daily "original left" count is per run. If the same day is translated twice, the counts are not added together.

## Test results (local, 23 Sep)
- `python3 scripts/test_ceviri_dedektoru.py`: **20/20 🟢**, fixed test ≥8/16, 0 model calls.
- `python3 build.py`: exit 0.
- `check_reports.py` (plain, `--dort-durum`, `--oyuncular`, `--ilk-ekran`, `--kanit-boslugu`): all exit 0.
- `test_uyari.py`, `test_collect.py`, `test_silme_yok.py`: all exit 0.
- `python3 review/tools/smoke.py`: **SMOKE OK**.
- All workflow YAML files parse.
- The tree is left normally built: no tracked output changed.
