"""Wave-9: stamp envelope v2 on the remaining extension emitters +
scripts/graph-query.py. Same trio + _dumps funnel.
"""
import ast
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

FILES = [
    "extensions/laya-compactor/compact.py",
    "extensions/ppisp-prep/photo_qc.py",
    "extensions/ppisp-prep/ppisp_runner.py",
    "extensions/mesh-utils/meshops.py",
    "extensions/api-bridge/bridge.py",
    "extensions/diagram-tools/plantuml_renderer.py",
    "extensions/craft-bridge/bridge.py",
    "extensions/craft-bridge/scene_manifest.py",
    "extensions/harness-tree/ns.py",
    "extensions/harness-tree/tree.py",
    "scripts/graph-query.py",
]

TRIO = '''
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
    return {"bundle": _bundle_version(), "wrapper": "WRAPPER"}


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

'''


def insert_trio(text, wrapper):
    tree = ast.parse(text)
    last_imp_end = 0
    doc_end = 0
    for node in tree.body:
        if isinstance(node, (ast.Import, ast.ImportFrom)):
            last_imp_end = max(last_imp_end, node.end_lineno)
        elif isinstance(node, ast.Expr) and isinstance(
                node.value, ast.Constant) and isinstance(
                node.value.value, str) and node.lineno <= 3:
            doc_end = node.end_lineno
    ins = last_imp_end or doc_end or (
        2 if text.startswith("#!") else 1)
    lines = text.split("\n")
    block = []
    if "from pathlib import" not in text:
        block.append("from pathlib import Path")
    block.append(TRIO.replace("WRAPPER", wrapper).rstrip("\n"))
    lines.insert(ins, "\n".join(block) + "\n")
    return "\n".join(lines)


for rel in FILES:
    p = ROOT / rel
    # wrapper name = extension dir, or the tool name for scripts/
    wrapper = (rel.split("/")[1] if rel.startswith("extensions/")
           else Path(rel).stem)
    text = p.read_text(encoding="utf-8")
    if "_BUNDLE_VERSION_CACHE" in text:
        print(f"{rel}: already stamped, skipping")
        continue
    n = len(re.findall(r"print\(json\.dumps\(", text))
    text = text.replace("print(json.dumps(", "print(_dumps(")
    text = insert_trio(text, wrapper)
    p.write_text(text, encoding="utf-8")
    print(f"{rel}: {n} emit sites stamped (wrapper={wrapper})")
