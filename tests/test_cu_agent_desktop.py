"""cu_agent_desktop contract tests (issue #427): JSON-envelope parsing,
ref passthrough, error taxonomy, verify loop - all via injected runner."""
import importlib.util
import io
import json
import os
import subprocess
import sys
from contextlib import redirect_stdout

import pytest

EXT = os.path.join(os.path.dirname(__file__), "..",
                   "extensions", "computer-use")
sys.path.insert(0, EXT)

import cu_agent_desktop as ad  # noqa: E402


def _cp(stdout="", stderr="", rc=0):
    return subprocess.CompletedProcess([], rc, stdout, stderr)


def _env(data=None, ok=True, **kw):
    body = {"ok": ok, "command": "x"}
    if ok:
        body["data"] = data if data is not None else {}
    else:
        body["error"] = kw.get("error", {"code": "E", "message": "m"})
    # simulate npm noise prefix like real npx output
    return _cp("npm notice run agent-desktop\n" + json.dumps(body))


@pytest.fixture
def cli():
    calls = []

    def run(argv, timeout_s):
        calls.append((list(argv), timeout_s))
        return _env({"snapshot_id": "s1", "tree": {"role": "window"}})

    c = ad.AgentDesktop(binary=["fake-ad"], run=run)
    c.calls = calls
    return c


def test_resolve_binary_env(monkeypatch):
    monkeypatch.setenv("CU_AGENT_DESKTOP", "C:/tools/ad.exe")
    assert ad.resolve_binary() == ["C:/tools/ad.exe"]


def test_resolve_binary_path(monkeypatch):
    monkeypatch.delenv("CU_AGENT_DESKTOP", raising=False)
    monkeypatch.setattr(ad.shutil, "which",
                        lambda x: "C:/bin/agent-desktop.cmd"
                        if "agent-desktop" in x else None)
    assert ad.resolve_binary() == ["C:/bin/agent-desktop.cmd"]


def test_unavailable_raises(cli):
    cli._bin = None
    with pytest.raises(ad.AgentDesktopUnavailable):
        cli.status()


def test_status_parses_envelope(cli):
    data = cli.status()
    assert data["tree"]["role"] == "window"
    argv = cli.calls[-1][0]
    assert argv[:2] == ["fake-ad", "status"]


def test_error_envelope_raises():
    def run(argv, t):
        return _env(ok=False, error={"code": "POLICY_DENIED",
                                     "message": "nope"})
    c = ad.AgentDesktop(binary=["x"], run=run)
    with pytest.raises(ad.AgentDesktopError, match="POLICY_DENIED"):
        c.click("@s1:e1")


def test_no_json_envelope_raises():
    c = ad.AgentDesktop(binary=["x"], run=lambda a, t: _cp("not json"))
    with pytest.raises(ad.AgentDesktopError, match="no_json_envelope"):
        c.status()


def test_snapshot_flags(cli):
    cli.snapshot(app="Notepad", interactive=True, compact=True)
    argv = cli.calls[-1][0]
    assert "--app" in argv and "Notepad" in argv
    assert "-i" in argv and "--compact" in argv
    cli.snapshot(skeleton=True)
    argv = cli.calls[-1][0]
    assert "--skeleton" in argv and "-i" not in argv


def test_act_commands(cli):
    cli.click("@s1:e3")
    assert cli.calls[-1][0][1:3] == ["click", "@s1:e3"]
    cli.type_text("@s1:e4", "hi there")
    argv = cli.calls[-1][0]
    assert argv[1:4] == ["type", "@s1:e4", "hi there"]
    cli.set_value("@s1:e5", "v")
    assert cli.calls[-1][0][1:4] == ["set-value", "@s1:e5", "v"]
    cli.select("@s1:e6", "opt")
    assert cli.calls[-1][0][1:4] == ["select", "@s1:e6", "opt"]
    cli.get("@s1:e3", "name")
    assert cli.calls[-1][0][1:] == ["get", "@s1:e3",
                                  "--property", "name"]
    cli.is_state("@s1:e3", "enabled")
    assert cli.calls[-1][0][1:] == ["is", "@s1:e3",
                                  "--property", "enabled"]
    cli.press("ctrl+s")
    assert cli.calls[-1][0][1:3] == ["press", "ctrl+s"]


