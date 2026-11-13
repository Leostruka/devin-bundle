"""Envelope contract v2 coverage guard (#593).

Every agent-facing wrapper listed in .devin/docs/CLI-CONTRACT.md must
carry the provenance markers. Static text check - fast, no imports.
When adding a new wrapper, extend WRAPPERS and the contract doc.
"""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

WRAPPERS = [
    "extensions/agent-reach/wrapper.py",
    "extensions/voicebox/wrapper.py",
    "extensions/hyperframes/wrapper.py",
    "extensions/gcal/wrapper.py",
    "extensions/offsec-tools/wrapper.py",
    "extensions/rea-ops/wrapper.py",
    "extensions/rz-ops/wrapper.py",
    "extensions/stock-footage/fetch.py",
    "extensions/blender-operator/wrapper.py",
    "extensions/comfyui-operator/wrapper.py",
    "extensions/laya-tools/laya_cli.py",
]


def test_all_listed_wrappers_exist():
    missing = [w for w in WRAPPERS if not (ROOT / w).is_file()]
    assert not missing, f"wrapper paths missing: {missing}"


def test_wrappers_emit_api_version_and_provenance():
    for w in WRAPPERS:
        text = (ROOT / w).read_text(encoding="utf-8")
        assert '"api_version"' in text or "'api_version'" in text, \
            f"{w}: missing api_version marker"
        assert "_bundle_version" in text, \
            f"{w}: missing _bundle_version provenance helper"
        assert "answered_by" in text, \
            f"{w}: missing meta.answered_by provenance"
