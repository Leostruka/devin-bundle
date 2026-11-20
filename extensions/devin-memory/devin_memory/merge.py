"""Plan and commit a staged union in the local store."""

from contextlib import closing, contextmanager
from hashlib import sha256
from hmac import compare_digest
import json
import os
from pathlib import Path
import sqlite3

from . import store


def _stale(migrate):
    command = "migrate" if migrate else "import"
    return store.MemoryFailure("E_PLAN_STALE", f"Input, mapping or store changed. Run {command} without --apply.")


def _mapping(db, root, requested, migrate):
    resolved = {}
    project = store._project(db, root, exact=migrate) if any(scope != "global" for scope in requested) else None
    for source, target in requested.items():
        if source == "global":
            resolved[source] = "global"
        elif migrate and project is None:
            resolved[source] = "project"
        elif not project or not store.PROJECT_ID.fullmatch(project) or target not in ("project", project):
            raise store.MemoryFailure("E_SCOPE", "Map to the current registered project explicitly.")
        else:
            resolved[source] = project
    if len(set(resolved.values())) != len(resolved):
        raise store.MemoryFailure("E_SCOPE", "Map at most one source to each destination scope.")
    return resolved


def _request(path, digest, mapping, project=None):
    identity = [digest, os.path.normcase(str(path.resolve())), sorted(mapping.items())]
    if project is not None:
        # Bind migration to the selected root before that root has a database ID.
        identity.extend(("migrate", os.path.normcase(str(project))))
    return sha256(json.dumps(identity, separators=(",", ":")).encode("utf-8")).hexdigest()


def _plan(request, revision):
    return sha256(f"{request}:{revision}".encode("ascii")).hexdigest()


def _prepare(db, package, mapping, layout):
    db.execute("ATTACH DATABASE ? AS incoming", (package.as_uri() + "?mode=ro&immutable=1",))
    db.execute("CREATE TEMP TABLE scope_map (source TEXT PRIMARY KEY, scope TEXT NOT NULL UNIQUE)")
    db.executemany("INSERT INTO scope_map VALUES (?, ?)", mapping.items())
    db.execute(
        "CREATE TEMP VIEW incoming_versions AS SELECT s.scope, m.key, m.version, m.body "
        "FROM incoming.memory m JOIN scope_map s ON s.source = m.scope"
    )
    db.execute(
        "CREATE TEMP VIEW incoming_origins AS SELECT s.scope, m.key, m.version, o.source, o.legacy "
        "FROM incoming.origin o JOIN incoming.memory m USING(scope, key, digest) "
        "JOIN scope_map s ON s.source = m.scope"
    )
    db.execute(
        "CREATE TEMP VIEW incoming_relations AS SELECT s.scope, e.key, a.version, "
        "e.target_key, b.version AS target_version, e.kind, e.evidence, e.source "
        "FROM incoming.edge e JOIN incoming.memory a USING(scope, key, digest) "
        "JOIN incoming.memory b ON (b.scope, b.key, b.digest) = (e.scope, e.target_key, e.target_digest) "
        "JOIN scope_map s ON s.source = e.scope"
    )
    local = "entries" if layout >= 2 else store._catalogue(layout)
    db.execute(
        "CREATE TEMP TABLE additions AS SELECT i.scope, i.key, i.version FROM incoming_versions i "
        f"WHERE NOT EXISTS (SELECT 1 FROM {local} l "
        "WHERE l.scope = i.scope AND l.key = i.key AND l.version = i.version)"
    )
    db.execute("CREATE INDEX temp.additions_key ON additions(scope, key)")
    db.execute(
        "CREATE TEMP TABLE conflicts AS SELECT a.scope, a.key FROM additions a "
        "GROUP BY a.scope, a.key HAVING count(*) > 1 OR "
        f"EXISTS (SELECT 1 FROM {local} l WHERE l.scope = a.scope AND l.key = a.key)"
    )
    db.execute("CREATE UNIQUE INDEX temp.conflicts_key ON conflicts(scope, key)")
    return local


