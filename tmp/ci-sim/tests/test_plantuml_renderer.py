"""Contract tests for extensions/diagram-tools/plantuml_renderer.py.

No network: urlopen is monkeypatched; emit() paths raise SystemExit.
"""
import importlib.util
import json
import sys
import urllib.request
from pathlib import Path

import pytest

RENDERER = (Path(__file__).resolve().parents[1] /
            "extensions" / "diagram-tools" / "plantuml_renderer.py")


def _load():
    spec = importlib.util.spec_from_file_location("plantuml_renderer",
                                                  RENDERER)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


renderer = _load()


def run_main(argv, capsys):
    with pytest.raises(SystemExit) as exc:
        sys.argv = ["plantuml_renderer.py"] + argv
        renderer.main()
    return exc.value.code, json.loads(capsys.readouterr().out)


def _src(tmp_path):
    p = tmp_path / "d.puml"
    p.write_text("@startuml\nAlice -> Bob: hi\n@enduml\n",
                 encoding="utf-8")
    return p


def test_server_is_https():
    assert renderer.SERVER.startswith("https://")


def test_explicit_out_refuses_overwrite(monkeypatch, capsys, tmp_path):
    src = _src(tmp_path)
    out = tmp_path / "arch.svg"
    out.write_text("<svg>old</svg>", encoding="utf-8")

    def boom(req, timeout=None):
        raise AssertionError("network must not be hit")

    monkeypatch.setattr(urllib.request, "urlopen", boom)
    code, env = run_main([str(src), "-o", str(out)], capsys)
    assert code == 2
    assert env["ok"] is False and "out exists" in env["error"]
    assert out.read_text() == "<svg>old</svg>"


def test_oversize_response_rejected(monkeypatch, capsys, tmp_path):
    src = _src(tmp_path)
    out = tmp_path / "big.svg"

    class Resp:
        def __enter__(self): return self
        def __exit__(self, *a): return False
        def read(self, n=-1): return b"x" * (renderer.MAX_BYTES + 1)

    monkeypatch.setattr(urllib.request, "urlopen",
                        lambda req, timeout=None: Resp())
    code, env = run_main([str(src), "-o", str(out)], capsys)
    assert code == 1
    assert env["ok"] is False and "exceeds" in env["error"]
    assert not out.exists()


def test_default_out_overwrites_on_rerender(monkeypatch, capsys, tmp_path):
    """Derived <src>.<fmt> path stays overwritable (idempotent re-render)."""
    src = _src(tmp_path)
    derived = tmp_path / "d.svg"
    derived.write_text("stale", encoding="utf-8")

    class Resp:
        def __enter__(self): return self
        def __exit__(self, *a): return False
        def read(self, n=-1): return b"<svg xmlns='x'></svg>"

    monkeypatch.setattr(urllib.request, "urlopen",
                        lambda req, timeout=None: Resp())
    code, env = run_main([str(src)], capsys)
    assert code == 0
    assert env["ok"] is True
    assert derived.read_bytes() == b"<svg xmlns='x'></svg>"
