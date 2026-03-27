from __future__ import annotations

from pathlib import Path

from click.testing import CliRunner

from autodev import cli, constants, orchestrator


def _jsonl_message(text: str) -> str:
    return (
        '{"type":"thread.started","thread_id":"th_1"}\n'
        + f'{{"type":"item.completed","item":{{"type":"agent_message","text":"{text}"}}}}\n'
    )


def test_orchestrator_dry_run_happy_path(tmp_path: Path) -> None:
    plan_file = tmp_path / "task.md"
    plan_file.write_text("# task\n", encoding="utf-8")

    rc = orchestrator.run(
        plan_file=plan_file,
        work_dir=tmp_path / ".autodev",
        use_worktree=False,
        merge_to_main=True,
        sandbox=False,
        max_plan_iteration=1,
        max_iteration=1,
        max_dev_iteration=1,
        max_review_iteration=1,
        max_arbitration_iteration=1,
        push=False,
        dry_run=True,
        timeout_sec=1,
        codex_bin="codex",
        max_retry=0,
    )
    assert rc == 0


def test_orchestrator_non_dry_success(tmp_path: Path, monkeypatch) -> None:  # type: ignore[no-untyped-def]
    plan_file = tmp_path / "task.md"
    plan_file.write_text("# task\n", encoding="utf-8")

    def fake_run_stage(codex_bin, sandbox, prompt, stage_name, context_file, timeout_sec, max_retry, dry_run, cwd=None):  # type: ignore[no-untyped-def]
        if stage_name == "计划":
            marker = "- 输出文件: "
            out_path = Path(prompt.split(marker, 1)[1].splitlines()[0].strip())
            out_path.parent.mkdir(parents=True, exist_ok=True)
            out_path.write_text("# plan\n\n- [ ] item\n", encoding="utf-8")
            return 0, _jsonl_message(constants.PLAN_DONE), ""
        if stage_name == "开发":
            return 0, _jsonl_message(constants.DEV_DONE), ""
        if stage_name == "审查":
            return 0, _jsonl_message(constants.REVIEW_PASS), ""
        return 0, _jsonl_message("ok"), ""

    monkeypatch.setattr(orchestrator, "run_stage", fake_run_stage)
    monkeypatch.setattr(orchestrator.shutil, "which", lambda _: "/bin/echo")
    rc = orchestrator.run(
        plan_file=plan_file,
        work_dir=tmp_path / ".autodev",
        use_worktree=False,
        merge_to_main=True,
        sandbox=False,
        max_plan_iteration=2,
        max_iteration=2,
        max_dev_iteration=2,
        max_review_iteration=2,
        max_arbitration_iteration=2,
        push=False,
        dry_run=False,
        timeout_sec=1,
        codex_bin="codex",
        max_retry=0,
    )
    assert rc == 0
    assert (tmp_path / ".autodev" / "task" / "context" / "task.log").exists()
    assert not (tmp_path / "task.log").exists()


def test_orchestrator_non_dry_arbitrator_path(tmp_path: Path, monkeypatch) -> None:  # type: ignore[no-untyped-def]
    plan_file = tmp_path / "task.md"
    plan_file.write_text("# task\n", encoding="utf-8")
    state = {"review_count": 0}

    def fake_run_stage(codex_bin, sandbox, prompt, stage_name, context_file, timeout_sec, max_retry, dry_run, cwd=None):  # type: ignore[no-untyped-def]
        if stage_name == "计划":
            out_path = Path(prompt.split("- 输出文件: ", 1)[1].splitlines()[0].strip())
            out_path.parent.mkdir(parents=True, exist_ok=True)
            out_path.write_text("# plan\n\n- [ ] item\n", encoding="utf-8")
            return 0, _jsonl_message(constants.PLAN_DONE), ""
        if stage_name == "开发":
            return 0, _jsonl_message(constants.DEV_DONE), ""
        if stage_name == "审查":
            state["review_count"] += 1
            text = f"{constants.REVIEW_FAIL}\n{constants.REVIEW_NEED_ARBITRATOR}"
            return 0, _jsonl_message(text), ""
        if stage_name == "仲裁":
            return 0, _jsonl_message(constants.ARBITRATOR_DONE), ""
        return 0, _jsonl_message("ok"), ""

    monkeypatch.setattr(orchestrator, "run_stage", fake_run_stage)
    monkeypatch.setattr(orchestrator.shutil, "which", lambda _: "/bin/echo")
    rc = orchestrator.run(
        plan_file=plan_file,
        work_dir=tmp_path / ".autodev",
        use_worktree=False,
        merge_to_main=True,
        sandbox=False,
        max_plan_iteration=1,
        max_iteration=1,
        max_dev_iteration=1,
        max_review_iteration=1,
        max_arbitration_iteration=1,
        push=False,
        dry_run=False,
        timeout_sec=1,
        codex_bin="codex",
        max_retry=0,
    )
    assert state["review_count"] >= 1
    assert rc == 0


