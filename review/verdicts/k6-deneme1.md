# K6: design review verdict

**FAIL**. K6-1 is not met for Elbit, and K6-4 is not paste-ready yet.

For this change only, the orchestrator allowed me to read two builder files: `review/builder-notes/k6.md` and `k6-kaynaklar.md`. I read no code or diffs. On 24 Sep I spot-checked the builder's claims myself, from this Mac, using the collector's Chrome user agent. Screenshots are in `review/shots/k6/reviewer/`.

- **K6-1 (diagnosis): FAIL.**
  - **Northrop: met.** Without an Accept-Language header the feed returns 403. With the header it returns 200 and an RSS feed. My own requests gave the same results.
  - **Elbit: not met.** The failure CI recorded was a 2xx response with no feed entries, from the URL stored in `kaynaklar.json`. The builder never requested that URL, because it is not in the repo. What the notes show instead amounts to a hypothesis, not a diagnosis:
    - `elbitsystems.com` returns 403 (I got 403 too).
    - `ir.elbitsystems.com/rss` returns 401 (I got 401 too).
    - The builder suggests a geo-block.
    - None of these is the response that actually failed. The cause of the empty feed is still unknown, and the note asks the client for the URL.
- **K6-2 (working source per company): PASS, on the letter of the criterion.**
  - **Northrop RSS:** I saw the same last 3 headlines in the live feed, dated 17, 14 and 10 Sep 2026.
  - **Elbit Systems UK page:** returns 200. Its last three items (16 Sep, 7 Sep and 5 Aug 2026) and their URLs match the note, and the page has 4 items dated 2026.
  - **Offline HTML parser test:** green in the (A) summary.
  - **Caveat:** by the builder's own admission, the Elbit source covers only the UK subsidiary. It is not the parent company's announcements.
- **K6-3 (A): PASS.** Evidence: `after/A-k6-test-ozet-girisli.jpg`. The summary shows:
  - job "ayristirici" green;
  - "🟢16/16 kontrol", with 0 calls to the network library;
  - Northrop: rss, `Accept-Language` fix, 10 items parsed;
  - Elbit UK: html · `elbitsystems-uk`, 20 items parsed;
  - the last 3 headlines and dates, identical to the hand-off note.

  The shot is cropped, so run ID 35927512282 does not appear in it.
- **K6-4 (hand-off paste-ready): FAIL.**
  - **Northrop block:** it is a whole object, `{"ad": …, "istek_basligi": …}`, but the instruction says to add one field to the existing entry. Pasting the block as written would create a second, partial "Northrop Grumman" entry, or broken JSON, in the source list. It should be just the single line `"istek_basligi": {"Accept-Language": "en-US,en;q=0.9"},`.
  - **Paste timing:** the note tells the client that the code "güncellendi". But the builder notes say the branch has not been committed, and the note never says to paste only after merge.
  - **Consistency with (A):** the headlines, dates, counts and the fix all match the (A) summary.

**Regressions: none.**
- On http://localhost:8000, the 23 Sep briefing still shows the Rev 28 line "Elbit Systems ve Northrop Grumman'ın kendi duyuruları bugün okunamadı." at 375 and 1440, light and dark, with no horizontal scroll. Evidence: `reviewer/reports-2026-09-23-{375,1440}-{light,dark}-caveat.png`.
- The top of the briefing at 1440 matches the K5 reviewer shot. Evidence: `reviewer/cmp-k5-vs-k6-1440-light-top.png`.
- I also shot the 23 Sep medya takibi and kaynaklar pages.
