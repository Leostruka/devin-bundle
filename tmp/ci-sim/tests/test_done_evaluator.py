import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SCRIPT = ROOT / "scripts" / "done-evaluator.py"

sys.path.insert(0, str(ROOT / "scripts"))
import importlib.util  # noqa: E402

spec = importlib.util.spec_from_file_location("done_evaluator", SCRIPT)
de = importlib.util.module_from_spec(spec)
spec.loader.exec_module(de)


# --- fixtures: wrong self-declared done must be caught ---

FALSE_DONE_TESTS_FAIL = """
Working on issue 03...
pytest tests/test_x.py
FAILED tests/test_x.py::test_thing - assert 1 == 2
1 failed, 3 passed
All done, issue resolved.
"""

FALSE_DONE_NO_RUN = """
I implemented the fix in foo.py. I didn't run the tests but the logic
is straightforward. Done, moving to the next ticket.
"""

FALSE_DONE_BLOCKED = """
The migration failed with a Traceback on step 3. I couldn't resolve it.
Marking as done since the rest is complete.
"""

UNCHECKED_TASK = """# Issue 05

## Acceptance criteria
- [ ] API returns 200
- [ ] migration applied
"""
UNCHECKED_TRANSCRIPT = "Implemented both endpoints. Done."

# --- fixtures: true done must NOT regress ---

TRUE_DONE = """
pytest tests/test_x.py -q
42 passed, 0 failed
python audit.py -> Errors: 0, Warnings: 0
All checks pass. Task complete, marking resolved.
"""

CHECKED_TASK = """# Issue 05

## Acceptance criteria
- [x] API returns 200
- [x] migration applied
"""


def test_false_done_test_failure():
    v, _ = de.grade(FALSE_DONE_TESTS_FAIL)
    assert v == "not_done"


def test_false_done_no_run():
    v, _ = de.grade(FALSE_DONE_NO_RUN)
    assert v == "not_done"


def test_false_done_blocked():
    v, _ = de.grade(FALSE_DONE_BLOCKED)
    assert v == "not_done"


def test_false_done_unchecked_acceptance():
    v, s = de.grade(UNCHECKED_TRANSCRIPT, UNCHECKED_TASK)
    assert v == "not_done"
    assert any(x.startswith("unchecked_acceptance") for x in s)


def test_true_done_passes():
    v, s = de.grade(TRUE_DONE, CHECKED_TASK)
    assert v == "done"
    assert "verify_evidence" in s


def test_claim_without_evidence_is_uncertain():
    v, _ = de.grade("Everything is done and shipped.")
    assert v == "uncertain"


def test_strict_exit_code(tmp_path):
    t = tmp_path / "t.txt"
    t.write_text(FALSE_DONE_TESTS_FAIL, encoding="utf-8")
    r = subprocess.run(
        [sys.executable, str(SCRIPT), "--transcript", str(t), "--strict"],
        capture_output=True, text=True, encoding="utf-8", errors="replace")
    assert r.returncode == 4
    assert json.loads(r.stdout)["verdict"] == "not_done"


def test_emit_brief_shape(tmp_path):
    t = tmp_path / "t.txt"
    t.write_text(TRUE_DONE, encoding="utf-8")
    r = subprocess.run(
        [sys.executable, str(SCRIPT), "--transcript", str(t),
         "--emit-brief"],
        capture_output=True, text=True, encoding="utf-8", errors="replace")
    d = json.loads(r.stdout)
    b = d["brief"]
    assert b["role"] == "done_grader"
    assert b["required_output"]["done"] == "bool"
    assert "transcript_tail" in b
