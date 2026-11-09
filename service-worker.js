/* Chrispy Games Service Worker
   Change VERSION every time you update the site. */

const VERSION = "chrispy-games-v2026-11-09-create-kick-fix-1";
const CACHE_NAME = VERSION;
// Firebase SDK + Google Fonts. Their URLs never change, so this cache survives version bumps.
const VENDOR_CACHE = "chrispy-games-vendor-v1";
// On bad signal, open the saved copy instead of a long black screen.
const NETWORK_TIMEOUT_MS = 3000;

const CORE_ASSETS = [
  "./",
  "./index.html",
  "./manifest.json",
  "./coin-icon-2.png",
  "./icons/icon-192.png",
  "./icons/icon-512.png"
];

self.addEventListener("install", event => {
  event.waitUntil(
    caches.open(CACHE_NAME)
      .then(cache => cache.addAll(CORE_ASSETS))
      .then(() => self.skipWaiting())
      .catch(error => {
        console.warn("Service worker install cache failed:", error);
      })
  );
});

self.addEventListener("activate", event => {
  event.waitUntil(
    caches.keys()
      .then(keys => Promise.all(
        keys
          .filter(key => key !== CACHE_NAME && key !== VENDOR_CACHE)
          .map(key => caches.delete(key))
      ))
      .then(() => self.clients.claim())
  );
});

self.addEventListener("message", event => {
  if (event.data && event.data.type === "SKIP_WAITING") {
    self.skipWaiting();
  }
});

self.addEventListener("fetch", event => {
  const request = event.request;

  if (request.method !== "GET") return;

  const url = new URL(request.url);

  // The Firebase SDK and Google Fonts block the page from drawing, so keep a copy.
  // Everything else external (the Firebase database itself, APIs) is never cached.
  if (url.origin !== self.location.origin) {
    const vendor = (url.hostname === "www.gstatic.com" && url.pathname.startsWith("/firebasejs/"))
      || url.hostname === "fonts.googleapis.com"
      || url.hostname === "fonts.gstatic.com";
    if (!vendor) return;
    event.respondWith(
      caches.open(VENDOR_CACHE).then(cache =>
        cache.match(request).then(cached => cached || fetch(request).then(response => {
          if (response && (response.ok || response.type === "opaque")) cache.put(request, response.clone());
          return response;
        }))
      )
    );
    return;
  }

  // Try fresh HTML first so game updates appear quickly, but give up after
  // NETWORK_TIMEOUT_MS and open the saved copy. The fresh copy still gets saved for next time.
  if (request.mode === "navigate" || url.pathname.endsWith("/index.html")) {
    const network = fetch(request, { cache: "no-store" }).then(response => {
      if (response && response.ok) {
        const copyA = response.clone();
        const copyB = response.clone();
        caches.open(CACHE_NAME).then(cache => {
          cache.put("./index.html", copyA);
          cache.put("./", copyB);
        });
      }
      return response;
    });
    event.waitUntil(network.catch(() => {}));
    event.respondWith(
      caches.match("./index.html")
        .then(cached => cached || caches.match("./"))
        .then(cached => {
          if (!cached) return network;
          const timeout = new Promise(resolve => setTimeout(() => resolve(null), NETWORK_TIMEOUT_MS));
          return Promise.race([network.catch(() => null), timeout]).then(fresh => (fresh && fresh.ok) ? fresh : cached);
        })
    );

    return;
  }

  // Static assets: cache first, then update in background.
  event.respondWith(
    caches.match(request).then(cached => {
      const networkFetch = fetch(request)
        .then(response => {
          if (response && response.ok) {
            const copy = response.clone();

            caches.open(CACHE_NAME).then(cache => {
              cache.put(request, copy);
            });
          }

          return response;
        })
        .catch(() => cached);

      return cached || networkFetch;
    })
  );
});
