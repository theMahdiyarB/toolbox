#!/usr/bin/env python3
"""
Fetches earthquake data from ble.ir and caches to earthquakes.json.
Run via cron: */15 * * * * /usr/bin/python3 /var/www/toolbox/scripts/fetch_earthquakes.py
"""
import subprocess, json, re, time, os, sys

BALE_URL   = 'https://ble.ir/irsc_public'
CACHE_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'earthquakes.json')
LOG_FILE   = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'fetch_eq.log')

def log(msg):
    ts = time.strftime('%Y-%m-%d %H:%M:%S')
    line = f"[{ts}] {msg}"
    print(line, flush=True)
    with open(LOG_FILE, 'a') as f:
        f.write(line + '\n')

def fetch():
    log("Fetching from ble.ir...")
    result = subprocess.run([
        'curl', '-s', '--max-time', '20',
        '-H', 'User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/148.0.0.0 Safari/537.36',
        '-H', 'Accept: text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        '-H', 'Accept-Language: fa,en;q=0.9',
        '--compressed', BALE_URL,
    ], capture_output=True, timeout=25)

    if result.returncode != 0:
        raise RuntimeError(f"curl failed: {result.stderr.decode()[:200]}")

    html = result.stdout.decode('utf-8', errors='replace')
    log(f"Fetched {len(html)} bytes")

    m = re.search(r'<script id="__NEXT_DATA__" type="application/json">(.*?)</script>', html, re.DOTALL)
    if not m:
        raise ValueError('__NEXT_DATA__ not found')

    data     = json.loads(m.group(1))
    messages = data['props']['pageProps']['messages']
    log(f"Total messages: {len(messages)}")

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
        eq['cities'] = [l.strip() for l in cities_m.group(1).strip().splitlines() if l.strip()] if cities_m else []

        provs_m = re.search(r'نزدیک\u200cترین مراکز استان:\s*\n((?:[^\n]+\n?){1,3})', text)
        eq['provinces'] = [l.strip() for l in provs_m.group(1).strip().splitlines() if l.strip()] if provs_m else []

        maps_m = re.search(r'(https://www\.google\.com/maps/place/[^\s\n]+)', text)
        eq['map_url'] = maps_m.group(1).strip() if maps_m else ''

        if eq['mag']:
            earthquakes.append(eq)

    log(f"Parsed {len(earthquakes)} earthquakes")

    output = {
        'cached_at': int(time.time()),
        'count':     len(earthquakes),
        'items':     earthquakes,
    }

    with open(CACHE_FILE, 'w', encoding='utf-8') as f:
        json.dump(output, f, ensure_ascii=False)
    log(f"Saved to {CACHE_FILE}")
    return len(earthquakes)

if __name__ == '__main__':
    try:
        n = fetch()
        sys.exit(0)
    except Exception as e:
        log(f"ERROR: {e}")
        sys.exit(1)
