"""Prompt bloat / cost-benefit gate tests."""
import importlib.util
import os
import sys

BUNDLE_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
_spec = importlib.util.spec_from_file_location(
    "context_pressure",
    os.path.join(BUNDLE_ROOT, "scripts", "context-pressure.py"),
)
cp = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(cp)


def test_rejects_expensive_low_benefit_refinement():
    """A refinement that adds many permanent tokens for tiny benefit is rejected."""
    before = 10_000
    after = 50_000  # 40K tokens growth
    benefit = 0.01  # 1% improvement
    verdict = cp.evaluate_refinement_cost_benefit(before, after, benefit)
    assert verdict["verdict"] == "rejected", verdict


def test_accepts_cheap_high_benefit_refinement():
    """A refinement with modest token growth and strong benefit is accepted."""
    before = 10_000
    after = 11_000
    benefit = 0.20  # 20% improvement
    verdict = cp.evaluate_refinement_cost_benefit(before, after, benefit)
    assert verdict["verdict"] == "accepted", verdict


def test_rejects_below_minimum_benefit():
    """A refinement with benefit below the minimum threshold is rejected."""
    before = 10_000
    after = 10_500
    benefit = 0.01
    verdict = cp.evaluate_refinement_cost_benefit(before, after, benefit, min_benefit=0.05)
    assert verdict["verdict"] == "rejected", verdict
    assert "below minimum" in verdict["reason"]


def test_measures_permanent_context():
    """Permanent context measurement returns a positive token estimate."""
    tokens = cp.measure_permanent_context(root=BUNDLE_ROOT)
    assert isinstance(tokens, int)
    assert tokens > 0
