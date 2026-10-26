"""Kalshi's fee schedule on Connection and in `read_connection` (fees.py;
from 0.10.0): not read, so no rate, and why -- never one assumed."""

from __future__ import annotations

from meridian.testing import PageClient

from kalshi import page
from kalshi.fees import FEES


def test_no_rate_is_assumed_where_the_schedule_was_not_read() -> None:
    assert FEES.rates == [] and "429" in FEES.not_read
    assert FEES.read_on == "2026-10-26"


def test_connection_says_the_schedule_was_not_read() -> None:
    client = PageClient(page.pages)
    fees = client.call_tool("read_connection", level="admin").data["fees"]
    assert fees["rates"] == [] and fees["not_read"] == FEES.not_read
    shown = client.get("/", "admin").text.replace("&#39;", "'")
    assert "Not read" in shown and "no rate is assumed" in shown
