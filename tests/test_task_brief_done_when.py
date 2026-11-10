import subprocess
import sys
from pathlib import Path

SCRIPT = (Path(__file__).resolve().parent.parent
          / "skills" / "dispatching-parallel-agents"
          / "scripts" / "task-brief.py")


def run(plan, n, *extra):
    return subprocess.run(
        [sys.executable, str(SCRIPT), str(plan), str(n), *extra],
        capture_output=True, text=True, encoding="utf-8", errors="replace")


PLAN_OK = "## Task 1\nDo the thing.\n\n**Done when:** `pytest -q` passes.\n\n## Task 2\nOther.\n"
PLAN_NO = "## Task 1\nDo the thing with no check at all.\n"


def test_done_when_passes_with_check(tmp_path):
    p = tmp_path / "plan.md"
    p.write_text(PLAN_OK, encoding="utf-8")
    out = tmp_path / "b.md"
    r = run(p, 1, str(out), "--require-done-when")
    assert r.returncode == 0 and out.exists()


def test_require_done_when_rejects_missing(tmp_path):
    p = tmp_path / "plan.md"
    p.write_text(PLAN_NO, encoding="utf-8")
    r = run(p, 1, str(tmp_path / "b.md"), "--require-done-when")
    assert r.returncode == 4 and "Done when" in r.stderr


def test_missing_check_warns_without_flag(tmp_path):
    p = tmp_path / "plan.md"
    p.write_text(PLAN_NO, encoding="utf-8")
    out = tmp_path / "b.md"
    r = run(p, 1, str(out))
    assert r.returncode == 0 and "warn" in r.stderr and out.exists()
