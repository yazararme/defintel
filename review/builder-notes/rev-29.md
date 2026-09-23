# Rev 29 — builder notes (visual system: L1-DOLGU · ÇİZGİ-KONTRAST · notification card)

Branch `rev21-33`. Nothing is committed or pushed. No workflow was triggered, no secret was created
or read, and no `gh` write command was run. `worker/`, `sw.js`, the workflows and DECISIONS.md were
not touched.

Scope follows the orchestrator note: R29-P0-1, R29-P1-1 and R29-P1-2, plus the L1-DOLGU and
ÇİZGİ-KONTRAST build rules. **Not done:** F-07 masthead, F-13 dead guard, R29.2 type tokens, F-11
grid, the TİP-BELİRTECİ rule, and the Rev 0 → R29.4 reversal entry (the orchestrator writes that).

## What changed

| # | File | Change |
|---|---|---|
| R29-P0-1 | `assets/app.css` | `.prose h2#ozet + ol` loses its `border-left: 3px solid var(--brand)` and keeps only the `--paper-2` ground. The 3px moves into `padding-left` (36 → 39px), so the text column sits exactly where it was and lines wrap the same way. The alarm-day variant drops `border-left-color: var(--alarm)` and keeps its `--alarm-tint` ground. |
| R29-P0-1 (L1-DOLGU) | `assets/app.css` | `.highlights` (Öne çıkanlar on the media pages) had the same Rev 0 L1 treatment: `--paper-2` plus a brand left edge. L1-DOLGU flagged it on the first run, so I removed the edge there too and moved the 3px into the padding (16 → 19px). **This is outside the P0-1 table row.** I did it because R29.4 overturns Rev 0's L1 definition as a whole, and the alternative was a rule that fires on every build. Reviewer: please confirm, or say if it should go back. |
| R29-P1-1 | `assets/app.css` | `--rule-2` light `#CAC6BC` → `#908E88`, and dark `#3B4048` → `#62656B`. Each new value is the old one mixed toward `--ink`, so the hue family stays the same. Only the values change: no token was added and `--rule` is unchanged. Everything else that uses `--rule-2` (chip borders, underline colours, the disabled daybar arrow) also gets darker. |
| R29-P1-2 | `assets/app.js` | The notification card no longer waits for a second visit: the `VISITS >= 2` gate and the `defintel:visits` counter are removed. When the card shows, it is moved in the DOM to sit right before `.endnav`. Everything else is unchanged: the iOS-installed rule, `permission === "default"`, no existing subscription, the 7-day "Şimdi değil" snooze, failure handling and `paint()`. |
| R29-P1-2 | `assets/app.css` | `#notifycard` is now in the page flow: `position: static`, no shadow or ground, a `--rule-2` top rule, 48px top margin, and `#notifycard + .endnav { margin-top: 0 }`. The install bar stays fixed. The footer bottom padding changes from 34px to **96px**. On screens up to 600px wide, while the install bar is visible, the footer padding is **168px** (`body:has(#installbar:not([hidden])) .foot`). See the note below. |
| rules | `build.py` (new "Rev 29" section at the end, and one call in `main()` after NOKTALI-İ) | `r29_kurallari()`, which uses `l1_dolgu_ihlalleri()`, `cizgi_kontrast()`, `css_belirtecleri()` and `kontrast_orani()`. |
| — | `review/tools/smoke.py` | Adds `r29_checks`, `R29_JS` and `R29_KART_JS`, and a docstring paragraph. |

The HTML changes only by the new `app.css?v=` / `app.js?v=` hashes: 90 and 69 lines, and nothing
else in any page. `data/` is unchanged.

**Why 168px on narrow screens.** 96px clears the install bar only above 600px, where the bar is
73–74px tall. At 320–600px the buttons wrap to their own row, and the bar grows to 130–152px
(measured). With only 96px, the bar covered the footer bell (bell 672–716px, bar top 682px). The
bigger padding applies only while the bar is showing, so there is no extra empty space otherwise.

## Build rules

- **L1-DOLGU.** The rule reads `assets/app.css` with comments removed, and merges each selector's
  declarations in file order; `@media` blocks count as unconditional. A longer selector inherits
  from any base selector it ends with, so `.report--alarm .prose h2#ozet + ol` gets
  `.prose h2#ozet + ol`, and `.chip:hover` gets `.chip`. That way a ground set in one rule and an
  edge set in another are still caught together.
  - **Ground token** = `--paper` or `--paper-2`. `--alarm-tint` is a state colour (DURUM), so the
    alarm band's tint plus alarm edge is colour on colour, not a boundary rule. I kept it out of
    the rule; including it would make every alarm-day build fire.
  - **Left edge** = a non-zero `border-left`, `border-inline-start` or `-width`. A four-sided
    `border:` box, such as a chip, does not count.
  - **Result:** 0 violations. Before the `.highlights` fix it was 1.
  - **Static limit:** a selector that reaches the same element by another path, such as
    `.report-grid .prose > ol`, is not matched as text. The smoke browser pass catches that case
    from computed styles.
