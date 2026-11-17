"""Regression: _dumps(list) must emit the v2 envelope wrap, not a bare list.

fold_store grep/list leaked raw lists (no api_version/answered_by) because
_stamp() returns non-dicts untouched. The fix wraps lists into
{"ok": True, "items": [...]} inside every _dumps copy. This guards the
shared envelope modules and the standalone trio copies.
"""
import importlib.util
import json
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]

MODULES = [
    "extensions/computer-use/cu_envelope.py",
    "extensions/media-tools/media_envelope.py",
    "extensions/ai-tools/ai_envelope.py",
    "extensions/laya-tools/laya_envelope.py",
    "extensions/image-forensics/forensics_envelope.py",
    "extensions/craft-bridge/craft_envelope.py",
    "extensions/asr/asr_envelope.py",
    "extensions/remotion-render/remotion_envelope.py",
    "extensions/design-intelligence/design_envelope.py",
    "extensions/diagram-tools/plantuml_renderer.py",
    "extensions/blender-operator/camera_blocking.py",
    "extensions/mesh-utils/meshops.py",
    "extensions/laya-compactor/compact.py",
    "extensions/ppisp-prep/photo_qc.py",
    "extensions/ppisp-prep/ppisp_runner.py",
    "extensions/code-graph/query.py",
    "extensions/code-graph/detect_changes.py",
    "extensions/harness-tree/ns.py",
    "extensions/harness-tree/tree.py",
    "extensions/api-bridge/bridge.py",
    "skills/context-hygiene/scripts/fold_store.py",
    "skills/grilling/scripts/start-server.py",
    "skills/grilling/scripts/stop-server.py",
]


def _load(path):
    spec = importlib.util.spec_from_file_location(path.stem, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


@pytest.mark.parametrize("rel", MODULES)
def test_dumps_wraps_lists(rel):
    mod = _load(ROOT / rel)
    dumped = json.loads(mod._dumps([{"a": 1}]))
    assert dumped["api_version"] == 2
    assert dumped["ok"] is True
    assert dumped["items"] == [{"a": 1}]
    assert "answered_by" in dumped["meta"]


@pytest.mark.parametrize("rel", MODULES)
def test_dumps_stamps_dicts(rel):
    mod = _load(ROOT / rel)
    dumped = json.loads(mod._dumps({"ok": True}))
    assert dumped["api_version"] == 2
    assert "answered_by" in dumped["meta"]


def test_bundle_envelope_stamp_does_not_mutate():
    """_stamp must copy — injecting api_version/meta into the caller's dict
    broke harness-tree tree_hash (AttributeError on int.encode())."""
    spec = importlib.util.spec_from_file_location(
        "bundle_envelope", ROOT / "scripts/bundle_envelope.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    _stamp, _dumps = mod.bind("probe")
    caller = {"ok": True}
    stamped = _stamp(caller)
    assert stamped["api_version"] == 2
    assert "api_version" not in caller
    dumped = json.loads(_dumps([1, 2]))
    assert dumped["items"] == [1, 2]
