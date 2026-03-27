"""Git and worktree helpers."""

from __future__ import annotations

import subprocess
from pathlib import Path

from loguru import logger


def setup_worktree(worktree_path: Path, branch_name: str) -> None:
    if worktree_path.exists():
        logger.info("[准备] worktree 已存在: {}", worktree_path)
        return
    worktree_path.parent.mkdir(parents=True, exist_ok=True)
    result = subprocess.run(
        ["git", "worktree", "add", str(worktree_path), "-b", branch_name],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        result = subprocess.run(
            ["git", "worktree", "add", str(worktree_path), branch_name],
            capture_output=True,
            text=True,
        )
        if result.returncode != 0:
            logger.error("创建 worktree 失败: {}", result.stderr.strip())
            raise SystemExit(2)
    logger.info("[准备] 已创建 worktree: {}", worktree_path)


def resolve_repo_root() -> Path | None:
    result = subprocess.run(
        ["git", "rev-parse", "--show-toplevel"],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        return None
    return Path(result.stdout.strip()).resolve()


def ensure_clean_and_committed_for_worktree(repo_root: Path, plan_file_input: Path) -> tuple[bool, Path | None]:
    status_result = subprocess.run(
        ["git", "status", "--porcelain"],
        cwd=repo_root,
        capture_output=True,
        text=True,
    )
    if status_result.returncode != 0:
        logger.error("无法检查主工作区状态: {}", status_result.stderr.strip())
        return False, None
    if status_result.stdout.strip():
        logger.error("启用 -T 前要求主工作区干净且提交。检测到未提交改动，请先提交后重试。")
        return False, None

    try:
        relative_plan = plan_file_input.relative_to(repo_root)
    except ValueError:
        logger.error("worktree 模式要求计划文件位于代码库内，当前不在仓库中: {}", plan_file_input)
        return False, None

    head_check = subprocess.run(
        ["git", "cat-file", "-e", f"HEAD:{relative_plan.as_posix()}"],
        cwd=repo_root,
        capture_output=True,
        text=True,
    )
    if head_check.returncode != 0:
        logger.error("启用 -T 前要求计划文件已提交到 HEAD：{}。请先提交后重试。", relative_plan)
        return False, None

    return True, relative_plan
