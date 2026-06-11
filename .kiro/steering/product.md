---
inclusion: always
---

# Product — vn.py

vn.py (package name `vnpy`) is an **open-source, Python-based quantitative trading
framework**. It was first released in January 2015 and has grown into a full-featured
platform for developing and running automated trading systems. Performance-sensitive,
low-level pieces are written in C++ and exposed to Python.

Current version: **2.4.0** (see `vnpy/__init__.py`). License: **MIT**.

## Who it is for

Institutional investors and professional traders — hedge funds, prop trading firms,
securities/futures asset managers, exchanges, research institutions, and crypto funds.
The framework targets users who build complex strategies and route orders to many
markets (equity, futures, options, forex, crypto).

## Capability areas

- **Trading core (`vnpy.trader`)** — the event-driven engine, the order-management
  system (OMS), shared data objects, and the desktop UI ("VN Trader").
- **Gateways (`vnpy.gateway`)** — connectors to dozens of brokers/exchanges across
  Chinese and global markets, plus crypto venues (e.g. CTP, XTP, IB, Binance, OKEX).
- **Apps (`vnpy.app`)** — pluggable applications such as CTA strategy, CTA backtester,
  portfolio strategy, spread trading, option master, algo trading, risk manager,
  data manager/recorder, paper account, script trader, and RPC service.
- **Charting (`vnpy.chart`)** — high-performance candlestick/k-line charting widgets.
- **Databases (`vnpy.database`)** — pluggable persistence (SQLite, MySQL, PostgreSQL,
  MongoDB, InfluxDB).
- **RPC (`vnpy.rpc`)** — process/host distribution so trading components can run apart.

## Strategy optimization (focus of the `dev-ga` branch)

Strategies are tuned with the optimization utilities in `vnpy/trader/optimize.py`:
brute-force (exhaustive grid) optimization and **genetic-algorithm (GA) optimization**.
The `dev-ga` branch customizes the GA optimizer with dynamic crossover/mutation
probabilities and dynamic early-stopping for faster, more robust convergence. See the
`ga-optimization` skill for details.

## Key links

- Project docs: https://www.vnpy.com/docs/cn/index.html
- Community forum: https://www.vnpy.com/forum/
