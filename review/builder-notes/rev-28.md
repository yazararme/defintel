# Rev 28 — builder notes (izlenen oyuncunun kaynağı düştüğünde · KANIT-BOŞLUĞU)

Branch `rev21-33`. Nothing is committed or pushed. No workflow was triggered, no secret was
created or read, and no `gh` write command was run. `worker/` was not touched, and neither were the
workflows.

## What changed

| # | File | Change |
|---|---|---|
| R28-P0-1 | `data/rakipler.json` | A new `kaynak` field on the 4 players whose own announcement feed is in the collector's roster: `elbit` → "Elbit Systems", `northrop-grumman` → "Northrop Grumman", `leonardo` → "Leonardo", `mbda` → "MBDA". Each value is spelt exactly as `failures[].source` / the roster spell it. The field goes right after `name`, and `_schema` documents it. The file is still `indent=1` JSON. The matcher never reads the field, so the alias test is still 64/64. |
| R28-P0-2 | `build.py` (new "Rev 28" section at the end, plus call sites in `main()` and `build_report`) | `kanit_boslugu(data)` computes `{failures[].source} ∩ {r.kaynak}`. The trigger is the collector's own record. The agent's text is never read (Rev 14). `kanit_cumlesi()` builds the sentence. `_ilgi_eki()` picks the genitive suffix from the last word: Grumman'ın, Leonardo'nun, and for acronyms MBDA'nın and KNDS'nin. `build_report(..., bosluk=)` puts `<span class="rail-not" data-kural="KANIT-BOŞLUĞU">` inside the Tarama `rail-block`, after the value. If the day has failures but no Tarama row, the span goes in a block of its own. When the intersection is empty, nothing is printed. `kanit_boslugu_kurali(iso, data)` handles the day's report, next to `r23_kurallari` / `tekrar_manset_kurali`. It writes a log line with each failed source's error, writes an (A) section, and calls `uyari.ekle("KANIT-BOŞLUĞU", …)` once when the line is printed. Every report's log line also gets a `KANIT-BOŞLUĞU: <sentence>` sub-line. |
| R28-P0-2 | `assets/app.css` | `.rail-not`: rail mono, 11px, `--ink-2` (the rail-value colour), `flex-basis: 100%`. No state colour, no new token. In the ≤700px block `.rail-block` gains `flex-wrap: wrap`, so the line drops under the Tarama row instead of sitting beside it. |
| R28-P0-1 / P1-1 | `build.py` `sources_page()` | Next to a source that is some player's `kaynak`, the row now shows `<span class="scount soyuncu">oyuncu: Elbit</span>`. The "yanıt vermedi" cell is gone, and so is "· N yanıt vermedi" in the header, which now reads "N kaynak okundu". Failed rows stay faded (`srow--off`, Rev 19). The failure count and the reasons are still in the build log. |
| — | `review/tools/smoke.py` | Adds `r28_checks` and `KANIT_JS` (see Tests). |

HTML diff check: I stripped the `app.css?v=` hash, the `.rail-not` span, the `soyuncu` span and the
removed "yanıt vermedi" pieces from all 94 changed pages. The result is identical to `HEAD`.

## Line printed (local build, 23 Sep)

```
  · reports/2026-09-23.html · özet 1 ilk: 19 Eyl G1
      KANIT-BOŞLUĞU: Elbit Systems ve Northrop Grumman'ın kendi duyuruları bugün okunamadı.
  · KANIT-BOŞLUĞU 2026-09-23: satır: Elbit Systems ve Northrop Grumman'ın kendi duyuruları bugün okunamadı.
      Elbit Systems (Elbit): feed parsed but empty
      Northrop Grumman (Northrop Grumman): HTTPError: 403 Client Error: Forbidden for url: https://investor.northropgrumman.com/rss/news-releases.xml
  ! KANIT-BOŞLUĞU · KANIT-BOŞLUĞU: 23 Eyl · Elbit Systems (feed parsed but empty) · Northrop Grumman (HTTPError: 403 … news-releases.xml) — okuyucuya satır basıldı, kaynağı onar
```

The page shows the sentence under "TARAMA 50 kaynak · 536 başlık →" on `/reports/2026-09-23.html`
and on `/`. The alert line carries the reasons, which the reader's line does not. It goes only to
the operator (Rev 30), following the NOKTALI-İ / TEKRAR-MANŞET prefix convention.

## Per-day result, and the "empty intersection" day

| Days | Line |
|---|---|
| 17, 18, 19, 20, 21, 23 Sep | Elbit Systems ve Northrop Grumman'ın … |
| 22 Sep | Elbit Systems, Leonardo ve Northrop Grumman'ın … (the Leonardo feed was also empty) |
| 14, 15, 16 Sep | no line. These days have no media sweep, so there is no failure record (unknown ≠ zero). |

