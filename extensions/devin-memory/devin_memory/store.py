"""The local acervo and its per-scope lexical indexes."""

from contextlib import closing, contextmanager
from hashlib import sha256
from itertools import islice
import json
import os
from pathlib import Path
import re
import sqlite3
import stat
import unicodedata
from uuid import uuid4


BODY_LIMIT = 8192
HISTORY_PAGE = 20
LAYOUT = 4
RELATIONS = ("related_to", "depends_on", "supersedes")
EVIDENCE = ("declared", "derived")
KEY = re.compile(r"[a-zA-Z0-9][a-zA-Z0-9_.-]{0,127}")
PROJECT_ID = re.compile(r"project:[0-9a-f]{32}")
VERSION = re.compile(r"[0-9a-f]{64}")
PRIVATE_KEY = re.compile(r"-----BEGIN (?:[A-Z0-9]+ )*PRIVATE KEY-----")
TOKEN = re.compile(r"[^\W_]+")


class MemoryFailure(Exception):
    def __init__(self, code: str, message: str):
        super().__init__(message)
        self.code = code


def _regular(path: Path, mode: int) -> bool:
    try:
        info = path.lstat()
    except FileNotFoundError:
        return False
    if stat.S_IFMT(info.st_mode) != mode or (
        getattr(info, "st_file_attributes", 0) & stat.FILE_ATTRIBUTE_REPARSE_POINT
    ):
        raise MemoryFailure("E_IO", "Refusing a link or unsupported file type.")
    return True


def _local_directory(path: Path) -> Path:
    path = path.absolute()
    if path.anchor.startswith(("\\\\", "//")) or ".." in path.parts:
        raise MemoryFailure("E_IO", "Choose an existing local directory without path traversal.")
    if os.name == "nt" and any(":" in part or part.endswith((".", " ")) for part in path.parts[1:]):
        raise MemoryFailure("E_IO", "Choose a regular Windows directory.")
    for parent in reversed((path, *path.parents)):
        if not _regular(parent, stat.S_IFDIR):
            raise MemoryFailure("E_IO", "The selected directory does not exist.")
    return path


@contextmanager
def _source_file(path: Path):
    path = path.absolute()
    if not path.name or (os.name == "nt" and (":" in path.name or path.name.endswith((".", " ")))):
        raise MemoryFailure("E_IO", "Choose a regular local source file.")
    _local_directory(path.parent)
    if not _regular(path, stat.S_IFREG):
        raise MemoryFailure("E_IO", "Choose a regular local source file.")
    before = path.lstat()
    flags = os.O_RDONLY | getattr(os, "O_BINARY", 0) | getattr(os, "O_NOFOLLOW", 0)
    with os.fdopen(os.open(path, flags | getattr(os, "O_NONBLOCK", 0)), "rb") as stream:
        opened = os.fstat(stream.fileno())
        if not stat.S_ISREG(opened.st_mode) or not os.path.samestat(before, opened):
            raise MemoryFailure("E_IO", "Input changed or is not a regular local file.")
        _local_directory(path.parent)
        if not _regular(path, stat.S_IFREG) or not os.path.samestat(path.lstat(), opened):
            raise MemoryFailure("E_IO", "Input changed while opening it.")
        yield stream
        after = os.fstat(stream.fileno())
        if (opened.st_size, opened.st_mtime_ns, opened.st_ctime_ns) != (
            after.st_size, after.st_mtime_ns, after.st_ctime_ns,
        ):
            raise MemoryFailure("E_IO", "Input changed while reading it.")


def state_directory() -> Path:
    if os.name == "nt":
        base = Path(os.environ.get("LOCALAPPDATA", ""))
    else:
        base = Path(os.environ.get("XDG_STATE_HOME") or Path.home() / ".local/state")
    if not base.is_absolute() or base.anchor.startswith("\\\\"):
        raise MemoryFailure("E_STORE", "Configure an absolute local state directory.")
    path = base / "devin" / "memory-v1"
    for parent in (base, path.parent, path):
        _regular(parent, stat.S_IFDIR)
    return path


def _database() -> Path:
    db = state_directory() / "memory.sqlite3"
    for suffix in ("", "-journal", "-wal", "-shm"):
        _regular(db.with_name(db.name + suffix), stat.S_IFREG)
    return db


