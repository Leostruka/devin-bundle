"""Validation tests for structured-knowledge-extraction.

Agent-chosen infrastructure tests, distinct from held-out behavioral tests.
"""
import json
import os
import shutil
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).parents[2]
SCRIPT = ROOT / "skills" / "structured-knowledge-extraction" / "scripts" / "extract.py"
FIXTURE = ROOT / "tests" / "fixtures" / "structured-knowledge-extraction"


def run(args, cwd=ROOT):
    return subprocess.run(
        ["python", str(SCRIPT)] + args,
        capture_output=True,
        text=True,
        encoding="utf-8",
        cwd=cwd,
        timeout=30,
    )


def _setup_project(tmp_path, source_name="source.md"):
    """Copy a fixture source into a temp project with .devin."""
    project = tmp_path / "project"
    project.mkdir()
    (project / ".devin").mkdir()
    src = project / "notes.md"
    shutil.copy(FIXTURE / source_name, src)
    return project, src


def test_extract_outputs_valid_json(tmp_path):
    project, src = _setup_project(tmp_path)
    result = run(["extract", str(src), str(project)])
    assert result.returncode == 0, result.stderr
    data = json.loads(result.stdout)
    assert data["schema_version"] == "1.0.0"
    assert data["sources"]["notes.md"]["sha256"]
    assert data["sources"]["notes.md"]["extracted_at"]
    assert data["entities"]
    assert data["relations"]
    by_id = {e["id"]: e for e in data["entities"].values()}
    assert any(e["name"] == "Project Alpha" and e["type"] == "heading" for e in by_id.values())
    assert any(e["name"] == "pip install -r requirements.txt" and e["type"] == "code" for e in by_id.values())
    assert any(e["name"] == "https://example.com/alpha" and e["type"] == "url" for e in by_id.values())
    assert any(e["name"] == "arXiv:2307.03172" and e["type"] == "citation" for e in by_id.values())
    for e in data["entities"].values():
        assert e["provenance"]
        for prov in e["provenance"]:
            assert prov["source"] == "notes.md"
            assert isinstance(prov["line"], int)
            assert "quote" in prov
    for rel in data["relations"]:
        assert rel["provenance"]


def test_extract_is_deterministic(tmp_path):
    project, src = _setup_project(tmp_path)
    a = run(["extract", str(src), str(project)])
    b = run(["extract", str(src), str(project)])
    assert a.returncode == 0, a.stderr
    assert b.returncode == 0, b.stderr
    assert json.loads(a.stdout) == json.loads(b.stdout)


def test_extract_requires_approval(tmp_path):
    project, src = _setup_project(tmp_path)
    result = run(["extract", str(src), str(project), "--write"])
    assert result.returncode != 0
    assert not (project / ".devin" / "notes" / "structured-knowledge-extraction" / "knowledge.json").exists()


def test_extract_writes_under_devin(tmp_path):
    project, src = _setup_project(tmp_path)
    before = {f: f.read_bytes() for f in project.rglob("*") if f.is_file() and f.relative_to(project).parts[0] != ".devin"}
    result = run(["extract", str(src), str(project), "--write", "--approve"])
    assert result.returncode == 0, result.stderr
    note_dir = project / ".devin" / "notes" / "structured-knowledge-extraction"
    assert (note_dir / "knowledge.json").is_file()
    assert (note_dir / "knowledge.md").is_file()
    for f, content in before.items():
        assert f.read_bytes() == content, f"{f} was modified outside .devin"
    data = json.loads((note_dir / "knowledge.json").read_text(encoding="utf-8"))
    assert data["schema_version"] == "1.0.0"


def test_extract_rejects_symlinks(tmp_path):
    project, src = _setup_project(tmp_path)
    link = project / "link.md"
    try:
        link.symlink_to(src)
    except OSError:
        pytest.skip("symlinks not supported on this platform")
    result = run(["extract", str(link), str(project)])
    assert result.returncode != 0
    assert "symlink" in result.stderr.lower()


def test_no_absolute_paths_in_outputs(tmp_path):
    project, src = _setup_project(tmp_path)
    result = run(["extract", str(src), str(project), "--write", "--approve"])
    assert result.returncode == 0, result.stderr
    assert "D:/" not in result.stdout
    assert "D:\\" not in result.stdout
    assert "C:" not in result.stdout
    md = (project / ".devin" / "notes" / "structured-knowledge-extraction" / "knowledge.md").read_text(encoding="utf-8")
    assert "D:/" not in md
    assert "D:\\" not in md
    assert "C:" not in md