**No day with sweep data has an empty intersection.** Elbit's feed has been "parsed but empty" and
Northrop's has returned 403 on every collected day (17–23 Sep). The days without the line in the real
data are 14–16 Sep, and there the reason is that no data exists, not that the intersection is
empty. The empty-intersection path is proven in smoke on synthetic input: failures of Hartpunkt and
AeroVironment only give no line, no alert and no `rail-not` in the rendered rail. For an (S) of a real
empty-intersection day, the collector needs a day on which both feeds answer.

**Flag for the reviewer (Rev 9):** on current data the line fires on 7 of 7 sweep days. That is
the "channel that fires 100% of the time" pattern. The brief's answer is the operator alert ("kaynağı
onar"), and this cannot fix itself. Both failures are structural: Northrop's investor RSS returns 403
to the collector, and Elbit's feed parses empty. Until someone repairs them, readers will see the
same sentence every morning.

## İLK-EKRAN

At 375px the rail sits after the summary list (Rev 24 order), so the new line is below item 4 and
cannot move either measured edge. Locally, `--ilk-ekran` gives h2#ozet at **280px** and item 4's bottom
edge at **773px**, with the rail top at 924px. These are unchanged from Rev 32 attempt 2.

For the CI worst case I use smoke's "İLK-EKRAN en kötü hâl" check. It forces the ilk token onto its
own line and adds 0.15px letter-spacing, which is how the Ubuntu line breaks are reproduced. It gives
**280 / 799** (≤300 / ≤812). The Rev 28 line adds height only below the rail's top edge, which is
already below the fold. Measured at 375px, the line is 33px high (2 lines) and starts 8px under the
Tarama row. At 1440 it is 66px (3 lines) in the left rail.

## Tests (local, 23 Sep)

- `python3 build.py`: exit 0.
- `check_reports.py`: all ok. `--dort-durum` 🟢 4/4. `--oyuncular` 🟢. `--ilk-ekran` 🟢 280/773.
- `test_uyari.py` 33/33 · `test_collect.py` 21/21 · `test_silme_yok.py` 22/22.
- `python3 review/tools/smoke.py`: **SMOKE OK**. KAPSAM-SAYI alias test is 64/64. İLK-EKRAN worst
  case is 280/799. New lines:
  - build: the 23 Sep sentence, plus exactly one alert that names both sources.
  - static: the line appears where the intersection is non-empty in 10/10 reports and in `index.html`.
    "yanıt vermedi" appears on 0/7 Kaynaklar pages, and the Elbit and Northrop rows carry their names.
  - rule controls: an empty intersection gives no line and 0 alerts; Elbit alone gives
    "Elbit Systems'in …" and 1 alert; no sweep gives no line; the genitive cases are checked; the
    rail gets the line only when it is given one. `RUNNER_TEMP` and `GITHUB_STEP_SUMMARY` are hidden
    during these checks so that they do not reach a real CI alert file.
  - 375×812: on `/reports/2026-09-23.html` and `/` the line appears once, in the Tarama block, under
    the row, with the same left edge, in `--ink-2` mono, with no horizontal overflow. `/reports/2026-09-14.html`
    has no line. The Kaynaklar page has no "yanıt vermedi" and shows "oyuncu: Elbit" and
    "oyuncu: Northrop Grumman".
- The tree is left in the normal build. Screenshots are in the session scratchpad
  (`r28-rapor-375.png`, `r28-kaynaklar-375.png`), not in `review/`.

## Orchestrator notes / not done

- **(P) → (I):** no code change is needed. `KANIT-BOŞLUĞU` was already in `uyari.KURALLAR`. On the
  branch, the existing `uyari_test` dispatch input of `build.yml` (`UYARI_TEST_ONEK: "[TEST] "`) writes
  23 Sep's real line to `[TEST] DEFINTEL uyarıları · <gün>`. That needs a push plus a dispatch, which
  is outside my limits. The live (S), (A) and (I) evidence is still pending.
- **Wording choices:** the brief writes "Elbit Systems", but the player's `name` is "Elbit" (the
  matcher uses it, so I did not change it). The sentence therefore prints the `kaynak` names, which
  are the companies' own names as the roster spells them. The Kaynaklar row prints the player `name`
  with the prefix "oyuncu:", because "Northrop Grumman  Northrop Grumman" with no prefix reads like a
  duplicate.
- **Scope:** the brief writes the trigger as `failed_sources ∩ {r.kaynak}`. In the data,
  `failed_sources` is a count. The named list is `failures[].source`, and that is what the build
  intersects. AeroVironment's own feed also fails daily, but AeroVironment is not one of the 64
  tracked players, so it has no line.

---

# Attempt 2: the empty-intersection half, made reproducible

Verdict `rev-28-deneme1.md` failed R28-P0-2 because no page on the site showed a day that had a sweep and an empty intersection, and therefore no line. On the real data every sweep day has Elbit and Northrop failing, and stored data is not faked. This attempt follows the `kapsam_boz` / `noktali_boz` / `ilk_ekran_boz` pattern. Nothing is committed and no workflow was triggered.

