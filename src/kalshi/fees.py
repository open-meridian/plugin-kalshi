"""Kalshi's published fee schedule: not read, and so no rate (571's category
column; task sdk-contract/event-contract-fees-vary-by-market-category).

Kalshi publishes its fee schedule at kalshi.com/docs/kalshi-fee-schedule.pdf,
linked from its help centre's "Fees" article (help.kalshi.com/trading/fees),
whose text gives no rate: "Some markets have fees that are different from
those of other markets". On 2026-10-26 both the schedule and
kalshi.com/fee-schedule answered HTTP 429 behind a bot challenge, as the
schedule did on 2026-10-24, so no rate is stated here and none is assumed.
What Kalshi's public API does state is each series' `fee_type`
(`quadratic`, `quadratic_with_maker_fees`,
`quadratic_with_combo_maker_fees`, `flat`) and `fee_multiplier`, an
event's override of them, and the series' `category`
(docs.kalshi.com, "Get Series Fee Changes", "Get Event Fee Changes"); the
coefficient they multiply is the schedule's. The schedule is read and dated
when it can be, at the plugin's next version.
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class Rate:
    """One category's row, in the venue's words: its taker and maker fee
    rates as text, and its maker rebate ("" where the venue lists none)."""

    category: str
    taker: str
    maker: str
    maker_rebate: str = ""


@dataclass(frozen=True)
class Fees:
    """A venue's published fee schedule: where and when it was read, its
    formula, its rows, what makers pay, and where it states a market's own
    rate; why a rate is left out, where the schedule could not be read."""

    source: str = ""
    read_on: str = ""
    formula: str = ""
    rates: list[Rate] = field(default_factory=list)
    makers: str = ""
    per_market: str = ""
    not_read: str = ""


SOURCE = "https://kalshi.com/docs/kalshi-fee-schedule.pdf"
READ_ON = "2026-10-26"

FEES = Fees(
    source=SOURCE,
    read_on=READ_ON,
    rates=[],
    per_market=(
        "each series states its fee_type, fee_multiplier and category, an event may override "
        "them; the coefficient is the schedule's"
    ),
    not_read=(
        "Kalshi's fee schedule could not be read on 2026-10-26 (HTTP 429 behind a bot "
        "challenge): no rate is assumed"
    ),
)
