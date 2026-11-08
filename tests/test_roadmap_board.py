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


def test_capacity_view(tmp_path):
    _fixture(tmp_path)
    _mk(tmp_path, ".devin/scratch/eff1/issues/R1-03-wip.md",
        "# scratch wip\n\nstatus: in-progress\n")
    _mk(tmp_path, ".devin/scratch/eff1/issues/R1-04-blk.md",
        "# scratch blocked\n\nstatus: blocked\n")
    issues = rb.build_model(str(tmp_path))
    cap = rb.capacity(issues)
    eff1 = cap["by_group"]["eff1"]
    # eff1: R1-01 done, R1-02 ready, R1-03 in-progress, R1-04 blocked
    assert eff1["total"] == 4 and eff1["done"] == 1
    assert eff1["open"] == 3
    assert eff1["ready"] == 1      # R1-02 only - in-flight is claimed
    assert eff1["blocked"] == 2    # R1-03 in-flight + R1-04 blocked:
                                  # open and not claimable (#405/#417)
    assert eff1["in_flight"] == 1
    assert cap["totals"]["in_flight"] == 1
    assert cap["frontier"] == cap["totals"]["ready"]
    assert cap["wip"]["over"] is None
    cap2 = rb.capacity(issues, wip_limit=0)
    assert cap2["wip"]["limit"] == 0 and cap2["wip"]["over"] is True


def test_capacity_blocked_by_undone(tmp_path):
    _mk(tmp_path, ".devin/issues/A.md",
        "# A\n\nStatus: open · Blocked-by: none · Blocks: B.md\n")
    _mk(tmp_path, ".devin/issues/B.md",
        "# B\n\nStatus: open · Blocked-by: A · Blocks: none\n")
    issues = rb.build_model(str(tmp_path))
    cap = rb.capacity(issues)
    # B's blocker "A" matches key "A" via alias? key is "A" (stem) -
    # blocked_by ref "A" lower -> "a"; alias set has "a". resolves.
    b = {i["key"]: i for i in issues}["B"]
    assert b["ready"] is False
    assert cap["totals"]["blocked"] == 1
    assert cap["totals"]["ready"] == 1


def test_blocked_by_markdown_residue(tmp_path):
    """Issue #402: '**Blocked by:** `X`**' captures must not leak
    markdown chars into refs."""
    _mk(tmp_path, ".devin/issues/A.md",
        "# A\n\nStatus: resolved\n")
    _mk(tmp_path, ".devin/issues/B.md",
        "# B\n\nStatus: open\n\n**Blocked by:** `A` and **C**\n")
    _mk(tmp_path, ".devin/issues/C.md",
        "# C\n\nStatus: resolved\n")
    issues = rb.build_model(str(tmp_path))
    b = {i["key"]: i for i in issues}["B"]
    assert [r["ref"] for r in b["blockers"]] == ["A", "C"]
    assert all(r["known"] and r["done"] for r in b["blockers"])
    assert b["ready"] is True


def test_blocked_by_prose_none(tmp_path):
    """Issue #402: 'None - can start immediately' is not a blocker."""
    _mk(tmp_path, ".devin/issues/A.md",
        "# A\n\nStatus: open\nBlocked-by: None - can start immediately\n")
    issues = rb.build_model(str(tmp_path))
    assert issues[0]["blockers"] == []
    assert issues[0]["ready"] is True


def test_group_prefix_blocker_ref(tmp_path):
    """Issue #403: scratch DAGs reference siblings as '01', '02' -
    resolved within the same effort group only."""
    _mk(tmp_path, ".devin/scratch/effX/issues/01-alpha.md",
        "# alpha\n\nstatus: resolved\n")
    _mk(tmp_path, ".devin/scratch/effX/issues/02-beta.md",
        "# beta\n\nstatus: open\nblocked_by: 01\n")
    _mk(tmp_path, ".devin/scratch/effY/issues/01-other.md",
        "# other effort, same prefix\n\nstatus: open\n")
    issues = rb.build_model(str(tmp_path))
    by_key = {i["key"]: i for i in issues}
    b = by_key["02-beta"]
    assert b["blockers"][0]["known"] is True
    assert b["blockers"][0]["via"] == "group-prefix"
    assert b["blockers"][0]["done"] is True
    assert b["ready"] is True
    # effY's 01-other must NOT satisfy effX's refs (group-scoped)
    other = by_key["01-other"]
    assert other["ready"] is True


def test_group_prefix_blocks_when_undone(tmp_path):
    _mk(tmp_path, ".devin/scratch/effX/issues/01-alpha.md",
        "# alpha\n\nstatus: open\n")
    _mk(tmp_path, ".devin/scratch/effX/issues/02-beta.md",
        "# beta\n\nstatus: open\nblocked_by: 01\n")
    issues = rb.build_model(str(tmp_path))
    b = {i["key"]: i for i in issues}["02-beta"]
    assert b["blockers"][0]["known"] is True
    assert b["blockers"][0]["done"] is False
    assert b["ready"] is False


