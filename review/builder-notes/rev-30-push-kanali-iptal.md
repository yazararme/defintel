# Rev 30 — builder notes (operatör uyarı kanalı)

Branch `rev21-33`, not committed. Nothing deployed, no secret created or read, no push sent.

## What changed

| File | Change |
|---|---|
| `worker/worker.js` | `/subscribe?rol=operator` (Bearer `OPERATOR_SECRET`, stores `op:<sha256(endpoint)>` with `keys.p256dh/auth`, sends that device alone "DEFINTEL · test uyarısı"); `/alert` (Bearer `OPERATOR_SECRET`, lists **only** `op:` keys, RFC 8291 aes128gcm encrypted payload, same-day dedup in KV `seen:<gün>:<hash>` TTL 3 d, written only after a device accepted the push; returns `{op, sent, removed, new, suppressed}`); CORS allows `authorization`. Missing secret never matches (no `"Bearer undefined"`). `/notify`, `/test`, `/unsubscribe`, reader `/subscribe` unchanged. |
| `worker/wrangler.toml` | comment only: `OPERATOR_SECRET` listed with the other secrets. |
| `worker/worker.test.mjs` | new. OPERATÖR-YALNIZ test: mock KV + mock push (global `fetch`), one `sub:` + one `op:`; decrypts the payload like a phone would. Prints `OPERATÖR-YALNIZ: sub N push · op N push`, appends 🟢/🔴 line to `$GITHUB_STEP_SUMMARY`. Exit 1 if red. Mutation-checked: pointing `/alert` at all keys turns it red (`sub 1 push`). |
| `.github/workflows/worker-test.yml` | new. Runs the test on push to `worker/**` and on dispatch. No secrets, no network. |
| `sw.js` | payload push with `tur:"uyari"` → notification with its own title/body, tag `defintel-uyari`, tap opens the Actions run URL (external → `openWindow`). Reader push path unchanged. `CACHE` v56 → v57. |
| `assets/app.js` | operator registration panel: 5-tap gesture on the footer note or `#operator=` fragment (below). Built pages' `app.js?v=` hash changed accordingly (build.py output). |
| `scripts/uyari.py` | new. `uyari.ekle(KURAL, metin)` — validates against the 18 fixed rule names, prints to log, appends to `$RUNNER_TEMP/defintel-uyari.jsonl` (outside the repo tree; in-memory locally). `python3 scripts/uyari.py` = the one flush per run: one `/alert` call even with zero warnings (health check), writes the (A) section; red line when `op == 0` or a new warning got 0 pushes. `--test` sends "DEFINTEL · test uyarısı". Never fails the job. |
| `build.yml`, `collect-news.yml`, `pull-drive.yml` | last step `Operatör uyarıları` (`if: always()`) → `python3 scripts/uyari.py`. `build.yml` passes the secrets only on `refs/heads/main`, so branch builds never reach the phone. |
| `review/tools/smoke.py` | new, stdlib: runs `build.py`, checks main pages + `/data/*.json` 200 on :8000, key HTML non-empty. |

Not changed: `build.py`, `collect_news.py`, `translate_news.py`, `check_reports.py`. None of the 18
named rules exists in the tree yet (all land in Revs 21–29, 31–33), and existing unnamed warnings
were not given invented names. Each rule's revision adds one line: `uyari.ekle("KUR", "…")`
(`from scripts import uyari` in build.py, `import uyari` in scripts/). DÖRT-DURUM / SİLME-YOK
are in `uyari.BLOKLAYICI`; `ekle` writes before the rule's `sys.exit`, and the flush step runs
under `if: always()`, so blocking failures still reach the phone.

## Operator registration

Two ways in, one in-page panel (a `promptbar` built by `app.js` with the existing classes, so no CSS
changes). Neither uses `alert`/`confirm`/`prompt`:

