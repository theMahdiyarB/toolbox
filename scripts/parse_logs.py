#!/usr/bin/env python3
"""
parse_logs.py — Caddy JSON access log → stats.json aggregator (INCREMENTAL)
Zero dependencies — Python 3.6+ stdlib only.

Usage:
    python3 parse_logs.py

Environment variables (all optional):
    LOG_FILE     Path to Caddy's JSON access log
                 Default: /var/log/caddy/access.log
    OUTPUT_FILE  Where to write stats.json
                 Default: /var/www/toolbox/scripts/stats.json

Cron (every 5 minutes):
    */5 * * * * python3 /var/www/toolbox/parse_logs.py >> /var/log/parse_logs.log 2>&1
"""

import gzip
import json
import os
import shutil
import sys
import tempfile
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlparse

# ── CONFIG ────────────────────────────────────────────────────────────────────

LOG_FILE    = os.environ.get("LOG_FILE",    "/var/log/caddy/access.log")
OUTPUT_FILE = os.environ.get("OUTPUT_FILE", "/var/www/toolbox/scripts/stats.json")

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

# ── LOG FILE ITERATOR (current + all rotated) ─────────────────────────────────

def iter_log_lines(log_path: str, last_processed_ts: float = 0):
    """
    Yield lines from all available log files, but only those with
    timestamp > last_processed_ts to avoid reprocessing old entries.
    """
    # Current live log
    if os.path.exists(log_path):
        with open(log_path, encoding="utf-8", errors="replace") as f:
            for line in f:
                if should_process_line(line, last_processed_ts):
                    yield line

    # Rotated files: .1 / .1.gz, .2.gz, .3.gz … up to logrotate's rotate 90
    n = 1
    while True:
        plain = f"{log_path}.{n}"
        gz    = f"{log_path}.{n}.gz"

        if os.path.exists(plain):
            with open(plain, encoding="utf-8", errors="replace") as f:
                for line in f:
                    if should_process_line(line, last_processed_ts):
                        yield line
            n += 1
        elif os.path.exists(gz):
            with gzip.open(gz, "rt", encoding="utf-8", errors="replace") as f:
                for line in f:
                    if should_process_line(line, last_processed_ts):
                        yield line
            n += 1
        else:
            break


def should_process_line(line: str, last_ts: float) -> bool:
    """Quick check if line timestamp is newer than last processed."""
    if last_ts == 0:
        return True
    try:
        entry = json.loads(line.strip())
        ts = entry.get("ts", 0)
        return ts > last_ts
    except:
        return False

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
    if "edg/" in u or "edge/" in u:     return "Edge"
    if "opr/" in u or "opera" in u:     return "Opera"
    if "samsungbrowser"          in u:   return "Samsung"
    if "ucbrowser"               in u:   return "UC Browser"
    if "firefox" in u or "fxios" in u:  return "Firefox"
    if "chrome"  in u or "crios" in u:  return "Chrome"
    if "safari"                  in u:   return "Safari"
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
    if "windows nt" in u:                    return "Windows"
    if "android"    in u:                    return "Android"
    if "iphone"     in u:                    return "iOS"
    if "ipad"       in u:                    return "iOS"
    if "mac os x"   in u or "macintosh" in u: return "macOS"
    if "linux"      in u:                    return "Linux"
    if "cros"       in u:                    return "ChromeOS"
    return "Other"


def normalize_protocol(proto: str) -> str:
    p = (proto or "").upper()
    if p.startswith("HTTP/3") or p == "H3": return "HTTP/3"
    if p.startswith("HTTP/2") or p == "H2": return "HTTP/2"
    if p.startswith("HTTP/1.1"):            return "HTTP/1.1"
    if p.startswith("HTTP/1"):              return "HTTP/1.0"
    return p or "Unknown"


def extract_encoding(resp_headers: dict) -> str:
    enc = resp_headers.get("Content-Encoding") or resp_headers.get("content-encoding")
    if isinstance(enc, list):
        enc = enc[0] if enc else ""
    return (enc or "none").lower()


def extract_referrer(req_headers: dict):
    ref = req_headers.get("Referer") or req_headers.get("referer")
    if isinstance(ref, list):
        ref = ref[0] if ref else ""
    if not ref:
        return None
    try:
        parsed = urlparse(ref)
        host = parsed.netloc.lower().split(":")[0]
        if host.startswith("www."):
            host = host[4:]
        if host in ("mahdiyar.info", "localhost", "127.0.0.1", ""):
            return None
        return host
    except Exception:
        return None


def parse_line(line: str):
    line = line.strip()
    if not line or line[0] != "{":
        return None
    try:
        return json.loads(line)
    except json.JSONDecodeError:
        return None


