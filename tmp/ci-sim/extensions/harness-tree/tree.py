#!/usr/bin/env python3
"""tree.py - harness component-tree read/validate/diff/apply engine.

ComponentTree = ordered dict path -> utf-8 content. Semantics:
  - omitted-is-inherited: diffs list only changed paths
  - diff value None means "deleted"
CLI:
  tree.py snapshot <root> [--out FILE]
  tree.py validate <root>
  tree.py diff <a.json|root> <b.json|root>
  tree.py apply <base.json> <diff.json> [--out FILE]
"""
import hashlib
import json
import os
import sys

try:
    sys.stdout.reconfigure(encoding="utf-8")
except AttributeError:
    pass

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from specs import DEVIN, component_of, skipped  # noqa: E402
from pathlib import Path

_BUNDLE_VERSION_CACHE = None


def _bundle_version():
    """Nearest ancestor manifest.json with a "name" marker, else ""."""
    global _BUNDLE_VERSION_CACHE
    if _BUNDLE_VERSION_CACHE is not None:
        return _BUNDLE_VERSION_CACHE
    import json as _json
    for parent in Path(__file__).absolute().parents:
        manifest = parent / "manifest.json"
        if manifest.is_file():
            try:
                data = _json.loads(
                    manifest.read_text(encoding="utf-8"))
            except (OSError, ValueError):
                break
            if isinstance(data, dict) and data.get("name"):
                _BUNDLE_VERSION_CACHE = str(data.get("version") or "")
            else:
                _BUNDLE_VERSION_CACHE = ""
            return _BUNDLE_VERSION_CACHE
    _BUNDLE_VERSION_CACHE = ""
    return _BUNDLE_VERSION_CACHE


def _answered_by():
    return {"bundle": _bundle_version(), "wrapper": "harness-tree"}


def _stamp(payload):
    if not isinstance(payload, dict):
        return payload
    payload["api_version"] = 2
    if not isinstance(payload.get("meta"), dict):
        payload["meta"] = {}
    payload["meta"].setdefault("answered_by", _answered_by())
    return payload


def _dumps(payload, **kw):
    return json.dumps(_stamp(payload), **kw)


RESERVED = {
    "scripts/check-ai-signature.py",
    "scripts/install-ledger.py",
    "scripts/check-push-green.py",
    "scripts/stop-guard.py",
}


def _iter_files(root, spec):
    seen = set()
    for cid in sorted(spec.components):
        for p in spec.components[cid]:
            p = p.replace("\\", "/").rstrip("/")
            absp = os.path.join(root, p)
            if os.path.isfile(absp):
                if p not in seen:
                    seen.add(p)
                    yield p
            elif os.path.isdir(absp):
                for dirpath, dirnames, filenames in os.walk(absp):
                    dirnames[:] = [d for d in sorted(dirnames)
                                   if d not in spec.exclude_names]
                    for fn in sorted(filenames):
                        rel = os.path.relpath(os.path.join(dirpath, fn),
                                              root).replace("\\", "/")
                        if rel not in seen and not skipped(rel, spec):
                            seen.add(rel)
                            yield rel


def read(root, spec=DEVIN):
    """Read all in-spec files under root -> ordered dict."""
    tree = {}
    for rel in _iter_files(root, spec):
        try:
            with open(os.path.join(root, rel), encoding="utf-8") as fh:
                tree[rel] = fh.read()
        except (OSError, UnicodeDecodeError):
            continue
    return tree


def validate(root, spec=DEVIN):
    """Report in-spec files missing from root + out-of-spec paths that would
    collide. Returns list of problem strings (empty = clean)."""
    problems = []
    seen = set()
    for rel in _iter_files(root, spec):
        if rel in seen:
            problems.append(f"duplicate: {rel}")
        seen.add(rel)
        if component_of(spec, rel) is None:
            problems.append(f"outside-spec: {rel}")
    for cid in sorted(spec.components):
        for p in spec.components[cid]:
            if not os.path.exists(os.path.join(root, p)):
                problems.append(f"missing: {cid} -> {p}")
    return problems


def diff(a, b):
    """Diff a->b: {path: new_content or None}. Omitted = unchanged."""
    out = {}
    for path in a:
        if path not in b:
            out[path] = None
        elif a[path] != b[path]:
            out[path] = b[path]
    for path in b:
        if path not in a:
            out[path] = b[path]
    return out


def apply(base, delta, spec=DEVIN):
    """Apply diff to base tree. Refuses to mutate RESERVED paths."""
    out = dict(base)
    for path, content in delta.items():
        if path in RESERVED:
            raise ValueError(f"reserved path cannot be mutated: {path}")
        if component_of(spec, path) is None:
            raise ValueError(f"path outside spec: {path}")
        if content is None:
            out.pop(path, None)
        else:
            out[path] = content
    return out


def tree_hash(tree):
    h = hashlib.sha256()
    for path in sorted(tree):
        h.update(path.encode())
        h.update(b"\0")
        h.update(tree[path].encode("utf-8"))
        h.update(b"\0")
    return h.hexdigest()


def _load(arg, spec=DEVIN):
    if arg.endswith(".json") and os.path.isfile(arg):
        with open(arg, encoding="utf-8") as fh:
            return json.load(fh)
    return read(arg, spec)


def main(argv):
    if len(argv) < 2:
        print(__doc__.strip())
        return 2
    cmd = argv[1]
    if cmd == "snapshot" and len(argv) >= 3:
        tree = read(argv[2])
        out = argv[argv.index("--out") + 1] if "--out" in argv else None
        payload = _dumps(tree, indent=1, ensure_ascii=False,
                             sort_keys=True)
        if out:
            with open(out, "w", encoding="utf-8", newline="\n") as fh:
                fh.write(payload + "\n")
        else:
            print(payload)
        print(f"# {len(tree)} files sha={tree_hash(tree)[:12]}",
              file=sys.stderr)
        return 0
    if cmd == "validate" and len(argv) >= 3:
        problems = validate(argv[2])
        for p in problems:
            print(p)
        print(f"{'FAIL' if problems else 'OK'}: {len(problems)} problem(s)")
        return 1 if problems else 0
    if cmd == "diff" and len(argv) >= 4:
        d = diff(_load(argv[2]), _load(argv[3]))
        print(_dumps(d, indent=1, ensure_ascii=False, sort_keys=True))
        return 0
    if cmd == "apply" and len(argv) >= 4:
        base = _load(argv[2])
        with open(argv[3], encoding="utf-8") as fh:
            delta = json.load(fh)
        try:
            out_tree = apply(base, delta)
        except ValueError as exc:
            print(f"ERROR: {exc}", file=sys.stderr)
            return 1
        out = argv[argv.index("--out") + 1] if "--out" in argv else None
        payload = _dumps(out_tree, indent=1, ensure_ascii=False,
                             sort_keys=True)
        if out:
            with open(out, "w", encoding="utf-8", newline="\n") as fh:
                fh.write(payload + "\n")
        else:
            print(payload)
        return 0
    print(__doc__.strip())
    return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv))
