"""Run the manual memory workflow in fresh processes with a private test profile."""

from contextlib import closing
from hashlib import sha256
import json
import os
from pathlib import Path
import shutil
import sqlite3
import subprocess
import sys
import time

import pytest


WRAPPER = Path(__file__).resolve().parents[2] / "extensions/devin-memory/wrapper.py"


def _profile_cli(profile):
    def run(cwd, *args, ok=True):
        assert WRAPPER.is_file(), "Manual memory CLI has not been implemented"
        env = dict(os.environ, LOCALAPPDATA=str(profile), XDG_STATE_HOME=str(profile))
        proc = subprocess.run(
            [sys.executable, str(WRAPPER), "--json", *args],
            cwd=cwd, env=env, capture_output=True, text=True, encoding="utf-8",
            errors="replace", timeout=10,
        )
        data = json.loads(proc.stdout)
        assert (proc.returncode == 0) is ok, data
        assert data["ok"] is ok
        return data["result"] if ok else data["code"]

    return run


@pytest.fixture
def cli(tmp_path):
    profile = tmp_path / "local state"
    return _profile_cli(profile), profile


def test_scope_manual_resume(tmp_path, cli):
    run, profile = cli
    first = tmp_path / "a" / "same-name"
    second = tmp_path / "b" / "same-name"
    first.mkdir(parents=True)
    second.mkdir(parents=True)
    assert run(first, "status") == {"state": "uninitialized", "revision": 0}
    assert run(first, "search", "pytest") == []
    assert not profile.exists()

    (first / "decisao.md").write_text("Run pytest -q for integration.", encoding="utf-8")
    run(first, "remember", "--scope", "project", "--key", "tests", "--file", "decisao.md")
    subdirectory = first / "src"
    subdirectory.mkdir()
    hit, = run(subdirectory, "search", "pytest")
    assert hit["key"] == "tests"
    assert hit["source"] == "decisao.md"
    assert "pytest -q" in hit["excerpt"]

    (second / "outra.md").write_text("Use tox for integration.", encoding="utf-8")
    run(second, "remember", "--scope", "project", "--key", "tests", "--file", "outra.md")
    assert run(second, "search", "pytest") == []
    assert run(first, "search", "tox") == []

    (first / "global.md").write_text("Prefer revis\u00e3o before shipping.", encoding="utf-8")
    run(first, "remember", "--scope", "global", "--key", "review", "--file", "global.md")
    for cwd in (first, second, tmp_path):
        hit, = run(cwd, "search", "revisao")
        assert hit["scope"] == "global"
        assert hit["source"] == "global.md"
    assert run(tmp_path, "search", "pytest") == []


def test_invalid_or_duplicate_note_preserves_store(tmp_path, cli):
    run, profile = cli
    source = tmp_path / "note.md"
    args = ("remember", "--scope", "project", "--key", "decision", "--file", "note.md")
    for invalid in (b"  ", b"x" * 8193, b"\xff"):
        source.write_bytes(invalid)
        assert run(tmp_path, *args, ok=False) == "E_FORMAT"
    assert not profile.exists()

    source.write_text("Use pytest.", encoding="utf-8")
    run(tmp_path, *args)
    before = run(tmp_path, "status")
    source.write_text("Use tox.", encoding="utf-8")
    assert run(tmp_path, *args, ok=False) == "E_EXISTS"
    assert run(tmp_path, "status") == before
    assert run(tmp_path, "search", 'pytest" NOT "never')[0]["key"] == "decision"
    assert run(tmp_path, "search", 'tox" OR "("') == []


def test_curation_edit_archive_review(tmp_path, cli):
    run, _ = cli
    args = ("remember", "--scope", "project", "--key", "runner", "--file")
    (tmp_path / "first.md").write_text("Use pytest.", encoding="utf-8")
    (tmp_path / "second.md").write_text("Use tox.", encoding="utf-8")
    first = run(tmp_path, *args, "first.md")["version"]
    second = run(tmp_path, *args, "second.md", "--base-version", first)["version"]
    assert first != second
    assert run(tmp_path, "search", "pytest") == []
    hit, = run(tmp_path, "search", "tox")
    assert (hit["version"], hit["source"]) == (second, "second.md")

    before = run(tmp_path, "status")
    assert run(tmp_path, *args, "first.md", "--base-version", first, ok=False) == "E_PLAN_STALE"
    assert run(tmp_path, "status") == before
    assert run(tmp_path, "search", "tox")[0]["version"] == second

    run(tmp_path, "archive", "runner", "--scope", "project")
    assert run(tmp_path, "search", "tox") == []
    history = run(tmp_path, "review", "runner")["versions"]
    assert [(v["version"], v["state"], v["source"], v["body"]) for v in history] == [
        (second, "archived", "second.md", "Use tox."),
        (first, "superseded", "first.md", "Use pytest."),
    ]
    before = run(tmp_path, "status")
    run(tmp_path, "archive", "runner", "--scope", "project")
    assert run(tmp_path, *args, "second.md", "--base-version", second, ok=False) == "E_PLAN_STALE"
    assert run(tmp_path, "status") == before

    run(tmp_path, "review", "runner", "--scope", "project", "--approve", first)
    assert run(tmp_path, "search", "pytest")[0]["version"] == first
    assert run(tmp_path, "search", "tox") == []
    assert len(run(tmp_path, "review", "runner")["versions"]) == 2


