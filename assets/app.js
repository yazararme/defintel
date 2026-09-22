/* DEFINTEL — client-side arşiv filtresi. İçerik HTML'de hazır; bu yalnızca süzer. */
(function () {
  "use strict";

  var q = document.getElementById("q");
  var none = document.getElementById("noresults");
  // arşivde .entry kartları, kupür sayfasında .clip satırları — ikisi de data-search taşır
  var rows = Array.prototype.slice.call(document.querySelectorAll("[data-search]"));
  // duruş hâli HTML'de yazılı; süzme bitince oraya dönmek için bir kez okunuyor
  var folds = Array.prototype.slice.call(document.querySelectorAll("details"));
  var resting = folds.map(function (el) { return el.open; });

  function norm(s) {
    return (s || "").toLocaleLowerCase("tr").replace(/ı/g, "i").replace(/İ/g, "i");
  }

  function apply() {
    var term = norm(q ? q.value.trim() : "");
    var shown = 0;

    if (!term) folds.forEach(function (el, i) { el.open = resting[i]; });

    rows.forEach(function (el) {
      var visible = !term || norm(el.getAttribute("data-search")).indexOf(term) !== -1;
      el.hidden = !visible;
      if (!visible) return;
      shown++;
      // Eşleşme özetin içinde olabilir, üstelik satır kapalı bir bölümün içinde
      // durabilir: satırı ve onu saran bölümleri aç, temizlenince hepsi geri döner.
      if (term) {
        for (var p = el; p; p = p.parentElement) {
          if (p.tagName === "DETAILS") p.open = true;
        }
      }
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
    }).then(function (res) {
      // fetch yalnızca ağ koptuğunda reddeder; 500 de "başarılı" sayılıyordu ve
      // düğme, sunucunun hiç duymadığı bir aboneliği "açık" diye boyuyordu.
      if (!res.ok) throw new Error(path + " " + res.status);
      return res;
    });
  }

  function subscribe() {
    return navigator.serviceWorker.ready.then(function (reg) {
      return Notification.requestPermission().then(function (permission) {
        if (permission !== "granted") return "blocked";
        return reg.pushManager
          .subscribe({ userVisibleOnly: true, applicationServerKey: keyBytes(vapid) })
          .then(function (sub) {
            // Sunucu kaydı alamadıysa tarayıcıdaki abonelik de kalmamalı:
            // kalırsa bir sonraki açılışta getSubscription() onu görür, düğme
            // "açık" boyanır ve hiçbir zaman bildirim gelmez.
            return tell("/subscribe", sub).catch(function (err) {
              return sub.unsubscribe().then(function () { throw err; });
            });
          })
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

  function cardSays(text, primary) {
    if (!card) return;
    card.querySelector('[data-role="head"]').textContent = text[0];
    card.querySelector('[data-role="body"]').textContent = text[1];
    card.querySelector('[data-action="enable"]').textContent = primary;
    // "Şimdi değil" arıza hâlinde "Kapat" olur: ertelenecek bir teklif yok,
    // kapatılacak bir arıza var.
    card.querySelector('[data-action="later"]').textContent = "Kapat";
    card.setAttribute("data-state", "failed");
  }

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
          // Erteleme yalnızca açık bir "Şimdi değil"de yazılır. Arızadan
          // sonraki "Kapat" bir tercih değil, hatayı kapatmadır — yedi gün
          // sessizlik yazmaz.
          if (card.getAttribute("data-state") !== "failed") snooze("defintel:notify", 7);
          return;
        }

        var enable = card.querySelector('[data-action="enable"]');
        enable.disabled = true;
        subscribe()
          .catch(function () { return "failed"; })
          .then(function (state) {
            enable.disabled = false;
            // Sonuç, eylemin olduğu yerde bildirilir. Kart ekranın altında
            // sabit duruyor; dokunma anında okuyucunun gözü orada, zil ise
            // büyük olasılıkla görüş alanı dışında — görünmeyen bir kontrole
            // boya basmak hiç basmamakla aynı şey.
            if (state === "on") {
              card.hidden = true;     // durum artık zilde görünür
            } else {
              cardSays(
                state === "blocked"
                  ? ["Bildirim izni verilmedi", "Cihaz ayarlarından izin verip tekrar deneyebilirsin."]
                  : ["Bildirim açılamadı", "Bağlantı ya da sunucu sorunu olabilir; tekrar dene."],
                "Tekrar dene"
              );
              // Arıza erteleme yazmaz: sunucu hatası için okuyucuyu yedi gün
              // karanlığa göndermek onu cezalandırmak olur.
            }
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
      // Kapalı etiket bir isim değil bir teklif: okuyucunun
      // kazanacağı şeyi söyler, kontrolün adını değil.
      off: "Yeni rapor bildirimi al",
      blocked: "Bildirimler kapalı",
      failed: "Bildirim kurulamadı",
      "failed-off": "Bildirim kapatılamadı",
    }[state];
    // Açıkken zil tek başına yetiyor; etiket CSS'te görsel olarak gizleniyor ama
    // DOM'da kalıyor, yoksa düğmenin erişilebilir adı yok olur.
    // Sınıf görünüşü, aria-pressed gerçeği söyler ve burada ikisi ayrışır:
    // "failed-off"ta abonelik hâlâ ayakta (basılı), ama zil "açık" görünümüne
    // geçerse etiket CSS'te gizlenir ve hata mesajı ekrandan kalkar. Etiket
    // kalsın, sonraki dokunuş da açmayı değil kapatmayı tekrar denesin.
    btn.classList.toggle("notify--on", state === "on");
    btn.setAttribute("aria-pressed", state === "on" || state === "failed-off" ? "true" : "false");
    btn.setAttribute("data-state", state);
    btn.title =
      state === "on"
        ? "Yeni rapor yayınlandığında bu cihaza bildirim gelir. Kapatmak için dokun."
        : state === "blocked"
        ? "Bildirim izni reddedilmiş. Cihaz ayarlarından açabilirsin."
        : state === "failed-off"
        ? "Abonelik sunucuda duruyor, bildirim gelmeye devam eder. Tekrar dene."
        : state === "failed"
        ? "Abonelik kurulamadı, bildirim gelmeyecek. Tekrar dene."
        : "Yeni rapor yayınlandığında bu cihaza bildirim gönderilsin.";
    btn.hidden = false;
  }

  if (btn && pushReady) {
    navigator.serviceWorker.ready
      .then(function (reg) { return reg.pushManager.getSubscription(); })
      .then(function (sub) {
        paint(Notification.permission === "denied" ? "blocked" : sub ? "on" : "off");

        btn.addEventListener("click", function () {
          btn.disabled = true;
          // Kapatma hatası ile açma hatası aynı şey değil: biri "bildirim
          // gelmeyecek", diğeri "gelmeye devam edecek" demek. Etiket ikisini
          // ayırmazsa okuyucu yanlış olanı doğru sanır.
          var on = btn.getAttribute("aria-pressed") === "true";
          (on
            ? unsubscribe().catch(function () { return "failed-off"; })
            : subscribe().catch(function () { return "failed"; })
          )
            .then(paint)
            .then(function () { btn.disabled = false; });
        });
      });
  }
})();

/* Rapor gezinme şeridi: çipten çapaya git, katlı grupları aç, bağlantı kopyala. */
(function () {
  "use strict";

  // brifingdeki devnav ya da medya sayfasındaki catbar; ikisi de aynı şerit
  var nav = document.querySelector(".devnav");

  function flash(el) {
    el.classList.add("flash");
    setTimeout(function () { el.classList.remove("flash"); }, 2000);
  }

  function goTo(id, push) {
    var el = document.getElementById(id);
    if (!el) return;
    var before = window.scrollY;
    // scroll-margin-top (CSS) keeps the sticky strip from covering the target
    try {
      el.scrollIntoView({ behavior: "smooth", block: "start" });
    } catch (err) {
      el.scrollIntoView();
    }
    // Smooth kaydırma bazı ortamlarda sessizce hiç çalışmıyor: çip tıklanıyor,
    // sayfa yerinde kalıyor. Kımıldamadıysa anında git — bir çipin hiçbir şey
    // yapmaması, animasyonsuz gitmesinden kötü.
    setTimeout(function () {
      if (Math.abs(window.scrollY - before) < 2 &&
          Math.abs(el.getBoundingClientRect().top) > 80) {
        el.scrollIntoView({ block: "start" });
      }
    }, 350);
    flash(el);
    if (push && history.replaceState) history.replaceState(null, "", "#" + id);
  }

  if (nav) {
    nav.addEventListener("click", function (e) {
      var chip = e.target.closest("a.chip");
      if (chip) {
        e.preventDefault();
        goTo(chip.getAttribute("href").slice(1), true);
      }
    });
  }

  // #g9 gibi katlı bir gruptaki çapayla açılırsa grubu aç ve hedefe git
  function fromHash() {
    var id = (location.hash || "").slice(1);
    if (!id || !document.getElementById(id)) return;
    setTimeout(function () { goTo(id, false); }, 60);

    // Web fonts land after the first paint and move everything down a little;
    // line the target up again once they are in.
    if (document.fonts && document.fonts.ready) {
      document.fonts.ready.then(function () {
        var el = document.getElementById(id);
        if (el) el.scrollIntoView({ block: "start" });
      });
    }
  }

  window.addEventListener("hashchange", fromHash);
  fromHash();

  // gövde içindeki atıf bağlantıları da yumuşak kaydırsın
  document.addEventListener("click", function (e) {
    var xref = e.target.closest("a.xref, a.gbadge");
    if (xref && xref.getAttribute("href").charAt(0) === "#") {
      e.preventDefault();
      goTo(xref.getAttribute("href").slice(1), true);
    }
  });

  // "bağlantıyı kopyala": çapalı tam adres
  document.addEventListener("click", function (e) {
    var btn = e.target.closest(".copylink");
    if (!btn) return;
    var url = location.origin + location.pathname + "#" + btn.getAttribute("data-anchor");
    var done = function () {
      btn.classList.add("copied");
      setTimeout(function () { btn.classList.remove("copied"); }, 1600);
    };
    if (navigator.clipboard && navigator.clipboard.writeText) {
      navigator.clipboard.writeText(url).then(done, function () {});
    } else {
      var tmp = document.createElement("input");
      tmp.value = url;
      document.body.appendChild(tmp);
      tmp.select();
      try { document.execCommand("copy"); done(); } catch (err) {}
      document.body.removeChild(tmp);
    }
  });
})();
