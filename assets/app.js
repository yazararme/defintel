/* DEFINTEL — client-side arşiv filtresi. İçerik HTML'de hazır; bu yalnızca süzer. */
(function () {
  "use strict";

  var q = document.getElementById("q");
  var tagbar = document.getElementById("tagbar");
  var none = document.getElementById("noresults");
  var entries = Array.prototype.slice.call(document.querySelectorAll(".entry"));
  var active = new Set();

  function norm(s) {
    return (s || "")
      .toLocaleLowerCase("tr")
      .replace(/ı/g, "i")
      .replace(/İ/g, "i");
  }

  function apply() {
    var term = norm(q ? q.value.trim() : "");
    var shown = 0;

    entries.forEach(function (el) {
      var hay = norm(el.getAttribute("data-search"));
      var tags = (el.getAttribute("data-tags") || "").split("|");
      var okText = !term || hay.indexOf(term) !== -1;
      var okTags = active.size === 0 || tags.some(function (t) { return active.has(t); });
      var visible = okText && okTags;
      el.hidden = !visible;
      if (visible) shown++;
    });

    // hide a section kicker whose feed is entirely filtered out
    document.querySelectorAll(".kicker").forEach(function (label) {
      var feed = label.nextElementSibling;
      if (!feed || !feed.classList.contains("feed")) return;
      var any = Array.prototype.some.call(feed.querySelectorAll(".entry"), function (el) {
        return !el.hidden;
      });
      label.hidden = !any;
      feed.hidden = !any;
    });

    if (none) none.hidden = shown !== 0;
  }

  if (q) {
    q.addEventListener("input", apply);
    q.addEventListener("keydown", function (e) {
      if (e.key === "Escape") { q.value = ""; apply(); }
    });
  }

  if (tagbar) {
    tagbar.addEventListener("click", function (e) {
      var btn = e.target.closest(".tag");
      if (!btn) return;
      var tag = btn.getAttribute("data-tag");
      if (active.has(tag)) { active.delete(tag); btn.setAttribute("aria-pressed", "false"); }
      else { active.add(tag); btn.setAttribute("aria-pressed", "true"); }
      apply();
    });
  }

  // "/" focuses search, the way every reader expects
  document.addEventListener("keydown", function (e) {
    if (e.key === "/" && document.activeElement !== q && q) {
      e.preventDefault();
      q.focus();
    }
  });
})();

/* Bildirim düğmesi: yeni rapor yayınlandığında telefona bildirim gönderilmesi için
   tarayıcıyı push servisine kaydeder. Sunucu adresi ve anahtar HTML'den gelir. */
(function () {
  "use strict";

  var btn = document.getElementById("notify");
  if (!btn) return;
  var api = btn.getAttribute("data-push");
  var vapid = btn.getAttribute("data-vapid");
  var supported =
    api && vapid && "serviceWorker" in navigator && "PushManager" in window && "Notification" in window;
  if (!supported) return;

  function keyBytes(base64) {
    var padded = (base64 + "===".slice((base64.length + 3) % 4)).replace(/-/g, "+").replace(/_/g, "/");
    var raw = atob(padded);
    return Uint8Array.from(raw, function (c) { return c.charCodeAt(0); });
  }

  function send(path, sub) {
    return fetch(api + path, {
      method: "POST",
      headers: { "content-type": "application/json" },
      body: JSON.stringify({ endpoint: sub.endpoint }),
    });
  }

  var label = btn.querySelector(".notify-label");

  function paint(state) {
    var text = {
      on: "Bildirimler açık",
      off: "Bildirimler",
      blocked: "Bildirimler kapalı",
      failed: "Bildirim kurulamadı",
    }[state];
    label.textContent = text;
    btn.setAttribute("aria-pressed", state === "on" ? "true" : "false");
    btn.setAttribute("data-state", state);
    btn.title =
      state === "on"
        ? "Yeni rapor yayınlandığında bu cihaza bildirim gelir. Kapatmak için dokun."
        : state === "blocked"
        ? "Bildirim izni reddedilmiş. Cihaz ayarlarından açabilirsin."
        : "Yeni rapor yayınlandığında bu cihaza bildirim gönderilsin.";
    btn.hidden = false;
  }

  navigator.serviceWorker.ready.then(function (reg) {
    reg.pushManager.getSubscription().then(function (sub) {
      paint(sub ? "on" : Notification.permission === "denied" ? "blocked" : "off");

      btn.addEventListener("click", function () {
        btn.disabled = true;
        reg.pushManager
          .getSubscription()
          .then(function (current) {
            if (current) {
              return send("/unsubscribe", current)
                .then(function () { return current.unsubscribe(); })
                .then(function () { paint("off"); });
            }
            return Notification.requestPermission().then(function (permission) {
              if (permission !== "granted") {
                paint("blocked");
                return;
              }
              return reg.pushManager
                .subscribe({ userVisibleOnly: true, applicationServerKey: keyBytes(vapid) })
                .then(function (fresh) { return send("/subscribe", fresh); })
                .then(function () { paint("on"); });
            });
          })
          .catch(function () { paint("failed"); })
          .then(function () { btn.disabled = false; });
      });
    });
  });
})();
