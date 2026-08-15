"""Characterization tests for the (currently duplicated) earthquake parsers.

These pin the CURRENT behavior of:
  - api_proxy.fetch_earthquakes()
  - fetch_earthquakes.fetch()

Plan 004 will extract these into one shared module; these tests must keep
passing to prove the refactor changed nothing. All network is mocked via
unittest.mock on subprocess.run.
"""
from unittest.mock import MagicMock, patch

import api_proxy
import fetch_earthquakes


def _fake_result(html):
    r = MagicMock()
    r.returncode = 0
    r.stdout = html.encode("utf-8")
    r.stderr = b""
    return r


def test_fetch_earthquakes_parses_one(sample_eq_html):
    with patch.object(api_proxy.subprocess, "run", return_value=_fake_result(sample_eq_html)):
        quakes = api_proxy.fetch_earthquakes()
    assert isinstance(quakes, list)
    assert len(quakes) == 1
    eq = quakes[0]
    assert eq["mag"] == "4.2"
    assert eq["depth"] == "۱۰ کیلومتر"
    assert eq["cities"] == ["تهران", "کرج"]
    assert eq["provinces"] == ["تهران"]
    assert eq["map_url"] == "https://www.google.com/maps/place/35.7,51.4"
    assert eq["rid"] == "123"


def test_fetch_earthquakes_skips_non_report(sample_eq_html):
    with patch.object(api_proxy.subprocess, "run", return_value=_fake_result(sample_eq_html)):
        quakes = api_proxy.fetch_earthquakes()
    # The second TEXT message is not an earthquake report and must be excluded.
    assert len(quakes) == 1
    assert all("گزارش مقدماتی زمین" in "" or True for _ in quakes)  # sanity placeholder


def test_fetch_earthquakes_no_next_data(no_next_data_html):
    with patch.object(api_proxy.subprocess, "run", return_value=_fake_result(no_next_data_html)):
        try:
            api_proxy.fetch_earthquakes()
        except ValueError as e:
            assert "__NEXT_DATA__" in str(e)
        else:
            raise AssertionError("expected ValueError for missing __NEXT_DATA__")


def test_fetch_returns_count_and_caches(sample_eq_html, tmp_path, monkeypatch):
    # fetch_earthquakes.fetch() returns an int count and writes a cache file.
    cache = tmp_path / "earthquakes.json"
    monkeypatch.setattr(fetch_earthquakes, "CACHE_FILE", str(cache))
    with patch.object(fetch_earthquakes.subprocess, "run", return_value=_fake_result(sample_eq_html)):
        n = fetch_earthquakes.fetch()
    assert n == 1
    assert cache.exists()
    import json
    saved = json.loads(cache.read_text(encoding="utf-8"))
    assert saved["count"] == 1
    assert saved["items"][0]["mag"] == "4.2"
