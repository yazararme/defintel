/* DEFINTEL — client-side arşiv filtresi. İçerik HTML'de hazır; bu yalnızca süzer. */

/* Oyuncu süzgeci hapı.

   Brifingin "Oyuncular" satırından ya da Oyuncular sayfasından gelen bağlantı
   ?oyuncu=<kimlik> taşıyor. Eskiden ?q=<ad> ile geliyordu ve arama kutusuna
   adı yazıyordu — iki sorun: kutuda bir şey yazıyor olması okuyucuya "bunu ben
   yazdım" dedirtiyor, ve ad üzerinden arama "Bayraktar" başlığını Baykar
   süzgecinden kaçırıyordu. Kimlik eşleşmesi build'de yapıldı; sayfa yalnız
   onu okuyor. Kutu boş kalıyor ve süzgecin varlığı hapta duruyor. */
function playerPill(label, onRemove) {
  var host = document.querySelector(".controls");
  if (!host) return null;
  var old = document.querySelector(".pill-wrap");
  if (old) old.remove();
  var wrap = document.createElement("div");
  wrap.className = "pill-wrap";
  var pill = document.createElement("span");
  pill.className = "pill";
  var text = document.createElement("span");
  text.className = "pill-label";
  text.textContent = label;
  var x = document.createElement("button");
  x.type = "button";
  x.className = "pill-x";
  x.setAttribute("aria-label", "Filtreyi kaldır");
  x.textContent = "×";
  x.addEventListener("click", onRemove);
  pill.appendChild(text);
  pill.appendChild(x);
  wrap.appendChild(pill);
  host.parentNode.insertBefore(wrap, host.nextSibling);
  return wrap;
}

function readParam(name) {
  try { return new URLSearchParams(location.search).get(name) || ""; }
  catch (err) { return ""; }
}

function dropParam(name, push) {
  try {
    var u = new URL(location.href);
    u.searchParams.delete(name);
    var next = u.pathname + (u.search || "") + u.hash;
    // pushState, replaceState değil: "× sonrası geri tuşu süzülmüş hâle
    // dönsün" ancak yeni bir geçmiş kaydıyla mümkün. replaceState bulunulan
    // kaydı ezer ve geri tuşu bir önceki *sayfaya* gider.
    if (history.pushState) history[push ? "pushState" : "replaceState"](null, "", next);
  } catch (err) { /* geçmiş API'si yoksa adres olduğu gibi kalır */ }
}

