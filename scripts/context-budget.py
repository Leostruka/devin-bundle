#!/usr/bin/env python3
"""Context budget reporter.

Reports the estimated token cost of the rules/context that loads into every
conversation, so the user has transparency analogous to Claude Code's
`/context` command. Writes to STDERR only — it does NOT inject into the
context window, so it never adds bloat (the very thing it measures).

Runs as a SessionStart hook (configured in config.json / hooks.v1.json) and
can also be invoked manually:

  python3 context-budget.py                 # auto-locate AGENTS.md
  python3 context-budget.py AGENTS.md       # explicit file
  python3 context-budget.py --json AGENTS.md

Stdin (hook mode):
  {"hook_event_name": "SessionStart", "source": "..."}
  (stdin is optional; the script works with or without it)

Token estimate uses the chars/4 heuristic. This is an estimate, not an exact
count — exact counts require the model provider's tokenizer.

Source: "Context Windows Explained for Coding Agents" (Matt Pocock) —
  you need full transparency of what is consuming your context window at any
  time. A 25k-token rules file is 12% of a 200k window before the first word.
"""
import sys, os, json, argparse

CHARS_PER_TOKEN = 4
WINDOW_200K = 200_000    # GLM-5.2 High primary model (free)
WINDOW_262K = 262_000    # SWE-1.7 Max subagent model (free, `devin models list`)


def estimate_tokens(text):
    if not text:
        return 0
    return len(text) // CHARS_PER_TOKEN


def find_agents_md():
    """Locate AGENTS.md: project dir, then DEVIN_HOME, then ~/.config/devin."""
    candidates = []
    project = os.environ.get("DEVIN_PROJECT_DIR") or os.getcwd()
    candidates.append(os.path.join(project, "AGENTS.md"))
    home = os.path.expanduser("~")
    candidates.append(os.path.join(home, ".config", "devin", "AGENTS.md"))
    appdata = os.environ.get("APPDATA", "")
    if appdata:
        candidates.append(os.path.join(appdata, "devin", "AGENTS.md"))
    for c in candidates:
        if os.path.isfile(c):
            return c
    return None


def find_extra_rules(path):
    """Find additional rules files that load into context: .devin/global_rules.md
    and .devin/rules/*.md (project) and ~/.config/devin/rules/*.md (global).

    Returns a list of file paths. These are reported alongside AGENTS.md so the
    user has full transparency of context-window consumption (Rule 18).
    """
    extras = []
    project = os.environ.get("DEVIN_PROJECT_DIR") or os.path.dirname(path)
    # Project-level .devin/global_rules.md
    gr = os.path.join(project, ".devin", "global_rules.md")
    if os.path.isfile(gr):
        extras.append(gr)
    # Project-level .devin/rules/*.md
    rules_dir = os.path.join(project, ".devin", "rules")
    if os.path.isdir(rules_dir):
        for f in sorted(os.listdir(rules_dir)):
            if f.endswith(".md"):
                extras.append(os.path.join(rules_dir, f))
    # Global ~/.config/devin/rules/*.md
    home = os.path.expanduser("~")
    global_rules = os.path.join(home, ".config", "devin", "rules")
    if os.path.isdir(global_rules):
        for f in sorted(os.listdir(global_rules)):
            if f.endswith(".md"):
                extras.append(os.path.join(global_rules, f))
    return extras


def report(path, as_json=False):
    try:
        with open(path, encoding="utf-8", errors="replace") as f:
            content = f.read()
    except (OSError, IOError) as e:
        print(f"context-budget: cannot read {path}: {e}", file=sys.stderr)
        return 1
    chars = len(content)
    tok = estimate_tokens(content)
    lines = content.count("\n") + 1
    share_200k = 100.0 * tok / WINDOW_200K
    share_262k = 100.0 * tok / WINDOW_262K

    # Also scan extra rules files for total context budget
    extras = find_extra_rules(path)
    extra_total_tok = 0
    extra_details = []
    for ep in extras:
        try:
            with open(ep, encoding="utf-8", errors="replace") as f:
                ec = f.read()
            et = estimate_tokens(ec)
            extra_total_tok += et
            extra_details.append({"file": ep, "tokens": et})
        except (OSError, IOError):
            pass

    total_tok = tok + extra_total_tok
    total_200k = 100.0 * total_tok / WINDOW_200K
    total_262k = 100.0 * total_tok / WINDOW_262K

    if as_json:
        print(json.dumps({
            "file": path,
            "chars": chars,
            "estimated_tokens": tok,
            "lines": lines,
            "window_200k_share_pct": round(share_200k, 2),
            "window_262k_share_pct": round(share_262k, 2),
            "extra_rules_files": extra_details,
            "extra_rules_tokens": extra_total_tok,
            "total_rules_tokens": total_tok,
            "total_200k_share_pct": round(total_200k, 2),
            "total_262k_share_pct": round(total_262k, 2),
        }))
        return 0
    print(f"context-budget: {path}", file=sys.stderr)
    print(f"  chars:    {chars}", file=sys.stderr)
    print(f"  lines:    {lines}", file=sys.stderr)
    print(f"  tokens:   ~{tok} (chars/4 heuristic)", file=sys.stderr)
    print(f"  200k share (GLM-5.2):  {share_200k:.2f}%", file=sys.stderr)
    print(f"  262k share (SWE-1.7):  {share_262k:.2f}%", file=sys.stderr)
    if extras:
        print(f"  extra rules files: {len(extras)} (~{extra_total_tok} tokens)", file=sys.stderr)
        for ed in extra_details:
            print(f"    - {ed['file']}: ~{ed['tokens']} tokens", file=sys.stderr)
        print(f"  TOTAL rules tokens: ~{total_tok}", file=sys.stderr)
        print(f"  TOTAL 200k share:    {total_200k:.2f}%", file=sys.stderr)
        print(f"  TOTAL 262k share:    {total_262k:.2f}%", file=sys.stderr)
    if total_200k >= 10:
        print(f"  WARN: total rules are >=10% of a 200k window before the first", file=sys.stderr)
        print(f"        message. Consider compressing/modularizing (context-window-hygiene).", file=sys.stderr)
    return 0


def main():
    ap = argparse.ArgumentParser(description="Context budget reporter")
    ap.add_argument("path", nargs="?", help="path to AGENTS.md (auto-located if omitted)")
    ap.add_argument("--json", action="store_true", help="emit JSON to stdout")
    args = ap.parse_args()

    # Drain stdin if present (hook payload) so the hook shell doesn't block.
    try:
        if not sys.stdin.isatty():
            sys.stdin.read()
    except (OSError, ValueError):
        pass

    path = args.path or find_agents_md()
    if not path:
        print("context-budget: no AGENTS.md found", file=sys.stderr)
        sys.exit(0)  # fail-open: not a blocking hook
    sys.exit(report(path, as_json=args.json))


if __name__ == "__main__":
    main()
