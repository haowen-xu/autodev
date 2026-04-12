from __future__ import annotations

import json
from pathlib import Path

from autodev.runner import run_stage


def _make_fake_codex(path: Path) -> None:
    script = """#!/usr/bin/env python3
import json
import pathlib
import sys

argv = sys.argv[1:]
prompt = argv[-1] if argv else ""
payload = {"argv": argv, "prompt": prompt}
log = pathlib.Path("fake-codex-calls.jsonl")
with log.open("a", encoding="utf-8") as f:
    f.write(json.dumps(payload, ensure_ascii=False) + "\\n")

print(json.dumps({"type": "thread.started", "thread_id": "th_test"}))
print(json.dumps({"type": "item.completed", "item": {"type": "agent_message", "text": "ok"}}))
"""
    path.write_text(script, encoding="utf-8")
    path.chmod(0o755)


def test_run_stage_with_patched_codex_exec_and_resume(tmp_path: Path) -> None:
    fake_codex = tmp_path / "codex"
    _make_fake_codex(fake_codex)

    context_file = tmp_path / "ctx.json"

    rc, out, err = run_stage(
        codex_bin=str(fake_codex),
        sandbox=False,
        prompt="PROMPT_EXEC",
        stage_name="阶段",
        context_file=context_file,
        timeout_sec=5,
        max_retry=0,
        dry_run=False,
        model="gpt-5.4",
        thinking_effort="medium",
        cwd=tmp_path,
    )
    assert rc == 0
    assert err == ""
    assert out
    assert context_file.exists()

    rc2, out2, err2 = run_stage(
        codex_bin=str(fake_codex),
        sandbox=True,
        prompt="PROMPT_RESUME",
        stage_name="阶段",
        context_file=context_file,
        timeout_sec=5,
        max_retry=0,
        dry_run=False,
        model="gpt-5.4",
        thinking_effort="medium",
        cwd=tmp_path,
    )
    assert rc2 == 0
    assert err2 == ""
    assert out2

    lines = (tmp_path / "fake-codex-calls.jsonl").read_text(encoding="utf-8").strip().splitlines()
    assert len(lines) == 2
    first = json.loads(lines[0])
    second = json.loads(lines[1])

    # First run uses exec mode and bypass flag when sandbox=False.
    assert first["argv"][:7] == [
        "exec",
        "--skip-git-repo-check",
        "--json",
        "--model",
        "gpt-5.4",
        "-c",
        'model_reasoning_effort="medium"',
    ]
    assert "--dangerously-bypass-approvals-and-sandbox" in first["argv"]
    assert first["prompt"] == "PROMPT_EXEC"

    # Second run resumes previous thread and uses full-auto when sandbox=True.
    assert second["argv"][:9] == [
        "exec",
        "resume",
        "th_test",
        "--skip-git-repo-check",
        "--json",
        "--model",
        "gpt-5.4",
        "-c",
        'model_reasoning_effort="medium"',
    ]
    assert "--full-auto" in second["argv"]
    assert second["prompt"] == "PROMPT_RESUME"