| File | Change |
|---|---|
| `build.py` | New `BOS_KESISIM` env switch (`1` → the latest briefing day with a sweep; `YYYY-MM-DD` → that day), with `bos_kesisim()` / `bos_kesisim_duzenle()` at the end of the file and one call right after `load_news()` in `main()`. The switch works **only in this build's memory**: it removes the player-`kaynak` entries from that day's `failures` and lowers `failed_sources` to match, so those feeds count as answered. The other failed sources stay (14 on 23 Sep), which means the day is still a swept day with failures. After that, the real `kanit_boslugu()` path computes the intersection, finds it empty and prints no line. The build log shows `⚠ BOS_KESISIM (bilerek, yalnız bu derleme) …`, and (A) gets a ⚠️ note. The KANIT-BOŞLUĞU rule line ends with `(BOS_KESISIM, bilerek: Elbit Systems, Northrop Grumman bu derlemede yanıt vermiş sayıldı; veri dosyası değişmedi)`. `data/news/*.json` is never written, and smoke checks this with a sha256. With the switch off, the output is unchanged. |
| `scripts/check_reports.py` | New `--kanit-boslugu [--out DIR] [--base URL] [--gun G] [--bos-kesisim]`. The default is the latest report, and `--bos-kesisim` defaults from `BOS_KESISIM`. The expected state comes from the record (`data/news/<gün>.json` failures ∩ `rakipler.json` `kaynak`), with the same arrangement applied when the switch is on. The check shoots the briefing at 375×812 and 1440×900 (full page plus an element shot of the rail) and the day's Kaynaklar page at 375. It then asserts: the Tarama block exists; a non-empty intersection gives exactly one `.rail-not` inside the Tarama block that names every source; an empty intersection gives no `.rail-not`, and Kaynaklar still has ≥1 faded failed row; there is no horizontal overflow. It writes a table to (A) and exits 1 on a mismatch. Filenames are `kanit-boslugu-<gün>[-kaynaklar|-ray]-<w>[-bos-kesisim].png`. |
| `.github/workflows/build.yml` | New dispatch input **`bos_kesisim`** (boolean, default false). It sets `BOS_KESISIM=1`, is ORed into `UYARI_TEST_ONEK: "[TEST] "`, and skips commit/push (`&& env.BOS_KESISIM != '1'`). New steps, placed after İLK-EKRAN and before commit: `KANIT-BOŞLUĞU görüntüleri` (runs on every build, `continue-on-error`), the artifact `kanit-boslugu-<run>-<attempt>`, and the artifact link in (A). A normal run therefore produces the positive-state shots, and a `bos_kesisim=true` run produces the empty-intersection shots. `boz`, `kapsam_boz`, `uyari_test`, `noktali_boz` and `ilk_ekran_boz` are unchanged. All workflow YAML files parse. |
| `review/tools/smoke.py` | `r28_bos_kesisim_checks`: `--kanit-boslugu` is green on the normal build. Then a `BOS_KESISIM=1` build must log "kesişim boş (14 …) … BOS_KESISIM, bilerek", raise 0 KANIT-BOŞLUĞU alerts, put 0 `.rail-not` on `reports/2026-09-23.html` and `/`, keep 1 on 22 Sep, and leave the data file hash unchanged. `--kanit-boslugu` is green in that state too. Finally the normal build is restored. |

## Local evidence (`review/shots/rev-28/after-bos-kesisim/`, system Chrome, light)

The same page at the same widths, in two states, with the rail crop being the direct comparison:

- Normal: `kanit-boslugu-2026-09-23-ray-375.png` / `-ray-1440.png` show "TARAMA 50 kaynak · 536 başlık →" with the line "Elbit Systems ve Northrop Grumman'ın kendi duyuruları bugün okunamadı." under it. Full pages are `-375.png` / `-1440.png`, and Kaynaklar is `-kaynaklar-375.png` with 16 faded rows.
- Arranged (`BOS_KESISIM=1`): `…-ray-375-bos-kesisim.png` / `…-ray-1440-bos-kesisim.png` show "TARAMA 52 kaynak · 536 başlık →" and then OYUNCULAR directly, with no line. Full pages are `…-375-bos-kesisim.png` / `…-1440-bos-kesisim.png`. `…-kaynaklar-375-bos-kesisim.png` still has 14 faded failed rows, so the day was swept and had failures, and the line is missing only because none of the failures is a player's source. The Elbit and Northrop rows keep their "oyuncu:" labels.

## Tests (attempt 2, local)

- `python3 build.py` (normal and `BOS_KESISIM=1`): exit 0. The tree is left in the normal build, and 23 Sep has its line.
- `check_reports.py`: all ok. `--dort-durum` 🟢 4/4, `--oyuncular` 🟢, `--ilk-ekran` 🟢 280/773, `--kanit-boslugu` 🟢 in both states.
- `test_uyari.py` 33/33 · `test_collect.py` 21/21 · `test_silme_yok.py` 22/22 · `review/tools/smoke.py` **SMOKE OK**, including the new lines.

## Pending (outside my limits)

A push, then a dispatch of `build.yml` on `rev21-33` with `bos_kesisim=true`, gives the CI (S) artifact of the empty state plus the (A) table. A normal run gives the positive-state artifact.
