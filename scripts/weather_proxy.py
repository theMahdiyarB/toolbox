#!/usr/bin/env python3
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
import urllib.request
import json

class ProxyHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        parsed_path = urlparse(self.path)
        
        if parsed_path.path != '/weather-proxy':
            self.send_error(404)
            return
            
        params = parse_qs(parsed_path.query)
        endpoint = params.get('endpoint', [None])[0]
        code = params.get('code', [None])[0]
        
        if not endpoint or not code:
            self.send_response(400)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps({"error": "Invalid request"}).encode())
            return
        
        # Map endpoints to IRIMO API URLs
        endpoint_map = {
            'gethava': 'https://webapp.irimo.ir/metapi/gethava.php',
            'forecast': 'https://webapp.irimo.ir/metapi/forecast.php',
            'getWrf': 'https://webapp.irimo.ir/metapi/getWrf.php'
        }
        
        if endpoint not in endpoint_map:
            self.send_response(400)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps({"error": "Invalid endpoint"}).encode())
            return
        
        try:
            url = f"{endpoint_map[endpoint]}?code={code}"
            req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
            
            with urllib.request.urlopen(req) as response:
                data = response.read()
                
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(data)
            
        except Exception as e:
            self.send_response(502)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps({"error": str(e)}).encode())

if __name__ == '__main__':
    server = HTTPServer(('0.0.0.0', 8085), ProxyHandler)
    print('Proxy server running on port 8085...')
    server.serve_forever()
