# Reconciliation — blind review vs builder's audit

Written after `review/blind.md`. Inputs: `audit/findings.md`, `audit/content.md` and
`DECISIONS.md`, all read only after blind.md was done.

Marks: **Confirmed**: I saw it too, or checked it now. **Disputed**: evidence below.
**Missed by me**: real, and I didn't find it in my pass. **Unverified**: I didn't test it
and can't vouch for it.

## A. `audit/findings.md`

| # | Mark | Note |
|---|---|---|
| F-01 network error shown as "kayıt yok" | Missed by me · Unverified | I didn't test the archive search. If it reproduces it is correctly P0: a pipeline fault stated as a fact about the world. |
| F-02 zero-result search shows a blank page | Missed by me · Unverified | Root-cause reasoning (`sectionParts()` walks past the last h2) is specific and plausible. |
| F-03 notify offer invisible on first visit, bell at 99% depth | Missed by me · Unverified | The audit says itself that Rev 7 settled *which surfaces*. The depth measurement is new evidence, so reopening is legitimate. |
| F-04 tracked rival's own source down, reader not told | Missed by me | The strongest finding in the audit. It is PRODUCT.md's belief-changing-failure exception, live today. Already listed in DECISIONS › Open. |
| F-05 "yanıt vermedi" column | Confirmed as a tension, not a new defect | Rev 19 chose "shown faded, not dropped". DECISIONS › Open already plans to drop the column. Treat it as that open item, not as a P2 bug. |
| F-06 scope line doesn't recount under filter | **Confirmed** | Seen with `?oyuncu=roketsan`: 1 story on screen, header still "536 başlık · 50 kaynak". Breaks the settled law "a number above a filtered list must recount". |
| F-07 briefing never names itself | Missed by me · weak | True, but its counterpart says "← BRİFİNG" and the archive card says "Brifing →". Low. |
| F-08 daybar chip has no count | Confirmed | Rev 1 put the count on the archive chip. The daybar chip was never specified, and the 88px sticky budget at 375px (Rev 0) limits it. Check the width before adding it. |
| F-09 no way back from thread to the day | **Confirmed** | The thread header has only the wordmark. Same as my #7. |
| F-10 thread count ≠ rows shown | **Confirmed** | Also on the XM30 thread: "4 hareket", 5 rows. |
| F-11 two desktop content widths | Confirmed | The thread and roster pages are visibly narrower than the briefing. |
| F-12 rules far below 3:1 | Confirmed | I measured a border colour of `rgb(202,198,188)` on `rgb(252,251,249)`, about 1.6:1. It matters because PRODUCT.md makes the rule *the* level-2 mechanism. |
| F-13 dark theme has no user path; CSS hook is dead | **Disputed (framing)** | The fact is right: `app.css:30` has only `:root:not([data-theme="light"])`. But Rev 0 says **NOT: a theme switch**, so "no user path" is the settled design, not a defect. The dead `:not()` guard is harmless cruft. Delete it or leave it. It is not P2. |
| F-14 notify card covers footer bell | Missed by me · Unverified | |
| F-15 64% of executive's first screen before content | **Confirmed** | My numbers are the same (summary heading at ~470px). This is my #3. |
| F-16 no loading state in archive search | Missed by me · Unverified | |
| F-17 unsegmented peers vanish under segment chips | Confirmed | Havelsan and FNSS show no segment on `/oyuncular.html`. Already in DECISIONS › Open. |

**"Verified working" list, two disputes:**

- **"Oyuncular sayfası üst satırı ray ile tutarlı: Bugün 9" — disputed.** The two numbers
  agree with each other, but the number itself is wrong. Word-boundary matching of
  `data/rakipler.json` names against today's 536 sweep rows finds tracked players that are
  **not** counted: Thales 4, PGZ 3, Northrop Grumman 3, Anduril 2, KNDS 1, Hanwha 1,
  Rafael 1, IAI 1, Munitions India 1. That is about 9 more (my match includes summaries, so
  a few may be passing mentions). PRODUCT.md says so directly: *"If the matcher covers
  only some players, the number is not incomplete — it is wrong."* The audit certified a
  number that the product's own core rule says must not be published. DECISIONS › Open
  lists the matcher gap. The audit should have listed "Bugün 9" as a live P1, not a pass.
