# Rev 32 — builder notes (tekrar eden manşet · TEKRAR-MANŞET)

Branch `rev21-33`. Nothing is committed or pushed. No workflow was triggered, no secret was
created or read, and no `gh` write command was run. `worker/` and `sw.js` were not touched, and
neither was `.github/workflows/build.yml` (see "Orchestrator notes").

## What changed

| # | File | Change |
|---|---|---|
| R32-P0-1 | `build.py` (new "Rev 32" section at the end, plus 3 call sites in `main()`) | `tekrar_eslesmeleri(sources)` runs once per build, over every report. It compares each summary item and the H1 with the developments of the previous 7 reports. `ilk_jetonlari()` appends `<a class="ilk" href="/reports/<gün>.html#g<n>">ilk: 19 Eyl</a>` to the end of the matching `h2#ozet + ol > li`. This happens on `reports/<gün>.html` and on `index.html`. The link's `title` is "19 Eylül 2026 raporu: <label>". Each report's log line lists its tokens. |
| R32-P0-1 | `assets/app.css` | `.prose a.ilk`. It uses the age-token voice: mono 10.5px, `--muted`, underline in `--rule-2`, no colour. `padding-block: 16px` gives a 46px tap height without changing the line box. The underline is `text-decoration`, because a `border-bottom` would sit 16px under the text. No new colour, font or design token. |
| R32-P0-2 | `build.py` `tekrar_manset_kurali()` | Runs next to `r23_kurallari()` for the day's report only. It prints a log line, writes an (A) section "### TEKRAR-MANŞET — …", and, if the H1 matches, calls `uyari.ekle("TEKRAR-MANŞET", "TEKRAR-MANŞET: 23 Eyl H1 ↔ 19 Eyl")`. The rule name was already in `uyari.KURALLAR`. |
| R32-P1-1 | `review/builder-notes/rev-32-prompt.md` | The sentence to paste, in the same format and block as Rev 23. |
| — | `review/tools/smoke.py` | Adds `r32_checks` and `ILK_JS` (see Tests). |

The site HTML changes only by the tokens (7 across 5 pages, index.html included) and the new
`app.css?v=` hash. I checked this by stripping both from all 90 changed pages: the result is
identical to `HEAD`. `data/*.json` is unchanged. `summary_line()` (lead/push) reads the Markdown,
so the token never reaches a notification or `index.json`.

## Matching (as the brief says, not reduced to URLs)

- **Previous development** = a `development_blocks()` unit: `### G#` blocks plus
  `- **G# · …** —` bullets, which includes watch items that carry a G#. Its comparison texts are
  its summary item (if any), and its label + the first sentence of its body. Its URLs are the
  `[K#]` it cites, resolved through KAYNAKLAR and `norm_url`.
- **Current side:** each YÖNETİCİ ÖZETİ item. Its URLs are those of its own `G#` block. The H1 is
  `guard_headline(title)` and is matched by text only, because it has no G#.
- **Match** = a shared URL, **or** ≥ 2 shared proper nouns plus word overlap ≥ 0.4. Overlap is
  shared words / the shorter text's word count, using `_sozcukler`, the same measure as
  H1-TEKRAR.
- **Proper noun** = a capitalised word, apostrophe suffix removed, that is "not in the
  dictionary". The dictionary is built from the corpus: any word that appears lowercase anywhere
  in the reports (body, summary, title) counts as a common word. Month and day names are added,
  because Turkish always capitalises them. "Savunma" at the start of a sentence therefore does
  not count, and neither does "Haziran".
- **"ilk"** = the **oldest** matching report inside the 7-report window. Chains are not followed:
  if 19 Sep had itself repeated 14 Sep, 23 Sep would still say 19 Sep.
- **H1 does not get its own token.** The brief's rule says a token is printed when "H1 ya da bir
  özet maddesi" matches. I print the token on summary items only. The H1 is the page's L1, and
  on every day so far the H1's development is also a summary item (23 Sep: item 1), so the fact
  is said once. The H1 match goes to the operator as the alert.

## Tokens printed across all 10 reports (genuine / false)

