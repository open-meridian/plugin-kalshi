"""Kalshi's settlement timer (from 0.10.0): a determination's window to
dispute it, `Outcome.challenge_ends_at_ns`, counted from when the answer
first stating it arrived, only where the read before it stated none and was
at most two minutes earlier; never counted from a read it did not follow."""

from __future__ import annotations

import json
from collections.abc import Mapping
from pathlib import Path
from typing import Any

from meridian.edge import RawStore

from kalshi.convert import KalshiMarket
from kalshi.venue import Kalshi, RateLimiter, Response

T = "KXSYNTH-26OCT-T4.00"
START = 1_791_633_600_000_000_000
SECOND = 1_000_000_000
MARKETS = Path(__file__).parent.parent / "src" / "kalshi" / "synthetic" / "markets.json"


class Clock:
    def __init__(self) -> None:
        self.now = START

    def __call__(self) -> int:
        return self.now


class Statuses:
    """Kalshi's answer for one market, its status set before each read."""

    def __init__(self) -> None:
        self.market: dict[str, Any] = json.loads(MARKETS.read_text())[T]["market"]

    def set(self, status: str, timer: int = 300) -> None:
        self.market = {**self.market, "status": status, "settlement_timer_seconds": timer}
        if status == "closed":
            self.market = {k: v for k, v in self.market.items() if k != "result"}
        else:
            self.market["result"] = "yes"

    def __call__(self, url: str, headers: Mapping[str, str]) -> Response:
        return Response(200, {}, json.dumps({"market": self.market}).encode())


def _market(tmp_path: Path) -> tuple[KalshiMarket, Statuses, Clock]:
    clock, answers = Clock(), Statuses()
    client = Kalshi(
        RawStore(tmp_path),
        transport=answers,
        limiter=RateLimiter(1000.0, 1000, sleep=lambda _: None),
        clock_ns=clock,
        sleep=lambda _: None,
    )
    return KalshiMarket(client, "synthetic"), answers, clock


def _ends(market: KalshiMarket) -> int:
    read = market.contract(T, watching=True)
    assert read is not None and read.resolution is not None
    return read.resolution.challenge_ends_at_ns


def test_the_timer_runs_from_the_answer_first_stating_the_determination(tmp_path: Path) -> None:
    market, answers, clock = _market(tmp_path)
    answers.set("closed")
    assert market.contract(T, watching=True) is not None
    clock.now += 60 * SECOND
    answers.set("determined")
    arrived = clock.now
    assert _ends(market) == arrived + 300 * SECOND
    # Read again, unchanged: the same end, never moved by a later read.
    clock.now += 60 * SECOND
    assert _ends(market) == arrived + 300 * SECOND


def test_an_amended_determination_restarts_the_timer(tmp_path: Path) -> None:
    market, answers, clock = _market(tmp_path)
    answers.set("closed")
    market.contract(T, watching=True)
    clock.now += 60 * SECOND
    answers.set("determined")
    market.contract(T, watching=True)
    clock.now += 60 * SECOND
    answers.set("disputed")
    assert _ends(market) == 0, "a dispute states no window of its own"
    clock.now += 60 * SECOND
    answers.set("amended", timer=600)
    assert _ends(market) == clock.now + 600 * SECOND


def test_a_determination_not_followed_from_a_read_states_no_end(tmp_path: Path) -> None:
    market, answers, clock = _market(tmp_path)
    answers.set("determined")
    assert _ends(market) == 0, "first read already determined: when it began is not known"
    other, answers, clock = _market(tmp_path / "late")
    answers.set("closed")
    other.contract(T, watching=True)
    clock.now += 10 * 60 * SECOND
    answers.set("determined")
    assert _ends(other) == 0, "the read before it was too long ago"
