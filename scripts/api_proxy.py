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


class ProxyHandler(BaseHTTPRequestHandler):

    def log_message(self, fmt, *args):
        log(f"{self.address_string()} {fmt % args}")

    def log_error(self, fmt, *args):
        log(f"ERROR {self.address_string()} {fmt % args}")

    def _cors(self):
        self.send_header('Access-Control-Allow-Origin', '*')
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
    server = HTTPServer(('0.0.0.0', 8085), ProxyHandler)
    log("Listening on: /weather-proxy  /weather-static  /irsc-proxy  /post-track")
    server.serve_forever()
