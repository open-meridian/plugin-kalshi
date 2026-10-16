# Overview

The Kalshi plugin puts Kalshi's public market data for binary event
contracts into your deployment's lake, where the plugins that watch and
value your book read it. It needs no key: Kalshi's market data is public.

It is a data plugin: its first-use path, its two pages and its Summary figures are every data plugin's, described once on [Using a data plugin](https://open-meridian.dev/how-to/using-a-data-plugin/). These sections cover what is Kalshi's own.

## Its role

It holds one role, `data`: it records prices and quotes into the lake, with
Kalshi's markets named as your deployment's instruments, and keeps Kalshi's
answers in its own storage. It shows no prices itself: reading them is for
the reporting, portfolio, signal and other reading plugins.

## What it records

For each contract a reader asks about, now: the last trade's price and the
best bid and offer, per contract in dollars, and the best bid and offer with
their sizes as a quote, at most once a second for each contract while a
reader keeps asking.

It records what readers ask for, not the whole exchange: when a reader asks
for a price nothing has recorded, the lake asks the plugin, which asks Kalshi
for that one market and records it, or says why it cannot.

## How it names what it prices

Each instrument a reader asks about is one of your deployment's records. The
plugin reads it and looks for Kalshi's ticker on it (for example
`KXFED-27APR-T4.25`, as Kalshi's own symbol), or another source's symbol
that is a Kalshi ticker. It serves a market only where Kalshi states it as a
binary contract: one paying a fixed amount, one dollar, if the event
happens, and nothing if it does not.

Where the record lacks Kalshi's ticker, its class or its type, the plugin
offers them, with Kalshi's title for the market, so you can complete the
record on the Instruments page. If the record already states a payout that
is not Kalshi's (another amount, or another currency), the plugin does not
serve it.

## Prices are money, not probabilities

A price is what one contract costs in dollars: 0.43 means 43 cents for a
contract that pays one dollar. The market's implied probability (43%) is
that price over the payout, which a reading plugin may compute; the lake
stores only the price.

Kalshi's book holds bids on both sides of a contract. A bid for NO at 56
cents is an offer to sell YES at 44 cents, so the plugin records the
contract's ask as one dollar less the best NO bid.

## Outcomes

Once Kalshi determines a contract a reader asked about, the plugin records
its outcome: whether the contract pays its dollar, pays nothing, or pays
part of it, what one contract settles at, and Kalshi's own word for the
result (yes, no or scalar). Each stage Kalshi states -- determined,
disputed, amended, finalized -- is a new version of the same outcome, so
your readers see a disputed result as it changed, and the final one with
when Kalshi paid out. Outcomes are kept by default. Paying the holders of a
position is not the plugin's: it records what Kalshi determined.

## What it never makes up

- A figure is recorded exactly as Kalshi stated it, never rounded and never
  through a float.
- A side of the book with no order is left empty, never zero.
- Nothing is recorded for a day already past: Kalshi's public reads answer
  now.

## What it keeps

Kalshi's answers, as received, in the storage your deployment gives the
plugin, for 30 days by default, each price naming the answer it came from.
Past that window, a day's answers are archived, kept or deleted as you set
it. Its live dataset's default licence is served, not kept: the lake keeps
none of its prices unless your deployment's licence says otherwise. Its
outcomes dataset is kept by default.
