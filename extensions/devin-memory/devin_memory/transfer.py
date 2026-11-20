"""Versioned, explicitly scoped memory exchange."""

from contextlib import closing
import ctypes
from hashlib import sha256
from hmac import compare_digest
from itertools import chain
import json
import os
from pathlib import Path
import sqlite3
import stat
from tempfile import gettempdir, mkstemp
import unicodedata
from uuid import uuid4

from . import legacy, merge, store

if os.name == "nt":
    from ctypes import wintypes
    import msvcrt


FORMAT = "devin-memory"
SCHEMA_VERSION = 1
MAX_BYTES = 64 * 1024 * 1024
MAX_RECORDS = 100_000
MAX_LINE = 16 * 1024


def _canonical(record: dict) -> bytes:
    return json.dumps(
        record, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False,
    ).encode("utf-8")


def _header(scopes):
    return {"type": "header", "format": FORMAT, "schema_version": SCHEMA_VERSION, "scopes": scopes}


def _normalized(body):
    return unicodedata.normalize("NFC", body.replace("\r\n", "\n").replace("\r", "\n"))


def _wire_version(body):
    return sha256(_canonical({"body": body})).hexdigest()


def _record(kind, row):
    body, key = row["body"], row["key"]
    if not isinstance(body, str) or "\x00" in body or not body.strip():
        raise store.MemoryFailure("E_STORE", "A stored note does not contain valid text.")
    if not isinstance(key, str) or not store.KEY.fullmatch(key):
        raise store.MemoryFailure("E_STORE", "A stored note has an invalid key.")
    body = _normalized(body)
    if len(body.encode("utf-8")) > store.BODY_LIMIT:
        raise store.MemoryFailure("E_LIMIT", "A note exceeds the export body limit.")
    if store.PRIVATE_KEY.search(body):
        raise store.MemoryFailure("E_FORMAT", "Detected private key material. Export refused.")
    # Wire hashes cover the canonical payload, without changing local version IDs.
    record = {
        "type": kind, "scope": row["scope"], "key": key,
        "sha256": _wire_version(body),
    }
    if kind == "memory":
        record.update(payload={"body": body}, state=row["state"])
    elif kind == "edge":
        record.update(target_key=row["target_key"], target_sha256=_wire_version(_normalized(row["target_body"])),
                      relation=row["kind"], evidence=row["evidence"], source=row["origin"])
    else:
        if not isinstance(row["source"], str):
            raise store.MemoryFailure("E_STORE", "A stored note has invalid provenance.")
        record.update(store._origin(row["source"], row["legacy"]))
    return record


def _write_package(stream, scopes, revision, records) -> dict:
    digest = sha256()
    size = count = 0
    counts = {"memory": 0, "origin": 0, "edge": 0}

    def write(record, *, hashed=True):
        nonlocal size, count
        line = _canonical(record) + b"\n"
        if len(line) > MAX_LINE or size + len(line) > MAX_BYTES or count == MAX_RECORDS:
            raise store.MemoryFailure("E_LIMIT", "Export exceeds JSONL v1 size or record limits.")
        stream.write(line)
        size += len(line)
        count += 1
        if hashed:
            digest.update(line)

    write(_header(scopes))
    for kind, row in records:
        write(_record(kind, row))
        counts[kind] += 1
    checksum = digest.hexdigest()
    write({"type": "footer", "sha256": checksum}, hashed=False)
    return {
        "scopes": list(scopes), "revision": revision, "counts": counts,
        "bytes": size, "sha256": checksum,
        "warning": "Export is plaintext. Keep the package in a trusted location.",
    }


def _destination(dst: Path) -> Path:
    path = dst.absolute()
    if path.anchor.startswith(("\\\\", "//")) or ".." in path.parts or path == path.parent:
        raise store.MemoryFailure("E_IO", "Choose a local output file without path traversal.")
    if os.name == "nt" and any(
        ":" in part or part.endswith((".", " ")) for part in path.parts[1:]
    ):
        raise store.MemoryFailure("E_IO", "Choose a regular Windows filename.")
    for parent in reversed(path.parents):
        if not store._regular(parent, stat.S_IFDIR):
            raise store.MemoryFailure("E_IO", "The output directory must already exist.")
    if (path.parent.resolve() / path.name).is_relative_to(store.state_directory().resolve()):
        raise store.MemoryFailure("E_IO", "Choose an output outside the managed memory directory.")
    try:
        path.lstat()
    except FileNotFoundError:
        return path
    raise store.MemoryFailure("E_EXISTS", "The output already exists. Choose a new --out path.")


