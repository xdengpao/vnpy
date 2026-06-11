---
name: ga-optimization
description: Use when working on strategy parameter optimization in vn.py — especially the genetic algorithm optimizer in vnpy/trader/optimize.py (run_ga_optimization, GA_accuracy, ga_evaluate, OptimizationSetting). Covers the dev-ga branch's dynamic crossover/mutation probabilities and dynamic early-stopping. Trigger on: GA, genetic algorithm, optimize, optimization, deap, cxpb, mutpb, logbook, parameter tuning.
---

# Skill: Genetic Algorithm Optimization (vnpy/trader/optimize.py)

This is the centerpiece of the `dev-ga` branch. Read `vnpy/trader/optimize.py` before
editing — the GA implementation is custom and differs from upstream vn.py.

## Public API surface

- `OptimizationSetting` — declares the parameter search space and the optimization target.
  - `add_parameter(name, start, end=None, step=None)` — a single value (fixed) when only
    `start` is given, otherwise an inclusive range `start..end` stepped by `step`.
    Returns `(ok: bool, message: str)`; validates `start < end` and `step > 0`.
  - `set_target(target_name)` — name of the metric to maximize.
  - `generate_settings()` → `List[dict]` — Cartesian product of all parameters.
- `check_optimization_setting(setting, output=print)` → `bool` — guards against an empty
  combination space or a missing target.
- `run_bf_optimization(evaluate_func, setting, key_func, max_workers=None, output=print)`
  → `List[Tuple]` — brute-force/exhaustive grid search using a `ProcessPoolExecutor`,
  results sorted descending by `key_func`.
- `run_ga_optimization(evaluate_func, setting, key_func, max_workers=cpu_count()-1,
  population_size=50, ngen_size=100, output=print)` → `Tuple[List[Tuple], logbook]`.

### Callable contracts

- `evaluate_func: Callable[[dict], dict]` — runs one backtest for a parameter `dict` and
  returns a statistics `dict`.
- `key_func: Callable[[list], float]` — extracts the scalar to maximize from the result.
  (deap fitness is configured with `weights=(1.0,)`, i.e. **maximization**.)

## How `run_ga_optimization` works

1. Builds candidate settings as lists of `(name, value)` items from `generate_settings()`.
2. Sets up a `multiprocessing.Manager().dict()` **cache** (keyed by the parameter tuple)
   and a `Pool(max_workers)` for parallel evaluation.
3. Configures a deap `Toolbox`:
   - `individual` / `population` via `tools.initIterate` / `initRepeat`.
   - `mate = tools.cxTwoPoint`, `mutate = mutate_individual` (resamples genes with prob
     `indpb`), `select = tools.selTournament(tournsize=2)`.
   - `map = pool.map`, `evaluate = ga_evaluate(cache, evaluate_func, key_func, ...)`.
4. Runs the nested `GA_accuracy(...)` driver, then returns
   `(sorted(list(cache.values()), reverse, key=key_func), logbook)`.

### `ga_evaluate(cache, evaluate_func, key_func, parameters)`

Memoizes by `tuple(parameters)`: on a cache miss it builds `dict(parameters)`, calls
`evaluate_func`, stores the **full result dict** in the cache, then returns
`(key_func(result),)` as the deap fitness tuple. This is why `cache.values()` yields the
complete result objects at the end.

## dev-ga customizations (the important part)

The nested `GA_accuracy` function implements the custom evolutionary loop:

- **Statistics + logbook:** records `avg/min/max/std` of fitness each generation into a
  `tools.Logbook`, which is returned to the caller for analysis/plotting.
- **Dynamic crossover probability** (`dynamic_probability == 1`), per mating pair:
  - if `max_child >= avg`: `cxpb = k1 * (max - max_child) / (max - avg)` (clamped `>= 0`)
  - else: `cxpb = k3`
- **Dynamic mutation probability**, per individual:
  - if `fitness >= avg`: `mutpb = k2 * (max - fitness) / (max - avg)` (clamped `>= 0`)
  - else: `mutpb = k4`
- **Constants:** `k1=0.85, k2=0.5, k3=1.0, k4=0.05`.
- **Elitism / reinsertion:** selects offspring (`2 * npop`, with `npop = 100`), applies
  crossover+mutation, re-evaluates invalid individuals, keeps the best via
  `tools.selBest(offspring, npop)`.
- **Dynamic early-stopping** (`dynamic_stop == 1`): returns as soon as
  `logbook.select('std')[0] <= 1e-10` (population has converged), saving runtime.

The module-level seeds for `cxpb`/`mutpb`/`mu`/`lambda_` are starting values for the
"speed" mode; with dynamic probability enabled they are recomputed each generation.

## When to use which optimizer

- **Brute force (`run_bf_optimization`)** — small/medium search spaces where you want the
  guaranteed global best across the grid.
- **Genetic algorithm (`run_ga_optimization`)** — large spaces where exhaustive search is
  too expensive; trades completeness for speed. The dynamic probabilities + early-stop
  improve convergence quality/robustness at some time cost.

## Guidance for safe changes

- Keep the deap `creator.create(...)` calls module-level and idempotent — re-creating
  `FitnessMax`/`Individual` raises at import if duplicated.
- Preserve the `(results, logbook)` return tuple of `run_ga_optimization`; callers in the
  CTA backtester app depend on it. If you change the return shape, update all callers.
- Anything passed to the `Pool` must be picklable (the `evaluate_func`/`key_func` and
  their closures). Keep them top-level-friendly.
- Tune dynamic behavior via the `k1..k4` constants, the `std` early-stop threshold, and
  `population_size`/`ngen_size` — document any change in the commit (`[Mod]` prefix).
- After edits, smoke-test by importing the module and running a tiny optimization with a
  trivial `evaluate_func`/`key_func` to confirm it converges and returns a logbook.
