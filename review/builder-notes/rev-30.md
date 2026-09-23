# Rev 30 — builder notes (operatör uyarı kanalı: günlük GitHub issue'su)

Branch `rev21-33`, not committed or pushed. No workflow triggered, no secret created or read,
no `gh` write. `worker/` and `sw.js` not touched. The earlier push-channel notes
(`rev-30-push-kanali-iptal.md`) describe cancelled code that is no longer in the tree.

## What changed

| File | Change |
|---|---|
| `scripts/uyari.py` | new, stdlib only. `uyari.ekle(KURAL, metin)`: checks the rule name against the 18 fixed names (`KURALLAR`; unknown name → `ValueError`, so a typo fails locally), collapses the text to one line, prints it to the log (plus a `::warning` annotation on Actions), and appends it to `$RUNNER_TEMP/defintel-uyari.jsonl`. That path is outside the repo tree and shared by all steps in one job. Locally (no `RUNNER_TEMP`) warnings stay in memory. `python3 scripts/uyari.py ekle KURAL METİN` does the same from a shell step. `python3 scripts/uyari.py` flushes once. |
| `scripts/test_uyari.py` | new, stdlib only. Runs a fake GitHub REST server on 127.0.0.1 and starts `uyari.py` as a separate process per step, the way a workflow does. 28 checks, exit 1 = red, and a 🟢/🔴 line goes to `$GITHUB_STEP_SUMMARY` when it runs in CI. |
| `build.yml`, `collect-news.yml`, `pull-drive.yml` | `issues: write` added next to `contents: write`, plus a new last step `Operatör uyarıları` (`if: always()`, `GITHUB_TOKEN: ${{ github.token }}`, `python3 scripts/uyari.py`). Nothing else changed. |
| `uyari-test.yml` | replaced with the evidence workflow. Triggers: push to `rev21-33` touching `scripts/uyari.py` or this file, plus `workflow_dispatch`. Uses `UYARI_TEST_ONEK: "[TEST] "`, permissions `issues: write, contents: read`, and no secrets besides `GITHUB_TOKEN`. It runs three jobs in sequence (`needs:`): **uyarili** runs the local test, then adds KUR + H1-TEKRAR and flushes. **ayni-gun-tekrar** adds the same KUR text plus a new TEKRAR-MANŞET and flushes. **uyarisiz** only flushes. Every warning text starts with "SINAMA (uyari-test) — gerçek uyarı değil". |
| `review/tools/smoke.py` | also runs `scripts/test_uyari.py`. |

Not changed: `build.py` and the other `scripts/*.py`. Existing unnamed warnings (for example
`HEADLINE_WARNINGS`) were left alone. Each later revision adds its own `uyari.ekle("…", "…")`
call, via `from scripts import uyari` in build.py or `import uyari` in `scripts/`. Both import
forms were checked.

## How the flush works

- **No warnings:** zero API calls. (A) says "uyarı yok" and prints
  `🟢 OPERATÖR-YALNIZ: issue — · +0 satır · okuyucu push 0`.
- **Gate:** it writes to GitHub only when `GITHUB_REF == refs/heads/main` or when
  `UYARI_TEST_ONEK` is set. The prefix goes in front of the title. On any other branch, (A)
  lists the warnings and says no issue was opened.
- **Finding today's issue:** it looks for an exact title match on
  `DEFINTEL uyarıları · YYYY-MM-DD`, using the Europe/Istanbul day (fixed UTC+3 fallback). It
  searches `GET /issues?state=all&since=<now-2d>` (up to 5 pages), not the search API, because
  the search index lags. Two jobs a minute apart have to find the same issue.
- **Opening a new issue:** the body has one line per warning:
  `- **KURAL** · metin · [çalıştırma](GITHUB_SERVER_URL/REPO/actions/runs/RUN_ID)`. The issue is
  assigned to `yazararme` and labelled `uyari`. The label is created if it is missing. If that
  fails, the issue opens without the label. If the POST returns 422, it retries without the
  label, then without the assignee, and logs a warning. No comment is posted when the issue is
  created, because the assignment itself sends the notification.
