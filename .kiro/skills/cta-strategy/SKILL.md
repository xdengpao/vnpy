---
name: cta-strategy
description: Use when building, backtesting, or optimizing CTA (trend/quant) strategies in vn.py. Explains how apps are packaged as vnpy_* re-exports, the backtesting workflow, and how to plug strategy parameter tuning into the brute-force/genetic-algorithm optimizers. Trigger on: CTA, strategy, backtest, backtesting, cta_backtester, portfolio strategy, parameter optimization.
---

# Skill: CTA Strategy & Backtesting

## How apps are packaged

The strategy/backtesting/portfolio apps in `vnpy/app/<name>/` are thin re-export shims.
For example `vnpy/app/cta_strategy/__init__.py` is just:

```python
import sys
import vnpy_ctastrategy
sys.modules[__name__] = vnpy_ctastrategy
```

So the real implementation lives in the installed `vnpy_*` package
(`vnpy_ctastrategy`, `vnpy_ctabacktester`, `vnpy_portfoliostrategy`,
`vnpy_spreadtrading`, ...). When investigating strategy/backtester internals, inspect the
installed package, not the in-repo shim. The in-repo `vnpy/trader/*` modules (event,
object, constant, optimize) are the shared foundation those apps build on.

## Typical workflow

1. **Define a strategy** subclassing the app's strategy template; declare its `parameters`
   and `variables`, and implement callbacks (`on_init`, `on_tick`/`on_bar`, `on_trade`,
   `on_order`, `on_stop`).
2. **Backtest** a single parameter set with the backtesting engine to produce a statistics
   `dict` (total return, Sharpe, max drawdown, etc.).
3. **Optimize** parameters across a search space (see below).
4. Review results, then deploy the chosen parameters live through a gateway.

See `examples/cta_backtesting/` and `examples/no_ui/run.py` for runnable references.

## Optimizing strategy parameters

Strategy optimization uses `vnpy/trader/optimize.py` (shared by the apps). The pattern:

```python
from vnpy.trader.optimize import (
    OptimizationSetting, check_optimization_setting,
    run_bf_optimization, run_ga_optimization,
)

setting = OptimizationSetting()
setting.add_parameter("fast_window", 5, 20, 1)   # range: 5..20 step 1
setting.add_parameter("slow_window", 20, 60, 5)  # range: 20..60 step 5
setting.add_parameter("fixed_size", 1)            # fixed value
setting.set_target("sharpe_ratio")                # metric to maximize

# evaluate_func(setting_dict) -> stats_dict   (runs one backtest)
# key_func(stats_dict) -> float               (extracts the target metric)
if check_optimization_setting(setting):
    bf_results = run_bf_optimization(evaluate_func, setting, key_func)
    ga_results, logbook = run_ga_optimization(evaluate_func, setting, key_func)
```

- `evaluate_func` wraps "configure backtest with these params → run → return stats".
- `key_func` pulls the scalar target out of the stats dict.
- Results are `(setting, target_value, stats)`-style tuples sorted best-first.

### Choosing the optimizer

- **`run_bf_optimization`** — exhaustive grid; use for small/medium spaces when you want
  the guaranteed best combination.
- **`run_ga_optimization`** — genetic algorithm; use for large spaces where brute force is
  too slow. On the `dev-ga` branch it adds dynamic crossover/mutation probabilities and
  dynamic early-stopping, and **also returns a `logbook`** for convergence analysis.
  See the `ga-optimization` skill for the full internals.

## Tips

- Both optimizers run evaluations in parallel processes; keep `evaluate_func`/`key_func`
  and their closures picklable.
- Maximization only: deap fitness uses `weights=(1.0,)`. To minimize a metric, return its
  negative from `key_func`.
- Validate inputs with `check_optimization_setting(...)` before launching a long run.
