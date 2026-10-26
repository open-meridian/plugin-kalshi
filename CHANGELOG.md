# Changelog

## 0.11.0

On open-meridian 0.33.1, contract v28 (rulings 624, 625, 629, 630, 647 to
649; task `sdk-contract/venue-plugins-keep-outcome-stages-and-bars`), on
core v28's harness.

- **Bars** (624, 625): a third dataset, `bars` (`meridian.v1.Bar`; pull and
  push; New York's day, `America/New_York`; kept): each contract's hourly
  and daily bars from Kalshi's candlesticks (`/markets/candlesticks`, the
  batch endpoint, `period_interval` 60 and 1440) -- the YES contract's
  traded prices (`price.*_dollars`), the contracts traded (`volume_fp`), no
  volume-weighted price; a candle with no trade is no bar. Kept by the
  SDK's `Feed.keep_bars` every five minutes, first 30 days back.
  `BARS_DECLARED` in `tests/venue_cases.py`; `a-daily-bar` is presented. On
  the synthetic exchange one pass keeps 6 bars of the base contract: 4
  hours and 2 New York days.
- **Fees computed** (630): each contract's taker and maker coefficients from
  its series' `fee_type` and `fee_multiplier`, or its event's override in
  effect, with Kalshi's published formula -- round up(0.07 x C x P x (1-P))
  to the next cent, 0.07 times the multiplier; makers 0.0175 (combos 0.035)
  times it where the type has maker fees; `flat` not computed. The formula
  is the fee schedule's (kalshi.com/docs/kalshi-fee-schedule.pdf, effective
  Feb 5, 2026), read 2026-10-26 from the Internet Archive's copy of
  2026-06-12: the live address answered HTTP 429 behind a bot challenge.
  Connection's "Fees" row says how many contracts take their series' fee,
  an event's or none, each contract's a tap away and in `read_connection`'s
  `fees.markets`. The series and its event's fee changes are read with the
  event, at most once a day each (`/series/{ticker}`,
  `/events/fee_changes`).
- **The pins**: open-meridian 0.33.1 and plugin-python:0.33.1 by tag and
  digest (`sha256:75ec238c...d5f46bac`); core's runtime and harness stay at
  `8def82a` (chart 0.1.313); `meridian` stays 0.1.52 in check.yaml.

## 0.10.0

On open-meridian 0.33.0, contract v28 (meridian-design `plans/the-v28-build.md`;
task `sdk-contract/venue-plugins-keep-outcome-stages-and-bars`), on core
v28's harness.

- **The settlement timer** (the options sample's Resolution window, its
  question 1): a `determined` or `amended` outcome's
  `Outcome.challenge_ends_at_ns` is Kalshi's `settlement_timer_seconds`
  counted from when the answer first stating it arrived, set only where the
  read before it -- at most two minutes earlier, the SDK reading a contract
  past its close each minute -- stated another status, so the end is at
  most that late and never early; an amendment restarts it (docs.kalshi.com,
  "Market lifecycle"). Otherwise 0, "deadline not reported"
  (`KalshiMarket.timed`, `tests/test_timer.py`).
