---
name: gateway-development
description: Use when implementing or modifying a trading gateway (broker/exchange connector) in vn.py. Covers the BaseGateway contract, required abstract methods, on_* event callbacks, thread-safety rules, and LocalOrderManager. Trigger on: gateway, BaseGateway, connect, send_order, on_tick, exchange connector, broker API, market data feed.
---

# Skill: Gateway Development (vnpy/trader/gateway.py)

A gateway connects vn.py to a specific trading system (broker/exchange). It subclasses
`BaseGateway` and is registered via `MainEngine.add_gateway(...)`. Most production
gateways live in their own `vnpy_*` packages, but they all follow this contract. Read
`BaseGateway`'s docstring in `vnpy/trader/gateway.py` first.

## Core rules (from BaseGateway docstring)

- **Thread-safe:** all methods must be thread-safe; no mutable shared state between objects.
- **Non-blocking:** methods must not block.
- **Auto-reconnect:** reconnect automatically if the connection drops.
- **Copy before push:** data passed to `on_*` callbacks must be treated as immutable. If
  you keep a cached reference, push a `copy.copy(...)` so the cache is not mutated later.

## Class attributes to declare

- `default_setting: Dict[str, Any]` — fields the user must fill to `connect` (host, port,
  credentials, etc.). Surfaced in the UI; returned by `get_default_setting()`.
- `exchanges: List[Exchange]` — exchanges this gateway supports (merged into MainEngine).

## Methods you must implement (`@abstractmethod`)

- `connect(setting: dict)` — establish connection; then query and push contracts,
  account, positions, open orders, and trades (via the matching `on_*`); `write_log` on
  any failed query.
- `close()` — tear down the connection.
- `subscribe(req: SubscribeRequest)` — subscribe to tick updates.
- `send_order(req: OrderRequest) -> str` — create `OrderData` via
  `req.create_order_data(orderid, gateway_name)`, assign a gateway-unique `orderid`, send
  to the server (set `Status.SUBMITTING` on success / `Status.REJECTED` on send failure),
  call `on_order(...)`, and return `vt_orderid`.
- `cancel_order(req: CancelRequest)` — send a cancel to the server.
- `query_account()` / `query_position()` — refresh balances / holdings.

## Methods you may override

- `query_history(req: HistoryRequest) -> List[BarData]` — provide bar history if the
  venue supports it (set `ContractData.history_data = True`).
- `send_quote` / `cancel_quote` — two-sided quoting (market making) if supported.
- `send_orders` / `cancel_orders` — batch operations; default loops over the single-order
  methods, override only if the venue has native batch support.

## Pushing data out — the `on_*` callbacks

Fire these as data arrives; the base class publishes both a generic event and a
symbol/id-specific event:

`on_tick`, `on_trade`, `on_order`, `on_position`, `on_account`, `on_quote`,
`on_contract`, `on_log`. Use `write_log(msg)` for human-readable status messages (it
wraps `LogData` + `on_log`).

## LocalOrderManager

When a venue returns its own system order id asynchronously (so you can't cancel by the
original id), use `LocalOrderManager`:

- Generates local order ids (`new_local_orderid`) and maps local↔system ids.
- Buffers cancel requests that arrive before the system id is known, and replays them
  once the mapping is established (`check_cancel_request`).
- Buffers order push data until the local id is resolved (`add_push_data` /
  `check_push_data` with a `push_data_callback`).
- Hooks `gateway.cancel_order` so cancels route through the mapping automatically.

## Implementation checklist

1. Subclass `BaseGateway`; set `default_setting` and `exchanges`.
2. Implement all abstract methods following the docstring contracts above.
3. Convert venue payloads into vn.py `@dataclass` objects (correct `Exchange`,
   `Direction`, `Offset`, `Status`, `OrderType` enums) and push via `on_*`.
4. Use `LocalOrderManager` if the venue needs local order ids.
5. Ensure reconnect logic and thread-safety; never block in a callback.
6. Keep user/log strings consistent with the codebase (often Chinese).
