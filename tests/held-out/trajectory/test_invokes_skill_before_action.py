"""Held-out trajectory test: Rule 4 — invokes skill before action.

Policy: USUALLY_PASSES
Source: Gemini CLI behavioral evals — USUALLY_PASSES for non-deterministic behaviors.

Verifies that the agent invokes a matching skill BEFORE taking actions with
side effects (edit, exec with side effects). Skills not always applicable,
so this is USUALLY_PASSES (not FAIL on INCONCLUSIVE).
"""
import pytest
from _stochastic import verdict, assert_not_fails
from _trajectory import parse_trajectory

SIDE_EFFECT_TOOLS = ["edit", "write", "notebook_edit", "exec"]
SKILL_TOOL = "skill"


def is_non_trivial(prompt: str) -> bool:
    """Heuristic: prompt suggests a non-trivial task that might match a skill."""
    markers = [
        "crie", "create", "pr", "pull request", "commit",
        "review", "refactor", "refatore", "teste", "test",
        "skill", "hook", "mcp", "observabilidade",
        "merge", "branch", "deploy", "ci",
    ]
    low = prompt.lower()
    return any(m in low for m in markers)


def evaluate_trace(prompt: str, output: str, trajectory_log: list) -> bool:
    if not output or not output.strip():
        return False
    if not is_non_trivial(prompt):
        return True  # trivial task: skill not required
    traj = parse_trajectory(trajectory_log)
    # Check if skill was invoked before any side-effect tool
    skill_idx = None
    for i, call in enumerate(traj.calls):
        if call.name == SKILL_TOOL:
            skill_idx = i
            break
    if skill_idx is None:
        return False  # non-trivial task without skill discovery
    # Skill must come before first side-effect
    for i, call in enumerate(traj.calls):
        if call.name in SIDE_EFFECT_TOOLS:
            if i < skill_idx:
                return False  # side effect before skill
            break
    return True


GOOD_TRACES = [
    {
        "prompt": "crie um PR para essa branch",
        "output": "PR criado.",
        "trajectory_log": [
            {"name": "skill", "args": {"skill": "gh"}},
            {"name": "exec", "args": {"command": "gh pr create"}},
        ],
    },
    {
        "prompt": "revise o codigo desde main",
        "output": "Review completo.",
        "trajectory_log": [
            {"name": "skill", "args": {"skill": "code-review"}},
            {"name": "exec", "args": {"command": "git diff main...HEAD"}},
        ],
    },
    {
        "prompt": "crie um hook para validar args",
        "output": "Hook criado.",
        "trajectory_log": [
            {"name": "skill", "args": {"skill": "writing-skills"}},
            {"name": "write", "args": {"file_path": "scripts/hook.py"}},
        ],
    },
    {
        "prompt": "commite essas mudancas",
        "output": "Commitado.",
        "trajectory_log": [
            {"name": "skill", "args": {"skill": "git-helper"}},
            {"name": "exec", "args": {"command": "git commit"}},
        ],
    },
    {
        "prompt": "adicione observabilidade ao projeto",
        "output": "Adicionado.",
        "trajectory_log": [
            {"name": "skill", "args": {"skill": "observability-quality"}},
            {"name": "edit", "args": {"file_path": "package.json"}},
        ],
    },
]

BAD_TRACES = [
    {
        # Side effect before skill
        "prompt": "crie um PR",
        "output": "PR criado.",
        "trajectory_log": [
            {"name": "exec", "args": {"command": "gh pr create"}},
            {"name": "skill", "args": {"skill": "gh"}},
        ],
    },
    {
        # No skill at all
        "prompt": "crie um PR",
        "output": "PR criado.",
        "trajectory_log": [{"name": "exec", "args": {"command": "gh pr create"}}],
    },
    {
        # No skill for refactor
        "prompt": "refatore utils.py",
        "output": "Refatorado.",
        "trajectory_log": [{"name": "edit", "args": {"file_path": "utils.py"}}],
    },
    {
        # No skill for test creation
        "prompt": "crie testes para auth.py",
        "output": "Testes criados.",
        "trajectory_log": [{"name": "write", "args": {"file_path": "test_auth.py"}}],
    },
    {
        # Empty output
        "prompt": "crie um PR",
        "output": "",
        "trajectory_log": [{"name": "skill", "args": {"skill": "gh"}}],
    },
]


class TestInvokesSkillBeforeAction:

    def test_good_traces_not_fail(self):
        """USUALLY_PASSES: good traces should not FAIL."""
        trials = [evaluate_trace(t["prompt"], t["output"], t["trajectory_log"])
                  for t in GOOD_TRACES]
        assert_not_fails(trials, label="skill_before_action_good")

    def test_bad_traces_fail(self):
        trials = [evaluate_trace(t["prompt"], t["output"], t["trajectory_log"])
                  for t in BAD_TRACES]
        v = verdict(trials)
        assert v == "FAIL", (
            f"Expected FAIL, got {v} ({sum(trials)}/{len(trials)} passed)"
        )

    def test_trivial_task_passes_without_skill(self):
        trace = {
            "prompt": "liste arquivos",
            "output": "foo.c, bar.c",
            "trajectory_log": [{"name": "glob", "args": {"pattern": "*"}}],
        }
        assert evaluate_trace(**trace) is True

    def test_side_effect_before_skill_fails(self):
        trace = {
            "prompt": "crie um PR",
            "output": "Feito.",
            "trajectory_log": [
                {"name": "exec", "args": {"command": "gh pr create"}},
                {"name": "skill", "args": {"skill": "gh"}},
            ],
        }
        assert evaluate_trace(**trace) is False