@contextmanager
def _connect(path: Path, *, mode: str = "ro"):
    if mode == "rwc":
        path.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
    uri = f"{path.as_uri()}?mode={mode}"
    with closing(sqlite3.connect(uri, uri=True, timeout=0.02 if mode == "ro" else 0.25)) as db:
        db.row_factory = sqlite3.Row
        if mode != "ro":
            db.execute("PRAGMA foreign_keys = ON")
            db.execute("PRAGMA journal_mode = DELETE")
            db.execute("PRAGMA synchronous = FULL")
        yield db


def _revision(db: sqlite3.Connection) -> int:
    row = db.execute("SELECT revision FROM state WHERE id = 1").fetchone()
    if row is None:
        raise MemoryFailure("E_STORE", "Missing memory store revision.")
    return row["revision"]


def status() -> dict:
    path = _database()
    if not path.is_file():
        return {"state": "uninitialized", "revision": 0}
    with _connect(path) as db:
        return {"state": "ready", "revision": _revision(db)}


def _layout(db: sqlite3.Connection) -> int:
    version = db.execute("PRAGMA user_version").fetchone()[0]
    if not 0 <= version <= LAYOUT:
        raise MemoryFailure("E_STORE", "Unsupported memory store schema.")
    return version


def _catalogue(layout: int) -> str:
    return ("notes", "versions", "catalogue")[min(layout, 2)]


def _origin_schema(db: sqlite3.Connection) -> None:
    db.execute(
        "CREATE TABLE origins (entry_id INTEGER NOT NULL REFERENCES entries(id), "
        "source TEXT NOT NULL, legacy TEXT NOT NULL DEFAULT '', "
        "PRIMARY KEY(entry_id, source, legacy)) WITHOUT ROWID"
    )


def _origin(source: str, legacy: str) -> dict:
    result = {"source": source}
    if legacy:
        try:
            result["legacy"] = json.loads(legacy)
        except ValueError:
            raise MemoryFailure("E_STORE", "Stored origin metadata is invalid.") from None
    return result


def _cue_schema(db):
    db.execute(
        "CREATE TABLE IF NOT EXISTS cues (scope TEXT NOT NULL, term TEXT NOT NULL, "
        "entry_id INTEGER NOT NULL REFERENCES entries(id), "
        "PRIMARY KEY(scope, term, entry_id)) WITHOUT ROWID"
    )
    db.execute("CREATE INDEX IF NOT EXISTS cues_by_entry ON cues(entry_id)")


def _recall_schema(db):
    db.execute("ALTER TABLE entries ADD COLUMN approved_cues TEXT NOT NULL DEFAULT ''")
    _cue_schema(db)
    db.execute(
        "CREATE TABLE relations (src INTEGER NOT NULL REFERENCES entries(id), "
        "dst INTEGER NOT NULL REFERENCES entries(id), kind TEXT NOT NULL, evidence TEXT NOT NULL, "
        "origin TEXT NOT NULL, approved INTEGER NOT NULL CHECK(approved IN (0, 1)), "
        "CHECK(src <> dst), PRIMARY KEY(src, dst, kind, evidence, origin)) WITHOUT ROWID"
    )
    db.execute("CREATE INDEX relations_by_target ON relations(dst, src) WHERE approved = 1 AND kind = 'related_to'")
    _rebuild_cues(db)
    db.execute(f"PRAGMA user_version = {LAYOUT}")