- **Gesture (works in the installed iPhone app):** tap the footer disclaimer text ("Yalnızca kamuya
  açık kaynaklara dayanır …") **5 times within 3 s**. The panel "Operatör kaydı" opens with a
  password-type field. Enter the code and tap **Kaydet**. The result shows in the panel itself.
- **URL:** `https://defintel.shadovi.com/#operator=<code>`. `app.js` removes the fragment from the
  address bar right away and opens the same panel with the code filled in. Tap **Kaydet**.

**Kaydet** requests notification permission inside that tap if it isn't granted yet (iOS only lets
a tap trigger the permission request). It reuses the device's push subscription or creates one,
then POSTs `subscription.toJSON()` to `/subscribe?rol=operator` with `Authorization: Bearer <code>`.
On success the phone gets "DEFINTEL · test uyarısı". If the panel created the subscription, the
device is also registered as a reader (`/subscribe`), so the bell showing "on" is true.

Why not the bell: each bell tap turns the subscription on or off, and the bell is disabled while
that request runs, so 5 fast taps would flip the reader subscription instead of opening the panel.
The disclaimer is plain text, not a link or control, and it gets `touch-action: manipulation`, so
5 taps don't zoom the page.

The code only exists in the input field (cleared on Kaydet or Kapat) and in local variables. It is
never written to localStorage, the URL, or any file. The fragment is never sent in a request.
Checked in headless Chrome at 375×812: 4 taps do nothing, the 5th opens the panel; `#operator=`
gets prefilled and stripped; localStorage holds only `defintel:visits`; no page errors.

## Secrets / env

- Worker: `NOTIFY_SECRET`, `VAPID_PRIVATE_JWK`, **`OPERATOR_SECRET` (new)** — secrets;
  `SITE_ORIGIN`, `VAPID_SUBJECT`, `VAPID_PUBLIC_KEY` — `[vars]`; KV `SUBS`. Read from `env` in `worker.js`.
- `pull-drive.yml`: `PUSH_URL`, `NOTIFY_SECRET` (existing notify step), `PUSH_URL` + **`OPERATOR_SECRET`** (uyari step), `GDRIVE_SA_KEY`.
- `collect-news.yml`: `GDRIVE_SA_KEY`, `CLAUDE_CODE_OAUTH_TOKEN`, `PUSH_URL` + **`OPERATOR_SECRET`** (uyari step).
- `build.yml`: `PUSH_URL` + **`OPERATOR_SECRET`** (uyari step, main only).
- `worker-test.yml`: none.
- `scripts/uyari.py` reads `PUSH_URL`, `OPERATOR_SECRET`, `GITHUB_STEP_SUMMARY`, `GITHUB_RUN_ID`,
  `GITHUB_REPOSITORY`, `GITHUB_SERVER_URL`, `GITHUB_WORKFLOW`, `RUNNER_TEMP`, optional `UYARI_DOSYASI`.

## Human steps (in order)

```sh
cd worker
S=$(openssl rand -hex 32)
printf %s "$S" | npx wrangler secret put OPERATOR_SECRET
printf %s "$S" | gh secret set OPERATOR_SECRET
printf %s "$S" | pbcopy        # into the password manager; needed once for registration
unset S
npx wrangler deploy
```
Then merge to main (site: `app.js`, `sw.js`), then register the phone as above (on iPhone: first Share → Add to Home Screen, open the installed app, then use the gesture). Optional check from a
shell with both env vars set: `python3 scripts/uyari.py --test`.

## Tests run here

- `python3 build.py` — exit 0.
- `node worker/worker.test.mjs` — 19/19 ok, `✅ OPERATÖR-YALNIZ: sub 0 push · op 1 push`.
- `python3 review/tools/smoke.py` — SMOKE OK.
- Local round trip `uyari.py` → mock worker (node, no real push): two runs with the same warning → 1 push, then 0 (suppressed); wrong secret → 401 reported.
- Leak check: no alert text or `/alert` in `reports/ haberler/ izleme/ data/` or root HTML.

## Notes

- `/notify` still compares against `"Bearer " + env.NOTIFY_SECRET` (brief: `/notify` değişmez); it would accept `Bearer undefined` if that secret were ever unset.
- (A) is the Actions summary page; if the repo is public, so is that page's warning list (the brief sends taps there on purpose).
