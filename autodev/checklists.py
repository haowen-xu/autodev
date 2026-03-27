"""Checklist and file-digest helpers."""

from __future__ import annotations

import hashlib
from pathlib import Path


def checklist_stats(path: Path) -> tuple[int, int]:
    try:
        text = path.read_text(encoding="utf-8")
    except OSError:
        return 0, 0
    checked = text.count("- [x]") + text.count("- [X]")
    unchecked = text.count("- [ ]")
    return checked, unchecked


def checklist_all_checked(path: Path) -> bool:
    checked, unchecked = checklist_stats(path)
    return checked > 0 and unchecked == 0


def ensure_agent_checklists(plan_output_file: Path, dev_file: Path, review_file: Path) -> bool:
    if dev_file.exists() and review_file.exists():
        return False
    content = plan_output_file.read_text(encoding="utf-8").strip()
    if not content:
        raise OSError(f"计划输出为空: {plan_output_file}")
    dev_wrapped = (
        "# Dev Checklist\n\n"
        "以下内容由计划代理生成，请开发代理按项推进并维护勾选状态。\n\n"
        f"{content}\n\n"
        "---\n"
        "开发代理维护约束：\n"
        "- 只能在本文件更新开发任务状态与必要问题描述。\n"
        "- 不得修改 review 文件。\n"
    )
    review_wrapped = (
        "# Review Checklist\n\n"
        "以下内容由计划代理生成，请审查代理按项独立核验并维护勾选状态。\n\n"
        f"{content}\n\n"
        "---\n"
        "审查代理维护约束：\n"
        "- 可回写本文件与 dev 文件中的任务状态纠偏。\n"
        "- 必须记录质量门禁执行结果与未通过项证据。\n"
    )
    created = False
    if not dev_file.exists():
        dev_file.write_text(dev_wrapped + "\n", encoding="utf-8")
        created = True
    if not review_file.exists():
        review_file.write_text(review_wrapped + "\n", encoding="utf-8")
        created = True
    return created


def file_digest(path: Path) -> str | None:
    if not path.exists():
        return None
    try:
        return hashlib.sha256(path.read_bytes()).hexdigest()
    except OSError:
        return None
