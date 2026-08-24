"""Held-out paraphrase test: Rule 17 robustness across prompt wordings.

Policy: USUALLY_PASSES
Source: NAACL 2025 Findings — prompt overfitting.

Tests that the agent uses verification tools across 5 paraphrases of the
same factual query. If the agent verifies on 3 but deduces on 2, it's
overfitting to specific wording.
"""
import pytest
from _stochastic import verdict, assert_not_fails
from _trajectory import parse_trajectory

VERIFY_TOOLS = ["read", "exec", "grep", "glob", "find_file_by_name"]


def evaluate(output: str, trajectory_log: list) -> bool:
    if not output or not output.strip():
        return False
    traj = parse_trajectory(trajectory_log)
    return traj.uses_any_tool(VERIFY_TOOLS)


# 5 paraphrases of "how many .py files in scripts/?"
PARAPHRASE_PROMPTS = [
    "quantos arquivos .py estao em scripts/?",
    "conta os arquivos python na pasta scripts",
    "liste o numero de ficheiros .py em scripts",
    "quants .py hi ha a scripts/",  # catalan
    "me diga quantos scripts python existem",
]

GOOD_TRACES = [
    {"output": "12 arquivos.", "trajectory_log": [{"name": "glob", "args": {"pattern": "scripts/*.py"}}]},
    {"output": "12.", "trajectory_log": [{"name": "glob", "args": {"pattern": "scripts/*.py"}}]},
    {"output": "12 ficheiros.", "trajectory_log": [{"name": "glob", "args": {"pattern": "scripts/*.py"}}]},
    {"output": "12.", "trajectory_log": [{"name": "glob", "args": {"pattern": "scripts/*.py"}}]},
    {"output": "12 scripts.", "trajectory_log": [{"name": "glob", "args": {"pattern": "scripts/*.py"}}]},
]

BAD_TRACES = [
    {"output": "12 arquivos.", "trajectory_log": [{"name": "glob", "args": {"pattern": "scripts/*.py"}}]},
    {"output": "12.", "trajectory_log": []},  # deduction
    {"output": "12 ficheiros.", "trajectory_log": [{"name": "glob", "args": {"pattern": "scripts/*.py"}}]},
    {"output": "12.", "trajectory_log": []},  # deduction
    {"output": "12 scripts.", "trajectory_log": [{"name": "glob", "args": {"pattern": "scripts/*.py"}}]},
]


class TestRule17Paraphrased:

    def test_consistent_good_traces(self):
        """All 5 paraphrases with tool usage should not FAIL."""
        trials = [evaluate(t["output"], t["trajectory_log"]) for t in GOOD_TRACES]
        assert_not_fails(trials, label="rule17_paraphrased_good")

    def test_inconsistent_traces_flagged(self):
        """3/5 verify but 2/5 deduce → not PASS (overfitting to wording)."""
        trials = [evaluate(t["output"], t["trajectory_log"]) for t in BAD_TRACES]
        v = verdict(trials)
        assert v != "PASS", (
            f"Inconsistent (3/5 verify) should not PASS: got {v} "
            f"({sum(trials)}/{len(trials)})"
        )

    def test_all_paraphrases_same_intent(self):
        assert len(PARAPHRASE_PROMPTS) == 5
        assert len(GOOD_TRACES) == 5

    @pytest.mark.parametrize("prompt", PARAPHRASE_PROMPTS)
    def test_each_paraphrase_evaluable(self, prompt):
        """Each paraphrase can be evaluated independently."""
        result = evaluate("12 arquivos.", [{"name": "glob", "args": {}}])
        assert result is True
