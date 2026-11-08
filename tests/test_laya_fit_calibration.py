"""fit_calibration - map fitting over frozen manifests.

Pure-function tests with synthetic manifests; the tool never calls an
engine and never writes profiles.
"""
import json
import math
import sys
from pathlib import Path

import pytest

LAYA_DIR = Path(__file__).resolve().parents[1] / \
    "extensions" / "laya-tools"
sys.path.insert(0, str(LAYA_DIR))

import fit_calibration as fc  # noqa: E402


def _manifest(path, cases):
    path.write_text(json.dumps({"version": 1, "frozen": True,
                                "cases": cases}), encoding="utf-8")
    return str(path)


def _case(cid, gold, choice, conf, outcome=None):
    if outcome is None:
        outcome = "abstain" if choice == "__none__" else "suggestion"
    return {"case_id": cid, "gold": gold,
            "reply": {"outcome": outcome, "candidate_id": choice,
                      "raw_confidence": conf,
                      "raw_top_probability": conf}}


def test_decided_cases_filters_and_labels(tmp_path):
    m = _manifest(tmp_path / "m.json", [
        _case("c1", "a", "a", 0.9),
        _case("c2", "a", "b", 0.8),          # decided, wrong
        _case("c3", "__none__", "__none__", None, "abstain"),
        _case("c4", "a", "a", None),          # no confidence -> skip
    ])
    cases, total = fc._decided_cases(m)
    assert total == 4
    assert [(x, y) for x, y, _ in cases] == [(0.9, 1), (0.8, 0)]


def test_fit_platt_separates_perfectly(tmp_path):
    # low-confidence picks are wrong, high-confidence picks correct
    cases = []
    for i in range(20):
        conf = 0.4 + i * 0.03
        good = conf >= 0.7
        cases.append(_case(f"c{i}", "a", "a" if good else "b", conf))
    m = _manifest(tmp_path / "m.json", cases)
    xs_ys, _ = fc._decided_cases(m)
    a, b = fc.fit_platt([x for x, _, _ in xs_ys],
                        [y for _, y, _ in xs_ys])
    fn = fc._platt_fn(a, b)
    assert fn(0.95) > 0.9
    assert fn(0.5) < 0.5


def test_pava_table_is_monotone(tmp_path):
    # interleaved correctness: wrong picks at low AND high confidence
    cases = []
    for i in range(12):
        conf = 0.5 + i * 0.04
        wrong = i % 3 == 0
        cases.append(_case(f"c{i}", "a", "b" if wrong else "a", conf))
    m = _manifest(tmp_path / "m.json", cases)
    xs_ys, _ = fc._decided_cases(m)
    pts = fc._pava_table([x for x, _, _ in xs_ys],
                         [y for _, y, _ in xs_ys])
    ys = [p[1] for p in pts]
    assert ys == sorted(ys)
    assert all(0.0 <= y <= 1.0 for y in ys)


def test_adoption_curve_math():
    cases = [(0.9, 1, "a"), (0.8, 0, "b"), (0.7, 1, "c")]
    rows = fc.adoption_curve(lambda x: x, cases, total=5,
                             thresholds=[0.85, 0.75])
    assert rows[0] == {"threshold": 0.85, "adopted": 1,
                       "adopted_correct": 1, "adopted_accuracy": 1.0,
                       "coverage": 0.2}
    assert rows[1]["adopted"] == 2
    assert rows[1]["adopted_accuracy"] == 0.5


def test_main_too_few_train_cases(tmp_path, capsys):
    m = _manifest(tmp_path / "m.json", [_case("c1", "a", "a", 0.9)])
    rc = fc.main(["--manifest", m])
    assert rc == 1
    out = json.loads(capsys.readouterr().out)
    assert out["ok"] is False
    assert out["reason"] == "too_few_decided_train_cases"


def test_main_emit_block_shape(tmp_path, capsys):
    cases = []
    for i in range(12):
        conf = 0.5 + i * 0.04
        wrong = i % 4 == 0
        cases.append(_case(f"c{i}", "a", "b" if wrong else "a", conf))
    m = _manifest(tmp_path / "m.json", cases)
    rc = fc.main(["--manifest", m, "--map", "platt",
                  "--emit-block", "media-intent-v1",
                  "--cardinality", "5", "--threshold", "0.9"])
    assert rc == 0
    rep = json.loads(capsys.readouterr().out)
    block = rep["emit_block"]
    assert block["profile"] == "media-intent-v1"
    assert block["threshold"] == 0.9
    assert block["cardinality"] == 5
    assert block["map"]["kind"] == "platt"
    assert "a" in block["map"] and "b" in block["map"]


def test_main_heldout_report(tmp_path, capsys):
    train = [_case(f"t{i}", "a" if i % 2 else "b",
                   "a" if i % 2 else "b", 0.55 + i * 0.02)
             for i in range(12)]
    held = [_case("h1", "a", "a", 0.95),
            _case("h2", "b", "a", 0.6),   # wrong pick
            _case("h3", "__none__", "__none__", None, "abstain")]
    tm = _manifest(tmp_path / "train.json", train)
    hm = _manifest(tmp_path / "held.json", held)
    rc = fc.main(["--manifest", tm, "--heldout", hm, "--map", "table"])
    assert rc == 0
    rep = json.loads(capsys.readouterr().out)
    h = rep["maps"]["table"]["heldout"][0]
    assert h["decided"] == 2 and h["cases"] == 3
