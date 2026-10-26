"""What this version declares beside its role (W8.1, W4.1; contract v19).

**Its catalogue** (spec/the-lake, "The catalogue"; the plan's Q21), declared
from code and read the same way at registration and by `meridian plugin
upload`:

- `live`: each contract's last trade price and best bid and offer as
  prices, and its best bid and offer with their sizes as a quote, at most
  once a second per subject, pulled for the latest or kept current for a
  standing want. Its day is the UTC day (`day_time_zone` `Etc/UTC`,
  `day_end_minute` 0): Kalshi trades around the clock and states no close.
- `outcomes` (contract v23): each contract's outcome as Kalshi determines
  it, a new version at each stage it states, recorded unasked (`push`) for
  each contract a subject the lake asked for is, a contract past its close
  read again each minute until its outcome is final. It names no business
  date; its day is declared as the live dataset's.
- `bars` (from 0.11.0; rulings 624, 625 and 629): each contract's hourly and
  daily bars, Kalshi's candlesticks of the YES contract's traded prices and
  the contracts traded, no volume-weighted price. Kept by the SDK's
  `Feed.keep_bars` for each contract served -- every closed hour and day,
  first read 30 days back -- recorded unasked (`push`), and a want of
  `bars` answered from Kalshi's history (`pull`). Its day is Kalshi's,
  New York's (`day_time_zone` `America/New_York`, `day_end_minute` 0): its
  daily candles end at New York's midnight.

**Its licence defaults** (the plan's row 20): `live` is served, not kept: the
lake hands each row to the readers waiting for it and keeps none. `outcomes`
is kept: an outcome is restated version by version and read back by the
version in force or as of a time, which a dataset not kept cannot answer
(a plugin's choice within contract v23, approved 2026-10-13). `bars` is
kept: a closed interval's bar does not change. No default claims anything
about Kalshi's terms, which the deployment admin settles with
whoever uses the deployment; the admin states the deployment's licence on
the Data sources page, which replaces it.

`venue_id` is empty: the venue master's ID for Kalshi is minted by the
platform, not known to the code a catalogue is declared from, so each row
names the venue by the ID it resolves at run time (the SDK's
`meridian.roles.data.event_contracts.Feed`), by Kalshi's MIC.

**Its storage**: one kind of raw record, Kalshi's responses as received,
kept a month by default (`KIND`, kept by the SDK's
`meridian.edge.RawStore`); the SDK declares the kind's two window settings.
**Its settings**: sample data, a developer's (synthetic.py). No secret:
Kalshi's public market data needs no key.
"""

import meridian
from meridian import DatasetDeclaration, DatasetLicence

VENDOR = "Kalshi"
SAMPLE_DATA = "sample_data"

#: Its one kind of raw record, Kalshi's responses as received: a month of
#: them by default, enough to re-convert a row a person questions. An admin
#: sets the window in Settings.
KIND = "responses"
LABEL = "Raw responses"
WINDOW_DAYS = 30

#: Its settings, in the data role's order (spec/plugin-pages-follow-their-role):
#: no environment and no credential -- Kalshi's public market data has one
#: environment and needs no key -- so only sample data, a developer's.
SETTINGS = [
    meridian.sample_data(
        description=(
            "Answer from built-in made-up Kalshi responses, or a developer's recorded ones, "
            "instead of calling Kalshi. Development deployments only."
        )
    ),
]

CATALOGUE = [
    DatasetDeclaration(
        key="live",
        vendor=VENDOR,
        data_types=["meridian.v1.Price", "meridian.v1.Quote"],
        modes=["pull", "stream"],
        cadence=1,
        history=0,
        licence_default=DatasetLicence(kept=False),
        day_time_zone="Etc/UTC",
        day_end_minute=0,
    ),
    DatasetDeclaration(
        key="outcomes",
        vendor=VENDOR,
        data_types=["meridian.v1.Outcome"],
        modes=["push"],
        cadence=60,
        history=0,
        licence_default=DatasetLicence(kept=True),
        day_time_zone="Etc/UTC",
        day_end_minute=0,
    ),
    DatasetDeclaration(
        key="bars",
        vendor=VENDOR,
        data_types=["meridian.v1.Bar"],
        modes=["pull", "push"],
        cadence=300,
        history=30,
        licence_default=DatasetLicence(kept=True),
        day_time_zone="America/New_York",
        day_end_minute=0,
    ),
]
#: The `bars` dataset's declaration, which says the day a daily bar is in.
BARS = CATALOGUE[2]
