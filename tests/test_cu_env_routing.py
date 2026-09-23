"""Gate for C01: --env resolves before ANY host resource is touched.

Unknown env never means local; a known env without an implemented backend
gets a typed `rejected` result. Hostile fixtures make host controllers,
emergency_release, mss and the local session daemon explode on contact —
the remote path must not reach any of them.
"""
import json
import os
import sys
import types
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent))
from cu_load import load  # noqa: E402

cu_target = load("cu_target")
cu_backend = load("cu_backend")
cu_actions = load("cu_actions")
mouse = load("mouse")
type_text = load("type_text")
screenshot = load("screenshot")
profile = load("profile")


def _boom(*args, **kwargs):
    raise AssertionError("host resource touched on remote path")


@pytest.fixture
def hostile_host(monkeypatch):
    """Every host-side seam is a trap on the remote branch."""
    fake_mouse = types.ModuleType("pynput.mouse")
    fake_mouse.Controller = _boom
    fake_mouse.Button = object()
    fake_kb = types.ModuleType("pynput.keyboard")
    fake_kb.Controller = _boom
    fake_kb.Key = object()
    fake_kb.KeyCode = object()
    fake_pynput = types.ModuleType("pynput")
    fake_pynput.mouse = fake_mouse
    fake_pynput.keyboard = fake_kb
    monkeypatch.setitem(sys.modules, "pynput", fake_pynput)
    monkeypatch.setitem(sys.modules, "pynput.mouse", fake_mouse)
    monkeypatch.setitem(sys.modules, "pynput.keyboard", fake_kb)

    fake_mss = types.ModuleType("mss")
    fake_mss.MSS = _boom
    monkeypatch.setitem(sys.modules, "mss", fake_mss)
    monkeypatch.setitem(sys.modules, "mss.tools",
                        types.ModuleType("mss.tools"))

    fake_dispatch = types.ModuleType("cu_session_dispatch")
    fake_dispatch.run_via_daemon = _boom
    monkeypatch.setitem(sys.modules, "cu_session_dispatch", fake_dispatch)

    monkeypatch.setattr(cu_actions, "emergency_release", _boom)


def _write_env(root, env_id="devin-linux", provider="qemu"):
    root = Path(root)
    root.mkdir(parents=True, exist_ok=True)
    spec = {"schema_version": 1, "env_id": env_id, "provider": provider,
            "image_ref": "approved-linux-desktop",
            "image_sha256": "0" * 64}
    (root / f"{env_id}.json").write_text(json.dumps(spec),
                                         encoding="utf-8")


def _run(mod, argv, monkeypatch, capsys):
    monkeypatch.setattr(sys, "argv", [f"{mod.__name__}.py"] + argv)
    with pytest.raises(SystemExit) as ei:
        mod.main()
    out = capsys.readouterr().out.strip().splitlines()
    return ei.value.code, json.loads(out[-1])


def test_unknown_environment_is_not_local():
    with pytest.raises(cu_target.TargetError, match="unknown_environment"):
        cu_target.resolve_target("missing", {})


def test_known_env_resolves_to_provider(tmp_path):
    _write_env(tmp_path)
    registry = cu_target.load_registry(tmp_path)
    target = cu_target.resolve_target("devin-linux", registry)
    assert target["kind"] == "qemu"
    assert target["env_id"] == "devin-linux"
    assert target["spec"]["image_sha256"] == "0" * 64


def test_load_registry_missing_dir_is_empty(tmp_path):
    assert cu_target.load_registry(tmp_path / "nope") == {}


def test_registry_rejects_spec_without_env_id(tmp_path):
    (tmp_path / "bad.json").write_text(
        json.dumps({"provider": "qemu"}), encoding="utf-8")
    with pytest.raises(cu_target.TargetError, match="invalid_spec"):
        cu_target.load_registry(tmp_path)


def test_open_backend_remote_is_typed_unavailable(tmp_path):
    _write_env(tmp_path)
    target = cu_target.resolve_target(
        "devin-linux", cu_target.load_registry(tmp_path))
    with pytest.raises(cu_backend.BackendUnavailable,
                       match="backend_unavailable"):
        cu_backend.open_backend(target)


def test_mouse_click_remote_rejected_without_host(hostile_host, tmp_path,
                                                  monkeypatch, capsys):
    _write_env(tmp_path)
    monkeypatch.setenv("CU_ENV_ROOT", str(tmp_path))
    code, out = _run(mouse, ["click", "10", "20", "--env", "devin-linux"],
                     monkeypatch, capsys)
    assert out["ok"] is False
    assert out["status"] == "rejected"
    assert "backend_unavailable" in out["error"]


def test_mouse_click_unknown_env_rejected(hostile_host, tmp_path,
                                          monkeypatch, capsys):
    monkeypatch.setenv("CU_ENV_ROOT", str(tmp_path))
    code, out = _run(mouse, ["click", "10", "20", "--env", "ghost"],
                     monkeypatch, capsys)
    assert out["ok"] is False
    assert out["status"] == "rejected"
    assert "unknown_environment" in out["error"]


def test_type_text_remote_rejected(hostile_host, tmp_path,
                                   monkeypatch, capsys):
    _write_env(tmp_path)
    monkeypatch.setenv("CU_ENV_ROOT", str(tmp_path))
    code, out = _run(type_text, ["hello", "--env", "devin-linux"],
                     monkeypatch, capsys)
    assert out["ok"] is False
    assert out["status"] == "rejected"


def test_screenshot_remote_rejected(hostile_host, tmp_path,
                                    monkeypatch, capsys):
    _write_env(tmp_path)
    monkeypatch.setenv("CU_ENV_ROOT", str(tmp_path))
    code, out = _run(screenshot, ["--env", "devin-linux"],
                     monkeypatch, capsys)
    assert out["ok"] is False
    assert out["status"] == "rejected"


def test_profile_remote_rejected(hostile_host, tmp_path,
                                 monkeypatch, capsys):
    _write_env(tmp_path)
    monkeypatch.setenv("CU_ENV_ROOT", str(tmp_path))
    code, out = _run(profile, ["--set", "fast", "--env", "devin-linux"],
                     monkeypatch, capsys)
    assert out["ok"] is False
    assert out["status"] == "rejected"


def test_remote_rejected_under_session_mode(hostile_host, tmp_path,
                                            monkeypatch, capsys):
    """$CU_SESSION=1 must not forward a remote request to the local
    daemon — --env resolves before the session shortcut."""
    _write_env(tmp_path)
    monkeypatch.setenv("CU_ENV_ROOT", str(tmp_path))
    monkeypatch.setenv("CU_SESSION", "1")
    code, out = _run(mouse, ["click", "10", "20", "--env", "devin-linux"],
                     monkeypatch, capsys)
    assert out["ok"] is False
    assert out["status"] == "rejected"


def test_dry_run_remote_still_rejected(hostile_host, tmp_path,
                                       monkeypatch, capsys):
    _write_env(tmp_path)
    monkeypatch.setenv("CU_ENV_ROOT", str(tmp_path))
    code, out = _run(mouse, ["click", "10", "20", "--env", "devin-linux",
                             "--dry-run"], monkeypatch, capsys)
    assert out["ok"] is False
    assert out["status"] == "rejected"


def test_no_env_keeps_local_path(monkeypatch, capsys):
    """Without --env the CLI takes the existing local path — it reaches
    the pynput import and fails honestly (no pynput in the test env)."""
    code, out = _run(mouse, ["position"], monkeypatch, capsys)
    assert out["ok"] is False
    assert "pynput" in out["error"]
    assert out.get("status") != "rejected"
