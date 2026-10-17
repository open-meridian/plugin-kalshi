"""Kalshi's answers, read into the venue's values (the SDK's
`meridian.roles.data.event_contracts`): the one place
Kalshi's vocabulary is read.

- **The cash** is the US dollar, by its ISO 4217 code: Kalshi's prices and
  payouts are dollars.
- **A contract** is one Kalshi market, by its ticker (`KXFED-27APR-T4.25`),
  binary where its `market_type` says so; what it pays is its
  `notional_value_dollars`, the dollar amount one contract pays if the event
  happens (1.0000); trading closes at its `close_time`. Its `title` is the
  venue's words for what it pays on. It trades while its `status` is
  `active` (or `open`).
- **One contract, two sides** (the plan's "The event contract"; step 5's
  ruling of 2026-09-30). Kalshi's book holds resting bids alone, on the YES
  side and on the NO side; a NO bid at p is an offer to sell YES at the
  payout less p. So the contract's quote is its best YES bid, and an ask of
  the payout less its best NO bid, with that NO bid's size: exact by the
  contract's definition, the raw book kept beside it. The plugin records
  the YES contract alone; its NO side is the same contract, held short.
- **Dollars, exactly.** Kalshi states each price in dollars as text
  (`yes_dollars`, `0.4300`) and each size in contracts as text
  (`120.00`, a fractional contract possible); an older answer states prices
  in whole cents (`yes`, `43`), converted to dollars at the edge by moving
  the point, never through a float.
- **Its outcome** (contract v23; the lake plan's "vL1c") is read from the
  same market answer. Kalshi's statuses run `closed`, `determined`, then
  (`disputed`, `amended`), then `finalized`
  (docs.kalshi.com, "Market lifecycle"): `determined` is the stage
  determined, `disputed` disputed, `amended` determined again -- a new
  version -- and `finalized` final; before `determined` there is none.
  What one contract settles at is its `settlement_value_dollars`, Kalshi's
  YES-side settlement value, the contract the plugin records; where Kalshi
  states none, `result` `yes` settles at the payout and `no` at nothing.
  Kalshi's word is its `result` (`yes`, `no` or `scalar`), kept as
  reported; its payout time `settlement_ts`, set when finalized. Kalshi
  states no time of determination, so the determination is valid from when
  the answer first stating it arrived.
- **The last trade** is `/markets/trades`' first, its `yes_price_dollars` (or
  `yes_price` in cents) at its `created_time`, its `trade_id` its identity.
  Kalshi's book states no time, so a quote is valid from when its answer
  first arrived.
"""

from __future__ import annotations

import datetime as _dt
import re
from collections.abc import Mapping, Sequence
from decimal import Decimal
from typing import Any

from meridian.roles.data import NANOS_PER_SECOND, Endpoint, Limits, Session, Unread, number
from meridian.roles.data.event_contracts import (
    DETERMINED,
    DISPUTED,
    FINAL,
    Cash,
    Contract,
    Resolution,
    Tick,
    Top,
)

from .venue import BURST, NOT_FOUND, RATE_PER_SECOND, REST, Kalshi, VenueError

VENUE = "kalshi"
NAME = "Kalshi"
#: What the venue entitles this plugin to: its public market data, no key.
ENTITLED = "Public market data: a contract is read only for a subject the lake asked for"
#: How the venue's two sides make one contract's quote, said on the Datasets
#: page: Kalshi's book holds bids alone, YES and NO.
VENDOR_NOTE = (
    "A contract's quote is its best YES bid, and an ask of the payout less its best NO bid: "
    "Kalshi's book holds bids alone, on both sides."
)
#: Kalshi in the venue master: its ISO 10383 MIC.
VENUE_IDENTIFIERS: tuple[tuple[str, str, str], ...] = (("iso10383", "KLSH", ""),)
CASH = Cash("USD", "currency", "iso4217", "USD", "US dollar")
#: The statuses in which Kalshi trades a market.
TRADING = frozenset({"active", "open"})
#: Kalshi's statuses that state a determination, as the contract's stages.
STAGES = {"determined": DETERMINED, "amended": DETERMINED, "disputed": DISPUTED,
          "finalized": FINAL}  # fmt: skip
