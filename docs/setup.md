# Setup

## 1. Launch it

Upload and launch the plugin as any other. It asks for the `data` role and
storage for its raw responses, and no key.

## 2. License its datasets

On the dashboard's **Data sources** page, the plugin's three datasets are
listed -- `<instance>:live`, `<instance>:outcomes` and `<instance>:bars` --
each with Kalshi's published terms described in words: free, no key, and
for personal, non-commercial use only without Kalshi's written consent.
The plugin declares no licence. Set the deployment's licence there, with a
note saying why, as you and Kalshi have settled it; until one is set, the
lake keeps the rows and reads every use right restrictively. A licence
served, not kept, has the lake hand each live price to the readers waiting
and keep none.

## 3. Entitle the plugins that read it

On the same page, entitle each reading plugin to the datasets. Prices are
read by the reading roles; quotes by the roles that read at a higher
resolution (signal, portfolio, order and execution plugins); outcomes by the
reading roles and by operations, which explains a payout with them. Nothing reads a
dataset it is not entitled to.

## 4. Complete the contracts' records

The plugin names the contracts your readers ask about from their records,
and offers Kalshi's ticker, the class, the type and Kalshi's title where a
record lacks them. Complete each record on the **Instruments** page: its
type, binary event contract, and its payout, one dollar.

## Agents

An agent you delegate to can read the plugin's two pages through its tools
(`read_connection`, `read_datasets`); the Data sources and Instruments pages
have tools of their own.

## Sample data

On a development deployment, the plugin's **Sample data** setting makes it
answer from built-in synthetic responses instead of calling Kalshi, to try it
without reaching Kalshi.
