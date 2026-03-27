[English](./README.en.md) | 中文

# autodev

`autodev` 是一个自动化开发流程编排工具。它通过 `plan -> dev -> review -> arbitrator -> merge` 的闭环循环，驱动多代理协作，直到任务通过质量门禁并完成合并。

## 概述

- 输入：一个计划文件（`-P/--plan-file`）。
- 输出：派生的计划与检查清单文件（`*.plan.md`, `*.dev.md`, `*.review.md`）以及日志（`*.log`）。
- 执行方式：调用 `codex exec`（支持上下文续跑、超时与重试）。
- Git 支持：可选 `worktree` 模式，支持自动提交、合并与推送。

## 用法

### 安装（本地开发）

```bash
pip install -e .
```

### 查看帮助

```bash
# 始终可用（推荐）
python -m autodev --help

# 若当前环境 PATH 已包含对应 venv/bin
autodev --help
```

### 基本执行

```bash
# 始终可用（推荐）
python -m autodev -P docs/feature.md

# 若 autodev 命令可用
autodev -P docs/feature.md
```

若 `pip install -e .` 后仍提示 `autodev: command not found`，通常是当前 shell 没有把安装环境的 `bin` 目录加入 `PATH`。可优先使用 `python -m autodev` 启动，或切换到正确的虚拟环境后再执行 `autodev`。

### 常见参数

- `-P, --plan-file`：计划文件路径（必填）。
- `-T, --work-tree`：启用独立 `git worktree`。
- `--merge/--no-merge`：worktree 模式下是否把分支合并回主分支（默认 `--merge`）。
- `--push/--no-push`：流程结束后是否自动推送。
- `--dry-run`：仅打印将执行的命令与提示词。
- `--max-plan-iteration`：计划阶段最大循环次数。
- `--max-iteration`：开发-审查外层循环次数。
- `--max-dev-iteration`：单轮开发最大连续次数。
- `--max-review-iteration`：单轮审查最大连续次数。
- `--max-arbitration-iteration`：仲裁最大轮次。

## 主循环

主循环与代码实现保持一致：

1. 计划阶段
- 若不存在 `*.plan.md`，进入 plan 循环，直到输出“全部计划工作已完成”。
- 由 `*.plan.md` 派生初始 `*.dev.md` 与 `*.review.md`（若已存在则保留）。

2. 开发-审查阶段
- dev 代理按清单实现、验证并更新 `*.dev.md`。  
  当 dev agent 回答末尾为 `还需要继续开发` 时，不是终态，会继续 dev 内层循环（最多 `--max-dev-iteration` 次，默认 `100`）；当回答末尾为 `所有开发已完成` 才进入 review。
- review 代理独立验收并更新 `*.review.md`，结果为：
  - `审查通过`
  - `审查不通过`
  - `审查未完成`
  - `审查发现需要仲裁者`
  其中 `审查未完成` 不是终态：会在当前开发轮次内继续 review 内层循环（最多 `--max-review-iteration` 次，默认 `5`）。

3. 仲裁阶段
- 当 review 输出 `审查发现需要仲裁者` 或系统检测连续冲突时，进入 arbitrator。
- 仲裁者可重写 dev/review 清单，并输出：
  - `仲裁者认为开发完成`
  - `仲裁者认为需要继续开发`

4. 合并阶段
- 审查通过后，进入 merge 阶段执行提交/合并/推送（取决于参数）。

## 目录结构

```text
autodev/
  __init__.py
  __main__.py
  cli.py
  orchestrator.py
  plan.py
  dev.py
  review.py
  arbitrator.py
  merge.py
  runner.py
  codex_io.py
  context.py
  checklists.py
  git_tools.py
  logging_utils.py
  constants.py
```
