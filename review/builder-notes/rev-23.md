# Rev 23: builder notes (one fact, one name, one value)

Branch `rev21-33`. Nothing is committed or pushed. No workflow was triggered, no secret was
read, no `gh` write was made, and `worker/` was not touched. Drive and `task-prompt.md` were
not read. The tree is left built in the normal state (alias testi 64/64).

## What changed

| # | File | Change |
|---|---|---|
| R23-P0-1 | `enrich.py` `add_heading_anchors(text, dev_labels)` | Every development heading (`<h3 id="gN">`) is now the frontmatter `label`. This covers `### GN · …` headings and rival items folded in from `**GN · …**`. The bold lead-in the agent wrote (for example "American Rheinmetall") is no longer printed. The agent keeps its markers and `enrich` strips them at render, the same approach as Rev 11. Labels are escaped with `quote=False`, so apostrophes stay as they are. If a label is missing, the agent's text is kept, and ETİKET-BAŞLIK alerts. |
| R23-P1-1 | `build.py` (new section at the end, "Rev 23") | `etiket_baslik()`, `kur_denetimi()`, `h1_tekrar()` and `r23_kurallari()`. They run once per build, **only on the day's report** (`sources[-1]`), right before `index.html` is written. They send alerts through `uyari.ekle(...)` and never stop the build. Why only the latest day: the build rebuilds the whole archive, so old days would put the same alerts into the issue every morning. The log line is `· R23 <gün>: ETİKET-BAŞLIK n · KUR n · H1-TEKRAR n`. |
| orchestrator | `.github/workflows/build.yml` | New dispatch input **`uyari_test`** (boolean, default false). It only adds `|| inputs.uyari_test == true` to the `UYARI_TEST_ONEK` expression. The build is not broken. `boz` and `kapsam_boz` are unchanged. `enrich.py` is added to the push `paths`: before this, a change to `enrich.py` did not trigger a build. All 5 workflow YAML files parse. |
| R23-P0-2 | `review/builder-notes/rev-23-prompt.md` | The three sentences, ready to paste, and where to put them. |
| n/a | `review/tools/smoke.py` | New Rev 23 checks, listed below. |

## The rules

