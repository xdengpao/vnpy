---
inclusion: always
---

# 项目结构与架构

## 仓库布局

```
vnpy/
├── event/        # 事件驱动内核：Event、EventEngine（发布/订阅 + 定时器）
├── trader/       # 交易内核：MainEngine、OMS、数据对象、网关/应用基类、
│   │             #   常量、优化、UI
│   ├── engine.py     # MainEngine + LogEngine/OmsEngine/EmailEngine + BaseEngine
│   ├── gateway.py    # BaseGateway（抽象基类）+ LocalOrderManager
│   ├── app.py        # BaseApp（抽象基类）
│   ├── object.py     # @dataclass 数据对象（TickData、OrderData ...）
│   ├── constant.py   # 枚举（Direction、Offset、Status、Exchange、Interval ...）
│   ├── event.py      # 事件类型字符串常量（EVENT_TICK、EVENT_ORDER ...）
│   ├── optimize.py   # 穷举 + 遗传算法优化（dev-ga 重点）
│   ├── converter.py  # 开平/持仓转换
│   ├── database.py / rqdata.py / setting.py / utility.py
│   └── ui/           # Qt 桌面界面（"VN Trader"）
├── gateway/      # 券商/交易所连接器（ctp、xtp、ib、binance、okex ...）
├── app/          # 可插拔应用；每个 __init__.py 重新导出已安装的 vnpy_* 包
├── chart/        # 高性能 K 线图组件
├── database/     # 可插拔持久化：sqlite、mysql、postgresql、mongodb、influxdb
├── rpc/          # 跨进程/主机 RPC
└── api/          # C++ 原生 API 绑定（编译为扩展模块）
examples/         # 可运行示例（no_ui、回测 notebook、client/server、rpc）
docs/             # Sphinx 文档（社区版 + 精英版）
```

## 事件驱动架构

系统围绕 `EventEngine`（`vnpy/event/engine.py`）构建：

- 一个 `Event` 携带 `type` 字符串与 `data` 负载。
- 处理器通过 `register(type, handler)` 注册到指定类型，或通过 `register_general(handler)`
  注册到**所有**事件。
- 后台线程从 `Queue` 中取出事件并分发给处理器；另一个线程每隔 `interval` 秒发出一个
  `EVENT_TIMER`（`"eTimer"`）事件。
- 生产者通过 `event_engine.put(Event(...))` 推送事件。

事件类型常量位于 `vnpy/trader/event.py`：`EVENT_TICK`（`"eTick."`）、`EVENT_TRADE`、
`EVENT_ORDER`、`EVENT_POSITION`、`EVENT_ACCOUNT`、`EVENT_QUOTE`、`EVENT_CONTRACT`、
`EVENT_LOG`。注意结尾的 `.`——网关同时推送一个通用事件和一个以 `vt_symbol`/`vt_orderid`
为后缀的具体事件（如 `EVENT_TICK + tick.vt_symbol`），便于订阅者精确过滤。

## 核心数据模型

`vnpy/trader/object.py` 中的数据对象都是 `@dataclass`。所有行情/账户对象继承自 `BaseData`
（携带 `gateway_name`）。复合标识符在 `__post_init__` 中计算：

- `vt_symbol = f"{symbol}.{exchange.value}"`
- `vt_orderid = f"{gateway_name}.{orderid}"`（同理还有 `vt_tradeid`、`vt_quoteid`、
  `vt_accountid`、`vt_positionid`）

请求对象（`SubscribeRequest`、`OrderRequest`、`CancelRequest`、`HistoryRequest`、
`QuoteRequest`）**流入**网关；数据对象通过 `on_*` 回调**流出**。
`OrderRequest.create_order_data(...)` 与 `OrderData.create_cancel_request()` 是规范的
转换辅助方法。

## 组件如何接入 MainEngine

`MainEngine`（`vnpy/trader/engine.py`）是核心。构造时它会拥有并启动一个 `EventEngine`，
并初始化内置引擎（`LogEngine`、`OmsEngine`、`EmailEngine`）。组件在运行时动态添加：

- `add_gateway(gateway_class)` → 实例化一个 `BaseGateway`，按 `gateway_name` 注册，并合并
  其 `exchanges`。
- `add_app(app_class)` → 注册一个 `BaseApp`，并加入该应用的 `engine_class`。
- `add_engine(engine_class)` → 注册一个功能型 `BaseEngine`。

正是这套接线机制让网关、应用与引擎保持解耦，仅通过事件与 OMS 进行通信。
