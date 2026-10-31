import json
import re
import runpy
import shlex
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]


def text(path):
    return (ROOT / path).read_text(encoding="utf-8")


def test_goldfish_requires_zoom_out_and_no_history():
    protocol = text(".devin/sdd/goldfish-review.md")
    assert "1. **zoom-out**" in protocol
    assert "originating chat history" in protocol
    assert "including any appendix" in protocol
    for path in ("agents/reviewer.md", ".devin/agents/repo-reviewer.md"):
        profile = text(path).split("## Goldfish Review protocol (EGM)", 1)[1]
        assert "spec.md" in profile
        assert "zoom-out" in profile
        assert ".devin/sdd/goldfish-review.md" in profile


def test_drift_audit_reuses_existing_skill():
    protocol = text(".devin/sdd/goldfish-review.md")
    assert "skills/drift-report/SKILL.md" in protocol
    assert (ROOT / "skills/drift-report/SKILL.md").is_file()
    assert "No standalone command" in protocol


@pytest.mark.parametrize("path", [
    "extensions/blender-operator/ROADMAP.md",
    "extensions/media-tools/ROADMAP.md",
    ".devin/scratch/egm-laya-bitnet-upgrade/issues/03-katana-camera-blocking.md",
])
def test_camera_addenda_reference_existing_owner(path):
    owner = ".devin/issues/MILESTONE_2_13_camera_blocking.md"
    assert owner in text(path)
    assert (ROOT / owner).is_file()


def test_openui_example_has_balanced_blocks_and_parseable_attributes():
    doc = text(".devin/rts/openui-lang.md")
    example = re.search(r"```\n(.*?)\n```", doc, re.S).group(1)
    stack = []
    for line in example.splitlines():
        parts = shlex.split(line, comments=True)
        if not parts:
            continue
        if parts[0] in ("hud", "form"):
            stack.append(parts[0])
        if parts[0] == "end":
            assert stack, "end without an open block"
            stack.pop()
        for part in parts[1:]:
            if part in ("choice", "multi"):
                continue
            assert "=" in part, part
    assert not stack, f"unclosed blocks: {stack}"
    sys.path.insert(0, str(ROOT / "extensions" / "craft-bridge"))
    import ui_dsl
    parsed = ui_dsl.parse(example)
    assert len(parsed.blocks) == len(
        [b for b in parsed.blocks if b.type in ("hud", "form")]) >= 1


def test_laya_rollout_is_distinct_from_current_runtime():
    doc = text(".devin/research/LAYA_MASTER_ARCHITECTURE.md").split("## 12.", 1)[1]
    assert "0.25" in doc and "0.70" in doc
    assert "batch_size=8" not in doc
    spec = runpy.run_path(str(ROOT / "scripts/compact-gate.py"))
    defaults = spec["DEFAULTS"]
    assert defaults["eval_floor"] == 0.25
    assert defaults["compact_at"] == 0.70
    assert defaults["force_at"] == 0.80
    assert defaults["compact_to"] == 0.40
    profile = json.loads(text(".devin/laya/profile.json"))
    assert profile["compact_gate"]["eval_floor"] == 0.25


def test_manifest_documents_security_guard_exception():
    hooks = json.loads(text("hooks.v1.json"))
    guards = [hook for entry in hooks["PreToolUse"]
              for hook in entry["hooks"]
              if "pre-exec-guard.py" in hook["command"]
              or "pre-write-guard.py" in hook["command"]]
    assert len(guards) == 2
    assert all(hook["fail_closed"] is True for hook in guards)
    manifest = text(".devin/ARCHITECTURE_MANIFEST.md")
    assert "fail_closed: true" in manifest
    assert "pre-exec-guard.py" in manifest
    assert "pre-write-guard.py" in manifest


def test_spec_separates_documentation_from_runtime_acceptance():
    spec = text(".devin/scratch/egm-laya-bitnet-upgrade/spec.md")
    assert "## Runtime acceptance" in spec
    for artifact in (
        "scripts/skill-picker.py",
        "extensions/laya-tools/review_gate.py",
        "extensions/laya-tools/doc_coverage.py",
        "extensions/laya-tools/explore.py",
        "extensions/computer-use/cu_dom_picker.py",
        "extensions/craft-bridge/ui_dsl.py",
    ):
        assert (ROOT / artifact).is_file(), artifact


@pytest.mark.parametrize("target, category, name", [
    ("agents/chief-of-staff.md", "agents", "chief-of-staff"),
    ("scripts/pre-exec-guard.py", "scripts", "pre-exec-guard.py"),
])
@pytest.mark.parametrize("newline", ["lf", "crlf"])
@pytest.mark.parametrize("writer_newline", ["lf", "crlf"])
@pytest.mark.parametrize("changed", [False, True])
def test_audit_hash_survives_newlines_not_content(
        target, category, name, newline, writer_newline, changed):
    script = '''
import builtins
import hashlib
import io
import json
import os
import runpy
import sys
from unittest.mock import patch
real_open = builtins.open
target, category, name, checkout, writer, mutation = sys.argv[1:]
with real_open(target, "rb") as source:
    canonical = source.read().replace(b"\\r\\n", b"\\n")
exported = canonical.replace(b"\\n", b"\\r\\n") if writer == "crlf" else canonical
expected = hashlib.sha256(exported).hexdigest().upper()

def checkout_open(path, mode="r", *args, **kwargs):
    normalized = os.path.normpath(str(path))
    if mode == "rb" and normalized == os.path.normpath(target):
        data = canonical.replace(b"\\n", b"\\r\\n") if checkout == "crlf" else canonical
        if mutation == "changed":
            data += b"\\nchanged = True\\n"
        return io.BytesIO(data)
    if normalized == "manifest.json" and mode == "r":
        with real_open(path, mode, *args, **kwargs) as source:
            manifest = json.load(source)
        entry = next(item for item in manifest[category] if item["name"] == name)
        entry["export_hash"] = expected
        return io.StringIO(json.dumps(manifest))
    return real_open(path, mode, *args, **kwargs)

with patch("builtins.open", checkout_open):
    runpy.run_path("audit.py", run_name="__main__")
'''
    result = subprocess.run([sys.executable, "-c", script, target, category,
                             name, newline, writer_newline,
                             "changed" if changed else "same"], cwd=ROOT,
                            capture_output=True, text=True, timeout=90)
    assert result.returncode == 0, result.stderr
    assert "Errors:   0" in result.stdout
    warning = "manifest agent hash mismatch" if category == "agents" else "manifest script hash mismatch"
    assert (warning in result.stdout) is changed
