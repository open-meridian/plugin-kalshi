"""Kalshi's answers read into the venue's values: one contract and two sides,
the NO side converted, dollars and cents exactly, the last trade."""

from __future__ import annotations

from decimal import Decimal
from typing import Any

from meridian.roles.data.event_contracts import Contract

from kalshi import convert

import venue_cases as venue

CONTRACT = Contract(code="KX-1", title="Will it?", binary=True, payout=Decimal("1.0000"))


def _top(book: dict[str, Any], of: Contract = CONTRACT) -> Any:
    return convert.top(of, book, "responses/2026-10-10/orderbook/KX-1.jsonl#0", 7)


def test_the_ask_is_the_payout_less_the_best_no_bid_with_its_size() -> None:
    book = {
        "orderbook_fp": {
            "yes_dollars": [["0.4100", "120.00"], ["0.4300", "55.00"]],
            "no_dollars": [["0.5600", "30.00"], ["0.5000", "400.00"]],
        }
    }
    top = _top(book)
    assert (str(top.bid), str(top.bid_size)) == ("0.4300", "55.00")
    assert (str(top.ask), str(top.ask_size)) == ("0.4400", "30.00")
    assert top.stated is False and top.at_ns == 7, "Kalshi's book states no time"


def test_cents_are_dollars_by_moving_the_point() -> None:
    top = _top({"orderbook": {"yes": [[41, 10], [39, 100]], "no": [[57, 5]]}})
    assert (str(top.bid), str(top.ask), str(top.ask_size)) == ("0.41", "0.4300", "5")
    trade = convert.tick(CONTRACT, {"trades": [{"yes_price": 41, "trade_id": "t",
                                                "created_time": "2026-10-10T11:50:00Z"}]},
                         "k", 0)  # fmt: skip
    assert str(trade.price) == "0.41" and trade.stated


def test_an_empty_book_has_neither_side_and_one_side_alone_is_one_sided() -> None:
    empty = _top({"orderbook_fp": {"yes_dollars": [], "no_dollars": []}})
    assert (empty.bid, empty.ask, empty.bid_size, empty.ask_size) == (None, None, None, None)
    bids = _top({"orderbook_fp": {"yes_dollars": [["0.0300", "64.00"]], "no_dollars": None}})
    assert str(bids.bid) == "0.0300" and bids.ask is None and bids.ask_size is None


def test_a_level_that_does_not_read_is_kept_as_sent() -> None:
    top = _top({"orderbook_fp": {"yes_dollars": [["n/a", "1.00"], ["0.2000", "2.00"]],
                                 "no_dollars": [["0.7000", "lots"]]}})  # fmt: skip
    assert str(top.bid) == "0.2000" and str(top.ask) == "0.3000" and top.ask_size is None
    assert {u.field for u in top.unread} == {"orderbook.yes_dollars.price",
                                             "orderbook.no_dollars.size"}  # fmt: skip


def test_no_payout_stated_leaves_the_ask_unread() -> None:
    top = _top({"orderbook_fp": {"yes_dollars": [], "no_dollars": [["0.6000", "1.00"]]}},
               of=Contract(code="KX-1", title="", binary=True, payout=None))  # fmt: skip
    assert top.ask is None and [u.field for u in top.unread] == ["orderbook.ask"]


def test_a_market_is_a_contract_with_its_payout_close_and_words() -> None:
    body = {"ticker": "KX-1", "title": "Will it?", "market_type": "binary",
            "notional_value_dollars": "1.0000", "close_time": "2026-12-09T18:55:00Z",
            "status": "active", "event_ticker": "KX"}  # fmt: skip
    read = convert.contract(body, "raw")
    assert (read.code, read.title, read.binary, str(read.payout)) == ("KX-1", "Will it?", True,
                                                                     "1.0000")  # fmt: skip
    assert read.closes_at_ns == 1_796_842_500 * 1_000_000_000 and read.tradable
    scalar = convert.contract(body | {"market_type": "scalar", "status": "settled"}, "raw")
    assert not scalar.binary and not scalar.tradable
    unread = convert.contract(body | {"notional_value_dollars": "lots"}, "raw")
    assert unread.payout is None and unread.unread


