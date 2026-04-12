"""Stage runner with context-aware resume support."""

from __future__ import annotations

from pathlib import Path

from loguru import logger

from .codex_io import (
    build_exec_base_cmd,
    build_resume_cmd,
    format_cmd,
    parse_jsonl_for_thread_and_last_message,
    run_codex_with_retry,
)
from .context import load_context, save_context


def run_stage(
    codex_bin: str,
    sandbox: bool,
    prompt: str,
    stage_name: str,
    context_file: Path | None,
    timeout_sec: int,
    max_retry: int,
    dry_run: bool,
    model: str,
    thinking_effort: str,
    cwd: Path | None = None,
) -> tuple[int, str, str]:
    if context_file:
        thread_id = load_context(context_file)
        if thread_id:
            cmd = build_resume_cmd(codex_bin, thread_id, sandbox, model, thinking_effort)
        else:
            cmd = build_exec_base_cmd(codex_bin, sandbox, model, thinking_effort)
    else:
        cmd = build_exec_base_cmd(codex_bin, sandbox, model, thinking_effort)

    if dry_run:
        logger.info("[执行器] 演练-{}: {}", stage_name, format_cmd(cmd, prompt))
        return 0, "", ""

    rc, out, err = run_codex_with_retry(
        cmd, prompt, timeout_sec, stage_name, max_retry=max_retry, cwd=cwd
    )

    new_thread_id, _ = parse_jsonl_for_thread_and_last_message(out)
    if context_file and new_thread_id:
        save_context(context_file, new_thread_id)

    return rc, out, err