def test_curation_requires_explicit_mutation_scope(tmp_path, cli):
    run, profile = cli
    archive = ("archive", "runner", "--scope", "project")
    assert "--approve" in run(tmp_path, "review", "--help")["help"]
    assert run(tmp_path, *archive, ok=False) == "E_NOT_FOUND"
    assert not profile.exists()
    (tmp_path / "project.md").write_text("Use pytest.", encoding="utf-8")
    (tmp_path / "global.md").write_text("Use tox.", encoding="utf-8")
    remember = ("remember", "--key", "runner", "--file")
    project = run(tmp_path, *remember, "project.md", "--scope", "project")["version"]
    global_note = run(tmp_path, *remember, "global.md", "--scope", "global")["version"]
    before = run(tmp_path, "status")
    assert run(tmp_path, "review", "runner", ok=False) == "E_SCOPE"
    assert run(tmp_path, "archive", "runner", ok=False) == "E_FORMAT"
    assert run(tmp_path, "review", "runner", "--approve", project, ok=False) == "E_FORMAT"
    assert run(tmp_path, *remember, "global.md", "--base-version", project, ok=False) == "E_FORMAT"
    assert run(
        tmp_path, "review", "runner", "--scope", "project", "--approve", global_note, ok=False
    ) == "E_NOT_FOUND"
    assert run(tmp_path, "status") == before

    run(tmp_path, *archive)
    assert run(tmp_path, "search", "pytest") == []
    assert run(tmp_path, "search", "tox")[0]["version"] == global_note


def test_curation_preserves_t01_store(tmp_path, cli):
    run, profile = cli
    db_path = profile / "devin" / "memory-v1" / "memory.sqlite3"
    db_path.parent.mkdir(parents=True)
    body = "Use unittest."
    version = sha256(body.encode("utf-8")).hexdigest()
    with closing(sqlite3.connect(db_path)) as db, db:
        db.executescript(
            "CREATE TABLE state (id INTEGER PRIMARY KEY, revision INTEGER NOT NULL);"
            "INSERT INTO state VALUES (1, 1);"
            "CREATE TABLE scopes (id TEXT PRIMARY KEY, root TEXT UNIQUE);"
            "INSERT INTO scopes VALUES ('global', NULL);"
            "CREATE TABLE notes (id INTEGER PRIMARY KEY, scope TEXT NOT NULL REFERENCES scopes(id),"
            " key TEXT NOT NULL, version TEXT NOT NULL, body TEXT NOT NULL, source TEXT NOT NULL,"
            " UNIQUE(scope, key));"
            "CREATE VIRTUAL TABLE fts_global USING fts5(body, content='', tokenize='unicode61');"
        )
        db.execute("INSERT INTO notes VALUES (7, 'global', 'runner', ?, ?, 'old.md')", (version, body))
        db.execute("INSERT INTO fts_global(rowid, body) VALUES (7, ?)", (body,))

    original = db_path.read_bytes()
    assert run(tmp_path, "review", "runner")["versions"][0]["version"] == version
    assert run(tmp_path, "search", "unittest")[0]["source"] == "old.md"
    assert db_path.read_bytes() == original

    (tmp_path / "new.md").write_text("Use pytest.", encoding="utf-8")
    run(
        tmp_path, "remember", "--scope", "global", "--key", "runner",
        "--file", "new.md", "--base-version", version,
    )
    assert run(tmp_path, "status") == {"state": "ready", "revision": 2}
    assert run(tmp_path, "search", "unittest") == []
    assert run(tmp_path, "search", "pytest")[0]["source"] == "new.md"
    old = run(tmp_path, "review", "runner")["versions"][1]
    assert (old["version"], old["source"], old["body"]) == (version, "old.md", body)


