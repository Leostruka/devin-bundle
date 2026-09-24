"""L00 — honest, testable laya_cli contract without models.

Every failure path emits one JSON object on stdout and exits nonzero —
no tracebacks, no partial output. check_questions validates the real
schema: non-empty dict, instructions non-empty string, choice criteria
{label: non-empty description}, score criteria non-empty string list,
noul takes instructions only. Unhashable `type` values return errors,
never crash the validator. No torch/laya imports anywhere in this file.
"""
import json
import subprocess
import sys
from pathlib import Path

import pytest

LAYA_DIR = Path(__file__).resolve().parents[1] / \
    "extensions" / "laya-tools"


def _load(name):
    import importlib.util
    spec = importlib.util.spec_from_file_location(
        name, LAYA_DIR / f"{name}.py")
    mod = importlib.util.module_from_spec(spec)
    sys.modules.setdefault(name, mod)
    spec.loader.exec_module(mod)
    return mod


laya_cli = _load("laya_cli")

CLI = LAYA_DIR / "laya_cli.py"


def run_cli(*argv):
    return subprocess.run([sys.executable, str(CLI), *argv],
                          capture_output=True, text=True, timeout=30)


# --- check_questions: pure validator ----------------------------------------

def test_empty_choice_is_rejected():
    q = {"x": {"type": "choice", "instructions": "Choose",
               "criteria": {}}}
    assert laya_cli.check_questions(q)


def test_questions_must_be_nonempty_dict():
    assert laya_cli.check_questions({})
    assert laya_cli.check_questions([])
    assert laya_cli.check_questions("x")
    assert laya_cli.check_questions(None)


def test_instructions_nonempty_string():
    base = {"x": {"type": "choice",
                  "criteria": {"a": "desc"}}}
    for bad in (None, "", 3, ["x"], {}):
        q = {"x": dict(base["x"], instructions=bad)}
        assert laya_cli.check_questions(q), f"instructions={bad!r}"


def test_unhashable_type_never_crashes():
    for bad in (["choice"], {"t": "choice"}, None, 3):
        q = {"x": {"type": bad, "instructions": "x"}}
        errors = laya_cli.check_questions(q)   # must return, not raise
        assert errors


def test_choice_criteria_content():
    # empty dict
    assert laya_cli.check_questions(
        {"x": {"type": "choice", "instructions": "i",
               "criteria": {}}})
    # non-dict
    assert laya_cli.check_questions(
        {"x": {"type": "choice", "instructions": "i",
               "criteria": ["a"]}})
    # empty description
    assert laya_cli.check_questions(
        {"x": {"type": "choice", "instructions": "i",
               "criteria": {"a": ""}}})
    # non-string label
    assert laya_cli.check_questions(
        {"x": {"type": "choice", "instructions": "i",
               "criteria": {3: "d"}}})
    # valid
    assert not laya_cli.check_questions(
        {"x": {"type": "choice", "instructions": "i",
               "criteria": {"a": "d1", "b": "d2"}}})


def test_score_criteria_ordered_list():
    assert laya_cli.check_questions(
        {"x": {"type": "score", "instructions": "i",
               "criteria": {"a": "b"}}})           # dict, not list
    assert laya_cli.check_questions(
        {"x": {"type": "score", "instructions": "i",
               "criteria": []}})                    # empty
    assert laya_cli.check_questions(
        {"x": {"type": "score", "instructions": "i",
               "criteria": ["ok", 5]}})             # non-string item
    assert not laya_cli.check_questions(
        {"x": {"type": "score", "instructions": "i",
               "criteria": ["bad", "mid", "good"]}})


def test_noul_shape_instructions_only():
    assert not laya_cli.check_questions(
        {"x": {"type": "noul", "instructions": "is this spam?"}})
    # noul takes no criteria — extra field is a shape error
    assert laya_cli.check_questions(
        {"x": {"type": "noul", "instructions": "i",
               "criteria": ["a"]}})


def test_spec_must_be_object():
    assert laya_cli.check_questions({"x": "choice"})
    assert laya_cli.check_questions({"x": None})


# --- CLI surface: JSON out + nonzero exit on every failure -------------------

def test_check_questions_cli_invalid_json(tmp_path):
    f = tmp_path / "q.json"
    f.write_text("{not json")
    r = run_cli("--check-questions", str(f))
    assert r.returncode != 0
    out = json.loads(r.stdout)
    assert out["ok"] is False


def test_check_questions_cli_invalid_schema(tmp_path):
    f = tmp_path / "q.json"
    f.write_text(json.dumps({"x": {"type": "choice",
                                   "instructions": "i",
                                   "criteria": {}}}))
    r = run_cli("--check-questions", str(f))
    assert r.returncode != 0
    out = json.loads(r.stdout)
    assert out["ok"] is False
    assert out["errors"]


def test_check_questions_cli_valid(tmp_path):
    f = tmp_path / "q.json"
    f.write_text(json.dumps({"x": {"type": "choice",
                                   "instructions": "i",
                                   "criteria": {"a": "d"}}}))
    r = run_cli("--check-questions", str(f))
    assert r.returncode == 0
    assert json.loads(r.stdout)["ok"] is True


def test_predict_missing_dep_or_preset_json_error():
    """predict --preset without laya installed → JSON + nonzero,
    never a traceback on stderr."""
    r = run_cli("predict", "--state", '{"a":1}', "--preset", "triage")
    assert r.returncode != 0
    out = json.loads(r.stdout)          # stdout is pure JSON
    assert out["ok"] is False
    assert "Traceback" not in r.stderr


def test_predict_invalid_questions_json():
    r = run_cli("predict", "--state", '{"a":1}',
                "--questions", "{bad")
    assert r.returncode != 0
    out = json.loads(r.stdout)
    assert out["ok"] is False


def test_self_test_offline():
    r = run_cli("--self-test")
    assert r.returncode == 0
    assert json.loads(r.stdout)["ok"] is True
    assert "Traceback" not in r.stderr
