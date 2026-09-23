# Rev 27 — builder notes (thread page: what happened, where it stands now · İPLİK-DURUM)

Branch `rev21-33`. Nothing is committed or pushed. No workflow was triggered, no secret was
read, no network call was made, and no `gh` write command was run. `worker/` and `sw.js` were not
touched. The orchestrator scoped this round to P0 and P1, so **R27-P2-1 and the SLUG rule were not
built**. Slugs, old addresses, `thread_slug` and `thread_redirect` are unchanged.

## What changed

| # | File | Change |
|---|---|---|
| R27-P0-1 | `build.py` `watch_status()` (new) | Takes a watch line and returns that day's status sentence. It applies the same rule as the briefing's "→ bugün:" tail (`enrich.reading_path_shape`). It drops the name, the italic status marker (`*bekliyor.*`, `*ilerledi (G3).*`), `(G#)`, `[K#]` and `(dd.mm.yyyy raporu)`. It also drops any sentence that points back into the briefing ("… bkz. ALARMLAR.", which Rev 6 already removes). The first letter is upper-cased the Turkish way. It returns an empty string when nothing is left. |
| R27-P0-1 | `build.py` `build_threads()`, `thread_status()`, `thread_page()` | Each move entry now stores `note` = `watch_status(raw)`. The thread page prints `p.thread-status` under the h1: the **last move's** sentence plus `· {23 Eylül}`, with the last word and the date on one line. If the last move has no sentence, the line is omitted. An older move's sentence is never shown as the current status. Each move row shows that day's sentence (`.thread-note`) under the development label. |
| R27-P0-2 | `enrich.py` `link_watch_items()` | Thread links in the briefing, and on `/` (a copy of the latest briefing), now carry `?g=<report day>`. |
| R27-P0-2 | `build.py` `thread_daybar()`, `assets/app.js` (new IIFE at the end) | Every thread page has the standard report daybar. The build renders it for the latest briefing day, which is what shows without JS or without `?g=`. The build also writes `data-rapor` (briefing days) and `data-medya` (media days) on it. app.js reads `?g=`. If the value is a briefing day, it rebuilds the date ("23 Eyl · Çar"), the ‹/› arrows to the adjacent briefings (disabled at either end), and the cross link ("MEDYA TAKİBİ →" to the same day, or the unclickable "Medya takibi yok"). An unknown `?g=` leaves the default. The page still has no `data-day`, so the "kaçırdınız" strip does not fire on thread pages. |
| R27-P1-1 | `build.py` rows, `assets/app.css` | Move rows keep the whole row as the link. `.thread-line` is underlined (`--rule-2`, offset 3px, `--brand` on hover). The opening row has **no `<a>`**, carries a mono uppercase `.thread-tag` "açıldı" above its line (renders as AÇILDI), and its line is `--muted` with no underline. No new colour or token was added. |
| İPLİK-DURUM | `build.py` `iplik_durum_kurali()`, `iplik_boz()` | Runs after `izleme/` is written. For each thread whose last move has a sentence, it reads the **built HTML** and alerts with `uyari.ekle("İPLİK-DURUM", …)` if `class="thread-status"` is missing. On every build it prints a log line and writes an (A) section ("### İPLİK-DURUM — iplik sayfasında durum satırı (Rev 27)"). `IPLIK_BOZ=1` suppresses the status line for that build only, as local proof. No workflow input was added; that was not asked for. |
| — | `review/tools/smoke.py` | Adds `r27_checks` (see Tests). |

The site HTML changes only in these places: thread pages; `?g=` on briefing thread links; and
the `app.css`/`app.js` hash on every page. NOKTALI-İ now counts 25 uppercase selectors
(`.thread-tag`), with 0 examples.

## Results

- XM30 (`/izleme/xm30-da-organik-c-uas-sarti-18-09-2026-raporu.html`): the status line reads
  "Prototip teslim edildi, şart hâlâ tanımlı değil. · 23 Eylül". The meta line still says "4 hareket"
  above 4 underlined rows plus the AÇILDI row (F-10).
- İPLİK-DURUM: 0 missing. Of 48 threads, **16** have a sentence on their last move and all 16 pages
  have `.thread-status`. The other **32** have no status line, because either the last move had no
  free sentence (e.g. XM30 on 20 Sep: "*ilerledi (G3).*") or the thread has no move after it opened.

## For the reviewer

- **"Moves" that say nothing moved.** This behaviour is older than Rev 27 and was not changed.
  Watch items that are their own development (in the fold with their own `id="gN"`, e.g. Malezya
  MERAD, Drone Round, 665 milyon $) cite their own G# every day. `build_threads` counts that as a
  move. So Malezya MERAD shows 9 moves titled with its own name, and its status line reads "Yeni
  karar sinyali yok; …" dated 23 Eylül. The sentence is correct for that day, but the "hareket"
  count is inflated. Fixing this means changing what counts as a move, which is outside this brief.
- The status line repeats the first row's sentence. The brief asks for both.
- The default daybar, shown without `?g=` (from `/izleme/`, search, or a shared link), is the
  latest briefing day.
- Old alias redirect stubs do not pass `?g=` on. Briefings never link to them.

## Tests (local, 23 Sep)

- `python3 build.py`: exit 0. Output includes `· İPLİK-DURUM: 0 eksik · 48 iplik, 16 …` and no broken links.
- `IPLIK_BOZ=1 python3 build.py` → `! İPLİK-DURUM · İPLİK-DURUM: 16 iplik sayfasında durum satırı yok
  (IPLIK_BOZ=1, bilerek) — ilk: usaf-orta-…, malezya-merad-rmk-13, tungsten-…`. The normal rebuild afterwards returns to 0.
- `check_reports.py` (all ok), `--dort-durum` 🟢 4/4, `--oyuncular` 🟢, `--ilk-ekran` 🟢 1/1;
  `test_uyari.py` 33/33, `test_collect.py` 21/21, `test_silme_yok.py` 22/22.
- `review/tools/smoke.py`: **SMOKE OK**. New checks:
  - the build line;
  - `watch_status()` 4/4 unit cases;
  - Playwright with Chrome, tr-TR, at 375×812 and 1440×900. Clicking the XM30 link on
    `/reports/2026-09-23.html` gives `?g=2026-09-23` and the daybar "23 Eyl · Çar". The status text is
    exact and sits under the h1. There are 4 underlined link rows, and one unlinked opening row, not
    underlined, with "AÇILDI". There is no horizontal overflow.
  - a thread opened from 20 Sep (Drone Round) shows "20 Eyl · Paz" with both arrows live;
  - `?g=1999-01-01` keeps "23 Eyl · Çar";
  - the IPLIK_BOZ build plus a normal rebuild.
- I also checked by hand, in the same browser, 155 mm obüs (23 Sep), jet-motorlu hedefler (from 17 Sep;
  no status line, correctly) and Malezya `?g=2026-09-14` ("14 Eyl · Pzt", ‹ disabled, "Medya takibi
  yok"), at both widths.
