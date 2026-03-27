from __future__ import annotations

import json
import subprocess
from pathlib import Path

import pytest

from autodev import run as exported_run
from autodev import (
    arbitrator,
    checklists,
    codex_io,
    constants,
    context,
    dev,
    git_tools,
    logging_utils,
    merge,
    plan,
    review,
)
from autodev.runner import run_stage


def test_exported_run_callable() -> None:
    assert callable(exported_run)


def test_prompt_builders_and_normalizers(tmp_path: Path) -> None:
    p = tmp_path / "task.md"
    out = tmp_path / "task.plan.md"
    d = tmp_path / "task.dev.md"
    r = tmp_path / "task.review.md"

    plan_prompt = plan.build_plan_prompt(p, out, 1, 3)
    assert str(p) in plan_prompt
    assert str(out) in plan_prompt
    assert constants.PLAN_DONE in plan_prompt

    dev_prompt = dev.build_dev_prompt(p, d, r, 1, 2)
    assert str(d) in dev_prompt
    assert constants.DEV_DONE in dev_prompt
    assert dev.normalize_dev_answer(constants.DEV_DONE, "") == constants.DEV_DONE
    assert dev.normalize_dev_answer(None, "") == constants.DEV_CONTINUE

    review_prompt = review.build_review_prompt(p, d, r)
    assert str(r) in review_prompt
    assert review.normalize_review_answer(constants.REVIEW_PASS, "") == constants.REVIEW_PASS
    assert review.normalize_review_answer(constants.REVIEW_INCOMPLETE, "") == constants.REVIEW_INCOMPLETE
    assert review.normalize_review_answer("x", "") == constants.REVIEW_FAIL

    arb_prompt = arbitrator.build_arbitrator_prompt(p, d, r, 1, 4)
    assert constants.ARBITRATOR_DONE in arb_prompt
    assert arbitrator.normalize_arbitrator_answer(constants.ARBITRATOR_DONE, "") == constants.ARBITRATOR_DONE
    assert arbitrator.normalize_arbitrator_answer(None, "") == constants.ARBITRATOR_CONTINUE

    merge_prompt = merge.build_merge_prompt(p, d, push=True, worktree_branch="b1", worktree_path=tmp_path)
    assert "git push" in merge_prompt
    assert str(p) in merge_prompt


def test_checklists_and_digest(tmp_path: Path) -> None:
    plan_file = tmp_path / "x.plan.md"
    dev_file = tmp_path / "x.dev.md"
    review_file = tmp_path / "x.review.md"
    plan_file.write_text("# t\n\n- [ ] a\n", encoding="utf-8")

    created = checklists.ensure_agent_checklists(plan_file, dev_file, review_file)
    assert created is True
    assert dev_file.exists() and review_file.exists()

    checked, unchecked = checklists.checklist_stats(dev_file)
    assert checked == 0
    assert unchecked >= 1
    assert checklists.checklist_all_checked(dev_file) is False

    dev_file.write_text("- [x] ok\n", encoding="utf-8")
    assert checklists.checklist_all_checked(dev_file) is True

    assert checklists.file_digest(tmp_path / "missing.txt") is None
    assert checklists.file_digest(dev_file) is not None


