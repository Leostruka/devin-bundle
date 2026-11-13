#!/usr/bin/env python3
"""Get/set the computer-use action profile for this session. JSON on stdout.

  profile.py --set human|smooth|fast   # persist to <temp>/devin-cu-profile.json
  profile.py --show                  # effective profile + sources
  profile.py                         # interactive menu (prompts go to stderr)

Agents: ask the user which profile to use (e.g. via ask_user_question), then
persist it with --set. Scripts resolve: --profile flag > $COMPUTER_USE_PROFILE
> session file > "fast".
"""
import argparse
import json
import os
import sys

import cu_actions
import cu_target
from cu_motion import (ENV_VAR, PROFILES, JsonParser, get_profile,
                       profile_path, set_profile)
from pathlib import Path



_BUNDLE_VERSION_CACHE = None


def _bundle_version():
    """Nearest ancestor manifest.json with a "name" marker, else ""."""
    global _BUNDLE_VERSION_CACHE
    if _BUNDLE_VERSION_CACHE is not None:
        return _BUNDLE_VERSION_CACHE
    import json as _json
    for parent in Path(__file__).absolute().parents:
        manifest = parent / "manifest.json"
        if manifest.is_file():
            try:
                data = _json.loads(
                    manifest.read_text(encoding="utf-8"))
            except (OSError, ValueError):
                break
            if isinstance(data, dict) and data.get("name"):
                _BUNDLE_VERSION_CACHE = str(data.get("version") or "")
            else:
                _BUNDLE_VERSION_CACHE = ""
            return _BUNDLE_VERSION_CACHE
    _BUNDLE_VERSION_CACHE = ""
    return _BUNDLE_VERSION_CACHE


def _answered_by():
    return {"bundle": _bundle_version(), "wrapper": "computer-use"}


def _stamp(payload):
    if not isinstance(payload, dict):
        return payload
    payload["api_version"] = 2
    if not isinstance(payload.get("meta"), dict):
        payload["meta"] = {}
    payload["meta"].setdefault("answered_by", _answered_by())
    return payload


def _dumps(payload, **kw):
    return json.dumps(_stamp(payload), **kw)

def fail(msg, code=1):
    print(_dumps({"ok": False, "error": msg}))
    sys.exit(code)


def main():
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    target = cu_target.cli_guard(sys.argv[1:])
    if target is not None:
        cu_target.reject_remote(
            f"env {target['env_id']}: remote dispatch not implemented "
            "for profile yet (C12)")
    p = JsonParser(description="computer-use action profile")
    p.add_argument("--set", dest="set_profile", choices=PROFILES,
                   help="persist profile to the session file")
    p.add_argument("--show", action="store_true",
                   help="print effective profile and where it came from")
    p.add_argument("--env", default=None,
                   help="isolated environment id "
                        "(.devin/computer-use/envs); absent = local host")
    args = p.parse_args()

    if args.set_profile:
        set_profile(args.set_profile)
        print(_dumps({"ok": True, "profile": args.set_profile,
                          "path": profile_path()}))
        return

    if args.show:
        env = os.environ.get(ENV_VAR)
        print(_dumps({"ok": True, "profile": get_profile(),
                          "env": env if env in PROFILES else None,
                          "file": profile_path()}))
        return

    # interactive menu — prompts on stderr keep stdout a pure JSON stream
    print("computer-use action profile:", file=sys.stderr)
    desc = {"fast": "instant teleport, zero delay (machine)",
            "smooth": "cinematic eased arc, uniform typing cadence",
            "human": "Fitts/bezier paths, jitter, stochastic keystrokes"}
    for i, n in enumerate(PROFILES, 1):
        cur = " (current)" if get_profile() == n else ""
        print(f"  {i}. {n:6s} — {desc[n]}{cur}", file=sys.stderr)
    try:
        sel = input("choose [1-3 or name]: ").strip().lower()
    except (EOFError, KeyboardInterrupt):
        fail("no selection")
    name = sel if sel in PROFILES else (
        PROFILES[int(sel) - 1] if sel.isdigit() and 1 <= int(sel) <= len(PROFILES)
        else None)
    if not name:
        fail(f"invalid selection: {sel}", 2)
    set_profile(name)
    print(_dumps({"ok": True, "profile": name, "path": profile_path()}))


if __name__ == "__main__":
    cu_actions.run_cli(main)