def test_the_last_trade_is_the_yes_price_at_its_time() -> None:
    body = {
        "trades": [
            {
                "yes_price_dollars": "0.4300",
                "no_price_dollars": "0.5700",
                "created_time": "2026-10-10T11:58:30.123456Z",
                "trade_id": "t-1",
            }
        ]
    }
    trade = convert.tick(CONTRACT, body, "k", 0)
    assert str(trade.price) == "0.4300" and trade.ident == "t-1" and trade.stated
    assert trade.at_ns == 1_791_633_510_123_456_000
    none = convert.tick(CONTRACT, {"trades": []}, "k", 9)
    assert none.price is None and not none.unread and none.at_ns == 9


def test_the_synthetic_exchange_reads_as_the_cases_say() -> None:
    market = venue.market()
    base = market.contract(venue.BASE)
    assert base is not None and str(base.payout) == venue.PAYOUT
    top = market.top(base)
    assert (str(top.bid), str(top.ask)) == (venue.BID, venue.ASK)
    cents = market.contract(venue.CENTS)
    assert cents is not None
    assert (str(market.top(cents).bid), str(market.top(cents).ask)) == (venue.CENTS_BID,
                                                                       venue.CENTS_ASK)  # fmt: skip
    assert str(market.last(cents).price) == venue.CENTS_LAST
    assert market.contract("NOPE") is None
    assert market.cash.currency_code == "USD" and market.venue_identifiers == (
        ("iso10383", "KLSH", ""),
    )


# ── Its outcome (contract v23) ──────────────────────────────────────────────


def _resolution(**market: Any) -> Any:
    return convert.resolution(market, Decimal("1.0000"))


def test_each_status_stating_a_determination_is_its_stage() -> None:
    stages = {status: getattr(_resolution(status=status, result="yes"), "stage", None)
              for status in ("active", "closed", "determined", "disputed", "amended",
                             "finalized")}  # fmt: skip
    assert stages == {"active": None, "closed": None, "determined": "determined",
                      "disputed": "disputed", "amended": "determined",
                      "finalized": "final"}  # fmt: skip


def test_the_settlement_value_stated_is_what_one_contract_settles_at() -> None:
    said = _resolution(status="determined", result="scalar", settlement_value_dollars="0.4500")
    assert (str(said.value), said.scheme, said.word, said.text) == (
        "0.4500",
        "kalshi:result",
        "scalar",
        "scalar",
    )
    assert said.determined_at_ns == 0, "Kalshi states no time of determination"


def test_yes_and_no_with_no_value_stated_settle_at_the_payout_and_at_nothing() -> None:
    assert _resolution(status="determined", result="yes").value == Decimal("1.0000")
    assert _resolution(status="determined", result="no").value == 0


def test_a_value_that_does_not_read_is_kept_as_sent() -> None:
    said = _resolution(status="determined", result="yes", settlement_value_dollars="1.00.00")
    assert said.value is None
    assert said.unread[0].field == "market.settlement_value_dollars"


def test_finalized_carries_its_payout_time_and_nothing_before() -> None:
    final = _resolution(status="finalized", result="yes", settlement_ts="2026-10-09T19:05:00Z")
    assert final.settled_at_ns == 1_791_572_700 * 1_000_000_000
    early = _resolution(status="determined", result="yes", settlement_ts="2026-10-09T19:05:00Z")
    assert early.settled_at_ns == 0


def test_a_market_is_read_with_its_determination_and_when_its_answer_arrived() -> None:
    market = venue.market()
    resolved = market.contract(venue.RESOLVED)
    assert resolved is not None and resolved.resolution is not None
    assert resolved.read_at_ns == venue.NOW_NS and not resolved.tradable
    active = market.contract(venue.BASE)
    assert active is not None and active.resolution is None


# ── Contract v26: events and a range market's bounds ────────────────────────


