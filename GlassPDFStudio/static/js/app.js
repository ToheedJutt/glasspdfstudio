/* ==========================================================================
   app.js — tool workspace controller.

   Owns the run/submit lifecycle for a single tool page:
   - enables the run button once the file queue satisfies the tool's minimum,
   - serialises the options form into the exact { tool, options, files } shape
     the /api/process endpoint expects (unchanged contract),
   - uploads via XMLHttpRequest for a real progress bar, and
   - renders the success (download) or error state.
   ========================================================================== */
(function () {
  "use strict";

  function init() {
    var ws = document.querySelector("[data-workspace]");
    if (!ws) { healthCheck(); return; }

    var toolId = ws.getAttribute("data-tool-id");
    var minFiles = parseInt(ws.getAttribute("data-min-files"), 10) || 0;

    var form = ws.querySelector("[data-option-form]");
    var runBtn = ws.querySelector("[data-run-btn]");
    var resetBtn = ws.querySelector("[data-reset-btn]");

    var result = ws.querySelector("[data-result]");
    var progressWrap = ws.querySelector("[data-progress-wrap]");
    var progressBar = ws.querySelector("[data-progress-bar]");
    var progressLabel = ws.querySelector("[data-progress-label]");
    var doneEl = ws.querySelector("[data-result-done]");
    var errorEl = ws.querySelector("[data-result-error]");
    var titleEl = ws.querySelector("[data-result-title]");
    var messageEl = ws.querySelector("[data-result-message]");
    var detailsEl = ws.querySelector("[data-result-details]");
    var downloadEl = ws.querySelector("[data-download]");
    var errorMessageEl = ws.querySelector("[data-error-message]");

    var busy = false;

    /* ------------------------------------------------------------ */
    /* Enable / disable the run button as the queue changes         */
    /* ------------------------------------------------------------ */
    function syncRun() {
      var count = ws.gpsQueue ? ws.gpsQueue.files.length : 0;
      runBtn.disabled = busy || count < minFiles;
    }
    ws.addEventListener("gps:queuechange", syncRun);
    syncRun();

    /* ------------------------------------------------------------ */
    /* Collect the options form into a plain object                 */
    /* ------------------------------------------------------------ */
    function collectOptions() {
      var opts = {};
      if (!form) return opts;
      var controls = form.querySelectorAll("[name]");
      Array.prototype.forEach.call(controls, function (el) {
        var name = el.getAttribute("name");
        if (!name) return;

        if (el.type === "checkbox") {
          if (el.getAttribute("data-array") === "true") {
            if (el.checked) { (opts[name] = opts[name] || []).push(el.value); }
          } else if (el.checked) {
            opts[name] = true;
          }
          return;
        }
        var value = el.value;
        // Skip empty optional fields so backend defaults apply unchanged.
        if (value === "" || value == null) return;
        opts[name] = value;
      });
      return opts;
    }

    /* ------------------------------------------------------------ */
    /* Progress helpers                                             */
    /* ------------------------------------------------------------ */
    var creepTimer = null;
    function setProgress(pct, label) {
      progressBar.style.width = Math.max(0, Math.min(100, pct)) + "%";
      if (label) progressLabel.textContent = label;
    }
    function startCreep(from, to) {
      var v = from;
      clearInterval(creepTimer);
      creepTimer = setInterval(function () {
        v += (to - v) * 0.08 + 0.2;
        if (v >= to) { v = to; clearInterval(creepTimer); }
        setProgress(v);
      }, 200);
    }
    function stopCreep() { clearInterval(creepTimer); }

    /* ------------------------------------------------------------ */
    /* Result rendering                                            */
    /* ------------------------------------------------------------ */
    function showResult() {
      result.hidden = false;
      progressWrap.hidden = false;
      doneEl.hidden = true;
      errorEl.hidden = true;
      result.scrollIntoView({ behavior: "smooth", block: "nearest" });
    }

    function showSuccess(data) {
      stopCreep();
      setProgress(100, "Done");
      setTimeout(function () {
        progressWrap.hidden = true;
        errorEl.hidden = true;
        doneEl.hidden = false;
        if (titleEl) titleEl.textContent = "Your file is ready";
        if (messageEl) messageEl.textContent = data.message || "";
        if (detailsEl) {
          detailsEl.innerHTML = "";
          (data.details || []).forEach(function (d) {
            var li = document.createElement("li");
            li.textContent = d;
            detailsEl.appendChild(li);
          });
        }
        if (downloadEl) {
          downloadEl.setAttribute("href", data.downloadUrl);
          downloadEl.setAttribute("download", data.filename || "");
        }
        if (resetBtn) resetBtn.hidden = false;
      }, 350);
    }

    function showError(msg) {
      stopCreep();
      progressWrap.hidden = true;
      doneEl.hidden = true;
      errorEl.hidden = false;
      if (errorMessageEl) errorMessageEl.textContent = msg || "Unexpected error.";
      if (resetBtn) resetBtn.hidden = false;
    }

    function setBusy(state) {
      busy = state;
      runBtn.classList.toggle("is-busy", state);
      syncRun();
    }

    /* ------------------------------------------------------------ */
    /* Submit                                                      */
    /* ------------------------------------------------------------ */
    function submit(e) {
      e.preventDefault();
      if (busy) return;

      var files = ws.gpsQueue ? ws.gpsQueue.files : [];
      if (files.length < minFiles) {
        (window.GPS && window.GPS.toast) &&
          window.GPS.toast("Please add at least " + minFiles + " file" + (minFiles > 1 ? "s" : "") + ".", "error");
        return;
      }

      var fd = new FormData();
      fd.append("tool", toolId);
      fd.append("options", JSON.stringify(collectOptions()));
      files.forEach(function (f) { fd.append("files", f, f.name); });

      setBusy(true);
      showResult();
      setProgress(2, "Uploading…");

      var xhr = new XMLHttpRequest();
      xhr.open("POST", "/api/process");

      xhr.upload.onprogress = function (ev) {
        if (ev.lengthComputable) {
          var pct = Math.round((ev.loaded / ev.total) * 65) + 2;
          setProgress(pct, "Uploading…");
        }
      };
      xhr.upload.onload = function () {
        setProgress(70, "Processing…");
        startCreep(70, 95);
      };

      xhr.onreadystatechange = function () {
        if (xhr.readyState !== 4) return;
        setBusy(false);
        var data = null;
        try { data = JSON.parse(xhr.responseText); } catch (err) { data = null; }

        if (xhr.status >= 200 && xhr.status < 300 && data && data.ok) {
          showSuccess(data);
        } else {
          var msg = (data && data.error) ? data.error :
            (xhr.status === 0 ? "Could not reach the server. Is it running?" :
              "Server error (" + xhr.status + ").");
          showError(msg);
        }
      };
      xhr.onerror = function () { setBusy(false); showError("Network error — please try again."); };
      xhr.send(fd);
    }

    if (form) form.addEventListener("submit", submit);

    /* ------------------------------------------------------------ */
    /* Reset                                                       */
    /* ------------------------------------------------------------ */
    if (resetBtn) {
      resetBtn.addEventListener("click", function () {
        if (ws.gpsQueue) ws.gpsQueue.clear();
        if (form) form.reset();
        result.hidden = true;
        doneEl.hidden = true;
        errorEl.hidden = true;
        resetBtn.hidden = true;
        setProgress(0, "Processing…");
        syncRun();
      });
    }

    healthCheck();
  }

  /* ---------------------------------------------------------------- */
  /* Silent health check — gently note when an optional engine is     */
  /* missing for engine-dependent tools (backend still has fallbacks).*/
  /* ---------------------------------------------------------------- */
  function healthCheck() {
    var ws = document.querySelector("[data-workspace]");
    if (!ws || !window.fetch) return;
    var toolId = ws.getAttribute("data-tool-id") || "";
    var needsOffice = /^(word|powerpoint|excel)_to_pdf$/.test(toolId);
    var needsOcr = toolId === "ocr_pdf";
    if (!needsOffice && !needsOcr) return;

    fetch("/api/health").then(function (r) { return r.json(); }).then(function (h) {
      if (needsOffice && !h.soffice && window.GPS && window.GPS.toast) {
        window.GPS.toast("LibreOffice isn't installed — a built-in converter will be used.");
      }
      if (needsOcr && !h.tesseract && window.GPS && window.GPS.toast) {
        window.GPS.toast("Tesseract isn't installed — OCR will use a built-in fallback.");
      }
    }).catch(function () { /* ignore */ });
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init);
  } else {
    init();
  }
})();
