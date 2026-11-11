"""busybar listen — event mapping + replay (#491)."""
import importlib.util
import json
import os
import sys

spec = importlib.util.spec_from_file_location(
    "busybar_listen",
    os.path.join(os.path.dirname(__file__), "..", "extensions",
                 "busybar", "listen.py"))
mod = importlib.util.module_from_spec(spec)
sys.modules["busybar_listen"] = mod
spec.loader.exec_module(mod)


def test_map_switch_toggle():
    assert mod.map_event({"switch": "star", "pressed": True}) == \
        "focus-start"
    assert mod.map_event({"switch": "star",
                          "pressed": False}) == "focus-stop"
    assert mod.map_event({"button": "pause", "state": "off"}) == \
        "focus-stop"


def test_map_dial_effort():
    assert mod.map_event({"dial": 1}) == "effort-S"
    assert mod.map_event({"encoder": {"position": 3}}) == "effort-L"
    assert mod.map_event({"dial": 9}) is None


def test_unknown_frames_ignored():
    assert mod.map_event({"type": "audio", "level": 5}) is None
    assert mod.map_event({}) is None


def test_replay_counts_actions_and_skips_bad(tmp_path, capsys):
    f = tmp_path / "f.jsonl"
    f.write_text('\n'.join([
        json.dumps({"switch": "star", "pressed": True}),
        "garbage{",
        json.dumps({"dial": 2}),
        json.dumps({"type": "noop"}),
    ]), encoding="utf-8")
    mod.replay(str(f), exec_mode=False)
    out = capsys.readouterr()
    assert '"actions": 2' in out.out
    assert "unreadable frame skipped" in out.err
