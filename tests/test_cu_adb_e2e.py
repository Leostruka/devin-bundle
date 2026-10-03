"""adb E2E — real CLIs against a real `adb` subprocess (fake device).

Unit tests inject `run`; nothing before this file crossed the actual
process boundary: PATH resolution (shutil.which -> adb.bat), argv
serialization, binary PNG over a pipe, real adb output shapes, and the
registry->backend->subprocess->device chain per CLI. A `.bat` shim is
the real boundary — CreateProcess launches it exactly like adb.exe.
"""
import json
import os
import shutil
import subprocess
import sys
import uuid
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parent.parent
EXT = REPO / "extensions" / "computer-use"
FAKE = Path(__file__).resolve().parent / "fake_adb.py"


@pytest.fixture
def phone(tmp_path):
    """Shim dir on PATH, env registry, state root, call log."""
    shimdir = tmp_path / "shim"
    shimdir.mkdir()
    shutil.copy(FAKE, shimdir / "adb_fake.py")
    (shimdir / "adb.bat").write_text(
        f'@echo off\r\n"{sys.executable}" "%~dp0adb_fake.py" %*\r\n')
    adb_sh = shimdir / "adb"
    adb_sh.write_text(
        f'#!/bin/sh\nexec "{sys.executable}" "{shimdir}/adb_fake.py" "$@"\n')
    adb_sh.chmod(0o755)
    envs = tmp_path / "envs"
    envs.mkdir()
    (envs / "phone.json").write_text(
        json.dumps({"env_id": "phone", "provider": "adb"}))
    log = tmp_path / "adb_calls.jsonl"
    env = dict(os.environ)
    env.update({
        "PATH": str(shimdir) + os.pathsep + env["PATH"],
        "CU_ENV_ROOT": str(envs),
        "CU_STATE_ROOT": str(tmp_path / "state"),
        "FAKE_ADB_LOG": str(log),
        "FAKE_ADB_MODE": "ok",
        "PYTHONUTF8": "1",
        "PYTHONPATH": str(EXT),
        "CU_SESSION": "",
    })
    env.pop("CU_ADB", None)

    def run_cli(script, *cli_args, mode=None):
        e = dict(env)
        if mode:
            e["FAKE_ADB_MODE"] = mode
        return subprocess.run(
            [sys.executable, str(EXT / script), *cli_args],
            capture_output=True, text=True, encoding="utf-8",
            errors="replace", env=e, cwd=str(REPO), timeout=60)

    def calls():
        if not log.exists():
            return []
        return [json.loads(l)["argv"] for l in
                log.read_text(encoding="utf-8").splitlines() if l.strip()]

    return run_cli, calls, tmp_path


def _json(proc):
    for candidate in (proc.stdout.strip(),
                      (proc.stdout.strip().splitlines() or [""])[-1]):
        try:
            return json.loads(candidate)
        except Exception:
            continue
    pytest.fail(f"no JSON on stdout: rc={proc.returncode} "
                f"out={proc.stdout[:300]} err={proc.stderr[:300]}")


def test_adb_shim_resolves_from_path(phone):
    run_cli, calls, _ = phone
    r = run_cli("env.py", "status", "--env", "phone")
    out = _json(r)
    assert r.returncode == 0 and out["ok"]
    assert out["device_state"] == "device" and out["serial"] == "FAKEDEV01"
    argv0 = calls()[0]
    assert argv0 == ["devices"]                       # auto-discovery
    assert any(c[2:] == ["get-state"] for c in calls())


