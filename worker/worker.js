// DEFINTEL push service.
//
// Two jobs:
//   POST /subscribe    a reader's browser registers for notifications
//   POST /notify       the publish workflow says a new report is out (needs the secret)
//   POST /test         a device asks for a push to itself, and only to itself
//
// Pushes carry no payload. The service worker wakes up, reads the site's own
// report list and builds the notification from it, so no report text ever
// passes through here.

const PUSH_SERVICES = [
  "android.googleapis.com",
  "fcm.googleapis.com",
  "updates.push.services.mozilla.com",
  "push.apple.com",
  "notify.windows.com",
  "wns2-", // windows regional hosts
];

export default {
  async fetch(request, env) {
    const path = new URL(request.url).pathname;

    if (request.method === "OPTIONS") return cors(new Response(null, { status: 204 }), env);
    if (request.method !== "POST") return cors(new Response("not found", { status: 404 }), env);

    if (path === "/subscribe") return cors(await subscribe(request, env), env);
    if (path === "/unsubscribe") return cors(await unsubscribe(request, env), env);
    if (path === "/test") return cors(await test(request, env), env);
    if (path === "/notify") return notify(request, env);
    return cors(new Response("not found", { status: 404 }), env);
  },
};

function cors(res, env) {
  const h = new Headers(res.headers);
  h.set("Access-Control-Allow-Origin", env.SITE_ORIGIN);
  h.set("Access-Control-Allow-Methods", "POST, OPTIONS");
  h.set("Access-Control-Allow-Headers", "content-type");
  h.set("Access-Control-Max-Age", "86400");
  return new Response(res.body, { status: res.status, headers: h });
}

async function keyFor(endpoint) {
  const digest = await crypto.subtle.digest("SHA-256", new TextEncoder().encode(endpoint));
  return "sub:" + b64url(new Uint8Array(digest));
}

function allowedEndpoint(endpoint) {
  try {
    const u = new URL(endpoint);
    return u.protocol === "https:" && PUSH_SERVICES.some((h) => u.hostname.includes(h));
  } catch {
    return false;
  }
}

async function subscribe(request, env) {
  const sub = await request.json().catch(() => null);
  if (!sub?.endpoint || !allowedEndpoint(sub.endpoint)) {
    return new Response("bad subscription", { status: 400 });
  }
  await env.SUBS.put(await keyFor(sub.endpoint), JSON.stringify({ endpoint: sub.endpoint }));
  return new Response(null, { status: 204 });
}

async function unsubscribe(request, env) {
  const sub = await request.json().catch(() => null);
  if (!sub?.endpoint) return new Response("bad subscription", { status: 400 });
  await env.SUBS.delete(await keyFor(sub.endpoint));
  return new Response(null, { status: 204 });
}

// Aboneliğin çalıştığını yarını beklemeden görmenin tek dürüst yolu: gerçek
// bir push. Sır gerekmiyor çünkü uç nokta adresinin kendisi zaten tahmin
// edilemez bir yetki belgesi — onu bilen cihazın kendisidir, ve yalnızca
// KV'de kayıtlı bir adrese gönderiyoruz. Yayın akışının /notify'ı herkese
// gider; bu yalnızca isteyene.
async function test(request, env) {
  const sub = await request.json().catch(() => null);
  if (!sub?.endpoint || !allowedEndpoint(sub.endpoint)) {
    return new Response("bad subscription", { status: 400 });
  }
  const key = await keyFor(sub.endpoint);
  if (!(await env.SUBS.get(key))) return new Response("not subscribed", { status: 404 });

  const status = await push(sub.endpoint, env);
  if (status === 404 || status === 410) {
    await env.SUBS.delete(key);
    return Response.json({ ok: false, status, removed: true });
  }
  return Response.json({ ok: status < 300, status });
}

async function notify(request, env) {
  if (request.headers.get("Authorization") !== "Bearer " + env.NOTIFY_SECRET) {
    return new Response("unauthorized", { status: 401 });
  }

  let sent = 0;
  let gone = 0;
  let cursor;
  do {
    const page = await env.SUBS.list({ prefix: "sub:", cursor });
    cursor = page.list_complete ? undefined : page.cursor;
    for (const { name } of page.keys) {
      const stored = await env.SUBS.get(name, "json");
      if (!stored) continue;
      const status = await push(stored.endpoint, env);
      if (status === 404 || status === 410) {
        await env.SUBS.delete(name);
        gone++;
      } else if (status < 300) {
        sent++;
      }
    }
  } while (cursor);

  return Response.json({ sent, removed: gone });
}

async function push(endpoint, env) {
  const res = await fetch(endpoint, {
    method: "POST",
    headers: {
      TTL: "86400",
      Urgency: "normal",
      Authorization: await vapidHeader(new URL(endpoint).origin, env),
      "Content-Length": "0",
    },
  });
  return res.status;
}

async function vapidHeader(audience, env) {
  const jwk = JSON.parse(env.VAPID_PRIVATE_JWK);
  const key = await crypto.subtle.importKey(
    "jwk",
    { ...jwk, key_ops: ["sign"], ext: true },
    { name: "ECDSA", namedCurve: "P-256" },
    false,
    ["sign"]
  );
  const header = b64urlText(JSON.stringify({ typ: "JWT", alg: "ES256" }));
  const body = b64urlText(
    JSON.stringify({
      aud: audience,
      exp: Math.floor(Date.now() / 1000) + 12 * 60 * 60,
      sub: env.VAPID_SUBJECT,
    })
  );
  const signature = await crypto.subtle.sign(
    { name: "ECDSA", hash: "SHA-256" },
    key,
    new TextEncoder().encode(`${header}.${body}`)
  );
  return `vapid t=${header}.${body}.${b64url(new Uint8Array(signature))}, k=${env.VAPID_PUBLIC_KEY}`;
}

function b64url(bytes) {
  let s = "";
  for (const b of bytes) s += String.fromCharCode(b);
  return btoa(s).replace(/\+/g, "-").replace(/\//g, "_").replace(/=+$/, "");
}

function b64urlText(text) {
  return b64url(new TextEncoder().encode(text));
}
