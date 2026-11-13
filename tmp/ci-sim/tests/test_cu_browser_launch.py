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


def test_launch_refuses_when_already_launched(monkeypatch, tmp_path):
    monkeypatch.setattr(br, "launched", lambda: {"pid": 111})
    spawned = []
    monkeypatch.setattr(br, "_spawn_browser",
                        lambda *a: spawned.append(a) or {"pid": 1})
    r = br.launch_owned("work")
    assert r["ok"] is False and r["error"] == "already_launched"
    assert spawned == []


def test_stop_refuses_dead_endpoint(monkeypatch, tmp_path):
    monkeypatch.setattr(br, "LAUNCHED_PATH", str(tmp_path / "x.json"))
    open(br.LAUNCHED_PATH, "w").write(json.dumps(
        {"pid": 555, "endpoint": "http://127.0.0.1:1"}))
    monkeypatch.setattr(br, "_pid_alive", lambda pid: True)
    def _boom(url, timeout=5.0):
        raise OSError("connection refused")
    monkeypatch.setattr(br, "_http_json", _boom)
    killed = []
    monkeypatch.setattr(br, "_kill_pid",
                        lambda pid: killed.append(pid) or True)
    r = br.stop_owned()
    assert r["ok"] is False and r["error"].startswith("not_owned")
    assert killed == []


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


def test_launch_kills_spawned_on_timeout(monkeypatch, tmp_path):
    monkeypatch.setattr(br, "find_browser_exe", lambda: "/x/chrome")
    monkeypatch.setattr(br, "_spawn_browser",
                        lambda exe, port, udd: {"pid": 777, "proc": object()})
    monkeypatch.setattr(br, "_wait_devtools", lambda ep, t: False)
    monkeypatch.setattr(br, "_free_port", lambda: 49998)
    monkeypatch.setattr(br, "profile_root", lambda: str(tmp_path))
    killed = []
    monkeypatch.setattr(br, "_kill_pid", lambda pid: killed.append(pid) or True)
    r = br.launch_owned("work")
    assert killed == [777]
    assert r["ok"] is False and r["error"] == "browser_start_timeout"
    assert r["pid"] == 777


def test_stop_reports_kill_failure(monkeypatch, tmp_path):
    monkeypatch.setattr(br, "LAUNCHED_PATH", str(tmp_path / "x.json"))
    open(br.LAUNCHED_PATH, "w").write(json.dumps(
        {"pid": 555, "endpoint": "http://127.0.0.1:2"}))
    monkeypatch.setattr(br, "_pid_alive", lambda pid: True)
    monkeypatch.setattr(br, "_http_json",
                        lambda url, timeout=5.0: {"Browser": "x"})
    monkeypatch.setattr(br, "binding", lambda: None)
    monkeypatch.setattr(br, "_kill_pid", lambda pid: False)
    r = br.stop_owned()
    assert r["ok"] is False and r["error"].startswith("kill_failed")
    assert os.path.isfile(br.LAUNCHED_PATH)