def test_screenshot_hints_real_png_and_sidecar(phone):
    run_cli, calls, tmp = phone
    r = run_cli("screenshot.py", "--env", "phone", "--hints")
    out = _json(r)
    assert r.returncode == 0 and out["ok"], out
    png = Path(out["path"])
    assert png.read_bytes()[:8] == b"\x89PNG\r\n\x1a\n"  # real PNG landed
    assert out["width"] == 1080 and out["height"] == 2400
    names = {h["name"] for h in out["hints"]}
    assert "Apps" in names and "Opções" in names      # content-desc, UTF-8
    assert "desligado" not in names                  # enabled=false skipped
    assert "ghost" not in names                      # zero-area skipped
    seq = [tuple(c[2:]) for c in calls() if c[:1] == ["-s"]]
    assert ("exec-out", "screencap", "-p") in seq
    assert any(c[:2] == ("shell", "uiautomator") for c in seq)
    assert any(c[:2] == ("exec-out", "cat") for c in seq)
    sidecar = tmp / "state" / "phone" / "FAKEDEV01" / "default" \
        / "devin-cu-hints.json"
    assert sidecar.is_file()
    sc = json.loads(sidecar.read_text(encoding="utf-8"))
    assert sc["hints"][out["hints"][0]["id"]]["name"]


def test_click_by_hint_dispatches_real_tap(phone):
    run_cli, calls, _ = phone
    shot = _json(run_cli("screenshot.py", "--env", "phone", "--hints"))
    hint = next(h for h in shot["hints"] if h["name"] == "Apps")
    r = run_cli("mouse.py", "click", "--hint", hint["id"],
                "--gen", str(shot["generation"]), "--env", "phone")
    out = _json(r)
    assert r.returncode == 0 and out["status"] == "dispatched", out
    taps = [c for c in calls() if "tap" in c]
    assert taps, "no input tap reached the device"
    assert taps[-1][-2:] == [str(hint["x"]), str(hint["y"])]


def test_click_raw_coords(phone):
    run_cli, calls, _ = phone
    r = run_cli("mouse.py", "click", "500", "1000", "--env", "phone")
    assert _json(r)["status"] == "dispatched"
    assert any(c[-4:] == ["input", "tap", "500", "1000"] for c in calls())


def test_click_oob_rejected_against_real_frame(phone):
    run_cli, calls, _ = phone
    r = run_cli("mouse.py", "click", "5000", "10", "--env", "phone")
    out = _json(r)
    assert r.returncode != 0 and "oob" in out["error"]
    assert not any("tap" in c for c in calls())


def test_stale_generation_never_dispatches(phone):
    run_cli, calls, _ = phone
    shot = _json(run_cli("screenshot.py", "--env", "phone", "--hints"))
    hid = shot["hints"][0]["id"]
    run_cli("screenshot.py", "--env", "phone", "--hints")  # gen +1
    calls()  # drain position marker irrelevant; count taps only
    r = run_cli("mouse.py", "click", "--hint", hid,
                "--gen", str(shot["generation"]), "--env", "phone")
    out = _json(r)
    assert r.returncode != 0 and "stale_generation" in out["error"]
    assert not any("tap" in c for c in calls())


def test_scroll_and_drag_encode_swipe(phone):
    run_cli, calls, _ = phone
    r = run_cli("mouse.py", "scroll", "--dy", "2", "--env", "phone")
    assert _json(r)["status"] == "dispatched"
    swipes = [c for c in calls() if "swipe" in c]
    assert swipes and "input" in swipes[-1]
    r = run_cli("mouse.py", "drag", "200", "400",
                "--from-x", "200", "--from-y", "1200", "--env", "phone")
    assert _json(r)["status"] == "dispatched"
    last = [c for c in calls() if "swipe" in c][-1]
    assert "1200" in last and "400" in last


def test_position_rejected(phone):
    run_cli, _, _ = phone
    r = run_cli("mouse.py", "position", "--env", "phone")
    assert "position_unavailable" in _json(r)["error"]


def test_type_text_and_key(phone):
    run_cli, calls, _ = phone
    r = run_cli("type_text.py", "hello world", "--env", "phone")
    assert _json(r)["status"] == "dispatched"
    texts = [c for c in calls() if "text" in c and "input" in c]
    assert texts and texts[-1][-1] == "'hello%sworld'"
    r = run_cli("type_text.py", "--key", "enter", "--env", "phone")
    assert _json(r)["status"] == "dispatched"
    assert any(c[-3:] == ["input", "keyevent", "66"] for c in calls())