def test_merge_no_duplicates(tmp_path):
    project, src = _setup_project(tmp_path)
    result = run(["extract", str(src), str(project), "--write", "--approve"])
    assert result.returncode == 0, result.stderr

    more = project / "more.md"
    shutil.copy(FIXTURE / "more.md", more)
    result = run(["merge", str(more), str(project), "--write", "--approve"])
    assert result.returncode == 0, result.stderr
    data = json.loads((project / ".devin" / "notes" / "structured-knowledge-extraction" / "knowledge.json").read_text(encoding="utf-8"))
    names = {e["name"] for e in data["entities"].values()}
    assert "Project Alpha" in names
    assert "Deployment" in names
    assert "https://example.com/deploy" in names
    assert "notes.md" in data["sources"]
    assert "more.md" in data["sources"]
    assert data["sources"]["notes.md"]["sha256"]
    assert data["sources"]["more.md"]["sha256"]
    assert data["sources"]["notes.md"]["extracted_at"]
    assert data["sources"]["more.md"]["extracted_at"]
    assert not data["conflicts"]

    # Re-merging the same source must not duplicate provenance.
    result = run(["merge", str(src), str(project), "--write", "--approve"])
    assert result.returncode == 0, result.stderr
    data2 = json.loads((project / ".devin" / "notes" / "structured-knowledge-extraction" / "knowledge.json").read_text(encoding="utf-8"))
    assert data2["entities"] == data["entities"]
    assert data2["sources"] == data["sources"]
    for e in data2["entities"].values():
        assert len(e["provenance"]) <= 1 or e["provenance"][0]["source"] != e["provenance"][1]["source"]


def test_merge_reports_conflicts(tmp_path):
    project, src = _setup_project(tmp_path)
    result = run(["extract", str(src), str(project), "--write", "--approve"])
    assert result.returncode == 0, result.stderr

    conflict = project / "conflict.md"
    shutil.copy(FIXTURE / "conflict.md", conflict)
    result = run(["merge", str(conflict), str(project), "--write", "--approve"])
    assert result.returncode == 0, result.stderr
    data = json.loads(result.stdout)
    assert data["conflicts"]
    assert any(
        c["kind"] == "entity_type_mismatch" and c["existing_name"] == "Project Alpha" and c["new_type"] == "code"
        for c in data["conflicts"]
    )
    # The existing heading entity should not have been silently overwritten.
    project_alpha = next(
        e for e in data["entities"].values() if e["name"] == "Project Alpha"
    )
    assert project_alpha["type"] == "heading"


def test_search_baseline_no_api_key(tmp_path):
    project, src = _setup_project(tmp_path)
    more = project / "more.md"
    shutil.copy(FIXTURE / "more.md", more)
    result = run(["merge", str(src), str(project), "--write", "--approve"])
    assert result.returncode == 0, result.stderr
    result = run(["merge", str(more), str(project), "--write", "--approve"])
    assert result.returncode == 0, result.stderr

    result = run(["search", "deploy", str(project)])
    assert result.returncode == 0, result.stderr
    data = json.loads(result.stdout)
    assert data["results"]
    names = [r.get("name", "").lower() for r in data["results"]]
    assert any("deploy" in n for n in names)

    result = run(["search", "pip", str(project)])
    assert result.returncode == 0, result.stderr
    data = json.loads(result.stdout)
    assert any("pip install" in r["name"] for r in data["results"])


def test_plan_outputs_integration_guidance(tmp_path):
    project, _ = _setup_project(tmp_path)
    result = run(["plan", str(project)])
    assert result.returncode == 0, result.stderr
    output = result.stdout
    assert "Hyper-Extract" in output
    assert "Apache-2.0" in output
    assert "no API key" in output.lower() or "API key" in output


def test_plan_writes_note_with_approval(tmp_path):
    project, _ = _setup_project(tmp_path)
    result = run(["plan", str(project), "--write", "--approve"])
    assert result.returncode == 0, result.stderr
    plan_path = project / ".devin" / "notes" / "structured-knowledge-extraction" / "plan.md"
    assert plan_path.is_file()
    text = plan_path.read_text(encoding="utf-8")
    assert "Hyper-Extract" in text
    assert "Apache-2.0" in text


def test_default_mode_does_not_write_outside_devin(tmp_path):
    project, src = _setup_project(tmp_path)
    before = {f: f.read_bytes() for f in project.rglob("*") if f.is_file() and f.relative_to(project).parts[0] != ".devin"}
    for cmd in (["extract", str(src), str(project)], ["search", "test", str(project)], ["plan", str(project)]):
        result = run(cmd)
        assert result.returncode == 0, result.stderr
    for f, content in before.items():
        assert f.read_bytes() == content, f"{f} was modified outside .devin"


