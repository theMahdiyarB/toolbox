#!/usr/bin/env python3
import sys
import os
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
import urllib.request
import json
import re
import time
import traceback
import subprocess

LOG_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'api_proxy.log')
CACHE_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'earthquakes.json')

def log(msg):
    ts = time.strftime('%Y-%m-%d %H:%M:%S')
    line = f"[{ts}] {msg}"
    print(line, flush=True)
    try:
        with open(LOG_FILE, 'a', encoding='utf-8') as f:
            f.write(line + '\n')
    except Exception:
        pass

WEATHER_ENDPOINTS = {
    'gethava':     'https://webapp.irimo.ir/metapi/gethava.php',
    'forecast':    'https://webapp.irimo.ir/metapi/forecast.php',
    'getWrf':      'https://webapp.irimo.ir/metapi/getWrf.php',
    'weatherapib': 'https://webapp.irimo.ir/metapi/weatherapib.php',
}
WEATHER_STATIC = {
    'ostemp':  'https://webapp.irimo.ir/metapi/ostemp.php',
    'extemp':  'https://webapp.irimo.ir/metapi/extemp.php',
    'msglist': 'https://webapp.irimo.ir/metapi/msglist.php',
}
_static_cache = {}
_STATIC_TTL   = 300
BALE_URL       = 'https://ble.ir/irsc_public'
TAPIN_URL      = 'https://search.tapin.ir/order/'

# Origins allowed to call this proxy from a browser (CORS).
# Same-origin requests (no Origin header) always work; cross-origin is only
# allowed when the request Origin is in this set. Override for your deploy by
# editing this list — no env files needed.
ALLOWED_ORIGINS = {'https://mahdiyar.info'}


def parse_earthquakes(html: str) -> list:
    """Parse IRSC/ble.ir earthquake reports out of a Next.js __NEXT_DATA__ blob.

    Returns a list of dicts; raises ValueError if __NEXT_DATA__ is absent.
    Behavior is locked by scripts/tests/test_eq_parser.py.
    """
    m = re.search(r'<script id="__NEXT_DATA__" type="application/json">(.*?)</script>', html, re.DOTALL)
    if not m:
        raise ValueError('__NEXT_DATA__ not found')
    data = json.loads(m.group(1))
    messages = data['props']['pageProps']['messages']
    earthquakes = []
    for msg in messages:
        if msg.get('type') != 'TEXT':
            continue
        text = msg.get('message', {}).get('textMessage', {}).get('text', '')
        if 'گزارش مقدماتی زمین' not in text:
            continue
        eq = {'rid': str(msg['rid']), 'date_ts': msg['date']}

        def make_find(t):
            def find(label):
                r = re.search(label + r'[:\s]*([^\n]+)', t)
                return r.group(1).strip() if r else ''
            return find
        find = make_find(text)

        eq['mag']      = find('بزرگی')
        eq['location'] = find('محل وقوع')
        eq['datetime'] = find('تاریخ و زمان وقوع به وقت محلی')
        eq['lon']      = find('طول جغرافیایی')
        eq['lat']      = find('عرض جغرافیایی')
        eq['depth']    = find('عمق زمین')

        cities_m = re.search(r'نزدیک‌ترین شهرها:\s*\n((?:[^\n]+\n?){1,5})', text)
        eq['cities'] = [l.strip() for l in cities_m.group(1).strip().splitlines() if l.strip()] if cities_m else []

        provs_m = re.search(r'نزدیک‌ترین مراکز استان:\s*\n((?:[^\n]+\n?){1,3})', text)
        eq['provinces'] = [l.strip() for l in provs_m.group(1).strip().splitlines() if l.strip()] if provs_m else []

        maps_m = re.search(r'(https://www\.google\.com/maps/place/[^\s\n]+)', text)
        eq['map_url'] = maps_m.group(1).strip() if maps_m else ''

        if eq['mag']:
            earthquakes.append(eq)
    return earthquakes


def fetch_eq_html() -> str:
    """Scrape ble.ir/irsc_public and return the raw HTML (no parse/cache here)."""
    log(f"EQ fetch starting from {BALE_URL}")
    result = subprocess.run(
        ['curl', '-s', '--max-time', '20',
         '-H', 'User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/148.0.0.0 Safari/537.36',
         '-H', 'Accept: text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
         '-H', 'Accept-Language: fa,en;q=0.9', '--compressed', BALE_URL],
        capture_output=True, timeout=25)
    if result.returncode != 0:
        raise RuntimeError(f"curl failed (exit {result.returncode}): {result.stderr.decode()[:200]}")
    html = result.stdout.decode('utf-8', errors='replace')
    log(f"EQ fetch OK, HTML length={len(html)}")
    return html


