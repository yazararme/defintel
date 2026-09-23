# DEFINTEL — product

A daily Turkish defence-market intelligence product for MKE, a state ammunition and
weapons manufacturer. An agent writes one briefing a day; the build publishes it
without human review. Two faces of the same day: the **briefing** (analysed) and the
**medya takibi** (the raw sweep it came from). Today: ~540 headlines a day, 64 tracked
players, 48 open watch threads.

## Who reads it

Turkish executives and analysts at MKE. Some do not read English — hence a Turkish
translation on every foreign headline and a proxy link to a translated article.

- **Yönetici** — four minutes, on a phone, one question: *does anything today change my
  decision?*
- **Analist** — desktop, wants the whole day, accepts nothing being hidden.

They do not conflict. They are both failed when the page gives them equal weight.

## The three jobs

1. **Morning briefing** — summary plus portfolio table, ~4 minutes. Above the fold
   answers the executive's one question.
2. **Who moved today, and what became of it** — the Oyuncular line names the players
   whose names came up; every watch item has a thread page with its own timeline.
3. **Scan and search ~540 translated headlines**, by category and by company.

## Principles

- **Say it once, say it short** (Axios). One development, one narrative home. A number
  that appears twice means one of them is redundant or wrong.
- **Reference folded, not deleted** (Readwise Reader). Sources, appendix and dormant
  threads collapse; every citation still reaches its target through the fold.
- **Computed, consistent, restrained** (Linear). Anything countable is computed by the
  build, never written by the agent. Mono labels in one voice. No new colour, font or
  token without deleting one.

Hierarchy comes from mechanism, not size — three levels (DURUM, YAPI, DETAY) under the
log's law:

> An element that marks a boundary gets a rule; one that marks state gets colour; one
> that carries content gets size — never two of them.

Colour marks state, and there is exactly one state worth marking: **alarm**.

## The core rule

**Never show the producer's internal state as a fact about the world.**

"80/89 özet", "16 kaynak yanıt vermedi", "aday listesi üretilmedi", "erişilemeyen
kaynaklar" — each reported pipeline health inside a document about the defence market.
No reader can act on any of them. Two edges keep being missed:

- **A count is a claim.** "Bugün 9" asserts nine players moved. If the matcher covers
  only some players, the number is not incomplete — it is **wrong**. Coverage limits
  must never be published as findings.
- **Belief-changing failure is the exception.** When a tracked player's own source
  fails, an announcement may be missing; the build says so in one computed caveat line.
  That is a caveat on the day's evidence, not telemetry.

Telemetry goes to the build log, and to the operator directly when it needs attention —
today a GitHub issue when the report fails to arrive, and a failure-threshold alert
still to be built. **No status page exists or is planned**: there is one operator, and a
page nobody opens is not a control.

## Settled decisions

In [DECISIONS.md](DECISIONS.md), one line each with its reason.

**Do not re-litigate without new evidence** — a measurement, a reader complaint, or a
defect. Not a fresh opinion. Several were re-opened once, re-argued, and landed in the
same place at a cost.
