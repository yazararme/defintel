/* DEFINTEL — client-side arşiv filtresi. İçerik HTML'de hazır; bu yalnızca süzer. */
(function () {
  "use strict";

  var q = document.getElementById("q");
  var none = document.getElementById("noresults");
  var entries = Array.prototype.slice.call(document.querySelectorAll(".entry"));

  function norm(s) {
    return (s || "").toLocaleLowerCase("tr").replace(/ı/g, "i").replace(/İ/g, "i");
  }

  function apply() {
    var term = norm(q ? q.value.trim() : "");
    var shown = 0;

    entries.forEach(function (el) {
      var visible = !term || norm(el.getAttribute("data-search")).indexOf(term) !== -1;
      el.hidden = !visible;
      if (visible) shown++;
    });

    if (none) none.hidden = shown !== 0;
  }

  if (q) {
    q.addEventListener("input", apply);
    q.addEventListener("keydown", function (e) {
      if (e.key === "Escape") { q.value = ""; apply(); }
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

/* Kurulum daveti, bildirim izni ve zil düğmesi.
   Sıra önemli: önce uygulamayı kurdur, bildirimi ancak kurulu uygulamada iste —
   iOS'ta Notification API sekmede zaten yok, yalnızca ana ekrana eklenmiş
   uygulamada var. */
(function () {
  "use strict";

  var api = document.body.getAttribute("data-push");
  var vapid = document.body.getAttribute("data-vapid");
  var pushReady =
    api && vapid && "serviceWorker" in navigator && "PushManager" in window && "Notification" in window;

  var DAY = 86400000;

  function snoozed(key, days) {
    try {
      var until = Number(localStorage.getItem(key) || 0);
      return Date.now() < until;
    } catch (e) {
      return false;
    }
  }

  function snooze(key, days) {
    try {
      localStorage.setItem(key, String(Date.now() + days * DAY));
    } catch (e) {
      /* private mode: just don't remember */
    }
  }

  function installed() {
    return (
      (window.matchMedia && window.matchMedia("(display-mode: standalone)").matches) ||
      navigator.standalone === true
    );
  }

  function isIOS() {
    return (
      /iPad|iPhone|iPod/.test(navigator.userAgent) ||
      (/Macintosh/.test(navigator.userAgent) && navigator.maxTouchPoints > 1)
    );
  }

  /* ---------- kurulum daveti ---------- */

  var bar = document.getElementById("installbar");
  var deferred = null;

  function showBar(kind) {
    if (!bar || installed() || snoozed("defintel:install")) return;
    bar.setAttribute("data-kind", kind);
    bar.hidden = false;
  }

  function hideBar(remember) {
    if (!bar) return;
    bar.hidden = true;
    if (remember) snooze("defintel:install", 30);
  }

  if (bar && !installed()) {
    var engaged = false;
    var kind = isIOS() ? "ios" : "manual";

    window.addEventListener("beforeinstallprompt", function (e) {
      e.preventDefault();
      deferred = e;          // Chrome kurulabilirlik denetimini geçtiyse gelir
      kind = "chrome";
      if (engaged) showBar(kind);
    });

    window.addEventListener("appinstalled", function () {
      deferred = null;
      hideBar(false);
    });

    var engage = function () {
      if (engaged) return;
      engaged = true;
      // Chrome olayı sayfa açılışında biraz gecikebiliyor; ona pay bırak
      setTimeout(function () { showBar(deferred ? "chrome" : kind); }, 1200);
    };
    setTimeout(engage, 12000);
    window.addEventListener("scroll", function onScroll() {
      if (window.scrollY > 400) { window.removeEventListener("scroll", onScroll); engage(); }
    }, { passive: true });

    bar.addEventListener("click", function (e) {
      var action = e.target.closest("[data-action]");
      if (!action) return;
      if (action.getAttribute("data-action") === "close") return hideBar(true);
      if (deferred) {
        deferred.prompt();
        deferred.userChoice.then(function () { deferred = null; hideBar(false); });
      }
    });
  }

  /* ---------- bildirim: abonelik işlemleri ---------- */

  function keyBytes(base64) {
    var padded = (base64 + "===".slice((base64.length + 3) % 4)).replace(/-/g, "+").replace(/_/g, "/");
    var raw = atob(padded);
    return Uint8Array.from(raw, function (c) { return c.charCodeAt(0); });
  }

  function tell(path, sub) {
    return fetch(api + path, {
      method: "POST",
      headers: { "content-type": "application/json" },
      body: JSON.stringify({ endpoint: sub.endpoint }),
    });
  }

  function subscribe() {
    return navigator.serviceWorker.ready.then(function (reg) {
      return Notification.requestPermission().then(function (permission) {
        if (permission !== "granted") return "blocked";
        return reg.pushManager
          .subscribe({ userVisibleOnly: true, applicationServerKey: keyBytes(vapid) })
          .then(function (sub) { return tell("/subscribe", sub); })
          .then(function () { return "on"; });
      });
    });
  }

  function unsubscribe() {
    return navigator.serviceWorker.ready
      .then(function (reg) { return reg.pushManager.getSubscription(); })
      .then(function (sub) {
        if (!sub) return "off";
        return tell("/unsubscribe", sub)
          .then(function () { return sub.unsubscribe(); })
          .then(function () { return "off"; });
      });
  }

  /* ---------- bildirim: kurulu uygulamadaki ilk davet ---------- */

  var card = document.getElementById("notifycard");

  if (card && pushReady && installed() && Notification.permission === "default" && !snoozed("defintel:notify")) {
    navigator.serviceWorker.ready.then(function (reg) {
      return reg.pushManager.getSubscription();
    }).then(function (sub) {
      if (sub) return;
      card.hidden = false;
      card.addEventListener("click", function (e) {
        var action = e.target.closest("[data-action]");
        if (!action) return;
        if (action.getAttribute("data-action") === "later") {
          card.hidden = true;
          return snooze("defintel:notify", 7);
        }
        subscribe().then(function (state) {
          card.hidden = true;
          paint(state);
        });
      });
    });
  }

  /* ---------- zil düğmesi ---------- */

  var btn = document.getElementById("notify");
  var label = btn && btn.querySelector(".notify-label");

  function paint(state) {
    if (!btn) return;
    label.textContent = {
      on: "Bildirimler açık",
      off: "Bildirimler",
      blocked: "Bildirimler kapalı",
      failed: "Bildirim kurulamadı",
    }[state];
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

  if (btn && pushReady) {
    navigator.serviceWorker.ready
      .then(function (reg) { return reg.pushManager.getSubscription(); })
      .then(function (sub) {
        paint(sub ? "on" : Notification.permission === "denied" ? "blocked" : "off");

        btn.addEventListener("click", function () {
          btn.disabled = true;
          var busy = btn.getAttribute("aria-pressed") === "true" ? unsubscribe() : subscribe();
          busy
            .then(paint)
            .catch(function () { paint("failed"); })
            .then(function () { btn.disabled = false; });
        });
      });
  }
})();
