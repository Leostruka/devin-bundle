"""Validation smoke test: validate-refinement-evidence.py reports 0 phantoms.

Agent-chosen infrastructure test (tests/validation/), distinct from held-out
behavioral tests. Verifies the refinement evidence validator catches phantom
guardrails (Rule 15 anti-cheat).
"""
import subprocess
import os


def test_refinement_evidence_no_phantoms():
    """validate-refinement-evidence.py must report 0 phantom suspects."""
    bundle_root = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
    result = subprocess.run(
        ["python", "scripts/validate-refinement-evidence.py"],
        capture_output=True,
        text=True,
        cwd=bundle_root,
        timeout=60,
    )
    assert result.returncode == 0, f"validate-refinement-evidence.py exited {result.returncode}"
    output = (result.stdout or "") + (result.stderr or "")
    assert "Phantom suspects: 0" in output, \
        f"Phantom suspects found in refinement evidence\n{output[-500:]}"