def test_non_actionable_statuses_not_ready(tmp_path):
    """Issue #405: implemented/landed/wontfix/archived/superseded-*
    are terminal; blocked/needs-*/in-flight are not claimable."""
    terminal = ["implemented", "landed", "wontfix", "archived",
                "superseded-by-x"]
    deferred = ["blocked", "needs-triage", "needs-info", "on-hold",
                "in-progress", "claimed"]
    for n, st in enumerate(terminal):
        _mk(tmp_path, f".devin/issues/T{n}.md",
            f"# t{n}\n\nStatus: {st}\n")
    for n, st in enumerate(deferred):
        _mk(tmp_path, f".devin/issues/D{n}.md",
            f"# d{n}\n\nStatus: {st}\n")
    issues = rb.build_model(str(tmp_path))
    for i in issues:
        assert i["ready"] is False, i["key"]
    by_key = {i["key"]: i for i in issues}
    for n in range(len(terminal)):
        assert by_key[f"T{n}"]["done"] is True
    for n in range(len(deferred)):
        assert by_key[f"D{n}"]["done"] is False


def test_status_vocab_parity_with_site(tmp_path):
    """Issue #407: roadmap-board and site/build.py share
    status_vocab - same status must classify identically."""
    spec = importlib.util.spec_from_file_location(
        "site_build", os.path.join(
            os.path.dirname(__file__), "..", "site", "build.py"))
    site = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(site)

    idir = tmp_path / "issues"
    idir.mkdir()
    statuses = ["resolved", "implemented", "landed", "closed",
                "shipped", "wontfix", "archived", "superseded-by-9",
                "blocked", "needs-triage", "in-progress", "open"]
    for n, st in enumerate(statuses):
        (idir / f"I{n}.md").write_text(
            f"# i{n}\n\nStatus: {st}\n", encoding="utf-8")
    # generic '## Done when' section must NOT mark resolved
    (idir / "J.md").write_text(
        "# j\n\nStatus: open\n\n## Done when\n\ncriteria\n",
        encoding="utf-8")

    rb_issues = []
    for p in sorted(idir.glob("*.md")):
        rb_issues.append(rb.parse_issue(str(p), "g"))
    rb_closed = {i["status"]: i["done"] for i in rb_issues}
    site_items = {i["file"]: i for i in site._issue_items(str(idir))}
    mismatches = []
    for n, st in enumerate(statuses):
        fn = f"I{n}.md"
        site_closed = site_items[fn]["status"] == "resolved"
        if site_closed != rb_closed[st]:
            mismatches.append((st, site_closed, rb_closed[st]))
    assert not mismatches, mismatches
    # '## Done when' is a checklist heading, not a resolution marker
    j = site_items["J.md"]
    assert j["status"] != "resolved"


def test_archived_effort_excluded(tmp_path, capsys):
    """Issue #406: scratch/<effort>/README.md 'Status: ARCHIVED'
    removes that effort's issues from the live board."""
    _mk(tmp_path, ".devin/scratch/dead-effort/README.md",
        "# dead-effort\n\nStatus: ARCHIVED\n\nDone.\n")
    _mk(tmp_path, ".devin/scratch/dead-effort/issues/D1.md",
        "# dead one\n\nstatus: open\n")
    _mk(tmp_path, ".devin/scratch/live-effort/issues/L1.md",
        "# live one\n\nstatus: open\n")
    issues = rb.build_model(str(tmp_path))
    assert [i["key"] for i in issues] == ["L1"]
    assert rb.archived_efforts(str(tmp_path)) == ["dead-effort"]

    out = io.StringIO()
    with redirect_stdout(out):
        rb.main(["--root", str(tmp_path), "--json"])
    data = json.loads(out.getvalue())
    assert data["summary"]["archived_efforts"] == ["dead-effort"]
    assert data["summary"]["archived_issues"] == 1
    assert data["summary"]["total"] == 1

    out = io.StringIO()
    with redirect_stdout(out):
        rb.main(["--root", str(tmp_path)])
    assert "Archived efforts excluded: 1 issues" in out.getvalue()


def test_bold_status_field_variants(tmp_path):
    """'- **Status**: x' and '**Status:** x' parse like 'Status: x'."""
    _mk(tmp_path, ".devin/issues/A.md",
        "# A\n\n- **Status**: resolved\n")
    _mk(tmp_path, ".devin/issues/B.md",
        "# B\n\n**Status:** resolved\n")
    _mk(tmp_path, ".devin/issues/C.md",
        "# C\n\n- **Status**: open\n")
    issues = rb.build_model(str(tmp_path))
    by_key = {i["key"]: i for i in issues}
    assert by_key["A"]["done"] is True
    assert by_key["B"]["done"] is True
    assert by_key["C"]["done"] is False
    assert by_key["C"]["status"] == "open"


