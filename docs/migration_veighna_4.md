# 迁移到 VeighNa/vn.py 4.x

本文记录当前分支迁移到 VeighNa/vn.py 4.x 的执行边界。目标版本为 `vnpy==4.4.0`。

## 结论

不要在 2.4.0 代码树上逐个改依赖来“原地升级”。4.x 已经把大量网关、应用、数据库和数据服务拆成独立的 `vnpy_*` 包，核心仓库结构也从 `setup.py` 迁移到 `pyproject.toml`。

当前分支已经同步到 upstream `4.4.0` 基线，并保留 `.kiro`、迁移说明、`requirements-veighna4.txt`、`examples/veighna4/run.py` 和 `scripts/check_veighna4_env.py`。旧仓库内的 `vnpy/gateway/*`、`vnpy/app/*`、`vnpy/api/*`、`vnpy/database/*` 已按 4.x 模块边界移除。

`dev-ga` 的 GA 优化器定制已移植到 4.4.0 的 `vnpy/trader/optimize.py`：动态交叉/变异概率和动态早停默认开启；默认返回值保持 4.x 的 `list[tuple]`，需要旧分支的收敛记录时传入 `return_logbook=True`。

## 版本与依赖变化

旧分支：

- `vnpy/__init__.py` 为 `2.4.0`
- Python 目标版本为 `3.7`
- GUI 使用 `PyQt5==5.14.1`
- 构建入口为 `setup.py`
- 大量网关/API 二进制随仓库分发

4.4.0：

- Python 目标版本为 `>=3.10`，官方 README 推荐 Python 3.13
- GUI 改为 `PySide6==6.8.2.1`
- 构建入口为 `pyproject.toml` + `hatchling`
- 核心包只保留 `vnpy.event`、`vnpy.trader`、`vnpy.chart`、`vnpy.rpc`、`vnpy.alpha`
- CTP、CTA、数据库等组件通过独立包安装，如 `vnpy_ctp`、`vnpy_ctastrategy`、`vnpy_sqlite`

## Mac mini M4 建议环境

优先用原生 arm64 Python 3.13：

```bash
conda create -n veighna4 python=3.13
conda activate veighna4
python -m pip install -U pip setuptools wheel
python -m pip install -r requirements-veighna4.txt
python scripts/check_veighna4_env.py
python examples/veighna4/run.py
```

如果 `ta-lib` 安装失败，先安装系统 C 库：

```bash
brew install ta-lib
python -m pip install ta-lib
```

如果需要 CTP 网关：

```bash
python -m pip install vnpy_ctp==6.7.11.4
```

若 macOS 上没有匹配 wheel，需要从 `https://github.com/vnpy/vnpy_ctp` 获取源码并本地编译。

## 已执行的代码迁移

1. 从 `upstream` 拉取官方 `4.4.0` 标签。
2. 用 4.4.0 的 `vnpy/`、`pyproject.toml`、README、安装脚本、docs、examples 和 tests 替换旧 2.4.0 基线。
3. 删除旧的内置网关/API/应用/数据库目录，避免旧实现遮蔽新的独立包。
4. 将旧示例里的导入方式迁移为独立包导入：

```python
from vnpy_ctp import CtpGateway
from vnpy_ctastrategy import CtaStrategyApp
```

5. 将 `dev-ga` 优化器定制移植到 4.x API：

```python
results = run_ga_optimization(evaluate_func, setting, key_func)
results, logbook = run_ga_optimization(
    evaluate_func,
    setting,
    key_func,
    return_logbook=True,
)
```

6. 更新 `.kiro/steering` 与技能文件，使它们以 4.x 的模块边界为准。

## 验证命令

```bash
python scripts/check_veighna4_env.py
python -c "import vnpy; print(vnpy.__version__)"
python examples/veighna4/run.py
```

## 后续需要人工复核的定制

- `.kiro/`：已更新到 4.x 方向，但可继续细化。
- `dev-ga`：已完成基础移植，仍建议用真实 CTA 回测任务确认收敛质量。
- UI 改动：`remove question button on QDialog` 需要对照 4.x 的 PySide6 UI 代码重新判断是否仍然需要。
- UFT 网关：4.x 网关拆为独立包，不能继续依赖旧仓库里的 `vnpy/gateway/uft`。
