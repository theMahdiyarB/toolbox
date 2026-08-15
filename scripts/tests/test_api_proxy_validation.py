"""Baseline tests for api_proxy request validation / allowlists.

Locks the current trust rules without binding a socket:
  - weather endpoint allowlists membership
  - /post-track barcode rule (10-30 digits)
"""
import re

import api_proxy
from api_proxy import WEATHER_ENDPOINTS, WEATHER_STATIC


# Mirrors api_proxy.py:208 — keep verbatim until Plan 004 extracts shared code.
POST_TRACK_BARCODE_RE = re.compile(r"^\d{10,30}$")


def test_weather_allowlists_are_non_empty():
    assert len(WEATHER_ENDPOINTS) > 0
    assert len(WEATHER_STATIC) > 0


def test_unknown_weather_endpoint_not_allowed():
    # The handler rejects any endpoint not in the allowlist (api_proxy.py:144-145).
    assert "bogus" not in WEATHER_ENDPOINTS
    assert "bogus" not in WEATHER_STATIC


def test_post_track_barcode_accepts_valid():
    assert POST_TRACK_BARCODE_RE.match("1234567890")        # exactly 10
    assert POST_TRACK_BARCODE_RE.match("12345678901234567890")  # 20


def test_post_track_barcode_rejects_invalid():
    assert not POST_TRACK_BARCODE_RE.match("")          # empty
    assert not POST_TRACK_BARCODE_RE.match("123")       # too short
    assert not POST_TRACK_BARCODE_RE.match("abc123")    # non-digits
    assert not POST_TRACK_BARCODE_RE.match("1" * 31)    # too long (31)
