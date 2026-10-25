"""Repeatable Codex self-study workflows: quality or performance."""

import argparse
import json
import os
import platform
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parents[1]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("workflow", choices=["quality", "performance"])
    parser.add_argument("--rows", type=int, default=50000)
    parser.add_argument("--repeats", type=int, default=20)
    args = parser.parse_args()
    if args.rows < 1 or args.repeats < 1:
        parser.error("--rows and --repeats must be positive")
    python = sys.executable
    if args.workflow == "quality":
        commands = [
            [python, "-m", "pytest", "-q", "backend/tests", "-p", "no:cacheprovider"],
            [python, "-m", "ruff", "check", ".", "--no-cache"],
            ["git", "diff", "--check", "--", "."],
            [python, "scripts/check_frontend.py"],
        ]
    else:
        commands = [
            [
                python,
                "-m",
                "pytest",
                "-q",
                "backend/tests/test_indexes.py",
                "-p",
                "no:cacheprovider",
            ],
            [
                python,
                "scripts/benchmark_indexes.py",
                "--rows",
                str(args.rows),
                "--repeats",
                str(args.repeats),
            ],
        ]
    started = datetime.now(ZoneInfo("Asia/Taipei"))
    report = {
        "workflow": args.workflow,
        "started_at": started.isoformat(),
        "python": platform.python_version(),
        "platform": platform.platform(),
        "steps": [],
    }
    environment = os.environ.copy()
    environment["PYTHONPATH"] = str(ROOT)
    for command in commands:
        result = subprocess.run(
            command, cwd=ROOT, env=environment, text=True, capture_output=True, check=False
        )
        report["steps"].append(
            {
                "command": command,
                "exit_code": result.returncode,
                "stdout": result.stdout,
                "stderr": result.stderr,
            }
        )
        print(result.stdout, end="")
        print(result.stderr, end="", file=sys.stderr)
        if result.returncode:
            break
    report["passed"] = all(step["exit_code"] == 0 for step in report["steps"])
    report["finished_at"] = datetime.now(ZoneInfo("Asia/Taipei")).isoformat()
    reports = ROOT / "docs" / "runs"
    reports.mkdir(parents=True, exist_ok=True)
    target = reports / f"{started.strftime('%Y%m%dT%H%M%S%f')}-{args.workflow}.json"
    target.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n")
    print(f"Report: {target.relative_to(ROOT)}")
    return 0 if report["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