- **Updating an existing issue:** it reads `(KURAL, metin)` pairs back from the body and appends
  only the new pairs. If any line was added, it reopens a closed issue and posts one comment,
  `+N uyarı · <GITHUB_WORKFLOW>`. If nothing is new, it does not touch the issue.
- **(A) section:** lists the warnings, then
  `🟢 OPERATÖR-YALNIZ: [issue #N](url) · +K satır · okuyucu push 0`.
- **Errors:** any API or network error becomes a `::error::` log line and a
  `🔴 OPERATÖR-YALNIZ: issue yazılamadı (…)` line in (A). The flush always exits 0, and the
  temp file is removed after the flush.
- **OPERATÖR-YALNIZ:** the module has no code path to `/notify` or to any file in the repo. It
  only writes to `RUNNER_TEMP`, the log, `GITHUB_STEP_SUMMARY` and the GitHub API.

## Test results (local, 23 Sep)

- `python3 scripts/test_uyari.py`: **28/28 green**.
  `🟢 OPERATÖR-YALNIZ testi: 28/28 kontrol · issue 1 · tekrar satırı 0 · uyarısız çalıştırmada API 0 · okuyucu push 0`.
  Scenarios covered:
  1. A run with warnings: 1 issue, title, assignee, label, 2 lines with run links, no comment.
  2. A same-day rerun with one repeat and one new warning: still 1 issue, +1 line, KUR appears
     once, exactly one comment `+1 uyarı · pull-drive`.
  3. 2b: an all-repeat run adds 0 lines and 0 comments.
  4. A run with no warnings: **0 API calls**, and (A) says "uyarı yok".
  5. Non-main branch: 0 API calls.
  6. `[TEST]` prefix: a separate issue.
  7. A closed issue is reopened.
  8. API 500: exit 0 and a red line in (A).
  9. An unknown rule name is rejected.
  10. No `/notify` calls, and no warning text in `data/*.json`.
- Mutation checks, both reverted afterwards:
  - Removing the same-day dedupe turns 5 checks red (`tekrar satırı 1`).
  - Letting the no-warning path call the API turns it red (`API 1`).
- `python3 build.py`: exit 0, and the tracked output is unchanged.
- `python3 review/tools/smoke.py`: **SMOKE OK**, including the new test line.
- All workflow YAML files parse (checked with PyYAML).

## Not done / for the reviewer

- The (I) and (A) evidence needs `uyari-test.yml` to run on GitHub. That means pushing
  `rev21-33`, which is outside my limits. Once pushed, the run should produce one
  `[TEST] DEFINTEL uyarıları · <gün>` issue with 3 lines and 1 comment `+1 uyarı · uyari-test`.
  The third job's (A) should say "uyarı yok". All three jobs share one run ID, so every line
  links to the same run.
- Two workflows on `main` that flush in the same second could both miss the issue and open two
  (there is no lock). This is rare: `pull-drive` and `collect-news` share `concurrency: publish`,
  and `build.yml` does not.
- `uyari-test.yml` should be deleted, or left dormant, before `rev21-33` is merged. It only
  triggers on that branch.

## Follow-up: Markdown escaping in issue lines

- Problem: a line with two `$` signs (e.g. "1,5 milyar $ ↔ … $'i") was rendered by GitHub as
  LaTeX math. `*`, `_`, `` ` ``, `<`, `[`, `]`, `|`, `~` and `#` could also break a line.
- Fix in `scripts/uyari.py`: `kacir()` escapes only the free text of each line; the bold rule
  name and the run link are unchanged. It is applied to the issue body, the comment's workflow
  name and the (A) summary. `$` becomes `<span>$</span>`, which is what GitHub's "Writing
  mathematical expressions" page documents for a literal `$` outside math (that page gives `\$`
  only for use inside math). The other characters get a CommonMark backslash escape.
- Dedupe: `mevcut_anahtarlar()` stores each existing line both as written and as un-escaped
  with `coz()`. Escaped lines are recognised as repeats, and so are lines from today's issue
  that were written before this fix without escaping.
- Tests: 9 (two `$`, and `*`/`_`/etc., in both the issue and (A), with a rerun that adds +0) and
  10 (an old unescaped line already in the issue gives +0 lines and no comment). Result: 33/33.
  Turning off escaping makes 2 checks fail. Smoke OK.
