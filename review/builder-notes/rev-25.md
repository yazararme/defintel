# Rev 25 — builder notes (filter gate, categories, translation cost · SİLME-YOK · İPUCU-YOK)

Branch `rev21-33`. Nothing committed or pushed. No workflow triggered. No network, Claude,
translation or summary call, and no Drive access. No secrets created or read. `worker/` not
touched. The Drive `kaynaklar.json` was not fetched. The nine filter-noted source entries (name,
language, tier, `not`) were copied into the fixture from the copy already read for the brief's
measurement. Skipped as the brief says: P2, S1, S5, S7, and growing the dictionary.

## What changed

| File | Change |
|---|---|
| `scripts/collect_news.py` | **P0-1** (the brief cites `:288-294`; the code was at `:476`): the `continue` is gone. A filter-noted source's item gets `savunma_terimi: true/false`. A `false` item is written, forced into Genel, and sorted to the end of Genel in the candidate file, so the 260-item limit cuts it first. **SİLME-YOK:** `silme_yok()` counts, per source, the items read inside the time window against the items written. An item counts as written if its URL is in the day file, if it was deduplicated into `also` by title key, or if an earlier run that day already wrote it. The (A) table lists filter-noted sources first; columns are okunan / yazılan / savunma dışı / durum. On a mismatch it calls `uyari.ekle("SİLME-YOK", …)` and exits 1 after the files and summary are written. SİLME-YOK is in `uyari.BLOKLAYICI`. `--sinama-silme-boz` works only with `--fixture` and drops one filter-noted item. **P0-2 S2:** `SOURCE_HINTS` is deleted, and `categorise(title, lang)` no longer takes a source. **P0-3 S3:** C-UAS keeps only counter and air-defence phrases, including the audit's `karşı-dron`, plus the existing air-defence system names (Skyranger, Patriot, NASAMS, Iron Dome, S-400). The bare words `drone/dron/uav/uas`, together with `loitering/dolanan mühimmat`, move to "Deniz ve İnsansız Sistemler". **S6:** İhale is limited to the audit's nine phrases plus `framework agreement`, the English form of `çerçeve anlaşma`. **P1-2 S4:** `player_announcement()` returns a match when a tracked player (the Rev 21 alias matcher, all 64) opens the title and the title contains an own-action verb (EN/TR/DE list, `PLAYER_ACTION`). "Opens the title" allows only a bullet or quote, a headline kicker ending in `:`, one possessive, or one co-subject before the name. The check runs after MKE and before the segments. The old 24-brand list is deleted, because a brand that is only mentioned is not its announcement. **P1-3 S8:** `rule_hits()` and `s8_counts()`. The candidate file heading says "Oyuncu Duyuruları"; the data key is unchanged. |
| `oyuncu_eslestir.py` (new, repo root) | The Rev 21 matcher moved out of `build.py` unchanged: `rivals_config`, `tr_fold`, `rival_patterns`, `rival_in_title`/`_body`, `headline_has`. Collection runs without markdown/pyyaml and cannot import `build.py`. It also adds `rival_start()`, which returns the text before the first match. `build.py` re-exports the old names. |
| `build.py` | **P1-1:** `NEWS_LABELS["Rakip Duyuruları"] = "Oyuncu Duyuruları"`. `cat_id` follows the label only for this key (`#kat-oyuncu-duyurulari`), because the anchor is visible in the address bar after a rail tap. MKE keeps `#kat-mke`. **P0-1 placement:** in `news_layout`, a `savunma_terimi: false` item is always placed in Genel, is never in Öne çıkanlar, and is never in "Taramaya değer", so it only sits in the closed full dump. `default_visible`, and through it `summarise_news.py`, therefore never gets one. **P1-3:** `kategori_isabeti()` covers the latest news day: a log line, an (A) table "Kategori · Kalem · Yalnız ipucuyla gelen · Hiçbir kelimeye değmeyen", and `uyari.ekle("İPUCU-YOK", …)` when hint-only is above 0. It reads its rules from `collect_news`. |
| `scripts/yeniden_kategorile.py` (new) | An offline re-categorisation with `--yaz` to write. It changes only `items[].category` and `categories`, and asserts that everything else round-trips unchanged. |
| `scripts/test_silme_yok.py` (new) | 22 checks, stdlib only. It reuses `test_collect.toplama()`, which runs a separate process with a network-library trap. The fixture has the 9 filter-noted sources, with Al Arabiya empty as it was on 23 Sep, plus DroneXL (with the old hint scope) and Defense Daily. There is an equal run and a deliberately broken run, plus S2, S3, S4, S6 and S8 unit checks. `hazirla DIR` writes the fixtures for the workflow. |
| `.github/workflows/silme-yok-test.yml` (new) | Workflow **`silme-yok-test`**. It runs on push to `rev21-33` (collect, test, matcher, the workflow itself) and on `workflow_dispatch` without inputs. It uses `UYARI_TEST_ONEK: "[TEST] "` and `GITHUB_TOKEN` only. Job **`esit`** runs the local test and one collection: (A) shows the SİLME-YOK table with 9/9 filter-noted rows equal, and no alert. Job **`bozuk`** (`needs: esit`) uses `--sinama-silme-boz`: (A) shows 🔴, the job goes red, and the flush writes a SİLME-YOK line to the `[TEST] DEFINTEL uyarıları · <gün>` issue. |
| `.github/workflows/build.yml` | The push `paths` list gains `oyuncu_eslestir.py` and `scripts/collect_news.py`. The dispatch inputs are unchanged (`boz`, `kapsam_boz`, `uyari_test`, `noktali_boz`, `ilk_ekran_boz`). A normal run's (A) now contains the "Kategori isabeti" table. |
| `review/tools/smoke.py` | `r25_checks`, see the docstring. |
| `data/news/2026-09-23.json` | Re-categorised. Only category fields changed. |
| `haberler/*.html` | Rebuilt: the label and anchor rename on every day, plus the new 23 Sep layout. |