def extract_fields(entry: dict) -> dict:
    req          = entry.get("request", {})
    req_headers  = req.get("headers", {})
    resp_headers = entry.get("resp_headers", {})

    ua  = (req_headers.get("User-Agent") or req_headers.get("user-agent") or [""])[0]
    uri = req.get("uri", "/")
    ts  = entry.get("ts")
    dt  = datetime.fromtimestamp(ts, tz=timezone.utc) if ts else datetime.now(tz=timezone.utc)

    tls         = entry.get("tls", {})
    resumed     = tls.get("resumed", False)
    proto       = req.get("proto", "")
    size        = entry.get("size", 0) or 0
    duration_ms = round((entry.get("duration", 0) or 0) * 1000)
    encoding    = extract_encoding(resp_headers)
    referrer    = extract_referrer(req_headers)

    return {
        "ua":          ua,
        "uri":         uri,
        "dt":          dt,
        "ts":          ts,
        "proto":       proto,
        "resumed":     resumed,
        "size":        size,
        "duration_ms": duration_ms,
        "encoding":    encoding,
        "referrer":    referrer,
        "status":      entry.get("status", 200),
        "remote_ip":   req.get("remote_ip", ""),
    }

# ── LOAD EXISTING STATS ───────────────────────────────────────────────────────

def load_existing_stats(output_path: str) -> dict:
    """Load existing stats.json or return empty structure."""
    if not os.path.exists(output_path):
        return {
            "lastProcessedTs": 0,
            "allTime": {"pageViews": 0, "browsers": {}, "devices": {}, "pages": {}},
            "series": {"daily": {}, "monthly": {}},
            "extra": {
                "protocols": {}, "encodings": {}, "referrers": {}, "oses": {},
                "uniqueIps": 0, "totalBandwidth": 0, "avgResponseMs": 0, "tlsResumed": 0,
                "totalDurationMs": 0, "tlsTotal": 0, "uniqueIpSet": []
            }
        }
    
    with open(output_path, encoding="utf-8") as f:
        stats = json.load(f)
    
    # Add tracking fields if missing
    if "lastProcessedTs" not in stats:
        stats["lastProcessedTs"] = 0
    if "totalDurationMs" not in stats.get("extra", {}):
        # Reconstruct from existing data
        pv = stats["allTime"]["pageViews"]
        avg = stats["extra"]["avgResponseMs"]
        stats["extra"]["totalDurationMs"] = pv * avg
    if "tlsTotal" not in stats.get("extra", {}):
        # Estimate from TLS percentage
        pv = stats["allTime"]["pageViews"]
        pct = stats["extra"].get("tlsResumed", 0)
        stats["extra"]["tlsTotal"] = pv
        stats["extra"]["tlsResumedCount"] = round(pv * pct / 100)
    if "uniqueIpSet" not in stats.get("extra", {}):
        stats["extra"]["uniqueIpSet"] = []
    
    return stats

# ── MERGE HELPERS ─────────────────────────────────────────────────────────────

def merge_dict(existing: dict, new: dict) -> dict:
    """Add new counts to existing dict."""
    result = existing.copy()
    for k, v in new.items():
        result[k] = result.get(k, 0) + v
    return result

# ── AGGREGATION ───────────────────────────────────────────────────────────────

def process_new_entries(log_path: str, existing_stats: dict) -> dict:
    """Process only new log entries and return incremental stats."""
    last_ts = existing_stats.get("lastProcessedTs", 0)
    
    new_page_views   = 0
    by_day           = defaultdict(int)
    by_month         = defaultdict(int)
    browsers         = defaultdict(int)
    devices          = defaultdict(int)
    oses             = defaultdict(int)
    pages            = defaultdict(int)
    protocols        = defaultdict(int)
    encodings        = defaultdict(int)
    referrers        = defaultdict(int)
    unique_ips       = set(existing_stats["extra"].get("uniqueIpSet", []))
    total_bytes      = 0
    total_dur_ms     = 0
    tls_resumed      = 0
    tls_total        = 0
    max_ts           = last_ts

    for line in iter_log_lines(log_path, last_ts):
        entry = parse_line(line)
        if not entry:
            continue

        f = extract_fields(entry)
        
        if f["ts"]:
            max_ts = max(max_ts, f["ts"])

        if is_bot(f["ua"]):                continue
        if is_static(f["uri"]):            continue
        if not is_tracked(f["uri"]):       continue
        if not (200 <= f["status"] < 400): continue

        day   = f["dt"].strftime("%Y-%m-%d")
        month = f["dt"].strftime("%Y-%m")
        page  = normalize_page(f["uri"])

        new_page_views                            += 1
        by_day[day]                               += 1
        by_month[month]                           += 1
        browsers[detect_browser(f["ua"])]         += 1
        devices[detect_device(f["ua"])]           += 1
        oses[detect_os(f["ua"])]                  += 1
        pages[page]                               += 1
        protocols[normalize_protocol(f["proto"])] += 1
        total_bytes                               += f["size"]
        total_dur_ms                              += f["duration_ms"]

        if f["encoding"] and f["encoding"] != "none":
            encodings[f["encoding"]] += 1

        if f["referrer"]:
            referrers[f["referrer"]] += 1

        if f["remote_ip"]:
            unique_ips.add(f["remote_ip"])

        tls_total += 1
        if f["resumed"]:
            tls_resumed += 1

    return {
        "new_page_views":  new_page_views,
        "by_day":          dict(by_day),
        "by_month":        dict(by_month),
        "browsers":        dict(browsers),
        "devices":         dict(devices),
        "oses":            dict(oses),
        "pages":           dict(pages),
        "protocols":       dict(protocols),
        "encodings":       dict(encodings),
        "referrers":       dict(referrers),
        "unique_ips":      unique_ips,
        "total_bytes":     total_bytes,
        "total_dur_ms":    total_dur_ms,
        "tls_resumed":     tls_resumed,
        "tls_total":       tls_total,
        "max_ts":          max_ts,
    }