def _counts(db, layout, local):
    def count(query):
        return db.execute(query).fetchone()[0]

    metadata = "p.legacy" if layout >= 3 else "''"
    if layout >= 2:
        payloads = "payloads"
        provenance = "entries l JOIN origins p ON p.entry_id = l.id"
    else:
        db.execute(
            f"CREATE TEMP TABLE existing_payloads AS SELECT DISTINCT scope, version FROM {local} "
            "WHERE scope IN (SELECT scope FROM scope_map)"
        )
        db.execute("CREATE UNIQUE INDEX temp.existing_payload_key ON existing_payloads(scope, version)")
        payloads = "existing_payloads"
        provenance = f"{local} l JOIN {local} p ON p.id = l.id"
    added = count("SELECT count(*) FROM additions")
    fresh = count(
        "SELECT count(*) FROM (SELECT DISTINCT i.scope, i.version FROM incoming_versions i "
        f"WHERE NOT EXISTS (SELECT 1 FROM {payloads} p WHERE p.scope = i.scope AND p.version = i.version))"
    )
    origins = count(
        "SELECT count(*) FROM incoming_origins i "
        f"WHERE NOT EXISTS (SELECT 1 FROM {provenance} WHERE l.scope = i.scope "
        f"AND l.key = i.key AND l.version = i.version AND p.source = i.source AND {metadata} = i.legacy)"
    )
    active = "WHERE l.state = 'active'" if layout else ""
    suspended = count(f"SELECT count(*) FROM {local} l JOIN conflicts c USING(scope, key) {active}")
    counts = {
        "additions": added,
        "new_payloads": fresh,
        "duplicates": count("SELECT count(*) FROM incoming_versions") - fresh,
        "origins": origins,
        "conflicts": count("SELECT count(*) FROM conflicts"),
        "suspended": suspended,
        "pending": added + suspended,
    }
    total_edges = count("SELECT count(*) FROM incoming.edge")
    if total_edges:
        counts["relations"] = total_edges if layout < 4 else count(
            "SELECT count(*) FROM incoming_relations i LEFT JOIN entries a USING(scope, key, version) "
            "LEFT JOIN entries b ON (b.scope, b.key, b.version) = (i.scope, i.target_key, i.target_version) "
            "LEFT JOIN relations r ON (r.src, r.dst, r.kind, r.evidence, r.origin) = "
            "(a.id, b.id, i.kind, i.evidence, i.source) WHERE r.src IS NULL"
        )
    return counts


def _commit(db, scopes, counts):
    for scope in sorted({"global", *scopes}):
        store._ensure_index(db, scope)
        if counts["suspended"]:
            index = store._index(scope)
            db.execute(
                f"INSERT INTO {index} ({index}, rowid, body) "
                "SELECT 'delete', v.id, v.body FROM catalogue v JOIN conflicts c USING(scope, key) "
                "WHERE v.scope = ? AND v.state = 'active'", (scope,),
            )
    if counts["suspended"]:
        db.execute(
            "DELETE FROM cues WHERE entry_id IN (SELECT e.id FROM entries e JOIN conflicts USING(scope, key) "
            "WHERE e.state = 'active')"
        )
    db.execute(
        "UPDATE entries SET state = 'pending' WHERE state = 'active' "
        "AND (scope, key) IN (SELECT scope, key FROM conflicts)"
    )
    db.execute(
        "INSERT INTO payloads SELECT scope, version, body FROM incoming_versions "
        "WHERE true GROUP BY scope, version ON CONFLICT(scope, version) DO NOTHING"
    )
    db.execute(
        "INSERT INTO entries(scope, key, version, source, state) "
        "SELECT a.scope, a.key, a.version, min(o.source), 'pending' "
        "FROM additions a JOIN incoming_origins o USING(scope, key, version) "
        "GROUP BY a.scope, a.key, a.version"
    )
    db.execute(
        "INSERT INTO origins SELECT e.id, o.source, o.legacy FROM incoming_origins o "
        "JOIN entries e USING(scope, key, version) WHERE true ON CONFLICT DO NOTHING"
    )
    if counts.get("relations"):
        db.execute(
            "INSERT INTO relations SELECT a.id, b.id, i.kind, i.evidence, i.source, 0 "
            "FROM incoming_relations i JOIN entries a USING(scope, key, version) "
            "JOIN entries b ON (b.scope, b.key, b.version) = (i.scope, i.target_key, i.target_version) "
            "WHERE true ON CONFLICT DO NOTHING"
        )
    if any(counts.get(name) for name in ("additions", "origins", "suspended", "relations")):
        store._bump_revision(db)


