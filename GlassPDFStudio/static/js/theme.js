/* ==========================================================================
   theme.js — light / dark / system theme handling
   The initial theme is set inline in <head> to avoid a flash; this module
   wires up the toggle button and keeps in sync with the OS preference until
   the user makes an explicit choice.
   ========================================================================== */
(function () {
  "use strict";

  var STORAGE_KEY = "gps-theme";
  var root = document.documentElement;

  function current() {
    return root.getAttribute("data-theme") === "dark" ? "dark" : "light";
  }

  function apply(theme, persist) {
    root.setAttribute("data-theme", theme);
    if (persist) {
      try { localStorage.setItem(STORAGE_KEY, theme); } catch (e) { /* ignore */ }
    }
    // Keep the browser UI (address bar) in step with the theme.
    var meta = document.querySelector('meta[name="theme-color"]');
    if (meta) meta.setAttribute("content", theme === "dark" ? "#0b0d1a" : "#6d5efc");
  }

  function toggle() {
    apply(current() === "dark" ? "light" : "dark", true);
  }

  document.addEventListener("click", function (e) {
    var btn = e.target.closest("[data-theme-toggle]");
    if (btn) { toggle(); }
  });

  // Follow the OS theme only while the user hasn't chosen one explicitly.
  if (window.matchMedia) {
    var mq = window.matchMedia("(prefers-color-scheme: dark)");
    var onChange = function (ev) {
      var saved;
      try { saved = localStorage.getItem(STORAGE_KEY); } catch (e) { saved = null; }
      if (!saved) apply(ev.matches ? "dark" : "light", false);
    };
    if (mq.addEventListener) mq.addEventListener("change", onChange);
    else if (mq.addListener) mq.addListener(onChange);
  }
})();
