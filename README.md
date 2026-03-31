[English](./README.en.md) | 中文

# autodev：全自动开发流程编排工具

## 这是什么？

一句话：**你写一个需求文档，它帮你把代码开发完。**

autodev 是一个多智能体协作脚本。你把功能需求写成一个 Markdown 文件，交给它，它会自动：

1. **规划**：把你的需求拆解成一步一步可执行的开发任务
2. **开发**：dev agent 照着任务清单写代码
3. **审查**：review agent 独立验收，检查代码有没有按要求做到位
4. **仲裁**：如果 dev 和 review 反复对不上，仲裁者出面调解
5. **合并**：验收通过后，自动提交、合并、推送

---

## 核心机制

### Plan → Dev → Review 闭环

```
你的需求文档 (xxx.md)
        ↓
   [plan agent]  ← 把需求细化为可执行步骤
        ↓
  ┌─────────────────────────────────────┐
  │  [dev agent]   按清单开发            │
  │       ↕  (disagreement → arbitrator) │
  │  [review agent] 独立审查             │
  └─────────────────────────────────────┘
        ↓ 审查通过
   [merge]  提交 / 合并 / 推送
```

**dev 和 review 各自维护一份 todo 清单**（内容一一对应），互不干扰地推进。

- dev 认为"开发完成"→ 交给 review 验收
- review 认为"没做完"→ 打回给 dev 继续
- 连续两次都对不上 → **仲裁者出场**

### 仲裁者（Arbitrator）

仲裁者是最终裁判。它会：

- 阅读 dev 和 review 双方的清单和分歧
- 要么**改写双方的清单**，让 dev 重新开发
- 要么**判定开发已完成**，跳过争议直接进入合并

仲裁最多进行 **5 轮**，防止死循环。

---

## 快速上手

### 1. 安装

```bash
pip install git+https://github.com/haowen-xu/autodev.git
```

### 2. 准备需求文档

在项目里写一个 Markdown 文件，描述你要开发什么功能。格式可以参考 `docs/plans/` 目录下的示例。

> **前提**：你的代码库需要有 `docs/` 文档体系和 `AGENTS.md` 文件，用来给各个 agent 提供项目上下文。可以参考本项目的写法。

### 3. 运行

```bash
# 基本用法
autodev -P docs/my-feature.md

# 开独立 worktree（推荐：不影响主干，可并行开多个功能）
autodev -P docs/my-feature.md -T

# worktree 完成后自动合并回主分支
autodev -P docs/my-feature.md -T --merge
```

---

## 并行开发多个功能

`-T` 参数会在同一个代码库开一个独立的 `git worktree`，这意味着：

- 不同功能互不干扰
- 可以**同时跑多个 autodev 进程**，并行开发不同 feature
- 每个 worktree 完成后加 `--merge` 自动合并回主干

---

## 前提条件

autodev 运行时，各 agent 需要读懂你的项目。你的代码库应当包含：

| 文件/目录 | 用途 |
|---|---|
| `AGENTS.md` | 告诉 agent 这个项目是什么、怎么开发、有哪些约定 |
| `docs/` | 架构说明、代码规范、开发计划等 |

可以参考本项目的 `AGENTS.md` 和 `docs/` 目录作为模板。

---

## 常用参数速查

| 参数 | 说明 |
|---|---|
| `-P, --plan-file` | 需求文档路径（必填） |
| `-T, --work-tree` | 在独立 git worktree 中运行 |
| `-M, --merge` | worktree 完成后合并回主分支 |
| `--push` | 完成后自动推送到远端 |
| `--dry-run` | 只打印命令和提示词，不实际执行 |
| `--max-arbitration-iteration` | 仲裁最大轮次（默认 5） |

完整参数列表：`autodev --help`

---

## 文档导航

- Agent 规则与约束：`docs/agents/index.md`
- 架构说明：`docs/arch/index.md`
- Python 代码风格：`docs/code-style/python.md`
- 审查规则：`docs/review/index.md`
- Orchestrator 实现细节：`docs/highlights/ochestrator.md`
