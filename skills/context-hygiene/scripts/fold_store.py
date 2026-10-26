"""Reversible fold store: persist folded context ranges for restore/search.

Inspired by billion-context's compress/decompress/search_context trio.
Instead of losing content to a one-way summary, the agent stores the folded
range with an id and a summary; the full text can be restored or grepped
later in the session (or a future one).

Store layout: .devin/scratch/folds/<fold_id>.json
    {id, summary, content, ts, tokens_est}

CLI:
    fold_store.py save <id> --summary "one line" --content-file f.txt | --content "..."
    fold_store.py unfold <id>            -> prints stored content
    fold_store.py grep <pattern>         -> folds matching id/summary/content
    fold_store.py list                   -> all folds (id, summary, size)
    fold_store.py delete <id>
"""

import json
import os
import sys
import time

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__),
                                    "..", "..", ".."))
STORE = os.environ.get(
    "FOLD_STORE_DIR", os.path.join(ROOT, ".devin", "scratch", "folds"))


def _path(fid):
    if "/" in fid or "\\" in fid or ".." in fid:
        raise ValueError("invalid fold id")
    return os.path.join(STORE, fid + ".json")


def _read(fid):
    with open(_path(fid), encoding="utf-8") as f:
        return json.load(f)


def save(fid, summary, content):
    os.makedirs(STORE, exist_ok=True)
    rec = {"id": fid, "summary": summary, "content": content,
           "ts": time.time(), "tokens_est": len(content) // 4}
    tmp = _path(fid) + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(rec, f)
    os.replace(tmp, _path(fid))
    return {"id": fid, "tokens_est": rec["tokens_est"]}


def unfold(fid):
    return _read(fid)["content"]


def grep(pattern):
    hits = []
    if not os.path.isdir(STORE):
        return hits
    import re
    rx = re.compile(re.escape(pattern), re.IGNORECASE)
    for name in sorted(os.listdir(STORE)):
        if not name.endswith(".json"):
            continue
        try:
            rec = _read(name[:-5])
        except (OSError, json.JSONDecodeError):
            continue
        blob = rec.get("id", "") + "\n" + rec.get("summary", "") + "\n" \
            + rec.get("content", "")
        if rx.search(blob):
            hits.append({k: rec.get(k) for k in ("id", "summary", "tokens_est")})
    return hits


def list_folds():
    if not os.path.isdir(STORE):
        return []
    out = []
    for name in sorted(os.listdir(STORE)):
        if name.endswith(".json"):
            try:
                rec = _read(name[:-5])
                out.append({k: rec.get(k)
                            for k in ("id", "summary", "tokens_est")})
            except (OSError, json.JSONDecodeError):
                continue
    return out


def delete(fid):
    os.remove(_path(fid))


def main():
    args = sys.argv[1:]
    if not args:
        print(__doc__)
        return 2
    cmd = args[0]
    if cmd == "save" and len(args) >= 2:
        fid = args[1]
        summary, content = "", ""
        i = 2
        while i < len(args):
            if args[i] == "--summary":
                summary = args[i + 1]; i += 2
            elif args[i] == "--content-file":
                with open(args[i + 1], encoding="utf-8",
                          errors="replace") as f:
                    content = f.read()
                i += 2
            elif args[i] == "--content":
                content = args[i + 1]; i += 2
            else:
                i += 1
        if not content:
            content = sys.stdin.read()
        print(json.dumps(save(fid, summary, content)))
        return 0
    if cmd == "unfold" and len(args) == 2:
        print(unfold(args[1]), end="")
        return 0
    if cmd == "grep" and len(args) == 2:
        print(json.dumps(grep(args[1]), indent=1))
        return 0
    if cmd == "list":
        print(json.dumps(list_folds(), indent=1))
        return 0
    if cmd == "delete" and len(args) == 2:
        delete(args[1])
        return 0
    print(__doc__, file=sys.stderr)
    return 2


if __name__ == "__main__":
    sys.exit(main())
