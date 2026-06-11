# Design — Project Steering & Skills

## Overview

We will produce two classes of Kiro context artifacts inside the repository's
`.kiro/` directory, derived from analysis of the `dev-ga` branch source:

```
.kiro/
├── specs/
│   └── project-steering-and-skills/   # this spec (requirements/design/tasks)
├── steering/
│   ├── product.md          # what vn.py is, capabilities, users
│   ├── tech.md             # languages, deps, build/lint commands
│   ├── structure.md        # repo layout + event-driven architecture
│   └── code-style.md       # conventions, commit/PR rules, flake8
└── skills/
    ├── ga-optimization/SKILL.md       # dev-ga GA optimizer guide
    ├── gateway-development/SKILL.md    # BaseGateway implementation guide
    └── cta-strategy/SKILL.md           # strategy + backtesting/optimization
```

## Steering — design decisions

Steering is **always loaded**, so each file is kept concise and factual. We follow
the conventional Kiro trio (product / tech / structure) plus a `code-style.md` because
the codebase has clear, repeatable conventions (dataclasses, `vt_*` ids, `[Mod]` commits).

### product.md
Sourced from `README.md` and `setup.py` docstring. Captures: open-source event-driven
framework; capability areas (`vnpy.trader`, `vnpy.gateway`, `vnpy.app`, `vnpy.chart`,
`vnpy.database`, `vnpy.rpc`); target users (institutions, professional traders).

### tech.md
Sourced from `setup.py`, `requirements.txt`, `.flake8`, `.github/workflows/pythonapp.yml`.
Captures: Python 3.7, C++17 native extensions built via setuptools `Extension`, the
`VNPY_BUILD_*` / `VNPY_BUILD_PARALLEL` env flags, dependency list, and flake8 lint command.

### structure.md
Sourced from the `vnpy/` tree and `trader/` core. Captures: package map; the
`EventEngine` publish/subscribe model and event-type strings; the dataclass data model
(`TickData`, `OrderData`, ... with `vt_symbol`/`vt_orderid` composite ids); and how
`MainEngine.add_gateway`/`add_app`/`add_engine` wire components together.

### code-style.md
Sourced from observed code + `.flake8` + git history + PR template. Captures: 4-space
indentation, type hints everywhere, `@dataclass` for data, triple-quote docstrings
(often empty `""""""` placeholders), `vt_*` id construction in `__post_init__`, Chinese
log/user strings, `[Mod]`/`[Add]`/`[Del]`/`[Fix]` commit prefixes, and the small-PR rule.

## Skills — design decisions

Each skill is a directory with a `SKILL.md` that begins with YAML frontmatter:

```yaml
---
name: <skill-name>
description: <when Kiro should load this skill>
---
```

The `description` is written so Kiro can decide when to activate it (trigger keywords +
intent). Body content stays task-focused.

### ga-optimization (the dev-ga centerpiece)
Explains `vnpy/trader/optimize.py`: `OptimizationSetting`, `check_optimization_setting`,
`run_bf_optimization`, and especially `run_ga_optimization` + the nested `GA_accuracy`.
Documents the deap toolbox wiring, the dynamic crossover probability
`cxpb = k1*(max-child)/(max-avg)` and dynamic mutation probability
`mutpb = k2*(max-fitness)/(max-avg)` with constants `k1=0.85, k2=0.5, k3=1.0, k4=0.05`,
the elite retention (`selBest`), the dynamic early-stop when `std <= 1e-10`, the
multiprocessing `Manager().dict()` result cache keyed by parameter tuple, and the
`(results, logbook)` return contract. Includes a guidance section on safe extension.

### gateway-development
Distills `BaseGateway`'s docstring contract: implement abstract methods (`connect`,
`close`, `subscribe`, `send_order`, `cancel_order`, `query_account`, `query_position`;
optional `query_history`, `send_quote`); fire `on_tick/on_trade/on_order/on_position/
on_account/on_contract`; declare `default_setting` and `exchanges`; respect thread-safety,
non-blocking, auto-reconnect, and copy-before-push rules; use `LocalOrderManager` when the
venue needs local order ids.

### cta-strategy
Explains that strategy/backtesting apps ship as separate `vnpy_*` packages re-exported by
`vnpy/app/<name>/__init__.py`, and ties strategy optimization back to the `OptimizationSetting`
+ `key_func` + brute-force/GA pattern, with guidance on when to use each optimizer.

## Out of scope
- No source code changes to `vnpy/` itself.
- No new dependencies. Documentation/context artifacts only.