def _schema(db: sqlite3.Connection) -> None:
    layout = _layout(db)
    if layout == LAYOUT:
        return
    if layout >= 2:
        if layout == 2:
            db.execute("ALTER TABLE origins RENAME TO origins_v2")
            _origin_schema(db)
            db.execute("INSERT INTO origins(entry_id, source) SELECT entry_id, source FROM origins_v2")
        _recall_schema(db)
        return
    db.execute("CREATE TABLE IF NOT EXISTS state (id INTEGER PRIMARY KEY, revision INTEGER NOT NULL)")
    db.execute("INSERT OR IGNORE INTO state VALUES (1, 0)")
    db.execute("CREATE TABLE IF NOT EXISTS scopes (id TEXT PRIMARY KEY, root TEXT UNIQUE)")
    db.execute("INSERT OR IGNORE INTO scopes VALUES ('global', NULL)")
    db.execute(
        "CREATE TABLE payloads (scope TEXT NOT NULL REFERENCES scopes(id), "
        "version TEXT NOT NULL, body TEXT NOT NULL, PRIMARY KEY(scope, version)) WITHOUT ROWID"
    )
    db.execute(
        "CREATE TABLE entries (id INTEGER PRIMARY KEY, scope TEXT NOT NULL, key TEXT NOT NULL, "
        "version TEXT NOT NULL, source TEXT NOT NULL, "
        "state TEXT NOT NULL CHECK(state IN ('active', 'pending', 'archived', 'superseded')), "
        "UNIQUE(scope, key, version), FOREIGN KEY(scope, version) REFERENCES payloads(scope, version))"
    )
    db.execute("CREATE UNIQUE INDEX active_entries ON entries(scope, key) WHERE state = 'active'")
    db.execute("CREATE INDEX entry_history ON entries(scope, key, id DESC)")
    _origin_schema(db)
    db.execute(
        "CREATE TABLE import_receipts (plan_id TEXT PRIMARY KEY, request TEXT NOT NULL, "
        "receipt TEXT NOT NULL) WITHOUT ROWID"
    )
    db.execute(
        "CREATE VIEW catalogue AS SELECT e.*, p.body FROM entries e JOIN payloads p USING(scope, version)"
    )
    old = _catalogue(layout)
    if db.execute(
        "SELECT 1 FROM sqlite_master WHERE type = 'table' AND name = ?", (old,)
    ).fetchone():
        # Keep old tables untouched and preserve the rowids already indexed by FTS.
        state = "state" if layout else "'active'"
        db.execute(f"INSERT INTO payloads SELECT DISTINCT scope, version, body FROM {old}")
        db.execute(
            f"INSERT INTO entries SELECT id, scope, key, version, source, {state} FROM {old}"
        )
        db.execute("INSERT INTO origins(entry_id, source) SELECT id, source FROM entries")
    _recall_schema(db)


@contextmanager
def _write(path: Path, *, create: bool = False, upgrade: bool = True):
    with _connect(path, mode="rwc" if create else "rw") as db, db:
        db.execute("BEGIN IMMEDIATE")
        if upgrade:
            _schema(db)
        yield db


def _key(key: str) -> None:
    if not KEY.fullmatch(key):
        raise MemoryFailure("E_FORMAT", "Use a 1-128 character alphanumeric note key (also ._-).")


def _check_version(version: str) -> None:
    if not VERSION.fullmatch(version):
        raise MemoryFailure("E_FORMAT", "Choose the 64-character SHA-256 shown by review.")


def _not_found():
    return MemoryFailure("E_NOT_FOUND", "No matching note or version in the selected scope.")


def _bump_revision(db: sqlite3.Connection) -> None:
    db.execute("UPDATE state SET revision = revision + 1 WHERE id = 1")


def _active(db: sqlite3.Connection, scope_id: str, key: str):
    return db.execute(
        "SELECT * FROM catalogue WHERE scope = ? AND key = ? AND state = 'active'", (scope_id, key)
    ).fetchone()


def _retire(db: sqlite3.Connection, row: sqlite3.Row, state: str) -> None:
    index = _index(row["scope"])
    db.execute(
        f"INSERT INTO {index} ({index}, rowid, body) VALUES ('delete', ?, ?)",
        (row["id"], row["body"]),
    )
    db.execute("DELETE FROM cues WHERE entry_id = ?", (row["id"],))
    db.execute("UPDATE entries SET state = ? WHERE id = ?", (state, row["id"]))


def cue_terms(text):
    folded = unicodedata.normalize("NFD", text.casefold())
    return (m.group() for m in TOKEN.finditer("".join(c for c in folded if not unicodedata.combining(c))))


def _index_cues(db, entry_id, scope, key, approved_cues):
    terms = set(cue_terms(key)) | set(approved_cues.split())
    db.executemany("INSERT INTO cues VALUES (?, ?, ?)", ((scope, term, entry_id) for term in sorted(terms)))


def _rebuild_cues(db):
    _cue_schema(db)
    db.execute("DELETE FROM cues")
    for row in db.execute("SELECT id, scope, key, approved_cues FROM entries WHERE state = 'active'"):
        _index_cues(db, row["id"], row["scope"], row["key"], row["approved_cues"])