def fetch_eq_and_cache() -> int:
    """Cron entry point: scrape, parse, and write earthquakes.json. Returns count."""
    html = fetch_eq_html()
    earthquakes = parse_earthquakes(html)
    if not earthquakes:
        raise RuntimeError("EQ fetch: no earthquakes parsed, not caching")
    output = {
        'cached_at': int(time.time()),
        'count':     len(earthquakes),
        'items':     earthquakes,
    }
    with open(CACHE_FILE, 'w', encoding='utf-8') as f:
        json.dump(output, f, ensure_ascii=False)
    log(f"EQ cache updated: {len(earthquakes)} items")
    return len(earthquakes)


def fetch_post_tracking(barcode):
    """Call search.tapin.ir/order/ via curl (bypasses VPS DNS issues)."""
    log(f"post-track: curl POST {TAPIN_URL} barcode={barcode}")
    payload = json.dumps({'barcode': barcode})
    result = subprocess.run(
        ['curl', '-s', '--max-time', '15',
         '-H', 'User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36',
         '-H', 'Content-Type: application/json',
         '-H', 'Origin: https://search.tapin.ir',
         '-H', 'Referer: https://search.tapin.ir/',
         '-H', 'Accept: application/json',
         '-d', payload,
         TAPIN_URL],
        capture_output=True, timeout=20)
    if result.returncode != 0:
        raise RuntimeError(f"curl failed (exit {result.returncode}): {result.stderr.decode()[:200]}")
    raw = result.stdout.decode('utf-8', errors='replace')
    log(f"post-track: response {len(raw)} bytes: {raw[:150]}")
    if not raw.strip():
        raise RuntimeError('پاسخ خالی از سرور')
    return json.loads(raw)


# ── پروکسی عمومی GET برای API‌هایی که CORS ندارند (فقط میزبان‌های فهرست سفید) ──
PROXY_HOSTS = {
    'translate.googleapis.com', 'lingva.ml', 'lingva.thedaviddelta.com', 'translate.plausibility.cloud',
    'api.mymemory.translated.net', 'www.seismicportal.eu', 'earthquake.usgs.gov',
    'api.priceto.day', 'nerkh.jahankhahan.shop', 'api.widgetify.ir', 'raw.githubusercontent.com',
    'backend.gheymat.online', 'api.zipodo.ir', 'api.bitpin.ir', 'apiv2.nobitex.ir',
    'api.tvmaze.com', 'v3.sg.media-imdb.com', 'api.themoviedb.org', 'moviesapi.ir',
    'v3-cinemeta.strem.io', 'imdb.iamidiotareyoutoo.com',
}
# میزبان‌های مجاز تصویر (پوستر). مرورگر به‌خاطر COEP نمی‌تواند تصویر بین‌مبدأ را مستقیم بگیرد؛ از /img-proxy رد می‌شود.
IMG_HOSTS = {'static.tvmaze.com', 'm.media-amazon.com', 'image.tmdb.org', 'moviesapi.ir', 'images.metahub.space', 'live.metahub.space', 'episodes.metahub.space', 'img.omdbapi.com'}
_IMG_MAX = 3 * 1024 * 1024
# TTL کش به ثانیه برای هر میزبان (پیش‌فرض _API_TTL). gheymat سقف ۲۵۰ درخواست در روز دارد.
HOST_TTL = {'v3-cinemeta.strem.io': 600, 'imdb.iamidiotareyoutoo.com': 600, 'backend.gheymat.online': 600, 'api.tvmaze.com': 600, 'api.themoviedb.org': 600, 'moviesapi.ir': 600, 'v3.sg.media-imdb.com': 600, 'api.mymemory.translated.net': 300}

# ── محدودیت نرخ برای هر IP کاربر (پنجره‌ی ۶۰ ثانیه‌ای) تا سهمیه‌ی مشترک سرور تمام نشود ──
RATE_LIMITS = {'/api-proxy': 60, '/translate-proxy': 20, '/img-proxy': 400}
_rate = {}


