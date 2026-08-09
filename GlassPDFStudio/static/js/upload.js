/* ==========================================================================
   upload.js — drag & drop upload engine + homepage → tool file handoff.

   Responsibilities
   - Wire the tool workspace dropzone: drag/drop, browse, multi-file queue,
     image previews, per-file remove and validation against the tool's
     `accept` list and `minFiles`.
   - Expose the live queue on the workspace element (`ws.gpsQueue`) and emit a
     `gps:queuechange` event so app.js can toggle the run button and submit.
   - Handle the landing hero dropzone: stash the chosen files in IndexedDB and
     open the tool chooser; the destination tool page picks them back up.
   ========================================================================== */
(function () {
  "use strict";

  window.GPS = window.GPS || {};

  /* ---------------------------------------------------------------- */
  /* Helpers                                                          */
  /* ---------------------------------------------------------------- */
  function formatBytes(bytes) {
    if (!bytes) return "0 B";
    var units = ["B", "KB", "MB", "GB"];
    var i = Math.floor(Math.log(bytes) / Math.log(1024));
    return (bytes / Math.pow(1024, i)).toFixed(i ? 1 : 0) + " " + units[i];
  }

  function extOf(name) {
    var m = /\.[^.]+$/.exec(name || "");
    return m ? m[0].toLowerCase() : "";
  }

  // Parse an accept string ("pdf,image/*,.docx") into a matcher function.
  function acceptMatcher(accept) {
    var parts = (accept || "").split(",").map(function (s) { return s.trim().toLowerCase(); })
      .filter(Boolean);
    if (!parts.length || parts.indexOf("*") > -1 || parts.indexOf("*/*") > -1) {
      return function () { return true; };
    }
    var exts = parts.filter(function (p) { return p.charAt(0) === "."; });
    var mimes = parts.filter(function (p) { return p.indexOf("/") > -1; });
    return function (file) {
      var ext = extOf(file.name);
      var type = (file.type || "").toLowerCase();
      if (exts.indexOf(ext) > -1) return true;
      for (var i = 0; i < mimes.length; i++) {
        var m = mimes[i];
        if (m.slice(-2) === "/*") { if (type.indexOf(m.slice(0, -1)) === 0) return true; }
        else if (m === type) return true;
      }
      return false;
    };
  }

  var IMG_EXT = [".jpg", ".jpeg", ".png", ".bmp", ".tif", ".tiff", ".webp", ".gif"];
  function isImage(file) {
    return (file.type || "").indexOf("image/") === 0 || IMG_EXT.indexOf(extOf(file.name)) > -1;
  }

  function docIcon() {
    return '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7" ' +
      'stroke-linecap="round" stroke-linejoin="round"><path d="M7 3h7l4 4v14H7zM14 3v5h5M9 13h6M9 17h6"/></svg>';
  }

  var toastTimer;
  function toast(msg, kind) {
    var el = document.querySelector(".gps-toast");
    if (!el) {
      el = document.createElement("div");
      el.className = "gps-toast";
      el.setAttribute("role", "status");
      el.style.cssText = "position:fixed;left:50%;bottom:28px;transform:translateX(-50%) translateY(20px);" +
        "background:var(--surface);color:var(--text);border:1px solid var(--border-2);" +
        "box-shadow:var(--sh-lg);padding:.8rem 1.2rem;border-radius:14px;font-weight:600;" +
        "font-size:.9rem;z-index:300;opacity:0;transition:opacity .25s,transform .25s;max-width:90vw;";
      document.body.appendChild(el);
    }
    el.textContent = msg;
    el.style.borderLeft = "4px solid " + (kind === "error" ? "#f43f5e" : "#6d5efc");
    requestAnimationFrame(function () {
      el.style.opacity = "1";
      el.style.transform = "translateX(-50%) translateY(0)";
    });
    clearTimeout(toastTimer);
    toastTimer = setTimeout(function () {
      el.style.opacity = "0";
      el.style.transform = "translateX(-50%) translateY(20px)";
    }, 3200);
  }
  window.GPS.toast = toast;

  /* ---------------------------------------------------------------- */
  /* IndexedDB handoff (hero files -> tool page)                      */
  /* ---------------------------------------------------------------- */
  var DB_NAME = "gps-handoff", STORE = "files", KEY = "pending";

  function openDB() {
    return new Promise(function (resolve, reject) {
      if (!("indexedDB" in window)) { reject(new Error("no-idb")); return; }
      var req = indexedDB.open(DB_NAME, 1);
      req.onupgradeneeded = function () {
        if (!req.result.objectStoreNames.contains(STORE)) req.result.createObjectStore(STORE);
      };
      req.onsuccess = function () { resolve(req.result); };
      req.onerror = function () { reject(req.error); };
    });
  }

  function savePending(files) {
    return openDB().then(function (db) {
      return new Promise(function (resolve, reject) {
        var tx = db.transaction(STORE, "readwrite");
        tx.objectStore(STORE).put(Array.prototype.slice.call(files), KEY);
        tx.oncomplete = function () { db.close(); resolve(); };
        tx.onerror = function () { reject(tx.error); };
      });
    });
  }

  function takePending() {
    return openDB().then(function (db) {
      return new Promise(function (resolve) {
        var tx = db.transaction(STORE, "readwrite");
        var store = tx.objectStore(STORE);
        var getReq = store.get(KEY);
        getReq.onsuccess = function () {
          var val = getReq.result || null;
          store.delete(KEY);
          tx.oncomplete = function () { db.close(); resolve(val); };
        };
        getReq.onerror = function () { resolve(null); };
      });
    }).catch(function () { return null; });
  }

  /* ---------------------------------------------------------------- */
  /* Workspace queue                                                  */
  /* ---------------------------------------------------------------- */
  function initWorkspace() {
    var ws = document.querySelector("[data-workspace]");
    if (!ws) return;

    var dropzone = ws.querySelector("[data-dropzone]");
    var input = ws.querySelector("[data-file-input]");
    var listEl = ws.querySelector("[data-filelist]");
    var multiple = ws.getAttribute("data-multiple") === "true";
    var minFiles = parseInt(ws.getAttribute("data-min-files"), 10) || 0;
    var accept = ws.getAttribute("data-accept") || "";
    var matches = acceptMatcher(accept);

    var files = [];
    var previews = new WeakMap();

    var queue = {
      get files() { return files.slice(); },
      get valid() { return files.length >= Math.max(minFiles, minFiles === 0 ? 0 : 1) || (minFiles === 0); },
      add: addFiles,
      clear: clearAll
    };
    ws.gpsQueue = queue;

    function emit() {
      ws.dispatchEvent(new CustomEvent("gps:queuechange", {
        detail: { count: files.length, valid: files.length >= minFiles && (minFiles > 0 ? files.length > 0 : true) }
      }));
    }

    function addFiles(fileList) {
      var incoming = Array.prototype.slice.call(fileList || []);
      var accepted = 0, rejected = 0;
      incoming.forEach(function (file) {
        if (!matches(file)) { rejected++; return; }
        // De-dupe by name+size.
        var dup = files.some(function (f) { return f.name === file.name && f.size === file.size; });
        if (dup) return;
        if (!multiple) files = [];
        files.push(file);
        accepted++;
      });
      if (!multiple && files.length > 1) files = files.slice(-1);
      if (rejected) toast(rejected + " file" + (rejected > 1 ? "s were" : " was") + " skipped — wrong type for this tool.", "error");
      render();
      emit();
    }

    function removeAt(index) {
      var li = listEl.children[index];
      files.splice(index, 1);
      if (li) {
        li.classList.add("is-removing");
        li.addEventListener("animationend", function () { render(); emit(); });
      } else { render(); emit(); }
      emit();
    }

    function clearAll() { files = []; render(); emit(); }

    function render() {
      listEl.innerHTML = "";
      files.forEach(function (file, i) {
        var li = document.createElement("li");
        li.className = "file-item";

        var thumb = document.createElement("span");
        thumb.className = "file-item__thumb";
        if (isImage(file)) {
          var url = previews.get(file);
          if (!url) { url = URL.createObjectURL(file); previews.set(file, url); }
          var img = document.createElement("img");
          img.src = url; img.alt = "";
          thumb.appendChild(img);
        } else {
          thumb.innerHTML = docIcon();
        }

        var meta = document.createElement("span");
        meta.className = "file-item__meta";
        var name = document.createElement("span");
        name.className = "file-item__name"; name.textContent = file.name;
        var size = document.createElement("span");
        size.className = "file-item__size"; size.textContent = formatBytes(file.size);
        meta.appendChild(name); meta.appendChild(size);

        var remove = document.createElement("button");
        remove.type = "button";
        remove.className = "file-item__remove";
        remove.setAttribute("aria-label", "Remove " + file.name);
        remove.innerHTML = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" ' +
          'stroke-width="2" stroke-linecap="round"><path d="M18 6 6 18M6 6l12 12"/></svg>';
        remove.addEventListener("click", function () { removeAt(i); });

        li.appendChild(thumb); li.appendChild(meta); li.appendChild(remove);
        listEl.appendChild(li);
      });
    }

    /* Events: browse + drag/drop */
    dropzone.addEventListener("click", function () { input.click(); });
    dropzone.addEventListener("keydown", function (e) {
      if (e.key === "Enter" || e.key === " ") { e.preventDefault(); input.click(); }
    });
    input.addEventListener("change", function () { addFiles(input.files); input.value = ""; });

    var depth = 0;
    ["dragenter", "dragover"].forEach(function (ev) {
      dropzone.addEventListener(ev, function (e) { e.preventDefault(); depth++; dropzone.classList.add("is-dragover"); });
    });
    ["dragleave", "dragend"].forEach(function (ev) {
      dropzone.addEventListener(ev, function (e) { e.preventDefault(); depth = Math.max(0, depth - 1); if (!depth) dropzone.classList.remove("is-dragover"); });
    });
    dropzone.addEventListener("drop", function (e) {
      e.preventDefault(); depth = 0; dropzone.classList.remove("is-dragover");
      if (e.dataTransfer && e.dataTransfer.files) addFiles(e.dataTransfer.files);
    });

    // Pick up any files handed over from the landing hero.
    takePending().then(function (pending) {
      if (pending && pending.length) {
        var usable = pending.filter(matches);
        if (usable.length) { addFiles(usable); toast("Loaded " + usable.length + " file" + (usable.length > 1 ? "s" : "") + " from the homepage."); }
      }
    });

    emit();
  }

  /* ---------------------------------------------------------------- */
  /* Landing hero launcher                                            */
  /* ---------------------------------------------------------------- */
  function initHero() {
    var hero = document.querySelector("[data-hero-drop]");
    var chooser = document.querySelector("[data-launch-chooser]");
    if (!hero || !chooser) return;

    var input = hero.querySelector("[data-hero-input]");
    var countEl = chooser.querySelector("[data-launch-count]");

    function openChooser(n) {
      if (countEl) countEl.textContent = n;
      chooser.hidden = false;
      document.body.style.overflow = "hidden";
    }
    function closeChooser() {
      chooser.hidden = true;
      document.body.style.overflow = "";
    }

    function handle(fileList) {
      var arr = Array.prototype.slice.call(fileList || []);
      if (!arr.length) return;
      savePending(arr).then(function () { openChooser(arr.length); })
        .catch(function () {
          // No IndexedDB — still let the user pick a tool (they'll re-upload).
          openChooser(arr.length);
          toast("Choose a tool to continue.");
        });
    }

    hero.addEventListener("click", function () { input.click(); });
    hero.addEventListener("keydown", function (e) {
      if (e.key === "Enter" || e.key === " ") { e.preventDefault(); input.click(); }
    });
    input.addEventListener("change", function () { handle(input.files); input.value = ""; });

    ["dragenter", "dragover"].forEach(function (ev) {
      hero.addEventListener(ev, function (e) { e.preventDefault(); hero.classList.add("is-dragover"); });
    });
    ["dragleave", "dragend"].forEach(function (ev) {
      hero.addEventListener(ev, function (e) { e.preventDefault(); hero.classList.remove("is-dragover"); });
    });
    hero.addEventListener("drop", function (e) {
      e.preventDefault(); hero.classList.remove("is-dragover");
      if (e.dataTransfer && e.dataTransfer.files) handle(e.dataTransfer.files);
    });

    chooser.addEventListener("click", function (e) {
      if (e.target.closest("[data-launch-close]")) closeChooser();
    });
    document.addEventListener("keydown", function (e) {
      if (e.key === "Escape" && !chooser.hidden) closeChooser();
    });
    // Tool tiles are plain links; the files are already saved, so just navigate.
  }

  function init() { initWorkspace(); initHero(); }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init);
  } else {
    init();
  }
})();
