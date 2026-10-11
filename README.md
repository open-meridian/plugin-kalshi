# plugin-kalshi

Kalshi's public market data for binary event contracts in an Open Meridian
deployment's lake: a data plugin. For each contract a deployment's readers
ask about, it records the last trade's price and the best bid and offer, per
contract in dollars, and the best bid and offer with their sizes as a quote,
every figure exactly as Kalshi stated it. No key: Kalshi's market data is
public.

It is the first half of the lake's second batch, with
[plugin-polymarket](https://github.com/open-meridian/plugin-polymarket):
the two pass one data suite unchanged between them (meridian-design
`plans/the-lake-prices-the-book.md`, row 20).

**Status.** 0.2.0, built on open-meridian 0.24.0 (contract v20), holding the
role `data`, and proven against the core it pins, by digest. Not
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

The SDK's data suite's cases about a kind of data this plugin never
publishes are marked not presented, with why, as contracts v19 and v20
allow (`tests/venue_cases.py`): daily closes and bars, trades, a currency's rate, a
stablecoin price and a security's price. It records no trades, so a restart
leaves no gap of trades to read back (`a-restarts-gap-backfilled`, contract
v20, not presented): its live dataset is read again when it is next wanted.
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
  waited out, the last call and the last error; "Stream" -- "Does not
  stream": it reads a contract when it is wanted, at most once a second.
- **Datasets**: "Served" -- its dataset, its data, how its rows arrive, its
  day, its default terms and whether a deployment admin has licensed it
  ("Licensed" or "Not licensed yet", read from the deployment from contract
  v20), what it recorded and declined and when it last recorded; "Wants" --
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
(`raw.py`); a live answer is a line of its day's file, added only when it
changed, and a row read from an unchanged answer names the line and time it
first arrived. Each row names its raw record (`RawRecordRef`). Kept in units
of a UTC day under `responses/`, moved past the window through the SDK.

## Proven on core's harness

    make e2e

runs the plugin with sample data on core's plugin harness beside the e2e's
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
    make test            # the tests, the SDK's data suite among them
    make preview         # preview/: each page on synthetic data, linking the kit
    make install-hooks   # git push runs ci-local first

`AGENTS.md` is for any coding agent working on it; `CLAUDE.md` leads Claude
Code there. The documentation for a deployment admin is in `docs/`.

## Licence

Apache-2.0. See `LICENSE` and `NOTICE`. Kalshi is a trademark of its owner;
this project is not affiliated with or endorsed by Kalshi.