def _operation(db, root, path, package, digest, requested, approved, migrate):
    mapping = _mapping(db, root, requested, migrate)
    request = _request(path, digest, requested, root) if migrate else _request(path, digest, mapping)
    layout = store._layout(db)
    if approved is not None and layout >= 2:
        saved = db.execute(
            "SELECT request, receipt FROM import_receipts WHERE plan_id = ?", (approved,)
        ).fetchone()
        if saved:
            if not compare_digest(saved["request"], request):
                raise _stale(migrate)
            return dict(json.loads(saved["receipt"]), replayed=True)
    revision = store._revision(db)
    plan_id = _plan(request, revision)
    if approved is not None and not compare_digest(approved, plan_id):
        raise _stale(migrate)
    if approved is not None and layout < store.LAYOUT:
        store._schema(db)
        layout = store._layout(db)
    if approved is not None and migrate and "project" in mapping.values():
        project = store._register_project(db, root)
        mapping = {source: project for source in mapping}
    local = _prepare(db, package, mapping, layout)
    counts = _counts(db, layout, local)
    result = {
        "plan_id": plan_id, "mapping": mapping, "counts": counts, "base_revision": revision,
        "revision": revision, "applied": approved is not None, "replayed": False,
    }
    if approved is not None:
        _commit(db, mapping.values(), counts)
        result["revision"] = store._revision(db)
        db.execute(
            "INSERT INTO import_receipts VALUES (?, ?, ?)",
            (plan_id, request, json.dumps(result, sort_keys=True)),
        )
    return result


@contextmanager
def _preview(path):
    if path.is_file():
        with store._connect(path) as db, db:
            db.execute("BEGIN")
            yield db
        return
    with closing(sqlite3.connect(":memory:", uri=True)) as db, db:
        db.row_factory = sqlite3.Row
        store._schema(db)
        yield db


def run(root: Path, package: Path, digest: str, requested: dict, approved: str | None, create_stage, *, migrate=False):
    path = store._database()
    args = (root, path, package, digest, requested, approved, migrate)
    if approved is None:
        with _preview(path) as db:
            return _operation(db, *args)
    if not path.is_file():
        if not migrate and requested != {"global": "global"}:
            raise store.MemoryFailure("E_SCOPE", "Map to an existing project scope.")
        if not compare_digest(approved, _plan(_request(path, digest, requested, root if migrate else None), 0)):
            raise _stale(migrate)
        # Do not expose a new database until its first transaction has committed.
        path.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
        fd, stage = create_stage(path.parent)
        os.close(fd)
        published = False
        try:
            with store._write(stage) as db:
                result = _operation(db, *args)
            try:
                os.link(stage, path)
            except FileExistsError:
                pass  # The winning initialization is checked under its own lock below.
            else:
                published = True
                return result
        finally:
            try:
                stage.unlink(missing_ok=True)
            except OSError:
                if not published:
                    raise
                result["warning"] = "A private initialization copy could not be removed."
    with store._write(path, upgrade=False) as db:
        return _operation(db, *args)
