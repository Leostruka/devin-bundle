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


def fail(msg, code=1):
    print(json.dumps({"ok": False, "error": msg}))
    sys.exit(code)


def main():
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
        print(json.dumps({"ok": True, "profile": args.set_profile,
                          "path": profile_path()}))
        return

    if args.show:
        env = os.environ.get(ENV_VAR)
        print(json.dumps({"ok": True, "profile": get_profile(),
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
    print(json.dumps({"ok": True, "profile": name, "path": profile_path()}))


if __name__ == "__main__":
    cu_actions.run_cli(main)
