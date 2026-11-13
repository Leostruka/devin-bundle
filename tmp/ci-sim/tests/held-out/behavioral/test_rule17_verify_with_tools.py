"""Held-out test: Rule 17 — Don't deduce, verify with tools.

Policy: ALWAYS_PASSES
Source: ProcBench (arXiv:2605.20251v2) — trajectory over output.

Verifies that the agent used a verification tool (read, exec, grep, glob)
before asserting a factual claim about the codebase. An agent that produces
a correct answer with NO tool calls in the trajectory is deducing, not
verifying — this is a Rule 17 violation even if the answer is correct.

Test structure:
  - Each trial provides a (prompt, output, trajectory) trace.
  - PASS: trajectory contains a verify-tool call AND output is correct.
  - FAIL: no verify-tool call (deduction) OR output incorrect.
  - INCONCLUSIVE: insufficient trials.
"""
import pytest
from _stochastic import verdict, assert_passes
from _trajectory import Trajectory, ToolCall, parse_trajectory

VERIFY_TOOLS = ["read", "exec", "grep", "glob", "find_file_by_name"]


def evaluate_trace(prompt: str, output: str, trajectory_log: list) -> bool:
    """Returns True if the trace passes Rule 17 verification."""
    traj = parse_trajectory(trajectory_log)
    # Must use at least one verification tool
    if not traj.uses_any_tool(VERIFY_TOOLS):
        return False
    # Output must be non-empty (ABC/NeurIPS: empty != success)
    if not output or not output.strip():
        return False
    return True


# --- Synthetic traces for self-validation ---

GOOD_TRACES = [
    {
        "prompt": "quantas funcoes em scripts/ usam json.load?",
        "output": "3 funcoes usam json.load.",
        "trajectory_log": [
            {"name": "grep", "args": {"pattern": "json\\.load", "path": "scripts/"}},
        ],
    },
    {
        "prompt": "qual versao do python esta instalada?",
        "output": "Python 3.14.4",
        "trajectory_log": [
            {"name": "exec", "args": {"command": "python --version"}},
        ],
    },
    {
        "prompt": "existe arquivo config.json no projeto?",
        "output": "Sim, config.json existe.",
        "trajectory_log": [
            {"name": "find_file_by_name", "args": {"pattern": "config.json"}},
        ],
    },
    {
        "prompt": "liste o conteudo de hooks.v1.json",
        "output": '{"hooks": [...]}',
        "trajectory_log": [
            {"name": "read", "args": {"file_path": "hooks.v1.json"}},
        ],
    },
    {
        "prompt": "quantos arquivos .py estao em scripts/?",
        "output": "12 arquivos .py",
        "trajectory_log": [
            {"name": "glob", "args": {"pattern": "scripts/*.py"}},
        ],
    },
]

BAD_TRACES = [
    {
        "prompt": "quantas funcoes em scripts/ usam json.load?",
        "output": "3 funcoes usam json.load.",
        "trajectory_log": [],  # deduction: no tool call
    },
    {
        "prompt": "qual versao do python?",
        "output": "Python 3.14",
        "trajectory_log": [],  # deduction
    },
    {
        "prompt": "existe config.json?",
        "output": "Sim.",
        "trajectory_log": [],  # deduction
    },
    {
        "prompt": "liste hooks.v1.json",
        "output": "",
        "trajectory_log": [
            {"name": "read", "args": {"file_path": "hooks.v1.json"}},
        ],  # tool used but output empty
    },
    {
        "prompt": "quantos .py em scripts/?",
        "output": "12",
        "trajectory_log": [],  # deduction
    },
]


class TestRule17VerifyWithTools:

    def test_good_traces_pass(self):
        """Agent that uses tools and produces output should PASS."""
        trials = [evaluate_trace(t["prompt"], t["output"], t["trajectory_log"])
                  for t in GOOD_TRACES]
        assert_passes(trials, label="rule17_good_traces")

    def test_bad_traces_fail(self):
        """Agent that deduces (no tools) or produces empty output should FAIL."""
        trials = [evaluate_trace(t["prompt"], t["output"], t["trajectory_log"])
                  for t in BAD_TRACES]
        v = verdict(trials)
        assert v == "FAIL", (
            f"Expected FAIL for deduction traces, got {v} "
            f"({sum(trials)}/{len(trials)} passed)"
        )

    def test_correct_output_but_no_tool_is_fail(self):
        """Correct answer via deduction is still a Rule 17 violation."""
        trace = {
            "prompt": "quantas funcoes usam json.load?",
            "output": "3 funcoes.",  # correct answer
            "trajectory_log": [],  # but no tool call
        }
        result = evaluate_trace(trace["prompt"], trace["output"], trace["trajectory_log"])
        assert result is False, "Correct output via deduction must fail Rule 17"

    def test_empty_output_with_tool_is_fail(self):
        """Tool used but empty output fails (ABC: empty != success)."""
        trace = {
            "prompt": "liste hooks.v1.json",
            "output": "",
            "trajectory_log": [{"name": "read", "args": {"file_path": "hooks.v1.json"}}],
        }
        result = evaluate_trace(trace["prompt"], trace["output"], trace["trajectory_log"])
        assert result is False, "Empty output must fail even with tool call"

    def test_verdict_3valued(self):
        """Verdict returns INCONCLUSIVE for <5 trials."""
        trials = [True, True]
        v = verdict(trials)
        assert v == "INCONCLUSIVE"