def test_transfer_export_atomic(tmp_path, cli):
    run, profile = cli
    (tmp_path / "first.md").write_bytes("Cafe\u0301\r\nold".encode("utf-8"))
    (tmp_path / "second.md").write_text("Revis\u00e3o atual.", encoding="utf-8")
    (tmp_path / "private.md").write_text("Project-only marker.", encoding="utf-8")
    save = ("remember", "--key", "decision", "--scope", "global", "--file")
    base = run(tmp_path, *save, "first.md")["version"]
    run(tmp_path, *save, "second.md", "--base-version", base)
    run(tmp_path, "archive", "decision", "--scope", "global")
    project = run(
        tmp_path, "remember", "--key", "decision", "--scope", "project", "--file", "private.md",
    )["scope"]
    db = profile / "devin" / "memory-v1" / "memory.sqlite3"
    before = db.read_bytes()

    args = ("export", "--scope", "global", "--out")
    target = tmp_path / "exporta\u00e7\u00e3o 1.jsonl"
    receipt = run(tmp_path, *args, target.name)
    run(tmp_path, *args, "second export.jsonl")
    data = target.read_bytes()
    assert data == (tmp_path / "second export.jsonl").read_bytes()
    assert db.read_bytes() == before
    assert b"Project-only marker" not in data and b"\r" not in data
    assert data.endswith(b"\n") and not data.startswith(b"\xef\xbb\xbf")
    lines = data.splitlines(keepends=True)
    header, *records, footer = map(json.loads, lines)
    assert header == {
        "type": "header", "format": "devin-memory", "schema_version": 1, "scopes": ["global"],
    }
    assert [record["type"] for record in records] == ["memory", "memory", "origin", "origin"]
    assert all(record["scope"] == "global" for record in records)
    digest = sha256(b"".join(lines[:-1])).hexdigest()
    assert footer == {"type": "footer", "sha256": digest}
    assert receipt["sha256"] == digest and "plaintext" in receipt["warning"]
    assert receipt["counts"] == {"memory": 2, "origin": 2, "edge": 0}
    assert {r["state"]: r["payload"]["body"] for r in records[:2]} == {
        "superseded": "Caf\u00e9\nold", "archived": "Revis\u00e3o atual.",
    }
    for memory in records[:2]:
        canonical = json.dumps(memory["payload"], ensure_ascii=False, sort_keys=True, separators=(",", ":"))
        assert memory["sha256"] == sha256(canonical.encode("utf-8")).hexdigest()
    assert {r["sha256"] for r in records[:2]} == {r["sha256"] for r in records[2:]}
    assert {r["source"] for r in records[2:]} == {"first.md", "second.md"}

    before_files = sorted(p.name for p in tmp_path.iterdir())
    assert run(tmp_path, *args, target.name, ok=False) == "E_EXISTS"
    assert target.read_bytes() == data
    assert sorted(p.name for p in tmp_path.iterdir()) == before_files

    result = run(tmp_path, "export", "--scope", "project", "--out", "project.jsonl")
    assert result["scopes"] == [project] and result["counts"]["memory"] == 1
    exported = (tmp_path / "project.jsonl").read_bytes()
    assert b"Project-only marker" in exported and b"old" not in exported
    assert str(tmp_path).encode("utf-8") not in exported


def test_transfer_limit_never_publishes_partial_package(tmp_path, cli):
    run, _ = cli
    note = tmp_path / "large.md"
    # The stored body fits, but JSON escaping makes its record too large.
    note.write_bytes(b"body" + b"\x01" * (8192 - 4))
    run(tmp_path, "remember", "--scope", "global", "--key", "large", "--file", note.name)
    files = sorted(p.name for p in tmp_path.iterdir())
    assert run(tmp_path, "export", "--scope", "global", "--out", "limited.jsonl", ok=False) == "E_LIMIT"
    assert sorted(p.name for p in tmp_path.iterdir()) == files


def _remember(run, root, key, filename, body, scope="global"):
    (root / filename).write_text(body, encoding="utf-8")
    return run(root, "remember", "--scope", scope, "--key", key, "--file", filename)


def test_merge_preview_conflict_and_replay(tmp_path, cli):
    dest, profile = cli
    source = _profile_cli(tmp_path / "source state")
    body = "Use fennel locally."
    local = _remember(dest, tmp_path, "recipe", "local.md", body)
    _remember(dest, tmp_path, "shared", "local-shared.md", "Same observation.")
    _remember(dest, tmp_path, "retired", "retired.md", "Use cinnamon.")
    dest(tmp_path, "archive", "retired", "--scope", "global")
    _remember(source, tmp_path, "recipe", "other.md", "Use thyme remotely.")
    _remember(source, tmp_path, "shared", "other-shared.md", "Same observation.")
    _remember(source, tmp_path, "retired", "retired.md", "Use cinnamon.")
    _remember(source, tmp_path, "fresh", "new.md", "Use oregano.")
    source(tmp_path, "export", "--scope", "global", "--out", "from.jsonl")

    db = profile / "devin" / "memory-v1" / "memory.sqlite3"
    args = ("import", "from.jsonl", "--map", "global=global")
    before = db.read_bytes()
    preview = dest(tmp_path, *args)
    assert db.read_bytes() == before
    assert preview["counts"] == {
        "additions": 2, "new_payloads": 2, "duplicates": 2, "origins": 3,
        "conflicts": 1, "suspended": 1, "pending": 3,
    }
    first_plan = preview["plan_id"]
    assert dest(tmp_path, "search", "fennel")[0]["version"] == local["version"]
    _remember(source, tmp_path, "another", "another.md", "Use mint.")
    source(tmp_path, "export", "--scope", "global", "--out", "changed.jsonl")
    assert dest(
        tmp_path, "import", "changed.jsonl", "--map", "global=global",
        "--apply", first_plan, ok=False,
    ) == "E_PLAN_STALE"
    assert db.read_bytes() == before
    _remember(dest, tmp_path, "independent", "independent.md", "Use chives.")
    before = db.read_bytes()
    assert dest(tmp_path, *args, "--apply", first_plan, ok=False) == "E_PLAN_STALE"
    assert db.read_bytes() == before

    preview = dest(tmp_path, *args)
    command = (*args, "--apply", preview["plan_id"])
    receipt = dest(tmp_path, *command)
    assert not receipt["replayed"] and receipt["counts"] == preview["counts"]
    history = dest(tmp_path, "review", "recipe")
    assert history["conflict"]
    assert {(v["body"], v["state"]) for v in history["versions"]} == {
        (body, "pending"), ("Use thyme remotely.", "pending"),
    }
    assert dest(tmp_path, "search", "fennel thyme cinnamon oregano") == []
    assert dest(tmp_path, "review", "retired")["versions"][0]["state"] == "archived"
    assert dest(tmp_path, "review", "fresh")["versions"][0]["state"] == "pending"
    assert dest(tmp_path, "search", "observation")[0]["source"] == "local-shared.md"

    dest(tmp_path, "review", "recipe", "--scope", "global", "--approve", local["version"])
    assert dest(tmp_path, "search", "fennel")[0]["version"] == local["version"]
    assert not dest(tmp_path, "review", "recipe")["conflict"]
    dest(tmp_path, "archive", "recipe", "--scope", "global")
    before = db.read_bytes()
    assert dest(tmp_path, *command)["replayed"]
    assert db.read_bytes() == before
    assert dest(tmp_path, "search", "fennel thyme") == []
    dest(tmp_path, "export", "--scope", "global", "--out", "merged.jsonl")
    records = [json.loads(line) for line in (tmp_path / "merged.jsonl").read_bytes().splitlines()]
    assert {r["source"] for r in records if r["type"] == "origin" and r["key"] == "shared"} == {
        "local-shared.md", "other-shared.md",
    }