- **Fees** (571; task `sdk-contract/event-contract-fees-vary-by-market-category`):
  Connection's "Limits and use" gains a "Fees" row, and `read_connection` a
  `fees` record, saying Kalshi's fee schedule
  (kalshi.com/docs/kalshi-fee-schedule.pdf, and kalshi.com/fee-schedule)
  could not be read on 2026-10-26 -- HTTP 429 behind a bot challenge, as on
  2026-10-24 -- so no rate is stated or assumed, and what Kalshi's API
  states per series instead (`fee_type`, `fee_multiplier`, its category, an
  event's override; `fees.py`).
- **The suite's v28 cases**: `reports-its-feed-delay` is presented (518);
  `a-crossed-quote-is-recorded-invalid` on a synthetic contract whose book
  is crossed (`CROSSED`, a YES bid above the payout less the best NO bid);
  the option-chain, filings, duplicate and gap cases not presented, the
  SDK's list (602).
- **`meridian plugin migrate`** (to_0_33_0): e2e/reader.py's SubjectRefs
  handed to the SDK are `meridian.SubjectRef` (ruling 599).
- **The pins**: open-meridian 0.33.0 and plugin-python:0.33.0 by tag and
  digest (`sha256:c95f1a03...c0fe39c6`); core v28's runtime and harness at
  `8def82a` (chart 0.1.313) by digest; `meridian` stays 0.1.52 in
  check.yaml until 0.1.53 is released.
- The README's "not released" line is gone.

## 0.9.0

On open-meridian 0.32.2, contract v27 (meridian-design `plans/the-v27-build.md`,
§B and §G), on core v27's harness.

- **The events are the SDK's.** `__main__.Events`, the loop reading each
  served contract's event once first served and every ten minutes and
  reporting it on a change, is gone: `Feed.keep_events` (open-meridian
  0.32.0) does the same over `KalshiMarket.event`. `tests/test_events.py`
  holds the SDK's loop to what Kalshi's did.
- **Each range member's bounds with its event's report** (ruling 464). The
  SDK's `report_event` sends each member's floor, cap and unit
  (`member_bounds`) as Kalshi's `strike_type` states them; the new test
  holds them to the design's v27 row: one per range member, naming a member
  of the group, inclusive as stated, no unit (Kalshi states none).
- **No challenge deadline.** Contract v27's `Outcome.challenge_ends_at_ns`
  stays 0 ("deadline not reported"): Kalshi's public REST states the
  dispute window's length (`settlement_timer_seconds`) but no time of
  determination, and the field is the venue's statement, never the
  plugin's sum. Said in the README, AGENTS.md and docs/overview.md.
- **The suite's v27 cases** are named not presented through the SDK's
  `EVENT_CONTRACTS_NOT_PRESENTED`: the seven rates cases;
  `records-a-datasets-liveness` (Kalshi is polled each second, and no
  stream gives a heartbeat); `queries-the-lake-within-bounds`, about trades
  from v27 (it records none); and `reports-its-feed-delay`, about latency,
  with ruling 518's reason (core receives ReportLatency from contract v28,
  ruling 515).
- **The pins**: open-meridian 0.32.2 and plugin-python:0.32.2 by tag and
  digest (`sha256:2235d96d...54020b80`); core v27's runtime and harness at
  `a5da59a` (chart 0.1.310) by digest; `meridian` 0.1.52 in check.yaml.
  e2e-latest.yaml keeps the harness's hidden logs (`include-hidden-files`).
- Its `DatasetLicence` sets none of 0.32.2's five new fields: core v27
  refuses a registration carrying them until a core that accepts them is
  published. The terms page is unchanged.

## 0.8.1

On open-meridian 0.31.1: a range market's bounds on its contract (the gaps
spec's A4), and two small fixes.

- **Bounds on the contract.** `convert.contract` sets `Contract.floor` and
  `.cap` from the market's `strike_type`, `floor_strike` and `cap_strike`,
  which 0.8.0 read but held off it: open-meridian 0.31.1's contract map
  keeps a bound (its value as exact text, and whether it is inclusive) and
  reads it back. Kalshi states no unit for a strike, so `bound_unit` stays
  empty. A bound reaches no row in contract v26; its data path is contract
  v27's (ruling 464).
- **The SDK's check restored.** 0.31.1's
  `test_a_record_already_complete_is_not_resolved_again` holds ruling 312's
  ticker itself, so this plugin's override is gone.
- **e2e/record.py** keeps its raw records through `meridian.edge.RawStore`;
  it still imported `kalshi.raw`, which 0.7.0 removed, so recording for
  `make e2e-recorded` failed.
- **The pins**: open-meridian 0.31.1 and plugin-python:0.31.1 by tag and
  digest (`sha256:67781f14...a3535b39`); core v26's runtime and harness and
  `meridian` 0.1.49 as 0.8.0 set them.

## 0.8.0

On open-meridian 0.31.0, contract v26: Kalshi's events reported as groups
(meridian-design `spec/the-contract-gaps-v26-and-v27-close.md`, A1 to A9;
W3.29), on core v26's harness. One version for v26 (open question 234): it
carries 0.6.0 and 0.7.0, which never merged on their own.

