# DEFINTEL — settled decisions

Appendix to [PRODUCT.md](PRODUCT.md). Source: `../defintel-ux/design-review-log-TR.md`
(baseline spec + 21 revisions).

**Do not re-litigate without new evidence** — a measurement, a reader complaint, or a
defect. Not a fresh opinion. Eight of these were already decided twice in opposite
directions (see *Reversals*); each cost a round.

`NOT:` marks an explicit will-not-do. `→ Rev M` marks a decision later overturned —
kept so the reversal is not itself reversed. Pure CSS-level items from the baseline are
grouped rather than listed one by one.

---

## Rev 0 — baseline (§1–§7)

- A day is one file with two faces: briefing (analysed) and media sweep (raw) — not two products.
- `daybar` carries that model: same place, same form, always the day being read — cross-product jumps were landing readers on the wrong day's data.
- Cross-product link always goes to the *same* day; when the counterpart is missing it renders as a non-clickable span — "absence is information too".
- `‹`/`›` move within a product only; at the ends they stay disabled rather than vanishing — so the layout does not jump.
- The archive is reached only from the daybar's centre date; `← Geri` removed — one fixed place for day selection.
- Sticky budget at 375px is 88px and no third sticky layer is ever added — 13% of the viewport is the ceiling.
- `masthead` is a colophon: wordmark only, never sticky — it occupied ~110px with no navigation function.
- `endnav` exists on both page types before the footer — a 3,000-word briefing had no exit but the browser back button.
- Ranking is computed in `build.py` with no new dependency; the per-source penalty is clamped and applied order-independently — unclamped it handed a single-item source +40, and which TASS item got punished was random.
- Three-layer expansion: Öne çıkanlar (top 12, max 2/source, open) · categories ≤20 open, >20 show 15 + "+N daha" · "Genel Savunma Gündemi" closed — the problem is not volume, it is unranked volume.
- Öne çıkanlar is the analyst's entry point, never defended as the executive's signal — the executive's view is the briefing.
- No item is ever deleted from the page; only default visibility changes — the analyst's contract is "everything is here".
- Duplication between Öne çıkanlar and a category is accepted without renumbering — repetition costs less than cross-referencing.
- Opened, the Genel bucket shows "Taramaya değer" (tier A, max 3/source) plus a closed full dump — 351 → 40, using the customer's own source tiering.
- Clip meta carries at most 3 tokens (source · date only if older · `+N` only if `also`); country code, `lang` and the publication list are removed — noise weighted equally with signal on 528 rows.
- A `BRİFİNGDE` token in `--brand` is the only coloured meta token on the page.
- The whole clip row is the link (`display:block; padding:11px 0`) — single-line rows were ~40px, under the 44px thumb target.
- Hierarchy uses three *mechanisms*, not size: L1 fill + border, L2 mono + rule, L3 size and colour only — headings were smaller and paler than the body beneath them.
- The executive summary gets `--paper-2` ground and a 3px `--brand` left border — it is the entirety of the executive's four minutes and had no visual distinction at all.
- `--alarm` is restricted to real alarm state — an alarmed day was indistinguishable from a clean one at 375px.
- No section boundary may ever be `--muted`.
- Grouped implementation items: chip padding to 38px height, `scroll-margin-top` to 100px, kicker `border-top` with the trailing `::after` deleted, `endnav` bottom padding 96px, clip clamp 3 lines, daybar short date, briefing stays one column, media page gets a sticky category rail collapsing below 860px, clip measure 82ch → 72ch.
- Acceptance tests marked ◆ are one-off checks pinned to 17 September data, not regression tests.
- NOT: filtering the Genel bucket with a keyword dictionary — tautological; the expanded dictionary passed "$10 billion for feds not to work" and dropped good items.
- NOT: deleting items · infinite scroll or virtual lists · new colours, fonts or tokens · a theme switch · a backend or search index.

## Rev 1 — card navigation and deadline

