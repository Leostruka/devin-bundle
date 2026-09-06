"""Validation smoke test: validate-refinement-evidence.py reports 0 phantoms.

Agent-chosen infrastructure test (tests/validation/), distinct from held-out
behavioral tests. Verifies the refinement evidence validator catches phantom
guardrails (Rule 15 anti-cheat).
"""
import subprocess
import os
import sys


BUNDLE_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
# Import script as module to test deterministic helper functions.
import importlib.util  # noqa: E402
_spec = importlib.util.spec_from_file_location(
    "validate_refinement_evidence",
    os.path.join(BUNDLE_ROOT, "scripts", "validate-refinement-evidence.py"),
)
vre = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(vre)


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


def test_temporal_regression_rejects_catastrophic_forgetting():
    """A refinement that improves the newest batch while degrading a retained
    recent batch must be rejected."""
    current = [0.85, 0.86, 0.87]
    retained = {"batch_n-1": [0.90, 0.91, 0.92]}
    verdict = vre.evaluate_batch_against_retained(current, retained)
    assert verdict["verdict"] == "rejected", verdict
    assert "degraded" in verdict["reason"].lower()


def test_temporal_regression_accepts_genuine_improvement():
    """A refinement that improves the newest batch without degrading retained
    batches is accepted."""
    current = [0.95, 0.96, 0.97]
    retained = {"batch_n-1": [0.80, 0.81, 0.82]}
    verdict = vre.evaluate_batch_against_retained(current, retained)
    assert verdict["verdict"] == "accepted", verdict


def test_temporal_regression_inconclusive_when_underpowered():
    """Too few repeated trials must return inconclusive instead of a pass/fail."""
    current = [0.95]
    retained = {"batch_n-1": [0.80, 0.81, 0.82]}
    verdict = vre.evaluate_batch_against_retained(current, retained, min_trials=3)
    assert verdict["verdict"] == "inconclusive", verdict
    assert "underpowered" in verdict["reason"].lower()
