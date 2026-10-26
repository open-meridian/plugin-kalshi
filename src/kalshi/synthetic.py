"""Synthetic mode: Kalshi's answers from files, never from Kalshi.

A developer's setting (`synthetic`, shown only on a development deployment)
turns it on. The client asks exactly as it asks Kalshi, keeps each answer as
a raw record and reads it the same way; only the transport differs:

- `Synthetic`: the synthetic exchanges this package carries (`synthetic/`),
  shaped exactly as Kalshi documents and sends its answers -- prices in
  dollars as text, sizes in contracts as text, and one market's book and
  last trade in the older whole cents -- with invented markets (tickers
  `KXSYNTH-...`) and invented values. They are what CI and `make e2e`
  replay.
- `Recorded`: a developer's own recorded exchanges -- the raw records a
  plugin kept of Kalshi's real answers to its public reads -- replayed by
  `make e2e-recorded` from a directory that is never committed (the plan's
  Q11).
"""

from __future__ import annotations

import json
import urllib.parse
from collections.abc import Mapping
from importlib import resources
from pathlib import Path
from typing import Any

from .venue import Response

_HEADERS = {"cache-control": "no-store"}
_FILES = ("markets", "orderbook", "trades")
#: Kept only where a directory states events (contract v26): a later
#: stage's exchanges state none.
_OPTIONAL = ("events", "candlesticks", "series", "fee-changes")


def _found(body: Any) -> Response:
    return Response(200, dict(_HEADERS), json.dumps(body).encode("utf-8"))


def _missing() -> Response:
    return Response(404, dict(_HEADERS), b'{"error":{"code":"not_found","message":"not found"}}')


def _route(url: str) -> tuple[list[str], dict[str, str]]:
    split = urllib.parse.urlsplit(url)
    parts = [urllib.parse.unquote(p) for p in split.path.split("/") if p]
    # The API's own prefix, /trade-api/v2, is the same for every call.
    if parts[:2] == ["trade-api", "v2"]:
        parts = parts[2:]
    return parts, dict(urllib.parse.parse_qsl(split.query))


def _asked(url: str) -> tuple[str, str] | None:
    """Which call a request is, and of which ticker."""
    parts, query = _route(url)
    if parts == ["markets", "candlesticks"] and query.get("market_tickers"):
        keys = ("market_tickers", "period_interval", "start_ts", "end_ts")
        return "candlesticks", "|".join(query.get(k, "") for k in keys)
    if parts == ["events", "fee_changes"] and query.get("event_ticker"):
        return "fee-changes", query["event_ticker"]
    if parts == ["markets", "trades"] and query.get("ticker"):
        return "trades", query["ticker"]
    if len(parts) == 2 and parts[0] == "markets":
        return "markets", parts[1]
    if len(parts) == 3 and parts[0] == "markets" and parts[2] == "orderbook":
        return "orderbook", parts[1]
    if len(parts) == 2 and parts[0] == "events":
        return "events", parts[1]
    if len(parts) == 2 and parts[0] == "series":
        return "series", parts[1]
    return None


class Synthetic:
    """Answers from a directory of synthetic exchanges: `markets.json`,
    `orderbook.json` and `trades.json`, each Kalshi's body per ticker, and
    `events.json`, each event's body per event ticker, where it has one;
    from 0.11.0 `candlesticks.json`, each ticker's candles by
    `<ticker>|<minutes>`, `series.json`, each series' body, and
    `fee-changes.json`, each event's fee changes."""

    def __init__(self, directory: Path | None = None) -> None:
        root = directory or Path(str(resources.files("kalshi") / "synthetic"))
        self.held: dict[str, dict[str, Any]] = {
            name: json.loads((root / f"{name}.json").read_text(encoding="utf-8")) for name in _FILES
        }
        for name in _OPTIONAL:
            path = root / f"{name}.json"
            self.held[name] = json.loads(path.read_text(encoding="utf-8")) if path.is_file() else {}

    def __call__(self, url: str, headers: Mapping[str, str]) -> Response:
        asked = _asked(url)
        if asked is None:
            return _missing()
        call, ticker = asked
        if call == "candlesticks":
            return _found(self._candles(ticker))
        if call == "fee-changes":
            changes = self.held[call].get(ticker, [])
            return _found({"event_fee_changes": changes, "cursor": ""})
        body = self.held[call].get(ticker)
        return _found(body) if body is not None else _missing()

    def _candles(self, asked: str) -> dict[str, Any]:
        """The batch endpoint's answer: each ticker's candles of the period
        asked, those ending from its start to its end."""
        tickers, period, start, end = asked.split("|")
        markets = []
        for ticker in tickers.split(","):
            held = self.held["candlesticks"].get(f"{ticker}|{period}", [])
            within = [c for c in held if int(start) <= int(c["end_period_ts"]) <= int(end)]
            markets.append({"market_ticker": ticker, "candlesticks": within})
        return {"markets": markets}


class Recorded:
    """Answers from a developer's recorded raw records (`meridian.edge.RawStore`'s files under a
    `responses/` directory): the latest answer kept for each call and ticker,
    a 404 among them."""

    def __init__(self, directory: Path) -> None:
        self.latest: dict[tuple[str, str], tuple[int, int, str]] = {}
        for path in sorted(directory.rglob("*")):
            if path.suffix == ".json":
                records = [json.loads(path.read_text(encoding="utf-8"))]
            elif path.suffix == ".jsonl":
                records = [
                    json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()
                ]
            else:
                continue
            for record in records:
                status = int(record.get("status", 0))
                asked = _asked(str(record.get("request", {}).get("url", "")))
                if asked is None or status not in (200, 404):
                    continue
                at = int(record.get("received_at_ns", 0))
                held = self.latest.get(asked)
                if held is None or at >= held[0]:
                    self.latest[asked] = (at, status, str(record["body"]))

    def calls(self) -> set[tuple[str, str]]:
        """Each call and ticker the recording answers."""
        return set(self.latest)

    def __call__(self, url: str, headers: Mapping[str, str]) -> Response:
        asked = _asked(url)
        held = self.latest.get(asked) if asked else None
        if held is None:
            return _missing()
        return Response(held[1], dict(_HEADERS), held[2].encode("utf-8"))