- `decision_by` withdrawn from the interface, the data field kept — all four archive cards carried the identical "9 Ekim", making four different days look the same.
- The deadline chip and badge are deleted — a deadline is actionable only when it says what expires and who owns it.
- The only card-level state worth marking is `alarm`.
- The archive card stops being one big link: `<article>` with the title primary plus two bordered chips, `Brifing →` and `Medya takibi · {n} →` — a selector for a two-faced day must let you pick the face.
- The clip chip carries the day's headline count — a concrete reason to tap.
- Days with no sweep show a non-clickable "Medya takibi yok" — an affordance that appears and vanishes row by row looks broken.
- The notify button is icon-only when subscribed, labelled when not, never hidden — the label is acquisition text that only works in the off state.
- NOT: hiding notify when subscribed (an un-cancellable subscription is a dark pattern) · a "show when N days remain" deadline variant.

## Rev 2 — naming

- `SITE_TAGLINE` = "Savunma pazarı · günlük bülten" — what, plus how often; no other claim; reads correctly alone on an install page.
- `manifest` `name` is kept in sync by hand; `short_name` stays "DEFINTEL".
- The `MKE` category renders as "Doğrudan ilgili" with the data key unchanged — otherwise the page prints the company name in caps as its topmost heading.
- The footer disclaimer is the one surface where the institution's name must appear.
- NOT: "analiz" in the tagline (covers one of two products) · "günlük" alone (reads as *diary*) · marketing tone · dropping the tagline.

## Rev 3 — collapsible summaries

- Summary stance depends on layer: open in Öne çıkanlar, closed in categories and Genel — measured 293px × 110 rows ≈ 32,000px, 3.7× the previous default view.
- A summary's value is inversely proportional to the number of rows on screen.
- Mechanism is plain `<details>`/`<summary>` with no self-written state — focus, keyboard, `aria-expanded`, screen-reader announcement and no-JS operation all come free.
- The row's primary action is "read the summary"; the source link is secondary — the summary exists so the reader need not open the foreign-language article.
- The English original drops into the body — a verification element, not a scanning element, costing 35px per closed row.
- Rows without a summary stay plain links with no chevron — an empty opener is never shown.
- Filter matches auto-open their fold and re-close on clear; summary text joins the search haystack.
- NOT: auto-closing accordion or `<details name>` (closing a row above the viewport jumps the page ~215px under the thumb) · 2-line clamp plus fade (cuts mid-sentence; only halves the height) · `<a>` inside `<summary>` · hand-written `role`/`tabindex`/`aria-expanded`.

## Rev 4 — partial coverage

- Summary coverage is defined as the default-visible set — self-documenting: "if you can see it without clicking, it has a summary".
- The summarizer selects by `news_score`, not publication time — 87% of the budget was landing in a bucket closed by default; Öne çıkanlar got 4 of 12.
- **Uniformity is mandatory within a block, not across the page.**
- An in-scope row with no summary gets a `--muted` "özet alınamadı" token; an out-of-scope row gets nothing — announcing a fault that does not exist.
- Öne çıkanlar is all-or-nothing: if any summary is missing, none render open — a bad fetch degrades to "all closed", never "some randomly open".
- `summary_scope` is written into the item data; old days without it count as out of scope.
- NOT: a chevron on every row (400 empty opens teach that chevrons are worthless) · accepting mixed shapes · forcing 100% coverage past paywalls.

## Rev 5 — translation proxy

- Every clip link goes through the Turkish proxy without exception — the reader does not read English, so the English original is a failure state.
- A one-line kill switch `TRANSLATE_PROXY` is mandatory; the exposure trade-off is escalated to the customer as a conscious choice — every outbound tap leaks the selection pattern of a state defence manufacturer's executives to Google.
- Probing is per domain, weekly, written to a data file the build only reads — the build never goes to the network.
- Unknown hosts default optimistically for clips — a false optimist costs one bounce; a false pessimist silently serves English to a Turkish reader.
- Summaries are *not* shortened — turning them into teasers breaks the executive's primary use.
- NOT: a per-row translation token · per-item 403 probing.

## Rev 6 — anchor language and tablet