def _bounds(**market: Any) -> Any:
    unread: list[Any] = []
    return convert.bounds(market, unread), unread


def test_a_one_sided_strike_is_one_bound_inclusive_as_its_type_says() -> None:
    (floor, cap), _ = _bounds(strike_type="greater", floor_strike=Decimal("4.00"))
    assert (str(floor.value), floor.inclusive, cap) == ("4.00", False, None)
    (floor, cap), _ = _bounds(strike_type="greater_or_equal", floor_strike=Decimal("4.00"))
    assert floor.inclusive is True and cap is None
    (floor, cap), _ = _bounds(strike_type="less", cap_strike=Decimal("84"))
    assert (floor, str(cap.value), cap.inclusive) == (None, "84", False)
    (floor, cap), _ = _bounds(strike_type="less_or_equal", cap_strike=Decimal("84"))
    assert floor is None and cap.inclusive is True


def test_a_range_is_both_bounds_inclusive_and_another_strike_none() -> None:
    (floor, cap), _ = _bounds(strike_type="between", floor_strike=84, cap_strike=85)
    assert (str(floor.value), floor.inclusive, str(cap.value), cap.inclusive) == (
        "84", True, "85", True,
    )  # fmt: skip
    assert _bounds(strike_type="functional", functional_strike="x")[0] == (None, None)
    assert _bounds(strike_type="greater")[0] == (None, None), "no strike stated, no bound"


def test_a_strike_that_does_not_read_is_kept_as_sent() -> None:
    (floor, _), unread = _bounds(strike_type="greater", floor_strike="four")
    assert floor is None and [(u.field, u.text) for u in unread] == [
        ("market.floor_strike", "four")
    ]


def test_an_event_is_its_markets_exclusive_as_kalshi_states_never_exhaustive() -> None:
    exclusive = venue.EVENT
    assert exclusive.ref == venue.EXCLUSIVE and exclusive.series == "KXSYNTHHIGH"
    assert exclusive.members == (venue.LOWER_TAIL, venue.RANGE, venue.UPPER_TAIL)
    assert (exclusive.mutually_exclusive, exclusive.exhaustive) == (True, None)
    assert exclusive.raw_key and exclusive.valid_from_ns == venue.NOW_NS
    ladder = venue.EVENT_PLACEHOLDERS
    assert (ladder.mutually_exclusive, ladder.exhaustive) == (False, None)
    assert len(ladder.members) == 4 and venue.BASE in ladder.members


def test_an_event_naming_no_market_is_none_and_old_answers_are_read() -> None:
    assert convert.event({"event_ticker": "KX", "markets": []}, "k") is None
    assert convert.event({"markets": [{"ticker": "KX-1"}]}, "k") is None
    said = convert.event({"event_ticker": "KX", "markets": [{"ticker": "KX-1"}]}, "k")
    assert said is not None and said.mutually_exclusive is None, "not stated, never false"
    assert venue.market().event("KXNOSUCH") is None  # type: ignore[attr-defined]


def test_a_range_markets_bounds_are_on_its_contract_and_kept_in_the_map(tmp_path: Any) -> None:
    from meridian.roles.data.event_contracts import ContractMap

    market = venue.market()
    ranged = market.contract(venue.RANGE)
    tail = market.contract(venue.LOWER_TAIL)
    assert ranged is not None and tail is not None
    assert ranged.floor is not None and ranged.cap is not None
    assert (str(ranged.floor.value), ranged.floor.inclusive) == ("84", True)
    assert (str(ranged.cap.value), ranged.cap.inclusive) == ("85", True)
    assert tail.floor is None and tail.cap is not None and tail.cap.inclusive is False
    assert ranged.bound_unit == "", "Kalshi states no unit for a strike"
    kept = ContractMap(tmp_path / "contracts.json")
    kept.contracts[ranged.code] = ranged
    kept.save()
    again = ContractMap(tmp_path / "contracts.json")
    assert again.load() and again.contracts[ranged.code].floor == ranged.floor
