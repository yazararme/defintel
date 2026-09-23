# Rev 23: prompt addition (R23-P0-2)

The desktop task's real instruction is not in this repo. The customer pastes these three
sentences into it themselves. Paste them word for word:

```
Tutarı kaynağın verdiği para biriminde yaz. Kaynak kendi çevirisini veriyorsa parantez içinde aynen aktar. Kendin kur çevirme.
Başlık günün tezidir, özet maddelerinden biri değildir.
Her özet maddesi kimin ne yaptığını söyler.
```

## Where each sentence goes

1. **Kur sentence (first line):** put it in the part of the instruction that covers the
   body text of the GELİŞMELER / development blocks, next to the rules on numbers and
   sources, for example where the instruction says that every claim gets a `[K#]`. If the
   instruction has no such part, put it just before the YÖNETİCİ ÖZETİ rules. The
   sentence covers every amount in the report, summary included.
2. **H1 sentence (second line):** put it in the frontmatter `title` rule, right after the
   existing "one development, at most 14 words" rule. The build takes the part of the
   title before the first `;` as the H1.
3. **Subject sentence (third line):** put it at the top of the YÖNETİCİ ÖZETİ rules,
   before the other rules for summary items.

## How the build checks them (the build does not stop)

- **KUR:** alerts when the body has an amount with another currency in parentheses, and
  either no single cited `[K#]` media summary contains both values, or a cited summary
  gives a different value in the same currency.
- **H1-TEKRAR:** alerts when the H1 and a summary item share at least 60% of their words.
- The subject sentence has no build rule. The reviewer checks it by reading.

Acceptance ("no KUR or H1-TEKRAR alert in the next 3 reports") depends on dates, so the
reviewer marks it PENDING-HUMAN. H1-TEKRAR would already have fired on 15, 18, 20, 21, 22 and
23 Sep, so the H1 sentence addresses a repeating pattern.
