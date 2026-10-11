# plugin-kalshi

Kalshi's public market data for binary event contracts in an Open Meridian
deployment's lake: a `dgm` plugin. For each contract a deployment's readers
ask about, it records the last trade's price and the best bid and offer, per
contract in dollars, and the best bid and offer with their sizes as a quote,
every figure exactly as Kalshi stated it. No key: Kalshi's market data is
public.

It is the first half of the lake's second batch, with
[plugin-polymarket](https://github.com/open-meridian/plugin-polymarket):
the two pass one `dgm` suite unchanged between them (meridian-design
`plans/the-lake-prices-the-book.md`, row 20).

**Status.** 0.1.0, built on open-meridian 0.23.0 (contract v19) and proven
against core's v19 runtime and harness (core e149c69), pinned by digest. Not
released, uploaded or launched anywhere.

## What it does

One dataset, declared from code in its catalogue (`declaration.py`):

| Dataset | Data | Modes | Day | Default licence |
|---|---|---|---|---|
| `<instance>:live` | each contract's last trade, best bid and ask as prices; its best bid and offer with sizes as a quote | pull, stream | `Etc/UTC`, ending at 00:00 | served, not kept |

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
- **The venue** is resolved in the platform's venue master by Kalshi's MIC
  (`iso10383` `KLSH`), and each row names its `VEN-` ID. A deployment that
  does not hold it gets each row with the venue left empty and the code
  beside it as reported, and the miss reported, asked again the next day.

### What it does not serve

The SDK's `dgm` suite's cases about a kind of data this plugin never
publishes are marked not presented, with why, as contract v19 allows
(`tests/venue_cases.py`): daily closes and bars, trades, a currency's rate, a
stablecoin price and a security's price. Every other case passes.

## Settings

| Setting | What it does |
|---|---|
| Synthetic mode (`synthetic`) | A developer's setting, shown only on a development deployment: answer from the synthetic exchanges this plugin carries instead of calling Kalshi, or from a developer's recorded exchanges where its storage holds them (`recorded/`). |
| Raw responses' window (`responses_window_days`, `responses_past_window`) | The SDK's, for the plugin's one kind of raw record: how long Kalshi's answers stay in its storage (30 days by default), and whether a day past it is archived, kept or deleted. |

No secret: Kalshi's public market data needs no key.

## Its pages, under Manage

A `dgm` shows no market data: viewing prices is for the reading roles.

- **Connection**: where it answers from (Kalshi, or synthetic mode), the
  endpoint, what the plugin spends of Kalshi's limits (at most 5 requests a
  second, a 429 waited out), its calls, rate limits met and failures, the
  last error, and the venue master's ID it resolved.
- **Datasets**: its dataset; the contracts mapped for the subjects the lake
  asked for, and those not served with why; the cash its prices and payouts
  are in (the dollar, and the deployment's record for it) and what each
  contract pays; what Kalshi entitles it to (public data, no key); and the
  wants it heard, standing ones first, each with what it recorded and
  declined, under the kit's search.

Both fit one screen at 1440x900 and 390x844, rows one line each, the wants
paged by the kit's `om-pager`.

### Offered to agents

Each page is a read tool on the deployment's MCP surface, answering the record
the page shows: `read_connection` and `read_datasets`, at the plugin's admin
level. The plugin has no route that changes anything.

## Raw responses

Every answer Kalshi sends, an error as much as a book, is kept in the storage
the deployment grants the plugin before anything is read from it, with the
request that asked for it, its status and headers, and when it arrived
(`raw.py`); a live answer is a line of its day's file, added only when it
changed, and a row read from an unchanged answer names the line and time it
first arrived. Each row names its raw record (`RawRecordRef`). Kept in units
of a UTC day under `responses/`, moved past the window through the SDK.

## Proven on core's harness

    make e2e

runs the plugin in synthetic mode on core's plugin harness beside the e2e's
reader (`e2e/reader.py`, holding `custody` to name a custodian's records,
`reporting` to hear prices and `signal` to hear quotes): the catalogue
listed, nothing asked of Kalshi before a want, a custodian's contract read
and named, its prices and quote recorded in dollars -- the ask from the NO
side -- served to the reader and heard, a range market declined, both read
tools answering what the pages show, and `store lake` keeping no row
(`e2e/run.py` says each step).

    docker run --rm --entrypoint python -v "$PWD/e2e":/e2e:ro \
        -v "$PWD/recordings":/recordings kalshi:local /e2e/record.py TICKER ...
    make e2e-recorded RECORDED=recordings/<directory>

records Kalshi's real answers to its public reads for the tickers named,
with the plugin's own client and no key, into the git-ignored `recordings/`,
then runs the same replaying them, holding each row to its shape rather than
to the synthetic values.

## Working on it

    make ci-local        # every gate: lint, tests, plugin check, the image, e2e, the pair the same
    make test            # the tests, the SDK's dgm suite among them
    make preview         # preview/: each page on synthetic data, linking the kit
    make install-hooks   # git push runs ci-local first

`AGENTS.md` is for any coding agent working on it; `CLAUDE.md` leads Claude
Code there. The documentation for a deployment admin is in `docs/`.

## Licence

Apache-2.0. See `LICENSE` and `NOTICE`. Kalshi is a trademark of its owner;
this project is not affiliated with or endorsed by Kalshi.
