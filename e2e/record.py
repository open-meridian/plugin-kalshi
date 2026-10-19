"""Record Kalshi's real answers for `make e2e-recorded`: the plugin's own client
asks Kalshi's public reads -- no key -- for each ticker named, and keeps every
answer as the plugin keeps its raw records, under a directory of its own.

Run in the plugin's image, which carries the package and the SDK, writing
into recordings/ (git-ignored: a recording is the developer's who made it,
never committed; the plan's Q11):

    make image
    docker run --rm --entrypoint python -v "$PWD/e2e":/e2e:ro \\
        -v "$PWD/recordings":/recordings kalshi:local /e2e/record.py TICKER [TICKER ...]
    make e2e-recorded RECORDED=recordings/<the directory it printed>

Each ticker's market, its book twice a second apart and its last trade are
asked; a ticker Kalshi knows nothing by is kept as its 404. Standard library
and the plugin only.
"""

import sys
import time
from datetime import UTC, datetime
from pathlib import Path

from meridian.edge import RawStore

from kalshi.venue import Kalshi, VenueError


def main(tickers):
    if not tickers:
        print("name at least one Kalshi ticker", file=sys.stderr)
        return 2
    stamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
    root = Path("/recordings") / stamp
    client = Kalshi(RawStore(root))
    for ticker in tickers:
        for ask in (client.market, client.orderbook, client.trades):
            try:
                ask(ticker)
            except VenueError as refused:
                print(f"{ticker}: {refused}", file=sys.stderr)
        time.sleep(1)
        try:
            client.orderbook(ticker)
        except VenueError as refused:
            print(f"{ticker}: {refused}", file=sys.stderr)
    print(f"recordings/{stamp}: {client.health.calls} answers kept")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
