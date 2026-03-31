// ============================================================
//  Service Worker — جعبه‌ابزار آفلاین 
//  Strategies:
//    - App shell (HTML/CSS/JS/fonts): Stale-While-Revalidate
//    - Static assets (images, maps): Cache-First
//    - External/opaque requests: Network-only (skip)
// ============================================================

const CACHE_VERSION = 'toolbox-v2.9';
const CACHE_SHELL   = CACHE_VERSION + '-shell';   // HTML, CSS, JS, fonts
const CACHE_ASSETS  = CACHE_VERSION + '-assets';  // images, maps, large files

// App shell — precached on install
const SHELL_URLS = [
  '/',
  '/index.html',
  '/iran.html',
  '/main.css',
  '/main.js',
  '/manifest.json',
  '/favicon.png',
  '/icon-512.png',
  '/Vazirmatn-VF.ttf',
  // Third-party libraries — cache shell to ensure offline functionality of tools that depend on them
  '/lib/qrcode.js',
  '/lib/jsQR.js',
  '/lib/qr-code-styling.js',
  '/lib/browser-image-compression.js',
  '/lib/pdf.mjs',
  '/lib/pdf.worker.mjs',
  '/lib/function-plot.js',
  '/lib/math.js',
  // Poem structures (small JSON files) — cache shell to ensure offline navigation
  '/poems/fersowsi/structure.json',
  '/poems/forugh/structure.json',
  '/poems/hafez/structure.json',
  '/poems/jami/structure.json',
  '/poems/khayyam/structure.json',
  '/poems/nizami/structure.json',
  '/poems/rumi/structure.json',
  '/poems/saadi/structure.json',
  '/poems/sanai/structure.json',
  '/poems/shahriar/structure.json',
  '/poems/sohrab-sepehri/structure.json',
  '/poems/vahsi/structure.json',
];

// ── Install: cache app shell ──────────────────────────────
self.addEventListener('install', function(event) {
  event.waitUntil(
    caches.open(CACHE_SHELL)
      .then(function(cache) {
        // addAll fails install if any file fails — ensures a complete shell
        return cache.addAll(SHELL_URLS);
      })
      .then(function() {
        return self.skipWaiting();
      })
  );
});
 
// ── Activate: delete all old caches ──────────────────────
self.addEventListener('activate', function(event) {
  var KEEP = [CACHE_SHELL, CACHE_ASSETS];
  event.waitUntil(
    caches.keys()
      .then(function(names) {
        return Promise.all(
          names
            .filter(function(n) { return !KEEP.includes(n); })
            .map(function(n)    { return caches.delete(n); })
        );
      })
      .then(function() {
        return self.clients.claim();
      })
      .then(function() {
        return self.clients.matchAll({ type: 'window' });
      })
      .then(function(clients) {
        clients.forEach(function(client) {
          client.postMessage({ type: 'SW_UPDATED', version: CACHE_VERSION });
        });
      })
  );
});
 
// ── Fetch ─────────────────────────────────────────────────
self.addEventListener('fetch', function(event) {
  if (event.request.method !== 'GET') return;
 
  var url = new URL(event.request.url);
 
  // Skip cross-origin (Bale SDK, CDN, external APIs)
  if (url.origin !== self.location.origin) return;
 
  var path = url.pathname;
 
  // Large on-demand files: Cache-First
  if (path.startsWith('/maps/') || path.endsWith('.pdf')) {
    event.respondWith(cacheFirst(event.request, CACHE_ASSETS));
    return;
  }
 
  // ── Navigation requests (opening PWA from home screen, typing URL) ──
  // This is the critical path for offline PWA launch.
  // Browser sends these as mode:'navigate' — intercept and serve from cache.
  if (event.request.mode === 'navigate') {
    event.respondWith(
      caches.match('/index.html', { cacheName: CACHE_SHELL })
        .then(function(cached) {
          if (cached) {
            // Revalidate in background for next visit
            fetch(event.request)
              .then(function(response) {
                if (response && response.ok) {
                  caches.open(CACHE_SHELL).then(function(c) {
                    c.put(event.request, response);
                  });
                }
              })
              .catch(function() {});
            return cached;
          }
          // Not in cache yet — try network
          return fetch(event.request).catch(function() {
            return new Response(
              '<h1 dir="rtl" style="font-family:sans-serif;text-align:center;padding:40px">برای اولین بار باید آنلاین باشید تا اپ کش شود</h1>',
              { status: 503, headers: { 'Content-Type': 'text/html; charset=utf-8' } }
            );
          });
        })
    );
    return;
  }
 
  // All other same-origin requests: Stale-While-Revalidate
  event.respondWith(staleWhileRevalidate(event.request, CACHE_SHELL));
});
 
// ── Strategy: Cache-First ────────────────────────────────
function cacheFirst(request, cacheName) {
  return caches.open(cacheName).then(function(cache) {
    return cache.match(request).then(function(cached) {
      if (cached) return cached;
      return fetch(request).then(function(response) {
        if (response && response.ok) {
          cache.put(request, response.clone());
        }
        return response;
      }).catch(function() {
        return new Response(
          JSON.stringify({ error: 'offline', url: request.url }),
          { status: 503, headers: { 'Content-Type': 'application/json' } }
        );
      });
    });
  });
}
 
// ── Strategy: Stale-While-Revalidate ─────────────────────
function staleWhileRevalidate(request, cacheName) {
  return caches.open(cacheName).then(function(cache) {
    return cache.match(request).then(function(cached) {
      var fetchPromise = fetch(request).then(function(response) {
        if (response && response.ok && response.type !== 'opaque') {
          cache.put(request, response.clone());
        }
        return response;
      }).catch(function() {
        return null;
      });
 
      if (cached) return cached;
      return fetchPromise.then(function(r) {
        if (r) return r;
        return caches.match('/index.html', { cacheName: CACHE_SHELL })
          .then(function(c) {
            return c || new Response('آفلاین', { status: 503 });
          });
      });
    });
  });
}