@pytest.mark.parametrize("case", ["checksum", "duplicate_key", "dangling", "invalid_utf8", "bad_map"])
def test_merge_refuses_invalid_package_without_initializing(tmp_path, cli, case):
    dest, profile = cli
    source = _profile_cli(tmp_path / "source state")
    _remember(source, tmp_path, "sample", "source.md", "Synthetic content.")
    source(tmp_path, "export", "--scope", "global", "--out", "from.jsonl")
    path = tmp_path / "from.jsonl"
    lines = path.read_bytes().splitlines(keepends=True)
    mapping, code = "global=global", "E_FORMAT"
    if case == "checksum":
        lines[0] = b" " + lines[0]
    elif case == "duplicate_key":
        lines[0] = lines[0].replace(b'"schema_version":1', b'"schema_version":1,"schema_version":1')
    elif case == "dangling":
        lines[2] = lines[2].replace(b'"key":"sample"', b'"key":"missing"')
    elif case == "invalid_utf8":
        lines[1] = lines[1].replace(b"Synthetic", b"\xff")
    else:
        mapping, code = "global=project:" + "a" * 32, "E_SCOPE"
    if case != "checksum":
        digest = sha256(b"".join(lines[:-1])).hexdigest()
        lines[-1] = (json.dumps({"type": "footer", "sha256": digest}) + "\n").encode("utf-8")
    path.write_bytes(b"".join(lines))
    assert dest(tmp_path, "import", "from.jsonl", "--map", mapping, ok=False) == code
    assert not profile.exists()


def test_merge_round_trip_is_order_independent(tmp_path):
    source = _profile_cli(tmp_path / "source state")
    _remember(source, tmp_path, "left", "one.md", "Same content.")
    source(tmp_path, "export", "--scope", "global", "--out", "left.jsonl")
    other = _profile_cli(tmp_path / "other state")
    _remember(other, tmp_path, "right", "two.md", "Same content.")
    other(tmp_path, "export", "--scope", "global", "--out", "right.jsonl")

    results = []
    for label, package_names in (("forward", ("left", "right")), ("reverse", ("right", "left"))):
        profile = tmp_path / label
        run = _profile_cli(profile)
        for index, name in enumerate(package_names):
            command = ("import", name + ".jsonl", "--map", "global=global")
            preview = run(tmp_path, *command)
            assert preview["counts"]["new_payloads"] == (1 if index == 0 else 0)
            assert preview["counts"]["additions"] == 1
            if index == 0:
                assert not profile.exists()
            run(tmp_path, *command, "--apply", preview["plan_id"])
        assert run(tmp_path, "search", "content") == []
        run(tmp_path, "export", "--scope", "global", "--out", label + ".jsonl")
        data = (tmp_path / (label + ".jsonl")).read_bytes()
        records = [json.loads(line) for line in data.splitlines()]
        assert {r["key"] for r in records if r["type"] == "memory"} == {"left", "right"}
        results.append(data)
    assert results[0] == results[1]


