"""Codex process execution helpers."""

from __future__ import annotations

import json
import shlex
import subprocess
import threading
import time
from pathlib import Path
from typing import Any

from loguru import logger


def extract_event_text(event: dict[str, Any]) -> str | None:
    if event.get("type") != "item.completed":
        return None
    item = event.get("item", {})
    if not isinstance(item, dict) or item.get("type") != "agent_message":
        return None
    text = item.get("text")
    if isinstance(text, str) and text.strip():
        return text.strip()
    return None


def _stream_pipe_lines(
    pipe: Any,
    sink: list[str],
    stage: str,
    stream_name: str,
) -> None:
    for line in iter(pipe.readline, ""):
        sink.append(line)
        text = line.rstrip("\n")
        if text.strip():
            if stream_name == "stdout":
                try:
                    event = json.loads(text)
                except json.JSONDecodeError:
                    continue
                else:
                    if isinstance(event, dict):
                        message = extract_event_text(event)
                        if message:
                            logger.debug("{}", message)
            else:
                logger.debug("[执行器] {} 实时{}: {}", stage, stream_name, text)
    pipe.close()


def run_codex(
    command: list[str],
    prompt: str,
    timeout_sec: int,
    stage: str,
    cwd: Path | None = None,
) -> tuple[int, str, str]:
    full_cmd = command + [prompt]
    out_lines: list[str] = []
    err_lines: list[str] = []
    try:
        with subprocess.Popen(
            full_cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1,
            cwd=cwd,
        ) as proc:
            threads: list[threading.Thread] = []
            for pipe, sink, name in [
                (proc.stdout, out_lines, "stdout"),
                (proc.stderr, err_lines, "stderr"),
            ]:
                t = threading.Thread(
                    target=_stream_pipe_lines,
                    args=(pipe, sink, stage, name),
                    daemon=True,
                )
                t.start()
                threads.append(t)
            try:
                proc.wait(timeout=timeout_sec)
            except subprocess.TimeoutExpired:
                proc.kill()
                proc.wait()
                for t in threads:
                    t.join()
                out = "".join(out_lines)
                err = "".join(err_lines)
                return 124, out, f"调用 codex 超时（{timeout_sec} 秒）\n{err}"
            for t in threads:
                t.join()
            return proc.returncode, "".join(out_lines), "".join(err_lines)
    except OSError as exc:
        return 1, "".join(out_lines), str(exc)


def run_codex_with_retry(
    command: list[str],
    prompt: str,
    timeout_sec: int,
    stage: str,
    max_retry: int,
    retry_wait_sec: int = 60,
    cwd: Path | None = None,
) -> tuple[int, str, str]:
    for attempt in range(max_retry + 1):
        rc, out, err = run_codex(command, prompt, timeout_sec, stage, cwd=cwd)
        log_codex_io(stage, out, err)
        if rc == 0:
            return rc, out, err

        logger.error("[执行器] {}失败（退出码={}）", stage, rc)
        if err.strip():
            logger.error(err.strip())

        if attempt < max_retry:
            logger.error(
                "[执行器] {}将在 {} 秒后重试（第 {}/{} 次重试）",
                stage,
                retry_wait_sec,
                attempt + 1,
                max_retry,
            )
            time.sleep(retry_wait_sec)

    return rc, out, err


def format_cmd(command: list[str], prompt: str) -> str:
    return shlex.join(command + [prompt])


def parse_jsonl_for_thread_and_last_message(output: str) -> tuple[str | None, str | None]:
    thread_id = None
    last_message = None
    for raw_line in output.splitlines():
        line = raw_line.strip()
        if not line:
            continue
        try:
            event = json.loads(line)
        except json.JSONDecodeError:
            continue
        if event.get("type") == "thread.started":
            thread_id = event.get("thread_id")
        if event.get("type") == "item.completed":
            item = event.get("item", {})
            if item.get("type") == "agent_message":
                last_message = item.get("text", "").strip()
    return thread_id, last_message


def build_exec_base_cmd(codex_bin: str, sandbox: bool) -> list[str]:
    cmd = [
        codex_bin,
        "exec",
        "--skip-git-repo-check",
        "--json",
    ]
    if sandbox:
        cmd.append("--full-auto")
    else:
        cmd.append("--dangerously-bypass-approvals-and-sandbox")
    return cmd


def build_resume_cmd(codex_bin: str, thread_id: str, sandbox: bool) -> list[str]:
    cmd = [
        codex_bin,
        "exec",
        "resume",
        thread_id,
        "--skip-git-repo-check",
        "--json",
    ]
    if sandbox:
        cmd.append("--full-auto")
    else:
        cmd.append("--dangerously-bypass-approvals-and-sandbox")
    return cmd


def log_codex_io(stage: str, out: str, err: str) -> None:
    if err.strip():
        logger.debug("[执行器] {} 标准错误:\n{}", stage, err.rstrip())