def rate_ok(ip, path):
    now = time.time()
    k = (ip, path)
    q = [t for t in _rate.get(k, []) if now - t < 60]
    if len(q) >= RATE_LIMITS[path]:
        _rate[k] = q
        return False
    q.append(now)
    _rate[k] = q
    if len(_rate) > 5000:
        for kk in [kk for kk, v in _rate.items() if not v or now - v[-1] > 60]:
            _rate.pop(kk, None)
    return True

_api_cache = {}
_API_TTL = 60
_API_MAX = 5 * 1024 * 1024
_UA = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'


def curl_get(url, timeout=12):
    """GET via curl (bypasses VPS DNS issues). Returns (status, bytes)."""
    r = subprocess.run(
        ['curl', '-s', '-L', '--max-time', str(timeout), '--max-filesize', str(_API_MAX), '--compressed',
         '-H', 'User-Agent: ' + _UA, '-H', 'Accept: application/json,*/*;q=0.8',
         '-w', '\n%{http_code}', url],
        capture_output=True, timeout=timeout + 5)
    if r.returncode != 0:
        raise RuntimeError(f"curl failed (exit {r.returncode}): {r.stderr.decode()[:150]}")
    body, _, code = r.stdout.rpartition(b'\n')
    return int(code or 0), body


def api_fetch(url):
    """Cached, allow-listed upstream GET. Returns (status, body)."""
    host = urlparse(url).hostname or ''
    if not url.startswith('https://') or host not in PROXY_HOSTS:
        raise PermissionError('host not allowed')
    now = time.time()
    ttl = HOST_TTL.get(host, _API_TTL)
    c = _api_cache.get(url)
    if c and now - c[0] < ttl:
        return 200, c[1]
    status, body = curl_get(url)
    if status == 200 and body:
        if len(_api_cache) > 200:
            _api_cache.clear()
        _api_cache[url] = (now, body)
    return status, body



def img_fetch(url):
    """Allow-listed image GET. Returns (content_type, bytes) or raises."""
    host = urlparse(url).hostname or ''
    if not url.startswith('https://') or host not in IMG_HOSTS:
        raise PermissionError('host not allowed')
    r = subprocess.run(
        ['curl', '-s', '-L', '--proto-redir', '=https', '--max-time', '12', '--max-filesize', str(_IMG_MAX),
         '-H', 'User-Agent: ' + _UA, '-H', 'Accept: image/*', url],
        capture_output=True, timeout=17)
    b = r.stdout
    if r.returncode != 0 or not b:
        raise RuntimeError('image fetch failed')
    if b[:3] == b'\xff\xd8\xff':
        ct = 'image/jpeg'
    elif b[:8] == b'\x89PNG\r\n\x1a\n':
        ct = 'image/png'
    elif b[:4] == b'RIFF' and b[8:12] == b'WEBP':
        ct = 'image/webp'
    elif b[:3] == b'GIF':
        ct = 'image/gif'
    else:
        raise RuntimeError('not an image')
    return ct, b


def translate_chain(text, frm, to):
    """Google (gtx) -> Lingva -> MyMemory, server-side (no CORS)."""
    from urllib.parse import quote
    q = quote(text, safe='')
    errs = []
    try:
        st, b = api_fetch(f'https://translate.googleapis.com/translate_a/single?client=gtx&dt=t&sl={frm}&tl={to}&q={q}')
        j = json.loads(b)
        out = ''.join((x[0] or '') for x in j[0])
        if st == 200 and out:
            return out, 'Google'
    except Exception as e:
        errs.append(f'Google: {e}')
    try:
        st, b = api_fetch(f'https://lingva.ml/api/v1/{frm}/{to}/{q}')
        out = json.loads(b).get('translation')
        if st == 200 and out:
            return out, 'Lingva'
    except Exception as e:
        errs.append(f'Lingva: {e}')
    raise RuntimeError('; '.join(errs) or 'no translation')


