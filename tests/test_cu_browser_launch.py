"""browser.py launch/stop: agent-owned Chromium lifecycle."""
import io, json, os, sys
from contextlib import redirect_stdout
import pytest

sys.path.insert(0, os.path.dirname(__file__))
import cu_load  # noqa: E402

br = cu_load.load("cu_browser")
cli_mod = cu_load.load("browser")


def test_find_browser_exe_env_wins(monkeypatch):
    monkeypatch.setenv("CU_BROWSER_EXE", "/x/fake-chrome")
    assert br.find_browser_exe() == "/x/fake-chrome"


def test_launch_records_ownership_and_binds(monkeypatch, tmp_path):
    monkeypatch.setattr(br, "find_browser_exe", lambda: "/x/chrome")
    monkeypatch.setattr(br, "_spawn_browser",
                        lambda exe, port, udd: {"pid": 4321, "proc": object()})
    monkeypatch.setattr(br, "_browser_pid_via_cdp",
                        lambda endpoint, timeout: 4321)
    monkeypatch.setattr(br, "_wait_devtools", lambda ep, t: True)
    monkeypatch.setattr(br, "_free_port", lambda: 49999)
    monkeypatch.setattr(br, "profile_root", lambda: str(tmp_path))
    bound = {}
    def _bind(ep, pid):
        bound["hit"] = (ep, pid)
        return {"ok": True}
    monkeypatch.setattr(br, "bind", _bind)
    monkeypatch.setattr(br, "LAUNCHED_PATH", str(tmp_path / "launched.json"))
    r = br.launch_owned("work")
    assert r["ok"] and r["pid"] == 4321 and r["endpoint"].endswith("49999")
    assert bound["hit"] == (r["endpoint"], 4321)
    assert json.loads(open(br.LAUNCHED_PATH).read())["pid"] == 4321


def test_stop_refuses_foreign_pid(monkeypatch, tmp_path):
    monkeypatch.setattr(br, "LAUNCHED_PATH", str(tmp_path / "x.json"))
    open(br.LAUNCHED_PATH, "w").write(json.dumps({"pid": 1}))
    monkeypatch.setattr(br, "_pid_alive", lambda pid: False)
    monkeypatch.setattr(br, "binding", lambda: None)
    r = br.stop_owned()
    assert r["ok"] is False and r["error"].startswith("not_owned")


def test_launch_cli_json(monkeypatch, tmp_path):
    monkeypatch.setattr(br, "launch_owned",
                        lambda profile, timeout_s=15.0:
                            {"ok": True, "pid": 9, "endpoint": "e",
                             "profile_dir": "d", "binding": {}})
    buf = io.StringIO()
    old = sys.argv
    sys.argv = ["browser.py", "launch", "--profile", "work"]
    try:
        with redirect_stdout(buf):
            cli_mod.main()
    finally:
        sys.argv = old
    out = json.loads(buf.getvalue())
    assert out["ok"] and out["pid"] == 9
