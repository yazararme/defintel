// DEFINTEL service worker.
// Pages and the report index: network first, so a new day's report shows up
// as soon as it is published; the cached copy is used only when offline.
// Styles, scripts and icons: served from cache, refreshed in the background.
const CACHE = "defintel-v49";

self.addEventListener("install", () => self.skipWaiting());

self.addEventListener("activate", (event) => {
  event.waitUntil(
    caches.keys()
      .then((keys) => Promise.all(keys.filter((k) => k !== CACHE).map((k) => caches.delete(k))))
      .then(() => self.clients.claim())
  );
});

self.addEventListener("fetch", (event) => {
  const req = event.request;
  const url = new URL(req.url);
  if (req.method !== "GET" || url.origin !== self.location.origin) return;

  const isAsset = url.pathname.includes("/assets/");
  event.respondWith(isAsset ? staleWhileRevalidate(req, event) : networkFirst(req));
});

// A push carries no text. Read the site's own report list and announce the
// newest one, so the notification always matches what is actually published.
self.addEventListener("push", (event) => {
  event.waitUntil(
    (async () => {
      let title = "Yeni rapor";
      let body = "";
      let url = "./index.html";
      try {
        // no-store skips the browser's cache; the query string also makes the
        // CDN treat this as a miss, so the phone can't be told about a report
        // list an edge node is still holding from yesterday.
        const res = await fetch("./data/reports.json?t=" + Date.now(), { cache: "no-store" });
        const list = await res.json();
        if (list.length) {
          const r = list[0];
          // Başlık günü söyler, gövde günün en önemli tek cümlesini. Manşet
          // sekmede ve arşiv kartında zaten var; bildirimde tekrar etmek
          // yerine okuyucuya karar verdirecek cümleyi taşıyoruz.
          const day = new Intl.DateTimeFormat("tr-TR", {
            day: "numeric", month: "long", year: "numeric",
          }).format(new Date(r.date + "T00:00:00"));
          title = r.alarm ? "⚠️ Alarm · " + day : day;
          body = (r.lead || r.summary || r.title || "").slice(0, 120);
          if (r.alarm && r.alarm_title) body = r.alarm_title + " — " + body;
          url = "./" + r.path;
        }
      } catch {
        /* offline: fall back to the generic title */
      }
      await self.registration.showNotification(title, {
        body,
        icon: "./assets/icons/icon-192.png",
        badge: "./assets/icons/icon-192.png",
        tag: "defintel-report",
        data: { url },
      });
    })()
  );
});

self.addEventListener("notificationclick", (event) => {
  event.notification.close();
  const target = new URL(event.notification.data?.url || "./index.html", self.location.href).href;
  event.waitUntil(
    self.clients.matchAll({ type: "window", includeUncontrolled: true }).then((wins) => {
      for (const w of wins) {
        if (w.url.startsWith(self.registration.scope)) return w.focus().then(() => w.navigate(target));
      }
      return self.clients.openWindow(target);
    })
  );
});

async function networkFirst(req) {
  const cache = await caches.open(CACHE);
  try {
    const res = await fetch(req, { cache: "no-store" });
    if (res.ok) cache.put(req, res.clone());
    return res;
  } catch {
    return (await cache.match(req)) || (await cache.match("./index.html")) || Response.error();
  }
}

async function staleWhileRevalidate(req, event) {
  const cache = await caches.open(CACHE);
  const hit = await cache.match(req);
  const refresh = fetch(req).then((res) => {
    if (res.ok) cache.put(req, res.clone());
    return res;
  });
  if (hit) {
    event.waitUntil(refresh.catch(() => {}));
    return hit;
  }
  return refresh;
}
