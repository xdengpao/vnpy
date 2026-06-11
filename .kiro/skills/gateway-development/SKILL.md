---
name: gateway-development
description: 当在 vn.py 中实现或修改交易网关（券商/交易所连接器）时使用。涵盖 BaseGateway 契约、必须实现的抽象方法、on_* 事件回调、线程安全规则以及 LocalOrderManager。触发关键词：gateway、网关、BaseGateway、connect、send_order、on_tick、交易所连接器、券商 API、行情订阅。
---

# 技能：网关开发（vnpy/trader/gateway.py）

网关把 vn.py 连接到某个具体的交易系统（券商/交易所）。它继承 `BaseGateway`，并通过
`MainEngine.add_gateway(...)` 注册。多数生产环境网关位于各自的 `vnpy_*` 包中，但都遵循同一
契约。请先阅读 `vnpy/trader/gateway.py` 中 `BaseGateway` 的 docstring。

本分支例外保留了旧式虚拟币交易兼容层：`vnpy.api.rest`、`vnpy.api.websocket`，以及
`vnpy/gateway` 下的虚拟币网关子集。修改这些网关时按兼容维护处理；新增非虚拟币网关仍优先
采用独立 `vnpy_*` 包。

## 核心规则（来自 BaseGateway docstring）

- **线程安全：** 所有方法必须线程安全；对象之间不共享可变状态。
- **非阻塞：** 方法不得阻塞。
- **自动重连：** 连接断开后自动重连。
- **推送前复制：** 传入 `on_*` 回调的数据应视为不可变。若需缓存引用，请推送
  `copy.copy(...)`，以免缓存随后被修改。

## 需声明的类属性

- `default_setting: Dict[str, Any]`——`connect` 所需用户填写的字段（host、port、凭证等）。
  会在 UI 中展示；由 `get_default_setting()` 返回。
- `exchanges: List[Exchange]`——该网关支持的交易所（会被合并进 MainEngine）。

## 必须实现的方法（`@abstractmethod`）

- `connect(setting: dict)`——建立连接；随后查询并推送合约、账户、持仓、未完成委托与成交
  （经对应的 `on_*`）；任何查询失败都应 `write_log`。
- `close()`——断开连接。
- `subscribe(req: SubscribeRequest)`——订阅 tick 行情。
- `send_order(req: OrderRequest) -> str`——通过
  `req.create_order_data(orderid, gateway_name)` 创建 `OrderData`，分配网关内唯一的
  `orderid`，发送到服务器（成功置 `Status.SUBMITTING` / 发送失败置 `Status.REJECTED`），
  调用 `on_order(...)`，并返回 `vt_orderid`。
- `cancel_order(req: CancelRequest)`——向服务器发送撤单。
- `query_account()` / `query_position()`——刷新资金 / 持仓。

## 可重写的方法

- `query_history(req: HistoryRequest) -> List[BarData]`——若交易所支持历史 K 线则提供
  （并设置 `ContractData.history_data = True`）。
- `send_quote` / `cancel_quote`——双边报价（做市），如支持。
- `send_orders` / `cancel_orders`——批量操作；默认循环调用单笔方法，仅在交易所有原生批量
  能力时重写。

## 向外推送数据——`on_*` 回调

数据到达时触发以下回调；基类会同时发布一个通用事件和一个按 symbol/id 区分的具体事件：

`on_tick`、`on_trade`、`on_order`、`on_position`、`on_account`、`on_quote`、
`on_contract`、`on_log`。人类可读的状态信息使用 `write_log(msg)`（它封装了
`LogData` + `on_log`）。

## LocalOrderManager（本地委托管理）

当交易所异步返回自身的系统委托号（导致无法用原始 id 撤单）时，使用 `LocalOrderManager`：

- 生成本地委托号（`new_local_orderid`）并维护 本地↔系统 id 的映射。
- 缓存在系统 id 已知之前到达的撤单请求，并在映射建立后重放（`check_cancel_request`）。
- 缓存委托推送数据直到本地 id 解析完成（`add_push_data` / `check_push_data` 配合
  `push_data_callback`）。
- 挂接 `gateway.cancel_order`，使撤单自动经由映射路由。

## 实现清单

1. 继承 `BaseGateway`；设置 `default_setting` 与 `exchanges`。
2. 按上述 docstring 契约实现所有抽象方法。
3. 把交易所返回的数据转换为 vn.py 的 `@dataclass` 对象（正确的 `Exchange`、`Direction`、
   `Offset`、`Status`、`OrderType` 枚举）并经 `on_*` 推送。
4. 若交易所需要本地委托号，使用 `LocalOrderManager`。
5. 保证重连逻辑与线程安全；切勿在回调中阻塞。
6. 用户/日志字符串与代码库保持一致（通常为中文）。