def _windows_stage(parent: Path):
    # Python 3.11 file modes cannot set a Windows DACL at creation.
    class SecurityAttributes(ctypes.Structure):
        _fields_ = [
            ("length", wintypes.DWORD), ("descriptor", ctypes.c_void_p),
            ("inherit_handle", wintypes.BOOL),
        ]

    advapi = ctypes.WinDLL("advapi32", use_last_error=True)
    kernel = ctypes.WinDLL("kernel32", use_last_error=True)
    convert = advapi.ConvertStringSecurityDescriptorToSecurityDescriptorW
    convert.argtypes = [wintypes.LPCWSTR, wintypes.DWORD, ctypes.POINTER(ctypes.c_void_p), ctypes.c_void_p]
    convert.restype = wintypes.BOOL
    create = kernel.CreateFileW
    create.argtypes = [
        wintypes.LPCWSTR, wintypes.DWORD, wintypes.DWORD, ctypes.POINTER(SecurityAttributes),
        wintypes.DWORD, wintypes.DWORD, wintypes.HANDLE,
    ]
    create.restype = wintypes.HANDLE
    kernel.LocalFree.argtypes = [ctypes.c_void_p]
    kernel.LocalFree.restype = ctypes.c_void_p
    kernel.CloseHandle.argtypes = [wintypes.HANDLE]
    kernel.CloseHandle.restype = wintypes.BOOL
    path = parent / f".devin-memory-{uuid4().hex}.tmp"
    descriptor = ctypes.c_void_p()
    if not convert("D:P(A;;GA;;;OW)", 1, ctypes.byref(descriptor), None):
        raise ctypes.WinError(ctypes.get_last_error())
    try:
        attrs = SecurityAttributes(ctypes.sizeof(SecurityAttributes), descriptor, False)
        # GENERIC_WRITE, no sharing, CREATE_NEW, FILE_ATTRIBUTE_NORMAL.
        handle = create(str(path), 0x40000000, 0, ctypes.byref(attrs), 1, 0x80, None)
        if handle == ctypes.c_void_p(-1).value:
            raise ctypes.WinError(ctypes.get_last_error())
        try:
            return msvcrt.open_osfhandle(handle, os.O_WRONLY | os.O_BINARY), path
        except OSError:
            kernel.CloseHandle(handle)
            path.unlink(missing_ok=True)
            raise
    finally:
        kernel.LocalFree(descriptor)


def _stage(parent: Path):
    if os.name == "nt":
        return _windows_stage(parent)
    fd, name = mkstemp(prefix=".devin-memory-", suffix=".tmp", dir=parent)
    return fd, Path(name)


def export(root: Path, scopes: list[str], dst: Path) -> dict:
    dst = _destination(dst)
    fd, stage = _stage(dst.parent)
    published = False
    try:
        with os.fdopen(fd, "wb") as stream:
            with store.snapshot(root, scopes) as snapshot:
                receipt = _write_package(stream, *snapshot)
            stream.flush()
            os.fsync(stream.fileno())
        _destination(dst)
        try:
            os.link(stage, dst)
        except FileExistsError:
            raise store.MemoryFailure("E_EXISTS", "The output already exists. Choose a new --out path.") from None
        except OSError:
            raise store.MemoryFailure("E_IO", "The local filesystem cannot publish the export atomically.") from None
        published = True
    finally:
        try:
            stage.unlink(missing_ok=True)
        except OSError:
            if not published:
                raise store.MemoryFailure("E_IO", "A private staging file could not be removed.") from None
            receipt["warning"] += " A private staging copy could not be removed."
    return receipt


def _format(message="Invalid or unsupported JSONL v1 record."):
    return store.MemoryFailure("E_FORMAT", message)


def _object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise _format("Duplicate JSON field.")
        result[key] = value
    return result


def _constant(_):
    raise _format("Non-finite JSON number.")


def _fields(value, *names):
    if not isinstance(value, dict) or value.keys() != set(names):
        raise _format()


def _is_scope(value):
    return isinstance(value, str) and (value == "global" or store.PROJECT_ID.fullmatch(value))


def _is_digest(value):
    return isinstance(value, str) and store.VERSION.fullmatch(value)


def _legacy_origin(record):
    if "legacy" not in record:
        return ""
    metadata = record["legacy"]
    _fields(metadata, "title", "category", "status", "cues")

    def text(value, *, optional=False):
        return (isinstance(value, str) and (optional or value.strip())
                and value.isprintable() and unicodedata.is_normalized("NFC", value)
                and not store.PRIVATE_KEY.search(value))

    if (legacy.relative_path(record["source"]) != record["source"]
            or not text(metadata["title"], optional=True)
            or not all(text(metadata[name]) for name in ("category", "status"))
            or not isinstance(metadata["cues"], list)):
        raise _format("Invalid legacy origin metadata.")
    for cue in metadata["cues"]:
        if not isinstance(cue, dict) or len(cue) != 1 or any(
            kind not in legacy.CUES or not text(value) for kind, value in cue.items()
        ):
            raise _format("Invalid legacy origin cue.")
    return _canonical(metadata).decode("utf-8")


