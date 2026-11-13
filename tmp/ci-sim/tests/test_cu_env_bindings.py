"""Gate for C12: browser/terminal bindings bound to the ENV, not host.

Bindings carry (env_id, instance_id) and live under the env's private
state namespace; a host binding never satisfies a guest target and a
stale instance never reactivates. Remote ops go through the guest
channel with capability gates — no host CDP publication, no host
loopback widening.
"""
import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent))
from cu_load import load  # noqa: E402

cu_guest = load("cu_guest")
cu_browser = load("cu_browser")
cu_terminal = load("cu_terminal")
cu_target = load("cu_target")


# --- binding_matches (pure) ------------------------------------------------------------

def test_host_binding_is_invalid_in_guest():
    assert cu_guest.binding_matches(
        {"env_id": "host", "instance_id": "h"}, "vm-a", "a") is False


def test_binding_matches_exact():
    b = {"env_id": "vm-a", "instance_id": "i-1"}
    assert cu_guest.binding_matches(b, "vm-a", "i-1") is True
    assert cu_guest.binding_matches(b, "vm-a", "i-2") is False
    assert cu_guest.binding_matches(b, "vm-b", "i-1") is False


def test_binding_matches_missing_fields():
    assert cu_guest.binding_matches({}, "e", "i") is False
    assert cu_guest.binding_matches(None, "e", "i") is False


# --- env-scoped browser binding ---------------------------------------------------------

def test_remote_binding_writes_under_env_namespace(tmp_path):
    monkey = pytest.MonkeyPatch()
    monkey.setenv("CU_STATE_ROOT", str(tmp_path))
    r = cu_browser.bind_remote("devin-linux", "i-1",
                               {"kind": "guest-cdp"})
    assert r["ok"] is True
    b = r["binding"]
    assert b["env_id"] == "devin-linux"
    assert b["instance_id"] == "i-1"
    p = Path(r["path"])
    parts = p.parts
    i = parts.index("devin-linux")
    assert parts[i + 1:i + 3] == ("i-1", "default")
    assert p.name == "browser-binding.json"


def test_remote_binding_scoped_read(tmp_path):
    monkey = pytest.MonkeyPatch()
    monkey.setenv("CU_STATE_ROOT", str(tmp_path))
    cu_browser.bind_remote("devin-linux", "i-1", {"kind": "guest-cdp"})
    b = cu_browser.binding(scope=("devin-linux", "i-1", "default"))
    assert b["env_id"] == "devin-linux"
    # wrong instance -> no binding
    assert cu_browser.binding(
        scope=("devin-linux", "i-2", "default")) is None


def test_host_loopback_allowlist_unchanged(tmp_path):
    """The host bind() still rejects non-loopback — nothing in C12
    widens it for guest endpoints."""
    r = cu_browser.bind("http://192.168.1.50:9222", 1234)
    assert r["ok"] is False
    r = cu_browser.bind("http://127.0.0.1:9222", 1234)
    assert r["ok"] is True


# --- remote browser ops through guest channel -------------------------------------------

@pytest.fixture
def remote_target(tmp_path, monkeypatch):
    reg = tmp_path / "envs"
    reg.mkdir()
    (reg / "devin-linux.json").write_text(json.dumps(
        {"env_id": "devin-linux", "provider": "qemu"}))
    monkeypatch.setenv("CU_ENV_ROOT", str(reg))
    return reg


def test_remote_browser_requires_dom_cap(remote_target, monkeypatch,
                                         capsys):
    """DOM ops need the guest 'dom' capability — absent → typed
    rejection, not a host fallback."""
    calls = []

    class FakeBackend:
        env_dir = remote_target

        def guest_caps(self):
            return {"dom": False}

        def guest_call(self, method, params):
            calls.append(method)
            raise AssertionError("guest_call without cap")

    cb = load("cu_backend")
    monkeypatch.setattr(cb, "open_backend",
                        lambda t: FakeBackend())
    browser = load("browser")
    monkeypatch.setattr(sys, "argv",
                        ["browser.py", "navigate", "https://x.test",
                         "--env", "devin-linux"])
    with pytest.raises(SystemExit):
        browser.main()
    out = json.loads(capsys.readouterr().out.strip().splitlines()[-1])
    assert out["ok"] is False
    assert calls == []


def test_remote_browser_op_dispatches_via_guest(remote_target,
                                                monkeypatch, capsys):
    calls = []

    class FakeBackend:
        env_dir = remote_target

        def guest_caps(self):
            return {"dom": True}

        def guest_call(self, method, params):
            calls.append((method, params))
            return {"ok": True, "url": params.get("url")}

    cb = load("cu_backend")
    monkeypatch.setattr(cb, "open_backend",
                        lambda t: FakeBackend())
    browser = load("browser")
    monkeypatch.setattr(sys, "argv",
                        ["browser.py", "navigate", "https://x.test",
                         "--env", "devin-linux"])
    browser.main()
    out = json.loads(capsys.readouterr().out.strip().splitlines()[-1])
    assert out["ok"] is True
    assert calls and calls[0][0].startswith("dom.")


# --- remote terminal: auth semantics + untrusted output ---------------------------------

def test_remote_terminal_exec_preserves_auth(remote_target, monkeypatch,
                                             capsys):
    """Guest exec goes through the worker's exec.run — capability-gated;
    output is marked untrusted. Host system-control DENY/CONFIRM is not
    on this path and is never bypassed: absent cap rejects."""
    calls = []

    class FakeBackend:
        env_dir = remote_target

        def guest_caps(self):
            return {"exec": False}

        def guest_call(self, method, params):
            calls.append(method)
            return {"ok": True}

    cb = load("cu_backend")
    monkeypatch.setattr(cb, "open_backend",
                        lambda t: FakeBackend())
    terminal = load("terminal")
    monkeypatch.setattr(sys, "argv",
                        ["terminal.py", "exec", "ls", "--env",
                         "devin-linux"])
    with pytest.raises(SystemExit):
        terminal.main()
    assert calls == []


def test_remote_terminal_exec_marks_untrusted(remote_target,
                                              monkeypatch, capsys):
    class FakeBackend:
        env_dir = remote_target

        def guest_caps(self):
            return {"exec": True}

        def guest_call(self, method, params):
            return {"ok": True, "stdout": "hello\n", "rc": 0}

    cb = load("cu_backend")
    monkeypatch.setattr(cb, "open_backend",
                        lambda t: FakeBackend())
    terminal = load("terminal")
    monkeypatch.setattr(sys, "argv",
                        ["terminal.py", "exec", "ls", "--env",
                         "devin-linux"])
    terminal.main()
    out = json.loads(capsys.readouterr().out.strip().splitlines()[-1])
    assert out["ok"] is True
    assert out.get("untrusted") is True
    assert out["stdout"] == "hello\n"
