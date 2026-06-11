---
inclusion: always
---

# 技术栈

## 语言与运行时

- **Python 3.7** 是受支持的目标版本（见 `setup.py` 的 classifiers 与 GitHub Actions
  工作流）。请勿使用高于 3.7 的语法/特性。
- **C++17** 用于 `vnpy/api/*` 下的原生 API 扩展（通过 setuptools `Extension` 构建）。
  Windows 使用预编译的 `.pyd`（仅限 Python 3.7）；Linux 现场编译扩展；macOS 默认不附带
  原生扩展。

## 关键依赖

- **图形界面：** PyQt5（锁定 `5.14.1`）、pyqtgraph、qdarkstyle、QScintilla。
- **数据/计算：** numpy、pandas、ta-lib、matplotlib、seaborn、plotly。
- **优化：** `deap`（遗传算法），以及 Python `multiprocessing` / `concurrent.futures`
  用于并行运行。
- **持久化：** peewee（ORM）、pymysql、psycopg2（PostgreSQL）、mongoengine、influxdb。
- **网络/IO：** requests、websocket-client、pyzmq（RPC）、quickfix。
- **数据源 / 券商 SDK：** rqdatac、futu-api、tigeropen、ibapi，以及 `requirements.txt`
  中列出的众多 `vnpy_*` 网关/应用包。

> 注意：大多数网关与应用以**独立的 `vnpy_*` 包**分发（如 `vnpy_ctp`、`vnpy_ctastrategy`）。
> 仓库内的 `vnpy/app/<name>/__init__.py` 仅通过 `sys.modules` 重新导出已安装的包。

## 构建 / 安装 / 代码检查命令

```bash
# 安装依赖
pip install -r requirements.txt

# 安装 vn.py（在 Linux 上会编译 C++ 扩展）
pip install .            # 或：python setup.py install
# 也提供辅助脚本：install.sh / install_osx.sh / install.bat

# 代码检查（CI 使用 flake8）。真正的错误硬性失败，其余仅警告：
flake8 . --count --select=E9,F63,F7,F82 --show-source --statistics
flake8 . --count --exit-zero --max-complexity=10 --max-line-length=127 --statistics
```

## 构建环境变量

`setup.py` 通过环境变量控制原生扩展的构建：

- `VNPY_BUILD_sgit`、`VNPY_BUILD_ksgold`、`VNPY_BUILD_ROHON`——设为 `'1'` 包含、`'0'`
  排除对应的 C++ 扩展模块。
- `VNPY_BUILD_PARALLEL`——`'auto'`（使用全部 CPU）、`'no'`，或一个整数表示并行编译的
  worker 数量。

## 持续集成（CI）

GitHub Actions（`.github/workflows/pythonapp.yml`）在 `windows-latest` + Python 3.7
上运行：安装依赖（含 TA-Lib/quickfix/ibapi 的 wheel）并执行 flake8。请保持
`E9,F63,F7,F82`（语法错误、未定义名称）始终为零。
