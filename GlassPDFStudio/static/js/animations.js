/* ==========================================================================
   animations.js — scroll reveal, button ripple, sticky navbar, mobile menu,
   count-up stats, active nav link and footer year.
   Pure vanilla, no dependencies. All effects degrade gracefully.
   ========================================================================== */
(function () {
  "use strict";

  var reduceMotion = window.matchMedia &&
    window.matchMedia("(prefers-reduced-motion: reduce)").matches;

  /* ---------------------------------------------------------------- */
  /* Scroll reveal                                                    */
  /* ---------------------------------------------------------------- */
  function initReveal() {
    var els = document.querySelectorAll("[data-reveal]");
    if (!els.length) return;

    if (reduceMotion || !("IntersectionObserver" in window)) {
      els.forEach(function (el) { el.classList.add("is-visible"); });
      return;
    }

    var io = new IntersectionObserver(function (entries) {
      entries.forEach(function (entry) {
        if (entry.isIntersecting) {
          entry.target.classList.add("is-visible");
          io.unobserve(entry.target);
        }
      });
    }, { threshold: 0.12, rootMargin: "0px 0px -8% 0px" });

    els.forEach(function (el) { io.observe(el); });
  }

  /* ---------------------------------------------------------------- */
  /* Button ripple                                                    */
  /* ---------------------------------------------------------------- */
  function initRipple() {
    document.addEventListener("pointerdown", function (e) {
      var btn = e.target.closest(".btn");
      if (!btn || btn.disabled) return;
      var rect = btn.getBoundingClientRect();
      var size = Math.max(rect.width, rect.height);
      var span = document.createElement("span");
      span.className = "ripple";
      span.style.width = span.style.height = size + "px";
      span.style.left = (e.clientX - rect.left - size / 2) + "px";
      span.style.top = (e.clientY - rect.top - size / 2) + "px";
      btn.appendChild(span);
      span.addEventListener("animationend", function () { span.remove(); });
    });
  }

  /* ---------------------------------------------------------------- */
  /* Sticky navbar shadow + mobile menu                               */
  /* ---------------------------------------------------------------- */
  function initNavbar() {
    var navbar = document.querySelector("[data-navbar]");
    if (navbar) {
      var onScroll = function () {
        navbar.classList.toggle("is-scrolled", window.scrollY > 8);
      };
      onScroll();
      window.addEventListener("scroll", onScroll, { passive: true });
    }

    var toggle = document.querySelector("[data-nav-toggle]");
    if (toggle) {
      toggle.addEventListener("click", function () {
        var open = document.body.classList.toggle("nav-open");
        toggle.setAttribute("aria-expanded", open ? "true" : "false");
      });
      // Close the menu when a link is chosen.
      document.querySelectorAll(".nav-menu .nav-link").forEach(function (link) {
        link.addEventListener("click", function () {
          document.body.classList.remove("nav-open");
          toggle.setAttribute("aria-expanded", "false");
        });
      });
    }
  }

  /* ---------------------------------------------------------------- */
  /* Highlight the current page in the nav                            */
  /* ---------------------------------------------------------------- */
  function initActiveLink() {
    var path = window.location.pathname.replace(/\/$/, "") || "/";
    document.querySelectorAll(".nav-menu .nav-link").forEach(function (link) {
      var href = (link.getAttribute("href") || "").replace(/\/$/, "") || "/";
      if (href === path) link.classList.add("is-active");
    });
  }

  /* ---------------------------------------------------------------- */
  /* Count-up numbers                                                 */
  /* ---------------------------------------------------------------- */
  function initCounters() {
    var nums = document.querySelectorAll("[data-count]");
    if (!nums.length) return;
    if (reduceMotion || !("IntersectionObserver" in window)) return;

    var io = new IntersectionObserver(function (entries) {
      entries.forEach(function (entry) {
        if (!entry.isIntersecting) return;
        var el = entry.target;
        io.unobserve(el);
        var target = parseInt(el.getAttribute("data-count"), 10) || 0;
        var start = performance.now();
        var dur = 1400;
        (function tick(now) {
          var p = Math.min((now - start) / dur, 1);
          var eased = 1 - Math.pow(1 - p, 3);
          el.textContent = Math.round(target * eased).toString();
          if (p < 1) requestAnimationFrame(tick);
          else el.textContent = target.toString();
        })(start);
      });
    }, { threshold: 0.5 });

    nums.forEach(function (el) { io.observe(el); });
  }

  /* ---------------------------------------------------------------- */
  /* Footer year                                                      */
  /* ---------------------------------------------------------------- */
  function initYear() {
    document.querySelectorAll("[data-year]").forEach(function (el) {
      el.textContent = new Date().getFullYear().toString();
    });
  }

  /* ---------------------------------------------------------------- */
  function init() {
    initReveal();
    initRipple();
    initNavbar();
    initActiveLink();
    initCounters();
    initYear();
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init);
  } else {
    init();
  }
})();
