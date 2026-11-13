"""check-tools.py - schema validation + byte-identity gate (M2_07)."""
import importlib.util
import json
import os
import sys
from unittest.mock import patch

SCRIPTS = os.path.join(os.path.dirname(__file__), "..", "scripts")
spec = importlib.util.spec_from_file_location(
    "check_tools", os.path.join(SCRIPTS, "check-tools.py"))
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)


def test_schema_valid_repo_tools_json():
    assert mod.validate_schema(mod._load()) == []


def test_schema_missing_tools():
    assert mod.validate_schema({}) == [
        "tools.json: missing non-empty 'tools' object"]


def test_schema_missing_keys_and_enabled_no_renderer():
    problems = mod.validate_schema({"tools": {
        "x": {"label": "X"},  # missing format/installKind/dest/enabled
        "y": {"label": "Y", "format": "f", "installKind": "roster",
              "dest": "d", "enabled": True}}})
    assert "x: missing 'format'" in problems
    assert "x: missing 'enabled'" in problems
    assert "y: enabled but no renderer" in problems


def test_byte_identity_deterministic(tmp_path):
    script = tmp_path / "r.py"
    script.write_text("import sys; print('stable')", encoding="utf-8")
    with patch.object(mod, "ROOT", str(tmp_path)):
        ok, detail = mod.check_byte_identity("r.py", None)
    assert ok and "identical" in detail


def test_byte_identity_catches_nondeterminism(tmp_path):
    script = tmp_path / "r.py"
    script.write_text(
        "import time; print(time.time_ns())", encoding="utf-8")
    with patch.object(mod, "ROOT", str(tmp_path)):
        ok, detail = mod.check_byte_identity("r.py", None)
    assert not ok and "diverge" in detail


def test_byte_identity_renderer_failure(tmp_path):
    script = tmp_path / "r.py"
    script.write_text("import sys; sys.exit(1)", encoding="utf-8")
    with patch.object(mod, "ROOT", str(tmp_path)):
        ok, detail = mod.check_byte_identity("r.py", None)
    assert not ok and "exit 1" in detail


def test_expand_dest_env():
    with patch.dict(os.environ, {"ZZDEST": "/tmp/x"}):
        assert mod._expand_dest("%ZZDEST%/devin") == "/tmp/x/devin"
        assert mod._expand_dest("$ZZDEST/y") == "/tmp/x/y"


def test_main_repo_check_passes():
    with patch.object(sys, "argv", ["check-tools.py"]):
        assert mod.main() == 0
