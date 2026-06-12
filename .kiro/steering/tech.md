---
inclusion: always
---

# 技术栈

## 语言与运行时

- 迁移目标是 **VeighNa/vn.py 4.x**，当前基线版本为 `vnpy==4.4.0`。
- **Python 3.10+** 是 4.x 支持范围；新环境优先使用 **Python 3.13 64 位**。
- 核心包使用 `pyproject.toml` + `hatchling` 构建，不再以旧分支的 `setup.py` 为准。
- C++/柜台 API 扩展大多迁移到独立 `vnpy_*` 包中维护，例如 `vnpy_ctp`。

## 关键依赖

- **图形界面：** PySide6 `6.8.2.1`、pyqtgraph、qdarkstyle。
- **数据/计算：** numpy 2.x、pandas 2.x、ta-lib 0.6.x、plotly、tqdm。
- **优化：** `deap`，以及 Python `multiprocessing` / `concurrent.futures`。
- **日志/网络/IO：** loguru、requests、pyzmq、qrcode。
- **拆分组件：** CTA、回测、数据库、行情源和网关通过独立包安装，例如
  `vnpy_ctastrategy`、`vnpy_ctabacktester`、`vnpy_sqlite`、`vnpy_rqdata`、`vnpy_ctp`。
- **虚拟币兼容层：** 本分支保留旧 `vnpy.api.rest`、`vnpy.api.websocket` 和虚拟币网关子集；
  需要 `pytz`、`websocket-client`，并通过 `vnpy_bybit`、`vnpy_deribit`、`vnpy_okex`
  继续兼容对应独立包入口。

> 迁移期间不要混用 2.x 仓库内的旧 `vnpy/app/*`、`vnpy/database/*` 与 4.x 独立包。
> `vnpy/api` 与 `vnpy/gateway` 仅允许保留虚拟币交易兼容子集，其他新增网关优先使用独立
> `vnpy_*` 包。

## 构建 / 安装 / 代码检查命令

```bash
# 创建 4.x 迁移环境
conda create -n veighna4 python=3.13
conda activate veighna4
python -m pip install -U pip setuptools wheel

# 安装迁移依赖
python -m pip install -r requirements-veighna4.txt
python scripts/check_veighna4_env.py

# 启动新版最小示例
python examples/veighna4/run.py
```

## Mac mini M4 注意事项

- 原生 arm64 路线优先；不要回退到旧分支的 Python 3.7 + PyQt5 路线。
- `ta-lib` 可能需要先执行 `brew install ta-lib`。
- `vnpy_ctp` 如无 macOS wheel，需要从源码本地编译；这要求 GitHub 可访问且本机有编译工具链。

## 迁移边界

- 当前仓库已同步到官方 4.4.0 基线，并保留 `.kiro` 与迁移辅助文件。
- 虚拟币交易 API 和网关入口已作为兼容层保留；实盘前需要按交易所当前 API 做联调。
- `dev-ga` 的动态 GA 定制已移植到 `vnpy/trader/optimize.py`；默认返回列表，传入
  `return_logbook=True` 时返回 `(results, logbook)`。
- 迁移记录见 `docs/migration_veighna_4.md`。