- **"İş 2: iplik sayfası … zaman çizgisiyle gösteriyor" — disputed.** The timeline exists, but job 2
  is "what became of it". The thread page never states the current state ("Prototip teslim
  edildi, şart hâlâ tanımlı değil" lives only in the day's watch list). Its rows are links
  styled as plain text.

## B. `audit/content.md`

| Section | Mark | Note |
|---|---|---|
| §0 Genel = 73%, 81% hit no rule | **Confirmed** | I saw 392/536 in Genel. |
| §0 / **S1 turn `looks_defence()` on by default** | **Flag: re-opens a settled NOT** | Rev 0: *"NOT: filtering the Genel bucket with a keyword dictionary — tautological; … dropped good items."* S1 applies the same mechanism one layer earlier. The audit measures what the filter removes (328 items) but never what it **wrongly** removes, and false drops were the reason for the original NOT. It isn't new evidence until someone samples the 328 for defence items. Per the analyst's contract (Rev 0 "no item is ever deleted"), dropping at ingest is also a deletion. |
| §1 case-style violations 16.4%, two prompt rules conflict | Confirmed (partly) | I saw English-style Title Case on Turkish headlines. The rule conflict (Ö4) needs a decision, and it is a prompt decision. |
| §2 translation, 40 items, 40% defective, silent clause deletion | Unverified | n=40, one per source. The clause-deletion class (Ö1/Ö2) is the one worth acting on regardless of rate. |
| §4 named categories 10–22% precise; C-UAS full of consumer drone press | Unverified, consistent | I saw Unmanned Airspace items rank at the top of Öne çıkanlar. |
| S2 drop `SOURCE_HINTS` · S3 split drone words · S6 narrow contract words | No conflict with DECISIONS | These change classification only. Nothing is deleted. |
| S5 who "Rakip Duyuruları" is for | Agree | It's a product question, and it's the same one as the Turkish-peer item in DECISIONS › Open. |

## C. What the builder missed

In rough order of consequence:

1. **SAN CUAS has two values, and the briefing's is probably the wrong one.** The briefing says
   "yaklaşık 1,5 milyar $ (16 milyar NOK)". Two sweep summaries of the same story
   (`data/news/2026-09-23.json:1179`, `…:1408` context) say NOK 16 bn ≈ **1,74 milyar $**.
   The agent did its own currency conversion, which breaks the settled law "the agent
   produces judgement; the build counts and derives".
2. **Development headings ignore `developments[].label`.** Rev 11 made the label *the single
   source of truth*. `source/2026-09-23.md:9` has G9 = "Lynx XM30 prototip teslimi",
   G3 = "Leonardo–Alkeon 76 mm Danimarka üretimi", G8 = "Hensoldt KENIS bağımsız sensör". The
   rendered headings use the agent's bold lead-ins instead ("American Rheinmetall",
   "Leonardo / Alkeon", "Hensoldt"). So a watch-list link reading "Lynx XM30 prototip
   teslimi" lands on a heading that says "American Rheinmetall". This defect breaks a settled
   decision. Fixing it needs no new decision.
3. **"Bugün 9" is wrong, not incomplete** (see A). The audit listed it as verified.
4. **Today's Aselsan–Roketsan €1.2 bn contract is absent from the briefing** while both
   names sit in its Oyuncular rail. This is live evidence for the Turkish-peer item in DECISIONS › Open. I'm not
   overriding that item, only adding a data point: when the agent leaves Turkish peers out,
   the rail still advertises them.
5. **H1 repeats summary item 1** almost word for word. That breaks "say it once" in the first
   300px. Not addressed by any decision.
6. **Thread pages carry no current state** (see A). Slugs are also truncated mid-word or carry
   report dates (`…-mut.html`, `…-g4.html`, `…-18-09-2026-raporu.html`). They are
   permanent URLs.
7. **Type scale sprawl.** `app.css` declares about 20 distinct font sizes (10–34px, with
   half-pixel steps such as 10.5/11/11.5 and 15/15.5/16/16.5). PRODUCT.md promises "no new
   token without deleting one". Sizes aren't tokenised at all, so that promise isn't enforced
   for type.
8. **Summary item 2 drops the actor** ("sipariş verildi"). The body names Kongsberg and
   Advanced Navigation. An executive can't tell who won.
9. **Mobile cards drop the "İzlenecek gösterge" label.** The third field is unlabelled grey
   text.
10. **The docs contradict each other.** PRODUCT.md: boundary gets a rule, state gets
    colour, content gets size, *"never two of them"*. Rev 0: L1 = *"fill + border"*, and
    the summary box is fill + 3px border. Both are "settled". Decide which one governs so the next reviewer
    doesn't flag it again.

## D. Blind-review items withdrawn after reading DECISIONS.md

- *FIRSAT/RİSK look the same; sort rows by severity* → Rev 16 settled "Etki is text,
  never colour; rows sorted by g-id". I have no new evidence, so withdrawn. The unlabelled mobile field
  (C9) stands.
- *Summary box uses rule + fill* → Rev 0 settled it. Only the doc contradiction (C10) stands.
- *Duplicate row under player filter* → Rev 0 and Rev 17 accept cross-section duplication.
  Withdrawn.
- *Rail links go to two kinds of destination* → Rev 17 and Rev 20 designed it. Withdrawn.
  The landing-doesn't-name-the-player part stays, and it is the same issue DECISIONS › Open
  describes for Korkut/Şahin.
- *Relative source ages go stale* → Rev 13 computes them at build against the report date.
  Withdrawn.

## Revised scores (after audit)

Unchanged apart from **core rule 6 → 5**, because of "Bugün 9" plus the agent-computed
currency figure. Overall about 5/10.
