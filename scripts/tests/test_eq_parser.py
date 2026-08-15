"""Characterization tests for the earthquake parser inside api_proxy.py.

api_proxy.py is now the single owner of EQ logic: it scrapes ble.ir, parses
via `parse_earthquakes()`, and caches to earthquakes.json via
`fetch_eq_and_cache()` (run by cron as `python3 api_proxy.py --fetch-eq`).
The /irsc-proxy handler serves the cache file.

These tests pin that behavior WITHOUT network: subprocess.run is mocked to
return a fake ble.ir-style __NEXT_DATA__ HTML (see conftest.py).
"""
from unittest.mock import MagicMock, patch

import api_proxy


def _fake_result(html):
    r = MagicMock()
    r.returncode = 0
    r.stdout = html.encode("utf-8")
    r.stderr = b""
    return r


def test_parse_earthquakes_parses_one(sample_eq_html):
    quakes = api_proxy.parse_earthquakes(sample_eq_html)
    assert isinstance(quakes, list)
    assert len(quakes) == 1
    eq = quakes[0]
    assert eq["mag"] == "4.2"
    assert eq["depth"] == "۱۰ کیلومتر"
    assert eq["cities"] == ["تهران", "کرج"]
    assert eq["provinces"] == ["تهران"]
    assert eq["map_url"] == "https://www.google.com/maps/place/35.7,51.4"
    assert eq["rid"] == "123"


def test_parse_earthquakes_skips_non_report(sample_eq_html):
    quakes = api_proxy.parse_earthquakes(sample_eq_html)
    # The second TEXT message is not an earthquake report and must be excluded.
    assert len(quakes) == 1


def test_parse_earthquakes_no_next_data(no_next_data_html):
    try:
        api_proxy.parse_earthquakes(no_next_data_html)
    except ValueError as e:
        assert "__NEXT_DATA__" in str(e)
    else:
        raise AssertionError("expected ValueError for missing __NEXT_DATA__")


def test_fetch_eq_and_cache_writes_count_and_file(sample_eq_html, tmp_path, monkeypatch):
    # fetch_eq_and_cache() scrapes, parses, and writes earthquakes.json.
    monkeypatch.setattr(api_proxy, "CACHE_FILE", str(tmp_path / "earthquakes.json"))
    with patch.object(api_proxy.subprocess, "run", return_value=_fake_result(sample_eq_html)):
        n = api_proxy.fetch_eq_and_cache()
    assert n == 1
    import json
    with open(api_proxy.CACHE_FILE, encoding="utf-8") as f:
        saved = json.load(f)
    assert saved["count"] == 1
    assert saved["items"][0]["mag"] == "4.2"


def test_fetch_eq_and_cache_rejects_no_quakes(no_next_data_html, tmp_path, monkeypatch):
    # HTML with no __NEXT_DATA__ parses to zero quakes -> must NOT write cache.
    monkeypatch.setattr(api_proxy, "CACHE_FILE", str(tmp_path / "earthquakes.json"))
    with patch.object(api_proxy.subprocess, "run", return_value=_fake_result(no_next_data_html)):
        try:
            api_proxy.fetch_eq_and_cache()
        except (RuntimeError, ValueError):
            pass
        else:
            raise AssertionError("expected RuntimeError/ValueError when no quakes parsed")
    import os
    assert not os.path.exists(api_proxy.CACHE_FILE)
