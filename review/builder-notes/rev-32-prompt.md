# Rev 32: prompt addition (R32-P1-1)

The desktop task's real instruction is not in this repo. The customer pastes this sentence into
it themselves. It joins the same block as Rev 23's three sentences (`rev-23-prompt.md`), as a
fourth line. Paste it word for word:

```
Önceki 7 raporda anlatılmış bir gelişme manşete ya da özete ancak neyin yeni olduğunu ilk cümlesinde söyleyerek girer ('resmîleşti', 'sözleşmeye döndü', 'bedel açıklandı').
```

The whole block after this revision, for a customer pasting it fresh:

```
Tutarı kaynağın verdiği para biriminde yaz. Kaynak kendi çevirisini veriyorsa parantez içinde aynen aktar. Kendin kur çevirme.
Başlık günün tezidir, özet maddelerinden biri değildir.
Her özet maddesi kimin ne yaptığını söyler.
Önceki 7 raporda anlatılmış bir gelişme manşete ya da özete ancak neyin yeni olduğunu ilk cümlesinde söyleyerek girer ('resmîleşti', 'sözleşmeye döndü', 'bedel açıklandı').
```

## Where it goes

Put it in the YÖNETİCİ ÖZETİ rules, directly after the subject sentence ("Her özet maddesi
kimin ne yaptığını söyler."). The sentence names both the headline and the summary, so it also
covers the frontmatter `title`. There is no need to repeat it in the title rule.

## How the build checks it (the build does not stop)

- **"ilk:" token (every report):** a summary item that matches a development in the previous 7
  reports gets a mono "ilk: 19 Eyl" token at its end, linked to that development. A match is a
  shared `[K#]` URL, or at least two shared proper nouns plus word overlap ≥ 0.4. The token is
  printed whether or not the item says what is new. It gives the reader context, and it does not
  judge the item.
- **TEKRAR-MANŞET alert (day's report only):** when the H1 matches, the Rev 30 channel gets
  `TEKRAR-MANŞET: 23 Eyl H1 ↔ 19 Eyl`.
- The build does not check the novelty verb. The reviewer reads it from the (S) summary
  screenshot. Acceptance ("in the next 5 reports, the first sentence of every item with a token
  has a novelty verb") depends on dates, so the reviewer marks it PENDING-HUMAN.

## Before the customer pastes it

The sentence assumes the agent can see what the previous 7 reports said. The build only derives
the token and the alert. If the task does not give the agent those reports (or `data/index.json`
/ `data/reports.json`), the agent cannot follow the rule. The token and the alert will still
appear.