def test_merge_project_mapping_must_target_current_scope(tmp_path, cli):
    dest, _ = cli
    source = _profile_cli(tmp_path / "source state")
    src_id = _remember(source, tmp_path, "incoming", "source.md", "Project data.", "project")["scope"]
    _remember(source, tmp_path, "private", "global.md", "Unselected global data.")
    source(tmp_path, "export", "--scope", "global", "--scope", "project", "--out", "from.jsonl")
    dest_id = _remember(dest, tmp_path, "local", "target.md", "Local data.", "project")["scope"]
    prefix = ("import", "from.jsonl", "--map")
    assert dest(tmp_path, *prefix, f"{src_id}=global", ok=False) == "E_SCOPE"
    assert dest(tmp_path, *prefix, f"{src_id}={src_id}", ok=False) == "E_SCOPE"
    args = (*prefix, f"{src_id}={dest_id}")
    preview = dest(tmp_path, *args)
    assert preview["mapping"] == {src_id: dest_id} and preview["counts"]["additions"] == 1
    dest(tmp_path, *args, "--apply", preview["plan_id"])
    assert dest(tmp_path, "review", "private", "--scope", "global", ok=False) == "E_NOT_FOUND"
    history = dest(tmp_path, "review", "incoming", "--scope", "project")
    assert history["scope"] == dest_id and history["versions"][0]["state"] == "pending"


def _legacy_note(path, body, status="active"):
    path.parent.mkdir(parents=True, exist_ok=True)
    text = (
        '---\ntitle: "A fixture note"\ndate: "2026-11-20"\nsession: ""\n'
        "category: decision\ntags:\n  - decision\n"
        f"status: {status}\ncues:\n  - keyword: 'compass'\n  - path: \"src/map.py\"\n---\n{body}\n"
    )
    path.write_bytes(text.replace("\n", "\r\n").encode("utf-8"))


def _legacy_hashes(root):
    return {p.relative_to(root): sha256(p.read_bytes()).hexdigest() for p in root.rglob("*.md")}


def test_legacy_migration_read_only(tmp_path, cli, monkeypatch):
    run, profile = cli
    project = tmp_path / "project"
    legacy = project / ".devin" / "memory"
    _legacy_note(legacy / "notes" / "caf\u00e9.md", "Decis\u00e3o: use a compass.")
    _legacy_note(legacy / "decisions" / "caf\u00e9.md", "Retired sextant.", "archived")
    (legacy / "MOC.md").write_text("This index is not a note.", encoding="utf-8")
    monkeypatch.setenv("DEVIN_MEMORY_DIR", str(tmp_path / "not selected"))
    before = _legacy_hashes(legacy)
    migrate = ("migrate", "--project", ".")
    preview = run(project, *migrate)
    assert not preview["applied"]
    assert preview["counts"] == {
        "additions": 2, "new_payloads": 2, "duplicates": 0, "origins": 2,
        "conflicts": 0, "suspended": 0, "pending": 2,
    }
    assert not profile.exists() and _legacy_hashes(legacy) == before
    assert "compass" not in json.dumps(preview)

    apply = (*migrate, "--apply", preview["plan_id"])
    receipt = run(project, *apply)
    assert receipt["applied"] and not receipt["replayed"]
    assert receipt["counts"] == preview["counts"]
    assert _legacy_hashes(legacy) == before
    assert run(project, "search", "compass sextant") == []
    review = ("review", "notes/cafe\u0301.md", "--legacy-path", "--scope", "project")
    note = run(project, *review)
    assert note["scope"].startswith("project:") and note["scope"] in receipt["mapping"].values()
    version = note["versions"][0]
    assert version["state"] == "pending" and version["body"] == "Decis\u00e3o: use a compass.\n"
    assert version["origins"] == [{
        "source": "notes/caf\u00e9.md",
        "legacy": {
            "title": "A fixture note", "category": "decision", "status": "active",
            "cues": [{"keyword": "compass"}, {"path": "src/map.py"}],
        },
    }]
    archived = run(project, "review", "decisions/caf\u00e9.md", "--legacy-path", "--scope", "project")
    assert archived["key"] != note["key"]
    assert archived["versions"][0]["state"] == "pending"
    assert archived["versions"][0]["origins"][0]["legacy"]["status"] == "archived"

    run(project, *review, "--approve", version["version"])
    assert run(project, "search", "compass")[0]["source"] == "notes/caf\u00e9.md"
    assert run(tmp_path, "search", "compass") == []
    db = profile / "devin" / "memory-v1" / "memory.sqlite3"
    ready = db.read_bytes()
    assert run(project, *apply)["replayed"]
    assert db.read_bytes() == ready and _legacy_hashes(legacy) == before


