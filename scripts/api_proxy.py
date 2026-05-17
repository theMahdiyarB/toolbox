#!/usr/bin/env python3
import sys
import os
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
import urllib.request
import urllib.error
import json
import re
import time
import traceback

# ── Logging ─────────────────────────────────────────────────────────────────
LOG_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'api_proxy.log')

def log(msg):
    ts  = time.strftime('%Y-%m-%d %H:%M:%S')
    line = f"[{ts}] {msg}"
    print(line, flush=True)
    try:
        with open(LOG_FILE, 'a', encoding='utf-8') as f:
            f.write(line + '\n')
    except Exception:
        pass

# ── Config ───────────────────────────────────────────────────────────────────
WEATHER_ENDPOINTS = {
    'gethava':  'https://webapp.irimo.ir/metapi/gethava.php',
    'forecast': 'https://webapp.irimo.ir/metapi/forecast.php',
    'getWrf':   'https://webapp.irimo.ir/metapi/getWrf.php',
}

BALE_URL  = 'https://ble.ir/irsc_public'
CACHE_TTL = 3600  # 1 hour

_eq_cache = {'data': None, 'ts': 0}


# ── Earthquake scraper ───────────────────────────────────────────────────────
def fetch_earthquakes():
    log(f"EQ fetch starting from {BALE_URL}")
    req = urllib.request.Request(
        BALE_URL,
        headers={
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
                          'AppleWebKit/537.36 (KHTML, like Gecko) '
                          'Chrome/148.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml',
        }
    )
    with urllib.request.urlopen(req, timeout=15) as resp:
        html = resp.read().decode('utf-8', errors='replace')
    log(f"EQ fetch OK, HTML length={len(html)}")

    m = re.search(r'<script id="__NEXT_DATA__" type="application/json">(.*?)</script>', html, re.DOTALL)
    if not m:
        raise ValueError('__NEXT_DATA__ not found in page')

    data     = json.loads(m.group(1))
    messages = data['props']['pageProps']['messages']
    log(f"EQ messages total={len(messages)}")

    earthquakes = []
    for msg in messages:
        if msg.get('type') != 'TEXT':
            continue
        text = msg.get('message', {}).get('textMessage', {}).get('text', '')
        if 'گزارش مقدماتی زمینلرزه' not in text:
            continue

        eq = {'rid': str(msg['rid']), 'date_ts': msg['date']}

        # Fix: define find as a lambda using the local text value, not a closure
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
        eq['depth']    = find('عمق زمینلرزه')

        # Cities — Bale text uses \n between items
        cities_m = re.search(r'نزدیکترین شهرها:\s*\n((?:[^\n]+\n?){1,5})', text)
        eq['cities'] = (
            [l.strip() for l in cities_m.group(1).strip().splitlines() if l.strip()]
            if cities_m else []
        )

        provs_m = re.search(r'نزدیکترین مراکز استان:\s*\n((?:[^\n]+\n?){1,3})', text)
        eq['provinces'] = (
            [l.strip() for l in provs_m.group(1).strip().splitlines() if l.strip()]
            if provs_m else []
        )

        maps_m = re.search(r'(https://www\.google\.com/maps/place/[^\s\n]+)', text)
        eq['map_url'] = maps_m.group(1).strip() if maps_m else ''

        if eq['mag']:
            earthquakes.append(eq)

    log(f"EQ parsed {len(earthquakes)} earthquake messages")
    if earthquakes:
        log(f"EQ sample[0]: mag={earthquakes[0]['mag']} loc={earthquakes[0]['location'][:40]}")
    return earthquakes


# ── HTTP Handler ─────────────────────────────────────────────────────────────
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

        # ── /weather-proxy ────────────────────────────────────────────────
        if path == '/weather-proxy':
            endpoint = params.get('endpoint', [None])[0]
            code     = params.get('code',     [None])[0]
            log(f"weather request: endpoint={endpoint} code={code}")

            if not endpoint or not code:
                return self._json_error(400, 'Missing endpoint or code')
            if endpoint not in WEATHER_ENDPOINTS:
                return self._json_error(400, f'Unknown endpoint: {endpoint}')

            url = f"{WEATHER_ENDPOINTS[endpoint]}?code={code}"
            log(f"weather upstream URL: {url}")
            self._upstream(url, content_type='application/json')

        # ── /irsc-proxy ───────────────────────────────────────────────────
        elif path == '/irsc-proxy':
            now = time.time()
            age = now - _eq_cache['ts']
            log(f"irsc-proxy: cache_age={age:.0f}s TTL={CACHE_TTL}s data={'yes' if _eq_cache['data'] else 'no'}")

            if _eq_cache['data'] is None or age > CACHE_TTL:
                try:
                    _eq_cache['data'] = fetch_earthquakes()
                    _eq_cache['ts']   = time.time()
                    log(f"EQ cache refreshed: {len(_eq_cache['data'])} items")
                except Exception as e:
                    log(f"EQ fetch FAILED: {e}\n{traceback.format_exc()}")
                    if _eq_cache['data'] is None:
                        return self._json_error(502, str(e))
                    log("Serving stale cache after fetch failure")

            body = json.dumps({
                'cached_at': int(_eq_cache['ts']),
                'count':     len(_eq_cache['data']),
                'items':     _eq_cache['data'],
            }, ensure_ascii=False).encode('utf-8')

            self.send_response(200)
            self.send_header('Content-Type', 'application/json; charset=utf-8')
            self._cors()
            self.end_headers()
            self.wfile.write(body)
            log(f"irsc-proxy: sent {len(body)} bytes, {len(_eq_cache['data'])} items")

        else:
            log(f"404: {path}")
            self.send_error(404, 'Not found')

    def _json_error(self, code, message):
        log(f"Returning {code}: {message}")
        body = json.dumps({'error': message}).encode()
        self.send_response(code)
        self.send_header('Content-Type', 'application/json')
        self._cors()
        self.end_headers()
        self.wfile.write(body)

    def _upstream(self, url, content_type):
        try:
            log(f"Fetching upstream: {url}")
            req = urllib.request.Request(
                url,
                headers={'User-Agent': 'Mozilla/5.0 (compatible; IranToolbox/1.0)'}
            )
            with urllib.request.urlopen(req, timeout=10) as resp:
                status = resp.status
                data   = resp.read()
            log(f"Upstream {url} -> HTTP {status}, {len(data)} bytes")

            self.send_response(200)
            self.send_header('Content-Type', content_type)
            self._cors()
            self.end_headers()
            self.wfile.write(data)

        except urllib.error.HTTPError as e:
            log(f"Upstream HTTPError {e.code}: {e.reason} for {url}")
            self._json_error(502, f'Upstream HTTP {e.code}: {e.reason}')
        except Exception as e:
            log(f"Upstream error for {url}: {e}\n{traceback.format_exc()}")
            self._json_error(502, str(e))


# ── Main ─────────────────────────────────────────────────────────────────────
if __name__ == '__main__':
    log(f"api_proxy starting on port 8085 — log file: {LOG_FILE}")
    server = HTTPServer(('0.0.0.0', 8085), ProxyHandler)
    log("Listening...")
    server.serve_forever()