"""token-saver.py - UserPromptSubmit: inject output-mode preset on change only."""
import importlib.util
import io
import json
import os
import sys
from unittest.mock import patch

import pytest

SCRIPTS = os.path.join(os.path.dirname(__file__), "..", "scripts")
spec = importlib.util.spec_from_file_location(
    "token_saver", os.path.join(SCRIPTS, "token-saver.py"))
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)


def _run(payload=None, root=None):
    out = io.StringIO()
    env = {"DEVIN_PROJECT_DIR": root} if root else {}
    with patch.object(sys, "stdin",
                      io.StringIO(json.dumps(payload or {}))), \
         patch.object(sys, "stdout", out), \
         patch.dict(os.environ, env), \
         pytest.raises(SystemExit) as e:
        mod.main()
    return e.value.code, out.getvalue()


@pytest.fixture()
def root(tmp_path, monkeypatch):
    (tmp_path / "data").mkdir()
    presets = {
        "caveman": {"context": "CAVEMAN fragment", "flags": {"diff_footer": True}},
        "quiet": {"context": "QUIET fragment", "flags": {"diff_footer": False}},
    }
    (tmp_path / "data" / "output-modes.json").write_text(json.dumps(presets), encoding="utf-8")
    (tmp_path / ".devin").mkdir()
    return tmp_path


def test_no_mode_file_silent(root):
    code, out = _run(root=str(root))
    assert code == 0 and out == ""


def test_injects_once_then_silent(root):
    (root / ".devin" / "output-mode.json").write_text(
        json.dumps({"mode": "caveman"}), encoding="utf-8")
    code, out = _run(root=str(root))
    assert code == 0 and "CAVEMAN fragment" in out
    # second call with unchanged mode: nothing injected (the savings)
    code, out = _run(root=str(root))
    assert code == 0 and out == ""


def test_mode_change_injects_new_preset(root):
    (root / ".devin" / "output-mode.json").write_text(
        json.dumps({"mode": "caveman"}), encoding="utf-8")
    _run(root=str(root))
    (root / ".devin" / "output-mode.json").write_text(
        json.dumps({"mode": "quiet"}), encoding="utf-8")
    code, out = _run(root=str(root))
    assert code == 0 and "QUIET fragment" in out


def test_combo_injects_both(root):
    (root / ".devin" / "output-mode.json").write_text(
        json.dumps({"mode": "caveman+quiet"}), encoding="utf-8")
    code, out = _run(root=str(root))
    assert "CAVEMAN fragment" in out and "QUIET fragment" in out


def test_switching_off_emits_restore_notice(root):
    (root / ".devin" / "output-mode.json").write_text(
        json.dumps({"mode": "caveman"}), encoding="utf-8")
    _run(root=str(root))
    # hook's state survives the mode edit (it lives in the same file)
    cfg = json.loads((root / ".devin" / "output-mode.json").read_text(encoding="utf-8"))
    cfg["mode"] = "off"
    (root / ".devin" / "output-mode.json").write_text(json.dumps(cfg), encoding="utf-8")
    code, out = _run(root=str(root))
    assert code == 0 and "restored to default" in out