def test_extract_relative_source_against_project(tmp_path):
    project, src = _setup_project(tmp_path)
    # Use the filename so the path is relative to project, not to cwd.
    result = run(["extract", "notes.md", str(project)], cwd=tmp_path)
    assert result.returncode == 0, result.stderr
    data = json.loads(result.stdout)
    assert "notes.md" in data["sources"]


def test_entity_ids_preserve_punctuation(tmp_path):
    project, _ = _setup_project(tmp_path, source_name="punctuation.md")
    src = project / "notes.md"
    shutil.copy(FIXTURE / "punctuation.md", src)
    result = run(["extract", str(src), str(project)])
    assert result.returncode == 0, result.stderr
    data = json.loads(result.stdout)
    headings = [e for e in data["entities"].values() if e["type"] == "heading"]
    names = {h["name"] for h in headings}
    assert "foo.md" in names
    assert "foo md" in names
    assert not data["conflicts"]


def test_content_deterministic_timestamp(tmp_path):
    project, src = _setup_project(tmp_path)
    result = run(["extract", str(src), str(project)])
    assert result.returncode == 0, result.stderr
    data_a = json.loads(result.stdout)

    # Alter mtime without changing content.
    os.utime(src, (1, 1))
    result = run(["extract", str(src), str(project)])
    assert result.returncode == 0, result.stderr
    data_b = json.loads(result.stdout)
    assert data_a == data_b


def test_reject_symlinked_devin(tmp_path):
    real_devin = tmp_path / "real_devin"
    real_devin.mkdir()
    project = tmp_path / "project"
    project.mkdir()
    devin = project / ".devin"
    try:
        devin.symlink_to(real_devin, target_is_directory=True)
    except OSError:
        pytest.skip("directory symlinks not supported on this platform")
    src = project / "notes.md"
    shutil.copy(FIXTURE / "source.md", src)
    result = run(["extract", str(src), str(project), "--write", "--approve"])
    assert result.returncode != 0
    assert "symlinked .devin" in result.stderr.lower()


def test_source_url_not_double_extracted(tmp_path):
    project, _ = _setup_project(tmp_path, source_name="source_url.md")
    src = project / "notes.md"
    shutil.copy(FIXTURE / "source_url.md", src)
    result = run(["extract", str(src), str(project)])
    assert result.returncode == 0, result.stderr
    data = json.loads(result.stdout)
    urls = [e for e in data["entities"].values() if e["type"] == "url"]
    assert len(urls) == 1
    assert urls[0]["name"] == "https://example.com/source"
    assert not data["conflicts"]


def test_link_and_bare_url_not_overlapping(tmp_path):
    project, _ = _setup_project(tmp_path, source_name="link_url.md")
    src = project / "notes.md"
    shutil.copy(FIXTURE / "link_url.md", src)
    result = run(["extract", str(src), str(project)])
    assert result.returncode == 0, result.stderr
    data = json.loads(result.stdout)
    urls = {e["name"] for e in data["entities"].values() if e["type"] == "url"}
    assert urls == {"https://example.com/link", "https://example.com/bare"}
    assert not data["conflicts"]


def test_merge_preserves_per_source_hash_and_metadata(tmp_path):
    project, src = _setup_project(tmp_path)
    result = run(["extract", str(src), str(project), "--write", "--approve"])
    assert result.returncode == 0, result.stderr

    more = project / "more.md"
    shutil.copy(FIXTURE / "more.md", more)
    result = run(["merge", str(more), str(project), "--write", "--approve"])
    assert result.returncode == 0, result.stderr
    data = json.loads((project / ".devin" / "notes" / "structured-knowledge-extraction" / "knowledge.json").read_text(encoding="utf-8"))
    assert isinstance(data["sources"], dict)
    for s in ("notes.md", "more.md"):
        assert s in data["sources"]
        assert data["sources"][s]["sha256"]
        assert data["sources"][s]["extracted_at"]


def test_merge_reports_source_changed_conflict(tmp_path):
    project, src = _setup_project(tmp_path)
    result = run(["extract", str(src), str(project), "--write", "--approve"])
    assert result.returncode == 0, result.stderr

    # Change the content of the already-merged source.
    src.write_text("# Modified\n", encoding="utf-8")
    result = run(["merge", str(src), str(project), "--write", "--approve"])
    assert result.returncode == 0, result.stderr
    data = json.loads(result.stdout)
    assert any(c["kind"] == "source_changed" and c["source"] == "notes.md" for c in data["conflicts"])
