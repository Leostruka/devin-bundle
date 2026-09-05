#!/usr/bin/env python3
"""Reference-trajectory alignment for self-improvement evidence.

Analyzes structured behavioral event trajectories to:
1. Localize the failing step and failure type.
2. Cluster repeated weaknesses across trajectories.
3. Propose minimal, evidence-linked harness changes.

All attribution is deterministic and based on explicit invariants before any
LLM-guided credit assignment is considered.
"""
from collections import Counter


def analyze(trajectory):
    """Return failing step and failure type for a single trajectory.

    Trajectory is a list of event dicts with keys: step, tool, status,
    and optional error_type. The first event with status != 'ok' is the
    failing step. Later events are not causal for this failure.
    """
    for event in trajectory:
        if event.get("status") != "ok":
            return {
                "failing_step": event.get("step"),
                "failure_type": event.get("error_type") or event.get("status"),
                "tool": event.get("tool"),
                "evidence": event,
            }
    return {
        "failing_step": None,
        "failure_type": None,
        "tool": None,
        "evidence": None,
    }


def cluster_weaknesses(trajectories):
    """Cluster repeated weakness types across multiple trajectories.

    Returns a Counter mapping failure_type to occurrence count.
    """
    counts = Counter()
    for trajectory in trajectories:
        result = analyze(trajectory)
        if result["failure_type"]:
            counts[result["failure_type"]] += 1
    return counts


def propose_harness_change(trajectory, supported_types=None):
    """Propose a minimal harness change linked to the failing step evidence.

    If the failure type is not in supported_types, the proposal is a stop
    decision with explicit rationale (reject unsupported credit assignment).
    """
    result = analyze(trajectory)
    if result["failing_step"] is None:
        return {"action": "none", "reason": "no failure detected"}

    supported_types = supported_types or {"timeout", "not_found", "parse_error"}
    if result["failure_type"] not in supported_types:
        return {
            "action": "stop",
            "reason": f"unsupported failure type '{result['failure_type']}'",
            "target_step": result["failing_step"],
            "failure_type": result["failure_type"],
            "evidence": result["evidence"],
        }

    return {
        "action": "change",
        "target_step": result["failing_step"],
        "failure_type": result["failure_type"],
        "tool": result["tool"],
        "evidence": result["evidence"],
    }


def compare_attributions(structured_result, llm_attribution):
    """Compare deterministic structured attribution with an LLM attribution.

    Returns agreement (bool) and a diff of mismatched fields. This prevents
    blindly trusting LLM credit assignment when structured invariants disagree.
    """
    mismatches = {}
    for key in ("failing_step", "failure_type", "tool"):
        if structured_result.get(key) != llm_attribution.get(key):
            mismatches[key] = (structured_result.get(key), llm_attribution.get(key))
    return {"agreement": not mismatches, "mismatches": mismatches}


if __name__ == "__main__":
    pass
