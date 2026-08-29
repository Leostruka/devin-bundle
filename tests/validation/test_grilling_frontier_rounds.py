"""Validation test for grilling frontier rounds respecting ask_user_question tool limits.

This test is the seam for the skill's question-selection rules.
It proves that the skill tells the agent to split frontiers that exceed
the ask_user_question limit, and it simulates fixtures to show the
turn/coverage/omission impact.
"""
import json
import os
import subprocess
import sys

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
SKILL_PATH = os.path.join(ROOT, "skills", "grilling", "SKILL.md")
VALIDATE_SCRIPT = os.path.join(ROOT, "scripts", "validate-tool-args.py")
FIXTURES_DIR = os.path.join(ROOT, "tests", "fixtures", "grilling-frontier")


def read_skill():
    with open(SKILL_PATH, encoding="utf-8") as f:
        return f.read().lower()


def run_validate(tool_name, tool_input):
    payload = json.dumps({
        "hook_event_name": "PreToolUse",
        "tool_name": tool_name,
        "tool_input": tool_input,
        "session_id": "test",
    })
    result = subprocess.run(
        [sys.executable, VALIDATE_SCRIPT],
        input=payload,
        capture_output=True,
        text=True,
        timeout=10,
        cwd=ROOT,
    )
    return result.returncode, result.stdout.strip()


def ask_user_question_payload(questions):
    return {
        "questions": [
            {"question": q["question"], "header": q["id"], "options": [{"label": "yes"}, {"label": "no"}]}
            for q in questions
        ]
    }


def test_ask_user_question_accepts_4_and_blocks_5():
    """The actual Devin CLI hook blocks >4 questions and >4 options."""
    for n in (4, 5):
        questions = [{"question": f"Q{i}?", "header": f"H{i}", "options": [{"label": "a"}, {"label": "b"}]} for i in range(n)]
        code, out = run_validate("ask_user_question", {"questions": questions})
        if n == 4:
            assert code == 0, f"4 questions should pass, got {code}: {out}"
        else:
            assert code == 2, f"5 questions should be blocked, got {code}: {out}"
            assert "at most 4 questions" in out


def test_skill_requires_question_limits_and_recomputation():
    """The skill must cap calls, await answers, and recompute dependencies."""
    text = read_skill()
    assert "1-4 questions per call" in text
    assert "wait for the answers" in text
    assert "recompute the frontier" in text
    assert "never include a question in the same call as an unanswered prerequisite" in text


def test_skill_requires_2_to_4_options_per_question():
    """The grilling skill must enforce the complete option range."""
    assert "2-4 options per multiple-choice question" in read_skill()


def test_ask_user_question_enforces_option_boundaries():
    for n, expected in ((1, 2), (2, 0), (4, 0), (5, 2)):
        options = [{"label": f"option-{i}"} for i in range(n)]
        code, _ = run_validate("ask_user_question", {
            "questions": [{"question": "Q?", "header": "Q", "options": options}],
        })
        assert code == expected


def load_fixture(name):
    path = os.path.join(FIXTURES_DIR, name)
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def chunk_size_from_skill():
    """Read the skill to decide whether the agent would chunk the frontier."""
    return 4 if "1-4 questions per call" in read_skill() else None


def simulate_frontier(fixture_name):
    """Simulate a frontier-round grilling session on a fixture.

    Returns (turns, covered, omitted, blocked) where
    - turns: number of ask_user_question calls made,
    - covered: set of question ids actually asked,
    - omitted: set of question ids never asked,
    - blocked: whether any generated call would be blocked by validate-tool-args.
    """
    questions = {q["id"]: q for q in load_fixture(fixture_name)}
    answered = set()
    covered = set()
    turns = 0
    blocked = False
    chunk = chunk_size_from_skill()

    while True:
        frontier = [
            q for q in questions.values()
            if q["id"] not in answered and all(d in answered for d in q["depends_on"])
        ]
        if not frontier:
            break
        # Old skill asks the whole frontier; new skill chunks at the tool limit.
        # Recompute the frontier after every batch so newly-unblocked questions can
        # join a later batch in the same round.
        if chunk is None:
            batch = frontier
        else:
            batch = frontier[:chunk]
        payload = ask_user_question_payload(batch)
        code, _ = run_validate("ask_user_question", payload)
        if code != 0:
            blocked = True
            break
        turns += 1
        for q in batch:
            covered.add(q["id"])
            answered.add(q["id"])

    omitted = set(questions) - covered
    return turns, covered, omitted, blocked


@pytest.mark.parametrize("fixture,expected_turns,expected_blocked,expected_omitted_count", [
    ("independent.json", 2, False, 0),
    ("dependent.json", 6, False, 0),
    ("mixed.json", 2, False, 0),
])
def test_frontier_simulation(fixture, expected_turns, expected_blocked, expected_omitted_count):
    """Frontier rounds must cover all questions without violating the ask_user_question limit."""
    turns, covered, omitted, blocked = simulate_frontier(fixture)
    assert blocked is False, f"{fixture}: generated ask_user_question was blocked (frontier too large)"
    assert turns == expected_turns, f"{fixture}: expected {expected_turns} turns, got {turns}"
    assert len(omitted) == expected_omitted_count, f"{fixture}: expected {expected_omitted_count} omitted, got {len(omitted)}"
    assert len(covered) == len(load_fixture(fixture)), f"{fixture}: incomplete coverage"