/* Kimlik → görünen ad. Hem kupür sayfası hem arşiv aynı dosyayı okuyor. */
var playerIndex = null;
function loadPlayers() {
  if (playerIndex) return playerIndex;
  playerIndex = fetch("/data/oyuncular.json", { cache: "no-store" })
    .then(function (r) { return r.json(); })
    .catch(function () { return {}; });
  return playerIndex;
}
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

  // Oyuncu kapsamı: null ise herkes. Metin süzgeciyle VE'leniyor — hap
  // duruyorken kutuya yazmak hapın satırları içinde daraltır, dışına çıkmaz.
  var scope = "";
  function inScope(el) {
    if (!scope) return true;
    var host = el.hasAttribute("data-oyuncu") ? el : el.closest("[data-oyuncu]");
    if (!host) return false;
    return (host.getAttribute("data-oyuncu") || "").split(/\s+/).indexOf(scope) !== -1;
  }

  function apply() {
    var term = norm(q ? q.value.trim() : "");
    var shown = 0;

    if (!term) folds.forEach(function (el, i) { el.open = resting[i]; });

    rows.forEach(function (el) {
      var visible = inScope(el) &&
        (!term || norm(el.getAttribute("data-search")).indexOf(term) !== -1);
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
    retally(!!term || !!scope);
    rescope(!!term || !!scope);
  }

  /* Kapsam satırı süzgeçle yeniden sayılır (Rev 22, Rev 18b'nin yasası):
     süzgeç açıkken "536 başlık" süzülmemiş sayfayı anlatır, altındaki liste
     başka bir şeyi. Pay "görünen": okurun listede gördüğü satırlar — bölüm
     sayılarının toplamı. Aynı başlık iki bölümde duruyorsa (ör. İhale ve
     Türk sanayii kesiti) iki kez görünür ve iki kez sayılır; pay ile
     bölüm sayıları birbirini tutar (Rev 22 kabulü: ?oyuncu=roketsan →
     "2 / 536"). Payda değişmez: günün tekil başlık sayısı. */
  var stat = document.querySelector(".news-stat > .num");
  var statRest = stat ? stat.textContent : "";
  function rescope(active) {
    if (!stat) return;
    if (!active) { stat.textContent = statRest; return; }
    var n = rows.filter(function (el) { return !el.hidden; }).length;
    stat.textContent = n + " / " + statRest;
  }

  /* Süzme açıkken bölüm sayıları ve gezinme sayıları da süzülmüş olanı
     göstermeli. Eskiden "C-UAS ve Hava Savunma 25" yazıp altında hiçbir
     satır olmuyordu: sayı sayfanın süzülmemiş hâlini anlatıyor, bağlantı
     da boş bir başlığa gidiyordu. Bir sayı neyi saydığını söylemiyorsa
     yanlış sayıdır. */
  var secs = {};
  rows.forEach(function (el) {
    // Özetli satırda data-sec saran <li>'de, özetsizde satırın kendisinde.
    var host = el.hasAttribute("data-sec") ? el : el.closest("[data-sec]");
    var id = host && host.getAttribute("data-sec");
    if (id) (secs[id] = secs[id] || []).push(el);
  });
  var navs = Array.prototype.slice.call(
    document.querySelectorAll(".news-rail-row, .catbar .chip"));
  var counters = {};
  Object.keys(secs).forEach(function (id) {
    var head = document.getElementById(id);
    counters[id] = {
      head: head,
      badge: head && head.querySelector(".kicker-count"),
      navs: navs.filter(function (a) { return a.getAttribute("href") === "#" + id; })
    };
    if (counters[id].badge) counters[id].rest = counters[id].badge.textContent;
  });

  /* Başlığın gövdesi: bölüm bir kapsayıcı değil, h2 + kardeşleri.
     Yürüyüş #noresults'ta durur (Rev 22): o paragraf son bölümün kardeşi ama
     hiçbir bölüme ait değil. Eskiden son bölüm boşalınca onu da gizliyordu —
     "sonuç yok" tam da görünmesi gerektiği anda kayboluyor, sayfa boş kalıyordu. */
  function sectionParts(head) {
    if (!head) return [];
    if (head.tagName === "SECTION") return [head];
    if (head.tagName === "SUMMARY") return [head.parentElement];
    var out = [head];
    for (var el = head.nextElementSibling; el; el = el.nextElementSibling) {
      if (el.id === "noresults") break; /* DÖRT-DURUM:noresults */
      if (el.tagName === "H2" || el.tagName === "SECTION") break;
      out.push(el);
    }
    return out;
  }

  function retally(active) {
    Object.keys(counters).forEach(function (id) {
      var c = counters[id];
      var live = secs[id].filter(function (el) { return !el.hidden; }).length;
      if (c.badge) c.badge.textContent = active ? live : c.rest;
      var empty = active && live === 0;
      sectionParts(c.head).forEach(function (el) { el.hidden = empty; });
      c.navs.forEach(function (a) {
        a.hidden = empty;
        var n = a.querySelector(".num, .chip-count");
        if (n) n.textContent = active ? live : c.rest;
      });
    });
  }

  if (q) {
    q.addEventListener("input", apply);
    q.addEventListener("keydown", function (e) {
      if (e.key === "Escape") { q.value = ""; apply(); }
    });
  }

  // ?q= düz metin için duruyor (paylaşılan aramalar); oyuncu bağlantıları
  // artık ?oyuncu=<kimlik> ile geliyor ve kutuya dokunmuyor.
  function applyUrl(first) {
    var who = readParam("oyuncu");
    var want = readParam("q");
    // Kapsam yalnız kupür sayfasında satır süzer. Arşivde gün kartları
    // data-oyuncu taşımıyor, kapsamı aşağıdaki scopeDays() uyguluyor; burada da
    // uygulanınca her kart gizleniyor ve kartlar geri gelse de "eşleşen rapor
    // yok" ekranda kalıyordu (Rev 22: sonuç varken "sonuç yok").
    scope = document.querySelector(".clips") ? who : "";
    var existing = document.querySelector(".pill-wrap");
    if (existing) existing.remove();
    if (who && document.querySelector(".clips")) {
      loadPlayers().then(function (index) {
        var entry = index[who];
        playerPill((entry && entry.ad) || who, function () {
          dropParam("oyuncu", true);
          scope = "";
          var w = document.querySelector(".pill-wrap");
          if (w) w.remove();
          apply();
        });
      });
    }
    if (want) q.value = want;
    else if (first) q.value = "";
    apply();
    if (want && document.querySelector(".clips")) {
      var hit = rows.filter(function (el) { return !el.hidden; })[0];
      if (hit) setTimeout(function () { hit.scrollIntoView({ block: "center" }); }, 60);
    }
  }

  if (q) {
    // setTimeout: arşivin içerik araması dosyanın altında, dinleyicisini
    // henüz kurmamış oluyor; "input" olayı ona da ulaşsın.
    setTimeout(function () {
      applyUrl(true);
      if (readParam("q")) q.dispatchEvent(new Event("input", { bubbles: true }));
    }, 0);
    window.addEventListener("popstate", function () { applyUrl(false); });
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

  /* ---------- bildirim: brifingin sonundaki davet ---------- */

  // R29 (F-03/F-14): kart ilk ziyarette de çıkar ve ekranın altına sabitlenmez;
  // sayfa akışında, sayfa sonu gezinmesinin (.endnav) hemen üstünde durur. Eskiden
  // ikinci ziyareti bekleyip alta yapışıyordu: ilk okuyucu teklifi hiç görmüyor,
  // gören de kartın altında kalan footer zilini göremiyordu. Okumayı bitiren
  // okuyucu kartla orada karşılaşır; zil footer'da görünür kalır.
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

  // iOS'ta Notification API yalnızca ana ekrana eklenmiş uygulamada var, o
  // yüzden orada kurulum şart kalıyor. Android ve masaüstünde tarayıcı
  // sekmesi yeterli: kurulum basamağını beklemek hunideki en büyük kayıptı.
  var cardEligible = pushReady && (installed() || !isIOS());

  if (card && cardEligible && Notification.permission === "default" && !snoozed("defintel:notify")) {
    navigator.serviceWorker.ready.then(function (reg) {
      return reg.pushManager.getSubscription();
    }).then(function (sub) {
      if (sub) return;
      var endnav = document.querySelector(".endnav");
      if (endnav) endnav.parentNode.insertBefore(card, endnav);
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
            // Sonuç, eylemin olduğu yerde bildirilir: dokunma anında
            // okuyucunun gözü kartta, zil ise büyük olasılıkla görüş alanı
            // dışında — görünmeyen bir kontrole boya basmak hiç basmamakla
            // aynı şey.
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

  function openAncestors(el) {
    // Hedef kapalı bir katlamanın içindeyse önce onu aç: kaynakça ve
    // "bekleyen başlıklar" katlandıktan sonra [K3] ya da bir izleme adı
    // hâlâ oraya götürmeli, yol kısalmamalı.
    for (var p = el; p; p = p.parentElement) {
      if (p.tagName === "DETAILS" && !p.open) p.open = true;
    }
  }

  /* Kaydırılabilir hedef: çapanın kendisi gizli olabilir.

     KAYNAKLAR ve EK katlandıktan sonra bölüm başlığı <h2 hidden id="kaynaklar">
     olarak duruyor — id orada kalıyor ki şerit çipini türetebilsin, ama hidden
     bir öğenin kutusu yok ve scrollIntoView hiçbir şey yapmıyor. Çip basılıyor,
     sayfa yerinde kalıyordu. Görünen en yakın ata (burada <details>) hedefin
     durduğu yer. */
  function scrollTarget(el) {
    var t = el;
    while (t && t !== document.body && !t.getClientRects().length) t = t.parentElement;
    return t || el;
  }

  function goTo(id, push) {
    var el = document.getElementById(id);
    if (!el) return;
    openAncestors(el);
    var before = window.scrollY;
    var target = scrollTarget(el);
    // scroll-margin-top (CSS) keeps the sticky strip from covering the target
    try {
      target.scrollIntoView({ behavior: "smooth", block: "start" });
    } catch (err) {
      target.scrollIntoView();
    }
    // Smooth kaydırma bazı ortamlarda sessizce hiç çalışmıyor: çip tıklanıyor,
    // sayfa yerinde kalıyor. Kımıldamadıysa anında git — bir çipin hiçbir şey
    // yapmaması, animasyonsuz gitmesinden kötü.
    setTimeout(function () {
      if (Math.abs(window.scrollY - before) < 2 &&
          Math.abs(target.getBoundingClientRect().top) > 80) {
        target.scrollIntoView({ block: "start" });
      }
    }, 350);
    flash(target);
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

  // Belge içi her çapa aynı yoldan gider: katlamayı aç, sonra kaydır.
  // Tarayıcının kendi atlaması kapalı <details> içini bulamıyor.
  document.addEventListener("click", function (e) {
    var a = e.target.closest && e.target.closest('a[href^="#"]');
    if (!a || a.closest(".devnav")) return;     // şerit kendi işleyicisinde
    var id = a.getAttribute("href").slice(1);
    if (!id || !document.getElementById(id)) return;
    e.preventDefault();
    goTo(id, true);
  });

  // #g9 gibi katlı bir gruptaki çapayla açılırsa grubu aç ve hedefe git
  function fromHash() {
    var id = (location.hash || "").slice(1);
    if (!id || !document.getElementById(id)) return;
    openAncestors(document.getElementById(id));
    setTimeout(function () { goTo(id, false); }, 60);

    // Web fonts land after the first paint and move everything down a little;
    // line the target up again once they are in.
    if (document.fonts && document.fonts.ready) {
      document.fonts.ready.then(function () {
        var el = document.getElementById(id);
        if (el) scrollTarget(el).scrollIntoView({ block: "start" });
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


/* Kaçırdıklarınız: okuyucu gün atladığında ürün susuyordu.

   Atlanan her gün kendi tek cümlesiyle geri veriliyor — manşetle değil,
   çünkü manşet neyin olduğunu söyler, özetin ilk maddesi neden önemli
   olduğunu. İlk ziyarette hiç çıkmaz: kaçırılmış bir şey yok. */
(function () {
  "use strict";

  var day = document.body.getAttribute("data-day");
  if (!day) return;

  var KEY = "defintel:last";
  var last;
  try { last = localStorage.getItem(KEY); } catch (e) { return; }
  try { localStorage.setItem(KEY, day); } catch (e) { /* özel sekme */ }

  if (!last || last >= day) return;          // ilk ziyaret ya da geri gidiş

  var base = document.querySelector('link[rel="stylesheet"][href*="app.css"]');
  var up = base && base.getAttribute("href").indexOf("../") === 0 ? "../" : "";

  fetch(up + "data/index.json", { cache: "no-store" })
    .then(function (r) { return r.json(); })
    .then(function (days) {
      var missed = days.filter(function (d) { return d.date > last && d.date < day; });
      if (!missed.length) return;

      // Dokuz günlük boşluk sekiz satır; tatil dönüşü doksan satır bir duvar.
      // En yeni yedi gün gösterilir, gerisi tek satıra iner — ama alarm günü
      // tavanın dışında kalmaz: geciken bir alarm, kaçırılmış alarmdır.
      var CAP = 7;
      var shown = missed.slice(0, CAP);
      var rest = missed.slice(CAP);
      var lateAlarms = rest.filter(function (d) { return d.alarm; });
      shown = shown.concat(lateAlarms);
      var hidden = rest.length - lateAlarms.length;
      var bar = document.createElement("section");
      bar.className = "missed";
      bar.innerHTML =
        '<div class="wrap missed-inner">' +
        '<p class="missed-head"><span class="num">' + missed.length + '</span> gün kaçırdınız' +
        '<button class="missed-close" type="button" aria-label="Kapat">×</button></p>' +
        shown.map(function (d) {
          return '<a class="missed-row" href="' + up + d.url + '">' +
                 '<span class="missed-date num">' + trDay(d.date) + '</span>' +
                 (d.alarm ? '<span class="badge badge--alarm">Alarm</span>' : "") +
                 '<span class="missed-lead">' + esc(d.lead) + "</span></a>";
        }).join("") +
        (hidden > 0
          ? '<a class="missed-more" href="' + up + 'arsiv.html">ve <span class="num">' +
            hidden + "</span> gün daha → arşiv</a>"
          : "") + "</div>";
      var after = document.querySelector(".daybar");
      if (after && after.parentNode) after.parentNode.insertBefore(bar, after.nextSibling);
      bar.addEventListener("click", function (e) {
        if (e.target.closest(".missed-close")) { e.preventDefault(); bar.remove(); }
      });
    })
    .catch(function () { /* dizin yoksa şerit de yok */ });

  function esc(t) {
    var d = document.createElement("div");
    d.textContent = t || "";
    return d.innerHTML;
  }

  function trDay(iso) {
    var months = ["Oca", "Şub", "Mar", "Nis", "May", "Haz",
                  "Tem", "Ağu", "Eyl", "Eki", "Kas", "Ara"];
    var p = iso.split("-");
    return Number(p[2]) + " " + months[Number(p[1]) - 1];
  }
})();


/* Arşivde içerik araması.

   Arşiv bugüne kadar yalnızca kart başlıklarını süzüyordu — yani günün
   manşetini. "Weibel" aramak, o adın geçtiği günü bulmuyordu; oysa ürünün
   değerinin çoğu manşette değil, o günün sekiz gelişmesinde duruyor. */
(function () {
  "use strict";

  var feed = document.querySelector(".feed");
  var box = document.getElementById("q");
  if (!feed || !box) return;                  // yalnızca arşivde

  var index = null, loading = null, panel = null, slow = null;
  var none = document.getElementById("noresults");
  // Yükleme bu eşiği aşarsa panel "Aranıyor…" der; altında bir yanıp sönme olmasın.
  var SLOW_MS = 300; /* DÖRT-DURUM:yukleniyor */

  /* Hata asla boş diziyle çözümlenmez (Rev 22). Eskiden .catch() [] döndürüyordu:
     ağ koptuğunda panel "kayıt yok" diyordu — arama çalışmıyorken "aradım,
     yok" demek. Hata reddedilir, run() onu kendi durumu olarak çizer; loading
     sıfırlanır ki bir sonraki tuş vuruşu yeniden denesin. */
  function load() {
    if (index) return Promise.resolve(index);
    if (!loading) {
      loading = fetch("data/search.json", { cache: "no-store" })
        .then(function (r) {
          if (!r.ok) throw new Error("search.json " + r.status);
          return r.json();
        })
        .then(function (rows) {
          if (!Array.isArray(rows)) throw new Error("search.json biçimi");
          index = rows;
          return rows;
        })
        .catch(function (err) {
          loading = null;
          throw err; /* DÖRT-DURUM:fetch */
        });
    }
    return loading;
  }

  function norm(s) {
    return (s || "").toLocaleLowerCase("tr").replace(/ı/g, "i").replace(/İ/g, "i");
  }

  function trDate(iso) {
    var m = ["Ocak", "Şubat", "Mart", "Nisan", "Mayıs", "Haziran",
             "Temmuz", "Ağustos", "Eylül", "Ekim", "Kasım", "Aralık"];
    var p = iso.split("-");
    return Number(p[2]) + " " + m[Number(p[1]) - 1] + " " + p[0];
  }

  function esc(t) {
    var d = document.createElement("div");
    d.textContent = t || "";
    return d.innerHTML;
  }

  function ensurePanel() {
    if (!panel) {
      panel = document.createElement("section");
      panel.className = "found";
      panel.setAttribute("aria-live", "polite");
      feed.parentNode.insertBefore(panel, feed);
    }
    return panel;
  }

  /* Dört durum, dördü de ayrı cümle: yükleniyor, hata, sonuç yok, N sonuç.
     Hata nedeni yazılmaz — okuyucu onunla bir şey yapamaz; yapabileceği tek
     şey yenilemek. */
  function say(text) {
    feed.hidden = true;
    ensurePanel().innerHTML = '<p class="found-none">' + esc(text) + "</p>";
  }

  function render(rows, term) {
    ensurePanel();
    if (!rows.length) {
      panel.innerHTML = '<p class="found-none">“' + esc(term) + '” için kayıt yok.</p>';
      return;
    }
    // Gün gün grupla: arşivde bir şeyi aramak, onu hangi günün taşıdığını aramaktır.
    var byDay = {}, order = [];
    rows.forEach(function (r) {
      if (!byDay[r.d]) { byDay[r.d] = []; order.push(r.d); }
      byDay[r.d].push(r);
    });
    order.sort().reverse();
    panel.innerHTML =
      '<p class="found-head"><span class="num">' + rows.length + "</span> kayıt · " +
      '<span class="num">' + order.length + "</span> gün</p>" +
      order.map(function (d) {
        return '<div class="found-day"><p class="found-date num">' + trDate(d) + "</p>" +
          byDay[d].map(function (r) {
            return '<a class="found-row" href="' + r.u + '">' +
              '<span class="found-title">' + esc(r.t) + "</span>" +
              (r.k === "thread"
                ? '<span class="found-kind">izleme dosyası</span>'
                : '<span class="found-text">' + esc(r.s) + "</span>") + "</a>";
          }).join("") + "</div>";
      }).join("");
  }

  function match(r, term) {
    if (allowDays && allowDays.indexOf(r.d) === -1) return false;
    return norm(r.t).indexOf(term) !== -1 || norm(r.s).indexOf(term) !== -1;
  }

  function run() {
    var term = norm(box.value.trim());
    clearTimeout(slow);
    if (!term) {
      if (panel) { panel.remove(); panel = null; }
      feed.hidden = false;
      return;
    }
    // Arama sürerken sonucun sahibi panel: kart başlıklarını süzen üstteki
    // süzgecin "eşleşen rapor yok"u panelle yan yana ikinci bir hüküm olurdu.
    if (none) none.hidden = true;
    if (!index) slow = setTimeout(function () { say("Aranıyor…"); }, SLOW_MS);
    load().then(function (rows) {
      clearTimeout(slow);
      if (norm(box.value.trim()) !== term) return;   // kullanıcı yazmaya devam etti
      feed.hidden = true;
      // Hap duruyorsa arama da onun günleri içinde kalır (VE).
      render(rows.filter(function (r) {
        var hit = match(r, term); /* DÖRT-DURUM:sonuc */
        return hit;
      }), box.value.trim());
    }, function () {
      clearTimeout(slow);
      if (norm(box.value.trim()) !== term) return;
      say("Arama şu an çalışmıyor — sayfayı yenileyin.");
    });
  }

  box.addEventListener("input", run);
  box.addEventListener("keydown", function (e) { if (e.key === "Escape") setTimeout(run, 0); });

  /* Oyuncular sayfasından gelen ?oyuncu=<kimlik>: akıştaki gün kartlarını
     o şirketin geçtiği günlere indir. Gün listesi data/oyuncular.json'dan —
     eşleştirme build'de yapıldı, sayfa onu yeniden hesaplamıyor. */
  var cards = Array.prototype.slice.call(feed.querySelectorAll(".entry"));
  var allowDays = null;          // null = kapsam yok

  function scopeDays(days) {
    allowDays = days;
    cards.forEach(function (card) {
      card.hidden = !!days && days.indexOf(card.getAttribute("data-day")) === -1;
    });
  }

  function applyPlayer(first) {
    var who = readParam("oyuncu");
    var old = document.querySelector(".pill-wrap");
    if (old) old.remove();
    if (!who) { scopeDays(null); return; }
    loadPlayers().then(function (index) {
      var entry = index[who] || {};
      var days = (entry.gunler || []).map(function (d) { return d.g; });
      scopeDays(days);
      playerPill(entry.ad || who, function () {
        dropParam("oyuncu", true);
        var w = document.querySelector(".pill-wrap");
        if (w) w.remove();
        scopeDays(null);
        run();
      });
      run();
    });
  }

  applyPlayer(true);
  window.addEventListener("popstate", function () { applyPlayer(false); });
})();


/* Oyuncular sayfasında segment süzgeci.

   Kupür sayfasındaki kategori şeridiyle aynı fikir: liste uzun, okuyucu
   çoğu zaman tek bir segmentle ilgileniyor. Üstteki üç sayı da süzülüyor —
   "Hafif silah" seçiliyken "Bugün 5" yazmak, ekranda olmayan bir kümeyi
   saymak olurdu. Sayı neyi saydığını söylemiyorsa yanlış sayıdır. */
(function () {
  "use strict";

  var strip = document.querySelector(".pchips");
  var tally = document.getElementById("ptally");
  if (!strip) return;
  var chips = Array.prototype.slice.call(strip.querySelectorAll(".pchip"));
  var rows = Array.prototype.slice.call(document.querySelectorAll(".player-row"));
  var cells = {};
  if (tally) {
    Array.prototype.slice.call(tally.querySelectorAll("[data-tally]"))
      .forEach(function (el) { cells[el.getAttribute("data-tally")] = el; });
  }

  function apply(seg) {
    var live = rows.filter(function (row) {
      var segs = (row.getAttribute("data-seg") || "").split(/\s+/);
      row.hidden = !!seg && segs.indexOf(seg) === -1;
      return !row.hidden;
    });
    if (cells.all) cells.all.textContent = live.length;
    if (cells.today) {
      cells.today.textContent = live.filter(function (r) {
        return r.getAttribute("data-today") === "1";
      }).length;
    }
    if (cells.seen) {
      cells.seen.textContent = live.filter(function (r) {
        return r.getAttribute("data-seen") === "1";
      }).length;
    }
    chips.forEach(function (c) {
      c.classList.toggle("pchip--on", (c.getAttribute("data-seg") || "") === seg);
    });
  }

  chips.forEach(function (c) {
    c.addEventListener("click", function () {
      apply(c.getAttribute("data-seg") || "");
    });
  });
})();


/* R27-P0-2: iplik sayfasının daybar'ı gelinen günü gösterir.

   İplik sayfası günden bağımsız tek dosya; brifingdeki bağlantı ?g=YYYY-MM-DD
   taşıyor. Build şeridi en son güne çizer ve brifing/medya günlerini
   data-rapor / data-medya'ya yazar; burada yalnız o güne kurulur. Bilinmeyen
   ?g= değeri şeridi olduğu gibi bırakır — var olmayan bir güne ok çizilmez. */
(function () {
  "use strict";

  var bar = document.querySelector(".daybar[data-rapor]");
  if (!bar) return;
  var g = "";
  try { g = new URLSearchParams(location.search).get("g") || ""; } catch (e) { return; }
  var days = (bar.getAttribute("data-rapor") || "").split(" ").filter(Boolean);
  var i = days.indexOf(g);
  if (i < 0) return;
  var news = (bar.getAttribute("data-medya") || "").split(" ");

  var MONTHS = ["Oca", "Şub", "Mar", "Nis", "May", "Haz",
                "Tem", "Ağu", "Eyl", "Eki", "Kas", "Ara"];
  var WEEK = ["Paz", "Pzt", "Sal", "Çar", "Per", "Cum", "Cmt"];
  function label(iso) {
    var p = iso.split("-").map(Number);
    var d = new Date(Date.UTC(p[0], p[1] - 1, p[2]));
    return p[2] + " " + MONTHS[p[1] - 1] + " · " + WEEK[d.getUTCDay()];
  }
  function arrow(old, target, glyph, name) {
    var el;
    if (target) {
      el = document.createElement("a");
      el.href = "/reports/" + target + ".html";
    } else {
      el = document.createElement("span");
      el.setAttribute("aria-disabled", "true");
    }
    el.className = "daybar-arrow";
    el.setAttribute("aria-label", name);
    el.textContent = glyph;
    old.parentNode.replaceChild(el, old);
  }

  var arrows = bar.querySelectorAll(".daybar-arrow");
  var date = bar.querySelector(".daybar-date");
  var cross = bar.querySelector(".daybar-link");
  if (arrows.length !== 2 || !date || !cross) return;
  arrow(arrows[0], i ? days[i - 1] : "", "‹", "Önceki gün");
  arrow(arrows[1], i + 1 < days.length ? days[i + 1] : "", "›", "Sonraki gün");
  date.textContent = label(g);
  var link;
  if (news.indexOf(g) >= 0) {
    link = document.createElement("a");
    link.className = "daybar-link";
    link.href = "/haberler/" + g + ".html";
    link.textContent = "MEDYA TAKİBİ →";
  } else {
    link = document.createElement("span");
    link.className = "daybar-link daybar-link--off";
    link.textContent = "Medya takibi yok";
  }
  cross.parentNode.replaceChild(link, cross);
  bar.setAttribute("data-g", g);
})();