- Every fact has one owning section; citation is one-directional toward the owner; the citing side may repeat the owner's one distinguishing datum but not its explanation; a citation may not point back at what points at it — the old "don't repeat" rule made the fact live nowhere.
- ALARMLAR owns date and name; the development owns the explanation; "bkz. ALARMLAR" sentences are removed.
- In one column the measure is centred — it was 706px left-aligned at 834px.
- The rail flips at 920px, not 860px — the grid needs 833px, leaving zero breathing room; 920 puts iPad portrait in one column and landscape in the railed layout.
- **Rotation changes the chrome, never the text block.**
- Two-column Öne çıkanlar is deleted (→ supersedes Rev 0) — written when rows were 293px; Rev 3 made them 78px.
- `copylink` states that the anchor belongs to this day only — `G#` is positional.

## Rev 7 — where notification control lives

- **No surface may trigger an action whose outcome it cannot report** — the card showed "Aç" on all three pages while `paint()` did nothing on two of them.
- The two jobs split: transient result at the card, persistent state and opt-out in one fixed home.
- The bell moves to the footer on all three page types — it is a *device* setting, not a property of the day being read; discoverability rises from 1 page to 3.
- The card reports its own result: closes on success, stays open on failure with a retry — success is visible in the bell, failure needs recovery.
- A failure never writes the 7-day snooze — punishing the reader for a server error.
- The off-state label becomes an offer ("Yeni rapor bildirimi al"); the bell is not an acquisition channel, the card is.
- NOT: the bell in the daybar (one strip, one job) or masthead (a colophon) or the `.controls` row (page scope vs device scope).

## Rev 8 — translation in the bibliography

- `[K#]` still points at the original; a `Türkçe oku ↗` chip is appended — Rev 5 over-ruled: a canonical citation and a reading path do not conflict. **(reverses Rev 5)**
- Polarity is deliberately inverted between surfaces — in clips proxy is primary, in the bibliography the original is; the inversion encodes "this is evidence, that is reading".
- The chip is a silent mono link, not a framed chip — the bibliography is Level 3; 16 framed chips would be Level 2 furniture.
- The build guard is structural, not positional: `translate.goog` may appear only inside `a.tr-read` — survives restructuring.
- Chips must be added *after* URL linkification — otherwise the chip's own address is linkified again and the HTML breaks.
- A blocked domain shows "çeviri engelli" in the same slot — the block stays uniform in shape while the difference is explained.
- In the bibliography, unknown hosts default *pessimistically* — on an evidence surface false optimism costs trust, not a bounce.

## Rev 9 — the alarm section

- On a quiet day ALARMLAR is not written at all — **a channel that fires 100% of the time carries zero information** and teaches the reader to skip the top of the document.
- **The break in familiarity is itself the signal.** Rev 4's uniformity rule governs simultaneous comparison; day-to-day sections are never seen side by side.
- Deadlines move into their watch item's own line; the generated deadline list from Rev 6 is withdrawn — nine days of data show the fact is static, and what is the same every morning is reference, not news. **(reverses Rev 6)**
- `decision_by`, `status_of()` and `reports.json.status` are retired — identical across nine reports, rendered nowhere, and producing wrong data.
- **A field rendered nowhere is not maintained**; if needed it returns on the same day as its render site.
- NOT: a "bugün sakin" substitute sentence — the same zero-information channel renamed.

## Rev 10 — the MKE agenda line

- The MKE section becomes one rail block — it passed Rev 9's conditional test but failed the hierarchy test: Level 2 weight carrying a single number.
- Its class is scan metadata: "we looked there too, but that is not our subject".
- **The build computes the number, not the agent** — a hand-copied number is never cross-checked, and *silently wrong is worse than absent*.
- The prompt loses the MKE instruction entirely: the report never carries MKE's own news, no exception.
- At zero nothing is printed — not because zero is dull but because with an empty category there is no anchor, so it would be an unclickable label.
- **Data absence is not zero** — implementers must not merge the branches.
- Scale never changes the row's shape — emphasis is an editorial judgement, and the standing decision is to pass none on MKE's own news.

