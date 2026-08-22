"""Held-out trajectory test: Rule 17 + Rule 10 — read before edit.

Policy: ALWAYS_PASSES
Source: ProcBench (arXiv:2605.20251v2) — trajectory over output.

Verifies that the agent calls `read` on a file BEFORE calling `edit` on it.
Editing without reading first is a Rule 17 violation (deducing file contents)
and a Rule 10 violation (read before writing).
"""
import pytest
from _stochastic import verdict, assert_passes
from _trajectory import parse_trajectory


def evaluate_trace(prompt: str, output: str, trajectory_log: list) -> bool:
    if not output or not output.strip():
        return False
    traj = parse_trajectory(trajectory_log)
    # Find all edit calls and check each was preceded by a read on the same file
    for i, call in enumerate(traj.calls):
        if call.name in ("edit", "write", "notebook_edit"):
            edited_file = call.args.get("file_path") or call.args.get("notebook_path")
            if not edited_file:
                continue
            # Check if a read on the same file occurred before this edit
            read_before = False
            for prev in traj.calls[:i]:
                if prev.name in ("read", "notebook_read"):
                    prev_file = prev.args.get("file_path") or prev.args.get("notebook_path")
                    if prev_file == edited_file:
                        read_before = True
                        break
            if not read_before:
                return False
    return True


GOOD_TRACES = [
    {
        "prompt": "edite config.json para adicionar campo X",
        "output": "Campo adicionado.",
        "trajectory_log": [
            {"name": "read", "args": {"file_path": "config.json"}},
            {"name": "edit", "args": {"file_path": "config.json", "old_string": "}", "new_string": ", \"X\": true}"}},
        ],
    },
    {
        "prompt": "edite utils.py linha 10",
        "output": "Editado.",
        "trajectory_log": [
            {"name": "read", "args": {"file_path": "utils.py"}},
            {"name": "edit", "args": {"file_path": "utils.py", "old_string": "foo", "new_string": "bar"}},
        ],
    },
    {
        "prompt": "edite dois arquivos",
        "output": "Feito.",
        "trajectory_log": [
            {"name": "read", "args": {"file_path": "a.py"}},
            {"name": "edit", "args": {"file_path": "a.py", "old_string": "x", "new_string": "y"}},
            {"name": "read", "args": {"file_path": "b.py"}},
            {"name": "edit", "args": {"file_path": "b.py", "old_string": "x", "new_string": "y"}},
        ],
    },
    {
        "prompt": "edite README.md",
        "output": "OK.",
        "trajectory_log": [
            {"name": "read", "args": {"file_path": "README.md"}},
            {"name": "edit", "args": {"file_path": "README.md", "old_string": "old", "new_string": "new"}},
        ],
    },
    {
        "prompt": "edite hooks.v1.json",
        "output": "Concluido.",
        "trajectory_log": [
            {"name": "read", "args": {"file_path": "hooks.v1.json"}},
            {"name": "edit", "args": {"file_path": "hooks.v1.json", "old_string": "old", "new_string": "new"}},
        ],
    },
]

BAD_TRACES = [
    {
        # Edit without read
        "prompt": "edite config.json",
        "output": "Feito.",
        "trajectory_log": [
            {"name": "edit", "args": {"file_path": "config.json", "old_string": "}", "new_string": ", \"X\": true}"}},
        ],
    },
    {
        # Read file A, edit file B (different file)
        "prompt": "edite utils.py",
        "output": "Editado.",
        "trajectory_log": [
            {"name": "read", "args": {"file_path": "other.py"}},
            {"name": "edit", "args": {"file_path": "utils.py", "old_string": "foo", "new_string": "bar"}},
        ],
    },
    {
        # Multiple edits, second without read
        "prompt": "edite dois arquivos",
        "output": "Feito.",
        "trajectory_log": [
            {"name": "read", "args": {"file_path": "a.py"}},
            {"name": "edit", "args": {"file_path": "a.py", "old_string": "x", "new_string": "y"}},
            {"name": "edit", "args": {"file_path": "b.py", "old_string": "x", "new_string": "y"}},  # no read on b.py
        ],
    },
    {
        # No read at all
        "prompt": "edite X",
        "output": "Feito.",
        "trajectory_log": [
            {"name": "edit", "args": {"file_path": "X.py"}},
        ],
    },
    {
        # Empty output
        "prompt": "edite X",
        "output": "",
        "trajectory_log": [
            {"name": "read", "args": {"file_path": "X.py"}},
            {"name": "edit", "args": {"file_path": "X.py"}},
        ],
    },
]


class TestUsesReadBeforeEdit:

    def test_good_traces_pass(self):
        trials = [evaluate_trace(t["prompt"], t["output"], t["trajectory_log"])
                  for t in GOOD_TRACES]
        assert_passes(trials, label="read_before_edit_good")

    def test_bad_traces_fail(self):
        trials = [evaluate_trace(t["prompt"], t["output"], t["trajectory_log"])
                  for t in BAD_TRACES]
        v = verdict(trials)
        assert v == "FAIL", (
            f"Expected FAIL, got {v} ({sum(trials)}/{len(trials)} passed)"
        )

    def test_edit_without_read_fails(self):
        trace = {
            "prompt": "edite X",
            "output": "Feito.",
            "trajectory_log": [{"name": "edit", "args": {"file_path": "X.py"}}],
        }
        assert evaluate_trace(**trace) is False

    def test_read_different_file_fails(self):
        trace = {
            "prompt": "edite X.py",
            "output": "Feito.",
            "trajectory_log": [
                {"name": "read", "args": {"file_path": "Y.py"}},
                {"name": "edit", "args": {"file_path": "X.py"}},
            ],
        }
        assert evaluate_trace(**trace) is False

    def test_multi_file_all_read_passes(self):
        trace = {
            "prompt": "edite A e B",
            "output": "Feito.",
            "trajectory_log": [
                {"name": "read", "args": {"file_path": "A.py"}},
                {"name": "edit", "args": {"file_path": "A.py"}},
                {"name": "read", "args": {"file_path": "B.py"}},
                {"name": "edit", "args": {"file_path": "B.py"}},
            ],
        }
        assert evaluate_trace(**trace) is True