`collect-news.yml` is unchanged. When SİLME-YOK fires, the collect step exits 1: translation,
summaries and the commit are skipped (blocking), and the `if: always()` flush still sends the
alert.

## Client decision (R25.1): translate the title only, no summary

`translate_news.py` already translates every item in the day file, so a kept non-defence title
gets `title_tr` with no change there. Summaries are chosen by `build.default_visible`. Because
`news_layout` keeps `savunma_terimi: false` out of Öne çıkanlar and out of every open category
head, these items never reach the summary call. Smoke checks this in memory: 60 of the 23 Sep
items are flagged, and 0 of them enter the scope or Öne çıkanlar.

## Re-categorisation: applied to 2026-09-23 only

`python3 scripts/yeniden_kategorile.py 2026-09-23 --yaz`. The earlier days (17–22) are not
re-categorised: their stored categories still include hint assignments, and only their label is
renamed. 536 items before and after; 97 items changed category. Same key order and format;
`git diff` shows 206 changed lines.

| Kategori | önce | sonra |
|---|--:|--:|
| C-UAS ve Hava Savunma | 59 | 14 |
| Topçu ve Mühimmat | 26 | 4 |
| Rakip → Oyuncu Duyuruları | 14 | 12 |
| İhale ve Sözleşmeler | 20 | 1 |
| Deniz ve İnsansız Sistemler | 16 | 39 |
| Hafif Silah ve Mayın | 2 | 2 |
| Tedarik Zinciri | 2 | 2 |
| Politika ve Regülasyon | 5 | 5 |
| Genel Savunma Gündemi | 392 | 457 |

Moves: C-UAS→İnsansız 26 · Topçu→Genel 21 (all hint) · C-UAS→Genel 18 · İhale→Genel 18 ·
Rakip→Genel 7 · İnsansız→Genel 2 · →Oyuncu 5 (one each from İhale, Genel, C-UAS, İnsansız, Topçu).

### S8 per category, 23 Sep (hint-only / no-word)

| Kategori | before (old rules) | after |
|---|---|---|
| C-UAS | 19 / 19 | 0 / 0 |
| Topçu | 21 / 21 | 0 / 0 |
| Deniz ve İnsansız | 2 / 2 | 0 / 0 |
| Rakip/Oyuncu, İhale, Hafif Silah, Tedarik, Politika | 0 / 0 | 0 / 0 |
| Genel | — / 392 | — / 457 |

