"""Read the legacy Markdown note format without following links or writing notes."""

from hashlib import sha256
from itertools import islice
import json
import os
from pathlib import Path, PurePosixPath
import re
import stat
import unicodedata

from . import store


SCOPE = "project:" + "0" * 32  # Internal source label; the destination assigns its own ID.
FIELDS = frozenset(("title", "date", "session", "category", "tags", "status", "cues"))
CUES = frozenset(("keyword", "path", "symbol"))
TAG_LIST = re.compile(r"\[\s*[\w.-]+(?:\s*,\s*[\w.-]+)*\s*\]")


def relative_path(value: str) -> str:
    path = PurePosixPath(unicodedata.normalize("NFC", value))
    if (path.is_absolute() or not value.isprintable() or "\\" in value or ":" in value
            or ".." in path.parts or path.suffix.lower() != ".md"):
        raise store.MemoryFailure("E_FORMAT", "Choose a relative Markdown path inside the legacy source.")
    return path.as_posix()


def key(value: str) -> str:
    return "legacy-" + sha256(relative_path(value).encode("utf-8")).hexdigest()


def directories(project: Path, source: Path | None) -> tuple[Path, Path]:
    root = store._local_directory(project).resolve(strict=True)
    directory = store._local_directory(source if source is not None else root / ".devin" / "memory")
    state = store.state_directory().resolve()
    selected = directory.resolve(strict=True)
    if state.is_relative_to(selected) or selected.is_relative_to(state):
        raise store.MemoryFailure("E_IO", "Keep the legacy source separate from the managed memory directory.")
    return root, directory


def _error(note, line, expected):
    return store.MemoryFailure("E_FORMAT", f"Legacy note {note}, line {line}: {expected}.")


def _scalar(raw, note, line):
    value = raw.strip()
    if value.startswith('"'):
        try:
            value = json.loads(value)
        except ValueError:
            raise _error(note, line, "invalid quoted frontmatter value") from None
    elif re.fullmatch(r"'(?:[^']|'')*'", value):
        value = value[1:-1].replace("''", "'")
    elif not value or value[0] in "'[{&*!|>@`%#" or re.search(r":(?:\s|$)|\s#", value):
        raise _error(note, line, "expected a plain or quoted frontmatter value")
    if not isinstance(value, str) or not value.isprintable():
        raise _error(note, line, "expected printable frontmatter text")
    return unicodedata.normalize("NFC", value)


def _parse(data: bytes, note: int):
    try:
        text = data.decode("utf-8").removeprefix("\ufeff").replace("\r\n", "\n").replace("\r", "\n")
    except UnicodeError as exc:
        line = data[:exc.start].replace(b"\r\n", b"\n").replace(b"\r", b"\n").count(b"\n") + 1
        raise _error(note, line, "expected valid UTF-8") from None
    lines = text.split("\n")
    if lines[0] != "---":
        raise _error(note, 1, "expected Markdown frontmatter starting with ---")
    try:
        end = lines.index("---", 1)
    except ValueError:
        raise _error(note, 1, "frontmatter is missing its closing ---") from None
    values = {}
    collection = indentation = None
    for index, line in enumerate(lines[1:end], 2):
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        item = re.fullmatch(r"( *)- +(.*)", line)
        if item:
            if collection is None or indentation not in (None, item[1]):
                raise _error(note, index, "unexpected frontmatter list item")
            indentation = item[1]
            raw = item[2]
            if collection == "cues":
                kind, separator, raw = raw.partition(":")
                if not separator or kind not in CUES:
                    raise _error(note, index, "expected a keyword, path or symbol cue")
                cue = _scalar(raw, note, index)
                if not cue.strip():
                    raise _error(note, index, "expected a nonempty cue")
                values[collection].append({kind: cue})
            else:
                _scalar(raw, note, index)
            continue
        field, separator, raw = line.partition(":")
        if not separator or field not in FIELDS or field in values:
            raise _error(note, index, "unknown, duplicate or malformed frontmatter field")
        collection = indentation = None
        if field in ("cues", "tags"):
            value = raw.strip()
            if value not in ("", "[]") and not (field == "tags" and TAG_LIST.fullmatch(value)):
                raise _error(note, index, f"expected a {field} list or []")
            values[field] = []
            if not raw.strip():
                collection = field
        else:
            values[field] = _scalar(raw, note, index)
    for field in ("category", "status"):
        if not values.get(field, "").strip():
            raise _error(note, end + 1, f"missing {field}")
    for index, line in enumerate(lines, 1):
        if "\x00" in line or store.PRIVATE_KEY.search(line):
            raise _error(note, index, "unsupported content in legacy note")
    body = unicodedata.normalize("NFC", "\n".join(lines[end + 1:]))
    if not body.strip():
        raise _error(note, end + 2, "expected a nonempty note body")
    return body, {
        "category": values["category"], "status": values["status"],
        "title": values.get("title", ""), "cues": values.get("cues", []),
    }


def _paths(directory: Path, limit: int):
    pending = [directory]
    while pending:
        parent = store._local_directory(pending.pop())
        with os.scandir(parent) as entries:
            children = sorted(islice(entries, limit + 1), key=lambda entry: entry.name)
        limit -= len(children)
        if limit < 0:
            raise store.MemoryFailure("E_LIMIT", "Legacy source contains too many directory entries.")
        for entry in children:
            path = Path(entry.path)
            info = entry.stat(follow_symlinks=False)
            mode = stat.S_IFMT(info.st_mode)
            if (mode not in (stat.S_IFDIR, stat.S_IFREG)
                    or getattr(info, "st_file_attributes", 0) & stat.FILE_ATTRIBUTE_REPARSE_POINT):
                raise store.MemoryFailure("E_IO", "Legacy source contains a link or unsupported file type.")
            if mode == stat.S_IFDIR:
                pending.append(path)
            elif path.suffix.lower() == ".md" and path.name.lower() != "moc.md":
                yield path


def notes(directory: Path, *, max_entries: int, max_bytes: int, max_file: int):
    seen = set()
    size = 0
    for index, path in enumerate(_paths(directory, max_entries), 1):
        relative = relative_path(path.relative_to(directory).as_posix())
        if relative in seen:
            raise _error(index, 1, "relative path collides after normalization")
        seen.add(relative)
        with store._source_file(path) as stream:
            data = stream.read(max_file + 1)
        size += len(data)
        if len(data) > max_file or size > max_bytes:
            raise store.MemoryFailure("E_LIMIT", f"Legacy note {index} exceeds the migration byte limits.")
        body, metadata = _parse(data, index)
        yield relative, body, metadata, sha256(data).hexdigest()
    if not seen:
        raise store.MemoryFailure("E_NOT_FOUND", "The selected source has no legacy Markdown notes.")
