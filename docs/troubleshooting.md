# Troubleshooting

## Kalshi is not answering

The Connection page's status says so, with the last error. The plugin waits
out a rate limit and tries again. Check the deployment can reach
external-api.kalshi.com.

## Venue master: not held

Your deployment has not pulled Kalshi from the platform's venue master. Each
price is recorded with its venue left empty and Kalshi named as reported, and
the plugin asks again the next day.

## A subject not served

The Datasets page says why for each:

- **Its record names none of the venue's binary event contracts**: the
  record carries no Kalshi ticker (nor another source's symbol that is one),
  or Kalshi does not state that market as binary. Add the ticker as a
  `symbol` with source `kalshi` on the Instruments page.
- **Its record states another payout**: the record's payout is not one
  dollar. Correct it on the Instruments page if it is Kalshi's contract.
- **Its record could not be read**: the deployment does not let the plugin
  read an instrument's record (a runtime before contract v18's ruling of
  2026-10-10).

## Not resolved: USD

Two of your deployment's records carry the dollar's ISO 4217 code. Merge
them on the Instruments page; nothing is priced until the dollar resolves to
one record.

## Nothing kept

The dataset's licence is served, not kept: the lake hands rows to the readers
waiting and keeps none. That is the default; change the licence on the Data
sources page if your deployment keeps them.
