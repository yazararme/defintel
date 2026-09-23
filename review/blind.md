# Blind review — defintel.shadovi.com, 23 Eylül 2026

Independent reviewer. Written after reading PRODUCT.md only — **before** opening `/audit`,
`DECISIONS.md` or `docs/ux-review.md`. Pages seen: briefing (`/`), medya takibi
(`/haberler/2026-09-23.html`, plain and `?oyuncu=roketsan`), one thread
(`/izleme/xm30-da-organik-c-uas-sarti-…`), `/oyuncular.html`. Viewports: 1434px (desktop
window floor) and 375×812 (same-origin iframe).

## Top 10 issues

1. **Today's biggest Turkish deal is not in the briefing.** Medya takibi, filtered by
   Roketsan, shows "ASELSAN ile ROKETSAN arasında 1,2 milyar avroluk sözleşme imzalandı"
   (Anadolu Ajansı, today). The briefing does not mention it, yet both firms sit in its
   Oyuncular rail. Either it was left out on purpose and the rail should not advertise
   them, or the briefing missed the day's largest domestic contract. Whichever it is, the executive sees two
   names with nothing behind them.

2. **One number, two values.** SAN CUAS is "yaklaşık 1,5 milyar $ (16 milyar NOK)" in the
   briefing and "yaklaşık 1,74 milyar dolarlık" in the medya takibi summary of the same
   story (Advanced Navigation / Kongsberg). PRODUCT.md says a number that appears twice means one is wrong.
   Summary item 2 also drops who placed and who won the order ("sipariş verildi"). The body
   names Kongsberg and Advanced Navigation.

3. **At 375px the executive's question is not answered above the fold.** Before the H1 the
   phone shows TARAMA (50 kaynak · 536 başlık) and all nine Oyuncular. After the H1 come two
   rows of section chips. The summary starts at ~470px, so about 1½ of 5 items are visible
   on an 812px screen. Nothing on the first screen reads as a verdict (fırsat vs risk, or
   "nothing changes today").

4. **The headline says item 1 again.** The H1 "Letonya … Morana'yı seçti" is summary item 1
   almost word for word, directly below it. That is the "say it once" rule broken in the
   first 300px.

5. **One development, several names.** Section headings mix topics ("Letonya Morana
   seçimi") with bare company names ("Hensoldt", "American Rheinmetall", "Leonardo /
   Alkeon"). The watch list's "→ bugün:" links use yet other names: "Lynx XM30 prototip
   teslimi" lands on "American Rheinmetall", and "Leonardo–Alkeon 76 mm Danimarka üretimi"
   lands on "Leonardo / Alkeon". The thread page uses a third name. A reader cannot tell
   whether they arrived at the right place.

6. **The Oyuncular rail is two controls that look like one.** Seven names jump to an
   in-page paragraph (`#g1…#g9`). Roketsan and Baykar leave the page for a filtered medya
   takibi. Nothing tells the two apart. Some anchors land on paragraphs that do not name the
   player: Aselsan → the Pakistan paragraph ("Türk menşeli Korkut"), CSG → "Çek Excalibur
   Army". On `/oyuncular.html`, "Aselsan · bugün · 7 kez" gives no window for the 7.

7. **Thread pages don't answer "what became of it".** A thread is a list of dated
   headlines. The current-state sentence ("Prototip teslim edildi, şart hâlâ tanımlı değil")
   exists only in the day's watch list, not on the thread. The rows are links but look like
   plain text, which reverses the briefing, where everything is underlined. The header has no
   day navigation back to today. Slugs are truncated mid-word or carry report dates
   (`…-mut.html`, `…-g4.html`, `…-18-09-2026-raporu.html`).

8. **Medya takibi categories don't sort the pile.** 392 of 536 headlines (73%) fall into
   "Genel Savunma Gündemi". With a player filter on, the same headline appears once per
   category, twice for Roketsan. The page header still says "536 başlık · 50 kaynak" while
   one item is shown. Translated headlines use English Title Case ("Sensörünü Bağımsız Ürün
   Olarak Pazarlıyor"), which is not Turkish headline style.

9. **Restraint is claimed but not held.** There are 12 distinct text sizes (10.5, 11, 11.5,
   12, 13, 14, 15.5, 16.5, 18, 18.5, 20, 34px) and two near-identical greens
   (#2F4C3B / #3C6B4C). The summary box uses both a left rule and a fill (two mechanisms for
   one boundary). Every summary sentence is underlined as a link, so an underline no longer
   signals anything.

10. **FIRSAT and RİSK are visually the same.** Eight portfolio rows mix opportunities and
    risks in no stated order. The label is 10–11px grey mono in both cases, so an executive
    has to read every row to find the two that hurt. On mobile cards the "İzlenecek gösterge"
    line loses its column label and is just unlabelled grey text.

Also noted, not top 10: source ages are relative ("dün", "20 gün önce") inside a dated,
archived document, so they go wrong when an old report is opened. Citation links open the
Kaynaklar fold and land correctly, but the target is not highlighted and there is no link
back to the text. The 1440 layout leaves ~280px unused on the right while the four-column
table wraps cells to 7 lines.

## Scores

| Dimension | Score | A 7 looks like | A 10 looks like |
|---|---|---|---|
| **Executive answer above the fold (375px)** | 4 | Summary starts within the first screen; rail and chips below it | First screen = date, one-line verdict, 3–5 items with FIRSAT/RİSK readable at a glance; nothing else |
| **Say it once / internal consistency** | 4 | No repeated sentence; each development has one name used everywhere | Every number and name is computed or linked from one source; cross-page values can't disagree |
| **Core rule (no producer state as fact)** | 6 | No pipeline stats in the reading path; counts carry their window | Every count on the page is exactly true as worded; sweep size lives only on the sweep page |
| **Hierarchy and scanning (desktop)** | 6 | Risks are findable without reading every row; sections have one heading style | Row order carries meaning (severity), and the table reads as a ranked answer |
| **Wayfinding and links** | 5 | Links that look alike go to the same kind of place | Every link says where it goes; every landing names what you clicked |
| **Threads — job 2** | 4 | Thread shows current state and last change at the top | Thread opens with a one-line status, then a timeline whose entries carry the finding, not just the headline |
| **Medya takibi — job 3** | 5 | Catch-all bucket under ~30%; filter updates counts; no duplicate rows | Category + company filter + search compose; every row is one story once, with a Turkish-style headline |
| **Mobile layout** | 6 | No overflow (true today), cards work (true), plus a correct first screen | Phone is the primary design: sticky section nav, labelled card fields, one-thumb reach |
| **Visual restraint / type system** | 6 | ≤6 text sizes, one accent green, one mechanism per boundary | A token sheet you could print on one card; nothing on the page uses a value outside it |

**Overall: ~5/10.** The foundation is good: the tone is calm, sources resolve through the
folds, mobile has no overflow, and the portfolio table turns news into consequences. The
weak points are consistency (names and numbers) and the first phone screen.