def _approved_cues(db, entry_id):
    # Snapshot cues only on local activation. An imported duplicate cannot
    # change the cues of a version that is already active.
    def terms():
        for row in db.execute(
            "SELECT source, legacy FROM origins WHERE entry_id = ? AND legacy <> '' "
            "ORDER BY source, legacy LIMIT 8", (entry_id,),
        ):
            for cue in _origin(row["source"], row["legacy"])["legacy"]["cues"]:
                yield from cue_terms(next(iter(cue.values())))

    return " ".join(dict.fromkeys(islice(terms(), 64)))


def _activate(db: sqlite3.Connection, target: sqlite3.Row, current: sqlite3.Row | None) -> None:
    if current is not None:
        if current["id"] == target["id"]:
            return
        _retire(db, current, "superseded")
    index = _index(target["scope"])
    db.execute(f"INSERT INTO {index} (rowid, body) VALUES (?, ?)", (target["id"], target["body"]))
    db.execute(
        "UPDATE entries SET state = 'superseded' WHERE scope = ? AND key = ? AND state = 'pending' AND id <> ?",
        (target["scope"], target["key"], target["id"]),
    )
    cues = _approved_cues(db, target["id"])
    db.execute("UPDATE entries SET state = 'active', approved_cues = ? WHERE id = ?", (cues, target["id"]))
    _index_cues(db, target["id"], target["scope"], target["key"], cues)
    _bump_revision(db)


def _version_ref(row: sqlite3.Row) -> dict:
    return {field: row[field] for field in ("key", "scope", "version", "source")}


def _version_row(db: sqlite3.Connection, scope_id: str, key: str, version: str):
    return db.execute(
        "SELECT * FROM catalogue WHERE scope = ? AND key = ? AND version = ?", (scope_id, key, version)
    ).fetchone()


def _scope_id(db: sqlite3.Connection, root: Path, scope: str) -> str | None:
    if scope == "global":
        return "global"
    if scope == "project":
        return _project(db, root)
    raise MemoryFailure("E_SCOPE", "Choose the project or global scope.")


@contextmanager
def snapshot(root: Path, selection: list[str]):
    """Stream selected versions and origins from one read-only transaction."""
    requested = set(selection)
    if not requested or not requested <= {"global", "project"}:
        raise MemoryFailure("E_SCOPE", "Select global or the current project explicitly.")
    project_required = "project" in requested
    no_project = "No registered memory scope for the current project."
    path = _database()
    if not path.is_file():
        if project_required:
            raise MemoryFailure("E_SCOPE", no_project)
        yield ("global",), 0, ()
        return
    with _connect(path) as db, db:
        db.execute("BEGIN")
        scopes = ["global"] if "global" in requested else []
        if project_required:
            project = _project(db, root)
            if not project:
                raise MemoryFailure("E_SCOPE", no_project)
            if not PROJECT_ID.fullmatch(project):
                raise MemoryFailure("E_STORE", "Invalid stored project scope.")
            scopes.append(project)
        layout = _layout(db)
        table = _catalogue(layout)
        state = "state" if layout else "'active' AS state"
        metadata = "o.legacy" if layout >= 3 else "'' AS legacy"
        placeholders = ",".join("?" for _ in scopes)
        queries = [
            ("memory", f"SELECT scope, key, body, {state} FROM {table} "
                       f"WHERE scope IN ({placeholders}) ORDER BY scope, key, version"),
            ("origin", f"SELECT v.scope, v.key, v.body, o.source, {metadata} FROM {table} v "
                       + ("JOIN origins o ON o.entry_id = v.id " if layout >= 2 else "JOIN "
                          f"{table} o ON o.id = v.id ")
                       + f"WHERE v.scope IN ({placeholders}) ORDER BY v.scope, v.key, v.version, o.source, legacy"),
        ]
        if layout >= 4:
            queries.append((
                "edge", "SELECT a.scope, a.key, a.body, b.key AS target_key, b.body AS target_body, "
                "r.kind, r.evidence, r.origin FROM relations r "
                "JOIN catalogue a ON a.id = r.src JOIN catalogue b ON b.id = r.dst "
                f"WHERE a.scope = b.scope AND a.scope IN ({placeholders}) "
                "ORDER BY a.scope, a.key, a.version, b.key, b.version, r.kind, r.evidence, r.origin",
            ))
        records = ((kind, row) for kind, query in queries for row in db.execute(query, scopes))
        yield tuple(scopes), _revision(db), records