## Rev 11 — the G# identity system

- `G#` lives as plumbing and dies as reader vocabulary: identity exists only in `id` and `href` — 27 self-explaining uses against 8 bare citations; once the bare ones carry words the number never has to be read. **(reverses Rev 6)**
- Chips, headings and table badges all drop the number; prose citations become labels.
- **No citation may consist of an identity alone** — it carries the name of the thing it points at.
- `developments[].label` is the single source of truth; a missing label degrades to plain text and a bare `G11` is never printed.
- The prompt is unchanged — the agent keeps its markers, `enrich.py` strips them at render.

## Rev 12 — the watch list

- Only items that moved stay in the reading path; everything still open goes into a closed fold — 29 rows of which 3 moved, grown 7 → 29 in nine days, one row word-for-word identical for nine days.
- "bekliyor" is removed entirely — everything inside the fold is by definition waiting.
- A closed fold is an index entry, not an announcement, so it does not violate Rev 9.
- **Placement is determined by movement, not by object type.**
- At 14 days idle the agent must either drop the item or write one sub-clause saying why it is still open — silent accumulation becomes an explicit decision.
- A dropped item is never silent: the build diffs against yesterday and prints what fell off.
- Waiting items live in frontmatter as a bare-name array; the build derives age, additions, drops, counts and the 14-day warning — the agent hand-copying 24 rows a morning is why the list fed itself.
- NOT: deleting or auto-dropping open items (an open question does not close because time passed) · a separate page for ~25 rows · past deadlines as an exit criterion (the field was retired).

## Rev 13 — source date

- The full date stays as the record; a derived freshness token sits beside it — one string was answering two questions and failing the second. **If there are two jobs, do not make one thing do both.**
- The token prints on every entry with no threshold and no colour — `3 gün önce` and `108 gün önce` both read with zero effort; colour indicates state, and staleness is a measure.
- **The build computes it, not the agent** — measured: the agent labelled 13 entries, the newest 16 days old, while leaving 20 entries older than 7 days unlabelled.
- If the date does not parse, nothing is printed — **affordances and markers do not lie**.
- `(arka plan)` is retired — it claimed a *role* but was applied by an *age* rule, so it never produced a role signal at all.

## Rev 14 — unreachable sources

- The "Erişilemeyen kaynaklar" section is removed, not renamed — it structurally carried entries that are not evidence.
- The heading described a property of the *source* while recording the *agent's* outcome — one entry returned 200 with 7,220 characters of full text.
- The section repairs no visible gap; it creates the thing it explains.
- **A source that contributed nothing to the report is not a source.**
- **The agent's self-report about its own failure is never printed** — unverifiable, and only the reader discovers when it is wrong.
- The legitimate case survives in a better home: "couldn't read it but it might matter" is an open question, so it becomes a watch item.
- Measured gaps that limit what the reader sees are written; the agent's experience is not.
- NOT: network probing in the build — our fetcher is not the reader's browser, and the build goes to the network nowhere.

## Rev 15 — the scope note

- The line survives because it corrects a promise the daybar makes, not because "coverage was narrow".
- It prints a measurement with no adjective and no threshold, **every day** — a number that appears only when things are bad can be compared to nothing.
- The wording is "de var", never "seçilmedi" — we can measure that a URL appears in both places; "selected from the pool" claims a causality we cannot measure.
- The trigger is derived from the existing citation set, not the agent's declaration — the old trigger was the agent declaring something Rev 14 had just banned.
- Two features police each other: the `Brifingde` marker count on the sweep page must equal the numerator, and the build warns on mismatch.
- Operational causes never enter the reader's document.

## Rev 16 — one narrative home, computed rival strip

