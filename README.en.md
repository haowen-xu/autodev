English | [中文](./README.md)

# autodev

`autodev` is an automated development workflow orchestrator. It drives a multi-agent loop of `plan -> dev -> review -> arbitrator -> merge` until quality gates pass and changes are merged.

## Overview

- Input: one plan file (`-P/--plan-file`).
- Output: derived checklist files (`*.plan.md`, `*.dev.md`, `*.review.md`) and logs (`*.log`).
- Execution: calls `codex exec` with thread resume, timeout, and retry support.
- Git support: optional `worktree` mode with automated commit/merge/push flow.

## Usage

### Install (local dev)

```bash
pip install -e .
```

### Help

```bash
autodev --help
```

### Basic run

```bash
autodev -P docs/feature.md
```

### Common options

- `-P, --plan-file`: plan file path (required).
- `-T, --work-tree`: run in isolated `git worktree`.
- `--merge/--no-merge`: in worktree mode, merge branch back to main or not.
- `--push/--no-push`: push after success or not.
- `--dry-run`: print commands/prompts only.
- `--max-plan-iteration`: max plan loop count.
- `-M, --max-iteration`: max outer dev-review loop count.
- `--max-dev-iteration`: max dev loop count per outer round.
- `--max-review-iteration`: max review loop count per outer round.
- `--max-arbitration-iteration`: max arbitration rounds.

## Main Loop

The runtime loop is aligned with implementation:

1. Plan stage
- If `*.plan.md` does not exist, run plan iterations until `全部计划工作已完成`.
- Generate initial `*.dev.md` and `*.review.md` from `*.plan.md` if missing.

2. Dev-review stage
- Dev agent implements and updates `*.dev.md`.
- Review agent validates independently and updates `*.review.md` with one of:
  - `审查通过`
  - `审查不通过`
  - `审查未完成`

3. Arbitration stage
- Triggered when review requests arbitration or conflict streak is detected.
- Arbitrator can rewrite dev/review checklists and returns:
  - `仲裁者认为开发完成`
  - `仲裁者认为需要继续开发`

4. Merge stage
- After passing review, merge stage performs commit/merge/push based on CLI flags.
