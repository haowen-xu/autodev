"""Dev agent prompt and result normalization."""

from __future__ import annotations

from pathlib import Path

from .constants import DEV_CONTINUE, DEV_DONE


def build_dev_prompt(
    plan_file: Path,
    dev_file: Path,
    review_file: Path,
    iteration: int,
    max_iteration: int,
) -> str:
    return (
        "你是开发执行代理。请根据计划和开发清单执行开发。\n"
        f"- 计划文件: {plan_file}\n"
        f"- 开发清单: {dev_file}\n"
        f"- 审查清单: {review_file}\n"
        f"- 当前轮次: {iteration}/{max_iteration}\n"
        "要求：\n"
        "1) 读取计划文件、开发清单与审查清单；优先处理审查清单中的未通过问题。\n"
        "   - 原始计划文件只读，严禁任何修改。\n"
        f"   - 审查清单 {review_file} 仅允许读取，严禁任何修改（包括新增、删除、覆盖内容）。\n"
        "2) 完整工作流：开发实现 → lint/格式检查 → 测试验证。\n"
        "3) 可按需执行 git commit（不强制每轮提交）。\n"
        f"4) 完成的任务请在 {dev_file} 中标记为 [x]。\n"
        "   - 必须在原有清单项上就地修改完成状态（[ ] -> [x]），"
        "禁止在 Round 轮次中复制/重写一份新的开发清单。\n"
        "   - 若该任务之前被审查标注过 `问题:`，在确认已完成并打钩后，必须删除对应 `问题:` 描述，避免遗留过期问题。\n"
        "5) 若某一步失败，先修复后重试；给出明确失败原因与后续处理。\n"
        "6) 每轮都必须基于当前代码重新校验完成状态，不得仅依赖历史状态。\n"
        "7) 回答中简要说明本轮完成了哪些任务，并包含执行的 lint/测试命令与提交信息（如有）。\n"
        f"8) 若你认为当前开发任务已全部完成，在回答末尾写：{DEV_DONE}\n"
        f"9) 若你认为仍有任务未完成，在回答末尾写：{DEV_CONTINUE}\n"
        f"10) 回答必须以 {DEV_DONE} / {DEV_CONTINUE} 之一结尾。"
    )


def normalize_dev_answer(answer: str | None, raw_output: str) -> str:
    merged = (answer or "").strip()
    if not merged:
        merged = raw_output.strip()
    if DEV_DONE in merged:
        return DEV_DONE
    return DEV_CONTINUE