- **ETİKET-BAŞLIK** checks two things in the rendered HTML:
  - each `h3#gN` (with the copy button removed) must equal its label, and a missing label is
    reported;
  - each `li.watch-move` "→ bugün:" link text must equal the text where it lands. That is the
    `h3#gN`, or for watch-list items the `li#gN > strong.ganchor`.

  Checked against a bad case: removing G9's label gives `G9 başlığı “American Rheinmetall” — frontmatter'da label yok`, and changing the link text gives `→ bugün: “Lynx XM30” ≠ indiği başlık …`.
- **KUR** splits the body (text before KAYNAKLAR) into lines. It looks for
  `TUTAR['ek] (TUTAR)` where the two amounts are in different currencies. The build does no
  currency conversion; it only parses and compares numbers (Turkish decimal comma, magnitudes
  bin/milyon/milyar). The `[K#]` set is the `[K#]` in the line, plus the `[K#]` of any
  development `GN` the line mentions. Each `[K#]` is mapped to its URL (from KAYNAKLAR) and
  then to `summary_tr` (all `data/news` days plus `summaries.json`). It alerts in two cases:
  - (a) no single cited summary contains both values;
  - (b) a cited summary gives a **different value in the same currency** at the same scale
    (×0.5–×2), meaning the sources disagree and the page prints only one value.
- **H1-TEKRAR** compares the H1 (the title after `guard_headline`) with each YÖNETİCİ ÖZETİ
  item. Words are folded with `tr_fold`, apostrophe suffixes are dropped (Archer'ı → archer),
  and `G#`/`[K#]` and a small stopword list are removed. Overlap = shared words / word count
  of the shorter text. It alerts at ≥ 0.6.

## Alert lines from the 23 Sep build (local)

```
! KUR · 2026-09-23 · SAN CUAS 1,5 milyar $ ↔ özet 1,74 milyar dolar [K2] · gövde “1,5 milyar $'lık (16 milyar NOK)” · atıflı özetler çelişiyor; 1,5 milyar $'i destekleyen: [K3]
! H1-TEKRAR · 2026-09-23 · özet 1 · örtüşme 0,73 · H1 “Letonya araç üstü 155 mm obüste Archer'ı bırakıp Çek Morana'yı seçti” ↔ “Letonya, Haziran 2025'te 18 adet için niyet mektubu imzaladığı İsveç Archer'ı bırakıp Çek …”
· R23 2026-09-23: ETİKET-BAŞLIK 0 · KUR 1 · H1-TEKRAR 1
```

A simulated CI run (`RUNNER_TEMP`, `GITHUB_STEP_SUMMARY`, `UYARI_TEST_ONEK="[TEST] "`, no
token) lists both lines under "Operatör uyarıları" in (A). No API call was made.

## For the reviewer: the KUR diagnosis does not match the data exactly

R23.0 §2 says the agent converted the currency itself. The data shows something different:
- `[K3]` (defence-blog) has this summary: *"yaklaşık 1,5 milyar dolarlık (16 milyar NOK)"*.
  That is the agent's value, word for word.
- `[K2]` (unmannedairspace) says *"yaklaşık 1,74 milyar dolarlık"*.
- The `data/news/2026-09-23.json:1179` line the brief cites is from defence-industry.eu, which
  the report does not cite.

So the literal KUR rule ("both values do not appear in the same [K#] summary") would **not
fire** on 23 Sep, because K3 supports both values. The expected alert
"SAN CUAS 1,5 milyar $ ↔ özet 1,74" comes from branch (b) instead: the cited summaries disagree
(1.5 vs 1.74) and the page shows one value. I think this is the "one fact, one value" problem
the revision is aimed at, but the rule is now broader than the brief's wording. If the
orchestrator wants only the literal rule, delete branch (b) (the `baska` list). The 23 Sep
KUR alert then goes away.

## Other observations

- Dry run on all 10 days: ETİKET-BAŞLIK and KUR are clean on every day except 23 Sep (KUR).
  H1-TEKRAR would have fired on 15, 18, 20, 21, 22 and 23 Sep, with overlap from 0.73 to 1.00.
  This is a repeating pattern, and the prompt sentence addresses it.
- The label change also renames headings in older reports, for example 14 Sep
  "Rheinmetall" → "Rheinmetall 155 mm mühimmat siparişi" and "Kongsberg" → "Kongsberg
  PROTECTOR radar entegrasyonu". `reports/*.html` and `index.html` differ only in `h3` text.
- The Oyuncular rail still links **Rheinmetall → G9**. Matching reads the agent's markdown
  heading (Rev 17: role and matching are data, not render). G9's rendered heading and body no
  longer contain the name "Rheinmetall". This is left as is and not changed in this revision.
- An agent-written sentence can lose its subject. For example, G9's body starts
  "ABD Ordusu'na … teslim ettiğini duyurdu" and the subject was the bold lead-in. The prompt's
  subject sentence covers summary items only.

## Test results (local, 23 Sep)

- `python3 build.py`: exit 0, with the two alert lines above and ETİKET-BAŞLIK 0.
- `check_reports.py --dort-durum`: 4/4 green. `--oyuncular`: 6/6 🟢. Structural check: 10 ok.
- `scripts/test_uyari.py`: 28/28.
- `review/tools/smoke.py`: **SMOKE OK**. New lines:
  - R23 alerts: the 23 Sep KUR/H1-TEKRAR lines are present and there is no ETİKET-BAŞLIK
    alert.
  - ETİKET-BAŞLIK: `reports/2026-09-23.html` and `index.html`, 9 headings = label.
  - Rule controls on synthetic input:
    - KUR is silent when both values are in one summary;
    - it fires when one value is missing;
    - it fires when summaries disagree;
    - H1-TEKRAR is silent when there is no overlap and fires when there is.
  - At 1440px, clicking "→ bugün: Lynx XM30 prototip teslimi" goes to `#g9`, and the heading
    "Lynx XM30 prototip teslimi" is visible.

## Not done

- (I) and (A) evidence in CI needs a push and a `build.yml` dispatch with `uyari_test=true` on
  `rev21-33`. That is outside my limits. That run also commits and pushes the normal build to
  the branch, as any non-broken dispatch does.
- The live (S) 1440 screenshot needs deployment. Locally, the smoke check covers the
  click-through.
- The "next 3 reports" check for R23-P0-2 is PENDING-HUMAN.
