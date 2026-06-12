# 需求 — 项目 Steering 与 Skills

## 引言

本 spec 定义为 vn.py（vnpy）量化交易框架生成 **steering 文件**与 **skills** 的工作，基于
`dev-ga` 分支。

- **Steering 文件**（`.kiro/steering/*.md`）提供始终可用的上下文，覆盖产品、技术栈、项目
  结构与编码约定，使每一次与 Kiro 的交互都根植于本项目的真实情况。
- **Skills**（`.kiro/skills/<name>/SKILL.md`）为代码库中反复出现的开发任务打包成聚焦的、
  按需加载的工作流指南。

`dev-ga` 分支的标志性特征是 `vnpy/trader/optimize.py` 中经过大量定制的**遗传算法（GA）
优化器**（动态交叉/变异概率、动态早停、多进程，以及返回 `logbook` 的精度函数）。生成的
内容必须准确刻画这一点。

## 需求

### 需求 1 — 产品 steering

**用户故事：** 作为贡献者，我希望有一份产品概览，以便在写代码前理解 vn.py 是什么、谁在用、
解决了哪些问题。

#### 验收标准

1. 当贡献者阅读产品 steering 时，它应将 vn.py 描述为开源、基于 Python、事件驱动的量化交易
   框架。
2. 产品 steering 应列出主要能力模块：交易内核、网关、应用、图表、数据库与策略优化。
3. 产品 steering 应说明目标用户（机构与专业交易员）。

### 需求 2 — 技术 steering

**用户故事：** 作为贡献者，我希望有一份技术栈参考，以便使用正确的语言、依赖与构建/检查命令。

#### 验收标准

1. 技术 steering 应说明 Python 版本（3.7）、C++17 原生扩展以及关键第三方库（PyQt5、numpy、
   pandas、deap、peewee、ta-lib 等）。
2. 技术 steering 应记录构建、安装与代码检查（flake8）命令。
3. 技术 steering 应记录构建环境变量（如 `VNPY_BUILD_*`）。

### 需求 3 — 结构 steering

**用户故事：** 作为贡献者，我希望有一张仓库地图，以便快速定位模块并遵循既有布局。

#### 验收标准

1. 结构 steering 应描述 `vnpy/` 包布局（event、trader、gateway、app、chart、database、
   rpc、api）。
2. 结构 steering 应解释事件驱动架构与核心数据对象（`vt_symbol`、`vt_orderid`、dataclass
   对象、事件类型）。
3. 结构 steering 应解释网关与应用如何接入 `MainEngine`。

### 需求 4 — 代码风格 steering

**用户故事：** 作为贡献者，我希望有编码约定，以便我的改动与项目既有风格一致并通过 CI。

#### 验收标准

1. 代码风格 steering 应记录代码库中观察到的命名、类型标注、dataclass 与 docstring 约定。
2. 代码风格 steering 应记录提交信息约定（`[Mod]`、`[Add]` 等）与 PR 指南（保持小、关联
   issue）。
3. 代码风格 steering 应记录被强制/忽略的 flake8 规则。

### 需求 5 — GA 优化 skill

**用户故事：** 作为开发者，我希望有一个 skill 来解释并指导对遗传算法优化器的修改，以便我能安全
地扩展 `dev-ga` 的工作。

#### 验收标准

1. 该 skill 应解释 `run_ga_optimization`、`GA_accuracy`、`ga_evaluate` 与
   `OptimizationSetting` API。
2. 该 skill 应解释 `dev-ga` 引入的动态交叉/变异概率公式与动态早停（std 阈值）行为。
3. 该 skill 应描述结果与 `logbook` 如何返回与被使用。

### 需求 6 — 网关开发 skill

**用户故事：** 作为开发者，我希望有一个实现交易网关的 skill，以便新的交易所接入遵循
`BaseGateway` 契约。

#### 验收标准

1. 该 skill 应列出必须实现的抽象方法以及必须触发的 `on_*` 回调。
2. 该 skill 应记录线程安全、非阻塞与推送前复制的要求。
3. 该 skill 应引用 `default_setting`、`exchanges` 与 `LocalOrderManager`。

### 需求 7 — CTA 策略与回测 skill

**用户故事：** 作为量化开发者，我希望有一个构建与优化 CTA 策略的 skill，以便正确使用回测加
穷举/GA 优化。

#### 验收标准

1. 该 skill 应描述 vnpy 应用（以 `vnpy_*` 包安装）与策略/回测工作流之间的关系。
2. 该 skill 应展示如何定义 `OptimizationSetting` 的参数、目标与 `key_func`，以及何时选择穷举
   还是 GA 优化。

### 需求 8 — 仓库放置与评审

**用户故事：** 作为仓库所有者，我希望产物提交进仓库，以便团队共享。

#### 验收标准

1. 产物应创建在仓库的 `.kiro/` 目录下。
2. 当生成完成时，工作应推送到一个分支并开启 PR 以供评审（切勿直接提交到
   `dev-ga`/`master`）。
