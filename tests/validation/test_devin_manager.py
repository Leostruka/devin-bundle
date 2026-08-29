"""Validation tests for devin-manager.

Agent-chosen infrastructure tests (tests/validation/), distinct from
held-out behavioral tests.
"""
import json
import shutil
import subprocess
import tempfile
from pathlib import Path

import pytest

ROOT = Path(__file__).parents[2]
FIXTURE = ROOT / "tests" / "fixtures" / "devin-manager" / "project"
SCRIPT = ROOT / "skills" / "devin-manager" / "scripts" / "devin-manager.py"


def run(args, cwd=ROOT):
    return subprocess.run(
        ["python", str(SCRIPT)] + args,
        capture_output=True,
        text=True,
        encoding="utf-8",
        cwd=cwd,
        timeout=30,
    )


def test_scan_is_deterministic():
    """Repeated scan of the fixture yields byte-identical stdout."""
    a = run(["scan", str(FIXTURE)])
    b = run(["scan", str(FIXTURE)])
    assert a.returncode == 0, a.stderr
    assert b.returncode == 0, b.stderr
    assert a.stdout == b.stdout
    assert a.stdout


def test_default_mode_does_not_write_outside_devin():
    """Default scan/doctor/plan does not create or modify files outside .devin/."""
    project = FIXTURE
    outside = []
    for f in project.rglob("*"):
        if f.is_file() and f.relative_to(project).parts[0] != ".devin":
            outside.append((f, f.read_bytes()))
    for cmd in ("scan", "doctor", "plan"):
        result = run([cmd, str(project)])
        assert result.returncode == 0, result.stderr
    for f, original in outside:
        assert f.read_bytes() == original, f"{f} was modified outside .devin"


def test_broken_reference_has_source_path():
    """Doctor reports a broken reference with its source path."""
    result = run(["doctor", str(FIXTURE)])
    assert result.returncode == 0, result.stderr
    data = json.loads(result.stdout)
    broken = data.get("broken_references", [])
    assert any(
        r.get("target") in ("rules/missing.md", ".devin/rules/missing.md")
        and r.get("source") in ("global_rules.md", "memory/notes/2026/08/example.md")
        for r in broken
    ), result.stdout


def test_references_deduplicated_by_source_target():
    """A source+target reference is stored once with the strongest kind."""
    result = run(["doctor", str(FIXTURE)])
    assert result.returncode == 0, result.stderr
    data = json.loads(result.stdout)
    broken = data.get("broken_references", [])
    config_refs = [r for r in broken if r["source"] == "config.json"]
    assert len([r for r in config_refs if r["target"] == "scripts/missing.py"]) == 1
    assert config_refs[0]["kind"] == "command"
    rules_refs = [r for r in broken if r["source"] == "global_rules.md" and r["target"] == "rules/missing.md"]
    assert len(rules_refs) == 1
    assert rules_refs[0]["kind"] == "markdown_link"


def test_doctor_rejects_outside_devin():
    """References resolving outside .devin/ are reported as broken."""
    result = run(["doctor", str(FIXTURE)])
    assert result.returncode == 0, result.stderr
    data = json.loads(result.stdout)
    broken = data.get("broken_references", [])
    outside = [r for r in broken if r["target"] == "src/main.py"]
    assert len(outside) == 2, result.stdout
    sources = {r["source"] for r in outside}
    assert sources == {"rules/core.md", "memory/notes/2026/08/example.md"}, sources


def test_doctor_skips_symlinks():
    """Symlinks inside .devin/ are not inventoried or resolved."""
    with tempfile.TemporaryDirectory() as tmp:
        dst = Path(tmp) / "project"
        shutil.copytree(FIXTURE, dst)
        try:
            (dst / ".devin" / "skills" / "symlink.md").symlink_to(dst / "src" / "main.py")
        except OSError:
            pytest.skip("symlinks not supported on this platform")
        result = run(["scan", str(dst)])
        assert result.returncode == 0, result.stderr
        data = json.loads(result.stdout)
        assert not any("symlink" in a["path"] for a in data["artifacts"])
        # Create a reference to the symlink target
        note = dst / ".devin" / "memory" / "symlink-test.md"
        note.write_text("See `skills/symlink.md` for context.")
        result = run(["doctor", str(dst)])
        assert result.returncode == 0, result.stderr
        data = json.loads(result.stdout)
        assert any(r["target"] == "skills/symlink.md" for r in data["broken_references"])


def test_doctor_reports_malformed_json():
    """Malformed core JSON is reported as a provenance-bearing divergence, not a crash."""
    with tempfile.TemporaryDirectory() as tmp:
        dst = Path(tmp) / "project"
        shutil.copytree(FIXTURE, dst)
        (dst / ".devin" / "config.json").write_text("{not valid json", encoding="utf-8", newline="\n")
        result = run(["doctor", str(dst)])
        assert result.returncode == 0, result.stderr
        data = json.loads(result.stdout)
        malformed = [d for d in data.get("divergences", []) if d["kind"] == "malformed_json"]
        assert malformed, result.stdout
        assert any(d["source"] == ".devin/config.json" for d in malformed)