- **Event groups.** For each contract it serves, the plugin reads the
  event Kalshi groups it in (`/events/{event_ticker}`, markets nested) and
  reports it through the SDK's `Feed.report_event`: its markets by ticker,
  its series, Kalshi's `mutually_exclusive`, and exhaustiveness not stated,
  never false, since Kalshi states none. Each event is read once its first
  contract is served and every ten minutes after, and reported again only
  where Kalshi states it otherwise; an event a member of which does not
  resolve is held back and read again (`__main__.Events`).
- **The data suite's v26 cases mapped**: `reports-an-event-group` on a
  synthetic event Kalshi states mutually exclusive (a day's high in ranges),
  `reports-a-flag-the-venue-does-not-state` on its ladder of "above" markets,
  `queries-the-lake-within-bounds` the SDK's producer
  (`tests/venue_cases.py`'s `EVENT` and `EVENT_PLACEHOLDERS`).
- **A range market's bounds** (A4) are read in `convert.py` from its
  `strike_type`, `floor_strike` and `cap_strike` (`greater` a floor not
  inclusive, `greater_or_equal` inclusive, `less` and `less_or_equal` a cap,
  `between` both inclusive), but not yet set on the contract:
  open-meridian 0.31.0's contract map cannot keep a bound and sends none.
  Kalshi states no unit for a strike, so `bound_unit` stays empty.
- **e2e on core v26's harness** (199): the custodian states Kalshi's
  ticker under its MIC beside its own symbol, as a broker reports the
  exchange's symbol, so the stand-in platform mints the platform's record
  by it; the stand-in holds Kalshi by its MIC, so rows name Kalshi's `VEN-`
  ID and no miss is counted; step 5a reads the contract's event group back.
  On a failure the run logs the instruments, the plugin's Datasets record
  and the lake's record, and e2e.yaml keeps the hidden `.e2e/` logs.
- **Tests**: `tests/test_events.py` (reported as stated, unchanged not
  reported again, held back while a member does not resolve), the
  conversion's events and bounds; the SDK check
  `test_a_record_already_complete_is_not_resolved_again` held to ruling
  312's ticker until open-meridian 0.31.1 corrects its own.
- **The pins**: open-meridian 0.31.0 and plugin-python:0.31.0 by tag and
  digest (`sha256:e041f83c...24cf5d2`); core v26's runtime and harness
  (17a13a2, merged as 648e25f) by digest; `meridian` 0.1.49, the first CLI
  carrying contract v26's suites.

## 0.7.0 (not released on its own: carried by 0.8.0)

On open-meridian 0.30.0, contract 25 unchanged: the data role's work is
the SDK's (sdk-contract/the-sdk-carries-each-roles-common-logic; ruling
202). It follows 0.6.0 (contract v25: the whole declaration and docs/),
which has not merged to main yet: this branch carries it.

- **The data role from the SDK's helpers.** `market.py`, `dgm.py`,
  `contracts.py` and `raw.py`, kept byte for byte with plugin-polymarket, are
  gone: the work is `meridian.roles.data.event_contracts.Feed` (prices,
  quotes and outcomes) over this venue's values and `ContractMap`, raw
  records `meridian.edge.RawStore`, and the pages the SDK's for an
  event-contract venue (`page.py` builds them; `templates/` gone),
  answering the kind's `ConnectionRead` and `DatasetsRead`.
  `e2e/reader.py` stays as this plugin's own e2e stand-in.
- **suite-same retired.** The copied tests (`test_suite`, `test_dgm`,
  `test_page`, `test_raw`, `conftest`) are one class,
  `tests/test_data_role.py`, running the SDK's `EventContractsChecks`
  against this plugin's conversion and the data suite by name; raw records
  are tested in the SDK. The Makefile's `suite-same`, `PAIR` and `SAME` are
  gone.
- **The pins**: open-meridian 0.30.0, as released on PyPI, and
  plugin-python:0.30.0 by tag and digest
  (`sha256:a238c6d9...3473ed6`) in the Dockerfile, which `make image` now
  builds on as an upload does; core v25's runtime and harness (abf028f) and
  `meridian` 0.1.46 as 0.6.0 set them.

Earlier versions are described in the git history.
