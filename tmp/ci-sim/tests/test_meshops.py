"""Contract tests for extensions/mesh-utils/meshops.py.

No mesh backend needed: exercised paths fail before _load().
"""
import importlib.util
import io
import json
import sys
from contextlib import redirect_stdout
from pathlib import Path

import pytest

MESOPS = (Path(__file__).resolve().parents[1] /
          "extensions" / "mesh-utils" / "meshops.py")


def _load():
    spec = importlib.util.spec_from_file_location("meshops", MESOPS)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


meshops = _load()


def _run(fn, *args):
    """Call a cmd_* helper; _out/_fail raise SystemExit."""
    buf = io.StringIO()
    with pytest.raises(SystemExit) as exc, redirect_stdout(buf):
        fn(*args)
    return exc.value.code, json.loads(buf.getvalue())


def test_clean_missing_src_typed_error(tmp_path):
    code, env = _run(meshops.cmd_clean, str(tmp_path / "nope.ply"),
                     str(tmp_path / "out.ply"))
    assert code == 1
    assert env["ok"] is False and "not found" in env["error"]


def test_convert_dst_refuses_overwrite(tmp_path):
    src = tmp_path / "in.ply"
    src.write_bytes(b"x")
    dst = tmp_path / "out.ply"
    dst.write_bytes(b"old")
    code, env = _run(meshops.cmd_convert, str(src), str(dst))
    assert code == 1
    assert env["ok"] is False and "refusing to overwrite" in env["error"]
    assert dst.read_bytes() == b"old"


def test_clean_dst_refuses_overwrite(tmp_path):
    src = tmp_path / "in.ply"
    src.write_bytes(b"x")
    dst = tmp_path / "out.ply"
    dst.write_bytes(b"old")
    code, env = _run(meshops.cmd_clean, str(src), str(dst))
    assert code == 1
    assert env["ok"] is False and "refusing to overwrite" in env["error"]
    assert dst.read_bytes() == b"old"
