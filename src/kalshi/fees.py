"""Kalshi's fees, computed for each contract served from the fee type and
multiplier Kalshi's API states for its series, or its event's override of
them, with Kalshi's published formula (ruling 630, from 0.11.0; 571's
category column; task sdk-contract/event-contract-fees-vary-by-market-category).

**The formula** is Kalshi's fee schedule's (kalshi.com/docs/kalshi-fee-schedule.pdf,
"Last updated and effective: Feb 5, 2026"): a taker pays
"fees = round up(0.07 x C x P x (1-P))", C the contracts traded and P their
price in dollars, rounded up to the next cent; where a market has maker
fees, a maker pays "round up(0.0175 x C x P x (1-P))". On 2026-10-26 the
schedule's own address answered HTTP 429 behind a bot challenge, as it did
on 2026-10-24, so it was read from the Internet Archive's copy of it taken
2026-06-12 (`SOURCE`), which states that effective date.

**Each series' type and multiplier** are the API's (docs.kalshi.com, "Get
Series"): `fee_type` -- "'quadratic' is described by the General Trading
Fees Table, 'quadratic_with_maker_fees' is described by the General Trading
Fees Table with maker fees described in the Maker Fees section,
'quadratic_with_combo_maker_fees' is the same maker-fee structure with a
0.5 maker multiplier instead of 0.25, 'flat' is described by the Specific
Trading Fees Table" -- and `fee_multiplier`, "a floating point multiplier
applied to the fee calculations". So a contract's taker coefficient is 0.07
times its multiplier, and its maker coefficient 0.07 x 0.25 (0.0175) or,
for combos, 0.07 x 0.5 (0.035), times its multiplier; `quadratic` charges
makers nothing. An event may override both ("Get Event Fee Changes": "an
override layered on top of the parent series' fee structure"; both null
clears it): the latest change in effect applies. `flat` is not computed:
the schedule read states no flat table, so its rate is not assumed. Read on
2026-10-26, of 15,394 series 15,199 stated `quadratic` at 1, 18 at 0.5 and
14 at 0; 160 had maker fees and 3 combo maker fees; the S&P 500 and
Nasdaq-100 series, which the Feb 5 schedule charges 0.035, state
`quadratic` at 1: the API's statement, current, is the one used.
"""

from __future__ import annotations

import math
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from decimal import Decimal
from typing import Any


@dataclass(frozen=True)
class Rate:
    """One fee type's row: its taker and maker coefficients as text, before
    the multiplier ("" where none is computed)."""

    category: str
    taker: str
    maker: str
    maker_rebate: str = ""


@dataclass(frozen=True)
class MarketFee:
    """One contract's fee as it applies (from 0.11.0, ruling 630): its taker
    and maker coefficients as text ("" where none is computed), where its
    type and multiplier come from -- `series`, `event` (an override) or
    `none` -- and what Kalshi said, in its words."""

    code: str
    taker: str
    maker: str
    source: str
    said: str


@dataclass(frozen=True)
class Fees:
    """A venue's published fee schedule: where and when it was read, its
    formula, its rows, what makers pay, and where it states a market's own
    rate; why a rate is left out, where the schedule could not be read; and
    each contract served's fee as it applies."""

    source: str = ""
    read_on: str = ""
    formula: str = ""
    rates: list[Rate] = field(default_factory=list)
    makers: str = ""
    per_market: str = ""
    not_read: str = ""
    markets: list[MarketFee] = field(default_factory=list)


#: Where the schedule was read: the Internet Archive's copy of
#: kalshi.com/docs/kalshi-fee-schedule.pdf taken 2026-06-12.
SOURCE = (
    "https://web.archive.org/web/20260612075630/https://kalshi.com/docs/kalshi-fee-schedule.pdf"
)
READ_ON = "2026-10-26"
#: The general taker coefficient, and each fee type's maker share of it.
TAKER = Decimal("0.07")
MAKER_SHARE = {
    "quadratic": Decimal(0),
    "quadratic_with_maker_fees": Decimal("0.25"),
    "quadratic_with_combo_maker_fees": Decimal("0.5"),
}

