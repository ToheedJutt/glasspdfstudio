/* ==========================================================================
   search.js — global command-palette search + all-tools page filtering.
   Reads the serialised catalogue from #tools-data and icon paths from
   #icons-data (both injected by layout.html).
   ========================================================================== */
(function () {
  "use strict";

  function readJSON(id) {
    var el = document.getElementById(id);
    if (!el) return null;
    try { return JSON.parse(el.textContent); } catch (e) { return null; }
  }

  var TOOLS = readJSON("tools-data") || [];
  var ICONS = readJSON("icons-data") || {};

  function iconSvg(name) {
    var d = ICONS[name] || ICONS.doc || "";
    return '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" ' +
      'stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round" ' +
      'aria-hidden="true"><path d="' + d + '"/></svg>';
  }

  function toolUrl(slug) { return "/tools/" + slug; }

  /* ================================================================ */
  /* Command palette                                                  */
  /* ================================================================ */
  function initPalette() {
    var overlay = document.querySelector("[data-search-overlay]");
    if (!overlay) return;

    var input = overlay.querySelector("[data-search-input]");
    var list = overlay.querySelector("[data-search-results]");
    var empty = overlay.querySelector("[data-search-empty]");
    var active = -1;
    var results = [];

    function open() {
      overlay.hidden = false;
      document.body.style.overflow = "hidden";
      render("");
      setTimeout(function () { input.focus(); }, 20);
    }
    function close() {
      overlay.hidden = true;
      document.body.style.overflow = "";
      input.value = "";
      active = -1;
    }
    function isOpen() { return !overlay.hidden; }

    function score(tool, q) {
      var name = tool.name.toLowerCase();
      var cat = (tool.category || "").toLowerCase();
      var desc = (tool.description || "").toLowerCase();
      if (name.indexOf(q) === 0) return 0;
      if (name.indexOf(q) > -1) return 1;
      if (cat.indexOf(q) > -1) return 2;
      if (desc.indexOf(q) > -1) return 3;
      return -1;
    }

    function render(query) {
      var q = query.trim().toLowerCase();
      if (!q) {
        results = TOOLS.slice(0, 6);
      } else {
        results = TOOLS
          .map(function (t) { return { t: t, s: score(t, q) }; })
          .filter(function (r) { return r.s > -1; })
          .sort(function (a, b) { return a.s - b.s; })
          .map(function (r) { return r.t; })
          .slice(0, 8);
      }
      active = results.length ? 0 : -1;
      list.innerHTML = results.map(function (t, i) {
        return '<li class="search-result' + (i === 0 ? " is-active" : "") + '" ' +
          'data-cat="' + t.category + '" data-url="' + toolUrl(t.slug) + '" role="option">' +
          '<span class="search-result__icon">' + iconSvg(t.icon) + '</span>' +
          '<span><span class="search-result__name">' + t.name + '</span>' +
          '<span class="search-result__cat">' + t.category + '</span></span></li>';
      }).join("");
      empty.hidden = results.length > 0;
    }

    function move(delta) {
      if (!results.length) return;
      active = (active + delta + results.length) % results.length;
      Array.prototype.forEach.call(list.children, function (li, i) {
        li.classList.toggle("is-active", i === active);
        if (i === active) li.scrollIntoView({ block: "nearest" });
      });
    }

    function go() {
      var li = list.children[active];
      if (li) window.location.href = li.getAttribute("data-url");
    }

    // Triggers
    document.addEventListener("click", function (e) {
      if (e.target.closest("[data-search-open]")) { e.preventDefault(); open(); }
      if (e.target.closest("[data-search-close]")) { close(); }
    });

    document.addEventListener("keydown", function (e) {
      // "/" or Ctrl/Cmd+K opens the palette from anywhere (unless typing).
      var typing = /^(input|textarea|select)$/i.test((e.target.tagName || "")) ||
        e.target.isContentEditable;
      if (!isOpen() && !typing && (e.key === "/" || ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === "k"))) {
        e.preventDefault(); open(); return;
      }
      if (!isOpen()) return;
      if (e.key === "Escape") { close(); }
      else if (e.key === "ArrowDown") { e.preventDefault(); move(1); }
      else if (e.key === "ArrowUp") { e.preventDefault(); move(-1); }
      else if (e.key === "Enter") { e.preventDefault(); go(); }
    });

    input.addEventListener("input", function () { render(input.value); });
    list.addEventListener("click", function (e) {
      var li = e.target.closest(".search-result");
      if (li) window.location.href = li.getAttribute("data-url");
    });
  }

  /* ================================================================ */
  /* All-tools page filtering                                         */
  /* ================================================================ */
  function initCatalogueFilter() {
    var input = document.querySelector("[data-filter-input]");
    var chipsWrap = document.querySelector("[data-filter-chips]");
    if (!input && !chipsWrap) return;

    var cards = Array.prototype.slice.call(document.querySelectorAll(".catalogue .tool-card"));
    var blocks = Array.prototype.slice.call(document.querySelectorAll("[data-cat-block]"));
    var emptyEl = document.querySelector("[data-filter-empty]");
    var termEl = document.querySelector("[data-filter-term]");
    var activeCat = "all";

    function apply() {
      var q = (input ? input.value : "").trim().toLowerCase();
      var anyVisible = false;

      cards.forEach(function (card) {
        var name = (card.querySelector(".tool-card__title") || {}).textContent || "";
        var desc = (card.querySelector(".tool-card__desc") || {}).textContent || "";
        var cat = card.getAttribute("data-category") || "";
        var matchQ = !q || (name + " " + desc).toLowerCase().indexOf(q) > -1;
        var matchCat = activeCat === "all" || cat === activeCat;
        var show = matchQ && matchCat;
        card.classList.toggle("is-hidden", !show);
        if (show) anyVisible = true;
      });

      // Hide category blocks that have no visible cards.
      blocks.forEach(function (block) {
        var visible = block.querySelectorAll(".tool-card:not(.is-hidden)").length;
        block.classList.toggle("is-hidden", visible === 0);
      });

      if (emptyEl) {
        emptyEl.hidden = anyVisible;
        if (termEl) termEl.textContent = q ? '"' + q + '"' : "your filter";
      }
    }

    if (input) input.addEventListener("input", apply);

    if (chipsWrap) {
      chipsWrap.addEventListener("click", function (e) {
        var chip = e.target.closest("[data-filter]");
        if (!chip) return;
        activeCat = chip.getAttribute("data-filter");
        Array.prototype.forEach.call(chipsWrap.children, function (c) {
          var on = c === chip;
          c.classList.toggle("is-active", on);
          c.setAttribute("aria-selected", on ? "true" : "false");
        });
        apply();
      });
    }
  }

  function init() {
    initPalette();
    initCatalogueFilter();
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init);
  } else {
    init();
  }
})();
