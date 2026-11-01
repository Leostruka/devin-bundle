#!/usr/bin/env python3
"""PostToolUse hook: deterministic stuck-detector for repeated exec failures.

Inspired by Microsoft's token-economizer plugin (analysis:
.devin/notes/youtube/1kQ_1_QL5Es/video-analysis.md). The plugin's third
mechanism checks after every tool call whether the agent is stuck and
nudges it. This hook is the deterministic subset that runs without a
model call (hooks are stdlib-only, never paid): if the same normalized
exec command fails STREAK_THRESHOLD times in a row, emit one advisory
via hookSpecificOutput.additionalContext.

State: <BUNDLE_MEMORY_DIR|.devin/memory>/.stuck-detect.json, bounded
(history <= HISTORY_MAX events, warned <= WARNED_MAX signatures),
rewritten atomically. Corrupt or unwritable state -> start fresh.
Fail-open everywhere: any exception -> exit 0 silent. Never blocks.
"""
import json
import os
import re
import sys

STREAK_THRESHOLD = 3
HISTORY_MAX = 12
WARNED_MAX = 16
SIG_MAX = 200

_EXIT_NONZERO = re.compile(
    r"(?:exit\s+code|EXIT=)\s*:?\s*([1-9]\d*)\b", re.IGNORECASE)
_WS = re.compile(r"\s+")


def _memory_dir():
    return (os.environ.get("BUNDLE_MEMORY_DIR")
            or os.environ.get("DEVIN_MEMORY_DIR")
            or os.path.join(os.environ.get("DEVIN_PROJECT_DIR")
                            or os.getcwd(), ".devin", "memory"))


def _signature(command):
    return _WS.sub(" ", str(command)).strip()[:SIG_MAX]


def _failed(response):
    if not isinstance(response, dict):
        return False
    if response.get("success") is False:
        return True
    error = response.get("error")
    if isinstance(error, str) and error.strip():
        return True
    output = response.get("output")
    if isinstance(output, str) and _EXIT_NONZERO.search(output):
        return True
    return False


def _load_state(path):
    try:
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
        if (isinstance(data, dict)
                and isinstance(data.get("history"), list)
                and isinstance(data.get("warned"), list)):
            data["history"] = [
                e for e in data["history"][-HISTORY_MAX:]
                if isinstance(e, dict) and "sig" in e]
            data["warned"] = [
                s for s in data["warned"][-WARNED_MAX:]
                if isinstance(s, str)]
            return data
    except (OSError, ValueError):
        pass
    return {"history": [], "warned": []}


def _save_state(path, state):
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(state, f, separators=(",", ":"))
    os.replace(tmp, path)


def _emit(message):
    print(json.dumps({
        "hookSpecificOutput": {
            "hookEventName": "PostToolUse",
            "additionalContext": message,
        }
    }))


def main():
    try:
        data = json.load(sys.stdin)
    except (json.JSONDecodeError, EOFError, ValueError):
        sys.exit(0)

    try:
        if not isinstance(data, dict):
            sys.exit(0)
        if data.get("tool_name") != "exec":
            sys.exit(0)
        tool_input = data.get("tool_input") or {}
        command = tool_input.get("command") if isinstance(tool_input, dict) else None
        if not command:
            sys.exit(0)

        state_path = os.path.join(_memory_dir(), ".stuck-detect.json")
        state = _load_state(state_path)
        sig = _signature(command)
        failed = _failed(data.get("tool_response"))
        state["history"] = (
            state["history"] + [{"sig": sig, "failed": bool(failed)}]
        )[-HISTORY_MAX:]
        try:
            os.makedirs(os.path.dirname(state_path), exist_ok=True)
            _save_state(state_path, state)
        except OSError:
            pass  # advisory state is best-effort; never break the hook

        streak = 0
        for event in reversed(state["history"]):
            if event.get("sig") != sig or not event.get("failed"):
                break
            streak += 1
        if streak >= STREAK_THRESHOLD and sig not in state["warned"]:
            state["warned"] = (state["warned"] + [sig])[-WARNED_MAX:]
            try:
                _save_state(state_path, state)
            except OSError:
                pass
            _emit(
                "stuck-detect: the same exec command failed "
                f"{streak}x consecutively: `{sig[:120]}` -- you may be "
                "repeating a failing approach. Read the error output and "
                "try a different command instead of retrying.")
    except Exception:
        sys.exit(0)
    sys.exit(0)


if __name__ == "__main__":
    main()
