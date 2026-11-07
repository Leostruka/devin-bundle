"""roadmap-board.py contract tests: parsing, frontier, rendering."""
import importlib.util
import io
import json
import os
import sys
from contextlib import redirect_stdout

SCRIPTS = os.path.join(os.path.dirname(__file__), "..", "scripts")


def _load():
    spec = importlib.util.spec_from_file_location(
        "roadmap_board", os.path.join(SCRIPTS, "roadmap-board.py"))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


rb = _load()


def _mk(root, rel, text):
    p = os.path.join(root, rel)
    os.makedirs(os.path.dirname(p), exist_ok=True)
    with open(p, "w", encoding="utf-8") as f:
        f.write(text)


def _fixture(tmp_path):
    _mk(tmp_path, ".devin/issues/MILESTONE_2_01_alpha.md",
        "# M2_01 alpha task\n\nStatus: resolved · Blocked-by: none · Blocks: M2_02\n")
    _mk(tmp_path, ".devin/issues/MILESTONE_2_02_beta.md",
        "# M2_02 beta task\n\nStatus: ready-for-agent · Blocked-by: M2_01 · Blocks: none\n")
    _mk(tmp_path, ".devin/issues/MILESTONE_2_03_gamma.md",
        "# M2_03 gamma task\n\nStatus: open · Blocked-by: M2_99_missing · Blocks: none\n")
    _mk(tmp_path, ".devin/scratch/eff1/issues/R1-01-one.md",
        "# scratch one\n\nstatus: resolved\npriority: P2\n")
    _mk(tmp_path, ".devin/scratch/eff1/issues/R1-02-two.md",
        "# scratch two\n\nstatus: ready-for-agent\npriority: P3\n")


def test_parse_milestone_meta(tmp_path):
    _fixture(tmp_path)
    issues = rb.build_model(str(tmp_path))
    by_key = {i["key"]: i for i in issues}
    m1 = by_key["MILESTONE_2_01_alpha"]
    assert m1["done"] is True and m1["status"] == "resolved"
    m2 = by_key["MILESTONE_2_02_beta"]
    assert m2["ready"] is True  # blocker M2_01 resolved
    m3 = by_key["MILESTONE_2_03_gamma"]
    assert m3["ready"] is True  # unknown blocker ref doesn't block
    assert m3["blockers"][0]["known"] is False


def test_scratch_priority_and_done(tmp_path):
    _fixture(tmp_path)
    issues = rb.build_model(str(tmp_path))
    by_key = {i["key"]: i for i in issues}
    assert by_key["R1-01-one"]["done"] is True
    assert by_key["R1-01-one"]["priority"] == "P2"
    assert by_key["R1-02-two"]["ready"] is True
    assert by_key["R1-02-two"]["group"] == "eff1"


def test_blocked_until_resolved(tmp_path):
    _mk(tmp_path, ".devin/issues/MILESTONE_2_01_a.md",
        "# A\n\nStatus: open · Blocked-by: none · Blocks: MILESTONE_2_02_b\n")
    _mk(tmp_path, ".devin/issues/MILESTONE_2_02_b.md",
        "# B\n\nStatus: open · Blocked-by: MILESTONE_2_01_a · Blocks: none\n")
    issues = rb.build_model(str(tmp_path))
    by_key = {i["key"]: i for i in issues}
    assert by_key["MILESTONE_2_01_a"]["ready"] is True
    assert by_key["MILESTONE_2_02_b"]["ready"] is False


def test_render_and_json(tmp_path, capsys):
    _fixture(tmp_path)
    out = io.StringIO()
    with redirect_stdout(out):
        assert rb.main(["--root", str(tmp_path)]) == 0
    md = out.getvalue()
    assert "Roadmap board" in md and "Frontier" in md
    assert "eff1" in md and "issues" in md

    out = io.StringIO()
    with redirect_stdout(out):
        rb.main(["--root", str(tmp_path), "--json"])
    data = json.loads(out.getvalue())
    assert data["summary"]["total"] == 5
    assert data["summary"]["done"] == 2


def test_empty_root(tmp_path):
    issues = rb.build_model(str(tmp_path))
    assert issues == []
    assert rb.summarize(issues)["total"] == 0
