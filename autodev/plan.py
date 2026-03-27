"""Plan agent prompt and result normalization."""

from __future__ import annotations

from pathlib import Path

from .constants import PLAN_DONE


def build_plan_prompt(
    source_plan_file: Path,
    output_plan_file: Path,
    iteration: int,
    max_iteration: int,
) -> str:
    return (
        "你是计划代理。请根据计划文件制定精细的开发计划。\n"
        f"- 计划文件: {source_plan_file}\n"
        f"- 输出文件: {output_plan_file}\n"
        f"- 当前轮次: {iteration}/{max_iteration}\n"
        "要求：\n"
        "1) 仔细阅读计划文件，理解全部需求和背景。\n"
        "2) 拆分为细粒度可执行的任务清单，每个任务有明确的完成标准。\n"
        "3) 输出 Markdown，严格按以下结构（不可省略任何章节）：\n"
        "\n"
        "   # <简洁主标题>\n"
        "\n"
        "   ## 任务描述\n"
        "   <用自己的话概述计划目标、范围、关键约束>\n"
        "\n"
        "   ## 任务列表\n"
        "   按逻辑阶段拆分为多个 Milestone（简单任务可只有一个）：\n"
        "   ### Milestone 1: <阶段名>\n"
        "   - [ ] 任务1：描述\n"
        "   - [ ] 任务2：描述\n"
        "   ### Milestone 2: <阶段名>\n"
        "   - [ ] 任务3：描述\n"
        "   ...\n"
        "\n"
        "   ## 验收标准\n"
        "   - [ ] 标准1\n"
        "   - [ ] 标准2\n"
        "   ...\n"
        "\n"
        "4) todo list 与验收标准中的每一项都必须使用 `- [ ]` 格式；"
        "禁止使用普通无勾选列表（如 `- `）或编号列表（如 `1.`）。\n"
        f"5) 将结果写入 {output_plan_file}。\n"
        "6) 仅做计划，不要执行任何开发工作。\n"
        "7) 自行检查计划是否完整且可执行。若已完成全部计划工作，"
        f"在回答最后一行输出：{PLAN_DONE}"
    )
