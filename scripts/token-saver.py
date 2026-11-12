#!/usr/bin/env python3
"""UserPromptSubmit hook: inject output-mode preset only on change.

PandaCode-style token saver (~650 tok/msg upstream claim): fixed
instructions should not be re-sent every message. This hook reads
.devin/output-mode.json {"mode": "off|caveman|lean|quiet|lean+quiet",
"state": {"last": "<mode>"}} and emits the preset fragment ONLY when the
mode differs from the last injected one — the style-of-output equivalent
of sending the system prompt once.

Presets live in data/output-modes.json (versioned). Combos join with '+'
(e.g. "lean+quiet" injects both fragments). Mode "off" (or missing file)
emits nothing; switching back to "off" emits a one-line restore notice so
a stale preset does not linger in context.

Fail-open everywhere: any exception -> exit 0 silent.
"""
import json
import os
import sys

MODE_FILE_REL = os.path.join(".devin", "output-mode.json")
PRESETS_REL = os.path.join("data", "output-modes.json")


def _project_dir():
    return os.environ.get("DEVIN_PROJECT_DIR") or os.getcwd()


def _read_json(path):
    try:
        with open(path, encoding="utf-8-sig") as fh:
            return json.load(fh)
    except (OSError, ValueError):
        return {}


def _emit(context):
    print(json.dumps({
        "hookSpecificOutput": {
            "hookEventName": "UserPromptSubmit",
            "additionalContext": context,
        }
    }))


def main():
    try:
        _recfg = getattr(sys.stdin, "reconfigure", None)
        if _recfg:
            try:
                _recfg(encoding="utf-8", errors="replace")
            except (OSError, ValueError):
                pass
        json.load(sys.stdin)
    except (json.JSONDecodeError, EOFError, ValueError):
        sys.exit(0)

    root = _project_dir()
    mode_path = os.path.join(root, MODE_FILE_REL)
    if not os.path.isfile(mode_path):
        sys.exit(0)  # no mode file: feature untouched, emit nothing
    cfg = _read_json(mode_path)
    mode = str(cfg.get("mode") or "off").strip().lower()
    state = cfg.get("state") if isinstance(cfg.get("state"), dict) else {}
    last = state.get("last")
    if mode == last:
        sys.exit(0)

    if mode != "off":
        presets = _read_json(os.path.join(root, PRESETS_REL))
        parts = [p for p in mode.split("+") if p in presets]
        if parts:
            _emit("\n".join(presets[p]["context"] for p in parts))
        # unknown modes fall through: state still recorded, nothing injected
    elif last:
        # only announce the restore when a preset was actually active
        _emit("Output mode restored to default (previous preset cleared).")

    cfg["state"] = {"last": mode}
    try:
        with open(mode_path, "w", encoding="utf-8") as fh:
            json.dump(cfg, fh)
    except OSError:
        pass
    sys.exit(0)


if __name__ == "__main__":
    main()