def test_orchestrator_dev_modifies_review_blocked(tmp_path: Path, monkeypatch) -> None:  # type: ignore[no-untyped-def]
    plan_file = tmp_path / "task.md"
    plan_file.write_text("# task\n", encoding="utf-8")

    def fake_run_stage(codex_bin, sandbox, prompt, stage_name, context_file, timeout_sec, max_retry, dry_run, cwd=None):  # type: ignore[no-untyped-def]
        autodev_dir = (tmp_path / ".autodev" / "task" / "context")
        review_file = autodev_dir / "task.review.md"
        if stage_name == "计划":
            out_path = Path(prompt.split("- 输出文件: ", 1)[1].splitlines()[0].strip())
            out_path.parent.mkdir(parents=True, exist_ok=True)
            out_path.write_text("# plan\n\n- [ ] item\n", encoding="utf-8")
            return 0, _jsonl_message(constants.PLAN_DONE), ""
        if stage_name == "开发":
            review_file.write_text("changed\n", encoding="utf-8")
            return 0, _jsonl_message(constants.DEV_DONE), ""
        return 0, _jsonl_message("ok"), ""

    monkeypatch.setattr(orchestrator, "run_stage", fake_run_stage)
    monkeypatch.setattr(orchestrator.shutil, "which", lambda _: "/bin/echo")
    rc = orchestrator.run(
        plan_file=plan_file,
        work_dir=tmp_path / ".autodev",
        use_worktree=False,
        merge_to_main=True,
        sandbox=False,
        max_plan_iteration=1,
        max_iteration=1,
        max_dev_iteration=1,
        max_review_iteration=1,
        max_arbitration_iteration=1,
        push=False,
        dry_run=False,
        timeout_sec=1,
        codex_bin="codex",
        max_retry=0,
    )
    assert rc == 1


def test_orchestrator_worktree_dry_run(tmp_path: Path, monkeypatch) -> None:  # type: ignore[no-untyped-def]
    plan_file = tmp_path / "task.md"
    plan_file.write_text("# task\n", encoding="utf-8")
    monkeypatch.setattr(orchestrator, "resolve_repo_root", lambda: tmp_path)
    monkeypatch.setattr(orchestrator, "setup_worktree", lambda worktree_path, branch_name, repo_root=None: None)
    rc = orchestrator.run(
        plan_file=plan_file,
        work_dir=tmp_path / ".autodev",
        use_worktree=True,
        merge_to_main=True,
        sandbox=False,
        max_plan_iteration=1,
        max_iteration=1,
        max_dev_iteration=1,
        max_review_iteration=1,
        max_arbitration_iteration=1,
        push=False,
        dry_run=True,
        timeout_sec=1,
        codex_bin="codex",
        max_retry=0,
    )
    assert rc == 0


def test_orchestrator_source_plan_mutation_detected(tmp_path: Path, monkeypatch) -> None:  # type: ignore[no-untyped-def]
    plan_file = tmp_path / "task.md"
    plan_file.write_text("# task\n", encoding="utf-8")
    ctx_dir = tmp_path / ".autodev" / "task" / "context"
    ctx_dir.mkdir(parents=True, exist_ok=True)
    # Force planning stage to execute.
    plan_out = ctx_dir / "task.plan.md"
    if plan_out.exists():
        plan_out.unlink()

    called = {"n": 0}

    def fake_run_stage(*args, **kwargs):  # type: ignore[no-untyped-def]
        called["n"] += 1
        # Mutate source plan after stage run to trigger digest check.
        plan_file.write_text("# changed\n", encoding="utf-8")
        return 0, "", ""

    monkeypatch.setattr(orchestrator, "run_stage", fake_run_stage)
    rc = orchestrator.run(
        plan_file=plan_file,
        work_dir=tmp_path / ".autodev",
        use_worktree=False,
        merge_to_main=True,
        sandbox=False,
        max_plan_iteration=1,
        max_iteration=1,
        max_dev_iteration=1,
        max_review_iteration=1,
        max_arbitration_iteration=1,
        push=False,
        dry_run=False,
        timeout_sec=1,
        codex_bin="python",
        max_retry=0,
    )
    assert called["n"] >= 1
    assert rc == 1


def test_orchestrator_codex_bin_missing(tmp_path: Path, monkeypatch) -> None:  # type: ignore[no-untyped-def]
    plan_file = tmp_path / "task.md"
    plan_file.write_text("# task\n", encoding="utf-8")
    monkeypatch.setattr(orchestrator.shutil, "which", lambda _: None)
    rc = orchestrator.run(
        plan_file=plan_file,
        work_dir=tmp_path / ".autodev",
        use_worktree=False,
        merge_to_main=True,
        sandbox=False,
        max_plan_iteration=1,
        max_iteration=1,
        max_dev_iteration=1,
        max_review_iteration=1,
        max_arbitration_iteration=1,
        push=False,
        dry_run=False,
        timeout_sec=1,
        codex_bin="codex",
        max_retry=0,
    )
    assert rc == 2


def test_orchestrator_plan_file_missing(tmp_path: Path) -> None:
    rc = orchestrator.run(
        plan_file=tmp_path / "missing.md",
        work_dir=tmp_path / ".autodev",
        use_worktree=False,
        merge_to_main=True,
        sandbox=False,
        max_plan_iteration=1,
        max_iteration=1,
        max_dev_iteration=1,
        max_review_iteration=1,
        max_arbitration_iteration=1,
        push=False,
        dry_run=True,
        timeout_sec=1,
        codex_bin="codex",
        max_retry=0,
    )
    assert rc == 2


def test_cli_invokes_run(monkeypatch, tmp_path: Path) -> None:  # type: ignore[no-untyped-def]
    runner = CliRunner()
    plan_file = tmp_path / "task.md"
    plan_file.write_text("# t\n", encoding="utf-8")

    captured: dict[str, object] = {}

    def fake_run(**kwargs):  # type: ignore[no-untyped-def]
        captured.update(kwargs)
        return 0

    monkeypatch.setattr(cli, "run", fake_run)
    result = runner.invoke(cli.cli, ["-P", str(plan_file), "--dry-run"])
    assert result.exit_code == 0
    assert captured["plan_file"] == plan_file
    assert captured["dry_run"] is True
