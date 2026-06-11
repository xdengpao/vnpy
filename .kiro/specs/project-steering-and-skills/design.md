# 设计 — 项目 Steering 与 Skills

## 概述

我们将基于对 `dev-ga` 分支源码的分析，在仓库的 `.kiro/` 目录下生成两类 Kiro 上下文产物：

```
.kiro/
├── specs/
│   └── project-steering-and-skills/   # 本 spec（requirements/design/tasks）
├── steering/
│   ├── product.md          # vn.py 是什么、能力、用户
│   ├── tech.md             # 语言、依赖、构建/检查命令
│   ├── structure.md        # 仓库布局 + 事件驱动架构
│   └── code-style.md       # 约定、提交/PR 规则、flake8
└── skills/
    ├── ga-optimization/SKILL.md       # dev-ga GA 优化器指南
    ├── gateway-development/SKILL.md    # BaseGateway 实现指南
    └── cta-strategy/SKILL.md           # 策略 + 回测/优化
```

## Steering — 设计决策

Steering **始终加载**，因此每个文件都保持简洁、客观。我们遵循常规的 Kiro 三件套
（product / tech / structure），并额外增加 `code-style.md`，因为该代码库有清晰、可复用的
约定（dataclass、`vt_*` id、`[Mod]` 提交）。

### product.md
取材于 `README.md` 与 `setup.py` 的 docstring。涵盖：开源的事件驱动框架；能力模块
（`vnpy.trader`、`vnpy.gateway`、`vnpy.app`、`vnpy.chart`、`vnpy.database`、`vnpy.rpc`）；
目标用户（机构、专业交易员）。

### tech.md
取材于 `setup.py`、`requirements.txt`、`.flake8`、`.github/workflows/pythonapp.yml`。
涵盖：Python 3.7、通过 setuptools `Extension` 构建的 C++17 原生扩展、`VNPY_BUILD_*` /
`VNPY_BUILD_PARALLEL` 环境变量、依赖列表，以及 flake8 检查命令。

### structure.md
取材于 `vnpy/` 目录树与 `trader/` 内核。涵盖：包地图；`EventEngine` 发布/订阅模型与事件类型
字符串；dataclass 数据模型（`TickData`、`OrderData` ... 带 `vt_symbol`/`vt_orderid` 复合
id）；以及 `MainEngine.add_gateway`/`add_app`/`add_engine` 如何接线各组件。

### code-style.md
取材于观察到的代码 + `.flake8` + git 历史 + PR 模板。涵盖：4 空格缩进、处处类型标注、
数据用 `@dataclass`、三引号 docstring（常见空占位 `""""""`）、在 `__post_init__` 中构造
`vt_*` id、中文日志/用户字符串、`[Mod]`/`[Add]`/`[Del]`/`[Fix]` 提交前缀，以及小 PR 原则。

## Skills — 设计决策

每个 skill 是一个目录，内含以 YAML frontmatter 开头的 `SKILL.md`：

```yaml
---
name: <skill-name>
description: <Kiro 何时应加载该 skill>
---
```

`description` 编写为便于 Kiro 判断何时激活（触发关键词 + 意图）。正文保持任务聚焦。

### ga-optimization（dev-ga 核心）
解释 `vnpy/trader/optimize.py`：`OptimizationSetting`、`check_optimization_setting`、
`run_bf_optimization`，尤其是 `run_ga_optimization` + 内嵌的 `GA_accuracy`。记录 deap
toolbox 接线、动态交叉概率 `cxpb = k1*(max-child)/(max-avg)` 与动态变异概率
`mutpb = k2*(max-fitness)/(max-avg)`、常量 `k1=0.85, k2=0.5, k3=1.0, k4=0.05`、精英保留
（`selBest`）、`std <= 1e-10` 时的动态早停、以参数元组为键的多进程 `Manager().dict()` 结果
缓存，以及 `(results, logbook)` 返回契约。附带安全扩展指南。

### gateway-development
提炼 `BaseGateway` 的 docstring 契约：实现抽象方法（`connect`、`close`、`subscribe`、
`send_order`、`cancel_order`、`query_account`、`query_position`；可选 `query_history`、
`send_quote`）；触发 `on_tick/on_trade/on_order/on_position/on_account/on_contract`；声明
`default_setting` 与 `exchanges`；遵守线程安全、非阻塞、自动重连与推送前复制规则；当交易所
需要本地委托号时使用 `LocalOrderManager`。

### cta-strategy
解释策略/回测应用以独立 `vnpy_*` 包形式发布并由 `vnpy/app/<name>/__init__.py` 重新导出，
并将策略优化与 `OptimizationSetting` + `key_func` + 穷举/GA 模式联系起来，附带何时选用各
优化器的指南。

## 范围之外
- 不修改 `vnpy/` 本身的源码。
- 不引入新依赖。仅为文档/上下文产物。