@contextmanager
def _curate(root: Path, key: str, scope: str):
    _key(key)
    path = _database()
    if not path.is_file():
        raise _not_found()
    with _write(path) as db:
        scope_id = _scope_id(db, root, scope)
        if scope_id is None:
            raise _not_found()
        yield db, scope_id


def approve(root: Path, key: str, scope: str, version: str) -> dict:
    _check_version(version)
    with _curate(root, key, scope) as (db, scope_id):
        target = _version_row(db, scope_id, key, version)
        if target is None:
            raise _not_found()
        _activate(db, target, _active(db, scope_id, key))
        return dict(_version_ref(target), state="active")


def archive(root: Path, key: str, scope: str) -> dict:
    with _curate(root, key, scope) as (db, scope_id):
        current = _active(db, scope_id, key)
        if current is not None:
            _retire(db, current, "archived")
            _bump_revision(db)
        elif not db.execute(
            "SELECT 1 FROM entries WHERE scope = ? AND key = ? AND state = 'archived' LIMIT 1",
            (scope_id, key),
        ).fetchone():
            raise _not_found()
        return {"key": key, "scope": scope_id, "state": "archived"}


def review(root: Path, key: str, scope: str | None = None, before: int | None = None) -> dict:
    _key(key)
    if before is not None and not 0 < before < (1 << 63):
        raise MemoryFailure("E_FORMAT", "Use the history cursor shown by review.")
    path = _database()
    if not path.is_file():
        raise _not_found()
    with _connect(path) as db, db:
        db.execute("BEGIN")
        layout = _layout(db)
        table = _catalogue(layout)
        state = "state" if layout else "'active' AS state"
        scopes = (_scope_id(db, root, scope),) if scope else (_project(db, root), "global")
        matches = [
            sid for sid in scopes if sid and db.execute(
                f"SELECT 1 FROM {table} WHERE scope = ? AND key = ? LIMIT 1", (sid, key)
            ).fetchone()
        ]
        if not matches:
            raise _not_found()
        if len(matches) > 1:
            raise MemoryFailure("E_SCOPE", "This key exists in both scopes. Specify --scope.")
        scope_id = matches[0]
        cursor = "AND id < ?" if before is not None else ""
        params = (scope_id, key) if before is None else (scope_id, key, before)
        rows = db.execute(
            f"SELECT id, version, {state}, body, source FROM {table} WHERE scope = ? AND key = ? "
            f"{cursor} ORDER BY id DESC LIMIT ?", (*params, HISTORY_PAGE + 1)
        ).fetchall()
        conflict = layout >= 2 and bool(db.execute(
            "SELECT EXISTS(SELECT 1 FROM entries WHERE scope = ? AND key = ? AND state = 'pending') "
            "AND EXISTS(SELECT 1 FROM entries WHERE scope = ? AND key = ? LIMIT 1 OFFSET 1)",
            (scope_id, key, scope_id, key),
        ).fetchone()[0])
        page = rows[:HISTORY_PAGE]
        versions = {
            row["id"]: {field: row[field] for field in ("version", "state", "body", "source")}
            for row in page
        }
        if versions and layout >= 2:
            metadata = "legacy" if layout >= 3 else "'' AS legacy"
            placeholders = ",".join("?" for _ in versions)
            for origin in db.execute(
                f"SELECT entry_id, source, {metadata} FROM origins WHERE entry_id IN ({placeholders}) "
                "ORDER BY entry_id, source, legacy", tuple(versions),
            ):
                versions[origin["entry_id"]].setdefault("origins", []).append(
                    _origin(origin["source"], origin["legacy"])
                )
    return {
        "key": key, "scope": scope_id, "conflict": conflict,
        "versions": list(versions.values()),
        "next_before": rows[HISTORY_PAGE - 1]["id"] if len(rows) > HISTORY_PAGE else None,
    }


def _index(scope: str) -> str:
    if scope == "global":
        return "fts_global"
    if not PROJECT_ID.fullmatch(scope):
        raise MemoryFailure("E_STORE", "Invalid stored project scope.")
    return "fts_" + scope.split(":")[1]


