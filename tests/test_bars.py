"""Each contract's hourly and daily bars from Kalshi's candlesticks (from
0.11.0; rulings 624 and 625): the YES contract's traded prices and the
contracts traded, a day New York's, a candle with no trade no bar, closed
intervals only, no volume-weighted price."""

from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal

from meridian.operations import as_decimal
from meridian.roles.data.event_contracts import DAY, HOUR, ContractMap, Feed
from meridian.roles.data.testing import Lake

from kalshi.convert import candles

import venue_cases as v


def _at(text: str) -> int:
    return int(datetime.fromisoformat(text).replace(tzinfo=UTC).timestamp())


async def test_hours_and_new_york_days_closed_kept_from_its_candlesticks() -> None:
    lake = Lake(v.VENUE)
    market = v.market()
    feed = Feed(lake, market, ContractMap(), clock_ns=lambda: v.NOW_NS)
    await feed.name([await lake.held(feed, v.BASE)])
    assert await feed.keep_bars(v.BARS_DECLARED, once=True) == 6
    bars = lake.rows("RecordBars")
    hours = [b for b in bars if not b.meta.business_date]
    days = [b for b in bars if b.meta.business_date]
    assert len(hours) == 4, "the hour with no trade and the hour still open are no bars"
    assert sorted(d.meta.business_date for d in days) == ["2026-10-08", "2026-10-09"]
    ninth = next(d for d in days if d.meta.business_date == "2026-10-09")
    assert (ninth.meta.valid_from_ns, ninth.meta.valid_until_ns) == (
        _at("2026-10-09T04:00:00") * 10**9, _at("2026-10-10T04:00:00") * 10**9,
    ), "New York's day, in daylight time"  # fmt: skip
    prices = [str(as_decimal(getattr(ninth, f).amount)) for f in ("open", "high", "low", "close")]
    assert prices == ["0.4100", "0.4400", "0.4000", "0.4200"]
    assert as_decimal(ninth.volume) == Decimal("155.50") and not ninth.HasField("vwap")
    calls = [r["request"]["url"] for r in market.client.store.records()  # type: ignore[attr-defined]
             if r["call"] == "candlesticks"]  # fmt: skip
    assert len(calls) == 2 and all("market_tickers=" + v.BASE in c for c in calls)
    assert {c.split("period_interval=")[1][:4] for c in calls} == {"60", "1440"}


def test_a_candle_spans_its_interval_and_one_with_no_trade_is_none() -> None:
    body = {"markets": [{"market_ticker": "T", "candlesticks": [
        {"end_period_ts": _at("2026-11-02T05:00:00"), "volume_fp": "3.00",
         "price": {"open_dollars": "0.10", "high_dollars": "0.20", "low_dollars": "0.10",
                   "close_dollars": "0.15"}},
        {"end_period_ts": _at("2026-11-02T06:00:00"), "volume_fp": "0.00",
         "price": {"previous_dollars": "0.15"}},
    ]}]}  # fmt: skip
    [day] = candles("T", DAY, body, "k")
    # New York's 2026-11-01, the day its clocks went back: 25 hours.
    assert (day.end_ns - day.start_ns) // 10**9 == 25 * 3_600
    assert day.start_ns == _at("2026-11-01T04:00:00") * 10**9
    [hour] = candles("T", HOUR, body, "k")
    assert (hour.start_ns, hour.end_ns) == (
        _at("2026-11-02T04:00:00") * 10**9, _at("2026-11-02T05:00:00") * 10**9,
    )  # fmt: skip
    assert (hour.open, hour.close, hour.volume, hour.vwap) == (
        Decimal("0.10"), Decimal("0.15"), Decimal("3.00"), None,
    )  # fmt: skip
    assert candles("U", HOUR, body, "k") == [], "another market's"