- FIRSATLAR + RİSKLER merge into "PORTFÖYE ETKİSİ" with an "Etki" column, rows sorted by g-id — both asked the same question; Leonardo sat in both, 40 rows apart.
- Root cause named: **sections had been built by the type of sentence about the development, not by the type of the development** — one item appeared in five places.
- "Etki" is text, never colour — risk/opportunity is an assessment; red would make it a warning.
- On mobile the tag is the card's first line via `order: -1` while staying second in the DOM.
- Rakip hareketleri folds into Gelişmeler, all sorted by g-id — those items held g1–g2, so the summary's first two lines pointed into a section with no developments.
- The rival closing sentence becomes a computed rail strip — it was an unverified absence claim over 12 brand names.
- Unmatched names stay faded rather than dropped — the fixed list makes the *scope* visible, so the reader need not trust "tespit edilmedi".
- Matching requires word boundaries and an explicitly bounded body — substring search found "IMI" inside "üret**imi**", and an unbounded last development swallowed the dropped brand list, attaching every rival to it.
- Watch rows become `<thread> → bugün: <development>`; the fold is renamed "Açık konular · N".

## Rev 17 — roles

- `role` replaces `domestic`: `rakip` / `yerli-rakip` / `emsal` — one heading conflated three relationships, and showing Aselsan under "rival" is a declaration the product has no authority to make.
- **Role belongs to rendering, never to matching** — so the decision can be reopened later with no loss of history.
- A second pass scans the day's headlines — almost all Turkish-industry news lands in the sweep's 400+ rows; an empty line would read as "nothing happened" when the truth is "we didn't look".
- Matched rows gather into a `#kat-turk` cross-section while staying in their own category — a lens, not a topic.
- On days with no sweep the names stay plain text with no arrow.

## Rev 18 — five blocks to three

- The two player strips merge into one "Oyuncular" block — both asked one question, and five labelled blocks in a 172px column is a second document beside the document.
- **Removing the heading removes Rev 17's problem by itself** — "oyuncu" is an observation, not a classification.
- Breaks occur only at separators; the arrow belongs to the last name's unit — "Nurol Makina" split across lines reads as two companies.
- The MKE count folds into the scan line; fractions move to the roster page — the denominator is learned once.
- Line-break verification measures rect `top` values, not `getClientRects()` count — an unbreakable span with two links yields three rects on one line.

## Rev 18b — /oyuncular.html

- The page moves and the old URL redirects — 17 of 64 names are plainly not rivals.
- Each row carries four derived values and links to the archive filtered to that company — "5 / 64" said five moved without saying which five.
- A never-seen company gets no token — **the blank is the statement**.
- `bugün` *is* printed here, unlike in the rail — in a 64-row roster today is not the default state.
- Group headings removed for one list sorted by mention count, Turkish and foreign interleaved — the reader's question is "who is active", not "who is ours". **(reverses Rev 17)**
- Filtering recomputes the header numbers — an unfiltered number above a filtered list does not say what it counted.
- Latent bug fixed: archive content search had **never worked since it was written** — `render()` referenced undefined leftovers, throwing inside an uncaught `.then()`, so everyone who typed saw an empty panel.

## Rev 19 — the scope line

- Six parts to three, count first — three were the pipeline's own state.
- `80/89 özet` removed: the same fact already sits on the row as "özet alınamadı", where it is actionable. **(reverses Rev 4)**
- `16 kaynak yanıt vermedi` removed: a maintenance metric with no reader baseline. **(reverses Rev 14)**
- The translation note removed: it pre-announces what tapping reveals. **(reverses Rev 5)**
- Neither number is deleted, only moved to the build log.
- "50 kaynak" becomes a door to a per-source page; non-responding sources are shown faded, not dropped.
- `collect_news.py` writes the source roster — 8 of 66 responded with nothing and appeared nowhere, so the page silently showed 58 of 66.

## Rev 20 — player filter

- Links carry an identity, not a name, and the page recomputes nothing — `?q=Baykar` text-searched a page whose "Bayraktar TB3" headline contains no "Baykar", so all four of Baykar's rows escaped the filter the build had computed. **(reverses Rev 17)**
- The box stays empty; the filter shows as a pill — **a filter is a state, and a state's place is its own indicator, not the input box**.
- Pill and box are ANDed; typing narrows within the pill.
- History uses `pushState` + `popstate` — the brief asked for `replaceState` *and* Back returning to the filtered state, which are impossible together; the behavioural requirement won.