def _ensure_index(db: sqlite3.Connection, scope: str) -> None:
    db.execute(
        f"CREATE VIRTUAL TABLE IF NOT EXISTS {_index(scope)} "
        "USING fts5(body, content='', tokenize='unicode61')"
    )


def _require_fts(db):
    try:
        db.execute("CREATE VIRTUAL TABLE temp.fts_probe USING fts5(body)")
    except sqlite3.OperationalError as exc:
        if "no such module: fts5" not in str(exc).lower():
            raise
        raise MemoryFailure("E_FTS", "Use a Python interpreter with SQLite FTS5 support.") from None


def _diagnose(db, action):
    _require_fts(db)
    layout = _layout(db)
    revision = _revision(db)
    if db.execute("PRAGMA quick_check(1)").fetchone()[0] != "ok" or db.execute(
        "PRAGMA foreign_key_check"
    ).fetchone():
        raise MemoryFailure("E_STORE", "Store consistency check failed. No reset performed; check your backup.")
    table = _catalogue(layout)
    active = "AND state = 'active'" if layout else ""
    failure = "Search index is inconsistent. Run doctor --rebuild-index."
    scopes = db.execute("SELECT id FROM scopes ORDER BY id")
    for (scope,) in scopes:
        index = _index(scope)
        if action == "rebuild-index":
            db.execute(f"DROP TABLE IF EXISTS {index}")
            _ensure_index(db, scope)
            db.execute(
                f"INSERT INTO {index}(rowid, body) SELECT id, body FROM {table} WHERE scope = ? {active}", (scope,)
            )
            continue
        exists = db.execute("SELECT 1 FROM sqlite_master WHERE type = 'table' AND name = ?", (index,)).fetchone()
        expected = f"SELECT id FROM {table} WHERE scope = ? {active}"
        indexed = f"SELECT rowid FROM {index}"
        if not exists or any(
            db.execute(f"SELECT 1 FROM ({left} EXCEPT {right}) LIMIT 1", (scope,)).fetchone()
            for left, right in ((expected, indexed), (indexed, expected))
        ):
            raise MemoryFailure("E_INDEX", failure)
    if layout >= 4:
        if action == "rebuild-index":
            _rebuild_cues(db)
        elif not db.execute("SELECT 1 FROM sqlite_master WHERE name = 'cues' AND type = 'table'").fetchone() or db.execute(
            "SELECT 1 FROM entries e WHERE (e.state = 'active') != "
            "EXISTS (SELECT 1 FROM cues c WHERE c.entry_id = e.id AND c.scope = e.scope) LIMIT 1"
        ).fetchone():
            raise MemoryFailure("E_INDEX", failure)
    return {"state": "ready", "revision": revision, "action": action, "fts5": True}


def doctor(action: str) -> dict:
    path = _database()
    if not path.is_file():
        with closing(sqlite3.connect(":memory:")) as db:
            _require_fts(db)
        return {"state": "uninitialized", "revision": 0, "action": action, "fts5": True}
    try:
        if action == "check":
            with _connect(path) as db, db:
                db.execute("BEGIN")
                return _diagnose(db, action)
        # Opening read-write lets SQLite recover a hot rollback journal.
        with _write(path, upgrade=False) as db:
            return _diagnose(db, action)
    except sqlite3.OperationalError as exc:
        if getattr(exc, "sqlite_errorcode", None) == sqlite3.SQLITE_READONLY_ROLLBACK:
            raise MemoryFailure("E_RECOVERY", "A rollback journal needs recovery. Run doctor --recover.") from None
        raise


def _project(db: sqlite3.Connection, root: Path, *, exact: bool = False) -> str | None:
    roots = [os.path.normcase(str(p)) for p in ((root,) if exact else (root, *root.parents))]
    placeholders = ",".join("?" for _ in roots)
    row = db.execute(
        f"SELECT id FROM scopes WHERE root IN ({placeholders}) ORDER BY length(root) DESC LIMIT 1",
        roots,
    ).fetchone()
    return row["id"] if row else None


def _register_project(db: sqlite3.Connection, root: Path) -> str:
    scope = f"project:{uuid4().hex}"
    db.execute("INSERT INTO scopes VALUES (?, ?)", (scope, os.path.normcase(str(root))))
    return scope


