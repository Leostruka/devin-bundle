"""Envelope contract v2 coverage guard (#593, hardened #601).

Every agent-facing wrapper listed in .devin/docs/CLI-CONTRACT.md must
emit api_version=2 plus meta.answered_by provenance on its JSON
responses. Each wrapper is probed in a real subprocess on a safe,
side-effect-free invocation; the parsed stdout must carry the markers.
Static text checks cannot see runtime breakage (e.g. a manifest that
parses but is not a dict), so this is the authoritative guard.

When adding a new wrapper, extend PROBES and the contract doc.
"""
import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
MANIFEST_VERSION = json.loads(
    (ROOT / "manifest.json").read_text(encoding="utf-8"))["version"]

# (wrapper path, argv that yields a JSON envelope without side effects,
#  expected answered_by.wrapper)
PROBES = [
    ("extensions/agent-reach/wrapper.py", [], "agent-reach"),
    ("extensions/voicebox/wrapper.py", [], "voicebox"),
    ("extensions/hyperframes/wrapper.py", [], "hyperframes"),
    ("extensions/gcal/wrapper.py", [], "gcal"),
    ("extensions/offsec-tools/wrapper.py", ["capabilities"], "offsec-tools"),
    ("extensions/rea-ops/wrapper.py", ["capabilities"], "rea-ops"),
    ("extensions/rz-ops/wrapper.py", ["capabilities"], "rz-ops"),
    ("extensions/stock-footage/fetch.py",
     ["search", "--query", "contract-probe"], "stock-footage"),
    ("extensions/blender-operator/wrapper.py", ["status"],
     "blender-operator"),
    ("extensions/comfyui-operator/wrapper.py", ["status"],
     "comfyui-operator"),
    ("extensions/laya-tools/laya_cli.py", ["--self-test"], "laya-tools"),
    # wave-5 utility CLIs (#604): SSRF-denied URL, missing-dep, missing
    # file, and binary-missing paths all emit JSON offline.
    ("extensions/scrape-tools/scrape.py",
     ["http://127.0.0.1/", "--css", "x"], "scrape-tools"),
    ("extensions/scrape-tools/parse.py",
     ["manifest.json", "--css", "x"], "scrape-tools"),
    ("extensions/scrape-tools/dom_elements.py",
     ["nonexistent.json"], "scrape-tools"),
    ("extensions/asr/bootstrap.py", ["--model", "bad!"], "asr"),
    ("extensions/asr/transcribe.py", ["manifest.json"], "asr"),
    # --envelope is opt-in: result envelope when index exists, stamped
    # missing-index JSON otherwise - deterministic contract either way.
    ("extensions/code-graph/query.py",
     [".", "files", "zzz-probe", "--envelope"], "code-graph"),
]

# Keys that could turn a probe into a real network call.
PROBE_ENV = {k: v for k, v in os.environ.items()
             if k not in ("PEXELS_API_KEY", "PIXABAY_API_KEY")}


def test_all_listed_wrappers_exist():
    missing = [w for w, _, _ in PROBES if not (ROOT / w).is_file()]
    assert not missing, f"wrapper paths missing: {missing}"


def test_wrappers_emit_api_version_and_provenance():
    """Static marker check - cheap smoke; the subprocess probes below
    are the authoritative runtime guard. Files that stamp via a shared
    helper (st_common.emit/_emit) don't carry the literals themselves."""
    markers = ('"api_version"', "'api_version'", "_bundle_version",
               "_stamp(", "st_common.emit(", "_emit(")
    for rel, _, _ in PROBES:
        text = (ROOT / rel).read_text(encoding="utf-8")
        assert any(m in text for m in markers), \
            f"{rel}: no contract v2 stamp site found"


@pytest.mark.parametrize("rel,argv,wrapper", PROBES,
                         ids=[w for _, _, w in PROBES])
def test_wrapper_emits_contract_v2(rel, argv, wrapper):
    proc = subprocess.run(
        [sys.executable, str(ROOT / rel)] + argv,
        capture_output=True, text=True, encoding="utf-8",
        errors="replace", timeout=90, env=PROBE_ENV, cwd=str(ROOT))
    payload = json.loads(proc.stdout)
    assert payload.get("api_version") == 2, \
        f"{wrapper}: api_version={payload.get('api_version')!r}"
    answered = payload.get("meta", {}).get("answered_by", {})
    assert answered.get("wrapper") == wrapper, \
        f"{wrapper}: answered_by.wrapper={answered.get('wrapper')!r}"
    assert answered.get("bundle") == MANIFEST_VERSION, \
        f"{wrapper}: answered_by.bundle={answered.get('bundle')!r} " \
        f"(manifest {MANIFEST_VERSION})"
