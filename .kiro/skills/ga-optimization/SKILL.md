---
name: ga-optimization
description: 当处理 vn.py 中的策略参数优化时使用——尤其是 vnpy/trader/optimize.py 中的遗传算法优化器（run_ga_optimization、GA_accuracy、ga_evaluate、OptimizationSetting）。涵盖 dev-ga 分支的动态交叉/变异概率与动态早停。触发关键词：GA、遗传算法、optimize、优化、deap、cxpb、mutpb、logbook、参数调优。
---

# 技能：遗传算法优化（vnpy/trader/optimize.py）

这是 `dev-ga` 分支的核心定制。当前仓库已同步到 VeighNa/vn.py 4.4.0，动态交叉/变异概率、
动态早停和可选 `logbook` 返回已移植到 `vnpy/trader/optimize.py`。

## 公开 API

- `OptimizationSetting`——声明参数搜索空间与优化目标。
  - `add_parameter(name, start, end=None, step=None)`——仅给 `start` 时为固定值；否则为
    闭区间 `start..end`，步长 `step`。返回 `(ok: bool, message: str)`；校验 `start < end`
    与 `step > 0`。
  - `set_target(target_name)`——要最大化的指标名称。
  - `generate_settings()` → `List[dict]`——所有参数的笛卡尔积。
- `check_optimization_setting(setting, output=print)` → `bool`——防止参数组合为空或未设置
  优化目标。
- `run_bf_optimization(evaluate_func, setting, key_func, max_workers=None, output=print)`
  → `List[Tuple]`——使用 `ProcessPoolExecutor` 的穷举/网格搜索，结果按 `key_func` 降序排序。
- `run_ga_optimization(..., dynamic_probability=True, dynamic_stop=True, return_logbook=False)`
  → 默认 `List[Tuple]`；传入 `return_logbook=True` 时返回 `Tuple[List[Tuple], logbook]`。

### 可调用对象契约

- `evaluate_func: Callable[[dict], dict]`——针对一组参数 `dict` 运行一次回测并返回统计 `dict`。
- `key_func: Callable[[list], float]`——从结果中提取要最大化的标量。
  （deap 的 fitness 配置为 `weights=(1.0,)`，即**最大化**。）

## `run_ga_optimization` 的工作流程

1. 由 `generate_settings()` 把候选设置构造为 `(name, value)` 项列表。
2. 建立 `multiprocessing.Manager().dict()` **缓存**（以参数元组为键）并用 `Pool(max_workers)`
   进行并行评估。
3. 配置 deap `Toolbox`：
   - `individual` / `population` 使用 `tools.initIterate` / `initRepeat`。
   - `mate = tools.cxTwoPoint`，`mutate = mutate_individual`（以 `indpb` 概率重采样基因，
     代码中 `indpb=1`），`select = tools.selTournament(tournsize=2)`。
   - `map = pool.map`，`evaluate = ga_evaluate(cache, evaluate_func, key_func, ...)`。
4. 动态模式运行 `run_dynamic_ga_optimization(...)`，否则回落到 deap
   `algorithms.eaMuPlusLambda(...)`。
5. 默认返回 `sorted(list(cache.values()), reverse=True, key=key_func)`；当
   `return_logbook=True` 时额外返回 `logbook`。

### `ga_evaluate(cache, evaluate_func, key_func, parameters)`

以 `tuple(parameters)` 做记忆化：缓存未命中时构造 `dict(parameters)`、调用 `evaluate_func`、
把**完整结果 dict** 存入缓存，再返回 `(key_func(result),)` 作为 deap 的 fitness 元组。这也是
最终 `cache.values()` 能产出完整结果对象的原因。

## dev-ga 定制要点（重点）

`run_dynamic_ga_optimization` 函数实现定制进化循环：

- **统计 + logbook：** 每代将 fitness 的 `avg/min/max/std` 记入 `tools.Logbook`，并返回给
  调用方用于分析/绘图。
- **动态交叉概率**（`dynamic_probability == 1`），逐对配种计算：
  - 若 `max_child >= avg`：`cxpb = k1 * (max - max_child) / (max - avg)`（下限钳为 `>= 0`）
  - 否则：`cxpb = k3`
- **动态变异概率**，逐个体计算：
  - 若 `fitness >= avg`：`mutpb = k2 * (max - fitness) / (max - avg)`（下限钳为 `>= 0`）
  - 否则：`mutpb = k4`
- **常量：** `k1=0.85, k2=0.5, k3=1.0, k4=0.05`。
- **精英保留 / 重插入：** 选择 `2 * npop`（其中 `npop = 100`）个后代，执行交叉+变异，对失效
  个体重新评估，再用 `tools.selBest(offspring, npop)` 保留最优。
- **动态早停**（`dynamic_stop=True`）：当当前代 `std <= 1e-10`（种群已收敛）
  时立即返回，节省运行时间。

`cxpb`/`mutpb`/`mu`/`lambda_` 仍保留 4.x 的可配置参数；启用动态概率后，每次交叉/变异会在
这些初始值基础上动态调整。

## 何时选择哪种优化器

- **穷举（`run_bf_optimization`）**——中小搜索空间，需要在网格内得到保证的全局最优时使用。
- **遗传算法（`run_ga_optimization`）**——大搜索空间、穷举过慢时使用；用完整性换取速度。动态
  概率 + 早停在一定时间成本下提升收敛质量与鲁棒性。

## 安全修改指南

- 保持 `creator.create(...)` 在模块级且幂等——重复创建 `FitnessMax`/`Individual` 会在导入时
  报错。
- 保持 `run_ga_optimization` 默认返回结果列表，避免破坏 4.x 调用方；需要收敛记录时使用
  `return_logbook=True`。
- 传入 `Pool` 的对象必须可 pickle（`evaluate_func`/`key_func` 及其闭包）。请保持它们便于在
  顶层使用。
- 通过 `k1..k4` 常量、`std` 早停阈值，以及 `population_size`/`ngen_size` 来调节动态行为；
  任何改动请在提交说明中记录（`[Mod]` 前缀）。
- 修改后请做冒烟测试：导入该模块，用平凡的 `evaluate_func`/`key_func` 跑一次极小规模优化，
  确认能收敛并返回 logbook。
