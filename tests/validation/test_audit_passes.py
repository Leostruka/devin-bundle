"""Validation smoke test: audit.py runs and exits 0.

This is an agent-chosen infrastructure test (tests/validation/), distinct
from held-out behavioral tests (tests/held-out/). It verifies the audit
script itself works, not agent behavior. The gap check in check-push-green.py
compares validation (these) vs held-out (independent) — if validation passes
but held-out fails, the push is blocked (Rule 16 reward hacking guard).
"""
import json
import subprocess
from pathlib import Path


ROOT = Path(__file__).parents[2]


def run_audit():
    return subprocess.run(
        ["python", "audit.py"],
        capture_output=True,
        text=True,
        cwd=ROOT,
        timeout=60,
    )


def test_audit_exits_zero():
    """audit.py must exit 0 with no errors."""
    result = run_audit()
    assert result.returncode == 0, f"audit.py exited {result.returncode}\n{result.stdout[-500:]}"
    assert "Errors:   0" in result.stdout, f"audit.py has errors\n{result.stdout[-500:]}"


def test_audit_check_count():
    """audit.py should report 26 checks (updates when new checks added)."""
    result = run_audit()
    assert "31 CHECKS PASSED" in result.stdout or "Errors:   0" in result.stdout, \
        f"audit.py check count mismatch\n{result.stdout[-300:]}"


def test_audit_validates_declared_counts():
    """audit.py must compare declared counts with their canonical sources."""
    manifest = json.loads((ROOT / "manifest.json").read_text(encoding="utf-8-sig"))
    result = run_audit()
    assert f"skill_count = {manifest['skill_count']}" in result.stdout, result.stdout[-500:]
    assert f"rule_count = {manifest['rule_count']}" in result.stdout, result.stdout[-500:]
