import json
import sys
import subprocess
from pathlib import Path


ROOT = Path(__file__).parents[2]


def run_memory_hook(payload):
    return subprocess.run(
        [sys.executable, "scripts/memory-stop.py"],
        input=json.dumps(payload),
        capture_output=True,
        text=True,
        cwd=ROOT,
        timeout=10,
    )


def test_config_uses_available_free_primary_model():
    config = json.loads((ROOT / "config.json").read_text(encoding="utf-8-sig"))
    assert config["agent"]["model"] == "swe-2-high"


def test_stop_accepts_last_assistant_message():
    result = run_memory_hook({
        "hook_event_name": "Stop",
        "stop_hook_active": False,
        "last_assistant_message": "completed",
    })
    assert result.returncode == 0


def test_session_end_consumes_reason():
    result = run_memory_hook({"hook_event_name": "SessionEnd", "reason": "logout"})
    assert result.returncode == 0
    assert "session ended: logout" in result.stderr


def test_session_end_hook_is_registered():
    # hooks.v1.json is the single authored source; user-level config.json.hooks
    # is rendered from it at install time by scripts/render-user-hooks.py.
    hooks = json.loads((ROOT / "hooks.v1.json").read_text(encoding="utf-8-sig"))
    entries = hooks["SessionEnd"][0]["hooks"]
    assert any("memory-stop.py" in hook["command"] for hook in entries)
    config = json.loads((ROOT / "config.json").read_text(encoding="utf-8-sig"))
    assert config["hooks"] == {}


def test_native_plugin_prototype_is_isolated_and_minimal():
    path = ROOT / "tests/fixtures/devin-plugin-prototype/.devin-plugin/plugin.json"
    manifest = json.loads(path.read_text(encoding="utf-8"))
    assert manifest["name"] == "devin-bundle-prototype"
    assert manifest["skills"] == []
    assert "mcpServers" not in manifest


def test_validator_accepts_discovered_project_profiles():
    for profile in ("domain", "issue-tracker", "triage-labels"):
        result = subprocess.run(
            [sys.executable, "scripts/validate-tool-args.py"],
            input=json.dumps({
                "hook_event_name": "PreToolUse",
                "tool_name": "run_subagent",
                "tool_input": {"profile": profile, "title": "test", "task": "test"},
            }),
            capture_output=True,
            text=True,
            cwd=ROOT,
            timeout=10,
        )
        assert result.returncode == 0, result.stdout