#: Where Kalshi's word for a determination is, as reported.
RESULT = "kalshi:result"

LIMITS = Limits(
    allowed="Kalshi limits its API's requests per account tier; its market data needs no key",
    spent=f"At most {RATE_PER_SECOND:g} a second, bursts of {BURST}; a 429 waited out",
)

_RFC3339 = re.compile(
    r"(\d{4})-(\d{2})-(\d{2})[T ](\d{2}):(\d{2}):(\d{2})(?:\.(\d{1,9}))?(Z|[+-]\d{2}:\d{2})"
)


def rfc3339_ns(text: str) -> int:
    """An RFC 3339 time, to the nanosecond (datetime holds only six digits)."""
    match = _RFC3339.fullmatch(text)
    if match is None:
        raise ValueError(f"{text!r} is not an RFC 3339 time")
    year, month, day, hour, minute, second, fraction, zone = match.groups()
    offset = _dt.timedelta()
    if zone != "Z":
        sign = 1 if zone[0] == "+" else -1
        offset = sign * _dt.timedelta(hours=int(zone[1:3]), minutes=int(zone[4:6]))
    moment = _dt.datetime(
        int(year), int(month), int(day), int(hour), int(minute), int(second),
        tzinfo=_dt.timezone(offset),
    )  # fmt: skip
    return int(moment.timestamp()) * NANOS_PER_SECOND + int((fraction or "0").ljust(9, "0"))


def _when(text: object) -> int:
    try:
        return rfc3339_ns(str(text)) if text else 0
    except ValueError:
        return 0


def resolution(body: Mapping[str, Any], payout: Decimal | None) -> Resolution | None:
    """A market's determination, at the stage its status states; None before
    Kalshi determines it."""
    stage = STAGES.get(str(body.get("status") or ""))
    if stage is None:
        return None
    result = str(body.get("result") or "")
    stated = body.get("settlement_value_dollars")
    value = number(stated) if stated not in (None, "") else None
    unread: list[Unread] = []
    if stated not in (None, "") and value is None:
        unread.append(Unread("market.settlement_value_dollars", str(stated)))
    elif value is None and result == "yes":
        value = payout
    elif value is None and result == "no":
        value = Decimal(0)
    return Resolution(
        stage=stage,
        value=value,
        scheme=RESULT if result else "",
        word=result,
        text=result,
        settled_at_ns=_when(body.get("settlement_ts")) if stage == FINAL else 0,
        unread=tuple(unread),
    )


def contract(body: Mapping[str, Any], raw_key: str, received_ns: int = 0) -> Contract:
    """One market, from `/markets/{ticker}`'s `market`, with its
    determination where Kalshi states one."""
    unread: list[Unread] = []
    stated = body.get("notional_value_dollars")
    payout = number(stated)
    if payout is None:
        unread.append(Unread("market.notional_value_dollars", str(stated)))
    status = str(body.get("status") or "")
    return Contract(
        code=str(body["ticker"]),
        title=str(body.get("title") or body.get("subtitle") or ""),
        binary=body.get("market_type") == "binary",
        payout=payout,
        closes_at_ns=_when(body.get("close_time")),
        tradable=status in TRADING,
        status=status,
        market=str(body.get("event_ticker") or ""),
        raw_key=raw_key,
        unread=tuple(unread),
        resolution=resolution(body, payout),
        read_at_ns=received_ns,
    )


def _cents(value: object) -> Decimal | None:
    """A price stated in whole cents, in dollars, by moving the point."""
    if isinstance(value, bool) or not isinstance(value, int | Decimal | str):
        return None
    amount = number(value)
    return None if amount is None else amount.scaleb(-2)


