---
inclusion: always
---

# Project Structure & Architecture

## Repository layout

```
vnpy/
├── event/        # Event-driven core: Event, EventEngine (publish/subscribe + timer)
├── trader/       # Trading core: MainEngine, OMS, data objects, gateway/app base,
│   │             #   constants, optimization, UI
│   ├── engine.py     # MainEngine + LogEngine/OmsEngine/EmailEngine + BaseEngine
│   ├── gateway.py    # BaseGateway (abstract) + LocalOrderManager
│   ├── app.py        # BaseApp (abstract)
│   ├── object.py     # @dataclass data objects (TickData, OrderData, ...)
│   ├── constant.py   # Enums (Direction, Offset, Status, Exchange, Interval, ...)
│   ├── event.py      # Event-type string constants (EVENT_TICK, EVENT_ORDER, ...)
│   ├── optimize.py   # Brute-force + genetic-algorithm optimization (dev-ga focus)
│   ├── converter.py  # Offset/position conversion
│   ├── database.py / rqdata.py / setting.py / utility.py
│   └── ui/           # Qt desktop UI ("VN Trader")
├── gateway/      # Broker/exchange connectors (ctp, xtp, ib, binance, okex, ...)
├── app/          # Pluggable apps; each __init__.py re-exports an installed vnpy_* pkg
├── chart/        # High-performance candlestick charting widgets
├── database/     # Pluggable persistence: sqlite, mysql, postgresql, mongodb, influxdb
├── rpc/          # Cross-process/host RPC
└── api/          # C++ native API bindings (built as extensions)
examples/         # Runnable demos (no_ui, backtesting notebooks, client/server, rpc)
docs/             # Sphinx documentation (community + elite)
```

## Event-driven architecture

The system is built around `EventEngine` (`vnpy/event/engine.py`):

- An `Event` carries a `type` string and a `data` payload.
- Handlers register against a specific type via `register(type, handler)` or against
  **all** events via `register_general(handler)`.
- A background thread pulls events off a `Queue` and dispatches to handlers; a second
  thread emits an `EVENT_TIMER` ("eTimer") every `interval` seconds.
- Producers call `event_engine.put(Event(...))`.

Event-type constants live in `vnpy/trader/event.py`: `EVENT_TICK` (`"eTick."`),
`EVENT_TRADE`, `EVENT_ORDER`, `EVENT_POSITION`, `EVENT_ACCOUNT`, `EVENT_QUOTE`,
`EVENT_CONTRACT`, `EVENT_LOG`. Note the trailing `.` — gateways push both a generic
event and a specific one suffixed with the `vt_symbol`/`vt_orderid`
(e.g. `EVENT_TICK + tick.vt_symbol`) so subscribers can filter precisely.

## Core data model

Data objects in `vnpy/trader/object.py` are `@dataclass`es. All market/account objects
inherit `BaseData` (carrying `gateway_name`). Composite identifiers are computed in
`__post_init__`:

- `vt_symbol = f"{symbol}.{exchange.value}"`
- `vt_orderid = f"{gateway_name}.{orderid}"` (likewise `vt_tradeid`, `vt_quoteid`,
  `vt_accountid`, `vt_positionid`)

Request objects (`SubscribeRequest`, `OrderRequest`, `CancelRequest`, `HistoryRequest`,
`QuoteRequest`) flow **into** gateways; data objects flow **out** via `on_*` callbacks.
`OrderRequest.create_order_data(...)` and `OrderData.create_cancel_request()` are the
canonical conversion helpers.

## How components plug into MainEngine

`MainEngine` (`vnpy/trader/engine.py`) is the core. On construction it owns/starts an
`EventEngine` and initializes the built-in engines (`LogEngine`, `OmsEngine`,
`EmailEngine`). Components are added at runtime:

- `add_gateway(gateway_class)` → instantiates a `BaseGateway`, registers it by
  `gateway_name`, and merges its `exchanges`.
- `add_app(app_class)` → registers a `BaseApp` and adds the app's `engine_class`.
- `add_engine(engine_class)` → registers a functional `BaseEngine`.

This wiring is what lets gateways, apps, and engines remain decoupled and communicate
only through events and the OMS.
