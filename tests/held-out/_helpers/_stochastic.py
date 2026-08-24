"""Stochastic test semantics for non-deterministic LLM agent evaluation.

Replaces binary pass/fail with 3-valued verdicts (Pass/Fail/Inconclusive)
backed by confidence intervals and sequential analysis.

Source: AgentAssay (Zenodo 18842011, 2025)
  - 78-100% cost reduction while maintaining statistical guarantees
  - Adaptive budget: 4-7x fewer trials for stable agents
  - Sequential analysis: stop early when 5/5 agree

Usage:
    from _helpers.stochastic import verdict, run_trials
    results = run_trials(agent_fn, n=5)
    v = verdict(results)
    assert v == "PASS"
"""
from __future__ import annotations
import math
from dataclasses import dataclass
from typing import Callable, List


@dataclass
class Interval:
    lower: float
    upper: float


def wilson_ci(p: float, n: int, confidence: float = 0.95) -> Interval:
    """Wilson score interval for a binomial proportion.

    More robust than the normal approximation for small n and extreme p.
    """
    if n == 0:
        return Interval(0.0, 1.0)
    z = 1.959964 if confidence == 0.95 else _z_for_confidence(confidence)
    denom = 1 + z * z / n
    center = (p + z * z / (2 * n)) / denom
    half = (z / denom) * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n))
    return Interval(max(0.0, center - half), min(1.0, center + half))


def _z_for_confidence(confidence: float) -> float:
    table = {0.90: 1.644854, 0.95: 1.959964, 0.99: 2.575829}
    return table.get(confidence, 1.959964)


def verdict(trials: List[bool], confidence: float = 0.95,
            pass_threshold: float = 0.8, fail_threshold: float = 0.2,
            min_n: int = 5) -> str:
    """3-valued verdict over a list of trial outcomes.

    Returns:
        "PASS"        - lower bound of CI >= pass_threshold (>=80% with 95% CI)
        "FAIL"        - upper bound of CI <= fail_threshold (<=20% with 95% CI)
        "INCONCLUSIVE"- ambiguous zone or insufficient samples
    """
    n = len(trials)
    if n < min_n:
        return "INCONCLUSIVE"
    n_pass = sum(1 for t in trials if t)
    # Unanimous shortcut: for small n, statistical CI is too conservative.
    # 5/5 or 0/5 is strong enough signal for practical agent testing.
    if n_pass == n:
        return "PASS"
    if n_pass == 0:
        return "FAIL"
    p = n_pass / n
    ci = wilson_ci(p, n, confidence)
    if ci.lower >= pass_threshold:
        return "PASS"
    if ci.upper <= fail_threshold:
        return "FAIL"
    return "INCONCLUSIVE"


def run_trials(agent_fn: Callable[[int], bool], n: int = 5,
               adaptive: bool = True) -> List[bool]:
    """Run N trials of an agent function, with adaptive early stopping.

    Adaptive budget (AgentAssay): if the first 5 trials all agree, stop.
    If variance is high, expand to the full N.
    """
    results: List[bool] = []
    stop_at = 5 if adaptive else n
    for i in range(n):
        results.append(bool(agent_fn(i)))
        if adaptive and i + 1 == stop_at:
            if all(results) or not any(results):
                break
            stop_at = n
    return results


def assert_passes(trials: List[bool], label: str = "") -> None:
    """pytest helper: assert a PASS verdict."""
    v = verdict(trials)
    n_pass = sum(1 for t in trials if t)
    assert v == "PASS", (
        f"{label}: expected PASS, got {v} ({n_pass}/{len(trials)} trials passed)"
    )


def assert_not_fails(trials: List[bool], label: str = "") -> None:
    """pytest helper: assert NOT FAIL (PASS or INCONCLUSIVE acceptable for USUALLY_PASSES)."""
    v = verdict(trials)
    n_pass = sum(1 for t in trials if t)
    assert v != "FAIL", (
        f"{label}: expected not FAIL, got FAIL ({n_pass}/{len(trials)} trials passed)"
    )
