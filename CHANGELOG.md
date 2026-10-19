# Changelog

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
- **e2e on core v26's harness** (199): the stand-in platform holds Kalshi
  by its MIC and mints its contracts by ticker, so rows name Kalshi's
  `VEN-` ID and no miss is counted; step 5a reads the contract's event
  group back by the contract.
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
