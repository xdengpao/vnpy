---
name: cta-strategy
description: 当在 vn.py 中构建、回测或优化 CTA（趋势/量化）策略时使用。说明应用如何以 vnpy_* 包重新导出、回测工作流，以及如何将策略参数调优接入穷举/遗传算法优化器。触发关键词：CTA、策略、backtest、回测、cta_backtester、组合策略、参数优化。
---

# 技能：CTA 策略与回测

## 应用的打包方式

`vnpy/app/<name>/` 下的策略/回测/组合应用都是很薄的"重新导出"垫片。例如
`vnpy/app/cta_strategy/__init__.py` 仅为：

```python
import sys
import vnpy_ctastrategy
sys.modules[__name__] = vnpy_ctastrategy
```

因此真正的实现位于已安装的 `vnpy_*` 包中（`vnpy_ctastrategy`、`vnpy_ctabacktester`、
`vnpy_portfoliostrategy`、`vnpy_spreadtrading` ...）。排查策略/回测内部逻辑时，请查看已安装
的包，而非仓库内的垫片。仓库内的 `vnpy/trader/*` 模块（event、object、constant、optimize）
是这些应用所依赖的共享基础。

## 典型工作流

1. **定义策略**：继承应用的策略模板；声明其 `parameters` 与 `variables`，并实现回调
   （`on_init`、`on_tick`/`on_bar`、`on_trade`、`on_order`、`on_stop`）。
2. **回测**单组参数：用回测引擎得到统计 `dict`（总收益、夏普、最大回撤等）。
3. **优化**：在搜索空间内对参数寻优（见下文）。
4. 审阅结果，再通过网关将选定参数部署到实盘。

可运行参考见 `examples/cta_backtesting/` 与 `examples/no_ui/run.py`。

## 优化策略参数

策略优化使用 `vnpy/trader/optimize.py`（被各应用共享）。模式如下：

```python
from vnpy.trader.optimize import (
    OptimizationSetting, check_optimization_setting,
    run_bf_optimization, run_ga_optimization,
)

setting = OptimizationSetting()
setting.add_parameter("fast_window", 5, 20, 1)   # 范围：5..20 步长 1
setting.add_parameter("slow_window", 20, 60, 5)  # 范围：20..60 步长 5
setting.add_parameter("fixed_size", 1)            # 固定值
setting.set_target("sharpe_ratio")                # 要最大化的指标

# evaluate_func(setting_dict) -> stats_dict   （运行一次回测）
# key_func(stats_dict) -> float               （提取目标指标）
if check_optimization_setting(setting):
    bf_results = run_bf_optimization(evaluate_func, setting, key_func)
    ga_results, logbook = run_ga_optimization(evaluate_func, setting, key_func)
```

- `evaluate_func` 封装"用这组参数配置回测 → 运行 → 返回统计"。
- `key_func` 从统计 dict 中取出标量目标。
- 结果是 `(setting, target_value, stats)` 形式的元组，按最优在前排序。

### 优化器选择

- **`run_bf_optimization`**——穷举网格；用于中小空间且希望得到保证的最优组合时。
- **`run_ga_optimization`**——遗传算法；用于穷举过慢的大空间。在 `dev-ga` 分支上它增加了动态
  交叉/变异概率与动态早停，并**额外返回一个 `logbook`** 用于收敛分析。完整内部细节见
  `ga-optimization` 技能。

## 提示

- 两种优化器都在并行进程中执行评估；请保持 `evaluate_func`/`key_func` 及其闭包可 pickle。
- 仅支持最大化：deap 的 fitness 使用 `weights=(1.0,)`。若需最小化某指标，请在 `key_func` 中
  返回其相反数。
- 启动长时间寻优前，用 `check_optimization_setting(...)` 校验输入。
