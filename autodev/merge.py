"""Merge stage prompt builder."""

from __future__ import annotations

from pathlib import Path


def build_merge_prompt(
    plan_file: Path,
    dev_file: Path,
    push: bool,
    worktree_branch: str | None = None,
    worktree_path: Path | None = None,
    merge_to_main: bool = False,
) -> str:
    steps: list[str] = []
    n = 0

    if worktree_branch and merge_to_main and worktree_path:
        n += 1
        steps.append(
            f"{n}) 先进入 worktree 目录 `{worktree_path}`，git add 所有已修改和新增的文件，\n"
            "   根据计划文件和开发清单生成有意义的 commit message 并 git commit。\n"
            "   若没有待提交的改动，跳过此步。\n"
        )
    else:
        n += 1
        steps.append(
            f"{n}) git add 所有已修改和新增的文件，根据计划文件和开发清单生成有意义的 commit message 并 git commit。\n"
            "   若没有待提交的改动，跳过此步。\n"
        )

    if worktree_branch:
        if merge_to_main:
            n += 1
            steps.append(
                f"{n}) 回到主仓库目录，切换到主分支，执行 git merge `{worktree_branch}`。\n"
                "   若产生合并冲突，逐文件解决后 git add + git commit 完成合并。\n"
                "   合并完成后执行 lint 和测试验证，若失败则修复后再 commit。\n"
            )
            n += 1
            steps.append(
                f"{n}) 合并完成后，在主仓库目录执行 `git worktree remove {worktree_path}` 删除该 worktree。\n"
                "   若提示 worktree 非干净，先确认改动已提交，再清理后重试。\n"
            )
        else:
            n += 1
            steps.append(
                f"{n}) 在当前 worktree 分支 `{worktree_branch}` 上执行 git merge 主分支（git merge main 或 master）。\n"
                "   若产生合并冲突，逐文件解决后 git add + git commit 完成合并。\n"
                "   合并完成后执行 lint 和测试验证，若失败则修复后再 commit。\n"
            )

    if push:
        n += 1
        steps.append(
            f"{n}) 执行 git push。若远程有更新导致 push 失败，先 git pull --rebase 解决冲突后重试。\n"
            "   若 rebase 产生冲突，逐文件解决后 git rebase --continue，确保最终 push 成功。\n"
        )
    else:
        n += 1
        steps.append(f"{n}) 不要执行 git push。\n")

    return (
        "你是合并代理。请将开发改动提交并合并到 git。\n"
        f"- 计划文件（用于生成 commit message）: {plan_file}\n"
        f"- 开发清单（用于生成 commit message）: {dev_file}\n"
        "要求：\n"
        + "".join(steps)
    )
