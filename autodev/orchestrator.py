"""Main workflow orchestration."""

from __future__ import annotations

import shutil
from pathlib import Path

from loguru import logger

from .arbitrator import build_arbitrator_prompt, normalize_arbitrator_answer
from .checklists import checklist_all_checked, ensure_agent_checklists, file_digest
from .codex_io import parse_jsonl_for_thread_and_last_message
from .constants import (
    ARBITRATOR_DONE,
    DEV_CONTINUE,
    DEV_DONE,
    PLAN_DONE,
    REVIEW_FAIL,
    REVIEW_INCOMPLETE,
    REVIEW_NEED_ARBITRATOR,
    REVIEW_PASS,
)
from .context import build_timestamped_context_file
from .dev import build_dev_prompt, normalize_dev_answer
from .git_tools import resolve_repo_root, setup_worktree
from .logging_utils import setup_logger
from .merge import build_merge_prompt
from .plan import build_plan_prompt
from .review import build_review_prompt, normalize_review_answer
from .runner import run_stage


def run(
    plan_file: Path,
    work_dir: Path,
    use_worktree: bool,
    merge_to_main: bool,
    sandbox: bool,
    max_plan_iteration: int,
    max_iteration: int,
    max_dev_iteration: int,
    max_review_iteration: int,
    max_arbitration_iteration: int,
    push: bool,
    dry_run: bool,
    timeout_sec: int,
    codex_bin: str,
    max_retry: int,
) -> int:
    if not dry_run and not shutil.which(codex_bin):
        logger.error("找不到 codex 可执行文件: {}", codex_bin)
        return 2

    plan_file_input = plan_file.resolve()
    if not plan_file_input.exists():
        logger.error("计划文件不存在: {}", plan_file_input)
        return 2

    plan_stem = plan_file_input.stem
    source_plan_file = plan_file_input
    source_plan_digest = file_digest(source_plan_file)
    if source_plan_digest is None:
        logger.error("无法读取原始计划文件: {}", source_plan_file)
        return 2

    def ensure_source_plan_unchanged(stage_name: str) -> bool:
        current_digest = file_digest(source_plan_file)
        if current_digest != source_plan_digest:
            logger.error(
                "[执行器] 检测到原始计划文件被修改（禁止）。阶段={} 文件={}",
                stage_name,
                source_plan_file,
            )
            return False
        return True

    autodev_dir = work_dir.resolve() / plan_stem
    context_dir = autodev_dir / "context"
    context_dir.mkdir(parents=True, exist_ok=True)
    plan_ctx = build_timestamped_context_file(context_dir, "plan")

    dev_cwd: Path | None = None
    worktree_branch: str | None = None
    if use_worktree:
        repo_root = resolve_repo_root()
        if repo_root is None:
            logger.error("无法获取主仓库根目录")
            return 2

        worktree_path = autodev_dir / "worktree"
        worktree_branch = f"autodev/{plan_stem}"
        setup_worktree(worktree_path, worktree_branch, repo_root=repo_root)
        dev_cwd = worktree_path

    plan_output_file = context_dir / f"{plan_stem}.plan.md"
    dev_file = context_dir / f"{plan_stem}.dev.md"
    review_file = context_dir / f"{plan_stem}.review.md"
    log_file = context_dir / f"{plan_stem}.log"

    setup_logger(log_file)
    logger.info(
        "[执行器] 开始: 计划输入={} 计划输出={} dev={} review={} 工作目录={} worktree={} merge_to_main={} push={} 沙箱={} 开发-审查最大轮次={} 内层开发最大轮次={} 每轮最大审查轮次={} 最大仲裁轮次={} 演练={}",
        source_plan_file,
        plan_output_file,
        dev_file,
        review_file,
        autodev_dir,
        use_worktree,
        merge_to_main,
        push,
        sandbox,
        max_iteration,
        max_dev_iteration,
        max_review_iteration,
        max_arbitration_iteration,
        dry_run,
    )

    if plan_output_file.exists():
        logger.info("[执行器] 计划输出已存在，跳过计划阶段: {}", plan_output_file)
    else:
        plan_done = False
        for p in range(1, max_plan_iteration + 1):
            logger.info("[执行器] ══ 计划轮次 {}/{} ══", p, max_plan_iteration)
            prompt = build_plan_prompt(source_plan_file, plan_output_file, p, max_plan_iteration)
            rc, out, _ = run_stage(
                codex_bin,
                sandbox,
                prompt,
                "计划",
                plan_ctx,
                timeout_sec,
                max_retry,
                dry_run,
                cwd=dev_cwd,
            )
            if rc != 0:
                return rc
            if not dry_run and not ensure_source_plan_unchanged("计划"):
                return 1
            if dry_run:
                continue
            _, last_message = parse_jsonl_for_thread_and_last_message(out)
            merged = (last_message or "") + out
            if PLAN_DONE in merged:
                plan_done = True
                logger.info("[执行器] 计划完成，共 {} 轮", p)
                break
            logger.info("[执行器] 计划未完成，继续下一轮")

        if not dry_run and not plan_done:
            logger.error("[执行器] 已到达计划最大轮次（{}），计划仍未完成", max_plan_iteration)
            return 1
        if not dry_run and not plan_output_file.exists():
            logger.error("计划阶段未生成 plan 文件: {}", plan_output_file)
            return 1

    if not dry_run:
        created = ensure_agent_checklists(plan_output_file, dev_file, review_file)
        if created:
            logger.info("[执行器] 已从 {} 派生生成 {} 与 {}", plan_output_file, dev_file, review_file)
        else:
            logger.info("[执行器] 检测到已有 {} 与 {}，保留现状不覆盖", dev_file, review_file)

    review_passed = False
    need_arbitration = False
    dev_done_but_review_fail_streak = 0
    for a in range(1, max_arbitration_iteration + 1):
        logger.info("[执行器] ══ 仲裁轮次 {}/{} ══", a, max_arbitration_iteration)
        need_arbitration = False
        for i in range(1, max_iteration + 1):
            logger.info("[执行器] ══ 仲裁 {} / 开发-审查轮次 {}/{} ══", a, i, max_iteration)
            dev_ctx = build_timestamped_context_file(context_dir, "dev")
            dev_status = DEV_CONTINUE
            for d in range(1, max_dev_iteration + 1):
                logger.info(
                    "[执行器] ══ 仲裁 {} / 开发-审查轮次 {}: 开发 {}/{} ══",
                    a,
                    i,
                    d,
                    max_dev_iteration,
                )
                review_before = file_digest(review_file)
                dev_prompt = build_dev_prompt(
                    source_plan_file, dev_file, review_file, d, max_dev_iteration
                )
                rc, dev_out, _ = run_stage(
                    codex_bin,
                    sandbox,
                    dev_prompt,
                    "开发",
                    dev_ctx,
                    timeout_sec,
                    max_retry,
                    dry_run,
                    cwd=dev_cwd,
                )
                if rc != 0:
                    return rc
                if not dry_run and not ensure_source_plan_unchanged("开发"):
                    return 1

                if dry_run:
                    dev_status = DEV_CONTINUE
                    continue

                review_after = file_digest(review_file)
                if review_after != review_before:
                    logger.error("[执行器] 开发阶段禁止修改审查记录，但检测到文件变化: {}", review_file)
                    return 1
                _, dev_last_message = parse_jsonl_for_thread_and_last_message(dev_out)
                dev_status = normalize_dev_answer(dev_last_message, dev_out)
                logger.info("[执行器] 开发结果: {}", dev_status)
                if dev_status == DEV_DONE:
                    break

            if not dry_run and dev_status != DEV_DONE:
                logger.info(
                    "[执行器] 本次开发循环达到上限（{}）仍未完成，进入下一开发-审查轮次",
                    max_dev_iteration,
                )
                continue

            review_final = REVIEW_INCOMPLETE
            dev_all_checked_before_review = checklist_all_checked(dev_file) if not dry_run else False
            review_reported_need_arbitrator = False
            review_ctx = build_timestamped_context_file(context_dir, "review")
            for r in range(1, max_review_iteration + 1):
                logger.info(
                    "[执行器] ══ 仲裁 {} / 开发轮次 {}: 审查 {}/{} ══",
                    a,
                    i,
                    r,
                    max_review_iteration,
                )
                review_prompt = build_review_prompt(source_plan_file, dev_file, review_file)
                rc, out, _ = run_stage(
                    codex_bin,
                    sandbox,
                    review_prompt,
                    "审查",
                    review_ctx,
                    timeout_sec,
                    max_retry,
                    dry_run,
                    cwd=dev_cwd,
                )
                if rc != 0:
                    return rc
                if not dry_run and not ensure_source_plan_unchanged("审查"):
                    return 1

                if dry_run:
                    review_final = REVIEW_INCOMPLETE
                    continue

                _, last_message = parse_jsonl_for_thread_and_last_message(out)
                answer = normalize_review_answer(last_message, out)
                logger.info("[执行器] 审查结果: {}", answer)
                if REVIEW_NEED_ARBITRATOR in ((last_message or "") + out):
                    review_reported_need_arbitrator = True

                if answer == REVIEW_INCOMPLETE:
                    if r < max_review_iteration:
                        logger.info("[执行器] 审查未完成，继续本轮审查")
                        continue
                    logger.error("[执行器] 审查在本轮达到最大次数仍未完成（{}）", max_review_iteration)
                    return 1

                review_final = answer
                break

            if dry_run:
                continue

            if review_final == REVIEW_PASS:
                logger.info("[执行器] 审查通过，在仲裁 {} / 开发轮次 {} 完成全部工作", a, i)
                review_passed = True
                break

            dev_all_checked_after_review = checklist_all_checked(dev_file)
            dev_done_but_review_fail = (
                dev_status == DEV_DONE
                and review_final == REVIEW_FAIL
                and (dev_all_checked_before_review or not dev_all_checked_after_review)
            )
            if dev_done_but_review_fail:
                dev_done_but_review_fail_streak += 1
                logger.warning(
                    "[执行器] dev agent 认为自己已经全部完成，但审查未通过（连续 {} 次）",
                    dev_done_but_review_fail_streak,
                )
            else:
                dev_done_but_review_fail_streak = 0

            if review_reported_need_arbitrator or dev_done_but_review_fail_streak >= 2:
                logger.warning("[执行器] {}", REVIEW_NEED_ARBITRATOR)
                need_arbitration = True
                break

            logger.info("[执行器] 审查未通过，进入下一轮开发修复")

        if dry_run:
            continue

        if review_passed:
            break

        if not need_arbitration:
            logger.error("[执行器] 开发轮次已达上限（{}），且未触发仲裁", max_iteration)
            return 1

        logger.info("[执行器] 进入仲裁阶段")
        arbitrator_ctx = build_timestamped_context_file(context_dir, "arbitrator")
        arbitrator_prompt = build_arbitrator_prompt(
            source_plan_file,
            dev_file,
            review_file,
            a,
            max_arbitration_iteration,
        )
        rc, out, _ = run_stage(
            codex_bin,
            sandbox,
            arbitrator_prompt,
            "仲裁",
            arbitrator_ctx,
            timeout_sec,
            max_retry,
            dry_run,
            cwd=dev_cwd,
        )
        if rc != 0:
            return rc
        if not dry_run and not ensure_source_plan_unchanged("仲裁"):
            return 1
        _, arbitrator_last_message = parse_jsonl_for_thread_and_last_message(out)
        arbitrator_result = normalize_arbitrator_answer(arbitrator_last_message, out)
        logger.info("[执行器] 仲裁结果: {}", arbitrator_result)
        if arbitrator_result == ARBITRATOR_DONE:
            review_passed = True
            break
        dev_done_but_review_fail_streak = 0
        logger.info("[执行器] 仲裁要求继续开发，进入下一仲裁轮次")

    if not dry_run and not review_passed:
        logger.error("[执行器] 已到达仲裁最大轮次（{}），流程仍未通过", max_arbitration_iteration)
        return 1

    logger.info("[执行器] ══ 阶段: 合并 ══")
    merge_prompt = build_merge_prompt(
        source_plan_file,
        dev_file,
        push,
        worktree_branch=worktree_branch,
        worktree_path=dev_cwd,
        merge_to_main=merge_to_main,
    )
    merge_cwd = None if (worktree_branch and merge_to_main) else dev_cwd
    rc, _, _ = run_stage(
        codex_bin,
        sandbox,
        merge_prompt,
        "合并",
        None,
        timeout_sec,
        max_retry,
        dry_run,
        cwd=merge_cwd,
    )
    if rc != 0:
        return rc

    logger.info("[执行器] 合并完成")
    return 0