def test_legacy_override_binds_input_and_preserves_provenance(tmp_path, cli):
    run, profile = cli
    project = tmp_path / "project"
    project.mkdir()
    source = tmp_path / "legacy elsewhere"
    note = source / "sample.md"
    _legacy_note(note, "Shared body.")
    local = _remember(run, project, "local", "local.md", "Shared body.\n", "project")
    migrate = ("migrate", "--project", ".", "--source", str(source))
    db = profile / "devin" / "memory-v1" / "memory.sqlite3"
    before = db.read_bytes()
    assert run(project, "migrate", "--project", ".", ok=False) == "E_IO"
    preview = run(project, *migrate)
    assert db.read_bytes() == before
    assert preview["counts"]["duplicates"] == 1 and preview["counts"]["new_payloads"] == 0
    assert run(
        project, "migrate", "--project", str(tmp_path), "--source", str(source),
        "--apply", preview["plan_id"], ok=False,
    ) == "E_PLAN_STALE"
    _legacy_note(note, "Shared body.", "archived")
    hashes = _legacy_hashes(source)
    assert run(project, *migrate, "--apply", preview["plan_id"], ok=False) == "E_PLAN_STALE"
    assert db.read_bytes() == before and _legacy_hashes(source) == hashes
    preview = run(project, *migrate)
    run(project, *migrate, "--apply", preview["plan_id"])
    assert _legacy_hashes(source) == hashes
    migrated = run(project, "review", "sample.md", "--legacy-path", "--scope", "project")
    assert migrated["scope"] == local["scope"]
    assert migrated["versions"][0]["version"] == local["version"]
    _legacy_note(note, "Shared body.", "active")
    preview = run(project, *migrate)
    assert preview["counts"]["additions"] == 0 and preview["counts"]["origins"] == 1
    run(project, *migrate, "--apply", preview["plan_id"])
    migrated = run(project, "review", migrated["key"], "--scope", "project")
    assert len(migrated["versions"]) == 1 and migrated["versions"][0]["state"] == "pending"
    assert {o["legacy"]["status"] for o in migrated["versions"][0]["origins"]} == {"active", "archived"}

    package = project / "project.jsonl"
    run(project, "export", "--scope", "project", "--out", package.name)
    other = _profile_cli(tmp_path / "other state")
    dest_id = _remember(other, project, "dest", "dest.md", "Own note.", "project")["scope"]
    args = ("import", package.name, "--map", f"{local['scope']}={dest_id}")
    other(project, *args, "--apply", other(project, *args)["plan_id"])
    history = other(project, "review", migrated["key"], "--scope", "project")
    assert history["versions"][0]["origins"] == migrated["versions"][0]["origins"]
    assert not other(project, "search", "Shared")


@pytest.mark.parametrize("case", ["duplicate", "bad_utf8", "outside_link"])
def test_legacy_refuses_invalid_source_without_writing(tmp_path, cli, case):
    run, profile = cli
    root = tmp_path / "project"
    legacy = root / ".devin" / "memory"
    _legacy_note(legacy / "valid.md", "Synthetic decision.")
    if case == "outside_link":
        outside = tmp_path / "outside"
        _legacy_note(outside / "private.md", "Outside note.")
        link = legacy / "linked"
        if os.name == "nt":
            subprocess.run(
                ["cmd.exe", "/d", "/c", "mklink", "/J", str(link), str(outside)],
                capture_output=True, encoding="utf-8", errors="replace", timeout=10, check=True,
            )
        else:
            link.symlink_to(outside, target_is_directory=True)
        paths = [legacy / "valid.md", outside / "private.md"]
        code = "E_IO"
    else:
        bad = legacy / "invalid.md"
        bad.write_bytes(
            b"---\ncategory: decision\nstatus: active\nstatus: archived\n---\nContent."
            if case == "duplicate" else b"\xff"
        )
        paths = [legacy / "valid.md", bad]
        code = "E_FORMAT"
    before = [p.read_bytes() for p in paths]
    assert run(root, "migrate", "--project", ".", ok=False) == code
    assert not profile.exists() and [p.read_bytes() for p in paths] == before


def test_legacy_preserves_v2_origins_and_replay(tmp_path, cli):
    run, profile = cli
    source = _profile_cli(tmp_path / "source state")
    _remember(run, tmp_path, "local", "local.md", "Local content.")
    _remember(source, tmp_path, "remote", "remote.md", "Remote content.")
    source(tmp_path, "export", "--scope", "global", "--out", "package.jsonl")
    args = ("import", "package.jsonl", "--map", "global=global")
    apply = (*args, "--apply", run(tmp_path, *args)["plan_id"])
    run(tmp_path, *apply)
    db_path = profile / "devin" / "memory-v1" / "memory.sqlite3"
    with closing(sqlite3.connect(db_path)) as db, db:
        db.executescript(
            "ALTER TABLE origins RENAME TO fixture_current_origins;"
            "CREATE TABLE origins (entry_id INTEGER NOT NULL REFERENCES entries(id),"
            "source TEXT NOT NULL, PRIMARY KEY(entry_id, source)) WITHOUT ROWID;"
            "INSERT INTO origins SELECT entry_id, source FROM fixture_current_origins;"
            "DROP TABLE relations; DROP TABLE cues;"
            "ALTER TABLE entries DROP COLUMN approved_cues;"
            "PRAGMA user_version = 2;"
        )

    _legacy_note(tmp_path / ".devin" / "memory" / "legacy.md", "Migrated content.")
    before = db_path.read_bytes()
    migrate = ("migrate", "--project", ".")
    preview = run(tmp_path, *migrate)
    assert db_path.read_bytes() == before
    assert run(tmp_path, *apply)["replayed"]
    assert db_path.read_bytes() == before
    run(tmp_path, *migrate, "--apply", preview["plan_id"])
    assert run(tmp_path, "search", "Local")[0]["source"] == "local.md"
    assert run(tmp_path, "review", "remote")["versions"][0]["origins"] == [{"source": "remote.md"}]


