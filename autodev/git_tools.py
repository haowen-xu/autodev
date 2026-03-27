"""Git and worktree helpers."""

from __future__ import annotations

import subprocess
from pathlib import Path

from loguru import logger


def setup_worktree(worktree_path: Path, branch_name: str, repo_root: Path | None = None) -> None:
    if worktree_path.exists():
        logger.info("[准备] worktree 已存在: {}", worktree_path)
        return
    worktree_path.parent.mkdir(parents=True, exist_ok=True)
    result = subprocess.run(
        ["git", "worktree", "add", str(worktree_path), "-b", branch_name],
        cwd=repo_root,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        result = subprocess.run(
            ["git", "worktree", "add", str(worktree_path), branch_name],
            cwd=repo_root,
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