The "before" column uses the old term lists: 42 hint-only, the audit's number. Measured against
the new rules, the same stored data would show hint-only of C-UAS 45, Topçu 21, İhale 19,
Rakip 7 and İnsansız 2, so an un-recategorised day raises İPUCU-YOK.

### Every move

**C-UAS ve Hava Savunma → Genel Savunma Gündemi (18)** Naval News: Belgium’s second rMCM ship ‘Tournai’ Arrives in Zeebrugge; Naval News: INS Trishul Arrives in Toulon Sporting Recent Upgrades; Unmanned Airspace: Russian reactor hit, more than 100 drones reported near Ukrainian nuclear sites ; Unmanned Airspace: Côte d’Ivoire expands Zipline logistics network to ten distribution centres; Unmanned Airspace: Australia completes first UTM system test; Naval News: Bayraktar TB3 Drops Sonobuoys from TCG Anadolu in ASW Milestone; Naval News: Japan Marine United and BMT Launch First CAIMEN Japan Landing Craft; DroneXL: Insta360 Luna Pro Review: 8K Gimbal Camera Tested in Alaska Wind; DroneXL: Zipline Promises Ivory Coast A 300% Return, Not What It Costs; DroneXL: DJI Osmo Pocket 4 Hits $572 on Amazon, a Price DJI Never Set; DroneXL: FCC Bars DJI Chips From New US-Built Drones on October 13; DroneXL: DJI Neo 3 Leak Is Recycled Box Art, and the Vents Gave It Away; DroneXL: Dolomites Parks Ban Hobby Drones, DJI Mini 5 Pro Included; DroneXL: DJI Spinoff Livox Halves Point Rate to Cut Robot LiDAR Cost; DroneXL: Air Force Loses Shahed Clone Off Eglin, Fishing Charter Reels It In; DroneXL: Amazon Wants Drones Over 6 Massachusetts Towns. Not All Have Been Told; DroneXL: Amazon Drones Overwhelm Texas Suburb, NYT Says. FAA Signed Off In July; DroneXL: Ben Biggs Built The 626 km/h Blackbird On 14-Cell Packs Few Pilots Use

**İhale ve Sözleşmeler → Genel Savunma Gündemi (18)** Indian Defence News: Canada PM Mark Carney, 'Looking Forward To Meeting PM Modi’, Aims To Wrap Up Tra; TASS: Trump undermined trust in US during negotiations on Greenland deal — senator; TASS: Spain to reject Russian LNG despite its companies’ contracts — foreign minister; TASS: Trump keeps Kiev concessions secret, says deal with Russia coming; TASS: US President Trump threatens Iran with ‘quick annihilation’ if no deal reached; TASS: Trump claims Iran repeatedly rejected US nuclear deal; TASS: Trump confident US, Iran to make deal right after November election; Naval Technology: Raytheon, Bell Boeing win $64m US Navy contracts for V-22 fleet support; Defense One: Trump's FBI shut down investigation into defense contractor's alleged bribes; Defense News: US Army awards Lockheed Martin $1.2B PrSM contract; Defense Daily: BAE Nabs $818 Million Order For More AMPVs, Details Army Unit’s Work With AMPV 3; Defense Daily: Contract Advances B-21 Weapons Storage Infrastructure at Whiteman Air Force Base; Breaking Defense: Trump signs Greenland security agreement, defusing allied tensions; Airforce Technology: CAE nets US Air Force C-130H aircrew training contract extension; Naval Technology: Lockheed Martin wins US Navy awards for F-35 support, Trident II work; Defense News: Denmark says NATO shares responsibility for Arctic security under Greenland deal; Defense Daily: JRC Integrated Systems wins contract mod for SLCM-N, NC3; Armada International: NP Aerospace Named Prime Contractor for UK Light Mobility Vehicle Bid

