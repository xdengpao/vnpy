---
inclusion: always
---

# 产品说明 — VeighNa/vn.py

VeighNa/vn.py（包名 `vnpy`）是一套**开源的、基于 Python 的量化交易框架**，用于构建自动化
交易、策略研究、回测和实盘运行平台。

当前版本：**4.4.0**（见 `vnpy/__init__.py`）。迁移记录见
`docs/migration_veighna_4.md`。许可证：**MIT**。

## 目标用户

机构投资者与专业交易员——对冲基金、自营交易公司、券商/期货资管、交易所、研究机构以及数字货币
基金。框架面向需要构建复杂策略并向多个市场（股票、期货、期权、外汇、数字货币）路由订单的用户。

## 4.x 能力模块

- **交易内核（`vnpy.trader`）**——事件驱动引擎、OMS、共享数据对象，以及桌面界面。
- **Alpha 模块（`vnpy.alpha`）**——4.x 新增的多因子/机器学习策略研究模块。
- **图表（`vnpy.chart`）**——高性能 K 线/蜡烛图绘制组件。
- **RPC（`vnpy.rpc`）**——进程/主机分布式部署，使交易组件可分离运行。
- **接口网关与应用模块**——主要由独立 `vnpy_*` 包提供，如 `vnpy_ctp`、`vnpy_ctastrategy`、
  `vnpy_ctabacktester`、`vnpy_sqlite`。

## 策略优化（`dev-ga` 分支的重点）

策略通过 `vnpy/trader/optimize.py` 中的优化工具进行调参。`dev-ga` 分支对 GA 优化器进行了
定制，引入动态交叉/变异概率与动态早停。该定制已按 4.x API 移植：默认返回优化结果列表，
需要收敛记录时传入 `return_logbook=True`。

## 关键链接

- 项目文档：https://www.vnpy.com/docs/cn/index.html
- 社区论坛：https://www.vnpy.com/forum/
