"""The events of the contracts served, reported (contract v26, W3.29): each
read once first served, reported as Kalshi states it, reported again only
where Kalshi states it otherwise, and held back while a member does not
resolve -- the SDK's `Feed.keep_events` (0.32.0) over Kalshi's conversion,
on Kalshi's synthetic exchange. From contract v27 (ruling 464) each range
member's floor, cap and unit go with the report."""

from __future__ import annotations

from dataclasses import replace
from typing import Any

from meridian.operations import as_decimal
from meridian.plugin.v1 import operations_pb2 as ops
from meridian.roles.data import event_contracts
from meridian.roles.data.event_contracts import EVENTS_EVERY_SECONDS
from meridian.roles.data.testing import Lake, held

import venue_cases as venue


class Clock:
    def __init__(self) -> None:
        self.now = 0.0

    def __call__(self) -> float:
        return self.now


async def _serving(lake: Lake, code: str) -> event_contracts.Feed:
    feed = event_contracts.Feed(
        lake, venue.market(), event_contracts.ContractMap(), clock_ns=lambda: venue.NOW_NS
    )
    subject = await held(lake.instruments, feed, code)
    await feed.name([subject])
    for member in venue.EVENT.members + venue.EVENT_PLACEHOLDERS.members:
        await held(lake.instruments, feed, member)
    return feed


def _reports(lake: Lake) -> list[Any]:
    return list(lake.on("ReportEventGroup"))


async def _pass(feed: event_contracts.Feed, clock: Clock | None = None) -> int:
    return await feed.keep_events(once=True, clock=clock or Clock())


async def test_the_event_of_a_contract_served_is_reported_as_kalshi_states_it() -> None:
    lake = Lake(venue.VENUE)
    feed = await _serving(lake, venue.RANGE)
    assert await _pass(feed) == 1
    [report] = _reports(lake)
    assert report.venue_event_ref == venue.EXCLUSIVE and report.series_id == "KXSYNTHHIGH"
    assert len(report.member_instrument_ids) == 3
    assert report.mutually_exclusive == ops.EVENT_GROUP_FLAG_TRUE
    assert report.exhaustive == ops.EVENT_GROUP_FLAG_NOT_STATED
    assert report.raw_record.key


async def test_each_range_members_bounds_go_with_the_report_as_kalshi_states_them() -> None:
    """Contract v27 (ruling 464; the design's report-event-group fixture,
    "v27, each range member's floor, cap and unit"): one bound per member as
    its `strike_type` states it, naming a member of the group, and no unit,
    since Kalshi states none for a strike."""
    lake = Lake(venue.VENUE)
    feed = await _serving(lake, venue.RANGE)
    assert await _pass(feed) == 1
    [report] = _reports(lake)
    stated = {}
    for code in venue.EVENT.members:
        contract = await feed.contract(code)
        assert contract is not None
        stated[await feed.member_id(code)] = contract
    bounds = {b.instrument_id: b for b in report.member_bounds}
    assert bounds and set(bounds) <= set(report.member_instrument_ids)
    for member, contract in stated.items():
        if contract.floor is None and contract.cap is None:
            assert member not in bounds
            continue
        sent = bounds[member]
        for side, said in (("floor", contract.floor), ("cap", contract.cap)):
            if said is None:
                assert not sent.HasField(side)
            else:
                bound = getattr(sent, side)
                assert bound.inclusive is said.inclusive
                assert as_decimal(bound.value) == said.value
        assert sent.bound_unit == ""


async def test_an_event_unchanged_is_not_reported_again_and_one_changed_is() -> None:
    lake, clock = Lake(venue.VENUE), Clock()
    feed = await _serving(lake, venue.BASE)
    assert await _pass(feed, clock) == 1
    assert await _pass(feed, clock) == 0, "read again only after EVENTS_EVERY_SECONDS"
    clock.now += EVENTS_EVERY_SECONDS
    assert await _pass(feed, clock) == 0, "read again, unchanged: nothing sent"
    market: Any = feed.market
    stated = market.event(venue.LADDER)
    market.event = lambda ref: replace(stated, members=stated.members[:3])
    clock.now += EVENTS_EVERY_SECONDS
    assert await _pass(feed, clock) == 1 and len(_reports(lake)) == 2


async def test_an_event_a_member_of_which_does_not_resolve_is_held_back() -> None:
    lake, clock = Lake(venue.VENUE), Clock()
    feed = event_contracts.Feed(
        lake, venue.market(), event_contracts.ContractMap(), clock_ns=lambda: venue.NOW_NS
    )
    subject = await held(lake.instruments, feed, venue.RANGE)
    await feed.name([subject])
    lake.answer(
        "ResolveIdentifier",
        lambda _: ops.ResolveIdentifierResult(found=False, miss_reason=ops.MISS_REASON_NOT_FOUND),
    )
    assert await _pass(feed, clock) == 0 and not _reports(lake)
    lake.instruments.answering(lake)
    for member in venue.EVENT.members:
        await held(lake.instruments, feed, member)
    assert await _pass(feed, clock) == 1, "read again on the next pass, not ten minutes on"
