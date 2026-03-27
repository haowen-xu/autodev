# autodev 架构概览

`autodev` 通过 `plan -> dev -> review -> arbitrator -> merge` 的循环驱动开发闭环。

## 核心模块

- `autodev/cli.py`: CLI 参数入口。
- `autodev/orchestrator.py`: 主流程调度与状态推进。
- `autodev/plan.py`: 计划阶段 prompt 构造。
- `autodev/dev.py`: 开发阶段 prompt 构造。
- `autodev/review.py`: 审查阶段 prompt 构造。
- `autodev/arbitrator.py`: 仲裁阶段 prompt 构造。
- `autodev/merge.py`: 合并阶段 prompt 构造。
- `autodev/runner.py`: 调用 `codex` 的执行与重试。

## 关键约束

- 原始 plan 文件为只读输入。
- 派生 `.plan/.dev/.review/.log` 统一写入 `work-dir/<plan_stem>/context/`。
- 可选 `-T` 启用 worktree 隔离执行目录。