def test_recall_related_decision(tmp_path, cli):
    run, _ = cli
    target = _remember(run, tmp_path, "retention", "retention.md", "Keep recovery snapshots for a week.")
    seed = _remember(run, tmp_path, "journal", "journal.md", "Roll back the rollbackjournal atomically.")
    query = ("search", "rollbackjournal")
    assert [hit["key"] for hit in run(tmp_path, *query)] == ["journal"]
    remember = ("remember", "--scope", "global", "--key", "journal", "--file", "journal.md",
                "--base-version", seed["version"])
    private = _remember(run, tmp_path, "foreign", "foreign.md", "Project-only note.", "project")
    assert run(tmp_path, *remember, "--relate", "related_to:foreign@" + private["version"],
               ok=False) == "E_NOT_FOUND"
    relation = "depends_on:retention@" + target["version"]
    run(tmp_path, *remember, "--relate", relation)
    hit, adjacent = run(tmp_path, *query)
    assert hit["key"] == "journal" and adjacent["key"] == "retention"
    assert adjacent["reason"] == "relation:depends_on" and adjacent["source"] == "retention.md"

    receipt = run(tmp_path, "export", "--scope", "global", "--out", "graph.jsonl")
    assert receipt["counts"]["edge"] == 1
    dest = _profile_cli(tmp_path / "recipient")
    args = ("import", "graph.jsonl", "--map", "global=global")
    preview = dest(tmp_path, *args)
    dest(tmp_path, *args, "--apply", preview["plan_id"])
    assert dest(tmp_path, *query) == []
    for key, version in (("journal", seed["version"]), ("retention", target["version"])):
        dest(tmp_path, "review", key, "--scope", "global", "--approve", version)
    assert [hit["key"] for hit in dest(tmp_path, *query)] == ["journal"]
    dest(tmp_path, "export", "--scope", "global", "--out", "recipient.jsonl")
    edges = lambda name: [r for r in map(json.loads, (tmp_path / name).read_bytes().splitlines())
                          if r["type"] == "edge"]
    assert edges("graph.jsonl") == edges("recipient.jsonl")
    run(tmp_path, "archive", "retention", "--scope", "global")
    assert [hit["key"] for hit in run(tmp_path, *query)] == ["journal"]


def test_crash_recovery_no_partial_commit(tmp_path, cli):
    run, profile = cli
    source = _profile_cli(tmp_path / "sender")
    _remember(run, tmp_path, "local", "local.md", "Local baseline.")
    _remember(source, tmp_path, "remote", "remote.md", "Incoming content.")
    source(tmp_path, "export", "--scope", "global", "--out", "incoming.jsonl")
    args = ("import", "incoming.jsonl", "--map", "global=global")
    plan = run(tmp_path, *args)["plan_id"]
    run(tmp_path, "export", "--scope", "global", "--out", "before.jsonl")
    db_path = profile / "devin/memory-v1/memory.sqlite3"
    env = dict(os.environ, LOCALAPPDATA=str(profile), XDG_STATE_HOME=str(profile),
               TEMP=str(tmp_path), TMP=str(tmp_path), TMPDIR=str(tmp_path))
    child = """
from contextlib import contextmanager
import os
import sys

sys.path.insert(0, sys.argv[1])
import wrapper
from devin_memory import merge, store

connect = store._connect
@contextmanager
def small_cache(*args, **kwargs):
    with connect(*args, **kwargs) as db:
        db.execute("PRAGMA cache_size = 2")
        db.execute("PRAGMA cache_spill = ON")
        yield db

store._connect = small_cache
where = sys.argv[2]
original = getattr(merge, where)
def interrupt(*args, **kwargs):
    original(*args, **kwargs)
    os._exit(91)

setattr(merge, where, interrupt)
raise SystemExit(wrapper.main(sys.argv[3:]))
"""
    for stage in ("_commit", "run"):
        proc = subprocess.run(
            [sys.executable, "-c", child, str(WRAPPER.parent), stage, "--json", *args, "--apply", plan],
            cwd=tmp_path, env=env, timeout=15, capture_output=True, encoding="utf-8", errors="replace",
        )
        assert proc.returncode == 91, proc.stderr
        result = run(tmp_path, "doctor", "--recover")
        assert result["state"] == "ready"
        if stage == "_commit":
            run(tmp_path, "export", "--scope", "global", "--out", "recovered.jsonl")
            assert (tmp_path / "recovered.jsonl").read_bytes() == (tmp_path / "before.jsonl").read_bytes()
            assert run(tmp_path, *args)["plan_id"] == plan
        else:
            snapshot = db_path.read_bytes()
            assert run(tmp_path, *args, "--apply", plan)["replayed"]
            assert db_path.read_bytes() == snapshot
            assert run(tmp_path, "review", "remote")["versions"][0]["state"] == "pending"

    with closing(sqlite3.connect(db_path)) as db, db:
        db.execute("BEGIN EXCLUSIVE")
        assert run(tmp_path, "doctor", ok=False) == "E_BUSY"
        assert run(tmp_path, "doctor", "--recover", ok=False) == "E_BUSY"
    with closing(sqlite3.connect(db_path)) as db, db:
        db.execute("INSERT INTO fts_global(fts_global) VALUES ('delete-all')")
    corrupted = db_path.read_bytes()
    assert run(tmp_path, "doctor", ok=False) == "E_INDEX"
    assert db_path.read_bytes() == corrupted
    run(tmp_path, "export", "--scope", "global", "--out", "pre-rebuild.jsonl")
    revision = run(tmp_path, "status")["revision"]
    assert run(tmp_path, "doctor", "--rebuild-index")["revision"] == revision
    run(tmp_path, "export", "--scope", "global", "--out", "post-rebuild.jsonl")
    assert (tmp_path / "pre-rebuild.jsonl").read_bytes() == (tmp_path / "post-rebuild.jsonl").read_bytes()
    assert run(tmp_path, "search", "baseline")[0]["key"] == "local"


