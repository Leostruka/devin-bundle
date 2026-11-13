"""comfyui-operator wrapper - trust-boundary contract (audit-r5 01/02)."""
import importlib.util
import io
import json
import os
import sys
from pathlib import Path
from unittest.mock import patch

import pytest

EXT = Path(__file__).resolve().parents[1] / "extensions" / "comfyui-operator"
spec = importlib.util.spec_from_file_location(
    "comfyui_wrapper", EXT / "wrapper.py")
wrapper = importlib.util.module_from_spec(spec)
spec.loader.exec_module(wrapper)


def _run_cli(argv, env=None):
    out = io.StringIO()
    with patch.object(sys, "argv", ["wrapper.py"] + argv), \
         patch.object(sys, "stdout", out), \
         patch.dict(os.environ, env or {}, clear=False), \
         pytest.raises(SystemExit) as e:
        wrapper.main()
    return e.value.code, out.getvalue()


# --- issue 01: loopback-only base url ------------------------------------------

def test_remote_url_rejected():
    code, out = _run_cli(["--url", "http://attacker.example:8188", "status"])
    assert code != 0
    assert "loopback" in out


def test_env_remote_url_rejected():
    code, out = _run_cli(["status"], env={"COMFYUI_URL": "http://8.8.8.8"})
    assert code != 0
    assert "loopback" in out


def test_non_http_scheme_rejected():
    code, out = _run_cli(["--url", "file:///etc/passwd", "status"])
    assert code != 0


def test_loopback_accepted(monkeypatch):
    monkeypatch.setattr(wrapper, "cmd_status",
                        lambda base: wrapper._out({"ok": True}))
    code, _ = _run_cli(["status"])
    assert code == 0


# --- issue 02: server-provided filename sanitization ----------------------------

def test_safe_dest_backslash_traversal(tmp_path):
    dest = wrapper._safe_dest(str(tmp_path), "..\\..\\", "evil.png")
    assert dest is not None
    assert os.path.basename(dest) == "evil.png"
    assert os.path.commonpath([os.path.realpath(str(tmp_path)), dest]) == \
        os.path.realpath(str(tmp_path))


def test_safe_dest_forward_slash_traversal(tmp_path):
    dest = wrapper._safe_dest(str(tmp_path), "../", "evil.png")
    assert dest is not None and os.path.basename(dest) == "evil.png"


def test_safe_dest_traversal_in_filename(tmp_path):
    dest = wrapper._safe_dest(str(tmp_path), "", "..\\..\\evil.png")
    assert dest is not None and os.path.basename(dest) == "evil.png"


def test_safe_dest_absolute_drive(tmp_path):
    dest = wrapper._safe_dest(str(tmp_path), "", "C:\\evil.png")
    assert dest is not None and os.path.basename(dest) == "evil.png"


def test_safe_dest_dotdot_filename_rejected(tmp_path):
    assert wrapper._safe_dest(str(tmp_path), "", "..") is None


def test_download_never_writes_outside(tmp_path, monkeypatch):
    monkeypatch.setattr(
        wrapper, "_request",
        lambda *a, **kw: {"p1": {"outputs": {"n": {"images": [
            {"filename": "..\\evil.png", "subfolder": "..\\..\\",
             "type": "output"}]}}}}
        if a[2].startswith("/history") else b"img")
    monkeypatch.setattr(wrapper, "_collect_outputs",
                        lambda e: [{"filename": "..\\evil.png",
                                    "subfolder": "..\\..\\",
                                    "type": "output", "node_id": "n",
                                    "kind": "images"}])
    outdir = tmp_path / "out"
    with patch.object(sys, "stdout", io.StringIO()) as buf, \
         pytest.raises(SystemExit) as e:
        wrapper.cmd_download("http://127.0.0.1:8188", "p1", str(outdir))
    assert e.value.code == 0
    assert (outdir / "evil.png").exists()
    assert not (tmp_path / "evil.png").exists()