def test_type_unicode_rejected(phone):
    run_cli, calls, _ = phone
    r = run_cli("type_text.py", "héllo", "--env", "phone")
    assert "unsupported_text" in _json(r)["error"]
    assert not any("text" in c and "input" in c for c in calls())


def test_terminal_exec_runs_remote_shell(phone):
    run_cli, calls, _ = phone
    r = run_cli("terminal.py", "exec", "pm list packages", "--env", "phone")
    out = _json(r)
    assert r.returncode == 0 and out["ok"], out
    assert out["stdout"] == "fake:pm list packages\n"
    assert any(c[2:] == ["shell", "pm list packages"]
               for c in calls() if c[:1] == ["-s"])


def test_no_device_typed_rejection(phone):
    run_cli, _, _ = phone
    r = run_cli("screenshot.py", "--env", "phone", mode="none")
    out = _json(r)
    assert r.returncode != 0 and "no_device" in out["error"]


def test_ambiguous_devices(phone):
    run_cli, _, _ = phone
    r = run_cli("screenshot.py", "--env", "phone", mode="two")
    assert "ambiguous_devices" in _json(r)["error"]


def test_unauthorized_is_not_a_device(phone):
    run_cli, _, _ = phone
    r = run_cli("screenshot.py", "--env", "phone", mode="unauth")
    assert "no_device" in _json(r)["error"]


def test_adb_failure_typed_rejection(phone):
    run_cli, calls, _ = phone
    r = run_cli("type_text.py", "hi", "--env", "phone", mode="badrc")
    out = _json(r)
    assert r.returncode != 0 and "adb_rc1" in out["error"]


def test_record_polls_observe(phone, tmp_path=None):
    run_cli, calls, tmp = phone
    out_file = tmp / "rec.webp"
    r = run_cli("record.py", "--seconds", "0.4", "--fps", "6",
                "--env", "phone", "--out", str(out_file), "--no-sheet")
    out = _json(r)
    assert r.returncode == 0 and out["ok"], out
    assert out_file.is_file() and out_file.stat().st_size > 0
    grabs = [c for c in calls() if "screencap" in c]
    assert len(grabs) >= 2               # polling, not a single shot


def test_explicit_serial_skips_discovery(tmp_path):
    shimdir = tmp_path / "shim"
    shimdir.mkdir()
    shutil.copy(FAKE, shimdir / "adb_fake.py")
    (shimdir / "adb.bat").write_text(
        f'@echo off\r\n"{sys.executable}" "%~dp0adb_fake.py" %*\r\n')
    adb_sh = shimdir / "adb"
    adb_sh.write_text(
        f'#!/bin/sh\nexec "{sys.executable}" "{shimdir}/adb_fake.py" "$@"\n')
    adb_sh.chmod(0o755)
    envs = tmp_path / "envs"
    envs.mkdir()
    (envs / "phone.json").write_text(json.dumps(
        {"env_id": "phone", "provider": "adb", "serial": "MY-SERIAL-9"}))
    log = tmp_path / "log.jsonl"
    env = dict(os.environ)
    env.update({"PATH": str(shimdir) + os.pathsep + env["PATH"],
                "CU_ENV_ROOT": str(envs),
                "CU_STATE_ROOT": str(tmp_path / "state"),
                "FAKE_ADB_LOG": str(log),
                "PYTHONUTF8": "1", "PYTHONPATH": str(EXT), "CU_SESSION": ""})
    env.pop("CU_ADB", None)
    r = subprocess.run(
        [sys.executable, str(EXT / "screenshot.py"), "--env", "phone"],
        capture_output=True, text=True, env=env, cwd=str(REPO), timeout=60)
    out = _json(r)
    assert out["ok"] and out["instance_id"] == "MY-SERIAL-9"
    calls = [json.loads(l)["argv"] for l in
             log.read_text().splitlines() if l.strip()]
    assert all(c[:2] == ["-s", "MY-SERIAL-9"] for c in calls)
    assert not any(c[0] == "devices" for c in calls)
