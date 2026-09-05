"""Bidirectional patch verification tests."""
import importlib.util
import os

BUNDLE_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
_spec = importlib.util.spec_from_file_location(
    "refine_review_prompt",
    os.path.join(BUNDLE_ROOT, "scripts", "refine-review-prompt.py"),
)
rr = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(rr)


def _patch_aligned():
    return """--- scripts/context-pressure.py
+++ scripts/context-pressure.py
@@ -10,0 +10,6 @@
+def evaluate_refinement_cost_benefit(before_tokens, after_tokens, benefit_score):
+    # Reject refinements whose permanent context growth exceeds measured benefit.
+    growth = after_tokens - before_tokens
+    if growth > benefit_score * 200000:
+        return {"verdict": "rejected"}
+    return {"verdict": "accepted"}
"""


def _patch_unrelated():
    return """--- scripts/weather.py
+++ scripts/weather.py
@@ -1,0 +1,2 @@
+def get_weather(city):
+    return "sunny"
"""


def _patch_symptom_only():
    return """--- scripts/context-pressure.py
+++ scripts/context-pressure.py
@@ -10,0 +10,2 @@
+# TODO: investigate context pressure
+pass
"""


def test_aligned_patch_passes():
    requested = "Reject refinements whose permanent context growth is not justified by measured benefit"
    result = rr.verify_patch_alignment(requested, _patch_aligned())
    assert result["verdict"] == "aligned", result


def test_unrelated_patch_fails():
    requested = "Reject refinements whose permanent context growth is not justified by measured benefit"
    result = rr.verify_patch_alignment(requested, _patch_unrelated())
    assert result["verdict"] == "unrelated", result


def test_symptom_only_patch_fails():
    requested = "Reject refinements whose permanent context growth is not justified by measured benefit"
    result = rr.verify_patch_alignment(requested, _patch_symptom_only(), symptom_only_terms=["benefit", "context"])
    assert result["verdict"] == "symptom_only", result
    assert "revision_guidance" in result


def test_reconstruction_blind_to_issue():
    recon = rr.reconstruct_problem_from_patch(_patch_aligned())
    assert "context-pressure" in recon["affected_paths"][0]
    assert "validate" in recon["intent_terms"] or "reject" in recon["intent_terms"]
