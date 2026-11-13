"""ship-metrics — row mapping, idempotent merge, report (#486)."""
import importlib.util
import json
import os
import sys

spec = importlib.util.spec_from_file_location(
    "ship_metrics",
    os.path.join(os.path.dirname(__file__), "..", "scripts",
                 "ship-metrics.py"))
mod = importlib.util.module_from_spec(spec)
sys.modules["ship_metrics"] = mod
spec.loader.exec_module(mod)

PR = {"number": 999, "title": "x",
      "createdAt": "2026-11-10T10:00:00Z",
      "mergedAt": "2026-11-10T10:30:00Z",
      "additions": 10, "deletions": 2, "changedFiles": 3,
      "author": {"login": "u"}}


def test_row_computes_lead_minutes():
    r = mod._row(PR)
    assert r["pr"] == 999 and r["lead_min"] == 30.0
    assert r["files"] == 3


def test_merge_rows_idempotent(tmp_path):
    log = str(tmp_path / "ships.jsonl")
    assert mod._merge_rows(log, [PR]) == 1
    assert mod._merge_rows(log, [PR]) == 0  # same PR skipped
    rows = mod._load(log)
    assert len(rows) == 1 and rows[0]["pr"] == 999


def test_report_stats(tmp_path, capsys):
    log = str(tmp_path / "s.jsonl")
    mod._merge_rows(log, [PR])
    mod.report(log)
    d = json.loads(capsys.readouterr().out)
    assert d["ok"] and d["n"] == 1 and d["lead_min"]["median"] == 30.0
