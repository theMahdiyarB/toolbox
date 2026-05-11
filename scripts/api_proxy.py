#!/usr/bin/env python3
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
import urllib.request
import json

WEATHER_ENDPOINTS = {
    'gethava':  'https://webapp.irimo.ir/metapi/gethava.php',
    'forecast': 'https://webapp.irimo.ir/metapi/forecast.php',
    'getWrf':   'https://webapp.irimo.ir/metapi/getWrf.php',
}

IRSC_URL = 'http://irsc.ut.ac.ir/events_list_fa.xml'


class ProxyHandler(BaseHTTPRequestHandler):

    def log_message(self, fmt, *args):
        print(f"[proxy] {self.address_string()} {fmt % args}")

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

        # /weather-proxy?endpoint=<name>&code=<station_code>
        if path == '/weather-proxy':
            endpoint = params.get('endpoint', [None])[0]
            code     = params.get('code',     [None])[0]

            if not endpoint or not code:
                return self._json_error(400, 'Missing endpoint or code')

            if endpoint not in WEATHER_ENDPOINTS:
                return self._json_error(400, f'Unknown endpoint: {endpoint}')

            url = f"{WEATHER_ENDPOINTS[endpoint]}?code={code}"
            self._upstream(url, content_type='application/json')

        # /irsc-proxy  (no params needed)
        elif path == '/irsc-proxy':
            self._upstream(IRSC_URL, content_type='application/xml; charset=utf-8')

        else:
            self.send_error(404, 'Not found')

    # helpers

    def _json_error(self, code, message):
        body = json.dumps({'error': message}).encode()
        self.send_response(code)
        self.send_header('Content-Type', 'application/json')
        self._cors()
        self.end_headers()
        self.wfile.write(body)

    def _upstream(self, url, content_type):
        try:
            req = urllib.request.Request(
                url,
                headers={'User-Agent': 'Mozilla/5.0 (compatible; IranToolbox/1.0)'}
            )
            with urllib.request.urlopen(req, timeout=10) as resp:
                data = resp.read()

            self.send_response(200)
            self.send_header('Content-Type', content_type)
            self._cors()
            self.end_headers()
            self.wfile.write(data)

        except urllib.error.HTTPError as e:
            self._json_error(502, f'Upstream HTTP {e.code}: {e.reason}')
        except Exception as e:
            self._json_error(502, str(e))


if __name__ == '__main__':
    server = HTTPServer(('0.0.0.0', 8085), ProxyHandler)
    print('api_proxy running on port 8085  (/weather-proxy  /irsc-proxy)')
    server.serve_forever()