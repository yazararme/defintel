# Rev 28 — FAIL

Reviewed against PRODUCT.md, the rev-28 criteria, review/shots/rev-28/{before,after}/ and http://localhost:8000 at 375×812 and 1440×900, light and dark. My screenshots are in review/shots/rev-28/reviewer/. The orchestrator's message had no builder rationale in it.

## Criteria

- **R28-P0-1 PASS.** On /haberler/2026-09-23-kaynaklar.html the Elbit Systems row carries "oyuncu: Elbit" and the Northrop Grumman row carries "oyuncu: Northrop Grumman". The label is right-aligned mono and doesn't wrap or overflow at 375 or 1440, light or dark. The 22, 17 and 18–21 pages do the same, and Leonardo is labelled on the 22nd. Evidence: after/haberler-2026-09-23-kaynaklar-375-*-full.png, reviewer/crop-haberler-2026-09-23-kaynaklar-375-{light,dark}-full.png, reviewer/haberler-2026-09-2{2,3}-kaynaklar-1440-*-full.png.
- **R28-P0-2 FAIL (cannot be verified).**
  - Positive half: met. On 23 Eylül the "Elbit Systems ve Northrop Grumman'ın kendi duyuruları bugün okunamadı." line sits directly under TARAMA as one caveat. At 375 it wraps to two visual lines inside a single element, and it stays below the first screen. Evidence: reviewer/crop-reports-2026-09-23-375-light-full.png, reviewer/reports-2026-09-23-375-dark-full.png, reviewer/crop-reports-2026-09-23-1440-light.png.
  - (I): met. Issue #5 has "KANIT-BOŞLUĞU: 23 Eyl · Elbit Systems (feed parsed but empty) · Northrop Grumman (HTTPError: 403…) — okuyucuya satır basıldı". Evidence: after/I-issue-5-kanit-boslugu.jpg.
  - Negative half ("kesişimi boş bir günde satır yok"): not shown. Every day that has a sweep (17–23 Eylül) has a non-empty intersection, and all of them print the line. The day submitted as the empty case, 15 Eylül, has no sweep at all ("Medya takibi yok", no TARAMA block, no kaynaklar page, and 14 and 16 are the same). The line is missing there because there is nothing to intersect, not because the intersection was computed as empty. No page on the site shows a swept day with an empty intersection and no line. Evidence: after/reports-2026-09-15-*.png, reviewer/reports-2026-09-1{4,5}-*.png.
- **R28-P1-1 PASS.** "yanıt vermedi" and "erişilemeyen" appear nowhere on kaynaklar 17–23, reports 14–23, haberler 23 or the home page. Failed sources show only as unnumbered rows. Evidence: after/haberler-2026-09-23-kaynaklar-*-full.png, reviewer/haberler-2026-09-*-kaynaklar-*-full.png.

## Regressions

- None found. The briefing first screen at 375 is the same before and after in light and dark (reviewer/cmp-23-375-dark-top.png). The only change at 1440 is the caveat added to the rail on 22 and 23 (reviewer/cmp-22-1440-light.png). No horizontal overflow at 375 on any page checked.
