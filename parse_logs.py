#!/usr/bin/env python3
"""
parse_logs.py — Caddy JSON access log → stats.json aggregator
Zero dependencies — Python 3.6+ stdlib only.

Usage:
    python3 parse_logs.py

Environment variables (all optional):
    LOG_FILE     Path to Caddy's JSON access log
                 Default: /var/log/caddy/access.log
    OUTPUT_FILE  Where to write stats.json
                 Default: /var/www/toolbox/stats.json

Cron (every 5 minutes):
    */5 * * * * python3 /var/www/toolbox/parse_logs.py >> /var/log/parse_logs.log 2>&1
"""

import json
import os
import shutil
import re
import sys
import tempfile
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlparse

# ── CONFIG ────────────────────────────────────────────────────────────────────

LOG_FILE    = os.environ.get("LOG_FILE",    "/var/log/caddy/access.log")
OUTPUT_FILE = os.environ.get("OUTPUT_FILE", "/var/www/toolbox/stats.json")

TRACKED_PATHS = {"/", "/index.html", "/iran.html", "/iran", "/analytics.html"}

IGNORE_EXTS = {
    ".js", ".css", ".png", ".jpg", ".jpeg", ".gif", ".svg", ".ico",
    ".woff", ".woff2", ".ttf", ".otf", ".webp", ".avif",
    ".json", ".map", ".mjs", ".pdf", ".txt", ".xml", ".manifest",
}

BOT_PATTERNS = [
    "bot", "crawler", "spider", "slurp", "facebookexternalhit",
    "curl", "wget", "python-requests", "go-http", "okhttp",
    "axios", "libwww", "java/", "ruby", "perl/",
]

# ── HELPERS ───────────────────────────────────────────────────────────────────

def is_bot(ua: str) -> bool:
    if not ua:
        return True
    low = ua.lower()
    return any(p in low for p in BOT_PATTERNS)


def is_static(uri: str) -> bool:
    ext = Path(uri.split("?")[0]).suffix.lower()
    return ext in IGNORE_EXTS


def is_tracked(uri: str) -> bool:
    clean = uri.split("?")[0].rstrip("/") or "/"
    return clean in TRACKED_PATHS


def normalize_page(uri: str) -> str:
    """Canonicalize tracked URIs so duplicates merge into one key."""
    clean = uri.split("?")[0].rstrip("/") or "/"
    _aliases = {
        "/index.html": "/",
        "/iran.html":  "/iran",
    }
    return _aliases.get(clean, clean)


def detect_browser(ua: str) -> str:
    if not ua:
        return "Unknown"
    u = ua.lower()
    if "edg/" in u or "edge/" in u:   return "Edge"
    if "opr/" in u or "opera" in u:   return "Opera"
    if "samsungbrowser"          in u: return "Samsung"
    if "ucbrowser"               in u: return "UC Browser"
    if "firefox" in u or "fxios" in u: return "Firefox"
    if "chrome"  in u or "crios" in u: return "Chrome"
    if "safari"                  in u: return "Safari"
    if "msie"    in u or "trident" in u: return "IE"
    return "Other"


def detect_device(ua: str) -> str:
    if not ua:
        return "Unknown"
    u = ua.lower()
    if "ipad" in u or "tablet" in u:
        return "Tablet"
    if "mobile" in u or "iphone" in u or ("android" in u and "tablet" not in u):
        return "Mobile"
    return "Desktop"


def detect_os(ua: str) -> str:
    if not ua:
        return "Unknown"
    u = ua.lower()
    if "windows nt" in u: return "Windows"
    if "android"    in u: return "Android"
    if "iphone"     in u: return "iOS"
    if "ipad"       in u: return "iOS"
    if "mac os x"   in u or "macintosh" in u: return "macOS"
    if "linux"      in u: return "Linux"
    if "cros"       in u: return "ChromeOS"
    return "Other"


def normalize_protocol(proto: str) -> str:
    """Normalize Caddy proto string to clean label."""
    p = (proto or "").upper()
    if p.startswith("HTTP/3") or p == "H3":  return "HTTP/3"
    if p.startswith("HTTP/2") or p == "H2":  return "HTTP/2"
    if p.startswith("HTTP/1.1"):             return "HTTP/1.1"
    if p.startswith("HTTP/1"):               return "HTTP/1.0"
    return p or "Unknown"


