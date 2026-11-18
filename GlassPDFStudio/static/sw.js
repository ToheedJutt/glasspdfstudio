/* GlassPDF Studio service worker (gps-v1).
 *
 * Served at /sw.js (see the route in routes/home.py) so its scope is the
 * whole site, even though this file lives in static/.
 *
 * Strategy:
 *  - Static assets (/static/*): cache-first, filled from the network.
 *  - Page navigations: network-first, falling back to the cache and
 *    finally to the cached app shell ("/") when offline.
 *  - Everything else (API calls, downloads, and ALL non-GET requests
 *    such as the /api/process file uploads) is never intercepted.
 */

const CACHE = "gps-v1";

const APP_SHELL = [
  "/",
  "/static/manifest.webmanifest",
  "/static/icons/icon-192.png",
  "/static/icons/icon-512.png",
  "/static/icons/icon-maskable-512.png",
  /* Dashboard (root index.html) assets */
  "/static/app.css",
  "/static/app.js",
  /* Templated-site assets */
  "/static/css/style.css",
  "/static/css/components.css",
  "/static/css/animations.css",
  "/static/css/responsive.css",
  "/static/css/redesign.css",
  "/static/js/theme.js",
  "/static/js/animations.js",
  "/static/js/search.js",
  "/static/js/upload.js",
  "/static/js/app.js",
];

self.addEventListener("install", (event) => {
  event.waitUntil(
    caches
      .open(CACHE)
      .then((cache) =>
        // Add one by one so a single missing asset can't fail the install.
        Promise.allSettled(APP_SHELL.map((url) => cache.add(url)))
      )
      .then(() => self.skipWaiting())
  );
});

self.addEventListener("activate", (event) => {
  event.waitUntil(
    caches
      .keys()
      .then((keys) =>
        Promise.all(keys.filter((key) => key !== CACHE).map((key) => caches.delete(key)))
      )
      .then(() => self.clients.claim())
  );
});

self.addEventListener("fetch", (event) => {
  const { request } = event;

  // Never intercept uploads or any other non-GET traffic.
  if (request.method !== "GET") return;

  const url = new URL(request.url);
  if (url.origin !== self.location.origin) return;

  // Navigations: network-first, cache fallback, app shell last.
  if (request.mode === "navigate") {
    event.respondWith(
      fetch(request)
        .then((response) => {
          const copy = response.clone();
          caches.open(CACHE).then((cache) => cache.put(request, copy));
          return response;
        })
        .catch(() =>
          caches
            .match(request, { ignoreSearch: true })
            .then((cached) => cached || caches.match("/"))
        )
    );
    return;
  }

  // Static assets: cache-first, then network (and cache the result).
  if (url.pathname.startsWith("/static/")) {
    event.respondWith(
      caches.match(request, { ignoreSearch: true }).then(
        (cached) =>
          cached ||
          fetch(request).then((response) => {
            const copy = response.clone();
            caches.open(CACHE).then((cache) => cache.put(request, copy));
            return response;
          })
      )
    );
    return;
  }

  // All other GETs (downloads, API reads): straight to the network.
});
