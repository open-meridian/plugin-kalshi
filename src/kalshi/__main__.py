"""Kalshi's public market data as an Open Meridian data plugin.

It runs its data role class, `Lake` -- the SDK's work for an event-contract
venue (`meridian.roles.data.event_contracts.Feed`, over Kalshi's conversion
in convert.py) -- on the sidecar it is launched beside, declaring its
catalogue, its storage and its settings (declaration.py) and its pages
(page.py), which `meridian.run` serves. It hears what the lake wants of it,
names each subject as one of Kalshi's contracts and records it, and keeps
each standing want current until stopped. Everything goes through the
sidecar; nothing but Kalshi's public REST is called, and with sample data
not even that (synthetic.py). Nothing is asked of Kalshi until the lake
wants something of it, and then only the contracts wanted.

From 0.8.0 (contract v26, W3.29) it reports, for each contract it serves,
the event Kalshi groups it in: its markets, and whether Kalshi states them
mutually exclusive (exhaustive never stated), each event when first read and
again whenever Kalshi states it otherwise, so the platform matches or mints
the group and keeps a new version when its members or flags change. From
0.9.0 (contract v27) that is the SDK's `Feed.keep_events`, and each range
member's floor and cap go with the report (ruling 464), offered for its
record.

From 0.12.0 (open-meridian 0.35, each role one class: rulings 1004, 1005,
1009 to 1023) the role's work is `Lake`, registered with `meridian.run`,
which delivers the settings, serves the pages, sets the figures on each
heartbeat and starts `Lake.run` again after a backoff should it fail -- the
work the plugin wired by hand before.

It holds nothing it cannot lose: Kalshi's raw responses and the contract map
are kept in the storage the deployment grants it (decisions/028), and a
restart reads the map back and hears again what the lake wants.
"""

from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any

import meridian
from meridian.edge import RawStore, storage_root
from meridian.roles.data.event_contracts import ContractMap, Feed

from .convert import KalshiMarket
from .declaration import DECLARATION, PORT
from .declared import BARS, KIND, SAMPLE_DATA, WINDOW_DAYS
from .page import figures_now, hold, pages
from .synthetic import Recorded, Synthetic
from .venue import Kalshi

log = logging.getLogger("kalshi")

#: Where a developer's recorded exchanges are replayed from, under the
#: plugin's storage, when `make e2e-recorded` mounts them there.
RECORDED = "recorded"
#: How often its datasets' licences are read again and whether Kalshi
#: answers is said on its health.
HEALTH_EVERY_SECONDS = 60


def market(store: RawStore, synthetic: bool) -> KalshiMarket:
    """Kalshi itself, or with sample data its answers from files: a
    developer's recorded exchanges where storage holds them, else this
    package's synthetic ones."""
    if not synthetic:
        return KalshiMarket(Kalshi(store), "live")
    recorded = store.root / RECORDED
    if recorded.is_dir():
        return KalshiMarket(Kalshi(store, transport=Recorded(recorded)), "recorded")
    return KalshiMarket(Kalshi(store, transport=Synthetic()), "synthetic")


def contract_map(store: RawStore, mode: str) -> ContractMap:
    held = ContractMap(store.root / f"contracts-{mode}.json")
    held.load()
    return held


@dataclass
class Lake(Feed):
    """The data role's class: the SDK's event-contract feed over Kalshi's
    conversion, which hears what the lake wants and keeps its standing wants
    current."""

    store: RawStore | None = None

    async def on_settings(self, delivered: Any) -> None:
        """Each delivery of the settings: the source switched where synthetic
        mode changed, its own contract map read back from storage, and each
        day's raw responses past their window moved. Whatever it answers
        from, nothing is asked of the venue, and nothing resolved, until the
        lake wants something of it."""
        values = delivered.values
        log.info("settings delivered: sample data %s", values.get(SAMPLE_DATA))
        synthetic = values.get(SAMPLE_DATA) is True
        if synthetic != (self.market.session.mode != "live") and self.store is not None:
            chosen = market(self.store, synthetic)
            self.use(chosen, contract_map(self.store, chosen.session.mode))
            log.info("answering from %s", chosen.session.mode)
        if self.store is not None:
            window = values.get(f"{KIND}_window_days")
            past = values.get(f"{KIND}_past_window")
            await self.store.tend(
                self.plugin,
                window if isinstance(window, int) else WINDOW_DAYS,
                past if isinstance(past, str) else "kept",
                datetime.now(UTC).date(),
            )

    async def run(self) -> None:
        """The SDK's feed's work -- each standing want kept current, the events
        of the contracts served reported as Kalshi states them, and each
        contract served's hourly and daily bars kept from Kalshi's
        candlesticks, the venue asked for only once a contract is served
        (open-meridian 0.35.1) -- and its health said each minute."""
        await asyncio.gather(super().run(), self._health())

    async def _health(self) -> None:
        """Each minute: its datasets' licences read again (contract v20), and
        on its health whether Kalshi answers."""
        while True:
            try:
                await self.read_licences()
            except meridian.MeridianError as failed:
                log.warning("licences not read: %s", failed)
            health = self.market.session.health
            healthy = health.last_ok_ns >= health.last_failed_ns
            detail = f"{self.market.name} answers" if healthy else health.last_error
            try:
                await self.plugin.report(healthy=healthy, detail=detail[:200])
            except (meridian.MeridianError, ValueError) as failed:
                log.warning("health not reported: %s", failed)
            await asyncio.sleep(HEALTH_EVERY_SECONDS)


def main() -> None:
    logging.basicConfig(
        level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s"
    )
    store = RawStore(storage_root(), KIND)
    chosen = market(store, synthetic=False)
    lake = Lake(chosen, contract_map(store, chosen.session.mode), store=store, bars_declared=BARS)
    hold(lake)
    # The version's whole declaration (declaration.py): its settings, its
    # pages with the levels each serves and their tools, and its
    # documentation. A version registers exactly what it was uploaded with
    # (contract v25).
    meridian.run(
        declaration=DECLARATION,
        roles=[lake],
        pages=pages,
        port=PORT,
        on_settings=lake.on_settings,
        figures=figures_now,
    )


if __name__ == "__main__":
    main()