def extract_encoding(resp_headers: dict) -> str:
    """Pull Content-Encoding from response headers."""
    enc = resp_headers.get("Content-Encoding") or resp_headers.get("content-encoding")
    if isinstance(enc, list):
        enc = enc[0] if enc else ""
    return (enc or "none").lower()


def extract_referrer(req_headers: dict) -> str | None:
    """
    Extract a cleaned referrer domain from request headers.
    Returns None for same-site or empty referrers.
    """
    ref = req_headers.get("Referer") or req_headers.get("referer")
    if isinstance(ref, list):
        ref = ref[0] if ref else ""
    if not ref:
        return None
    try:
        parsed = urlparse(ref)
        host = parsed.netloc.lower()
        # Strip port
        host = host.split(":")[0]
        # Strip www.
        if host.startswith("www."):
            host = host[4:]
        # Ignore self-referrals (same domain)
        if host in ("mahdiyar.info", "localhost", "127.0.0.1", ""):
            return None
        return host
    except Exception:
        return None


def parse_line(line: str) -> dict | None:
    line = line.strip()
    if not line or line[0] != "{":
        return None
    try:
        return json.loads(line)
    except json.JSONDecodeError:
        return None


def extract_fields(entry: dict) -> dict:
    """Extract all fields we care about from a Caddy JSON log entry."""
    req          = entry.get("request", {})
    req_headers  = req.get("headers", {})
    resp_headers = entry.get("resp_headers", {})

    ua  = (req_headers.get("User-Agent") or req_headers.get("user-agent") or [""])[0]
    uri = req.get("uri", "/")
    ts  = entry.get("ts")
    dt  = datetime.fromtimestamp(ts, tz=timezone.utc) if ts else datetime.now(tz=timezone.utc)

    # TLS block: resumed = True means session was reused (cheaper)
    tls     = entry.get("tls", {})
    resumed = tls.get("resumed", False)

    # HTTP protocol (e.g. "HTTP/3.0", "h3", "HTTP/2.0")
    proto = req.get("proto", "")

    # Response size in bytes
    size = entry.get("size", 0) or 0

    # Server-side duration in seconds → convert to ms
    duration_ms = round((entry.get("duration", 0) or 0) * 1000)

    # Encoding
    encoding = extract_encoding(resp_headers)

    # Referrer domain
    referrer = extract_referrer(req_headers)

    return {
        "ua":          ua,
        "uri":         uri,
        "dt":          dt,
        "proto":       proto,
        "resumed":     resumed,
        "size":        size,
        "duration_ms": duration_ms,
        "encoding":    encoding,
        "referrer":    referrer,
        "status":      entry.get("status", 200),
    }

# ── AGGREGATION ───────────────────────────────────────────────────────────────

