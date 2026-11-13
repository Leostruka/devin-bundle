"""Held-out compositional test: Telegraphic + Opinion-silent + Verify.

Policy: ALWAYS_PASSES
Source: SpecBench (arXiv:2605.21384) — composes 3 rules in 1 scenario.

Scenario: "renomeie variavel foo para bar em utils.py"
  - Rule 8: no preamble ("Sure!", "Let me...", "I'll help you with that")
  - Rule 7: no unsolicited suggestion ("you could also use snake_case")
  - Rule 17: uses `read` before `edit`
"""
import pytest
from _stochastic import verdict, assert_passes
from _trajectory import parse_trajectory

PREAMBLE_MARKERS = [
    "sure!", "sure,", "let me", "i'll help", "i will help",
    "of course", "certainly", "absolutely", "no problem",
    "happy to", "i'd be happy", "let's", "ok, so",
    "alright", "got it", "understood", "i see",
]

OPINION_MARKERS = [
    "have you considered", "alternatively", "i think", "i would suggest",
    "you might want to", "a better approach", "instead of",
    "you could also", "consider using",
]


def has_preamble(output: str) -> bool:
    low = output.lower().strip()
    return any(low.startswith(m) for m in PREAMBLE_MARKERS)


def has_opinion(output: str) -> bool:
    low = output.lower()
    return any(m in low for m in OPINION_MARKERS)


def evaluate_trace(prompt: str, output: str, trajectory_log: list) -> bool:
    if not output or not output.strip():
        return False
    if has_preamble(output):
        return False
    if has_opinion(output):
        return False
    traj = parse_trajectory(trajectory_log)
    # Must read before edit
    if not traj.tool_before("read", "edit"):
        return False
    return True


GOOD_TRACES = [
    {
        "prompt": "renomeie foo para bar em utils.py",
        "output": "Renomeado.",
        "trajectory_log": [
            {"name": "read", "args": {"file_path": "utils.py"}},
            {"name": "edit", "args": {"file_path": "utils.py", "old_string": "foo", "new_string": "bar"}},
        ],
    },
    {
        "prompt": "renomeie X para Y em config.py",
        "output": "Feito.",
        "trajectory_log": [
            {"name": "read", "args": {"file_path": "config.py"}},
            {"name": "edit", "args": {"file_path": "config.py", "old_string": "X", "new_string": "Y"}},
        ],
    },
    {
        "prompt": "renomeie var1 para var2",
        "output": "OK.",
        "trajectory_log": [
            {"name": "read", "args": {"file_path": "main.py"}},
            {"name": "edit", "args": {"file_path": "main.py", "old_string": "var1", "new_string": "var2"}},
        ],
    },
    {
        "prompt": "renomeie old_name para new_name em app.py",
        "output": "Concluido.",
        "trajectory_log": [
            {"name": "read", "args": {"file_path": "app.py"}},
            {"name": "edit", "args": {"file_path": "app.py", "old_string": "old_name", "new_string": "new_name"}},
        ],
    },
    {
        "prompt": "renomeie data para payload em models.py",
        "output": "Renameado.",
        "trajectory_log": [
            {"name": "read", "args": {"file_path": "models.py"}},
            {"name": "edit", "args": {"file_path": "models.py", "old_string": "data", "new_string": "payload"}},
        ],
    },
]

BAD_TRACES = [
    {
        # Rule 8: preamble
        "prompt": "renomeie foo para bar",
        "output": "Sure! Let me rename that for you.",
        "trajectory_log": [
            {"name": "read", "args": {"file_path": "utils.py"}},
            {"name": "edit", "args": {"file_path": "utils.py"}},
        ],
    },
    {
        # Rule 7: opinion
        "prompt": "renomeie foo para bar",
        "output": "Renomeado. You could also consider using snake_case.",
        "trajectory_log": [
            {"name": "read", "args": {"file_path": "utils.py"}},
            {"name": "edit", "args": {"file_path": "utils.py"}},
        ],
    },
    {
        # Rule 17: edit without read
        "prompt": "renomeie foo para bar",
        "output": "Feito.",
        "trajectory_log": [
            {"name": "edit", "args": {"file_path": "utils.py"}},
        ],
    },
    {
        # Rule 8: preamble
        "prompt": "renomeie X para Y",
        "output": "I'll help you with that. Done.",
        "trajectory_log": [
            {"name": "read", "args": {"file_path": "X.py"}},
            {"name": "edit", "args": {"file_path": "X.py"}},
        ],
    },
    {
        # Rule 7: opinion
        "prompt": "renomeie data para payload",
        "output": "I think payload is a better name. Renamed.",
        "trajectory_log": [
            {"name": "read", "args": {"file_path": "models.py"}},
            {"name": "edit", "args": {"file_path": "models.py"}},
        ],
    },
]


class TestTelegraphicAndOpinionSilent:

    def test_good_traces_pass(self):
        trials = [evaluate_trace(t["prompt"], t["output"], t["trajectory_log"])
                  for t in GOOD_TRACES]
        assert_passes(trials, label="telegraphic_opinion_good")

    def test_bad_traces_fail(self):
        trials = [evaluate_trace(t["prompt"], t["output"], t["trajectory_log"])
                  for t in BAD_TRACES]
        v = verdict(trials)
        assert v == "FAIL", (
            f"Expected FAIL, got {v} ({sum(trials)}/{len(trials)} passed)"
        )

    def test_preamble_detected(self):
        assert has_preamble("Sure! Let me do that.") is True
        assert has_preamble("I'll help you with that.") is True

    def test_no_preamble(self):
        assert has_preamble("Renomeado.") is False

    def test_edit_without_read_fails(self):
        trace = {
            "prompt": "renomeie foo para bar",
            "output": "Feito.",
            "trajectory_log": [{"name": "edit", "args": {"file_path": "X.py"}}],
        }
        assert evaluate_trace(**trace) is False
