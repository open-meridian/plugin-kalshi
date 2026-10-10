"""The client: every answer kept before it is read, the rate limit honoured, a
429 waited out, a 404 an answer rather than a failure, and synthetic mode's
two transports answering as Kalshi does."""

from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path

import pytest

from kalshi.raw import RawStore
from kalshi.synthetic import Recorded, Synthetic
from kalshi.venue import REST, Kalshi, RateLimiter, Response, VenueError

T = "KXSYNTH-26DEC-T4.00"


def _client(tmp_path: Path, transport: object) -> Kalshi:
    clock = iter(range(1_791_633_600_000_000_000, 1_791_633_700_000_000_000, 1_000))
    return Kalshi(
        RawStore(tmp_path),
        transport=transport,  # type: ignore[arg-type]
        limiter=RateLimiter(1000.0, 1000, sleep=lambda _: None),
        clock_ns=lambda: next(clock),
        sleep=lambda _: None,
    )


class Scripted:
    def __init__(self, *answers: Response) -> None:
        self.answers = list(answers)
        self.asked: list[str] = []

    def __call__(self, url: str, headers: Mapping[str, str]) -> Response:
        self.asked.append(url)
        assert "User-Agent" in headers and "Authorization" not in headers, "no key, ever"
        return self.answers.pop(0)


def test_every_answer_is_kept_before_it_is_read(tmp_path: Path) -> None:
    body = b'{"market":{"ticker":"KXSYNTH-26DEC-T4.00"}}'
    client = _client(tmp_path, Scripted(Response(200, {"date": "Sat"}, body)))
    fetched = client.market(T)
    kept = client.store.get(fetched.raw_key)
    assert kept is not None and kept["body"] == body.decode()
    assert kept["headers"] == {"date": "Sat"} and kept["status"] == 200
    assert fetched.raw_key.startswith("responses/2026-10-10/market/")


def test_each_call_asks_for_one_contract(tmp_path: Path) -> None:
    scripted = Scripted(*[Response(200, {}, b"{}") for _ in range(3)])
    client = _client(tmp_path, scripted)
    client.market(T)
    client.orderbook(T)
    client.trades(T)
    assert scripted.asked == [
        f"{REST}/markets/{T}",
        f"{REST}/markets/{T}/orderbook",
        f"{REST}/markets/trades?ticker={T}&limit=1",
    ]


def test_a_429_is_waited_out_and_counted(tmp_path: Path) -> None:
    scripted = Scripted(Response(429, {"retry-after": "1"}, b'{"error":{"message":"slow"}}'),
                        Response(200, {}, b'{"orderbook_fp":{}}'))  # fmt: skip
    client = _client(tmp_path, scripted)
    assert client.orderbook(T).value == {"orderbook_fp": {}}
    assert (client.health.rate_limited, client.health.calls) == (1, 2)


def test_a_404_is_an_answer_kept_and_said_not_a_failure(tmp_path: Path) -> None:
    body = b'{"error":{"code":"not_found","message":"not found"}}'
    client = _client(tmp_path, Scripted(Response(404, {}, body)))
    with pytest.raises(VenueError) as refused:
        client.market("NOPE")
    assert refused.value.status == 404 and "not found" in str(refused.value)
    assert client.store.get(refused.value.raw_key) is not None
    assert client.health.failures == 0 and client.health.last_ok_ns > 0


def test_an_error_is_kept_and_said(tmp_path: Path) -> None:
    client = _client(tmp_path, Scripted(Response(500, {}, b'{"error":{"message":"broken"}}')))
    with pytest.raises(VenueError) as refused:
        client.trades(T)
    assert "broken" in str(refused.value) and client.store.get(refused.value.raw_key)
    assert client.health.failures == 1 and "broken" in client.health.last_error


def test_no_answer_is_said(tmp_path: Path) -> None:
    def down(url: str, headers: Mapping[str, str]) -> Response:
        raise OSError("connection refused")

    client = _client(tmp_path, down)
    with pytest.raises(VenueError):
        client.market(T)
    assert client.health.failures == 1


def test_a_live_answer_unchanged_is_the_line_and_time_first_kept(tmp_path: Path) -> None:
    client = _client(tmp_path, Synthetic())
    first, second = client.orderbook(T), client.orderbook(T)
    assert first.raw_key == second.raw_key and first.raw_key.endswith(".jsonl#0")
    assert first.received_at_ns == second.received_at_ns


def test_synthetic_answers_kalshis_shapes(tmp_path: Path) -> None:
    client = _client(tmp_path, Synthetic())
    market = client.market(T).value["market"]
    assert (market["ticker"], market["market_type"]) == (T, "binary")
    assert str(market["notional_value_dollars"]) == "1.0000"
    assert client.trades(T).value["trades"][0]["trade_id"]
    with pytest.raises(VenueError):
        client.market("NOPE")


def test_recorded_exchanges_are_replayed_from_a_plugins_raw_records(tmp_path: Path) -> None:
    recording = _client(tmp_path / "kept", Synthetic())
    for call in (recording.market, recording.orderbook, recording.trades):
        call(T)
    with pytest.raises(VenueError):
        recording.market("NOPE")
    recorded = Recorded(tmp_path / "kept" / "responses")
    assert ("markets", T) in recorded.calls() and ("trades", T) in recorded.calls()
    replay = _client(tmp_path / "replayed", recorded)
    assert replay.market(T).value == recording.market(T).value
    assert replay.orderbook(T).value == recording.orderbook(T).value
    with pytest.raises(VenueError) as refused:
        replay.market("NOPE")
    assert refused.value.status == 404
