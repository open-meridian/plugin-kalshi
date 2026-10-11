"""The pages as a deployment admin would see them, on synthetic data, each
printed as one HTML file: for looking at them without a deployment.

    python -m kalshi.preview connection > preview/connection.html
    python -m kalshi.preview datasets > preview/datasets.html
    python -m kalshi.preview datasets-empty > preview/datasets-empty.html

The page links the kit where the dashboard serves it, /.meridian/ui/<version>/,
so serve it beside the kit to see it styled (meridian-ui's `make serve`);
opened on its own it is the page without the kit, unstyled, which works too.

There is no sidecar here: the SDK's `Recorder` answers as one would, the
deployment holding two records of Kalshi's synthetic contracts (one by
Kalshi's ticker, one by a custodian's symbol) and one of a range market
Kalshi does not state as binary, the venue answers from the synthetic
exchanges this package carries, and the lake asks for the latest of each
many times and keeps two current, as a reader would make it, so the
Datasets page has wants to page through and search (the kit's search, in
the browser). A deployment admin has licensed its live dataset (contract
v20). `datasets-empty` is the page of a plugin just started, before the
lake has asked anything: its next step, as a deployment admin sees it.
"""

from __future__ import annotations

import asyncio
import sys
import tempfile
from collections.abc import Callable
from pathlib import Path
from typing import Any

from meridian.plugin.v1 import operations_pb2 as ops
from meridian.suites import Recorder
from meridian.testing import PageClient

from .contracts import ContractMap
from .convert import KalshiMarket
from .dgm import Dgm
from .page import hold, pages
from .raw import RawStore
from .synthetic import Synthetic
from .venue import Kalshi

#: The preview's clock: 2026-10-10 12:00 UTC.
NOW_NS = 1_791_633_600 * 1_000_000_000

#: The deployment's records the lake asks about.
RECORDS = {
    "LCL-kalshi-t400": [
        ops.Identifier(scheme="symbol", value="KXSYNTH-26DEC-T4.00", source="kalshi")
    ],
    "LCL-custodian-t450": [
        ops.Identifier(scheme="symbol", value="KXSYNTH-26DEC-T4.50", source="custodian")
    ],
    "LCL-custodian-range": [
        ops.Identifier(scheme="symbol", value="KXSYNTHRANGE-26DEC", source="custodian")
    ],
}


def _record(params: Any) -> Any:
    held = RECORDS.get(params.instrument_id)
    record = ops.InstrumentRecord(instrument_id=params.instrument_id, identifiers=held or [])
    return ops.ResolveInstrumentResult(found=held is not None, instrument=record)


def _resolved(params: Any) -> Any:
    for instrument_id, held in RECORDS.items():
        if any(i in held for i in params.identifiers):
            return ops.ResolveIdentifierResult(found=True, instrument_id=instrument_id)
    return ops.ResolveIdentifierResult(found=True, instrument_id="LCL-usd")


def _delivering(want: ops.ObservationsWantedEvent) -> Callable[[Any], Any]:
    return lambda _: want


async def _worked() -> Dgm:
    lake = Recorder("kalshi")
    lake.answer("ResolveIdentifier", _resolved)
    lake.answer("ResolveInstrument", _record)
    store = RawStore(Path(tempfile.mkdtemp(prefix="kalshi-preview-")))
    client = Kalshi(store, transport=Synthetic(), clock_ns=lambda: NOW_NS)
    dgm = Dgm(lake, KalshiMarket(client, "synthetic"), ContractMap(), clock_ns=lambda: NOW_NS)
    subjects = list(RECORDS)
    for n in range(30):
        want = ops.ObservationsWantedEvent(
            want_id=f"WNT-{n:04d}",
            dataset="kalshi:live",
            data_type="meridian.v1.Price" if n % 2 else "meridian.v1.Quote",
            subjects=[ops.SubjectRef(entity_id=subjects[n % 3])],
        )
        lake.answer("ObservationsWanted", _delivering(want))
        await lake.receive(observations_wanted=dgm.on_want)
    for n, subject in enumerate(subjects[:2]):
        want = ops.ObservationsWantedEvent(
            want_id=f"WNT-L{n}",
            dataset="kalshi:live",
            data_type="meridian.v1.Quote",
            subjects=[ops.SubjectRef(entity_id=subject)],
            standing=True,
        )
        lake.answer("ObservationsWanted", _delivering(want))
        await lake.receive(observations_wanted=dgm.on_want)
    dgm.licensed = frozenset({dgm.dataset("live")})
    return dgm


async def _fresh() -> Dgm:
    """The plugin just started: nothing asked, nothing read of the venue."""
    lake = Recorder("kalshi")
    store = RawStore(Path(tempfile.mkdtemp(prefix="kalshi-preview-")))
    client = Kalshi(store, transport=Synthetic(), clock_ns=lambda: NOW_NS)
    return Dgm(lake, KalshiMarket(client, "synthetic"), ContractMap(), clock_ns=lambda: NOW_NS)


def main(argv: list[str]) -> int:
    page = argv[0] if argv else "connection"
    paths = {"connection": "/", "datasets": "/datasets", "datasets-empty": "/datasets"}
    if page not in paths:
        print(f"no page {page!r}: connection, datasets or datasets-empty", file=sys.stderr)
        return 2
    hold(asyncio.run(_fresh() if page == "datasets-empty" else _worked()))
    answered = PageClient(pages, deployment_admin=True).get(paths[page], "admin")
    sys.stdout.write(answered.text)
    return 0 if answered.status == 200 else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
