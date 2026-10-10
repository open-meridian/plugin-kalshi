# Setup

## 1. Launch it

Upload and launch the plugin as any other. It asks for the `dgm` role and
storage for its raw responses, and no key.

## 2. License its dataset

On the dashboard's **Data sources** page, the plugin's dataset is listed
with its default licence:

- `<instance>:live`: served, not kept.

The default says nothing about Kalshi's terms. Set the deployment's licence
there, with a note saying why, as you and the people using the deployment
have settled it. What you enter is what your deployment records.

## 3. Entitle the plugins that read it

On the same page, entitle each reading plugin to the dataset. Prices are
read by the reading roles; quotes by the roles that read at a higher
resolution (signal, portfolio, order and execution plugins). Nothing reads a
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

## Synthetic mode

On a development deployment, the plugin's **Synthetic mode** setting makes it
answer from built-in synthetic responses instead of calling Kalshi, to try it
without reaching Kalshi.
