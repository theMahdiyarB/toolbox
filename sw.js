// ============================================================
//  Service Worker — جعبه‌ابزار آفلاین 
//  Strategies:
//    - App shell (HTML/CSS/JS/fonts): Stale-While-Revalidate
//    - Static assets (images, maps): Cache-First
//    - External/opaque requests: Network-only (skip)
// ============================================================

const CACHE_VERSION = 'toolbox-v2.6';
const CACHE_SHELL   = CACHE_VERSION + '-shell';   // HTML, CSS, JS, fonts
const CACHE_ASSETS  = CACHE_VERSION + '-assets';  // images, maps, large files

// App shell — precached on install
const SHELL_URLS = [
  './',
  './index.html',
  './iran.html',
  './main.css',
  './main.js',
  './manifest.json',
  './favicon.png',
  './icon-512.png',
  './Vazirmatn-VF.ttf',
  './lib/qrcode.js',
  './lib/jsQR.js',
  './lib/qr-code-styling.js',
  './lib/browser-image-compression.js',
  './lib/pdf.mjs',
  './lib/pdf.worker.mjs',
  './lib/function-plot.js',
  './lib/math.js',
];

// ── Install: cache app shell ──────────────────────────────
self.addEventListener('install', function(event) {
  event.waitUntil(
    caches.open(CACHE_SHELL)
      .then(function(cache) {
        return Promise.allSettled(
          SHELL_URLS.map(function(url) {
            return cache.add(url).catch(function(err) {
              console.warn('[SW] Precache failed:', url, err.message);
            });
          })
        );
      })
      .then(function() {
        // Take control immediately — don't wait for old tabs to close
        return self.skipWaiting();
      })
  );
});

// ── Activate: delete all old caches ──────────────────────
self.addEventListener('activate', function(event) {
  const KEEP = [CACHE_SHELL, CACHE_ASSETS];
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
        // Take control of all open tabs immediately
        return self.clients.claim();
      })
      .then(function() {
        // Tell all open tabs that a new version is active
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
  // Only handle GET
  if (event.request.method !== 'GET') return;

  const url = new URL(event.request.url);

  // Skip cross-origin requests entirely (fonts CDN, etc.)
  if (url.origin !== self.location.origin) return;

  const path = url.pathname;

  // ── Large on-demand files (maps, PDFs): Cache-First ──
  // Not precached, but cached on first access and served offline after
  if (path.startsWith('/maps/') || path.endsWith('.pdf')) {
    event.respondWith(cacheFirst(event.request, CACHE_ASSETS));
    return;
  }

  // ── App shell (HTML, CSS, JS, fonts): Stale-While-Revalidate ──
  // Serve from cache instantly, update cache in background
  event.respondWith(staleWhileRevalidate(event.request, CACHE_SHELL));
});

// ── Strategy: Cache-First ────────────────────────────────
// Serve from cache if available, fetch and cache if not.
// Good for large immutable files.
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
// Serve from cache immediately (no waiting), then fetch fresh
// copy and update cache silently for next time.
function staleWhileRevalidate(request, cacheName) {
  return caches.open(cacheName).then(function(cache) {
    return cache.match(request).then(function(cached) {
      // Kick off a background fetch regardless
      var fetchPromise = fetch(request).then(function(response) {
        if (response && response.ok && response.type !== 'opaque') {
          cache.put(request, response.clone());
        }
        return response;
      }).catch(function() {
        // Network failed — that's fine, we have the cache
        return null;
      });

      // Return cache immediately if available, otherwise wait for network
      return cached || fetchPromise.then(function(r) {
        return r || caches.match('./index.html').then(function(c) {
          return c || new Response('آفلاین', { status: 503 });
        });
      });
    });
  });
}