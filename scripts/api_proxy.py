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

# ── Logging ─────────────────────────────────────────────────────────────────
LOG_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'api_proxy.log')

def log(msg):
    ts   = time.strftime('%Y-%m-%d %H:%M:%S')
    line = f"[{ts}] {msg}"
    print(line, flush=True)
    try:
        with open(LOG_FILE, 'a', encoding='utf-8') as f:
            f.write(line + '\n')
    except Exception:
        pass

# ── Config ───────────────────────────────────────────────────────────────────
WEATHER_ENDPOINTS = {
    'gethava':     'https://webapp.irimo.ir/metapi/gethava.php',
    'forecast':    'https://webapp.irimo.ir/metapi/forecast.php',
    'getWrf':      'https://webapp.irimo.ir/metapi/getWrf.php',
    'weatherapib': 'https://webapp.irimo.ir/metapi/weatherapib.php',
}

# Static endpoints — no code param, cached for 5 minutes
WEATHER_STATIC = {
    #'warning': 'https://webapp.irimo.ir/metapi/warning.php',
    'ostemp':  'https://webapp.irimo.ir/metapi/ostemp.php',
    'extemp':  'https://webapp.irimo.ir/metapi/extemp.php',
    'msglist': 'https://webapp.irimo.ir/metapi/msglist.php',
}
_static_cache = {}
_STATIC_TTL   = 300  # 5 minutes

BALE_URL  = 'https://ble.ir/irsc_public'
CACHE_TTL = 3600  # 1 hour


# ── Earthquake scraper ───────────────────────────────────────────────────────
def fetch_earthquakes():
    log(f"EQ fetch starting from {BALE_URL}")
    result = subprocess.run(
        [
            'curl', '-s', '--max-time', '20',
            '-H', 'User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/148.0.0.0 Safari/537.36',
            '-H', 'Accept: text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            '-H', 'Accept-Language: fa,en;q=0.9',
            '--compressed',
            BALE_URL,
        ],
        capture_output=True,
        timeout=25,
    )
    if result.returncode != 0:
        raise RuntimeError(f"curl failed (exit {result.returncode}): {result.stderr.decode()[:200]}")
    html = result.stdout.decode('utf-8', errors='replace')
    log(f"EQ fetch OK via curl, HTML length={len(html)}")

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

        cities_m = re.search(r'نزدیک\u200cترین شهرها:\s*\n((?:[^\n]+\n?){1,5})', text)
        eq['cities'] = (
            [l.strip() for l in cities_m.group(1).strip().splitlines() if l.strip()]
            if cities_m else []
        )

        provs_m = re.search(r'نزدیک\u200cترین مراکز استان:\s*\n((?:[^\n]+\n?){1,3})', text)
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

        # ── /weather-proxy?endpoint=<name>&code=<code> ────────────────────
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

        # ── /weather-static?endpoint=<name> ──────────────────────────────
        elif path == '/weather-static':
            endpoint = params.get('endpoint', [None])[0]
            log(f"weather-static: endpoint={endpoint}")
            if not endpoint or endpoint not in WEATHER_STATIC:
                return self._json_error(400, f'Unknown static endpoint: {endpoint}')
            now    = time.time()
            cached = _static_cache.get(endpoint)
            if cached and (now - cached['ts']) < _STATIC_TTL:
                log(f"weather-static: serving cached {endpoint} ({len(cached['body'])} bytes)")
                self.send_response(200)
                self.send_header('Content-Type', 'application/json; charset=utf-8')
                self._cors()
                self.end_headers()
                self.wfile.write(cached['body'])
            else:
                url = WEATHER_STATIC[endpoint]
                log(f"weather-static: fetching {url}")
                try:
                    req = urllib.request.Request(
                        url,
                        headers={'User-Agent': 'Mozilla/5.0 (compatible; IranToolbox/1.0)'}
                    )
                    with urllib.request.urlopen(req, timeout=10) as resp:
                        data = resp.read()
                    _static_cache[endpoint] = {'body': data, 'ts': time.time()}
                    self.send_response(200)
                    self.send_header('Content-Type', 'application/json; charset=utf-8')
                    self._cors()
                    self.end_headers()
                    self.wfile.write(data)
                    log(f"weather-static: cached {endpoint} ({len(data)} bytes)")
                except Exception as e:
                    log(f"weather-static error: {e}")
                    return self._json_error(502, str(e))

        # ── /irsc-proxy — serve from file cache ───────────────────────────
        elif path == '/irsc-proxy':
            cache_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'earthquakes.json')
            log(f"irsc-proxy: reading cache file")
            try:
                with open(cache_file, 'r', encoding='utf-8') as cf:
                    body = cf.read().encode('utf-8')
                self.send_response(200)
                self.send_header('Content-Type', 'application/json; charset=utf-8')
                self._cors()
                self.end_headers()
                self.wfile.write(body)
                log(f"irsc-proxy: served {len(body)} bytes")
            except FileNotFoundError:
                log("irsc-proxy: no cache file, triggering fetch_earthquakes.py")
                script = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'fetch_earthquakes.py')
                r = subprocess.run([sys.executable, script], timeout=35, capture_output=True)
                log(f"fetch result: exit={r.returncode} {r.stdout.decode()[-200:]}")
                try:
                    with open(cache_file, 'r', encoding='utf-8') as cf:
                        body = cf.read().encode('utf-8')
                    self.send_response(200)
                    self.send_header('Content-Type', 'application/json; charset=utf-8')
                    self._cors()
                    self.end_headers()
                    self.wfile.write(body)
                except Exception as e2:
                    return self._json_error(502, f'Cache not ready: {e2}')
            except Exception as e:
                log(f"irsc-proxy error: {e}")
                return self._json_error(502, str(e))

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
    log("Listening on: /weather-proxy  /weather-static  /irsc-proxy")
    server.serve_forever()