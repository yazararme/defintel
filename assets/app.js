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

    // hide a section label whose entries are all filtered out
    document.querySelectorAll(".section-label").forEach(function (label) {
      var any = false;
      var n = label.nextElementSibling;
      while (n && !n.classList.contains("section-label")) {
        if (n.classList.contains("entry") && !n.hidden) { any = true; break; }
        n = n.nextElementSibling;
      }
      label.hidden = !any;
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