def _best(levels: object, dollars: bool, side: str, unread: list[Unread]) -> tuple[Any, Any]:
    """The highest bid of a side's levels, `[price, size]` each, and its size;
    a level whose price or size does not read is kept as sent."""
    best: tuple[Decimal, Decimal | None] | None = None
    for level in levels if isinstance(levels, Sequence) and not isinstance(levels, str) else []:
        if not isinstance(level, Sequence) or isinstance(level, str) or len(level) < 2:
            unread.append(Unread(f"orderbook.{side}", str(level)))
            continue
        price = number(level[0]) if dollars else _cents(level[0])
        size = number(level[1])
        if price is None:
            unread.append(Unread(f"orderbook.{side}.price", str(level[0])))
            continue
        if size is None:
            unread.append(Unread(f"orderbook.{side}.size", str(level[1])))
        if best is None or price > best[0]:
            best = (price, size)
    return best if best is not None else (None, None)


def top(of: Contract, body: Mapping[str, Any], raw_key: str, received_ns: int) -> Top:
    """The contract's best bid and offer: its best YES bid, and the payout less
    its best NO bid, each with its size."""
    unread: list[Unread] = []
    if "orderbook_fp" in body:
        book, dollars, yes, no = body.get("orderbook_fp") or {}, True, "yes_dollars", "no_dollars"
    else:
        book, dollars, yes, no = body.get("orderbook") or {}, False, "yes", "no"
    bid, bid_size = _best(book.get(yes), dollars, yes, unread)
    no_bid, no_size = _best(book.get(no), dollars, no, unread)
    ask = None
    if no_bid is not None and of.payout is not None:
        ask = of.payout - no_bid
    elif no_bid is not None:
        unread.append(Unread("orderbook.ask", f"{no_bid} with no payout stated"))
    return Top(
        code=of.code,
        bid=bid,
        ask=ask,
        bid_size=bid_size if bid is not None else None,
        ask_size=no_size if ask is not None else None,
        at_ns=received_ns,
        stated=False,
        raw_key=raw_key,
        unread=tuple(unread),
    )


def tick(of: Contract, body: Mapping[str, Any], raw_key: str, received_ns: int) -> Tick:
    """The contract's last trade, its YES price; no trade, no price."""
    trades = body.get("trades") or []
    if not trades:
        return Tick(code=of.code, price=None, at_ns=received_ns, stated=False, raw_key=raw_key)
    last = trades[0]
    if "yes_price_dollars" in last:
        stated, price = last.get("yes_price_dollars"), number(last.get("yes_price_dollars"))
    else:
        stated, price = last.get("yes_price"), _cents(last.get("yes_price"))
    at = _when(last.get("created_time"))
    return Tick(
        code=of.code,
        price=price,
        at_ns=at or received_ns,
        stated=bool(at),
        ident=str(last.get("trade_id") or ""),
        raw_key=raw_key,
        unread=() if price is not None else (Unread("trades.yes_price", str(stated)),),
    )


class KalshiMarket:
    """Kalshi's market data, as the shared data plugin's work asks for it."""

    venue = VENUE
    name = NAME
    venue_identifiers = VENUE_IDENTIFIERS
    cash = CASH

    def __init__(self, client: Kalshi, mode: str = "live") -> None:
        self.client = client
        address = REST if mode == "live" else f"{mode}: no call leaves the deployment"
        self.session = Session(
            mode=mode,
            endpoints=(
                Endpoint("REST", address, "a market and its outcome, its book and its last trade"),
            ),
            limits=LIMITS,
            health=client.health,
        )

    def contract(self, code: str, watching: bool = False) -> Contract | None:
        try:
            fetched = self.client.market(code, live=watching)
        except VenueError as refused:
            if refused.status == NOT_FOUND:
                return None
            raise
        body = fetched.value.get("market") if isinstance(fetched.value, Mapping) else None
        if not isinstance(body, Mapping) or "ticker" not in body:
            return None
        return contract(body, fetched.raw_key, fetched.received_at_ns)

    def last(self, of: Contract) -> Tick:
        fetched = self.client.trades(of.code)
        return tick(of, fetched.value, fetched.raw_key, fetched.received_at_ns)

    def top(self, of: Contract) -> Top:
        fetched = self.client.orderbook(of.code)
        return top(of, fetched.value, fetched.raw_key, fetched.received_at_ns)
