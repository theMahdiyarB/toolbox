"""Shared fixtures for the scripts/ test suite.

These let the earthquake-parser tests run WITHOUT network: we hand the parser
(a api_proxy.parse_earthquakes) a fake ble.ir-style `__NEXT_DATA__` HTML containing
one earthquake report and one non-matching TEXT message.
"""
import json
import pytest


def _build_html():
    messages = [
        {
            "rid": 123,
            "date": 1723800000,
            "type": "TEXT",
            "message": {
                "textMessage": {
                    "text": (
                        "گزارش مقدماتی زمین‌لرزه\n"
                        "بزرگی: 4.2\n"
                        "محل وقوع: استان تهران - شمال تهران\n"
                        "تاریخ و زمان وقوع به وقت محلی: ۱۴۰۳/۰۵/۱۲ ۰۳:۲۲\n"
                        "طول جغرافیایی: 51.4\n"
                        "عرض جغرافیایی: 35.7\n"
                        "عمق زمین: ۱۰ کیلومتر\n"
                        "نزدیک‌ترین شهرها:\n"
                        "تهران\n"
                        "کرج\n"
                        "\n"
                        "نزدیک‌ترین مراکز استان:\n"
                        "تهران\n"
                        "\n"
                        "https://www.google.com/maps/place/35.7,51.4\n"
                    )
                }
            },
        },
        {
            "rid": 999,
            "date": 1723800500,
            "type": "TEXT",
            "message": {
                "textMessage": {
                    "text": "این یک پیام عادی است که گزارش زمین‌لرزه نیست."
                }
            },
        },
    ]
    payload = {"props": {"pageProps": {"messages": messages}}}
    html = (
        '<html><body><script id="__NEXT_DATA__" '
        'type="application/json">' + json.dumps(payload, ensure_ascii=False) +
        "</script></body></html>"
    )
    return html


@pytest.fixture
def sample_eq_html():
    """Raw ble.ir-style HTML with one earthquake report + one non-report."""
    return _build_html()


@pytest.fixture
def no_next_data_html():
    """HTML with no __NEXT_DATA__ script at all."""
    return "<html><body><p>no data here</p></body></html>"
