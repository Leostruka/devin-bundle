"""Unit tests for scripts/spec-consistency.py — fixture plans, no network."""
import json
import subprocess
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parent.parent
SCRIPT = REPO / "scripts" / "spec-consistency.py"


def run_check(plan, root, *extra):
    r = subprocess.run(
        [sys.executable, str(SCRIPT), str(plan), "--root", str(root), *extra],
        capture_output=True, text=True)
    return r, json.loads(r.stdout)


@pytest.fixture
def repo(tmp_path):
    """Minimal repo root: .devin/, one ledger, one ADR, one real file."""
    (tmp_path / ".devin" / "ledgers").mkdir(parents=True)
    (tmp_path / ".devin" / "adr").mkdir(parents=True)
    (tmp_path / ".devin" / "ARCHITECTURE_MANIFEST.md").write_text(
        "# Manifest\n\nTop dirs: `extensions/`, `scripts/`, `tests/`, `.devin/`.\n",
        encoding="utf-8")
    (tmp_path / ".devin" / "adr" / "0001-x.md").write_text("# ADR\n")
    (tmp_path / "scripts").mkdir()
    (tmp_path / "scripts" / "existing.py").write_text("# exists\n")
    (tmp_path / ".devin" / "ledgers" / "clean.md").write_text(
        "# GATES\n\n- [x] G1: thing\n  CHECK: true\n  EVIDENCE: ok\n")
    (tmp_path / ".devin" / "ledgers" / "dirty.md").write_text(
        "# GATES\n\n- [x] G1: claimed\n  CHECK: pytest x\n"
        "  EXPECT: pass\n  EVIDENCE: pending\n")
    return tmp_path


def write_plan(root, body):
    p = root / "plan.md"
    p.write_text(body, encoding="utf-8")
    return p


GOOD_PLAN = """# Good plan

## Global Constraints
- No SendInput anywhere.

- [ ] S1 Create `scripts/new_tool.py` skeleton
- [ ] S2 Modify `scripts/existing.py`
- [ ] S3 Reference `.devin/adr/0001-x.md` and `.devin/ledgers/clean.md`
"""

BAD_PLAN = """# Bad plan

Status: done

## Global Constraints
- No `SendInput` anywhere.

- [ ] S1 Modify `scripts/ghost.py` (claims modify, file absent)
- [x] S2 wired `scripts/never_made.py` (closed task, file absent)
- [ ] S3 use SendInput for typing (banned token in task)
- [ ] S4 see `.devin/ledgers/dirty.md`
"""


def test_good_plan_is_clean(repo):
    plan = write_plan(repo, GOOD_PLAN)
    r, out = run_check(plan, repo)
    assert r.returncode == 0
    assert out["ok"] is True
    assert out["summary"]["errors"] == 0
    statuses = {f["path"]: f["status"] for f in out["checks"]["files"]}
    assert statuses["scripts/new_tool.py"] == "planned_new"
    assert statuses["scripts/existing.py"] == "exists"


def test_missing_modify_target_flagged(repo):
    plan = write_plan(repo, BAD_PLAN)
    r, out = run_check(plan, repo)
    missing = {f["detail"] for f in out["findings"]
               if f["kind"] == "missing_referenced_file"}
    assert "scripts/ghost.py" in missing  # declared Modify of absent file
    assert "scripts/never_made.py" in missing  # closed task -> error
    assert out["ok"] is False


def test_done_claim_with_open_boxes(repo):
    plan = write_plan(repo, BAD_PLAN)
    _, out = run_check(plan, repo)
    kinds = {f["kind"] for f in out["findings"]}
    assert "done_claim_with_open_boxes" in kinds


def test_banned_token_in_task_flagged(repo):
    plan = write_plan(repo, BAD_PLAN)
    _, out = run_check(plan, repo)
    toks = {c["constraint_token"] for c in out["checks"]["constraint_conflicts"]}
    assert "SendInput" in toks


def test_ledger_pending_evidence_flagged(repo):
    plan = write_plan(repo, BAD_PLAN)
    _, out = run_check(plan, repo)
    kinds = {f["kind"] for f in out["findings"]}
    assert "ledger_ticked_gate_pending_evidence" in kinds


def test_strict_exit_code(repo):
    plan = write_plan(repo, BAD_PLAN)
    r, _ = run_check(plan, repo, "--strict")
    assert r.returncode == 1
    r2, _ = run_check(write_plan(repo, GOOD_PLAN), repo, "--strict")
    assert r2.returncode == 0


def test_outside_manifest_dirs(repo):
    plan = write_plan(repo, "- [ ] S1 Create `weird_dir/thing.py`\n")
    _, out = run_check(plan, repo)
    assert "weird_dir/thing.py" in out["checks"]["outside_manifest_dirs"]


def test_missing_plan_exits_2(repo):
    r = subprocess.run([sys.executable, str(SCRIPT), "nope.md",
                        "--root", str(repo)], capture_output=True, text=True)
    assert r.returncode == 2
    assert json.loads(r.stdout)["ok"] is False