def keep_last(d: dict, n: int) -> dict:
    keys = sorted(d.keys())[-n:]
    return {k: d[k] for k in keys}

# ── MAIN ──────────────────────────────────────────────────────────────────────

def main():
    if not os.path.exists(LOG_FILE):
        print(f"Error: log file not found: {LOG_FILE}", file=sys.stderr)
        sys.exit(1)

    # Load existing stats
    existing = load_existing_stats(OUTPUT_FILE)
    
    # Process only new entries
    new = process_new_entries(LOG_FILE, existing)
    
    # If no new entries, skip update
    if new["new_page_views"] == 0:
        print(f"[{datetime.now(tz=timezone.utc).isoformat()}] No new entries to process")
        return

    # Merge with existing data
    total_page_views = existing["allTime"]["pageViews"] + new["new_page_views"]
    old_total_dur = existing["extra"].get("totalDurationMs", 0)
    old_tls_total = existing["extra"].get("tlsTotal", 0)
    old_tls_resumed = existing["extra"].get("tlsResumedCount", 0)
    
    new_total_dur = old_total_dur + new["total_dur_ms"]
    new_tls_total = old_tls_total + new["tls_total"]
    new_tls_resumed_count = old_tls_resumed + new["tls_resumed"]
    
    avg_dur_ms = round(new_total_dur / total_page_views) if total_page_views else 0
    tls_pct = round((new_tls_resumed_count / new_tls_total) * 100) if new_tls_total else 0

    now       = datetime.now(tz=timezone.utc)
    today_key = now.strftime("%Y-%m-%d")
    month_key = now.strftime("%Y-%m")

    merged_daily = merge_dict(existing["series"]["daily"], new["by_day"])
    merged_monthly = merge_dict(existing["series"]["monthly"], new["by_month"])

    stats = {
        "generatedAt": now.isoformat(),
        "logFile": LOG_FILE,
        "lastProcessedTs": new["max_ts"],

        "allTime": {
            "pageViews": total_page_views,
            "browsers": merge_dict(existing["allTime"]["browsers"], new["browsers"]),
            "devices": merge_dict(existing["allTime"]["devices"], new["devices"]),
            "pages": merge_dict(existing["allTime"]["pages"], new["pages"]),
        },

        "thisMonth": {
            "pageViews": merged_monthly.get(month_key, 0),
            "label": month_key,
        },

        "today": {
            "pageViews": merged_daily.get(today_key, 0),
            "label": today_key,
        },

        "series": {
            "daily": keep_last(merged_daily, 30),
            "monthly": keep_last(merged_monthly, 12),
        },

        "extra": {
            "protocols": merge_dict(existing["extra"]["protocols"], new["protocols"]),
            "encodings": merge_dict(existing["extra"]["encodings"], new["encodings"]),
            "referrers": merge_dict(existing["extra"]["referrers"], new["referrers"]),
            "oses": merge_dict(existing["extra"]["oses"], new["oses"]),
            "uniqueIps": len(new["unique_ips"]),
            "totalBandwidth": existing["extra"]["totalBandwidth"] + new["total_bytes"],
            "avgResponseMs": avg_dur_ms,
            "tlsResumed": tls_pct,
            "totalDurationMs": new_total_dur,
            "tlsTotal": new_tls_total,
            "tlsResumedCount": new_tls_resumed_count,
            "uniqueIpSet": list(new["unique_ips"])[:10000],  # Cap to prevent bloat
        },
    }

    out_path = Path(OUTPUT_FILE)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    tmp_fd, tmp_path = tempfile.mkstemp(dir=out_path.parent, suffix=".tmp")
    try:
        with os.fdopen(tmp_fd, "w", encoding="utf-8") as f:
            json.dump(stats, f, ensure_ascii=False, indent=2)
        os.replace(tmp_path, out_path)
        shutil.chown(out_path, user="caddy", group="caddy")
        os.chmod(out_path, 0o644)
    except Exception:
        os.unlink(tmp_path)
        raise

    print(
        f"[{now.isoformat()}] {OUTPUT_FILE} updated — "
        f"+{new['new_page_views']} new views (total: {total_page_views}), "
        f"{len(new['unique_ips'])} unique IPs, "
        f"{avg_dur_ms}ms avg response"
    )


if __name__ == "__main__":
    main()
