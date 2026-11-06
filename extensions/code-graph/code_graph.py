"""Shared code-graph core: schema, tokenizer, incremental index (stdlib).

DB: .devin/code-graph/index.db (gitignored). FTS5 over pre-split tokens so
camelCase/snake_case both resolve. Incremental = mtime+sha1 per file.
"""
import hashlib
import os
import re
import sqlite3

EXTS = {".py", ".ts", ".tsx", ".js", ".jsx", ".md", ".ps1", ".sh",
        ".rs", ".go", ".java", ".rb", ".c", ".cpp", ".h", ".cs"}
SKIP_DIRS = {".git", ".venv", "venv", "node_modules", "target",
             "__pycache__", "dist", "build", ".devin"}

PATTERNS = [
    ("py", re.compile(
        r"^\s*(?:async\s+def|def|class)\s+([A-Za-z_]\w*)")),
    ("js", re.compile(
        r"^\s*(?:export\s+)?(?:async\s+)?(?:function\*?\s+|class\s+|"
        r"(?:const|let|var)\s+)([A-Za-z_$][\w$]*)")),
    ("rs", re.compile(r"^\s*(?:pub\s+)?(?:fn|struct|enum|trait|impl)"
                      r"\s+([A-Za-z_]\w*)")),
    ("sh", re.compile(r"^\s*(?:function\s+)?([A-Za-z_]\w*)\s*\(\s*\)")),
    ("ps1", re.compile(r"^\s*function\s+([A-Za-z_][\w-]*)",
                       re.IGNORECASE)),
]
IMPORT_RE = re.compile(
    r"^\s*(?:from\s+([\w.]+)\s+import|import\s+([\w.]+)|"
    r"require\(['\"]([^'\"]+)|from\s+['\"]([^'\"]+))")

_SPLIT = re.compile(r"[A-Z]+(?![a-z])|[A-Z][a-z0-9]*|[a-z0-9]+")


def tokens(name):
    """camel/snake-split token stream for FTS content."""
    parts = _SPLIT.findall(name.replace("_", " ").replace("-", " "))
    return " ".join(dict.fromkeys([name] + [p.lower() for p in parts]))


def sha1(path):
    h = hashlib.sha1()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def iter_files(root):
    for dirpath, dirs, names in os.walk(root):
        dirs[:] = [d for d in dirs if d not in SKIP_DIRS]
        for n in names:
            if os.path.splitext(n)[1] in EXTS:
                yield os.path.join(dirpath, n)


def extract_symbols(path):
    """([(kind, name, line)], [import targets])."""
    ext = os.path.splitext(path)[1]
    kind_map = {".py": "py", ".ts": "js", ".tsx": "js", ".js": "js",
                ".jsx": "js", ".rs": "rs", ".sh": "sh", ".ps1": "ps1"}
    kind = kind_map.get(ext)
    pat = next((p for k, p in PATTERNS if k == kind), None)
    syms, imports = [], []
    try:
        with open(path, encoding="utf-8", errors="replace") as fh:
            for i, line in enumerate(fh, 1):
                if pat:
                    m = pat.match(line)
                    if m:
                        syms.append((kind, m.group(1), i))
                im = IMPORT_RE.match(line)
                if im:
                    imports.append(next(
                        g for g in im.groups() if g))
    except OSError:
        pass
    return syms, imports


def open_db(path):
    db = sqlite3.connect(path)
    db.executescript("""
        CREATE TABLE IF NOT EXISTS files(
            path TEXT PRIMARY KEY, mtime REAL, sha TEXT);
        CREATE TABLE IF NOT EXISTS symbols(
            file TEXT, kind TEXT, name TEXT, line INTEGER);
        CREATE TABLE IF NOT EXISTS edges(
            file TEXT, target TEXT);
        CREATE VIRTUAL TABLE IF NOT EXISTS fts USING fts5(
            name, file, content, tokenize='unicode61');
    """)
    return db


def index_file(db, root, path):
    rel = os.path.relpath(path, root).replace("\\", "/")
    st = os.stat(path)
    digest = sha1(path)
    row = db.execute(
        "SELECT mtime, sha FROM files WHERE path=?", (rel,)).fetchone()
    if row and row[0] == st.st_mtime and row[1] == digest:
        return False
    db.execute("DELETE FROM symbols WHERE file=?", (rel,))
    db.execute("DELETE FROM edges WHERE file=?", (rel,))
    db.execute("DELETE FROM fts WHERE file=?", (rel,))
    syms, imports = extract_symbols(path)
    for kind, name, line in syms:
        db.execute(
            "INSERT INTO symbols VALUES(?,?,?,?)", (rel, kind, name, line))
        db.execute("INSERT INTO fts(name, file, content) VALUES(?,?,?)",
                   (name, rel, tokens(name)))
    for target in imports:
        db.execute("INSERT INTO edges VALUES(?,?)", (rel, target))
    db.execute("INSERT OR REPLACE INTO files VALUES(?,?,?)",
               (rel, st.st_mtime, digest))
    return True
