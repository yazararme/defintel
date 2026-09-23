# K5: prompt addition (first-screen limits) — attempt 2

The desktop task's real instruction is not in this repo. The customer pastes these three
sentences into it themselves, on merge day. They join the same block as Rev 23 and Rev 32
(`rev-23-prompt.md`, `rev-32-prompt.md`). Paste them word for word:

```
Manşet en fazla 65 karakterdir, boşluklar dahil (yaklaşık 9 kelime).
Alarm günü alarm_title en fazla 70 karakterdir, boşluklar dahil; gelişmenin adını ve son tarihini taşır, açıklamayı değil.
Her özet maddesi en fazla 110 karakterdir, boşluklar dahil (yaklaşık 15 kelime); ayrıntı gelişmenin kendi bloğunda kalır.
```

The whole block after this revision, for a customer pasting it fresh:

```
Tutarı kaynağın verdiği para biriminde yaz. Kaynak kendi çevirisini veriyorsa parantez içinde aynen aktar. Kendin kur çevirme.
Başlık günün tezidir, özet maddelerinden biri değildir.
Her özet maddesi kimin ne yaptığını söyler.
Önceki 7 raporda anlatılmış bir gelişme manşete ya da özete ancak neyin yeni olduğunu ilk cümlesinde söyleyerek girer ('resmîleşti', 'sözleşmeye döndü', 'bedel açıklandı').
Manşet en fazla 65 karakterdir, boşluklar dahil (yaklaşık 9 kelime).
Alarm günü alarm_title en fazla 70 karakterdir, boşluklar dahil; gelişmenin adını ve son tarihini taşır, açıklamayı değil.
Her özet maddesi en fazla 110 karakterdir, boşluklar dahil (yaklaşık 15 kelime); ayrıntı gelişmenin kendi bloğunda kalır.
```

What changed from attempt 1: the headline limit goes from 75 to **65**, and there is a new
sentence for `alarm_title` (**70**). The summary limit stays at **110**.

## Where each sentence goes

1. **Headline sentence:** put it in the frontmatter `title` rule, **in place of** the
   existing "at most 14 words" limit. Keep the "one development" part of that rule.
2. **Alarm title sentence:** put it in the frontmatter `alarm_title` rule. That text is the
   alarm band, which stays at the very top of the page, above the headline.
3. **Summary sentence:** put it in the YÖNETİCİ ÖZETİ rules, after the Rev 32 sentence.

## How the limits were derived

All figures come from the 10 reports of 14–23 Sep, measured in Chrome at 375×812 after the
K5 layout change. The shortened versions were built in the browser only. Published pages and
data are unchanged.

**The CI worst case is now 0.3px letter spacing, plus every "ilk:" token on its own line.**
Attempt 1 used 0.15px. In the reviewer's CI run, that model was too mild. CI measured 16 Sep's
headline, cut to 75 characters (70 characters in practice), at 4 lines (311 / 805). Locally at
0.15px the same text was 3 lines. At 0.3px it is 4 lines. Every limit below was also checked at
0.45px.

- **The fixed part of the page (after K5).** On a day without an alarm, the masthead and
  daybar end at 98px. With a 3-line headline, the summary heading sits at **263px**. Each
  extra headline line costs 32px. With 3 headline lines, items 1–4 get **18 summary lines**
  (26.25px each) before 812px.
- **Headline ≤ 65.** I cut every headline one word at a time and counted its lines. Across
  the 10 headlines:
  - Locally and at 0.15px, the shortest cut that reached 4 lines was 78 characters (14 Sep).
  - At 0.3px and 0.45px it was **70 characters** (16 Sep). That is the break CI showed.

  65 leaves 5 characters, about one word, under the shortest known 4-line cut. Attempt 1's
  75 was already over that edge. The headlines that fit in 3 lines ran to 63–69 characters,
  so this limit costs them at most one word.
- **Alarm title ≤ 70.** The band text wraps at about 308px at 15.5px. I put 49 Turkish texts
  into the band one word at a time: 14 Sep's `alarm_title` and every summary item from the
  10 days. **Every cut up to 70 characters stayed within 2 lines**, from 0 to 0.45px. The
  shortest 3-line cut was 71 characters, or 78 locally. A 3rd line still passes: with a
  3-line band the summary heading sits at 295px. So 70 needs no extra margin. The limit also
  keeps the name and the deadline: "USAF namlulu hava savunma pazar araştırması — yanıt
  9 Ekim'de doluyor" is 69 characters. The published title is 90 characters and wraps to
  3 lines.
- **Summary item ≤ 110** (unchanged). I cut each item to the limit and measured item 4. With
  headline ≤ 65 and items ≤ 110, the worst of the 10 days is 20 Sep, at **782px** at both
  0.3 and 0.45px with every token on its own line. That leaves 30px, more than one line. At
  120 or 130 characters, 20 Sep reaches 835px in the CI worst case and fails.

With all three limits applied, **all 10 days pass, including the alarm day**, locally and in
the CI worst case. This file gives no per-day figures. For those, read the (A) table
"İLK-EKRAN tanı", which `check_reports.py --ilk-ekran --tani` writes on every run. Its
"CI en kötü" columns use the model described above: 0.3px letter spacing plus every "ilk:"
token on its own line. In Actions that model runs on top of Ubuntu Chromium's own wider
line breaks, so its figures are higher than a local run's. Of the numbers above, only 20 Sep's
782 and the 835 at 120 characters come from this model. They were measured locally.

## How the build checks them (the build does not stop)

- **İLK-EKRAN** (Rev 24, unchanged) still measures the day's report at 375×812. It alerts
  through the Rev 30 channel when the heading is below 300px or item 4 ends below 812px.
- **İLK-EKRAN tanı** (K5) writes a table to (A) on every run. For each of the last 10
  reports it shows:
  - both edges, locally and in the CI worst case
  - the headline's lines and characters
  - the band's lines, and ALARMLAR's height if it comes before the summary (0 since K5)
  - the summary's lines
  - the cause of any overflow
  - the estimate with the limits applied

  A day where the agent broke a limit shows up there as, for example, "metin: başlık 4 satır
  (83 kr.)" or "metin: alarm bandı 3 satır (91 kr.)".
- The build does not count characters itself. `guard_headline()` still warns at more than
  14 words. That is looser than the new sentence, and I left it unchanged.

Acceptance ("the next reports stay inside the limits") depends on future dates, so the
reviewer marks it PENDING-HUMAN.
