"""Kalshi's fees on Connection and in `read_connection` (fees.py): from
0.11.0 (ruling 630) computed for each contract served from its series'
fee type and multiplier, or its event's override, with Kalshi's published
formula -- never a type's rate assumed where the schedule states none."""

from __future__ import annotations

import asyncio
from decimal import Decimal

from meridian.roles.data.event_contracts import ContractMap, Feed
from meridian.roles.data.testing import Lake
from meridian.testing import PageClient

from kalshi import page
from kalshi.fees import FEES, MarketFee, Stated, coefficients, fee, market_fee, override

import venue_cases as v


def test_the_published_formula_gives_the_schedules_table() -> None:
    # The General Trading Fees Table (effective Feb 5, 2026): one contract
    # at 50 cents pays $0.02, a hundred $1.75; a hundred at 1 cent $0.07.
    general = Decimal("0.07")
    assert fee(general, Decimal(1), Decimal("0.5")) == Decimal("0.02")
    assert fee(general, Decimal(100), Decimal("0.5")) == Decimal("1.75")
    assert fee(general, Decimal(100), Decimal("0.01")) == Decimal("0.07")
    assert fee(general, Decimal(100), Decimal("0.35")) == Decimal("1.60")
    assert fee(Decimal("0.035"), Decimal(100), Decimal("0.5")) == Decimal("0.88")
    assert FEES.source.startswith("https://web.archive.org/") and FEES.read_on == "2026-10-26"
    assert "429" in FEES.not_read


def test_each_fee_type_its_coefficients_and_flat_never_assumed() -> None:
    assert coefficients("quadratic", Decimal(1)) == ("0.07", "0")
    assert coefficients("quadratic", Decimal("0.5")) == ("0.035", "0")
    assert coefficients("quadratic_with_maker_fees", Decimal(1)) == ("0.07", "0.0175")
    assert coefficients("quadratic_with_combo_maker_fees", Decimal(1)) == ("0.07", "0.035")
    assert coefficients("quadratic", Decimal(0)) == ("0", "0")
    assert coefficients("flat", Decimal(1)) is None


def test_an_events_override_in_effect_applies_before_its_series() -> None:
    changes: list[dict[str, object]] = [
        {"event_ticker": "E", "fee_type_override": "quadratic",
         "fee_multiplier_override": Decimal("0.5"), "scheduled_ts": "2026-10-01T00:00:00Z"},
        {"event_ticker": "E", "fee_type_override": None, "fee_multiplier_override": None,
         "scheduled_ts": "2026-11-01T00:00:00Z"},
    ]  # fmt: skip
    now = override(changes, "2026-10-10T12:00:00Z")
    assert now == Stated("quadratic", Decimal("0.5"), "event E")
    assert override(changes, "2026-11-02T00:00:00Z") is None, "cleared: the series' applies"
    series = Stated("quadratic_with_maker_fees", Decimal(1), "series S")
    assert market_fee("M", series, now) == MarketFee(
        "M", "0.035", "0", "event", "event E: quadratic x0.5"
    )
    assert market_fee("M", series, None).source == "series"
    unread = market_fee("M", None, None)
    assert (unread.taker, unread.source) == ("", "none")
    flat = market_fee("M", Stated("flat", Decimal(1), "series F"), None)
    assert (flat.taker, flat.source) == ("", "none") and "not computed" in flat.said


def test_connection_says_which_fee_applies_to_each_contract_served() -> None:
    lake = Lake(v.VENUE)
    feed = Feed(lake, v.market(), ContractMap(), clock_ns=lambda: v.NOW_NS)

    async def served() -> None:
        for code in (v.BASE, v.RANGE):
            await feed.name([await lake.held(feed, code)])
        await feed.keep_events(once=True)

    asyncio.run(served())
    page.hold(feed)
    try:
        client = PageClient(page.pages)
        fees = client.call_tool("read_connection", level="admin").data["fees"]
        applying = {m["code"]: (m["taker"], m["maker"], m["source"]) for m in fees["markets"]}
        assert applying == {v.BASE: ("0.07", "0", "series"), v.RANGE: ("0.035", "0", "event")}
        shown = client.get("/", "admin").text
        assert "Per market: 1 by series, 1 by event, 0 none" in shown
        assert "quadratic_with_maker_fees 0.07/0.0175" in shown
    finally:
        page.HELD.feed = None
