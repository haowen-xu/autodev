"""Arbitrator prompt and result normalization."""

from __future__ import annotations

from pathlib import Path

from .constants import ARBITRATOR_CONTINUE, ARBITRATOR_DONE


def build_arbitrator_prompt(
    plan_file: Path,
    dev_file: Path,
    review_file: Path,
    arbitration_round: int,
    max_arbitration_iteration: int,
) -> str:
    return (
        "你是仲裁者代理。当前开发代理与审查代理对完成状态存在分歧，请根据原始计划进行仲裁。\n"
        f"计划文件: {plan_file}\n"
        f"开发清单(dev): {dev_file}\n"
        f"审查清单(review): {review_file}\n"
        f"当前仲裁轮次: {arbitration_round}/{max_arbitration_iteration}\n"
        "要求：\n"
        "1) 以计划文件为唯一基准，重新审视 dev 与 review 是否准确反映真实进度。\n"
        "2) 你可以直接修改 dev 与 review，不限于勾选/取消勾选；必要时可彻底重写两份文件。\n"
        "3) dev 与 review 的任务项必须严格一一对应（同一任务在两份文件中都要存在且可相互映射），"
        "禁止只改其中一份导致编号/条目错位。\n"
        "4) 若你重写了任一文件，必须同步重写另一文件并在结束前自检一一对应关系。\n"
        "5) 重写时必须保留可执行性与可验证性，确保后续开发和审查可以继续闭环推进。\n"
        "6) 结合当前代码状态判断是否已满足计划目标与验收标准。\n"
        f"7) 若你认为开发可以停止，在回答末尾写：{ARBITRATOR_DONE}\n"
        f"8) 若你认为仍需继续开发，在回答末尾写：{ARBITRATOR_CONTINUE}\n"
        f"9) 回答必须以 {ARBITRATOR_DONE} / {ARBITRATOR_CONTINUE} 之一结尾。"
    )


def normalize_arbitrator_answer(answer: str | None, raw_output: str) -> str:
    merged = (answer or "").strip()
    if not merged:
        merged = raw_output.strip()
    if ARBITRATOR_DONE in merged:
        return ARBITRATOR_DONE
    return ARBITRATOR_CONTINUE
