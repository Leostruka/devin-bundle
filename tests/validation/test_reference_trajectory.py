"""Reference-trajectory alignment tests.

Synthetic trajectories demonstrate failing-step attribution and stable
weakness clustering without LLM involvement.
"""
import sys
from pathlib import Path

ROOT = Path(__file__).parents[2]
sys.path.insert(0, str(ROOT / "scripts"))

import reference_trajectory  # noqa: E402


def test_failing_step_is_localized_to_error_event():
    trajectory = [
        {"step": 1, "tool": "read", "status": "ok"},
        {"step": 2, "tool": "exec", "status": "error", "error_type": "timeout"},
        {"step": 3, "tool": "edit", "status": "ok"},
    ]
    result = reference_trajectory.analyze(trajectory)
    assert result["failing_step"] == 2
    assert result["failure_type"] == "timeout"


def test_missing_failure_returns_none():
    trajectory = [
        {"step": 1, "tool": "read", "status": "ok"},
        {"step": 2, "tool": "exec", "status": "ok"},
    ]
    result = reference_trajectory.analyze(trajectory)
    assert result["failing_step"] is None


def test_clustering_groups_same_error_type():
    trajectories = [
        [{"step": 1, "tool": "exec", "status": "error", "error_type": "timeout"}],
        [{"step": 1, "tool": "exec", "status": "error", "error_type": "timeout"}],
        [{"step": 1, "tool": "read", "status": "error", "error_type": "not_found"}],
    ]
    clusters = reference_trajectory.cluster_weaknesses(trajectories)
    assert clusters["timeout"] == 2
    assert clusters["not_found"] == 1


def test_proposed_change_links_evidence_to_failing_step():
    trajectory = [
        {"step": 1, "tool": "read", "status": "ok"},
        {"step": 2, "tool": "exec", "status": "error", "error_type": "timeout"},
    ]
    proposal = reference_trajectory.propose_harness_change(trajectory)
    assert proposal["target_step"] == 2
    assert proposal["failure_type"] == "timeout"
    assert "evidence" in proposal
    assert proposal["evidence"]["step"] == 2
