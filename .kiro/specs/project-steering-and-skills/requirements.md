# Requirements — Project Steering & Skills

## Introduction

This spec defines the work to generate **steering files** and **skills** for the
vn.py (vnpy) quantitative trading framework, based on the `dev-ga` branch.

- **Steering files** (`.kiro/steering/*.md`) provide always-available context about
  the product, technology stack, project structure, and coding conventions so that
  every Kiro interaction is grounded in this project's reality.
- **Skills** (`.kiro/skills/<name>/SKILL.md`) package focused, on-demand workflow
  guides for recurring development tasks in this codebase.

The `dev-ga` branch's defining characteristic is a heavily customized **genetic
algorithm (GA) optimizer** in `vnpy/trader/optimize.py` (dynamic crossover/mutation
probabilities, dynamic early-stopping, multiprocessing, and a `logbook`-returning
accuracy function). The generated artifacts must capture this accurately.

## Requirements

### Requirement 1 — Product steering

**User Story:** As a contributor, I want a product overview so that I understand what
vn.py is, who uses it, and which problems it solves before writing code.

#### Acceptance Criteria

1. WHEN a contributor reads the product steering THEN it SHALL describe vn.py as an
   open-source, Python-based, event-driven quant trading framework.
2. THE product steering SHALL list the major capability areas: trading core, gateways,
   apps, charting, databases, and strategy optimization.
3. THE product steering SHALL note the target users (institutions and professional traders).

### Requirement 2 — Technology steering

**User Story:** As a contributor, I want a tech-stack reference so that I use the
correct languages, dependencies, and build/lint commands.

#### Acceptance Criteria

1. THE tech steering SHALL state the Python version (3.7), the C++17 native extensions,
   and key third-party libraries (PyQt5, numpy, pandas, deap, peewee, ta-lib, etc.).
2. THE tech steering SHALL document the build, install, and lint (flake8) commands.
3. THE tech steering SHALL document the environment build flags (e.g. `VNPY_BUILD_*`).

### Requirement 3 — Structure steering

**User Story:** As a contributor, I want a map of the repository so that I can locate
modules quickly and follow the established layout.

#### Acceptance Criteria

1. THE structure steering SHALL describe the `vnpy/` package layout (event, trader,
   gateway, app, chart, database, rpc, api).
2. THE structure steering SHALL explain the event-driven architecture and core data
   objects (`vt_symbol`, `vt_orderid`, dataclass objects, event types).
3. THE structure steering SHALL explain how gateways and apps plug into `MainEngine`.

### Requirement 4 — Code-style steering

**User Story:** As a contributor, I want coding conventions so that my changes match
the project's existing style and pass CI.

#### Acceptance Criteria

1. THE code-style steering SHALL document naming, type-hinting, dataclass, and docstring
   conventions observed in the codebase.
2. THE code-style steering SHALL document the commit-message convention (`[Mod]`, `[Add]`, etc.)
   and PR guidelines (kept small, link the issue).
3. THE code-style steering SHALL document the flake8 rules that are enforced/ignored.

### Requirement 5 — GA optimization skill

**User Story:** As a developer, I want a skill that explains and guides changes to the
genetic algorithm optimizer so that I can safely extend the `dev-ga` work.

#### Acceptance Criteria

1. THE skill SHALL explain `run_ga_optimization`, `GA_accuracy`, `ga_evaluate`, and the
   `OptimizationSetting` API.
2. THE skill SHALL explain the dynamic crossover/mutation probability formulas and the
   dynamic early-stopping (std threshold) behavior introduced on `dev-ga`.
3. THE skill SHALL describe how results and the `logbook` are returned and consumed.

### Requirement 6 — Gateway development skill

**User Story:** As a developer, I want a skill for implementing a trading gateway so that
new exchange integrations follow `BaseGateway` contracts.

#### Acceptance Criteria

1. THE skill SHALL list the abstract methods that must be implemented and the `on_*`
   callbacks that must be fired.
2. THE skill SHALL document thread-safety, non-blocking, and copy-on-push requirements.
3. THE skill SHALL reference `default_setting`, `exchanges`, and `LocalOrderManager`.

### Requirement 7 — CTA strategy & backtesting skill

**User Story:** As a quant developer, I want a skill for building and optimizing CTA
strategies so that I can use backtesting plus brute-force/GA optimization correctly.

#### Acceptance Criteria

1. THE skill SHALL describe the relationship between vnpy apps (installed as `vnpy_*`
   packages) and the strategy/backtesting workflow.
2. THE skill SHALL show how to define `OptimizationSetting` parameters, targets, and
   `key_func`, and when to choose brute-force vs GA optimization.

### Requirement 8 — Repository placement & review

**User Story:** As the repository owner, I want the artifacts committed in the repo so
that the team shares them.

#### Acceptance Criteria

1. THE artifacts SHALL be created under the repository's `.kiro/` directory.
2. WHEN generation is complete THEN the work SHALL be pushed to a branch and a PR SHALL
   be opened for review (never committed directly to `dev-ga`/`master`).