def test_context_helpers(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    c = tmp_path / "c.json"
    assert context.load_context(c) is None

    context.save_context(c, "t1")
    assert context.load_context(c) == "t1"

    c.write_text("{bad json", encoding="utf-8")
    assert context.load_context(c) is None

    d = tmp_path / "ctx"
    d.mkdir()
    p1 = d / "dev.20260101-000000.json"
    p1.write_text("{}", encoding="utf-8")
    seq = iter(["20260101-000000", "20260101-000001"])
    monkeypatch.setattr(context.time, "strftime", lambda fmt: next(seq))
    monkeypatch.setattr(context.time, "sleep", lambda s: None)
    p = context.build_timestamped_context_file(d, "dev")
    assert p.name == "dev.20260101-000001.json"


def test_codex_io_utilities() -> None:
    evt = {"type": "item.completed", "item": {"type": "agent_message", "text": " hello "}}
    assert codex_io.extract_event_text(evt) == "hello"
    assert codex_io.extract_event_text({"type": "x"}) is None

    output = "\n".join(
        [
            json.dumps({"type": "thread.started", "thread_id": "th_1"}),
            json.dumps({"type": "item.completed", "item": {"type": "agent_message", "text": "a"}}),
        ]
    )
    thread_id, last_message = codex_io.parse_jsonl_for_thread_and_last_message(output)
    assert thread_id == "th_1"
    assert last_message == "a"

    cmd = codex_io.build_exec_base_cmd("codex", sandbox=False)
    assert "--dangerously-bypass-approvals-and-sandbox" in cmd
    cmd2 = codex_io.build_resume_cmd("codex", "th_1", sandbox=True)
    assert "resume" in cmd2 and "--full-auto" in cmd2
    assert "hello world" in codex_io.format_cmd(["echo"], "hello world")


def test_run_codex_with_retry(monkeypatch: pytest.MonkeyPatch) -> None:
    calls: list[int] = []

    def fake_run_codex(command, prompt, timeout_sec, stage, cwd=None):  # type: ignore[no-untyped-def]
        calls.append(1)
        if len(calls) == 1:
            return 1, "", "boom"
        return 0, "ok", ""

    monkeypatch.setattr(codex_io, "run_codex", fake_run_codex)
    monkeypatch.setattr(codex_io.time, "sleep", lambda _: None)
    rc, out, err = codex_io.run_codex_with_retry(["x"], "p", 1, "s", max_retry=2, retry_wait_sec=0)
    assert rc == 0
    assert out == "ok"
    assert err == ""
    assert len(calls) == 2


def test_run_codex_timeout_and_oserror(monkeypatch: pytest.MonkeyPatch) -> None:
    class FakePopen:
        def __init__(self, *args, **kwargs) -> None:
            self.stdout = type("S", (), {"readline": staticmethod(lambda: ""), "close": staticmethod(lambda: None)})()
            self.stderr = type("S", (), {"readline": staticmethod(lambda: ""), "close": staticmethod(lambda: None)})()
            self.returncode = 0

        def __enter__(self):  # type: ignore[no-untyped-def]
            return self

        def __exit__(self, exc_type, exc, tb) -> None:  # type: ignore[no-untyped-def]
            return None

        def wait(self, timeout=None):  # type: ignore[no-untyped-def]
            if timeout is not None:
                raise subprocess.TimeoutExpired(cmd="x", timeout=timeout)
            return 0

        def kill(self) -> None:
            return None

    monkeypatch.setattr(codex_io.subprocess, "Popen", FakePopen)
    rc, _, err = codex_io.run_codex(["x"], "p", 1, "stage")
    assert rc == 124
    assert "超时" in err

    def raise_oserror(*args, **kwargs):  # type: ignore[no-untyped-def]
        raise OSError("bad")

    monkeypatch.setattr(codex_io.subprocess, "Popen", raise_oserror)
    rc2, _, err2 = codex_io.run_codex(["x"], "p", 1, "stage")
    assert rc2 == 1
    assert "bad" in err2


def test_git_tools(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    class Res:
        def __init__(self, code: int, out: str = "", err: str = "") -> None:
            self.returncode = code
            self.stdout = out
            self.stderr = err

    calls: list[list[str]] = []

    def fake_run(args, cwd=None, capture_output=None, text=None):  # type: ignore[no-untyped-def]
        calls.append(args)
        if args[:3] == ["git", "rev-parse", "--show-toplevel"]:
            return Res(0, str(tmp_path))
        if args[:3] == ["git", "worktree", "add"] and "-b" in args:
            return Res(1, err="exists")
        return Res(0)

    monkeypatch.setattr(git_tools.subprocess, "run", fake_run)

    wt = tmp_path / "a" / "wt"
    git_tools.setup_worktree(wt, "b1", repo_root=tmp_path)
    assert calls
    assert git_tools.resolve_repo_root() == tmp_path.resolve()


def test_runner_stage_resume_and_exec(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    cfile = tmp_path / "c.json"
    cfile.write_text(json.dumps({"thread_id": "th_1"}), encoding="utf-8")

    monkeypatch.setattr("autodev.runner.build_resume_cmd", lambda codex_bin, thread_id, sandbox: ["resume"])  # type: ignore[arg-type]
    monkeypatch.setattr("autodev.runner.build_exec_base_cmd", lambda codex_bin, sandbox: ["exec"])  # type: ignore[arg-type]
    monkeypatch.setattr(
        "autodev.runner.run_codex_with_retry",
        lambda cmd, prompt, timeout_sec, stage_name, max_retry, cwd=None: (
            0,
            json.dumps({"type": "thread.started", "thread_id": "th_2"}),
            "",
        ),
    )

    rc, out, _ = run_stage("codex", False, "p", "阶段", cfile, 1, 0, dry_run=False, cwd=None)
    assert rc == 0
    assert out
    assert context.load_context(cfile) == "th_2"

    rc2, out2, err2 = run_stage("codex", False, "p2", "阶段", cfile, 1, 0, dry_run=True, cwd=None)
    assert rc2 == 0
    assert out2 == ""
    assert err2 == ""


def test_setup_logger_creates_log_file(tmp_path: Path) -> None:
    log_file = tmp_path / "logs" / "run.log"
    logging_utils.setup_logger(log_file)
    # Trigger one line so file sink is exercised.
    logging_utils.logger.info("hello")
    assert log_file.exists()
