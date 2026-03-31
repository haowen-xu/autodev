English | [中文](./README.md)

# autodev: Fully Automated Development Workflow

## What is this?

In one line: **you write a requirements doc, it writes the code.**

autodev is a multi-agent collaboration script. Write your feature requirements in a Markdown file, hand it over, and it will automatically:

1. **Plan**: break down your requirements into executable development steps
2. **Dev**: dev agent implements the tasks from the checklist
3. **Review**: review agent independently validates that everything is done correctly
4. **Arbitrate**: if dev and review keep disagreeing, an arbitrator steps in
5. **Merge**: once review passes, commit / merge / push automatically

---

## How it works

### Plan → Dev → Review loop

```
your requirements doc (xxx.md)
        ↓
   [plan agent]  ← breaks requirements into executable steps
        ↓
  ┌─────────────────────────────────────┐
  │  [dev agent]    implements           │
  │       ↕  (disagreement → arbitrator) │
  │  [review agent] validates            │
  └─────────────────────────────────────┘
        ↓ review passed
   [merge]  commit / merge / push
```

**dev and review each maintain their own todo checklist** (items correspond one-to-one), progressing independently.

- dev says "done" → handed to review for validation
- review says "not done" → sent back to dev
- two consecutive disagreements → **arbitrator steps in**

### Arbitrator

The arbitrator is the final judge. It will:

- Read both the dev and review checklists and the points of disagreement
- Either **rewrite both checklists** and send dev back to work
- Or **declare development complete** and proceed to merge

Arbitration runs at most **5 rounds** to prevent infinite loops.

---

## Getting started

### 1. Install

```bash
pip install git+https://github.com/haowen-xu/autodev.git
```

### 2. Prepare your requirements doc

Write a Markdown file in your project describing the feature you want built. See `docs/plans/` for examples.

> **Prerequisite**: your codebase needs a `docs/` documentation structure and an `AGENTS.md` file so the agents can understand your project. Use this project's setup as a reference.

### 3. Run

```bash
# basic usage
autodev -P docs/my-feature.md

# isolated git worktree (recommended: keeps main branch clean, supports parallel runs)
autodev -P docs/my-feature.md -T

# auto-merge the worktree branch back to main when done
autodev -P docs/my-feature.md -T --merge
```

---

## Developing multiple features in parallel

The `-T` flag creates an isolated `git worktree` within the same repository, which means:

- Different features don't interfere with each other
- You can **run multiple autodev processes simultaneously**, each on a different feature
- Add `--merge` to each worktree run to auto-merge back to main when done

---

## Prerequisites

When autodev runs, each agent needs to understand your project. Your codebase should include:

| File/Directory | Purpose |
|---|---|
| `AGENTS.md` | Tells agents what the project is, how to develop it, and what conventions to follow |
| `docs/` | Architecture docs, code style guides, development plans, etc. |

Use this project's `AGENTS.md` and `docs/` as a template.

---

## Common options

| Option | Description |
|---|---|
| `-P, --plan-file` | Path to requirements doc (required) |
| `-T, --work-tree` | Run in an isolated git worktree |
| `-M, --merge` | Merge worktree branch back to main when done |
| `--push` | Push to remote after completion |
| `--dry-run` | Print commands and prompts only, don't execute |
| `--max-arbitration-iteration` | Max arbitration rounds (default: 5) |

Full option list: `autodev --help`

---

## Documentation

- Agent rules & constraints: `docs/agents/index.md`
- Architecture overview: `docs/arch/index.md`
- Python code style: `docs/code-style/python.md`
- Review rules: `docs/review/index.md`
- Orchestrator internals: `docs/highlights/ochestrator.md`