def test_devin_memory_installed_profile(tmp_path):
    repo = WRAPPER.parents[2]
    bundle = tmp_path / "bundle"
    bundle.mkdir()
    (bundle / "skills").mkdir()
    (bundle / "AGENTS.md").write_text("# Test bundle\n", encoding="utf-8")
    shutil.copyfile(repo / "manifest.json", bundle / "manifest.json")
    shutil.copytree(WRAPPER.parent, bundle / "extensions/devin-memory",
                    ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
    home, app, state, workspace = (tmp_path / name for name in ("home", "app", "state", "workspace"))
    for path in (home, app, workspace):
        path.mkdir()
    target = app / "devin"
    env = dict(os.environ, HOME=str(home), USERPROFILE=str(home), APPDATA=str(app), DEVIN_HOME=str(target),
               LOCALAPPDATA=str(state), XDG_CONFIG_HOME=str(app), XDG_STATE_HOME=str(state))
    if os.name == "nt":
        name = "install.ps1"
        engine = shutil.which("pwsh") or shutil.which("powershell")
        command = [engine, "-NoProfile", "-NonInteractive", "-File", str(bundle / name)]
        dry, backup = "-DryRun", "-Backup"
    else:
        name = "install.sh"
        command = ["bash", str(bundle / name)]
        dry, backup = "--dry-run", "--backup"
    shutil.copyfile(repo / name, bundle / name)

    def install(*flags):
        proc = subprocess.run(
            [*command, *flags], cwd=workspace, env=env, capture_output=True, encoding="utf-8",
            errors="replace", timeout=60,
        )
        assert proc.returncode == 0, proc.stdout + proc.stderr

    install(dry)
    assert not target.exists() and not state.exists()
    install(backup)
    wrapper = target / "extensions/devin-memory/wrapper.py"

    def call(*args, profile=state):
        proc = subprocess.run(
            [sys.executable, str(wrapper), "--json", *args], cwd=workspace, capture_output=True,
            encoding="utf-8", errors="replace", timeout=15,
            env=dict(env, LOCALAPPDATA=str(profile), XDG_STATE_HOME=str(profile)),
        )
        envelope = json.loads(proc.stdout)
        assert proc.returncode == 0 and envelope["ok"]
        assert envelope["api_version"] == 2
        assert envelope["meta"]["answered_by"] == {"bundle": version, "wrapper": "devin-memory"}
        return envelope["result"]

    version = json.loads((bundle / "manifest.json").read_text(encoding="utf-8"))["version"]
    start = time.monotonic()
    assert call("status")["state"] == "uninitialized"
    assert not state.exists()
    (workspace / "sample.md").write_text("Use the synthetic artifact to resume.", encoding="utf-8")
    saved = call("remember", "--scope", "global", "--key", "test", "--file", "sample.md")
    assert call("search", "artifact")[0]["version"] == saved["version"]
    assert time.monotonic() - start < 60

    call("export", "--scope", "global", "--out", "package.jsonl")
    recipient = tmp_path / "recipient"
    ingest = ("import", "package.jsonl", "--map", "global=global")
    plan = call(*ingest, profile=recipient)["plan_id"]
    call(*ingest, "--apply", plan, profile=recipient)
    assert call(*ingest, "--apply", plan, profile=recipient)["replayed"]
    assert call("search", "artifact", profile=recipient) == []
    call("review", "test", "--scope", "global", "--approve", saved["version"], profile=recipient)
    assert call("search", "artifact", profile=recipient)[0]["version"] == saved["version"]
    db = state / "devin/memory-v1/memory.sqlite3"
    original = db.read_bytes()
    install(dry)
    install(backup)
    assert db.read_bytes() == original
    assert not list(target.rglob("memory.sqlite3")) and not list(bundle.rglob("memory.sqlite3"))