def test_explain_default_project():
    """explain with a single argument treats it as the artifact under cwd."""
    result = run(["explain", "global_rules.md"], cwd=FIXTURE)
    assert result.returncode == 0, result.stderr
    data = json.loads(result.stdout)
    assert data["command"] == "explain"
    assert data["artifact"]["path"] == "global_rules.md"


def test_explain_with_project():
    """explain accepts [PROJECT] ARTIFACT shape."""
    result = run(["explain", str(FIXTURE), "global_rules.md"])
    assert result.returncode == 0, result.stderr
    data = json.loads(result.stdout)
    assert data["artifact"]["path"] == "global_rules.md"


def test_no_absolute_paths_in_outputs():
    """scan and plan outputs/notes contain no absolute paths."""
    result = run(["scan", str(FIXTURE)])
    assert result.returncode == 0, result.stderr
    assert "D:/" not in result.stdout
    assert "D:\\" not in result.stdout
    data = json.loads(result.stdout)
    assert not data["project"].startswith("/")
    assert not data["project"].startswith("C:")
    assert not data["project"].startswith("D:")

    with tempfile.TemporaryDirectory() as tmp:
        dst = Path(tmp) / "project"
        shutil.copytree(FIXTURE, dst)
        result = run(["plan", str(dst), "--write", "--approve"])
        assert result.returncode == 0, result.stderr
        data = json.loads(result.stdout)
        assert data["written"].startswith(".devin/")
        assert "D:/" not in data["written"]
        note = dst / ".devin" / "notes" / "devin-manager" / "plan.md"
        note_text = note.read_text(encoding="utf-8")
        assert "D:/" not in note_text
        assert "D:\\" not in note_text


def test_scan_includes_agents_and_mcp():
    """scan inventories agent profiles and MCP servers from the project root."""
    result = run(["scan", str(FIXTURE)])
    assert result.returncode == 0, result.stderr
    data = json.loads(result.stdout)
    by_prov = {a["provenance"]: a for a in data["artifacts"]}
    assert "agents/architect.md" in by_prov
    assert by_prov["agents/architect.md"]["category"] == "agents"
    assert "mcp_config.json" in by_prov
    assert by_prov["mcp_config.json"]["category"] == "mcp"
    assert by_prov["mcp_config.json"].get("mcp_servers") == ["fetch"]


def test_doctor_detects_duplicates():
    result = run(["doctor", str(FIXTURE)])
    assert result.returncode == 0, result.stderr
    data = json.loads(result.stdout)
    assert data.get("duplicates"), result.stdout
    names = [d.get("name") for d in data["duplicates"] if d.get("kind") == "skill_name"]
    assert "duplicate-skill" in names


def test_doctor_detects_divergences():
    result = run(["doctor", str(FIXTURE)])
    assert result.returncode == 0, result.stderr
    data = json.loads(result.stdout)
    kinds = [d.get("kind") for d in data.get("divergences", [])]
    assert "hooks_config_mismatch" in kinds
    assert "manifest_skill_count" in kinds


def test_plan_does_not_update_moc_or_memory():
    """plan --write only writes the plan note; it does not touch memory or MOC."""
    with tempfile.TemporaryDirectory() as tmp:
        dst = Path(tmp) / "project"
        shutil.copytree(FIXTURE, dst)
        moc = dst / ".devin" / "memory" / "MOC.md"
        moc_before = moc.read_bytes()
        memory_files = list((dst / ".devin" / "memory").rglob("*"))
        result = run(["plan", str(dst), "--write", "--approve"])
        assert result.returncode == 0, result.stderr
        note = dst / ".devin" / "notes" / "devin-manager" / "plan.md"
        assert note.is_file()
        assert moc.read_bytes() == moc_before
        memory_files_after = list((dst / ".devin" / "memory").rglob("*"))
        assert set(memory_files_after) == set(memory_files), "plan modified .devin/memory/"


def test_plan_requires_approval():
    """plan --write without --approve is rejected."""
    with tempfile.TemporaryDirectory() as tmp:
        dst = Path(tmp) / "project"
        shutil.copytree(FIXTURE, dst)
        result = run(["plan", str(dst), "--write"])
        assert result.returncode != 0
        assert not (dst / ".devin" / "notes" / "devin-manager" / "plan.md").exists()


def test_plan_writes_note_under_devin_with_approval():
    """plan --write --approve persists the plan note under .devin/ only."""
    with tempfile.TemporaryDirectory() as tmp:
        dst = Path(tmp) / "project"
        shutil.copytree(FIXTURE, dst)
        before = {f.relative_to(dst) for f in dst.rglob("*") if f.is_file() and f.relative_to(dst).parts[0] != ".devin"}
        result = run(["plan", str(dst), "--write", "--approve"])
        assert result.returncode == 0, result.stderr
        written = json.loads(result.stdout)["written"]
        assert ".devin/" in written
        note = dst / ".devin" / "notes" / "devin-manager" / "plan.md"
        assert note.is_file()
        after = {f.relative_to(dst) for f in dst.rglob("*") if f.is_file() and f.relative_to(dst).parts[0] != ".devin"}
        assert after == before, f"plan created files outside .devin: {after - before}"
