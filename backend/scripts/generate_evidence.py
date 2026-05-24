#!/usr/bin/env python3
"""Run tests and write portfolio evidence under docs/evidence/ (for Phase 3 report)."""

from __future__ import annotations

import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BACKEND = ROOT / "backend"
EVIDENCE = ROOT / "docs" / "evidence"


def run(cmd: list[str], cwd: Path) -> tuple[int, str]:
    proc = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True)
    out = (proc.stdout or "") + (proc.stderr or "")
    return proc.returncode, out


def main() -> int:
    EVIDENCE.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    header = f"# Empirical validation run\n\nGenerated (UTC): {stamp}\n\n"

    code, pytest_out = run(
        [sys.executable, "-m", "pytest", "-v", "--tb=short"],
        BACKEND,
    )
    (EVIDENCE / "pytest_output.txt").write_text(header + "```\n" + pytest_out + "\n```\n", encoding="utf-8")

    env = {**os.environ, "PYTHONPATH": str(BACKEND)}
    proc_load = subprocess.run(
        [sys.executable, "scripts/load_test_booking.py"],
        cwd=BACKEND,
        capture_output=True,
        text=True,
        env=env,
    )
    code_load = proc_load.returncode
    load_out = (proc_load.stdout or "") + (proc_load.stderr or "")
    (EVIDENCE / "load_test_output.txt").write_text(header + load_out + "\n", encoding="utf-8")

    summary = [
        header,
        "## Summary\n",
        f"- pytest exit code: `{code}` (0 = all passed)\n",
        f"- load test exit code: `{code_load}`\n",
        "- Attach `pytest_output.txt` and `load_test_output.txt` to the Phase 3 report.\n",
        "- CI runs the same pytest suite on GitHub Actions (see `.github/workflows/ci.yml`).\n",
    ]
    (EVIDENCE / "README.md").write_text("".join(summary), encoding="utf-8")

    print(f"Evidence written to {EVIDENCE}")
    return code if code != 0 else code_load


if __name__ == "__main__":
    raise SystemExit(main())