def process_log(log_path: str) -> dict:
    page_views    = 0
    by_day        = defaultdict(int)
    by_month      = defaultdict(int)
    browsers      = defaultdict(int)
    devices       = defaultdict(int)
    oses          = defaultdict(int)
    pages         = defaultdict(int)
    protocols     = defaultdict(int)
    encodings     = defaultdict(int)
    referrers     = defaultdict(int)
    unique_ips    = set()
    total_bytes   = 0
    total_dur_ms  = 0
    tls_resumed   = 0
    tls_total     = 0

    with open(log_path, encoding="utf-8", errors="replace") as fh:
        for line in fh:
            entry = parse_line(line)
            if not entry:
                continue

            f = extract_fields(entry)

            if is_bot(f["ua"]):          continue
            if is_static(f["uri"]):      continue
            if not is_tracked(f["uri"]): continue
            if not (200 <= f["status"] < 400): continue

            day   = f["dt"].strftime("%Y-%m-%d")
            month = f["dt"].strftime("%Y-%m")
            page  = normalize_page(f["uri"])

            page_views                        += 1
            by_day[day]                       += 1
            by_month[month]                   += 1
            browsers[detect_browser(f["ua"])] += 1
            devices[detect_device(f["ua"])]   += 1
            oses[detect_os(f["ua"])]           += 1
            pages[page]                       += 1
            protocols[normalize_protocol(f["proto"])] += 1
            total_bytes                       += f["size"]
            total_dur_ms                      += f["duration_ms"]

            # Encoding — skip "none" from aggregation (too dominant, uninformative)
            if f["encoding"] and f["encoding"] != "none":
                encodings[f["encoding"]] += 1

            # Referrer
            if f["referrer"]:
                referrers[f["referrer"]] += 1

            # Unique IPs — from entry.request.remote_ip
            ip = entry.get("request", {}).get("remote_ip", "")
            if ip:
                unique_ips.add(ip)

            # TLS stats (all requests, not just tracked ones — more representative)
            tls_total += 1
            if f["resumed"]:
                tls_resumed += 1

    avg_dur_ms = round(total_dur_ms / page_views) if page_views else 0
    tls_pct    = round((tls_resumed / tls_total) * 100) if tls_total else 0

    return {
        "page_views": page_views,
        "by_day":     dict(by_day),
        "by_month":   dict(by_month),
        "browsers":   dict(browsers),
        "devices":    dict(devices),
        "oses":       dict(oses),
        "pages":      dict(pages),
        "protocols":  dict(protocols),
        "encodings":  dict(encodings),
        "referrers":  dict(referrers),
        "unique_ips": len(unique_ips),
        "total_bytes":   total_bytes,
        "avg_dur_ms":    avg_dur_ms,
        "tls_resumed_pct": tls_pct,
    }


def keep_last(d: dict, n: int) -> dict:
    keys = sorted(d.keys())[-n:]
    return {k: d[k] for k in keys}

# ── MAIN ──────────────────────────────────────────────────────────────────────

def main():
    if not os.path.exists(LOG_FILE):
        print(f"Error: log file not found: {LOG_FILE}", file=sys.stderr)
        sys.exit(1)

    c = process_log(LOG_FILE)

    now       = datetime.now(tz=timezone.utc)
    today_key = now.strftime("%Y-%m-%d")
    month_key = now.strftime("%Y-%m")

    stats = {
        "generatedAt": now.isoformat(),
        "logFile":     LOG_FILE,

        "allTime": {
            "pageViews": c["page_views"],
            "browsers":  c["browsers"],
            "devices":   c["devices"],
            "pages":     c["pages"],
        },

        "thisMonth": {
            "pageViews": c["by_month"].get(month_key, 0),
            "label":     month_key,
        },

        "today": {
            "pageViews": c["by_day"].get(today_key, 0),
            "label":     today_key,
        },

        "series": {
            "daily":   keep_last(c["by_day"],   30),
            "monthly": keep_last(c["by_month"], 12),
        },

        # Extra enriched fields shown in the dashboard
        "extra": {
            "protocols":      c["protocols"],
            "encodings":      c["encodings"],
            "referrers":      c["referrers"],
            "oses":           c["oses"],
            "uniqueIps":      c["unique_ips"],
            "totalBandwidth": c["total_bytes"],
            "avgResponseMs":  c["avg_dur_ms"],
            "tlsResumed":     c["tls_resumed_pct"],
        },
    }

    out_path = Path(OUTPUT_FILE)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    tmp_fd, tmp_path = tempfile.mkstemp(dir=out_path.parent, suffix='.tmp')
    try:
        with os.fdopen(tmp_fd, 'w', encoding='utf-8') as f:
            json.dump(stats, f, ensure_ascii=False, indent=2)
        os.replace(tmp_path, out_path)
        # Fix ownership and permissions so Caddy can read the file
        shutil.chown(out_path, user='caddy', group='caddy')
        os.chmod(out_path, 0o644)
    except Exception:
        os.unlink(tmp_path)
        raise

    print(
        f"[{now.isoformat()}] {OUTPUT_FILE} written — "
        f"{c['page_views']} page views, "
        f"{c['unique_ips']} unique IPs, "
        f"{c['avg_dur_ms']}ms avg response"
    )


if __name__ == "__main__":
    main()