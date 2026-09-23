# K5: prompt addition (first-screen limits)

The desktop task's real instruction is not in this repo. The customer pastes these two
sentences into it themselves, on merge day. They join the same block as Rev 23 and Rev 32
(`rev-23-prompt.md`, `rev-32-prompt.md`). Paste them word for word:

```
Manşet en fazla 75 karakterdir, boşluklar dahil (yaklaşık 10 kelime).
Her özet maddesi en fazla 110 karakterdir, boşluklar dahil (yaklaşık 15 kelime); ayrıntı gelişmenin kendi bloğunda kalır.
```

The whole block after this revision, for a customer pasting it fresh:

```
Tutarı kaynağın verdiği para biriminde yaz. Kaynak kendi çevirisini veriyorsa parantez içinde aynen aktar. Kendin kur çevirme.
Başlık günün tezidir, özet maddelerinden biri değildir.
Her özet maddesi kimin ne yaptığını söyler.
Önceki 7 raporda anlatılmış bir gelişme manşete ya da özete ancak neyin yeni olduğunu ilk cümlesinde söyleyerek girer ('resmîleşti', 'sözleşmeye döndü', 'bedel açıklandı').
Manşet en fazla 75 karakterdir, boşluklar dahil (yaklaşık 10 kelime).
Her özet maddesi en fazla 110 karakterdir, boşluklar dahil (yaklaşık 15 kelime); ayrıntı gelişmenin kendi bloğunda kalır.
```

## Where each sentence goes

1. **Headline sentence:** put it in the frontmatter `title` rule, **in place of** the
   existing "at most 14 words" limit. Keep the "one development" part of that rule.
   Fourteen words gave 4- and 5-line headlines at 375px.
2. **Summary sentence:** put it in the YÖNETİCİ ÖZETİ rules, after the Rev 32 sentence.

## How the limits were derived

Every figure below comes from the 10 reports of 14–23 Sep. They were measured at 375×812 in
Chrome, as published and in a browser-only shortened copy. The full table is in `k5.md`.

- **The fixed part of the page.** The masthead and daybar end at 98px. With a 3-line
  headline, the summary heading sits at **280px**, 20px under the 300px threshold. Each extra
  headline line costs 32px, so a 4-line headline puts it at 311px and a 5-line one at 343px.
  **The headline must fit in 3 lines.**
- **Headline: characters decide, words do not.** The 3-line headlines had 63–69 characters
  and 9–11 words. The 4-line ones had 80–83 characters but only 8–14 words (16 Sep: 8 words,
  4 lines). I cut every headline one word at a time and measured each version, both normally
  and with CI's wider line breaks. **No version up to 77 characters went past 3 lines.** The
  limit is 75, which leaves 2 characters of margin. As a word limit, only 7 words would be
  guaranteed, and 17 Sep already had 10 words in 3 lines.
- **Summary.** With the heading at 280px, item 4 must end by 812px. That leaves room for
  **17 summary lines** across items 1–4, at 26px each. The days that pass had exactly 16. The
  failing days had 19–21 (15 and 16 Sep), because their items ran to 150–209 characters. The
  17th line is the only spare, and two things use it:
  - **CI wraps wider.** 17 Sep grows from 16 to 18 lines at 0.15px letter spacing (773 → 826).
  - **The "ilk:" token** (Rev 32) can drop onto a line of its own. 20 Sep has 3 tokens.

  I cut the items one word at a time and measured. **3 lines are guaranteed up to 97
  characters and 4 lines up to 137.** At 110 characters, all 10 days pass in the CI worst
  case: 0.15px letter spacing plus every token on its own line. The worst day is 20 Sep, at
  280 / 799. At 120 characters, 20 Sep fails in that worst case (852). At 137 it fails too.
  So the limit is 110.

With both limits applied, all nine days without an alarm pass. The measurements are in
the shortened copy, and the published pages are unchanged:

| day | as published (h2 / item 4) | with limits: local | with limits: CI worst |
|---|---|---|---|
| 15 Sep | 280 / 904 | 280 / 694 | 280 / 747 |
| 16 Sep | 311 / 884 | 280 / 721 | 280 / 747 |
| 19 Sep | 343 / 837 | 280 / 747 | 280 / 747 |
| 20 Sep | 343 / 863 | 280 / 747 | 280 / 799 |
| 21 Sep | 311 / 700 | 280 / 668 | 280 / 668 |
| 22 Sep | 311 / 726 | 280 / 668 | 280 / 668 |

17, 18 and 23 Sep already pass, and still pass with the limits.

**The alarm day (14 Sep) is not fixed by these sentences.** With the limits, it goes from
840 / 1423 to 808 / 1234. See `k5.md`: the alarm day needs a decision, not a prompt limit.

## How the build checks them (the build does not stop)

- **İLK-EKRAN** (Rev 24, unchanged) still measures the day's report at 375×812. It alerts
  through the Rev 30 channel when the heading is below 300px or item 4 ends below 812px.
- **İLK-EKRAN tanı** (new, K5) writes a table to (A) on every run. For each of the last 10
  reports it shows the headline's lines and characters, the summary's lines, the cause of
  any overflow, and the estimate with the limits applied. A day where the agent broke the
  limit shows up there as "metin: başlık 4 satır (83 kr.)".
- The build does not count characters itself. `guard_headline()` still warns at more than
  14 words. That is a looser check than the new sentence, and I left it unchanged.

Acceptance ("the next reports stay inside the limits") depends on dates, so the reviewer
marks it PENDING-HUMAN.
