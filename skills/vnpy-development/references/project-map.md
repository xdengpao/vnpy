# vn.py Project Map

Use this reference after loading `SKILL.md` when the task needs concrete file locations, extension paths, or validation commands.

## Runtime Flow

`MainEngine` in `vnpy/trader/engine.py` owns an `EventEngine`, starts it, initializes `LogEngine`, `OmsEngine`, `EmailEngine`, and `WechatEngine`, then dynamically registers gateways, apps, and function engines.

Gateway implementations convert external exchange or broker payloads into dataclasses from `vnpy/trader/object.py`, then push events through `BaseGateway.on_tick`, `on_order`, `on_trade`, `on_position`, `on_account`, `on_quote`, `on_contract`, and `on_log`. `OmsEngine` stores the latest ticks, orders, trades, positions, accounts, contracts, and quotes from those events.

## Important Files

| Task area | Files to inspect first |
| --- | --- |
| Project metadata and CI | `pyproject.toml`, `requirements-veighna4.txt`, `.github/workflows/pythonapp.yml`, `scripts/check_veighna4_env.py` |
| Migration context | `docs/migration_veighna_4.md`, `.kiro/steering/*.md` |
| Event system | `vnpy/event/engine.py`, `vnpy/trader/event.py` |
| Main engine and OMS | `vnpy/trader/engine.py`, `vnpy/trader/object.py`, `vnpy/trader/constant.py`, `vnpy/trader/converter.py` |
| Gateway contract | `vnpy/trader/gateway.py`, `.kiro/skills/gateway-development/SKILL.md` |
| Crypto compatibility | `vnpy/api/rest/rest_client.py`, `vnpy/api/websocket/websocket_client.py`, `vnpy/gateway/*/*_gateway.py` |
| App integration | `vnpy/trader/app.py`, examples using `vnpy_ctastrategy`, `vnpy_ctabacktester`, and other `vnpy_*` packages |
| Optimization | `vnpy/trader/optimize.py`, `.kiro/skills/ga-optimization/SKILL.md` |
| Alpha research | `vnpy/alpha/dataset/`, `vnpy/alpha/model/`, `vnpy/alpha/strategy/`, `tests/alpha/`, `tests/test_alpha101.py` |
| Charting and UI | `vnpy/chart/`, `vnpy/trader/ui/`, `vnpy/trader/locale/` |
| RPC | `vnpy/rpc/client.py`, `vnpy/rpc/server.py`, `examples/simple_rpc/` |
| Examples | `examples/veighna4/run.py`, `examples/veighna_trader/`, legacy examples under `examples/cta_backtesting/` and `examples/no_ui/` |

## Extension Recipes

### Modify or add gateway behavior

Read `.kiro/skills/gateway-development/SKILL.md` and `vnpy/trader/gateway.py` first. Preserve the `BaseGateway` contract: methods are thread-safe and non-blocking, connection loss is handled by reconnect logic where applicable, data passed to callbacks is treated as immutable, and cached mutable payloads are copied before callback dispatch.

For exchanges that return system order IDs asynchronously, use `LocalOrderManager` to map local IDs to system IDs, buffer cancellation requests, and replay pending push data when mappings become available.

### Work on CTA strategy, backtesting, or parameter optimization

Read `.kiro/skills/cta-strategy/SKILL.md`. In 4.x, CTA apps come from independent packages such as `vnpy_ctastrategy` and `vnpy_ctabacktester`; core repo changes usually touch shared contracts, examples, docs, or `vnpy/trader/optimize.py`, not old in-tree `vnpy/app` code.

### Work on GA optimization

Read `.kiro/skills/ga-optimization/SKILL.md` and inspect `vnpy/trader/optimize.py`. Keep `evaluate_func` and `key_func` pickleable for spawn-based multiprocessing. Preserve default return type compatibility for `run_ga_optimization`; only return `(results, logbook)` when `return_logbook=True`.

For a quick smoke test, use a tiny `OptimizationSetting`, top-level or otherwise pickleable evaluation functions, low `pop_size`, low `ngen`, and `return_logbook=True`.

### Work on Alpha data/model code

Start in `vnpy/alpha/dataset/utility.py` and nearby dataset functions for expression behavior. Add or update focused tests in `tests/alpha/` or `tests/test_alpha101.py`. Many Alpha paths require optional dependencies from `.[alpha]`.

### Work on UI, charting, or localization

Use PySide6 patterns already in `vnpy/trader/ui/` and charting patterns in `vnpy/chart/`. When adding user-facing strings to localized modules, follow existing `_()` usage and consider whether locale artifacts under `vnpy/trader/locale/` need regeneration.

### Work on docs or examples

Prefer `examples/veighna4/run.py` for 4.x startup behavior. Treat older 2.x examples as migration references unless the task is specifically to update them.

## Validation Matrix

Use the narrowest meaningful command first:

```bash
python scripts/check_veighna4_env.py
python -m pytest tests/alpha/test_dataproxy.py
python -m pytest tests/test_alpha101.py
ruff check .
mypy vnpy
uv build
```

Run a broader set before handoff when touching shared contracts, package metadata, or migration-sensitive behavior:

```bash
python -m pip install -e .[alpha,dev]
ruff check .
mypy vnpy
python -m pytest tests
uv build
```

## Current Implementation Notes

- CI installs Python 3.13 on Windows, installs `ruff`, `mypy`, `uv`, `types-tqdm`, installs `ta-lib` from the vn.py package index, installs `.[alpha,dev]`, then runs `ruff check .`, `mypy vnpy`, and `uv build`.
- `pyproject.toml` is authoritative for build metadata, optional dependencies, ruff settings, and mypy settings.
- `requirements-veighna4.txt` is a migration environment helper and pins common split-out `vnpy_*` packages.
- In-tree crypto APIs and gateways are compatibility code; new non-crypto production gateways should normally live in separate `vnpy_*` packages.
- Avoid tests that hit live broker/exchange endpoints by default. Mock or isolate network clients unless the user requests integration testing.