- **ÇİZGİ-KONTRAST.** The rule reads `:root` and the `prefers-color-scheme: dark`
  `:root:not([data-theme="light"])` block, and computes the WCAG ratio of `--rule-2` against
  `--paper`: **light 3.17:1** (`#908E88` / `#FCFBF9`) and **dark 3.18:1** (`#62656B` / `#121316`),
  threshold 3. With the Rev 0 values it would be 1.65 and 1.78. Against `--paper-2` the new values
  are 2.95 and 2.92; no section rule sits on that ground.
- **Outputs.**
  - Log: `· L1-DOLGU: 0 ihlal …` and `· ÇİZGİ-KONTRAST: --rule-2 / --paper · açık 3,17:1 … · koyu 3,18:1 …`
  - (A): one section, "L1-DOLGU · ÇİZGİ-KONTRAST — görsel sistem (Rev 29)", with one line per
    rule (🟢/🔴 and the two ratios in bold).
  - On a violation: `uyari.ekle("L1-DOLGU", …)` or `uyari.ekle("ÇİZGİ-KONTRAST", …)`. Both names
    were already in `KURALLAR`.

## P1-2 verification (real browser context)

`review/tools/shoot.py` blocks service workers, and the card depends on `serviceWorker.ready` plus
`PushManager`. So the check runs in Playwright with `channel="chrome"` and
`service_workers="allow"`, in a fresh context (clean storage) at 375×812 with mobile and touch
enabled, on `/reports/2026-09-23.html`:

- **On the first visit, the card appears.** It has `position: static` and its next sibling is
  `.endnav`: it sits between "EK: KATILIMCI LİSTELERİ" and "← 22 EYLÜL 2026 BRİFİNGİ".
- **At the bottom of the page, the footer bell ("YENİ RAPOR BİLDİRİMİ AL") is visible and passes
  a hit test while the card is open** (top 672px).
- After the install bar appears (scroll, then 1.2s; 130px tall, top 682px), the bell is still
  visible above it (top 600px).
- **"Şimdi değil" hides the card, and it stays hidden after a reload.**
- The same holds on `/haberler/2026-09-23.html`.

Mutation checks, reverted afterwards: putting the card gate back makes the smoke card check fail.
A summary-list edge added through `.report-grid .prose > ol`, plus a `--rule` h2 rule, makes the
browser pass fail on both (ratio 1.27).

## İLK-EKRAN

The layout is unchanged because the 3px moved into the padding. On 23 Sep at 375×812: `--ilk-ekran`
gives 🟢 **h2#ozet 280px / item 4 773px** (the same as Rev 32 attempt 2). The smoke worst case,
with the token on its own line, bare or with 0.15px spacing, gives 280 / 799.

## Tests (local, 23 Sep)

- `python3 build.py`: exit 0.
- `check_reports.py`: all ok. `--dort-durum`: 🟢 4/4. `--oyuncular`: 🟢. `--ilk-ekran`: 🟢 280/773.
- `test_uyari`: 33/33. `test_collect`: 21/21. `test_silme_yok`: 22/22.
- `python3 review/tools/smoke.py`: **SMOKE OK**. The new lines are:
  - the R29 build line
  - rule controls on mutated CSS, not written to disk: a brand edge on the summary box, an edge
    from a longer selector, and an edge from `:hover` each raise exactly L1-DOLGU; a `border:` box
    raises nothing; the Rev 0 `--rule-2` values raise exactly ÇİZGİ-KONTRAST
  - a browser pass over the report and media pages at 375/1440, light and dark: 8/8, with the
    lowest section-rule ratio at 3.17
  - the first-visit card check

The tree is left in the normal build.

## Not done / for the reviewer

- The (S) and (A) evidence on the live site and in Actions needs a push and a build, which are
  outside my limits.
- The `.highlights` edge removal and the 168px narrow-screen footer padding both go beyond the
  letter of the brief (see above).
- Screenshots are in the session scratchpad (`p12.png`, `p12-alt.png`, `r29-*-{375,1440}.png`),
  not in `review/`.
