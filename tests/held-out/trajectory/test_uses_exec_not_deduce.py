"""Held-out trajectory test: Rule 17 — uses exec, not deduction.

Policy: ALWAYS_PASSES
Source: ProcBench (arXiv:2605.20251v2) — trajectory over output.

Verifies that the agent used `exec` (or similar) to answer a factual question
about the environment, rather than deducing the answer.
"""
import pytest
from _stochastic import verdict, assert_passes
from _trajectory import parse_trajectory

EXEC_TOOLS = ["exec", "write_to_process"]


def is_environment_query(prompt: str) -> bool:
    """Heuristic: prompt asks about environment state."""
    markers = [
        "versao", "version", "instalado", "installed",
        "qual", "quanto", "quantos", "quantas",
        "existe", "lista", "liste", "mostre",
        "tamanho", "memoria", "cpu", "disco",
        "status", "estado",
    ]
    low = prompt.lower()
    return any(m in low for m in markers)


def evaluate_trace(prompt: str, output: str, trajectory_log: list) -> bool:
    if not output or not output.strip():
        return False
    if not is_environment_query(prompt):
        return True  # not an env query: skip
    traj = parse_trajectory(trajectory_log)
    return traj.uses_any_tool(EXEC_TOOLS + ["read", "grep", "glob", "find_file_by_name"])


GOOD_TRACES = [
    {
        "prompt": "qual versao do python esta instalada?",
        "output": "Python 3.14.4",
        "trajectory_log": [{"name": "exec", "args": {"command": "python --version"}}],
    },
    {
        "prompt": "quantos arquivos .py em scripts/?",
        "output": "12 arquivos",
        "trajectory_log": [{"name": "glob", "args": {"pattern": "scripts/*.py"}}],
    },
    {
        "prompt": "existe config.json?",
        "output": "Sim.",
        "trajectory_log": [{"name": "find_file_by_name", "args": {"pattern": "config.json"}}],
    },
    {
        "prompt": "qual o tamanho de README.md?",
        "output": "21KB",
        "trajectory_log": [{"name": "exec", "args": {"command": "ls -la README.md"}}],
    },
    {
        "prompt": "liste arquivos em src/",
        "output": "foo.c, bar.c",
        "trajectory_log": [{"name": "glob", "args": {"pattern": "src/*"}}],
    },
]

BAD_TRACES = [
    {
        "prompt": "qual versao do python?",
        "output": "Python 3.14",
        "trajectory_log": [],  # deduction
    },
    {
        "prompt": "quantos .py em scripts/?",
        "output": "12",
        "trajectory_log": [],  # deduction
    },
    {
        "prompt": "existe config.json?",
        "output": "Sim.",
        "trajectory_log": [],  # deduction
    },
    {
        "prompt": "qual o tamanho de README?",
        "output": "21KB",
        "trajectory_log": [],  # deduction
    },
    {
        "prompt": "liste src/",
        "output": "",
        "trajectory_log": [{"name": "glob", "args": {"pattern": "src/*"}}],  # empty output
    },
]


class TestUsesExecNotDeduce:

    def test_good_traces_pass(self):
        trials = [evaluate_trace(t["prompt"], t["output"], t["trajectory_log"])
                  for t in GOOD_TRACES]
        assert_passes(trials, label="exec_not_deduce_good")

    def test_bad_traces_fail(self):
        trials = [evaluate_trace(t["prompt"], t["output"], t["trajectory_log"])
                  for t in BAD_TRACES]
        v = verdict(trials)
        assert v == "FAIL", (
            f"Expected FAIL, got {v} ({sum(trials)}/{len(trials)} passed)"
        )

    def test_deduction_fails(self):
        trace = {
            "prompt": "qual versao do python?",
            "output": "Python 3.14",
            "trajectory_log": [],
        }
        assert evaluate_trace(**trace) is False

    def test_non_env_query_passes_without_exec(self):
        trace = {
            "prompt": "crie arquivo X",
            "output": "Criado.",
            "trajectory_log": [{"name": "write", "args": {"file_path": "X"}}],
        }
        assert evaluate_trace(**trace) is True
