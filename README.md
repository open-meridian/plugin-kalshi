# plugin-kalshi

Kalshi's public market data for binary event contracts in an Open Meridian
deployment's lake: a data plugin. For each contract a deployment's readers
ask about, it records the last trade's price and the best bid and offer, per
contract in dollars, and the best bid and offer with their sizes as a quote,
every figure exactly as Kalshi stated it; and, from contract v23, each such
contract's outcome once Kalshi determines it; and, from 0.11.0, each
contract's hourly and daily bars from Kalshi's candlesticks. No key:
Kalshi's market data is public.

It is one of the lake's second batch, with
[plugin-polymarket](https://github.com/open-meridian/plugin-polymarket): each runs the SDK's
data suite and its checks for an event-contract venue unchanged against its own conversion
(meridian-design `plans/the-lake-prices-the-book.md`, row 20); what the two do alike is
the SDK's (`meridian.roles.data.event_contracts`, open-meridian 0.33.1), never copied
between them.

**Status.** 0.11.0, built on open-meridian 0.33.1 (contract v28: each contract's hourly and daily bars from Kalshi's candlesticks, each contract's fee computed from its series' fee type and multiplier with Kalshi's published formula, a determination's settlement timer kept as its challenge window's end, its feed delay reported, a crossed quote recorded invalid at the edge; contract v27: each range member's bounds sent with its event's report, the events kept by the SDK's `Feed.keep_events`; contract v26: each contract's event reported as a group, a range market's bounds on its contract; contract v25's whole declaration and docs/, which a deployment shows on its Documentation tab; its work the SDK's role helpers), holding the
role `data`, and proven against the core it pins, by digest.

## What it does

Three datasets, declared from code in its catalogue (`declaration.py`):

| Dataset | Data | Modes | Day | Default licence |
|---|---|---|---|---|
| `<instance>:live` | each contract's last trade, best bid and ask as prices; its best bid and offer with sizes as a quote | pull, stream | `Etc/UTC`, ending at 00:00 | served, not kept |
| `<instance>:outcomes` | each contract's outcome, a new version at each stage Kalshi states (contract v23) | push | `Etc/UTC`, ending at 00:00 (an outcome names no business date) | kept |
| `<instance>:bars` | from 0.11.0, each contract's hourly and daily bars, Kalshi's candlesticks of its traded prices, no volume-weighted price | pull, push | `America/New_York`, ending at 00:00 | kept |

- **Per subject wanted, never the whole venue.** A reader reads a price or
  quote nothing has recorded; the lake asks this plugin (a want). The plugin
  reads the subject's record (W3.6) and names the Kalshi market it is by its
  identifiers: Kalshi's ticker (`symbol` at `kalshi`), else another source's
  symbol that Kalshi answers as one of its markets (never for a record that
  is a security, or a type other than a binary event contract). It asks
  Kalshi for that market alone; Kalshi's market list is never read, and no
  record is minted for a market no reader asked about.
- **Binary event contracts.** A market is served only where Kalshi states it
  binary (`market_type`), and only where its record states no other payout
  than Kalshi's. Where the record lacks Kalshi's ticker, or its class or
  type, the ticker is reported beside the identifier it matched, with
  `event_contract`, `binary_event_contract` and Kalshi's title offered, so a
  person completing the record on the Instruments page has them.
- **One contract, two sides.** Kalshi's book holds resting bids on its YES
  side and its NO side; a NO bid at p is an offer to sell YES at the payout
  less p. So the contract's bid is its best YES bid and its ask the payout
  less its best NO bid, with that bid's size: exact by the contract's
  definition, the raw book kept beside it.
- **Money per contract, in dollars.** A price is what one contract costs,
  `Money(0.43, "USD")`, never a probability: the implied probability is the
  price over the payout, a reader's computation. Kalshi's prices are dollars
  as text; an older answer's whole cents are moved two places at the edge,
  never through a float. A contract's payout, Kalshi's
  `notional_value_dollars`, is one dollar, and a price outside nothing to the
  payout is left unrecorded and counted.
- **Wants**, each recorded against or declined per subject with why:
  `not_covered` (not one of Kalshi's binary contracts), `beyond_history` (a
  day or range already past: Kalshi's public reads answer now),
  `source_silent` (Kalshi states nothing for it). A standing want keeps its
  subjects current, at most once a second, until the lake withdraws it.
- **Served, not kept**, by default: the lake hands each row to the readers
  waiting for it and keeps none. The deployment admin states the
  deployment's own licence on the Data sources page, which replaces the
  default; the default claims nothing about Kalshi's terms, which are for
  the deployment admin and whoever uses the deployment to settle.
- **Outcomes** (contract v23; meridian-design `plans/the-lake-prices-the-book.md`,
  "vL1c"). For each contract a reader asked about, the plugin records its
  outcome, unasked, once Kalshi determines it: from the contract's own side
  -- it pays its full payout, pays nothing, or pays part -- with what one
  contract settles at in dollars (Kalshi's `settlement_value_dollars`, or
  the payout for `yes` and nothing for `no` where Kalshi states none), and
  Kalshi's word, its `result` (`yes`, `no`, `scalar`), kept as reported.
  Kalshi's statuses are its stages: `determined` determined, `disputed`
  disputed, `amended` determined again, `finalized` final, with its
  payout time, `settlement_ts`. One row key per contract
  (`<ticker>:outcome`), each change a new version, nothing sent while
  Kalshi's answer is unchanged. Kalshi states no time of determination, so
  an outcome is valid from when the answer first stating it arrived. A
  contract past its close is read again each minute until its final stage
  is recorded. Kept by default, so a reader reads the version in force or
  as of a time; paying holders is servicing's, not the lake's. **The
  settlement timer** (from 0.10.0; `Outcome.challenge_ends_at_ns`, the
  sample's Resolution window): Kalshi runs a determination's dispute window
  for `settlement_timer_seconds` and restarts it on an amendment
  (docs.kalshi.com, "Market lifecycle"), stating its length but not when it
  began. So its end is the timer counted from when the answer first stating
  the determination arrived, set only where the plugin's read before it,
  at most two minutes earlier, stated none: at most that late, never early.
  A determination first read without that read before it -- after a
  restart, or a contract first asked for once determined -- carries none
  (0, "deadline not reported").
- **Events** (contract v26; meridian-design
  `spec/the-contract-gaps-v26-and-v27-close.md`, A1 to A9; W3.29). For each
  contract it serves, the plugin reads the event Kalshi groups it in
  (`/events/{event_ticker}`, its markets nested) and reports it
  (`ReportEventGroup`, the SDK's `Feed.report_event`): its markets, each
  named as the deployment's record by its ticker, its series
  (`series_ticker`), and Kalshi's `mutually_exclusive` -- true only where at
  most one market can resolve YES. Kalshi never states whether an event's
  markets are exhaustive, so that flag is reported not stated, never false.
  The platform matches or mints the group (`EVG-`), the deployment keeping
  its own `LCL-` group meanwhile. Each event is read once its first contract
  is served and again every ten minutes, and reported again only where
  Kalshi states it otherwise, which makes a new version; an event a member
  of which does not resolve is held back and read again. From 0.9.0 that
  loop is the SDK's (`Feed.keep_events`, open-meridian 0.32.0), over
  Kalshi's `event(ref)`.
- **A range market's bounds** (contract v26, A4) are on its contract:
  `floor_strike` and `cap_strike` as its `strike_type` reads them --
  `greater` a floor not inclusive, `greater_or_equal` one inclusive, `less`
  and `less_or_equal` a cap the same way, an open tail one bound only,
  `between` both inclusive -- kept in the contract map with the rest.
  Kalshi states no unit for a strike, so `bound_unit` is left empty. From
  contract v27 (ruling 464) each range member's floor, cap and unit go with
  its event's report (`ReportEventGroupRequest.member_bounds`), which the
  member's instrument record takes as values offered; a person's value wins.
- **Bars** (from 0.11.0; rulings 624 and 625). For each contract it
  serves, the plugin keeps hourly and daily bars from Kalshi's candlesticks
  (`/markets/candlesticks`, the batch endpoint, one ticker at a time;
  `period_interval` 60 or 1440): open, high, low and close the YES
  contract's traded prices (`price.open_dollars` and the rest, never the
  bid's or ask's), volume the contracts traded (`volume_fp`). A candle
  stating no traded price -- no trade in it -- is no bar. Kalshi's day ends
  at New York's midnight (its daily candles end 04:00 UTC in daylight time,
  05:00 in standard), so the `bars` dataset declares New York's day and a
  daily bar is dated on it. `mean_dollars` is a mean of the traded prices,
  not stated as volume-weighted, so no volume-weighted price is kept. The
  SDK's `Feed.keep_bars` (open-meridian 0.33.1) runs it: every five
  minutes each closed hour and day since the last kept, first 30 days back,
  recorded unasked; a want of `bars` is answered from Kalshi's history.
- **Fees** (from 0.11.0; ruling 630). Each contract's fee is computed from
  its series' `fee_type` and `fee_multiplier` (`/series/{ticker}`), or its
  event's override in effect (`/events/fee_changes`), read with the event
  it reports and again each day, with Kalshi's published formula: a taker
  pays round up(0.07 x C x P x (1-P)) to the next cent, 0.07 times the
  multiplier; a maker, where the type has maker fees, 0.0175 (0.035 for
  combos) times it (`fees.py`). The schedule
  (kalshi.com/docs/kalshi-fee-schedule.pdf, effective Feb 5, 2026) answered
  HTTP 429 behind a bot challenge on 2026-10-26, so it was read from the
  Internet Archive's copy of 2026-06-12. `flat` is not computed: the
  schedule read states no flat table. Read 2026-10-26, the S&P 500 and
  Nasdaq-100 series state `quadratic` at 1 where that schedule charges
  them 0.035: the API's statement, current, is the one used.
- **The venue** is resolved in the platform's venue master by Kalshi's MIC
  (`iso10383` `KLSH`), and each row names its `VEN-` ID. A deployment that
  does not hold it gets each row with the venue left empty and the code
  beside it as reported, and the miss reported, asked again the next day.

### What it does not serve

The SDK's data suite's cases about a kind of data this plugin never
publishes are marked not presented, with why, as contracts v19 and v20
allow (`tests/venue_cases.py`): daily closes, trades, a currency's rate, a
stablecoin price and a security's price. From 0.11.0 `a-daily-bar` passes
on the synthetic contract's candlesticks of New York's day before. It records no trades, so a restart
leaves no gap of trades to read back (`a-restarts-gap-backfilled`, contract
v20, not presented): its live dataset is read again when it is next wanted.
Contract v22's two calendar cases are not presented either: it reads no
settlement calendar, and an event contract settles on its outcome, so it
never computes a settlement date. Contract v23's three outcome cases are
mapped: an outcome recorded, a disputed outcome restated, a partial payout.
Contract v26's are mapped too: `reports-an-event-group` on an event Kalshi
states mutually exclusive, `reports-a-flag-the-venue-does-not-state` on one
it states is not (exhaustiveness, which Kalshi never states, reported not
stated); `hears-and-reads-an-event-group` is answered by the SDK.
Contract v27's cases an event-contract venue never presents are the SDK's
list (`EVENT_CONTRACTS_NOT_PRESENTED`): the seven rates cases (it publishes
no rates); `records-a-datasets-liveness` (Kalshi is polled over REST each
second, and no stream gives a heartbeat to record); and
`queries-the-lake-within-bounds`, about trades from v27 (it records none).
Contract v28's are the SDK's list too: the option-chain and filings cases
(it lists no chain and publishes no filing), and
`a-duplicate-is-recorded-suspicious` and `rows-after-a-gap-are-suspicious`
(its quotes are polled; no message is numbered).
`a-crossed-quote-is-recorded-invalid` passes on a synthetic contract whose
book is crossed, and `reports-its-feed-delay` (required from contract v28,
ruling 518) on a standing want kept current, its rows' age at the edge.
Every other case passes, `reads-its-datasets-licences` among them: it reads
which of its datasets a deployment admin has licensed, on start and each
minute.

## Settings

| Setting | What it does |
|---|---|
| Sample data (`sample_data`) | A developer's setting, shown only on a development deployment: answer from the synthetic exchanges this plugin carries instead of calling Kalshi, or from a developer's recorded exchanges where its storage holds them (`recorded/`). |
| Raw responses' window (`responses_window_days`, `responses_past_window`) | The SDK's, for the plugin's one kind of raw record: how long Kalshi's answers stay in its storage (30 days by default), and whether a day past it is archived, kept or deleted. |

No secret: Kalshi's public market data needs no key.

## Its pages, under Manage

The data role's two pages (meridian-design
`spec/plugin-pages-follow-their-role.md`), the same sections, rows, labels
and "not set up yet" states as every data plugin's, drawn from the SDK's
role templates (`meridian.roles.data`); Kalshi's nuance only at their
extension points. A data plugin shows no market data: viewing prices is for
the reading roles.

- **Connection**: "Key" -- the mode (Live, or Sample data), "No key needed",
  what Kalshi entitles it to (public data: a contract read only for a
  subject the lake asked for) and, the role's row for a source of one venue,
  the venue master's ID it resolved; "Limits and use" -- what Kalshi allows
  and what the plugin spends of it, its calls and the rate-limited ones
  waited out, the last call and the last error, and "Fees": from 0.11.0
  (ruling 630) "Per market: n by series, n by event, n none" and the
  formula's taker/maker coefficients by fee type, each contract's computed
  coefficients and what Kalshi stated a tap away and in `read_connection`'s
  `fees.markets` (`code`, `taker`, `maker`, `source`
  `series`/`event`/`none`, `said`), with the formula, its source and the
  day it was read (`fees.py`); "Stream" -- "Does not
  stream": it reads a contract when it is wanted, at most once a second.
- **Datasets**: "Served" -- each dataset (`live`, `outcomes`, from 0.11.0 `bars`), its data, how
  its rows arrive, its day, its default terms and whether a deployment admin
  has licensed it
  ("Licensed" or "Not licensed yet", read from the deployment from contract
  v20), what it recorded and declined and when it last recorded, each
  dataset's own; "Wants" --
  the wants it heard and the standing wants it keeps current, searched and
  paged by the kit's `om-pager`; "Subjects" -- whether the deployment lets
  it read an instrument's record; then a section under Kalshi's name: the
  contracts mapped for the subjects the lake asked for and those not served
  with why, the cash its prices and payouts are in (the dollar, and the deployment's record for it) and what each
  contract pays, and how its YES and NO sides make one contract's quote: the best YES bid, and an ask of the
  payout less the best NO bid. Before the lake has asked anything it says the
  next step: "No wants yet", a deployment admin licensing its dataset on
  Data sources.

Its Summary carries the data role's figures, in the role's order:
Connection, Entitled at the vendor, Stream ("Does not stream") and Last
recorded. Both pages fit one screen at 1440x900 and 390x844, rows one line
each.

### Offered to agents

Each page is a read tool on the deployment's MCP surface, answering the record
the page shows: `read_connection` and `read_datasets`, at the plugin's admin
level. The plugin has no route that changes anything.

## Raw responses

Every answer Kalshi sends, an error as much as a book, is kept in the storage
the deployment grants the plugin before anything is read from it, with the
request that asked for it, its status and headers, and when it arrived
(`meridian.edge.RawStore`); a live answer is a line of its day's file, added only when it
changed, and a row read from an unchanged answer names the line and time it
first arrived. Each row names its raw record (`RawRecordRef`). Kept in units
of a UTC day under `responses/`, moved past the window through the SDK.

## Proven on core's harness

    make e2e

runs the plugin with sample data on core's plugin harness beside the e2e's
reader (`e2e/reader.py`, holding `custody` to name a custodian's records,
`reporting` to hear prices and `signal` to hear quotes): the catalogue
listed, nothing asked of Kalshi before a want, a custodian's contract --
stated by its own symbol and Kalshi's ticker, which the stand-in platform
mints the platform's record by (contract v26) -- read and named, its prices and quote recorded in dollars -- the ask from the NO
side -- served to the reader and heard, its event reported and read back
as a group, a range market declined, a
determined market's outcome recorded, kept, heard and read back, both read
tools answering what the pages show, and `store lake` keeping no row of the
live dataset and the outcome's one (`e2e/run.py` says each step).

    docker run --rm --entrypoint python -v "$PWD/e2e":/e2e:ro \
        -v "$PWD/recordings":/recordings kalshi:local /e2e/record.py TICKER ...
    make e2e-recorded RECORDED=recordings/<directory>

records Kalshi's real answers to its public reads for the tickers named,
with the plugin's own client and no key, into the git-ignored `recordings/`,
then runs the same replaying them, holding each row to its shape rather than
to the synthetic values.

## Working on it

    make ci-local        # every gate: lint, tests, plugin check, the image, e2e, the pair the same
    make test            # the tests, the SDK's data suite among them
    make preview         # preview/: each page on synthetic data, linking the kit
    make install-hooks   # git push runs ci-local first

`AGENTS.md` is for any coding agent working on it; `CLAUDE.md` leads Claude
Code there. The documentation for a deployment admin is in `docs/`.

## Licence

Apache-2.0. See `LICENSE` and `NOTICE`. Kalshi is a trademark of its owner;
this project is not affiliated with or endorsed by Kalshi.
