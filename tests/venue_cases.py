"""Kalshi's side of the data role's checks: this plugin's synthetic exchanges,
named for what each of the checks asks a source to present.

tests/test_data_role.py runs the SDK's checks for an event-contract venue
(`meridian.roles.data.testing.EventContractsChecks`) -- the data suite
unchanged, the venue's work past the suite's cases, its outcomes, and the
pages -- against this plugin's own conversion; this module is the one place
they learn which venue they are holding. Each answer comes through the
plugin's real client, raw records and reading (synthetic.py's transport over
the exchanges this package carries, `src/kalshi/synthetic/`), with invented
markets and values; real recordings are never committed (the plan's Q11).
"""

from __future__ import annotations

import tempfile
from datetime import date
from pathlib import Path
from typing import Any

from meridian.edge import RawStore
from meridian.roles.data.event_contracts import Market

from kalshi import page
from kalshi.convert import KalshiMarket
from kalshi.synthetic import Synthetic
from kalshi.venue import Kalshi, RateLimiter

__all__ = ["page"]

SYNTHETIC = Path(__file__).parent.parent / "src" / "kalshi" / "synthetic"

#: The venue's name as a symbol's source, and the plugin's.
VENUE = "kalshi"
#: The suite's clock: 2026-10-10 12:00 UTC.
NOW_NS = 1_791_633_600 * 1_000_000_000
TODAY = date(2026, 10, 10)

#: A binary contract with both sides of its book and a last trade.
BASE = "KXSYNTH-26DEC-T4.00"
#: Its last trade's YES price, its best YES bid and size, and its ask -- the
#: payout less its best NO bid (0.5600) -- with that NO bid's size.
LAST = "0.4300"
BID, BID_SIZE = "0.4300", "55.00"
ASK, ASK_SIZE = "0.4400", "30.00"
#: What one contract pays, in the venue's cash.
PAYOUT, CASH = "1.0000", "USD"
#: A contract whose prices have more places than a float holds.
EXACT = "KXSYNTH-26DEC-T4.25"
EXACT_LAST = "0.123456789012345678"
#: A contract with bids and no offer: nobody bids for its NO side.
ONE_SIDED = "KXSYNTH-26DEC-T4.50"
#: A contract whose book and last trade an older answer states in cents.
CENTS = "KXSYNTH-26DEC-T3.75"
CENTS_BID, CENTS_ASK, CENTS_LAST = "0.41", "0.4300", "0.41"
#: A market Kalshi does not state as binary.
NOT_BINARY = "KXSYNTHRANGE-26DEC"
#: Kalshi prices in dollars: no stablecoin, so its cash is a currency code.
STABLE = False

# ── Outcomes (contract v23) ─────────────────────────────────────────────────

#: Where each later stage of a contract's determination is stated: the same
#: market as Kalshi answers it then, beside the package's exchanges.
EXCHANGES = Path(__file__).parent / "exchanges"
#: A market Kalshi has determined `yes`, settling at its payout: its outcome
#: from its own side, at the stage Kalshi states, with Kalshi's word.
RESOLVED = "KXSYNTH-26OCT-T4.00"
RESOLVED_STAGE = "OUTCOME_STAGE_DETERMINED"
WORD = ("kalshi:result", "yes")
#: A market determined `no`, its settlement value not stated: nothing.
RESOLVED_LOSER = "KXSYNTH-26OCT-T4.50"
#: A market determined `scalar`, settling at part of its payout.
PARTIAL, PARTIAL_VALUE = "KXSYNTH-26OCT-T4.10", "0.4500"
#: A market past its close that Kalshi has not determined yet.
PENDING = "KXSYNTH-26OCT-T3.75"
#: The resolved market's later stages, each as Kalshi then answers it:
#: disputed, then finalized and paid out at its `settlement_ts`.
LATER = (
    (EXCHANGES / "disputed", "OUTCOME_STAGE_DISPUTED", 0),
    (EXCHANGES / "finalized", "OUTCOME_STAGE_FINAL", 1_791_572_700 * 1_000_000_000),
)
#: The suite's outcome cases, each as Kalshi presents it: determined, then
#: disputed after it was recorded; and a scalar result.
DETERMINED: str | None = RESOLVED
DISPUTED: tuple[str, tuple[Path, ...]] | None = (RESOLVED, (EXCHANGES / "disputed",))

#: The suite's cases Kalshi's one dataset never presents, each with why: the
#: dataset publishes prices and quotes now, per contract, in dollars.
NOT_PRESENTED = {
    "a-daily-close": "its one dataset publishes live prices and quotes, and no daily closes",
    "the-forming-day-restated": "its one dataset publishes no daily closes to restate",
    "a-daily-bar": "its one dataset publishes live prices and quotes, and no bars",
    "an-fx-rate": "it prices event contracts, and no currency's rate against another",
    "a-stablecoin-quote": "its prices are in US dollars, and it quotes nothing in a stablecoin",
    "a-subject-another-source-resolved": "its subjects are event contracts, and no security",
    "a-trade-recorded": "its one dataset publishes prices and quotes, and no trades",
    "the-makers-side-inverted": "its one dataset publishes no trades",
    "a-condition-converted": "its one dataset publishes no trades",
    "a-condition-not-converted": "its one dataset publishes no trades",
    "a-trade-withdrawn": "its one dataset publishes no trades",
    "a-standing-want-streamed": "its one dataset publishes no trades to stream",
    "the-takers-side-stated": "its one dataset publishes no trades",
    "a-restarts-gap-backfilled": "its one dataset publishes no trades, so a restart leaves no gap "
    "of trades to read back",
    "reads-a-calendar": "it records event contracts' prices and quotes as they stream: it reads "
    "no settlement calendar",
    "asks-for-a-settlement-date": "it records prices and quotes as published; an event contract "
    "settles on its outcome, and it never computes a settlement date",
}


def _instant(_: float) -> None:
    return None


def market(now_ns: int = NOW_NS, directory: Path | None = None) -> Market:
    """Kalshi's synthetic exchange through the plugin's own client, its answers
    kept in a fresh store."""
    store = RawStore(Path(tempfile.mkdtemp(prefix="kalshi-raw-")))
    client = Kalshi(
        store,
        transport=Synthetic(directory or SYNTHETIC),
        limiter=RateLimiter(1000.0, 1000, sleep=_instant),
        clock_ns=lambda: now_ns,
        sleep=_instant,
    )
    return KalshiMarket(client, "synthetic")


def calls(market: Any) -> list[str]:
    """The URLs the plugin asked of the venue, in order, from its raw records."""
    return [r["request"]["url"] for r in market.client.store.records()]