class ProxyHandler(BaseHTTPRequestHandler):

    def log_message(self, fmt, *args):
        log(f"{self.address_string()} {fmt % args}")

    def log_error(self, fmt, *args):
        log(f"ERROR {self.address_string()} {fmt % args}")

    def _cors(self):
        origin = self.headers.get('Origin', '')
        if origin in ALLOWED_ORIGINS:
            self.send_header('Access-Control-Allow-Origin', origin)
        # else: same-origin requests need no header; unknown cross-origin is denied.
        self.send_header('Access-Control-Allow-Methods', 'GET, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')

    def do_OPTIONS(self):
        self.send_response(204)
        self._cors()
        self.end_headers()

    def do_GET(self):
        parsed = urlparse(self.path)
        path   = parsed.path
        params = parse_qs(parsed.query)
        if path in RATE_LIMITS:
            log(f"GET {path}")  # پارامترها (متن ترجمه، کلید API) لاگ نمی‌شوند
            ip = (self.headers.get('X-Forwarded-For', '') or self.client_address[0]).split(',')[0].strip()
            if not rate_ok(ip, path):
                body = json.dumps({'error': 'too many requests'}).encode('utf-8')
                self.send_response(429)
                self.send_header('Content-Type', 'application/json; charset=utf-8')
                self.send_header('Retry-After', '60')
                self._cors(); self.end_headers()
                self.wfile.write(body)
                return
        else:
            log(f"GET {path} params={dict(params)}")

        if path == '/weather-proxy':
            endpoint = params.get('endpoint', [None])[0]
            code     = params.get('code',     [None])[0]
            log(f"weather request: endpoint={endpoint} code={code}")
            if not endpoint or not code:
                return self._json_error(400, 'Missing endpoint or code')
            if endpoint not in WEATHER_ENDPOINTS:
                return self._json_error(400, f'Unknown endpoint: {endpoint}')
            self._upstream(f"{WEATHER_ENDPOINTS[endpoint]}?code={code}", 'application/json')

        elif path == '/weather-static':
            endpoint = params.get('endpoint', [None])[0]
            log(f"weather-static: endpoint={endpoint}")
            if not endpoint or endpoint not in WEATHER_STATIC:
                return self._json_error(400, f'Unknown static endpoint: {endpoint}')
            now = time.time()
            cached = _static_cache.get(endpoint)
            if cached and (now - cached['ts']) < _STATIC_TTL:
                self.send_response(200)
                self.send_header('Content-Type', 'application/json; charset=utf-8')
                self._cors(); self.end_headers()
                self.wfile.write(cached['body'])
            else:
                try:
                    req = urllib.request.Request(WEATHER_STATIC[endpoint],
                        headers={'User-Agent': 'Mozilla/5.0 (compatible; IranToolbox/1.0)'})
                    with urllib.request.urlopen(req, timeout=10) as resp:
                        data = resp.read()
                    _static_cache[endpoint] = {'body': data, 'ts': time.time()}
                    self.send_response(200)
                    self.send_header('Content-Type', 'application/json; charset=utf-8')
                    self._cors(); self.end_headers()
                    self.wfile.write(data)
                except Exception as e:
                    log(f"weather-static error: {e}")
                    return self._json_error(502, str(e))

        elif path == '/irsc-proxy':
            try:
                with open(CACHE_FILE, 'r', encoding='utf-8') as cf:
                    body = cf.read().encode('utf-8')
                self.send_response(200)
                self.send_header('Content-Type', 'application/json; charset=utf-8')
                self._cors(); self.end_headers()
                self.wfile.write(body)
                log(f"irsc-proxy: served {len(body)} bytes")
            except FileNotFoundError:
                # Cache missing: generate it inline (no external script).
                try:
                    fetch_eq_and_cache()
                    with open(CACHE_FILE, 'r', encoding='utf-8') as cf:
                        body = cf.read().encode('utf-8')
                    self.send_response(200)
                    self.send_header('Content-Type', 'application/json; charset=utf-8')
                    self._cors(); self.end_headers()
                    self.wfile.write(body)
                except Exception as e2:
                    return self._json_error(502, f'Cache not ready: {e2}')
            except Exception as e:
                log(f"irsc-proxy error: {e}")
                return self._json_error(502, str(e))

        elif path == '/api-proxy':
            u = params.get('u', [None])[0]
            if not u:
                return self._json_error(400, 'Missing u')
            try:
                st, body = api_fetch(u)
            except PermissionError:
                return self._json_error(403, 'host not allowed')
            except Exception as e:
                log(f"api-proxy error: {e}")
                return self._json_error(502, str(e))
            self.send_response(st if 100 <= st < 600 and st != 0 else 502)
            self.send_header('Content-Type', 'application/json; charset=utf-8')
            self._cors(); self.end_headers()
            self.wfile.write(body)

        elif path == '/img-proxy':
            u = params.get('u', [None])[0]
            if not u:
                return self._json_error(400, 'Missing u')
            try:
                ct, body = img_fetch(u)
            except PermissionError:
                return self._json_error(403, 'host not allowed')
            except Exception as e:
                return self._json_error(502, str(e))
            self.send_response(200)
            self.send_header('Content-Type', ct)
            self.send_header('Cache-Control', 'public, max-age=604800, immutable')
            self.send_header('Cross-Origin-Resource-Policy', 'same-origin')
            self.end_headers()
            self.wfile.write(body)

        elif path == '/translate-proxy':
            text = (params.get('q', [''])[0] or '').strip()
            frm = params.get('from', ['en'])[0]
            to = params.get('to', ['fa'])[0]
            if not text or len(text) > 1800 or not re.match(r'^[a-zA-Z-]{2,7}$', frm) or not re.match(r'^[a-zA-Z-]{2,7}$', to):
                return self._json_error(400, 'bad translate params')
            try:
                out, src = translate_chain(text, frm, to)
                body = json.dumps({'text': out, 'src': src}, ensure_ascii=False).encode('utf-8')
                self.send_response(200)
                self.send_header('Content-Type', 'application/json; charset=utf-8')
                self._cors(); self.end_headers()
                self.wfile.write(body)
            except Exception as e:
                log(f"translate-proxy error: {e}")
                return self._json_error(502, str(e))

        elif path == '/post-track':
            barcode = params.get('barcode', [None])[0]
            log(f"post-track: barcode={barcode}")
            if not barcode:
                return self._json_error(400, 'پارامتر barcode اجباری است.')
            barcode = barcode.strip()
            if not re.match(r'^\d{10,30}$', barcode):
                return self._json_error(400, 'بارکد باید بین ۱۰ تا ۳۰ رقم باشد.')
            try:
                data = fetch_post_tracking(barcode)
                body = json.dumps(data, ensure_ascii=False).encode('utf-8')
                self.send_response(200)
                self.send_header('Content-Type', 'application/json; charset=utf-8')
                self._cors(); self.end_headers()
                self.wfile.write(body)
                log(f"post-track: served code={data.get('code')} for {barcode}")
            except Exception as e:
                log(f"post-track error: {e}\n{traceback.format_exc()}")
                return self._json_error(502, f'خطا در دریافت اطلاعات: {str(e)}')

        else:
            log(f"404: {path}")
            self.send_error(404, 'Not found')

    def _json_error(self, code, message):
        log(f"Returning {code}: {message}")
        body = json.dumps({'error': message}, ensure_ascii=False).encode('utf-8')
        self.send_response(code)
        self.send_header('Content-Type', 'application/json; charset=utf-8')
        self._cors(); self.end_headers()
        self.wfile.write(body)

    def _upstream(self, url, content_type):
        try:
            log(f"Fetching upstream: {url}")
            req = urllib.request.Request(url,
                headers={'User-Agent': 'Mozilla/5.0 (compatible; IranToolbox/1.0)'})
            with urllib.request.urlopen(req, timeout=10) as resp:
                data = resp.read()
            log(f"Upstream {url} -> {len(data)} bytes")
            self.send_response(200)
            self.send_header('Content-Type', content_type)
            self._cors(); self.end_headers()
            self.wfile.write(data)
        except urllib.error.HTTPError as e:
            self._json_error(502, f'Upstream HTTP {e.code}: {e.reason}')
        except Exception as e:
            log(f"Upstream error: {e}\n{traceback.format_exc()}")
            self._json_error(502, str(e))


if __name__ == '__main__':
    if len(sys.argv) > 1 and sys.argv[1] == '--fetch-eq':
        # Standalone cron mode: scrape + cache, then exit.
        try:
            n = fetch_eq_and_cache()
            sys.exit(0)
        except Exception as e:
            log(f"fetch-eq failed: {e}")
            sys.exit(1)
    log(f"api_proxy starting on port 8085 — log file: {LOG_FILE}")
    # Bind to loopback only; expose publicly via the reverse proxy (Caddy).
    server = HTTPServer(('127.0.0.1', 8085), ProxyHandler)
    log("Listening on: /weather-proxy  /weather-static  /irsc-proxy  /post-track  /api-proxy  /translate-proxy  /img-proxy")
    server.serve_forever()
