import json
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SCRIPT = ROOT / "scripts" / "subagent-trace.py"


def run(args, payload=None, proj=None):
    env = dict(os.environ)
    if proj is not None:
        env["DEVIN_PROJECT_DIR"] = str(proj)
    r = subprocess.run(
        [sys.executable, str(SCRIPT), *args],
        input=json.dumps(payload) if payload is not None else "",
        capture_output=True, text=True, encoding="utf-8", errors="replace",
        env=env)
    return r


def trace_file(proj):
    return proj / ".devin" / "subagent-trace.jsonl"


def test_record_appends_record(tmp_path):
    r = run(["record"], {"agent": "implementer", "title": "fix tests",
                         "profile": "swe-2-medium"}, proj=tmp_path)
    out = json.loads(r.stdout)
    assert r.returncode == 0 and out["ok"] is True
    rec = json.loads(trace_file(tmp_path).read_text(
        encoding="utf-8").strip())
    assert rec["agent"] == "implementer" and rec["status"] == "running"
    assert rec["id"] == out["id"] and rec["ts"]


def test_record_updates_existing_id(tmp_path):
    run(["record"], {"id": "s1", "agent": "implementer"},
        proj=tmp_path)
    r = run(["record"], {"id": "s1", "status": "done",
                         "notes": "3 files changed"}, proj=tmp_path)
    assert json.loads(r.stdout)["ok"] is True
    lines = trace_file(tmp_path).read_text(encoding="utf-8").strip()
    recs = [json.loads(x) for x in lines.splitlines()]
    assert len(recs) == 1
    assert recs[0]["status"] == "done" and recs[0]["agent"] == "implementer"


def test_record_args_and_bad_status(tmp_path):
    r = run(["record", "--id", "s9", "--agent", "reviewer",
             "--status", "bogus"], proj=tmp_path)
    assert r.returncode == 2 and json.loads(r.stdout)["ok"] is False
    r = run(["record", "--id", "s9", "--agent", "reviewer",
             "--status", "running"], proj=tmp_path)
    assert r.returncode == 0
    rec = json.loads(trace_file(tmp_path).read_text(
        encoding="utf-8").strip())
    assert rec["agent"] == "reviewer"


def test_pending_lists_running_only(tmp_path):
    run(["record"], {"id": "a", "status": "running"}, proj=tmp_path)
    run(["record"], {"id": "b", "status": "done"}, proj=tmp_path)
    r = run(["--pending"], proj=tmp_path)
    out = json.loads(r.stdout)
    assert out["pending"] == 1 and out["records"][0]["id"] == "a"
    r = run(["--list"], proj=tmp_path)
    assert len(json.loads(r.stdout)["records"]) == 2


def test_abort_flag_roundtrip(tmp_path):
    run(["record"], {"id": "s1", "status": "running"}, proj=tmp_path)
    r = run(["check-abort", "s1"], proj=tmp_path)
    assert r.returncode == 1 and json.loads(r.stdout)["abort"] is False
    r = run(["--abort", "s1"], proj=tmp_path)
    assert json.loads(r.stdout)["ok"] is True
    assert (tmp_path / ".devin" / "subagent-abort" / "s1").exists()
    r = run(["check-abort", "s1"], proj=tmp_path)
    assert r.returncode == 0 and json.loads(r.stdout)["abort"] is True
    run(["--clear-abort", "s1"], proj=tmp_path)
    r = run(["check-abort", "s1"], proj=tmp_path)
    assert r.returncode == 1


def test_clear_abort_missing_is_ok(tmp_path):
    r = run(["--clear-abort", "nope"], proj=tmp_path)
    out = json.loads(r.stdout)
    assert r.returncode == 0 and out["ok"] is True
    assert out["removed"] is False


def test_unexpected_error_exits_nonzero(tmp_path, monkeypatch):
    # {"ok": false} envelope must never exit 0 (CLI contract + docstring)
    import importlib.util
    spec = importlib.util.spec_from_file_location("st2", SCRIPT)
    st = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(st)
    monkeypatch.setattr(st, "_load",
                        lambda p: (_ for _ in ()).throw(RuntimeError("boom")))
    r = subprocess.run(
        [sys.executable, "-c",
         "import importlib.util,sys;"
         "s=importlib.util.spec_from_file_location('st',r'" + str(SCRIPT) + "');"
         "m=importlib.util.module_from_spec(s);s.loader.exec_module(m);"
         "m._load=lambda p:(_ for _ in ()).throw(RuntimeError('boom'));"
         "sys.exit(m.main(['x','--list']))"],
        capture_output=True, text=True, encoding="utf-8", errors="replace")
    out = json.loads(r.stdout)
    assert out["ok"] is False and r.returncode != 0


def test_concurrent_record_keeps_trace_intact(tmp_path):
    # atomic _save: trace file must remain valid JSONL after writes
    import concurrent.futures
    def rec(i):
        return run(["record"], {"id": f"t{i}", "status": "running"},
                   proj=tmp_path)
    with concurrent.futures.ThreadPoolExecutor(max_workers=8) as ex:
        list(ex.map(rec, range(8)))
    lines = trace_file(tmp_path).read_text(encoding="utf-8").strip().splitlines()
    ids = {json.loads(l)["id"] for l in lines}
    assert len(ids) == len(lines)  # every line valid, no torn writes


def test_abort_id_traversal_rejected(tmp_path):
    # rid is joined into the abort path - traversal must not write/delete
    # outside <proj>/.devin (was: --abort ../../x truncated arbitrary files)
    victim = tmp_path / "victim.txt"
    victim.write_text("keep me", encoding="utf-8")
    for bad in ["../../victim", "../victim", ".", "..", "a/b", "a\b",
                ".hidden"]:
        r = run(["--abort", bad], proj=tmp_path)
        out = json.loads(r.stdout)
        assert out["ok"] is False and r.returncode == 2, bad
        r = run(["--clear-abort", bad], proj=tmp_path)
        out = json.loads(r.stdout)
        assert out["ok"] is False and r.returncode == 2, bad
    assert victim.read_text(encoding="utf-8") == "keep me"
    # legit id still works
    r = run(["--abort", "ok-id_1.2"], proj=tmp_path)
    assert json.loads(r.stdout)["ok"] is True
