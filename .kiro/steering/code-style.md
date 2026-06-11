---
inclusion: always
---

# Code Style & Conventions

Follow the conventions already present in the codebase so changes blend in and pass CI.

## Python conventions

- **Indentation:** 4 spaces; no tabs.
- **Type hints everywhere.** Functions annotate parameters and return types; local
  variables are frequently annotated too (e.g. `settings: List[Dict] = ...`). Match the
  surrounding density of hints.
- **Data objects use `@dataclass`** with defaults, and compute derived fields
  (`vt_symbol`, `vt_orderid`, ...) inside `__post_init__`. Add new market/account data
  by subclassing `BaseData`.
- **Enums for fixed vocabularies** (`Direction`, `Offset`, `Status`, `Exchange`,
  `OrderType`, `Interval`, ...) in `vnpy/trader/constant.py`. The enum *value* is often a
  Chinese display string (e.g. `LONG = "多"`); use the enum member in code and rely on
  `.value` only for display/serialization.
- **Abstract base classes** (`ABC` + `@abstractmethod`) define plugin contracts
  (`BaseGateway`, `BaseApp`, `BaseEngine`). New gateways/apps subclass these.
- **Docstrings:** module/class/method docstrings use triple quotes. Empty placeholder
  docstrings `""""""` are common in this codebase for trivial methods — acceptable, but
  prefer a real one-line description for non-trivial logic.
- **User-facing/log strings are typically Chinese** (e.g. `output("优化目标未设置")`).
  Keep new user/log messages consistent with the local module's language.
- Communicate with the rest of the system through **events** and the **OMS**, not by
  reaching into other components directly.

## Linting (flake8)

Config in `.flake8`:

- Excludes: `venv, build, __pycache__, __init__.py, ib, talib, uic`.
- Ignores: `E501` (line too long — handled by black) and `W503` (line break before
  binary operator).
- CI hard-fails on `E9, F63, F7, F82` (syntax errors / undefined names). Always keep
  these clean. The soft pass uses `--max-complexity=10 --max-line-length=127`.

## Commit messages

Use the existing bracketed-prefix convention (see `git log`):

- `[Add]` new feature/module, `[Mod]` modification/improvement, `[Fix]` bug fix,
  `[Del]` removal. Example: `[Mod] use accuracy function for ga algorithm`.
- Keep the subject short and imperative; English is standard for commit subjects.

## Pull requests

Per `.github/PULL_REQUEST_TEMPLATE.md`:

- Keep each PR **small and focused**; split complex changes into multiple PRs.
- List the concrete changes (numbered) and reference the related issue with `Close #<n>`.
- Never push directly to `master` (or `dev-ga`); open a PR for review.