def _note(path: Path) -> str:
    name = path.name.lower()
    if name in {"credentials.toml", ".env"} or name.startswith(".env."):
        raise MemoryFailure("E_FORMAT", "Credential files cannot be saved as memory.")
    with _source_file(path) as stream:
        raw = stream.read(BODY_LIMIT + 1)
    if len(raw) > BODY_LIMIT:
        raise MemoryFailure("E_FORMAT", "Note must not exceed 8192 UTF-8 bytes.")
    text = unicodedata.normalize("NFC", raw.decode("utf-8").replace("\r\n", "\n").replace("\r", "\n"))
    if not text.strip() or "\x00" in text or len(text.encode("utf-8")) > BODY_LIMIT:
        raise MemoryFailure("E_FORMAT", "Choose a nonempty UTF-8 text note of at most 8192 bytes.")
    if PRIVATE_KEY.search(text):
        raise MemoryFailure("E_FORMAT", "Detected private key material. Remove it before saving.")
    return text


def _relation_specs(relations):
    if len(relations) > 24:
        raise MemoryFailure("E_LIMIT", "Declare at most 24 relations per note.")
    for spec in relations:
        kind, _, target = spec.partition(":")
        key, _, version = target.partition("@")
        if kind not in RELATIONS or not KEY.fullmatch(key) or not VERSION.fullmatch(version):
            raise MemoryFailure("E_FORMAT", "Use --relate TYPE:KEY@VERSION from the same scope.")
        yield kind, key, version


def remember(root: Path, scope: str, key: str, source: Path, base_version: str | None = None,
             relations=()) -> dict:
    _key(key)
    edges = tuple(_relation_specs(relations))
    stale = "The active version changed or is absent. Run review before editing."
    if base_version is not None:
        _check_version(base_version)
    body = _note(source)
    digest = sha256(body.encode("utf-8")).hexdigest()
    path = _database()
    if base_version is not None and not path.is_file():
        raise MemoryFailure("E_PLAN_STALE", stale)
    if edges and not path.is_file():
        raise _not_found()
    with _write(path, create=base_version is None) as db:
        scope_id = _scope_id(db, root, scope)
        if scope_id is None:
            if base_version is not None:
                raise MemoryFailure("E_PLAN_STALE", stale)
            scope_id = _register_project(db, root)
        current = _active(db, scope_id, key)
        if base_version is None:
            if db.execute(
                "SELECT 1 FROM entries WHERE scope = ? AND key = ? LIMIT 1", (scope_id, key)
            ).fetchone():
                raise MemoryFailure("E_EXISTS", "That key already exists in this scope.")
            for scope_to_index in {"global", scope_id}:
                _ensure_index(db, scope_to_index)
        elif current is None or current["version"] != base_version:
            raise MemoryFailure("E_PLAN_STALE", stale)
        destinations = []
        for kind, other_key, other_version in edges:
            other = _active(db, scope_id, other_key)
            if other_key == key or other is None or other["version"] != other_version:
                raise MemoryFailure("E_NOT_FOUND", "Link to a different active version in this scope. Run review.")
            destinations.append((other["id"], kind))
        db.execute(
            "INSERT INTO payloads VALUES (?, ?, ?) ON CONFLICT(scope, version) DO NOTHING",
            (scope_id, digest, body),
        )
        db.execute(
            "INSERT INTO entries (scope, key, version, source, state) "
            "VALUES (?, ?, ?, ?, 'pending') ON CONFLICT(scope, key, version) DO NOTHING",
            (scope_id, key, digest, source.name),
        )
        target = _version_row(db, scope_id, key, digest)
        origin = db.execute(
            "INSERT INTO origins(entry_id, source) VALUES (?, ?) ON CONFLICT DO NOTHING",
            (target["id"], source.name),
        ).rowcount
        changes = db.total_changes
        db.executemany(
            "INSERT INTO relations VALUES (?, ?, ?, 'declared', ?, 1) "
            "ON CONFLICT DO UPDATE SET approved = 1 WHERE approved = 0",
            ((target["id"], dst, kind, source.name) for dst, kind in destinations),
        )
        changed = bool(origin or db.total_changes != changes)
        _activate(db, target, current)
        if changed and current is not None and current["id"] == target["id"]:
            _bump_revision(db)
        return _version_ref(target)
