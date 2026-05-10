#!/usr/bin/env python3
"""
api_proxy.py — Unified HTTP proxy for toolbox (port 8085)

Endpoints:
  GET /weather-proxy?endpoint=<name>&code=<code>   — IRIMO weather API
  GET /irsc-proxy                                  — IRSC earthquake XML feed
"""

from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
import urllib.request
import json
import sys
import traceback
import ssl

IRIMO_ENDPOINTS = {
    'gethava':   'https://webapp.irimo.ir/metapi/gethava.php',
    'forecast':  'https://webapp.irimo.ir/metapi/forecast.php',
    'getWrf':    'https://webapp.irimo.ir/metapi/getWrf.php',
}

IRSC_XML_URL = 'http://irsc.ut.ac.ir/events_list_fa.xml'

CORS_HEADERS = {
    'Access-Control-Allow-Origin': '*',
    'Access-Control-Allow-Methods': 'GET, OPTIONS',
    'Access-Control-Allow-Headers': 'Content-Type',
}


class ProxyHandler(BaseHTTPRequestHandler):

    def log_message(self, fmt, *args):
        # Suppress default request logs; remove this line to re-enable.
        pass

    def send_cors_headers(self):
        for k, v in CORS_HEADERS.items():
            self.send_header(k, v)

    def do_OPTIONS(self):
        self.send_response(204)
        self.send_cors_headers()
        self.end_headers()

    def do_GET(self):
        parsed = urlparse(self.path)
        path   = parsed.path

        if path == '/weather-proxy':
            self._handle_weather(parsed)
        elif path == '/irsc-proxy':
            self._handle_irsc()
        else:
            self.send_response(404)
            self.send_header('Content-Type', 'application/json')
            self.send_cors_headers()
            self.end_headers()
            self.wfile.write(json.dumps({'error': 'Not found'}).encode())

    # ──────────────────────────────────────────────
    # IRIMO weather proxy
    # ──────────────────────────────────────────────
    def _handle_weather(self, parsed):
        params   = parse_qs(parsed.query)
        endpoint = params.get('endpoint', [None])[0]
        code     = params.get('code', [None])[0]

        if not endpoint or not code:
            self._json_error(400, 'Missing endpoint or code parameter')
            return

        if endpoint not in IRIMO_ENDPOINTS:
            self._json_error(400, f'Unknown endpoint: {endpoint}')
            return

        url = f'{IRIMO_ENDPOINTS[endpoint]}?code={code}'
        self._fetch_and_relay(url, 'application/json')

    # ──────────────────────────────────────────────
    # IRSC earthquake XML proxy
    # ──────────────────────────────────────────────
    def _handle_irsc(self):
        self._fetch_and_relay(IRSC_XML_URL, 'application/xml; charset=utf-8')

    # ──────────────────────────────────────────────
    # Shared fetch helper
    # ──────────────────────────────────────────────
    def _fetch_and_relay(self, url, content_type):
        try:
            print(f'[PROXY] Fetching: {url}', file=sys.stderr, flush=True)
            req = urllib.request.Request(
                url,
                headers={
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/148.0.0.0 Safari/537.36',
                    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                    'Accept-Language': 'en-US,en;q=0.9,fa;q=0.8',
                    'Accept-Encoding': 'gzip, deflate',
                    'DNT': '1',
                    'Connection': 'keep-alive',
                    'Upgrade-Insecure-Requests': '1',
                    'Referer': 'https://irsc.ut.ac.ir/',
                }
            )
            
            # Create SSL context that doesn't verify certificates
            ssl_context = ssl.create_default_context()
            ssl_context.check_hostname = False
            ssl_context.verify_mode = ssl.CERT_NONE
            
            with urllib.request.urlopen(req, timeout=60, context=ssl_context) as resp:
                data = resp.read()

            self.send_response(200)
            self.send_header('Content-Type', content_type)
            self.send_cors_headers()
            self.end_headers()
            self.wfile.write(data)

        except urllib.error.HTTPError as e:
            msg = f'Upstream HTTP {e.code}: {e.reason}'
            print(f'[PROXY] HTTPError: {msg}', file=sys.stderr, flush=True)
            self._json_error(502, msg)
        except urllib.error.URLError as e:
            msg = f'Upstream unreachable: {e.reason}'
            print(f'[PROXY] URLError: {msg}', file=sys.stderr, flush=True)
            self._json_error(502, msg)
        except Exception as e:
            msg = str(e)
            print(f'[PROXY] Exception: {msg}', file=sys.stderr, flush=True)
            traceback.print_exc(file=sys.stderr)
            self._json_error(500, msg)

    def _json_error(self, code, msg):
        body = json.dumps({'error': msg}).encode()
        self.send_response(code)
        self.send_header('Content-Type', 'application/json')
        self.send_cors_headers()
        self.end_headers()
        self.wfile.write(body)


if __name__ == '__main__':
    PORT = 8085
    server = HTTPServer(('0.0.0.0', PORT), ProxyHandler)
    print(f'api_proxy running on port {PORT}')
    server.serve_forever()