---

## Reversals — decided twice, in opposite directions

Each cost a round. Check this list before reopening anything.

1. **Bibliography reachability** — Rev 5 exempted it, Rev 8 added the chip. The `[K#]` href itself never moved; only reachability reversed.
2. **Deadline list at the top** — Rev 6 designed it, Rev 9 withdrew it.
3. **Printing `G#` at the anchor** — Rev 6 restored it as arrival confirmation, Rev 11 removed it.
4. **Two-column Öne çıkanlar** — Rev 0 specified it, Rev 6 deleted it (written when rows were 4× taller).
5. **Role headings on the roster page** — Rev 17 shipped three, Rev 18b deleted them.
6. **"16 kaynak yanıt vermedi"** — Rev 14 kept it explicitly, twice, as a measurement; Rev 19 removed it as a maintenance metric.
7. **`?q=<name>` player links** — Rev 17 shipped with a passing acceptance test, Rev 20 found it broken by design.
8. **"The archive is only a day picker"** — Rev 0 said so, Rev 1 corrected it: a selector for a two-faced day must let you pick the face.

## Laws

- An element that marks a boundary gets a rule; one that marks state gets colour; one that carries content gets size — never two.
- No surface may trigger an action whose outcome it cannot report.
- A surface with two targets cannot be a single link.
- Affordances and markers do not lie.
- A channel that fires 100% of the time carries zero information; the break in familiarity is the signal.
- What is the same every morning is reference, not news — reference is consulted, not recited.
- A number that appears only when things are bad can be compared to nothing.
- A number above a filtered list must recount with the filter.
- Every fact has one owning section; citation is one-directional; no citation is an identity alone.
- The agent produces judgement; the build counts and derives. Silently wrong is worse than absent.
- The agent's internal state is never printed as a fact about the world.
- A field rendered nowhere is not maintained; it returns on the same day as its render site.
- Unknown is not zero. Absence is stated, not hidden.
- Uniformity is mandatory within a block, not across the page.
- If there are two jobs, do not make one thing do both.
- Rotation changes the chrome, never the text block.

## Open

- **Extend matching to every tracked player.** Today 11 international rivals appeared in headlines and none counted; Thales, PGZ, Northrop, KNDS and Rafael are absent from the line entirely. Short or ambiguous names need a safe-alias list and a passing test before they count.
- **Split the Kaynaklar page** — keep scope, drop the "yanıt vermedi" column, add a computed caveat line shown only when a failed source covers a tracked player.
- **Build the failure-threshold alert** to the operator. Today only a missing-report issue exists.
- **Put the Turkish-peer question to MKE — it is a prompt question, not an interface one.** Audit of all ten briefings: framing is *not* consistently neutral. Only two of the seventeen tracked Turkish companies appear in the agent's prose (Aselsan 12, Roketsan 8); Aselsan is routed `home: rakip` on both days it appears, and on 21 Eylül occupies a RİSKLER row naming MKE's own DENİZHAN as exposed — "yurt içinde 25 mm … ihracat pazarlarında da sunulabilir". Two days later the same manufacturer's Korkut and Şahin appear under FIRSATLAR as a demand signal *for* MKE, described only as "Türk menşeli". **The same company is a risk when named and an opportunity when not.**
- **Peer segments** — `emsal` entries carry no segment, so all ten vanish under any segment chip although Havelsan and FNSS are in the month's top ten. Give them segments, add a "Segmentsiz" chip, or leave it.
- **The ranking model is unvalidated** — the clamped penalty does not reproduce the analyst's manual selection (1 of 8 in the top 12). Cause diagnosed as mass ties; the fix was ruled out of scope and left to the designer.
- **Translation-proxy exposure** was escalated to the customer as a conscious choice and has not been confirmed.
- Deferred with a stated direction: single-open accordion (one attribute away) · `decision_by`'s future form (a state marker, not a raw date) · a source "role" marker · a "taranmadı" line · what to do if the MKE count grows large.
