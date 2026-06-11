---
inclusion: always
---

# Technology Stack

## Languages & runtime

- **Python 3.7** is the supported/target version (see `setup.py` classifiers and the
  GitHub Actions workflow). Avoid syntax/features newer than 3.7.
- **C++17** for native API extensions under `vnpy/api/*` (built via setuptools
  `Extension`). Windows uses pre-built `.pyd` (Python 3.7 only); Linux compiles the
  extensions; macOS ships no native extensions by default.

## Key dependencies

- **GUI:** PyQt5 (pinned `5.14.1`), pyqtgraph, qdarkstyle, QScintilla.
- **Data/Compute:** numpy, pandas, ta-lib, matplotlib, seaborn, plotly.
- **Optimization:** `deap` (genetic algorithm), Python `multiprocessing` /
  `concurrent.futures` for parallel runs.
- **Persistence:** peewee (ORM), pymysql, psycopg2 (PostgreSQL), mongoengine, influxdb.
- **Networking/IO:** requests, websocket-client, pyzmq (RPC), quickfix.
- **Data feeds / broker SDKs:** rqdatac, futu-api, tigeropen, ibapi, and many `vnpy_*`
  gateway/app packages listed in `requirements.txt`.

> Note: most gateways and apps are distributed as **separate `vnpy_*` packages**
> (e.g. `vnpy_ctp`, `vnpy_ctastrategy`). The in-repo `vnpy/app/<name>/__init__.py`
> simply re-exports the installed package via `sys.modules`.

## Build / install / lint commands

```bash
# Install dependencies
pip install -r requirements.txt

# Install vn.py (compiles C++ extensions on Linux)
pip install .            # or: python setup.py install
# Helper scripts also exist: install.sh / install_osx.sh / install.bat

# Lint (CI uses flake8). Hard-fail on real errors, warn otherwise:
flake8 . --count --select=E9,F63,F7,F82 --show-source --statistics
flake8 . --count --exit-zero --max-complexity=10 --max-line-length=127 --statistics
```

## Build environment flags

`setup.py` reads environment variables to control native extension builds:

- `VNPY_BUILD_sgit`, `VNPY_BUILD_ksgold`, `VNPY_BUILD_ROHON` — set to `'1'` to include
  or `'0'` to exclude the corresponding C++ extension module.
- `VNPY_BUILD_PARALLEL` — `'auto'` (use all CPUs), `'no'`, or an integer worker count
  to parallelize the extension build.

## CI

GitHub Actions (`.github/workflows/pythonapp.yml`) runs on `windows-latest` with
Python 3.7: installs deps (including TA-Lib/quickfix/ibapi wheels) and runs flake8.
Keep `flake8` clean for `E9,F63,F7,F82` (syntax errors, undefined names).
