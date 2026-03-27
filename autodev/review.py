"""Review agent prompt and result normalization."""

from __future__ import annotations

from pathlib import Path

from .constants import REVIEW_FAIL, REVIEW_INCOMPLETE, REVIEW_NEED_ARBITRATOR, REVIEW_PASS


def build_review_prompt(
    plan_file: Path,
    dev_file: Path,
    review_file: Path,
) -> str:
    return (
        "请审查开发工作是否满足计划要求和验收标准。\n"
        f"计划文件: {plan_file}\n"
        f"开发清单（可按规则回写）: {dev_file}\n"
        f"审查清单（可按规则回写）: {review_file}\n"
        "要求：\n"
        "1) 独立逐项核对计划文件中的需求和验收标准，检查当前代码是否满足。\n"
        "2) 执行 lint 和测试验证。\n"
        f"3) 若发现 {dev_file} 中有“实际未完成但被打钩 [x]”的条目，必须立即就地修正：\n"
        "   - 将该条目标记改回 [ ]。\n"
        "   - 必须在该条目的下一行补充 `问题: <未完成原因>`。\n"
        "   - `问题:` 必须包含可定位证据（至少文件路径，建议行号）。\n"
        "4) 在审查清单中维护你自己的审查检查项：\n"
        "   - 首轮审查时，根据计划文件和验收标准生成完整的检查项。\n"
        "   - 每项通过标记为 [x]，未通过标记为 [ ] 并附上问题描述。\n"
        "   - 后续轮次基于上一轮的审查清单继续更新，不要从零重建。\n"
        "   - 必须在原有检查项上就地更新状态，禁止在 Round 轮次中追加一份重复清单。\n"
        "5) 不要依赖开发清单的勾选状态来判断完成情况，必须独立验证代码。\n"
        "6) 若你发现开发代理把开发清单全部打钩，但你审查后仍需取消打钩，"
        "必须在审查清单中“质量门禁执行记录”章节特别注明：`dev agent 认为自己已经全部完成`。\n"
        "7) 若连续两次及以上出现“dev agent 认为自己全部完成，但审查仍不通过”，"
        f"请在回答中输出：{REVIEW_NEED_ARBITRATOR}\n"
        "8) 若审查不通过，将不通过的理由和需修复的问题明确写入审查清单对应检查项。\n"
        f"9) 全部检查项通过则在回答末尾写：{REVIEW_PASS}\n"
        f"10) 有未通过项则在回答末尾写：{REVIEW_FAIL}\n"
        f"11) 若本轮审查尚未完成（例如仍在补充验证），在回答末尾写：{REVIEW_INCOMPLETE}\n"
        f"12) 回答必须以 {REVIEW_PASS} / {REVIEW_FAIL} / {REVIEW_INCOMPLETE} 之一结尾。"
    )


def normalize_review_answer(answer: str | None, raw_output: str) -> str:
    merged = (answer or "").strip()
    if not merged:
        merged = raw_output.strip()
    if not merged:
        return REVIEW_FAIL
    if REVIEW_INCOMPLETE in merged:
        return REVIEW_INCOMPLETE
    if REVIEW_PASS in merged:
        return REVIEW_PASS
    return REVIEW_FAIL