**Topçu ve Mühimmat → Genel Savunma Gündemi (21)** Armada International: FQ-42 Vengeance Finds New Home at Creech Air Force BASE; Armada International: Chess Dynamics Expands Vision4ce CHARM Portfolio With Low-SWap CHARM50; European Security & Defence: Norway Orders Three More WiSENT 2 Armoured Recovery Vehicles from FFG; European Security & Defence: The M941 Tournai has arrived in Zeebruges; European Security & Defence: Bittium and Safran Electronics & Defense sign MoU; Army Technology: Delivery of UK’s future tank capability remains uncertain; Army Technology: Bundeswehr’s Heavy Infantry Weapon Carrier simulators pass factory test; Army Technology: Ukraine codifies Dodge RAM 5500-based armoured pickup; Armada International: Wescom Defence introduces its ATMIS Mobile Signature Management System to market; Armada International: German Special Forces Receive TAHR Airborne LTV; Armada International: Special – Electronic Warfare – 2026 – Issue 3; Analisi Difesa: React4life nel programma del Pentagono per la tecnologia Organ-on-Chip nelle con; Analisi Difesa: Primo contratto d’esportazione per lo Yakovlev Yak-130M; Analisi Difesa: Chi ha paura del voto?; Analisi Difesa: Agenzia Nova: i russi sbarcano mezzi a Tobruk per l’Africa Corps e l’esercito di; Analisi Difesa: L’Italia chiede il rafforzamento della missione europea Aspides nel Mar Rosso; Armada International: International Test Pilots School Canada spreads its wings; Analisi Difesa: Putin vince le elezioni, Trump dalla pace alle sanzioni contro Mosca. Gaiani a “; Analisi Difesa: Telsy: le ultime dall’Italia, operazioni cybercrime internazionali, novità da Te; Analisi Difesa: Verso la revisione radicale delle forze statunitensi in Europa; Analisi Difesa: Squadra che perde non si cambia!

**İhale ve Sözleşmeler → Rakip Duyuruları (1)** Anadolu Ajansı — güncel: ASELSAN ile ROKETSAN arasında 1,2 milyar avroluk sözleşme imzalandı

**C-UAS ve Hava Savunma → Deniz ve İnsansız Sistemler (26)** Al Jazeera: Pakistan’s new drone deal is with Trump-backed firm also selling to India; Unmanned Airspace: CAA Zimbabwe grants approval for nationwide VLOS and BVLOS drone deliveries; Unmanned Airspace: Denmark to present defence drone plan to industry; Unmanned Airspace: SESAR JU-funded RAXUS project to streamline UAS operations gets underway; UK Defence Journal: British drone submarine fires torpedo off Scotland; TASS: Ukraine cannot win drone war — Russian expert; Quwa Defence News: How Two-Way Drone Warfare Is Shaping Pakistan’s Counter-Insurgency (COIN) Effort; Opex360: Londres se félicite d’une «avancée majeure» après le tir d’une torpille par le d; European Security & Defence: Gogo and Insitu collaborate on Group 3 UAS connectivity; DroneLife: Alaska Drone Program Flies Blood Samples 1,000 Kilometers for Olympic Anti-Dopin; DroneLife: Matternet Drone Delivery Begins Trading on OTCQB; DroneLife: One of Europe’s Largest Civilian Drone Factories Just Opened in Hungary.  Here’s; DroneLife: Groups Ask Appeals Court to Review Rescinded FAA Drone Restriction; Defense Daily: Pentagon Program Selects 17 Companies To Compete In Drone Bomber Qualifier; Defence24 (PL): Dron nad amerykańską bazą w Polsce; Defence24 (EN): TUGA: A Polish radar for drone detection; Defence Security Asia: [VIDEO] Loji Minyak Moscow Diserang Dron, Pantsir Muncul di Lebuh Raya; Defence Industry Europe: U.S. Army tests layered defenses against 100-drone swarms at Fort Bragg, prepari; Defence Industry Europe: DeltaQuad launches Evo-LE drone with eight-hour endurance and 480 km reach for m; Defence Blog: U.S. Army tests drone mothership that launches its own swarm; Army Technology: Estonian firms demonstrate latest UAS tech in live flights; defenceWeb: Paramount reveals V-Raven VTOL UAV; DroneXL: ABZ Opens Hungary Drone Plant, Its FCC Pass Hinges on a US Factory; DroneXL: Belvedere Puts Drone Delivery on the Books Before Wing Names a City; DroneLife: Beijing Drone Owners Sell Aircraft Ahead of Citywide Ban; DroneLife: Drone Solutions Wins BVLOS Approval for Medical Deliveries in Zimbabwe

