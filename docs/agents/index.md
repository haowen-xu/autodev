# Agent 需知（工作区约定）

## 1. 目标

在本仓库内以可复现、可回溯方式完成开发任务，优先保证正确性、可维护性和可验证性。

## 2. 文档阅读顺序

1. 本文档 `docs/agents/index.md`
2. `docs/agents/spec.md`
3. `docs/agents/engineering.md`
4. `docs/agents/runbook.md`
5. `docs/agents/evals.md`
6. `docs/agents/change-policy.md`

## 3. 项目硬约束

- Python 运行环境优先使用 `.venv`。
- 原始 plan 文件只读，禁止修改输入 plan。
- 所有派生 markdown（`*.plan.md/*.dev.md/*.review.md`）统一写入 `work-dir/<plan_stem>/context/`。
- 非任务要求，不新增散落的临时 markdown 到仓库根目录。
- 执行前后优先保持改动最小化，避免无关重构。

## 4. 目录边界

- 核心流程代码在 `autodev/`。
- 设计与流程文档在 `docs/`。
- 构建与发布配置在 `pyproject.toml` 与根目录文件。

## 5. 默认执行流程

1. 先读计划与需求，明确验收条件。
2. 实施最小必要改动。
3. 运行必要验证（至少语法/导入检查，必要时补充执行示例）。
4. 汇报改动范围、风险与后续动作。
