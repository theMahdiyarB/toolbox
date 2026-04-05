// ============================================================
//  Service Worker — جعبه‌ابزار آفلاین
//  Strategies:
//    - App shell (HTML/CSS/JS/fonts): Stale-While-Revalidate
//    - Static assets (images, maps): Cache-First
//    - External/opaque requests: Network-only (skip)
// ============================================================

const CACHE_VERSION = 'toolbox-v3.2';
const CACHE_SHELL   = CACHE_VERSION + '-shell';
const CACHE_ASSETS  = CACHE_VERSION + '-assets';

// Pages that must be served as their own HTML (not redirected to index.html)
const STANDALONE_PAGES = ['/iran', '/iran/', '/iran.html'];

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
  '/lib/qrcode.js',
  '/lib/jsQR.js',
  '/lib/qr-code-styling.js',
  '/lib/browser-image-compression.js',
  '/lib/pdf.mjs',
  '/lib/pdf.worker.mjs',
  '/lib/function-plot.js',
  '/lib/math.js',
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

// ── Install: cache app shell (resilient — one missing file won't abort) ───────
self.addEventListener('install', function(event) {
  event.waitUntil(
    caches.open(CACHE_SHELL).then(function(cache) {
      var results = SHELL_URLS.map(function(url) {
        return cache.add(url).catch(function(err) {
          console.warn('[SW] Failed to cache:', url, err);
        });
      });
      return Promise.all(results);
    }).then(function() {
      console.log('[SW] Install complete');
      return self.skipWaiting();
    })
  );
});

// ── Activate: delete old caches ───────────────────────────────────────────────
self.addEventListener('activate', function(event) {
  var KEEP = [CACHE_SHELL, CACHE_ASSETS];
  event.waitUntil(
    caches.keys()
      .then(function(names) {
        return Promise.all(
          names.filter(function(n) { return !KEEP.includes(n); })
               .map(function(n)    { return caches.delete(n); })
        );
      })
      .then(function() { return self.clients.claim(); })
      .then(function() { return self.clients.matchAll({ type: 'window' }); })
      .then(function(clients) {
        clients.forEach(function(client) {
          client.postMessage({ type: 'SW_UPDATED', version: CACHE_VERSION });
        });
      })
  );
});

// ── Fetch ─────────────────────────────────────────────────────────────────────
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

  // ── Navigation requests ──────────────────────────────────────────────────────
  if (event.request.mode === 'navigate') {

    // Standalone pages (/iran) must be served as themselves, not as index.html
    if (STANDALONE_PAGES.includes(path)) {
      event.respondWith(
        caches.match('/iran.html', { cacheName: CACHE_SHELL })
          .then(function(cached) {
            if (cached) {
              fetch(event.request)
                .then(function(r) {
                  if (r && r.ok) {
                    caches.open(CACHE_SHELL).then(function(c) { c.put('/iran.html', r); });
                  }
                }).catch(function() {});
              return cached;
            }
            return fetch(event.request).catch(function() {
              return new Response(
                '<h1 dir="rtl" style="font-family:sans-serif;text-align:center;padding:40px">برای اولین بار باید آنلاین باشید</h1>',
                { status: 503, headers: { 'Content-Type': 'text/html; charset=utf-8' } }
              );
            });
          })
      );
      return;
    }

    // All other navigations → SPA shell (index.html)
    event.respondWith(
      caches.match('/index.html', { cacheName: CACHE_SHELL })
        .then(function(cached) {
          if (cached) {
            fetch(event.request)
              .then(function(response) {
                if (response && response.ok) {
                  caches.open(CACHE_SHELL).then(function(c) { c.put(event.request, response); });
                }
              }).catch(function() {});
            return cached;
          }
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

// ── Strategy: Cache-First ─────────────────────────────────────────────────────
function cacheFirst(request, cacheName) {
  return caches.open(cacheName).then(function(cache) {
    return cache.match(request).then(function(cached) {
      if (cached) return cached;
      return fetch(request).then(function(response) {
        if (response && response.ok) cache.put(request, response.clone());
        return response;
      }).catch(function() {
        return new Response(JSON.stringify({ error: 'offline', url: request.url }),
          { status: 503, headers: { 'Content-Type': 'application/json' } });
      });
    });
  });
}

// ── Strategy: Stale-While-Revalidate ─────────────────────────────────────────
function staleWhileRevalidate(request, cacheName) {
  return caches.open(cacheName).then(function(cache) {
    return cache.match(request).then(function(cached) {
      var fetchPromise = fetch(request).then(function(response) {
        if (response && response.ok && response.type !== 'opaque') {
          cache.put(request, response.clone());
        }
        return response;
      }).catch(function() { return null; });

      if (cached) return cached;
      return fetchPromise.then(function(r) {
        if (r) return r;
        return caches.match('/index.html', { cacheName: CACHE_SHELL })
          .then(function(c) { return c || new Response('آفلاین', { status: 503 }); });
      });
    });
  });
}