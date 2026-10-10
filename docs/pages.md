# Pages

Both pages are under **Manage**, for the plugin's admin. Neither shows a
price, a side of the book or a size.

## Connection

How the plugin reaches Kalshi: whether it answers from Kalshi or from
synthetic responses, the endpoint, what the plugin spends of Kalshi's limits
(at most 5 requests a second), how many calls it made, how many met a rate
limit or failed, the last error, and the venue's ID in the platform's venue
master, or that your deployment does not hold it.

## Datasets

What the plugin serves: its dataset, with its data, modes, day and default
licence; how many contracts are mapped for the instruments the lake asked
about, and how many it did not serve and why; the currency its prices and
payouts are in, your deployment's record for it, and what each contract
pays; what Kalshi entitles it to (public data, no key); and the wants the
lake sent it, those it keeps current first, each with how many rows it
recorded and subjects it declined. The search above the wants narrows them.

## Tools for agents

Each page is a read tool answering what the page shows: `read_connection` and
`read_datasets`, for a person holding admin on the plugin.
