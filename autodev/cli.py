"""CLI entrypoint for autodev."""

from __future__ import annotations

from pathlib import Path

import click

from .orchestrator import run


@click.command(help="自动化开发流程：计划 → 开发 → 审查 → 仲裁，循环直到通过。")
@click.option(
    "-P",
    "--plan-file",
    required=True,
    type=click.Path(path_type=Path),
    help="计划文件路径（.md）。",
)
@click.option(
    "-T",
    "--work-tree",
    is_flag=True,
    default=False,
    help="使用独立 git worktree 进行开发。",
)
@click.option(
    "-w",
    "--work-dir",
    type=click.Path(path_type=Path),
    default=Path(".autodev"),
    show_default=True,
    help="autodev 工作目录（存放 context、worktree 等）。",
)
@click.option(
    "-M",
    "--merge/--no-merge",
    default=False,
    show_default=True,
    help="worktree 模式：--merge 将 worktree 分支合并到主分支；--no-merge（默认）将主分支合并到 worktree 并推送 worktree 分支。非 worktree 模式忽略此选项。",
)
@click.option("--sandbox/--no-sandbox", default=False, show_default=True)
@click.option(
    "--max-plan-iteration",
    type=click.IntRange(1),
    default=20,
    show_default=True,
    help="计划阶段最大循环轮次。",
)
@click.option(
    "--max-iteration",
    type=click.IntRange(1),
    default=5,
    show_default=True,
    help="开发-审查最大循环轮次（外层）。",
)
@click.option(
    "--max-dev-iteration",
    type=click.IntRange(1),
    default=100,
    show_default=True,
    help="每个开发-审查轮次内，开发阶段最大连续轮次（内层开发循环）。",
)
@click.option(
    "--max-review-iteration",
    type=click.IntRange(1),
    default=5,
    show_default=True,
    help="每个开发轮次内，审查阶段最大连续轮次（用于处理“审查未完成”）。",
)
@click.option(
    "--max-arbitration-iteration",
    type=click.IntRange(1),
    default=5,
    show_default=True,
    help="仲裁阶段最大轮次（超过后流程失败）。",
)
@click.option(
    "--push/--no-push",
    default=True,
    show_default=True,
    help="审查通过后自动 push（含冲突解决）。",
)
@click.option(
    "--dry-run",
    is_flag=True,
    help="仅打印将执行的 codex 命令与提示词，不实际运行。",
)
@click.option(
    "--timeout-sec",
    type=click.IntRange(1),
    default=7200,
    show_default=True,
    help="每次调用 codex 的超时时间（秒）。",
)
@click.option(
    "--codex-bin",
    default="codex",
    show_default=True,
    help="codex 可执行文件路径。",
)
@click.option(
    "--model",
    default="gpt-5.4",
    show_default=True,
    help="codex 使用的模型。",
)
@click.option(
    "--thinking-effort",
    type=click.Choice(["minimal", "low", "medium", "high", "xhigh"]),
    default="medium",
    show_default=True,
    help="codex 的 thinking effort（映射到 model_reasoning_effort）。",
)
@click.option(
    "--max-retry",
    type=click.IntRange(0),
    default=10,
    show_default=True,
    help="codex 调用失败后的最大重试次数（每次等待 60 秒）。",
)
def cli(
    plan_file: Path,
    work_tree: bool,
    work_dir: Path,
    merge: bool,
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
    model: str,
    thinking_effort: str,
    max_retry: int,
) -> None:
    raise SystemExit(
        run(
            plan_file=plan_file,
            work_dir=work_dir,
            use_worktree=work_tree,
            merge_to_main=merge,
            sandbox=sandbox,
            max_plan_iteration=max_plan_iteration,
            max_iteration=max_iteration,
            max_dev_iteration=max_dev_iteration,
            max_review_iteration=max_review_iteration,
            max_arbitration_iteration=max_arbitration_iteration,
            push=push,
            dry_run=dry_run,
            timeout_sec=timeout_sec,
            codex_bin=codex_bin,
            model=model,
            thinking_effort=thinking_effort,
            max_retry=max_retry,
        )
    )


def main() -> None:
    cli()


if __name__ == "__main__":
    main()
