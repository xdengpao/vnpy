---
name: vnpy-development
description: Project-specific development guidance for VeighNa/vn.py 4.4.0. Use when Codex works in this repository on the Python trading core, event engine, MainEngine/OMS, gateways, cryptocurrency compatibility APIs, Alpha module, chart/RPC/UI code, CTA/backtesting workflows through vnpy_* packages, GA optimization in vnpy/trader/optimize.py, migration docs, tests, packaging, CI, or project steering/spec files.
---

# vn.py Development

## Overview

Use this skill to make repository changes without rediscovering the 4.x migration boundaries, event-driven architecture, and trading-system safety rules.

## Startup Context

Before feature work or non-trivial code changes:

1. Inspect `git status --short` and preserve user changes.
2. Read the smallest relevant code slice before changing behavior.
3. For broad or unfamiliar changes, read `.kiro/steering/product.md`, `.kiro/steering/tech.md`, `.kiro/steering/structure.md`, and `.kiro/steering/code-style.md`.
4. Read `references/project-map.md` when the task needs concrete file routing, extension recipes, or validation commands.
5. Check `.kiro/skills/` before CTA, gateway, or GA optimization work.
6. Prefer actual source and `pyproject.toml` over older migration/spec text if they conflict.

Briefly confirm the relevant architecture understanding to the user after reading broad context.

## Choose Workflow

For new features or complex behavior changes, ask the user to choose:

- **Spec mode**: Requirements -> Design -> Tasks. Use for new framework features, trading behavior changes, gateway/API boundary changes, migration work, or multi-module changes where traceability matters.
- **Vibe mode**: Direct implementation. Use for small fixes, focused refactors, narrow tests, documentation cleanup, and quick improvements.

If the user explicitly asks for direct implementation or the change is clearly small, proceed in Vibe mode without blocking on a workflow question.

## Spec Mode

Create a folder under `.kiro/specs/` named with English kebab-case, such as `gateway-order-routing-fix`.

Generate these files in order, asking for confirmation after each major document:

1. `requirements.md`
   - Background and feature summary
   - Glossary if needed
   - Numbered requirements with user stories and SHALL/WHEN/IF-THEN acceptance criteria

2. `design.md`
   - Overview and design principles
   - Mermaid architecture diagram when useful
   - Technical implementation plan with files, classes, functions, API contracts, and data structures
   - Compatibility, migration, exchange behavior, and testing notes

3. `tasks.md`
   - Phased task list
   - Use `- [ ]` checkboxes
   - Keep tasks independently verifiable

After all three documents are complete, ask whether to execute tasks, cross-check the docs against existing code, or stop after documentation. When executing tasks, update `tasks.md` to `- [x]` as each task completes. If a task cannot pass review after retries, mark it `- [!]` with the failure reason.

## Vibe Mode

Implement directly without creating spec documents. Keep changes focused, follow existing architecture, and validate with the narrowest meaningful checks.

## Project Shape

- Current baseline is VeighNa/vn.py `4.4.0`; package name is `vnpy`; Python support is `>=3.10` and CI uses Python 3.13.
- Core runtime is event-driven: `vnpy/event/engine.py` dispatches `Event` objects; `vnpy/trader/engine.py` wires `MainEngine`, `OmsEngine`, gateway instances, apps, and function engines.
- Trading data objects live in `vnpy/trader/object.py` as dataclasses. Derived IDs such as `vt_symbol`, `vt_orderid`, and `vt_accountid` are computed in `__post_init__`.
- Gateways implement `BaseGateway` from `vnpy/trader/gateway.py` and push immutable data through `on_*` callbacks.
- In 4.x, most apps, data services, databases, and production gateways are independent `vnpy_*` packages. Do not reintroduce old 2.x in-tree app/database layouts.
- This repository keeps `vnpy.api.rest`, `vnpy.api.websocket`, and selected cryptocurrency gateways as compatibility code.
- GA optimization customizations live in `vnpy/trader/optimize.py`, including dynamic crossover/mutation probability, dynamic stop, and optional `logbook` return.

## Task-Specific Recipes

Check these before implementing related work:

- CTA strategy, backtesting, or parameter optimization: `.kiro/skills/cta-strategy/SKILL.md`
- Gateway or exchange connector work: `.kiro/skills/gateway-development/SKILL.md`
- GA optimization, `deap`, `OptimizationSetting`, or `run_ga_optimization`: `.kiro/skills/ga-optimization/SKILL.md`

## Code Quality Review

After generating or modifying code, self-review for:

- No API keys, private keys, account secrets, or real trading credentials in the repo.
- No tests that place real orders or require live exchange side effects unless the user explicitly asks for integration testing.
- Correct `BaseGateway` semantics: thread-safe, non-blocking methods; automatic reconnect where applicable; `copy.copy(...)` before pushing cached mutable data.
- Backend data contracts use existing enums from `vnpy/trader/constant.py` and dataclasses from `vnpy/trader/object.py`.
- 4.x package boundaries remain intact: use independent `vnpy_*` packages for new apps/gateways unless maintaining the existing crypto compatibility layer.
- `run_ga_optimization` keeps its default list return; use `return_logbook=True` for `(results, logbook)`.
- User-facing logs/messages follow nearby language style, usually Chinese via `_()` where localization is already used. Identifiers, API names, and JSON fields stay English.
- Public API, examples, docs, and tests stay synchronized when behavior changes.

If review fails, fix issues and review again. If it still fails, fix and review one more time. On a third failure, report unresolved issues clearly; in Spec mode, mark the task `- [!]`.

## Validation

Use targeted checks first:

```bash
python scripts/check_veighna4_env.py
python -m pytest tests/alpha/test_dataproxy.py
python -m pytest tests/test_alpha101.py
ruff check .
mypy vnpy
uv build
```

Run the full CI-equivalent path before handoff when touching shared contracts, packaging, or broad framework behavior:

```bash
python -m pip install -e .[alpha,dev]
ruff check .
mypy vnpy
python -m pytest tests
uv build
```

## Known Sharp Edges

- Do not treat older 2.x examples or spec text as authoritative for 4.x code. Prefer `pyproject.toml`, `docs/migration_veighna_4.md`, and actual source.
- `PySide6` is the 4.x UI dependency; avoid adding new `PyQt5` assumptions.
- `ta-lib` may require OS-level installation, especially on macOS Apple Silicon.
- `multiprocessing` uses spawn in optimization paths; keep functions passed to workers top-level and pickleable.
- Crypto compatibility imports remain in-tree, but real exchange API behavior must be reverified before live trading.