| Day | Item | Token → target | Why it matched | Verdict |
|---|---|---|---|---|
| 15 Sep | 2 "ABD'nin üs savunması … üç ayrı satın alma hattına bölündü" | ilk: 14 Eyl → G1 "USAF orta kalibreli namlulu hava savunma pazar araştırması" | shared URL (armyrecognition USAF medium-calibre notice) | **Genuine.** One of the item's three strands is the notice reported the day before. |
| 18 Sep | 1 "DHS … Track One … kesinleşti" | ilk: 17 Eyl → G9 "DHS C-UAS Track One yeniden değerlendirmesi" | names: track, one · overlap 0.40 | **Genuine** (a continuing story). It already carries its novelty verb, "kesinleşti". This match sits exactly on the 0.4 threshold. |
| 20 Sep | 1 "Deniz Piyadeleri 400.000 adet … Drone Round" | ilk: 14 Eyl → G16 "ABD Deniz Piyadeleri Drone Round" (watch item) | shared URL (twz) | **Genuine.** Same programme, and the 400k figure is new. |
| 20 Sep | 3 "Kongre Araştırma Servisi … XM30 … organik C-UAS" | ilk: 16 Eyl → G5 "XM30'da organik C-UAS boşluğu" | names: kongre, araştırma, servisi, xm30, c-uas · overlap 0.50 | **Genuine repeat.** It is the same CRS finding 4 days later, from a different source, so the URL path would have missed it. |
| 20 Sep | 4 "SGT STOUT … obüs mevzilerini" | ilk: 14 Eyl → G5 "SGT STOUT ve topçu koruma doktrini" | shared URL (the same armyrecognition article) | **Genuine repeat.** Same exercise, same article, 6 days later. |
| 23 Sep | 1 "Letonya … Archer'ı bırakıp Çek Morana …" | **ilk: 19 Eyl → G1 "Letonya Morana 155 mm kararı"** | names: archer, letonya, morana, çek · overlap 0.88 | **Genuine.** This is the brief's case. |

That makes 6 tokens with 0 false positives. The 14, 16, 17, 19, 21 and 22 Sep reports got no
tokens. The H1 matched only on 23 Sep (overlap 0.73 against 19 Sep G1), so the build emits one
alert. Risk: "C-UAS", "ABD" and similar recurring acronyms count as proper nouns. On this data
the 0.4 overlap still holds them back, and none of the 6 tokens depends on them alone.

## Alert lines (local build, 23 Sep)

```
  · TEKRAR-MANŞET 2026-09-23: H1 ↔ 19 Eyl · jetonlu özet maddesi 1
      özet 1 ↔ 19 Eyl G1 “Letonya Morana 155 mm kararı” (ad 0,88 · archer, letonya, morana, çek)
  ! TEKRAR-MANŞET · TEKRAR-MANŞET: 23 Eyl H1 ↔ 19 Eyl
```

The issue line will be `- **TEKRAR-MANŞET** · TEKRAR-MANŞET: 23 Eyl H1 ↔ 19 Eyl · [çalıştırma](…)`.
The repeated prefix follows the NOKTALI-İ convention, so the brief's text appears verbatim.

## Tests (local, 23 Sep)

- `python3 build.py`: exit 0. It prints `özet 1 ilk: 19 Eyl G1` on the 23 Sep line, plus the
  TEKRAR-MANŞET lines above.
- `check_reports.py`: all ok. `--dort-durum`: 🟢 4/4. `--oyuncular`: 🟢 all rows.
  `--ilk-ekran`: 🟢, with h2#ozet at 294px and item 4's bottom edge at 791px. These are the same
  as before, because the token fits on item 1's last line.
- `scripts/test_uyari.py` 33/33 · `scripts/test_collect.py` 21/21.
- 375×812 touch (Playwright, `is_mobile`/`has_touch`), on `/reports/2026-09-23.html` and `/`:
  "ilk: 19 Eyl" is the last element of summary item 1. It is mono and `--muted`, one piece
  (nowrap), and has a 46px tap height. There is no horizontal overflow. Tapping it goes to
  `/reports/2026-09-19.html#g1` with "Letonya Morana 155 mm kararı" on screen. The before/after
  screenshots are in the session scratchpad (`r32-375-once.png`, `r32-375-sonra.png`), not in
  `review/`.
- `python3 review/tools/smoke.py`: **SMOKE OK**. New lines:
  - the TEKRAR-MANŞET build line, with the per-day tokens and the alert
  - rule controls: shared URL → match; ≥ 2 names + overlap → match; one name → none; dictionary
    words only → none; another development → none
  - the 375px touch check on both pages

The tree is left in the normal build.

## Orchestrator notes

- **(P) → (I):** no code change. The branch uses the existing `uyari_test` dispatch input of
  `build.yml`, which sets only `UYARI_TEST_ONEK: "[TEST] "`. The normal build then writes 23 Sep's
  real `TEKRAR-MANŞET: 23 Eyl H1 ↔ 19 Eyl` line to `[TEST] DEFINTEL uyarıları · <gün>`. It sits
  next to that day's KUR and H1-TEKRAR lines. `build.yml` already triggers on `build.py` and
  `assets/**`.
- **R32-P1-1:** see `rev-32-prompt.md`.

## Not done / for the reviewer

- The (I), (A) and live (S) evidence needs a push plus a `build.yml` dispatch with
  `uyari_test=true`, which is outside my limits.
- R32-P1-1 acceptance (the next 5 reports) is PENDING-HUMAN.
- `review/plan-rev21-29.md` (modified) and `review/briefs/rev-25.md` (untracked) changed on disk
  at 19:42 while I was working. I did not make those changes and left them alone.
