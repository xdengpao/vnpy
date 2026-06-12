# 设计 — CTA 回测行情数据下载源选择

## 概述

改动分为 UI 和引擎两部分：

- `vnpy_ctabacktester/ui/widget.py`：在参数表单中增加可编辑 `QComboBox`，放在「交易策略」下方；下载数据时把选中的数据源名称传给引擎；保存/恢复到 `cta_backtester_setting.json`。
- `vnpy_ctabacktester/engine.py`：为下载任务增加 `datafeed_name` 参数；每次下载前按该名称刷新 `SETTINGS["datafeed.name"]`、重置全局 datafeed 缓存并重新 `get_datafeed()`；随后直接调用该 datafeed 查询历史数据。

## UI 设计

新增控件：

```python
self.datafeed_combo = QtWidgets.QComboBox()
self.datafeed_combo.setEditable(True)

self.symbol_source_combo = QtWidgets.QComboBox()
self.symbol_combo = QtWidgets.QComboBox()
self.symbol_combo.setEditable(True)

self.interval_source_combo = QtWidgets.QComboBox()
self.interval_combo = QtWidgets.QComboBox()
self.interval_combo.setEditable(True)
```

选项来源：

1. 当前 `SETTINGS["datafeed.name"]`。
2. 常用数据源名称：`rqdata`、`xt`、`wind`、`tushare`、`tinysoft`。
3. `vnpy.vnpym.data.available_crypto_gateways()` 暴露的虚拟币行情源名称。

因为 vn.py 的 datafeed 模块加载规则是 `vnpy_{name}`，控件保存的是短名称，例如 `rqdata`，而不是 `vnpy_rqdata`。
虚拟币行情源也直接保存短名称，例如 `binance_spot`。

「本地代码」从 `QLineEdit` 改为可编辑 `QComboBox`。新增「代码来源」行，包含：

- 来源下拉框：「本地」「数据源Reload」。
- 「刷新代码」按钮。

刷新逻辑：

- 「本地」：调用引擎读取 MainEngine 合约列表、数据库 K 线概览和 Tick 概览，合并去重后填入本地代码下拉框。
- 「数据源Reload」：
  - 虚拟币行情源：创建对应 gateway，调用 REST 合约查询，收集 `ContractData.vt_symbol`。
  - 普通 datafeed：没有统一代码列表接口，若实现了常见的 symbol 查询方法则尝试调用，否则输出不支持日志。

## 引擎设计

新增私有方法：

```python
def get_datafeed_by_name(self, datafeed_name: str) -> BaseDatafeed | None:
```

新增列表加载方法：

```python
def get_local_vt_symbols(self) -> list[str]:
def get_source_vt_symbols(self, datafeed_name: str) -> list[str]:
def get_crypto_vt_symbols(self, gateway_name: str) -> list[str]:
```

职责：

1. 校验名称非空。
2. 写入 `SETTINGS["datafeed.name"]`。
3. 将 `vnpy.trader.datafeed.datafeed` 置空，避免复用旧 datafeed 实例。
4. 通过 `get_datafeed()` 创建新实例。
5. 调用 `init(self.write_log)` 初始化；失败则返回 `None`。

`get_local_vt_symbols` 从当前 `MainEngine.get_all_contracts()`、`database.get_bar_overview()` 和
`database.get_tick_overview()` 汇总 `vt_symbol`。

`get_source_vt_symbols` 根据当前行情数据源分流：

- 命中虚拟币行情源时调用 `get_crypto_vt_symbols`。
- 普通 datafeed 尝试调用 `query_symbols`、`get_symbols`、`get_all_symbols` 等常见扩展方法；
  如果没有可用方法，输出不支持日志并返回空列表。

`get_crypto_vt_symbols` 会启动 gateway 的 REST 客户端执行 `query_contract()`，收集 gateway
通过 `on_contract` 推送的 `ContractData`。

为避免旧 REST 客户端在网络异常时调用 `sys.excepthook`，虚拟币合约列表 Reload 改为同步 HTTP
请求，并显式设置超时。所有 `requests` 异常都捕获后写入日志，返回空列表；UI 层的刷新方法也会
兜底捕获异常。

### K 线周期

「K线周期」同样改成可编辑 `QComboBox`，并新增「周期来源」行：

- 「本地」：从 `database.get_bar_overview()` 读取当前 `vt_symbol` 已保存的周期；如果为空，回退到
  `Interval` 默认值。
- 「数据源Reload」：
  - 虚拟币行情源：返回当前网关 `query_history` 映射中支持的 `Interval` 值，例如 Binance
    系列支持 `1m`、`1h`、`d`。
  - 普通 datafeed：尝试调用常见扩展方法 `query_intervals`、`get_intervals` 等；否则回退到默认值。

当前不把交易所全部原生周期（如 Binance 的 `5m`、`15m`）直接加入回测周期，因为本地
`HistoryRequest.interval` 和现有 gateway `query_history` 映射只安全支持 vn.py 的
`Interval` 枚举值。

下载逻辑：

- Tick：调用所选 datafeed 的 `query_tick_history`。
- K 线：调用所选 datafeed 的 `query_bar_history`。
- 不再检查 `main_engine.get_contract(vt_symbol)` 和 `main_engine.query_history(...)`，避免页面选择被网关分支绕过。

### 虚拟币行情源

当选择值命中 `vnpy.vnpym.data.CRYPTO_GATEWAYS` 时，下载逻辑不再走 `vnpy.trader.datafeed.get_datafeed()`，而是：

1. 通过 `get_crypto_gateway_spec(name)` 获取网关元数据。
2. 构造默认 `VnpymConfig` 并将 `crypto_gateway.name` 设置为当前选择。
3. 通过 `create_crypto_gateway(spec, config)` 初始化网关 REST API。
4. 校验 `vt_symbol` 的交易所与网关元数据一致。
5. 调用 `gateway.query_history(req)` 获取 K 线并保存数据库。

虚拟币行情源当前仅支持 K 线下载；如果用户选择 Tick 周期，直接输出不支持日志。

## 兼容性

- 只修改本地安装包中的 `vnpy_ctabacktester`，不改变核心 `vnpy` 包 API。
- `BacktesterEngine.start_downloading` 和 `run_downloading` 增加参数，因此同步修改唯一调用点 `BacktesterManager.start_downloading`。
- 既有全局 `datafeed.username/password` 仍沿用 `vt_setting.json` 配置，本次 UI 只负责选择数据源名称。

## 风险

- 修改的是当前虚拟环境的安装包，而非仓库源码；后续重新安装 `vnpy_ctabacktester` 可能覆盖改动。
- 手动输入的数据源如果没有安装对应 `vnpy_<name>` 包，会在下载时失败并输出日志。
