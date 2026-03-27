#!/usr/bin/env python3
"""Run tests and enforce coverage gates."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


MIN_TOTAL_COVERAGE = 80.0
LOGIC_FILE_MIN_STATEMENTS = 5
EXCLUDED_LOGIC_FILES = {"__init__.py", "__main__.py", "constants.py"}


def _run_tests() -> int:
    cmd = [
        ".venv/bin/python",
        "-m",
        "pytest",
        "--cov=autodev",
        "--cov-report=term-missing",
        "--cov-report=json:coverage.json",
    ]
    result = subprocess.run(cmd)
    return result.returncode


def _to_repo_relative(path: str, repo_root: Path) -> str:
    p = Path(path)
    if not p.is_absolute():
        return p.as_posix()
    try:
        return p.resolve().relative_to(repo_root.resolve()).as_posix()
    except ValueError:
        return p.as_posix()


def _is_logic_file(rel_path: str, num_statements: int) -> bool:
    if not rel_path.startswith("autodev/"):
        return False
    if Path(rel_path).name in EXCLUDED_LOGIC_FILES:
        return False
    return num_statements >= LOGIC_FILE_MIN_STATEMENTS


def _check_gates(coverage_json_file: Path) -> int:
    data = json.loads(coverage_json_file.read_text(encoding="utf-8"))
    totals = data.get("totals", {})
    total_pct = float(totals.get("percent_covered", 0.0))
    if total_pct < MIN_TOTAL_COVERAGE:
        print(
            f"[gate] FAIL: total coverage {total_pct:.2f}% < {MIN_TOTAL_COVERAGE:.2f}%",
            file=sys.stderr,
        )
        return 1

    repo_root = Path.cwd()
    zero_covered_logic_files: list[str] = []
    files = data.get("files", {})
    for file_path, detail in files.items():
        summary = detail.get("summary", {})
        num_statements = int(summary.get("num_statements", 0))
        covered_lines = int(summary.get("covered_lines", 0))
        rel_path = _to_repo_relative(file_path, repo_root)
        if _is_logic_file(rel_path, num_statements) and covered_lines == 0:
            zero_covered_logic_files.append(rel_path)

    if zero_covered_logic_files:
        print("[gate] FAIL: logic files with 0 coverage:", file=sys.stderr)
        for rel in sorted(zero_covered_logic_files):
            print(f"  - {rel}", file=sys.stderr)
        return 1

    print(
        f"[gate] PASS: total coverage {total_pct:.2f}% >= {MIN_TOTAL_COVERAGE:.2f}% "
        "and no logic file has 0 coverage."
    )
    return 0


def main() -> int:
    rc = _run_tests()
    if rc != 0:
        return rc

    coverage_json_file = Path("coverage.json")
    if not coverage_json_file.exists():
        print("[gate] FAIL: coverage.json not found", file=sys.stderr)
        return 1
    return _check_gates(coverage_json_file)


if __name__ == "__main__":
    raise SystemExit(main())