def test_estimate_actual_fields(tmp_path):
    """Issue #418: estimate_min/actual_min frontmatter -> JSON fields
    and capacity est_open_min rollup."""
    _mk(tmp_path, ".devin/issues/A.md",
        "# A\n\nStatus: open\nestimate_min: 90\nactual_min: 45\n")
    _mk(tmp_path, ".devin/issues/B.md",
        "# B\n\nStatus: resolved\nestimate_min: 30\n")
    _mk(tmp_path, ".devin/issues/C.md",
        "# C\n\nStatus: open\n**Estimate-min**: 60\n")
    issues = rb.build_model(str(tmp_path))
    by_key = {i["key"]: i for i in issues}
    assert by_key["A"]["estimate_min"] == 90
    assert by_key["A"]["actual_min"] == 45
    assert by_key["B"]["estimate_min"] == 30
    assert by_key["C"]["estimate_min"] == 60  # bold + dash variant
    cap = rb.capacity(issues)
    # only OPEN issues' estimates roll up: A(90) + C(60) = 150
    assert cap["by_group"]["issues"]["est_open_min"] == 150
    assert cap["totals"]["est_open_min"] == 150


def test_goals_rollup(tmp_path):
    """Issue #420: .devin/goals/*.md -> coverage over linked issues."""
    _fixture(tmp_path)
    gdir = tmp_path / ".devin" / "goals"
    gdir.mkdir(parents=True)
    (gdir / "g1.md").write_text(
        "# Goal: Test goal\n\nStatus: active\n"
        "Horizon: 2026-11-09..2026-11-15\n"
        "Objective: verify rollup\n"
        "Efforts: eff1\nIssues: missing-key\nRefs: #346 #999\n",
        encoding="utf-8")
    (gdir / "README.md").write_text("# not a goal\n", encoding="utf-8")
    issues = rb.build_model(str(tmp_path))
    goals = rb.load_goals(str(tmp_path), issues)
    assert len(goals) == 1
    g = goals[0]
    assert g["name"] == "g1" and g["status"] == "active"
    assert g["horizon"] == "2026-11-09..2026-11-15"
    assert g["linked"] == 2 and g["done"] == 1  # eff1: 1 done + 1 open
    assert g["coverage"] == 0.5
    assert g["unresolved"] == ["missing-key"]
    assert g["refs"] == ["#346", "#999"]
    # group/key form resolves too
    (gdir / "g2.md").write_text(
        "# Goal: keyed\nIssues: eff1/R1-01-one\n", encoding="utf-8")
    goals = rb.load_goals(str(tmp_path), issues)
    g2 = [x for x in goals if x["name"] == "g2"][0]
    assert g2["linked"] == 1
    # markdown section renders
    out = io.StringIO()
    with redirect_stdout(out):
        rb.main(["--root", str(tmp_path)])
    assert "## Goals" in out.getvalue() and "Test goal" in out.getvalue()


def test_goals_empty_dir(tmp_path):
    _fixture(tmp_path)
    issues = rb.build_model(str(tmp_path))
    assert rb.load_goals(str(tmp_path), issues) == []


def test_capacity_in_json_and_md(tmp_path, capsys):
    _fixture(tmp_path)
    out = io.StringIO()
    with redirect_stdout(out):
        rb.main(["--root", str(tmp_path), "--json", "--wip-limit", "2"])
    data = json.loads(out.getvalue())
    assert "capacity" in data
    assert data["capacity"]["wip"]["limit"] == 2
    assert "by_group" in data["capacity"]

    out = io.StringIO()
    with redirect_stdout(out):
        rb.main(["--root", str(tmp_path)])
    assert "## Capacity" in out.getvalue()


def test_archived_word_in_prose_not_status(tmp_path):
    """Review regression: 'ARCHIVED' inside README prose must not archive
    the effort - only a real Status field counts."""
    _mk(tmp_path, ".devin/scratch/someday/README.md",
        "# someday\n\nNotes: older audits were ARCHIVED in batch-6.\n")
    _mk(tmp_path, ".devin/scratch/someday/issues/S1.md",
        "# s one\n\nstatus: open\n")
    issues = rb.build_model(str(tmp_path))
    assert [i["key"] for i in issues] == ["S1"]
    assert rb.archived_efforts(str(tmp_path)) == []


def test_split_ids_strips_prose_tail(tmp_path):
    """Review regression: 'M2-01 - pending' must resolve M2-01, not the raw
    token with the prose tail."""
    _mk(tmp_path, ".devin/scratch/e/issues/M2-01.md",
        "# blocker\n\nstatus: open\n")
    _mk(tmp_path, ".devin/scratch/e/issues/X9.md",
        "# x\n\nstatus: open\nblocked_by: M2-01 - pending review\n")
    issues = {i["key"]: i for i in rb.build_model(str(tmp_path))}
    assert "M2-01" in issues["X9"]["blocked_by"]
