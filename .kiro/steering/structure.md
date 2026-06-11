---
inclusion: always
---

# 项目结构与架构

## 迁移状态

当前工作区已同步到 VeighNa/vn.py 4.4.0 基线。新增代码或文档时，以
`pyproject.toml`、`docs/migration_veighna_4.md` 和 `requirements-veighna4.txt` 为准。

## 仓库布局

4.x 核心包布局：

```
vnpy/
├── alpha/        # 4.x 新增 AI/多因子研究与策略模块
├── chart/        # K 线图组件
├── event/        # 事件驱动内核
├── rpc/          # 跨进程/主机 RPC
└── trader/       # 交易内核、对象、优化、UI
```

网关、应用、数据库和数据服务不再作为核心目录维护，而是通过独立包接入：

```
vnpy_ctp
vnpy_ctastrategy
vnpy_ctabacktester
vnpy_sqlite
vnpy_rqdata
...
```

旧 2.x 的 `vnpy/gateway`、`vnpy/app`、`vnpy/api`、`vnpy/database` 目录已移除。

## 事件驱动架构

系统围绕 `EventEngine`（`vnpy/event/engine.py`）构建：

- 一个 `Event` 携带 `type` 字符串与 `data` 负载。
- 处理器通过 `register(type, handler)` 注册到指定类型，或通过 `register_general(handler)`
  注册到**所有**事件。
- 后台线程从 `Queue` 中取出事件并分发给处理器；另一个线程每隔 `interval` 秒发出一个
  `EVENT_TIMER`（`"eTimer"`）事件。
- 生产者通过 `event_engine.put(Event(...))` 推送事件。

事件类型常量位于 `vnpy/trader/event.py`。网关通常同时推送一个通用事件和一个以
`vt_symbol`/`vt_orderid` 为后缀的具体事件，便于订阅者精确过滤。

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

4.x 示例导入方式：

```python
from vnpy_ctp import CtpGateway
from vnpy_ctastrategy import CtaStrategyApp
from vnpy_ctabacktester import CtaBacktesterApp
```

不要再为新代码使用旧式导入：

```python
from vnpy.gateway.ctp import CtpGateway
from vnpy.app.cta_strategy import CtaStrategyApp
```
