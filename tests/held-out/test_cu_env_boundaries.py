"""C16 held-out — remote-path boundary checks, deterministic.

Two axes, no VM needed:
1. Static: modules that carry remote/guest dispatch never reference
   host input/capture APIs (pynput, mss, SendInput, hooks, clipboard).
2. Dynamic: host-input modules are replaced by traps that explode on
   ANY attribute access; remote dispatch (screenshot/mouse/type with a
   fake backend) must complete without touching them.

Absence of observation is not absence of leak — the trap proves the
call never happened, it does not merely fail to see it.
"""
import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from cu_load import load  # noqa: E402

EXT = Path(__file__).resolve().parents[2] / \
    "extensions" / "computer-use"

REMOTE_MODULES = ["cu_qmp.py", "cu_qmp_backend.py", "cu_env_daemon.py",
                  "cu_guest.py", "cu_target.py", "cu_backend.py",
                  "cu_env.py", "cu_devices.py", "cu_container.py",
                  "guest/worker.py", "guest/container-entry.py"]

FORBIDDEN_TOKENS = ("pynput", "mss", "pyautogui", "SendInput",
                    "SetWindowsHookEx", "GetAsyncKeyState",
                    "OpenClipboard", "GetClipboardData",
                    "mouse_event", "keybd_event", "UIAutomation")


class Exploding:
    """Any attribute access on this module-stand-in is a leak."""

    def __init__(self, name):
        self._name = name

    def __getattr__(self, attr):
        raise AssertionError(
            f"remote path touched host module {self._name}.{attr}")


def _code_tokens(path):
    """Source minus strings/comments — docstrings may NAME the host
    APIs they exclude; the ban is on references in code."""
    import io
    import tokenize
    out = []
    for tok in tokenize.generate_tokens(
            io.StringIO(path.read_text("utf-8")).readline):
        if tok.type in (tokenize.COMMENT, tokenize.STRING):
            continue
        out.append(tok.string)
    return " ".join(out)


@pytest.mark.parametrize("mod", REMOTE_MODULES)
def test_remote_module_has_no_host_input_api(mod):
    code = _code_tokens(EXT / mod)
    for tok in FORBIDDEN_TOKENS:
        assert tok not in code, f"{mod} references {tok}"


@pytest.fixture
def host_traps(monkeypatch):
    """Exploding stand-ins for every host input/capture module."""
    for name in ("pynput", "mss", "pyautogui", "keyboard"):
        monkeypatch.setitem(sys.modules, name, Exploding(name))
    yield


def _frame():
    import cu_qmp_backend
    return cu_qmp_backend.Frame(b"\x00" * (2 * 2 * 3), 2, 2)


class FakeBackend:
    """Minimal remote backend — observe() returns (Frame, meta)."""

    name = "qmp"

    def __init__(self, env_dir):
        self.env_dir = Path(env_dir)
        self.sent = []

    def observe(self, timeout_s=15):
        return _frame(), {"instance_id": "i-1",
                          "frame_sha256": "x" * 64,
                          "backend": "qmp", "origin_px": [0, 0]}

    def send_events(self, events, **kw):
        self.sent.extend(events)
        return {"dispatched": len(events)}

    def pointer_position(self):
        import cu_qmp_backend
        raise cu_qmp_backend.BackendError("position_unavailable")

    def release_all(self):
        return {"ok": True}

    def guest_caps(self):
        return {}

    def text_insert(self, text):
        return {"inserted": len(text)}


def _target(backend):
    return {"kind": "qemu", "env_id": "devin-linux",
            "instance_id": "i-1", "backend": backend,
            "spec": {"keyboard_layout": "en-us"}}


def test_remote_screenshot_no_host_modules(host_traps, tmp_path,
                                           monkeypatch, capsys):
    monkeypatch.setenv("CU_STATE_ROOT", str(tmp_path))
    screenshot = load("screenshot")
    backend = FakeBackend(tmp_path / "env")
    backend.env_dir.mkdir(parents=True)
    monkeypatch.setattr("cu_target.cli_guard",
                        lambda argv: _target(backend))
    monkeypatch.setattr(sys, "argv",
                        ["screenshot.py", "--env", "devin-linux"])
    screenshot.main()
    out = json.loads(capsys.readouterr().out)
    assert out["ok"] is True
    assert out["backend"] == "qmp"


def test_remote_type_no_host_modules(host_traps, tmp_path,
                                     monkeypatch, capsys):
    monkeypatch.setenv("CU_STATE_ROOT", str(tmp_path))
    type_text = load("type_text")
    backend = FakeBackend(tmp_path / "env")
    monkeypatch.setattr("cu_target.cli_guard",
                        lambda argv: _target(backend))
    monkeypatch.setattr(sys, "argv",
                        ["type_text.py", "--key", "enter",
                         "--env", "devin-linux"])
    type_text.main()
    out = json.loads(capsys.readouterr().out)
    assert out["ok"] is True
    assert backend.sent  # events went to the guest


def test_remote_mouse_position_is_honest(host_traps, tmp_path,
                                         monkeypatch, capsys):
    monkeypatch.setenv("CU_STATE_ROOT", str(tmp_path))
    mouse = load("mouse")
    backend = FakeBackend(tmp_path / "env")
    monkeypatch.setattr("cu_target.cli_guard",
                        lambda argv: _target(backend))
    monkeypatch.setattr(sys, "argv",
                        ["mouse.py", "position", "--env",
                         "devin-linux"])
    with pytest.raises(SystemExit):
        mouse.main()
    out = json.loads(capsys.readouterr().out)
    assert out["ok"] is False
    assert "position_unavailable" in out.get("error", "")


def test_remote_mouse_move_no_host_modules(host_traps, tmp_path,
                                           monkeypatch, capsys):
    monkeypatch.setenv("CU_STATE_ROOT", str(tmp_path))
    mouse = load("mouse")
    backend = FakeBackend(tmp_path / "env")
    monkeypatch.setattr("cu_target.cli_guard",
                        lambda argv: _target(backend))
    monkeypatch.setattr(sys, "argv",
                        ["mouse.py", "move", "1", "1",
                         "--env", "devin-linux"])
    mouse.main()
    out = json.loads(capsys.readouterr().out)
    assert out["ok"] is True
    assert backend.sent


def test_cleanup_never_calls_host_release(host_traps, tmp_path,
                                          monkeypatch):
    monkeypatch.setenv("CU_STATE_ROOT", str(tmp_path))
    cu_backend = load("cu_backend")
    import cu_actions
    monkeypatch.setattr(
        cu_actions, "emergency_release",
        lambda *a, **kw: (_ for _ in ()).throw(
            AssertionError("host emergency_release on remote path")))
    backend = FakeBackend(tmp_path / "env")
    calls = []
    backend.release_all = lambda: calls.append("guest") or {
        "ok": True}
    cu_backend.cleanup({"kind": "qemu", "backend": backend})
    assert calls == ["guest"]
    # absent kind is not a license to release host state either
    with pytest.raises(Exception):
        cu_backend.cleanup({"kind": "qemu",
                            "env_id": "env-does-not-exist"})
