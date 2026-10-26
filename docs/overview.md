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

A determined result may be disputed while Kalshi's settlement timer runs,
and an amended one starts it again. Kalshi states how long the timer runs
but not when it started, so the plugin counts it from when it first read the
determination, and only where it read the contract a minute or so before
and found it not yet determined: the deadline your pages show is then at
most that late, never early. Where it has no such read -- after a restart,
or for a contract first asked about once determined -- your pages show
"deadline not reported".

## Fees

Connection's "Fees" row shows the fee for each contract the plugin serves,
computed from what Kalshi states for its series -- which fee formula applies
and its multiplier -- or for its event where it overrides them, with
Kalshi's published formula: a taker pays 0.07 x contracts x price x (1 -
price) times the multiplier, rounded up to the next cent; a maker, where the
series has maker fees, 0.0175 (0.035 for combos) times it. Kalshi's schedule
page refused automated reads when this version was made, so the formula was
read from an archived copy of it (effective Feb 5, 2026), with its source
and the day it was read on the row. A formula Kalshi names that the schedule
does not state (`flat`) gets no rate, never an assumed one.

## Bars

For each contract it serves, the plugin keeps hourly and daily bars --
open, high, low and close traded prices and the contracts traded -- from
Kalshi's candlesticks, first reaching 30 days back. Kalshi's day is New
York's, so a daily bar is dated on New York's day. An hour or a day with no
trade has no bar.

## Events

For each contract it serves, the plugin also reports the Kalshi event the
contract belongs to: the event's markets, its series, and whether Kalshi
states the markets mutually exclusive (at most one can resolve YES). Your
deployment keeps the group beside its instrument records and asks the
platform to match it; a change to its markets or to what Kalshi states makes
a new version. Kalshi never states whether an event's markets cover every
result, so that is reported as not stated, never as no. For a range market
(a temperature between two values, say) the report also carries each
market's lower and upper bound as Kalshi states them, which your instrument
records show as values offered: a value a person set always wins.

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
outcomes and bars datasets are kept by default.