def _stage_record(db, record, scopes):
    kind = record.get("type")
    if kind == "memory":
        _fields(record, "type", "scope", "key", "sha256", "payload", "state")
    elif kind == "origin":
        optional = ("legacy",) if "legacy" in record else ()
        _fields(record, "type", "scope", "key", "sha256", "source", *optional)
    elif kind == "edge":
        _fields(record, "type", "scope", "key", "sha256", "target_key", "target_sha256",
                "relation", "evidence", "source")
    else:
        raise _format()
    scope, key, digest = record["scope"], record["key"], record["sha256"]
    if not _is_scope(scope) or scope not in scopes:
        raise _format("Record is outside the declared package scopes.")
    if not isinstance(key, str) or not store.KEY.fullmatch(key) or not _is_digest(digest):
        raise _format("Invalid record identity.")
    if kind == "memory":
        _fields(record["payload"], "body")
        body = record["payload"]["body"]
        if (not isinstance(body, str) or "\x00" in body or not body.strip()
                or record["state"] not in ("active", "pending", "archived", "superseded")):
            raise _format()
        body = _normalized(body)
        raw = body.encode("utf-8")
        if len(raw) > store.BODY_LIMIT:
            raise store.MemoryFailure("E_LIMIT", "An imported note exceeds the body limit.")
        if store.PRIVATE_KEY.search(body):
            raise _format("Detected private key material. Import refused.")
        if not compare_digest(digest, _wire_version(body)):
            raise _format("Payload checksum does not match.")
        db.execute("INSERT INTO memory VALUES (?, ?, ?, ?, ?)", (scope, key, digest, sha256(raw).hexdigest(), body))
    else:
        source = record["source"]
        if not isinstance(source, str) or not source or "\x00" in source or store.PRIVATE_KEY.search(source):
            raise _format("Invalid origin metadata.")
        source.encode("utf-8")
        if kind == "origin":
            db.execute("INSERT INTO origin VALUES (?, ?, ?, ?, ?)",
                       (scope, key, digest, source, _legacy_origin(record)))
        else:
            target_key, target_digest = record["target_key"], record["target_sha256"]
            relation, evidence = record["relation"], record["evidence"]
            if (not isinstance(target_key, str) or not store.KEY.fullmatch(target_key)
                    or not _is_digest(target_digest) or (key, digest) == (target_key, target_digest)
                    or relation not in store.RELATIONS or evidence not in store.EVIDENCE):
                raise _format("Invalid relation identity or evidence.")
            db.execute("INSERT INTO edge VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                       (scope, key, digest, target_key, target_digest, relation, evidence, source))


def _load_package(db, lines):
    db.executescript(
        "CREATE TABLE memory (scope TEXT, key TEXT, digest TEXT, version TEXT, body TEXT, "
        "PRIMARY KEY(scope, key, digest)) WITHOUT ROWID;"
        "CREATE TABLE origin (scope TEXT, key TEXT, digest TEXT, source TEXT, legacy TEXT, "
        "PRIMARY KEY(scope, key, digest, source, legacy)) WITHOUT ROWID;"
        "CREATE TABLE edge (scope TEXT, key TEXT, digest TEXT, target_key TEXT, target_digest TEXT, "
        "kind TEXT, evidence TEXT, source TEXT, "
        "PRIMARY KEY(scope, key, digest, target_key, target_digest, kind, evidence, source)) WITHOUT ROWID;"
    )
    checksum, size = sha256(), 0
    lines = iter(lines)
    for count, line in enumerate(lines, 1):
        size += len(line)
        if len(line) > MAX_LINE or size > MAX_BYTES or count > MAX_RECORDS:
            raise store.MemoryFailure("E_LIMIT", "Package exceeds JSONL v1 size or record limits.")
        if not line.endswith(b"\n") or b"\r" in line:
            raise _format("Use UTF-8 JSONL with LF line endings.")
        try:
            record = json.loads(line.decode("utf-8"), object_pairs_hook=_object, parse_constant=_constant)
        except (ValueError, RecursionError):
            raise _format() from None
        if not isinstance(record, dict):
            raise _format()
        kind = record.get("type")
        if count == 1:
            _fields(record, "type", "format", "schema_version", "scopes")
            scopes = record["scopes"]
            if (kind != "header" or record["format"] != FORMAT or type(record["schema_version"]) is not int
                    or record["schema_version"] != SCHEMA_VERSION or not isinstance(scopes, list)
                    or not scopes or not all(_is_scope(scope) for scope in scopes)
                    or len(set(scopes)) != len(scopes)):
                raise _format("Invalid package header.")
            scopes = set(scopes)
        elif kind == "footer":
            _fields(record, "type", "sha256")
            if (not _is_digest(record["sha256"]) or not compare_digest(record["sha256"], checksum.hexdigest())
                    or next(lines, None) is not None):
                raise _format("Package checksum or footer does not match.")
            for first, second in (("origin", "memory"), ("memory", "origin")):
                if db.execute(
                    f"SELECT 1 FROM {first} a WHERE NOT EXISTS (SELECT 1 FROM {second} b "
                    "WHERE b.scope = a.scope AND b.key = a.key AND b.digest = a.digest) LIMIT 1"
                ).fetchone():
                    raise _format("Package contains a missing or dangling origin.")
            if db.execute(
                "SELECT 1 FROM edge e LEFT JOIN memory a ON (a.scope, a.key, a.digest) = (e.scope, e.key, e.digest) "
                "LEFT JOIN memory b ON (b.scope, b.key, b.digest) = (e.scope, e.target_key, e.target_digest) "
                "WHERE a.key IS NULL OR b.key IS NULL LIMIT 1"
            ).fetchone():
                raise _format("Package relation refers to a missing version in its scope.")
            checksum.update(line)
            return scopes, checksum.hexdigest()
        else:
            try:
                _stage_record(db, record, scopes)
            except sqlite3.IntegrityError:
                raise _format("Duplicate record identity.") from None
        checksum.update(line)
    raise _format("Package must end with a checksum footer.")


def _scope_map(scopes, arguments):
    result = {}
    for argument in arguments:
        source, separator, target = argument.partition("=")
        if (not separator or source not in scopes or source in result
                or (source == "global" and target != "global")
                or (source != "global" and target != "project" and not store.PROJECT_ID.fullmatch(target))):
            raise store.MemoryFailure("E_SCOPE", "Map global to global and each project to a registered project.")
        result[source] = target
    if not result:
        raise store.MemoryFailure("E_SCOPE", "Supply at least one explicit scope mapping.")
    return result


def _ingest(root, load, apply, *, legacy_source=None):
    if apply is not None and not _is_digest(apply):
        raise _format("Use the 64-character plan ID from the preview.")
    temporary = Path(gettempdir()).resolve()
    if legacy_source is not None and temporary.is_relative_to(legacy_source):
        raise store.MemoryFailure("E_IO", "Choose a temporary directory outside the legacy source.")
    fd, stage = _stage(temporary)
    os.close(fd)
    result = None
    try:
        with closing(sqlite3.connect(stage)) as db, db:
            db.execute("PRAGMA journal_mode = OFF")
            digest, mapping = load(db)
        result = merge.run(root, stage, digest, mapping, apply, _stage, migrate=legacy_source is not None)
        return result
    finally:
        try:
            stage.unlink(missing_ok=True)
        except OSError:
            if result is None:
                raise
            warning = "A private staging copy could not be removed."
            result["warning"] = (result.get("warning", "") + " " + warning).strip()


def import_package(root: Path, source: Path, mappings: list[str], apply: str | None = None) -> dict:
    def load(db):
        with store._source_file(source) as stream:
            scopes, digest = _load_package(db, iter(lambda: stream.readline(MAX_LINE + 1), b""))
        return digest, _scope_map(scopes, mappings)

    return _ingest(root, load, apply)


def migrate(project: Path, source: Path | None, apply: str | None = None) -> dict:
    root, selected = legacy.directories(project, source)

    def load(db):
        fingerprints = sha256()

        def records():
            for relative, body, metadata, raw in legacy.notes(
                selected, max_entries=MAX_RECORDS, max_bytes=MAX_BYTES, max_file=MAX_LINE + 2 * store.BODY_LIMIT,
            ):
                fingerprints.update(_canonical({"path": relative, "sha256": raw}) + b"\n")
                payload = {"body": body}
                identity = {
                    "scope": legacy.SCOPE, "key": legacy.key(relative),
                    "sha256": sha256(_canonical(payload)).hexdigest(),
                }
                yield dict(identity, type="memory", payload=payload, state="pending")
                yield dict(identity, type="origin", source=relative, legacy=metadata)

        def lines():
            checksum = sha256()
            for record in chain((_header([legacy.SCOPE]),), records()):
                line = _canonical(record) + b"\n"
                checksum.update(line)
                yield line
            yield _canonical({"type": "footer", "sha256": checksum.hexdigest()}) + b"\n"

        _, wire = _load_package(db, lines())
        digest = sha256(_canonical({
            "source": os.path.normcase(str(selected)), "files": fingerprints.hexdigest(), "wire": wire,
        })).hexdigest()
        return digest, {legacy.SCOPE: "project"}

    return _ingest(root, load, apply, legacy_source=selected)
