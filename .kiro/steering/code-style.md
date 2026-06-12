---
inclusion: always
---

# 代码风格与约定

请遵循代码库中已有的约定，使改动风格统一并通过 CI。

## Python 约定

- **缩进：** 4 个空格；禁止使用 Tab。
- **处处使用类型标注。** 函数对参数与返回值进行标注；局部变量也经常标注
  （如 `settings: List[Dict] = ...`）。请与上下文的标注密度保持一致。
- **数据对象使用 `@dataclass`** 并带默认值，在 `__post_init__` 中计算派生字段
  （`vt_symbol`、`vt_orderid` ...）。新增行情/账户数据时继承 `BaseData`。
- **固定取值集合使用枚举**（`Direction`、`Offset`、`Status`、`Exchange`、`OrderType`、
  `Interval` ...），定义在 `vnpy/trader/constant.py`。枚举的*值*通常是中文显示字符串
  （如 `LONG = "多"`）；代码中使用枚举成员，仅在显示/序列化时使用 `.value`。
- **抽象基类**（`ABC` + `@abstractmethod`）定义插件契约（`BaseGateway`、`BaseApp`、
  `BaseEngine`）。新增网关/应用时继承这些基类。
- **文档字符串：** 模块/类/方法的 docstring 使用三引号。本代码库中常见空的占位 docstring
  `""""""`（用于简单方法）——可以接受，但对非平凡逻辑建议补充一行真实说明。
- **面向用户/日志的字符串通常为中文**（如 `output("优化目标未设置")`）。新增的用户/日志
  信息请与所在模块的语言保持一致。
- 与系统其余部分通过**事件**与 **OMS** 通信，不要直接深入其他组件内部。

## 代码检查（flake8）

配置见 `.flake8`：

- 排除：`venv, build, __pycache__, __init__.py, ib, talib, uic`。
- 忽略：`E501`（行过长——由 black 处理）与 `W503`（二元运算符前换行）。
- CI 对 `E9, F63, F7, F82`（语法错误 / 未定义名称）硬性失败，请始终保持为零。软性检查使用
  `--max-complexity=10 --max-line-length=127`。

## 提交信息

使用已有的方括号前缀约定（见 `git log`）：

- `[Add]` 新功能/模块，`[Mod]` 修改/改进，`[Fix]` 缺陷修复，`[Del]` 删除。
  示例：`[Mod] use accuracy function for ga algorithm`。
- 主题简短、使用祈使语气；提交主题以英文为标准。

## 拉取请求（PR）

参见 `.github/PULL_REQUEST_TEMPLATE.md`：

- 每个 PR 保持**小而专注**；复杂改动拆分为多个 PR。
- 用编号列出具体改动，并用 `Close #<编号>` 关联相关 issue。
- 切勿直接推送到 `master`（或 `dev-ga`）；提交 PR 以供评审。