def test_snapshot_id_tracked(cli):
    assert cli._snapshot_id is None
    cli.status()
    assert cli._snapshot_id == "s1"


def test_verify_loop():
    seq = iter([{"ready": False}, {"ready": True}])

    def run(argv, t):
        return _env({"snapshot_id": "s", "tree": next(seq)})

    c = ad.AgentDesktop(binary=["x"], run=run)
    ok, data = c.verify(lambda d: d["tree"].get("ready"), attempts=3,
                        delay=0)
    assert ok and data["tree"]["ready"] is True


def test_verify_exhausts():
    c = ad.AgentDesktop(binary=["x"],
                        run=lambda a, t: _env({"tree": {"ready": False}}))
    ok, _ = c.verify(lambda d: d["tree"]["ready"], attempts=2, delay=0)
    assert ok is False


# -- DesktopBackend contract adapter (issue #429) --------------------------


class _FakeAD:
    """AgentDesktop-shaped stub for DesktopBackend tests."""

    def __init__(self):
        self.calls = []

    def _rec(self, name, *a, **k):
        self.calls.append((name, a, k))
        return {"ok": True, "name": name}

    def status(self):
        return {"platform": "windows", "surfaces": ["window"]}

    def snapshot(self, **kw):
        self.calls.append(("snapshot", kw, {}))
        return {"snapshot_id": "snap9", "tree": {"role": "window"}}

    def click(self, ref):
        return self._rec("click", ref)

    def type_text(self, ref, text):
        return self._rec("type", ref, text)

    def set_value(self, ref, value):
        return self._rec("set_value", ref, value)

    def press(self, combo):
        return self._rec("press", combo)

    def scroll(self, ref, direction="down", amount=None):
        return self._rec("scroll", ref, direction, amount)


def test_backend_observe_returns_tree_dict():
    b = ad.DesktopBackend(client=_FakeAD())
    obs = b.observe({"app": "WindowsTerminal"})
    assert obs["tree"]["snapshot_id"] == "snap9"
    assert obs["meta"]["backend"] == "agent-desktop"
    assert obs["meta"]["monotonic_ns"] > 0


def test_backend_dispatch_maps_ops():
    fake = _FakeAD()
    b = ad.DesktopBackend(client=fake)
    r = b.dispatch({"op": "click", "ref": "@s1:e3"})
    assert r["status"] == "dispatched" and r["op"] == "click"
    assert fake.calls[-1][0] == "click"
    r = b.dispatch({"op": "type", "ref": "@s1:e4", "text": "hi"})
    assert r["status"] == "dispatched"
    assert fake.calls[-1][1] == ("@s1:e4", "hi")


def test_backend_dispatch_rejects_unknown_and_errors():
    b = ad.DesktopBackend(client=_FakeAD())
    assert b.dispatch({"op": "teleport"})["status"] == "rejected"
    assert b.dispatch("not-a-dict")["status"] == "rejected"

    class Boom(_FakeAD):
        def click(self, ref):
            raise ad.AgentDesktopError("boom")
    r = ad.DesktopBackend(client=Boom()).dispatch(
        {"op": "click", "ref": "@e1"})
    assert r["status"] == "error" and "boom" in r["error"]


def test_backend_capabilities_and_lifecycle():
    b = ad.DesktopBackend(client=_FakeAD())
    caps = b.capabilities()
    assert caps["available"] and caps["observe"] == "tree"
    assert "click" in caps["verbs"] and "set_value" in caps["verbs"]
    assert b.release_all()["released"] == []
    b.close()  # no-op, must not raise


def test_open_backend_desktop_kind():
    import cu_backend
    b = cu_backend.open_backend({"kind": "desktop"})
    assert isinstance(b, ad.DesktopBackend)
    assert cu_backend.open_backend({"kind": "agent-desktop"}).kind == \
        "agent-desktop"