**Genel Savunma Gündemi → Rakip Duyuruları (1)** defenceWeb: Hensoldt introduces KENIS sensor and secures major customer order at AAD 2026

**C-UAS ve Hava Savunma → Rakip Duyuruları (1)** Unmanned Airspace: Hensoldt markets KENIS sensor as standalone product, announces first order

**Rakip Duyuruları → Genel Savunma Gündemi (7)** Soldat und Technik: KNDS: Weitere Türme THL20 für indische Kampfhubschrauber; Defense Arabia: Lockheed Martin Connects F-35 Crews Across Multiple Locations for Live Mission R; Defence Industry Europe: American Rheinmetall says next Lynx XM30 prototype delivered to U.S. Army for so; Analisi Difesa: La danese Alkeon avvia una collaborazione strategica con Leonardo; Soldat und Technik: HexaForce von Thales: KI-C2-System für NATO; DefenseScoop: Pentagon taps Northrop Grumman, True Anomaly for recon satellites that can monit; Airforce Technology: Lockheed Martin presents Germany’s first F-35A jet

**Deniz ve İnsansız Sistemler → Rakip Duyuruları (1)** Naval News: Leonardo and Alkeon Partner to Bring 76mm Naval Gun Production to Denmark

**Deniz ve İnsansız Sistemler → Genel Savunma Gündemi (2)** Naval Technology: Forecasts: Global body armour market (2026-2036); Naval Technology: Keel laid for Indian Navy’s first Next Generation Missile Vessel

**Topçu ve Mühimmat → Rakip Duyuruları (1)** Defense Daily: Hanwha Ups Munitions Investment At Pine Bluff To $2.2 Billion

## (S) on /haberler/2026-09-23.html (Chrome, 375×812 and 1440×900, `smoke.py` R25)

- The rail and chips say **Oyuncu Duyuruları 12**. "Rakip Duyuruları" appears nowhere in the
  text or the HTML, and after the rail tap the address bar shows `#kat-oyuncu-duyurulari`. No
  site HTML file contains the old label; only the data key in `data/news/*.json` and the old
  `*-aday.md` files do.
- **C-UAS** has 14 rows: no Tournai, no Zipline, no DroneXL row.
- **İhale** has 1 row ("CAE USA Awarded $300M …"): no Greenland/Grönland row.
- "Hanwha, Pine Bluff'taki Mühimmat Yatırımını …" is under **Oyuncu Duyuruları**.
- The Genel full dump can be searched ("Dolomites" → 1 visible row inside `details.more`).
- **P0-1 (S), Trend.az: PENDING-HUMAN.** Those items were dropped at collection time and are not
  in the stored data. Check this on the first live collection after merge.

## Tests (all local)

`python3 build.py` exits 0; its log shows `İPUCU-YOK / S8 2026-09-23: yalnız ipucuyla gelen 0 ·
hiçbir kelimeye değmeyen 457`. `test_silme_yok.py` 22/22. By hand: the equal run's (A) shows
🟢 11/11 with 9 filter-noted rows equal, and the broken run exits 1 with 🔴 10/11 and the
SİLME-YOK alert. `test_collect.py` 21/21 · `test_uyari.py` 33/33 · `check_reports.py` ok ·
`--dort-durum`, `--oyuncular`, `--ilk-ekran` exit 0 · `review/tools/smoke.py` **SMOKE OK**.

## Notes / not done

- The S4 subject test is positional and conservative. "American Rheinmetall says …" (a
  subsidiary) and "KNDS: Weitere Türme …" (no verb) went to Genel. Players outside the 64
  (Lockheed, Raytheon, Rostec) are never Oyuncu.
- The 23 Sep `summary_scope` flags were not recomputed (no summary call allowed). Newly visible
  category-head rows have no summary and no "özet alınamadı" token, so blocks like İnsansız have
  mixed rows until the next live run. Öne çıkanlar is unchanged: 12 rows, same state as before.
- `data/news/2026-09-23-aday.md` (already consumed) still has the old sections and was left as
  it was. `data/news/2026-09-24-aday.md` is still local-only (Rev 31).
