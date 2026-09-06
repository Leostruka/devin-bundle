"""Task-adaptive harness recipe selection tests."""
import importlib.util
import os

BUNDLE_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
_spec = importlib.util.spec_from_file_location(
    "context_pressure",
    os.path.join(BUNDLE_ROOT, "scripts", "context-pressure.py"),
)
cp = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(cp)


def test_select_implement_recipe_from_instruction():
    result = cp.select_recipe("Implement a new feature", tools=["read", "edit", "write", "exec"], model="swe-1-7")
    assert result["verdict"] == "routed"
    assert result["recipe"] == "implement"


def test_select_research_recipe_with_web_tools():
    result = cp.select_recipe("Research the latest Python release", tools=["web_search", "webfetch"], model="gemini-3-7-flash")
    assert result["verdict"] == "routed"
    assert result["recipe"] == "research"


def test_fallback_when_no_confident_recipe():
    result = cp.select_recipe("Do something random", tools=["read"], model="glm-5-2", confidence_threshold=0.9)
    assert result["verdict"] == "fallback"
    assert result["recipe"] == "default"


def test_recipe_accepted_when_within_budget_and_beats_baseline():
    result = cp.evaluate_recipe_against_baseline("implement", task_score=0.9, baseline_score=0.7, context_budget_tokens=50000, estimated_tokens=10000)
    assert result["verdict"] == "accepted"


def test_recipe_rejected_when_exceeds_context_budget():
    result = cp.evaluate_recipe_against_baseline("research", task_score=0.9, baseline_score=0.7, context_budget_tokens=5000, estimated_tokens=10000)
    assert result["verdict"] == "rejected"
    assert "budget" in result["reason"]