FEES = Fees(
    source=SOURCE,
    read_on=READ_ON,
    formula=(
        "fees = round up(0.07 x C x P x (1-P)) to the next cent, C contracts at price P, "
        "0.07 times the fee_multiplier; makers, where the fee_type has maker fees, 0.0175 "
        "(combos 0.035) times it; effective Feb 5, 2026"
    ),
    rates=[
        Rate("quadratic", "0.07", "0"),
        Rate("quadratic_with_maker_fees", "0.07", "0.0175"),
        Rate("quadratic_with_combo_maker_fees", "0.07", "0.035"),
    ],
    makers="charged only where the fee_type has maker fees",
    per_market=(
        "each contract's series states its fee_type and fee_multiplier, its event may override "
        "them; flat is not computed"
    ),
    not_read=(
        "kalshi.com/docs/kalshi-fee-schedule.pdf answered HTTP 429 behind a bot challenge on "
        "2026-10-26: read from the Internet Archive's copy of 2026-06-12"
    ),
)


def _text(value: Decimal) -> str:
    """A coefficient as text, with no trailing zeros."""
    said = format(value.normalize(), "f")
    return "0" if said in ("-0", "0.0") else said


def coefficients(fee_type: str, multiplier: Decimal) -> tuple[str, str] | None:
    """A fee type's taker and maker coefficients at a multiplier; None for a
    type not computed (`flat`, or one Kalshi adds later)."""
    share = MAKER_SHARE.get(fee_type)
    if share is None or multiplier < 0:
        return None
    return _text(TAKER * multiplier), _text(TAKER * share * multiplier)


def fee(coefficient: Decimal, contracts: Decimal, price: Decimal) -> Decimal:
    """Kalshi's published formula: coefficient x C x P x (1-P), rounded up
    to the next cent."""
    cents = coefficient * contracts * price * (1 - price) * 100
    return Decimal(math.ceil(cents)) / 100


@dataclass(frozen=True)
class Stated:
    """A fee type and multiplier as Kalshi states them: a series', or an
    event's override."""

    fee_type: str
    multiplier: Decimal
    of: str


def series_stated(body: Mapping[str, Any]) -> Stated | None:
    """A series' fee type and multiplier, from `/series/{ticker}`."""
    series = body.get("series") if isinstance(body.get("series"), Mapping) else body
    if not isinstance(series, Mapping):
        return None
    fee_type, multiplier = series.get("fee_type"), series.get("fee_multiplier")
    if not isinstance(fee_type, str) or not isinstance(multiplier, int | Decimal):
        return None
    return Stated(fee_type, Decimal(multiplier), f"series {series.get('ticker', '')}".strip())


def override(changes: Sequence[Mapping[str, object]], now_iso: str) -> Stated | None:
    """An event's override in effect at `now_iso` (RFC 3339, UTC): the latest
    change scheduled at or before it; None where none is, or it cleared the
    override (both null)."""
    due = sorted(
        (
            c
            for c in changes
            if isinstance(c, Mapping) and str(c.get("scheduled_ts", "")) <= now_iso
        ),
        key=lambda c: str(c.get("scheduled_ts", "")),
    )
    if not due:
        return None
    last = due[-1]
    fee_type, multiplier = last.get("fee_type_override"), last.get("fee_multiplier_override")
    if not isinstance(fee_type, str) or not isinstance(multiplier, int | Decimal):
        return None
    return Stated(fee_type, Decimal(multiplier), f"event {last.get('event_ticker', '')}".strip())


def market_fee(code: str, series: Stated | None, event: Stated | None) -> MarketFee:
    """The fee applying to one contract: its event's override where one is
    in effect, else its series'; none where neither is read, or its type is
    not computed."""
    stated = event or series
    if stated is None:
        return MarketFee(code, "", "", "none", "its series' fee type not read yet")
    said = f"{stated.of}: {stated.fee_type} x{_text(stated.multiplier)}"
    computed = coefficients(stated.fee_type, stated.multiplier)
    if computed is None:
        return MarketFee(code, "", "", "none", f"{said}, not computed")
    return MarketFee(code, *computed, "event" if event else "series", said)
