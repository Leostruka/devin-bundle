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
  python3 context-budget.py --full          # measure AGENTS.md + MCP + skills dir
  python3 context-budget.py --full --model glm-5.2  # model-aware thresholds

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
WINDOW_200K = 200_000
DEFAULT_WINDOW = 128_000  # GLM-5.2 default

MODEL_DATA = None


def estimate_tokens(text):
    if not text:
        return 0
    return len(text) // CHARS_PER_TOKEN


def find_bundle_root():
    """Find the devin-bundle root for data files and skills."""
    candidates = []
    env = os.environ.get("DEVIN_PROJECT_DIR")
    if env:
        candidates.append(env)
    candidates.append(os.getcwd())
    home = os.path.expanduser("~")
    candidates.append(os.path.join(home, ".config", "devin"))
    for c in candidates:
        if os.path.isfile(os.path.join(c, "AGENTS.md")):
            return c
    return None


def load_model_data():
    global MODEL_DATA
    if MODEL_DATA is not None:
        return MODEL_DATA
    root = find_bundle_root()
    if not root:
        return None
    path = os.path.join(root, "data", "model-context-windows.json")
    try:
        with open(path, encoding="utf-8", errors="replace") as f:
            MODEL_DATA = json.load(f)
            return MODEL_DATA
    except (OSError, json.JSONDecodeError):
        return None


def get_model_window(model_id=None):
    data = load_model_data()
    if not data or not model_id:
        return DEFAULT_WINDOW
    for m in data.get("models", []):
        if model_id.lower() in m.get("id", "").lower() or model_id.lower() in m.get("name", "").lower():
            return m.get("context_window", DEFAULT_WINDOW)
    return DEFAULT_WINDOW


def get_thresholds():
    data = load_model_data()
    if not data:
        return 60, 75, 80
    t = data.get("thresholds", {})
    return t.get("warn_pct", 60), t.get("critical_pct", 75), t.get("clear_recommended_pct", 80)


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


def measure_file(path):
    try:
        with open(path, encoding="utf-8", errors="replace") as f:
            content = f.read()
    except (OSError, IOError):
        return None
    return {
        "path": path,
        "chars": len(content),
        "tokens": estimate_tokens(content),
        "lines": content.count("\n") + 1,
    }


def estimate_mcp_cost():
    """Estimate token cost of MCP tool definitions from mcp_config.json."""
    root = find_bundle_root()
    if not root:
        return {"servers": 0, "estimated_tokens": 0, "details": []}
    mcp_path = os.path.join(root, "mcp_config.json")
    if not os.path.isfile(mcp_path):
        return {"servers": 0, "estimated_tokens": 0, "details": []}
    try:
        with open(mcp_path, encoding="utf-8", errors="replace") as f:
            config = json.load(f)
    except (OSError, json.JSONDecodeError):
        return {"servers": 0, "estimated_tokens": 0, "details": []}
    servers = config.get("mcpServers", {})
    details = []
    total = 0
    for name, cfg in servers.items():
        # Conservative: 3000 tokens per server (tool defs + schema)
        est = 3000
        total += est
        details.append({"server": name, "estimated_tokens": est})
    return {"servers": len(servers), "estimated_tokens": total, "details": details}


def estimate_skills_dir():
    """Estimate total token cost of all SKILL.md files in skills/."""
    root = find_bundle_root()
    if not root:
        return {"skills": 0, "estimated_tokens": 0}
    skills_dir = os.path.join(root, "skills")
    if not os.path.isdir(skills_dir):
        return {"skills": 0, "estimated_tokens": 0}
    total = 0
    count = 0
    for entry in sorted(os.listdir(skills_dir)):
        skill_md = os.path.join(skills_dir, entry, "SKILL.md")
        if os.path.isfile(skill_md):
            m = measure_file(skill_md)
            if m:
                total += m["tokens"]
                count += 1
    return {"skills": count, "estimated_tokens": total}


def report(path, as_json=False):
    m = measure_file(path)
    if not m:
        print(f"context-budget: cannot read {path}", file=sys.stderr)
        return 1
    share = 100.0 * m["tokens"] / WINDOW_200K
    if as_json:
        print(json.dumps({
            "file": m["path"],
            "chars": m["chars"],
            "estimated_tokens": m["tokens"],
            "lines": m["lines"],
            "window_200k_share_pct": round(share, 2),
        }))
        return 0
    print(f"context-budget: {m['path']}", file=sys.stderr)
    print(f"  chars:    {m['chars']}", file=sys.stderr)
    print(f"  lines:    {m['lines']}", file=sys.stderr)
    print(f"  tokens:   ~{m['tokens']} (chars/4 heuristic)", file=sys.stderr)
    print(f"  200k share: {share:.2f}%", file=sys.stderr)
    if share >= 10:
        print(f"  WARN: rules file is >=10% of a 200k window before the first", file=sys.stderr)
        print(f"        message. Consider compressing/modularizing (context-window-hygiene).", file=sys.stderr)
    return 0


def report_full(model_id=None):
    """Full context budget: AGENTS.md + MCP + skills directory."""
    window = get_model_window(model_id)
    warn_pct, critical_pct, clear_pct = get_thresholds()

    agents_path = find_agents_md()
    agents = measure_file(agents_path) if agents_path else None
    mcp = estimate_mcp_cost()
    skills = estimate_skills_dir()

    agents_tok = agents["tokens"] if agents else 0
    total_fixed = agents_tok + mcp["estimated_tokens"]

    print(f"context-budget: FULL REPORT", file=sys.stderr)
    print(f"  model window: {window:,} tokens" + (f" ({model_id})" if model_id else " (default)"), file=sys.stderr)
    print(f"  thresholds:   warn={warn_pct}%  critical={critical_pct}%  clear={clear_pct}%", file=sys.stderr)
    print(f"", file=sys.stderr)

    if agents:
        pct = 100.0 * agents_tok / window
        print(f"  AGENTS.md:     ~{agents_tok:>6} tokens ({pct:.1f}% of window)  [{agents['lines']} lines]", file=sys.stderr)
    else:
        print(f"  AGENTS.md:     not found", file=sys.stderr)

    if mcp["servers"] > 0:
        pct = 100.0 * mcp["estimated_tokens"] / window
        print(f"  MCP overhead:  ~{mcp['estimated_tokens']:>6} tokens ({pct:.1f}% of window)  [{mcp['servers']} servers]", file=sys.stderr)
        for d in mcp["details"]:
            print(f"    - {d['server']}: ~{d['estimated_tokens']} tokens", file=sys.stderr)
    else:
        print(f"  MCP overhead:  0 tokens (no servers configured)", file=sys.stderr)

    pct = 100.0 * skills["estimated_tokens"] / window
    print(f"  Skills dir:    ~{skills['estimated_tokens']:>6} tokens ({pct:.1f}% of window)  [{skills['skills']} skills, on-demand]", file=sys.stderr)
    print(f"", file=sys.stderr)

    pct_total = 100.0 * total_fixed / window
    print(f"  FIXED COST:    ~{total_fixed:>6} tokens ({pct_total:.1f}% of window) — loads every session", file=sys.stderr)
    print(f"  Skills are on-demand: only invoked skills enter context, not all {skills['skills']}.", file=sys.stderr)
    print(f"", file=sys.stderr)

    if pct_total >= clear_pct:
        print(f"  STATUS: CLEAR NOW — fixed cost alone is {pct_total:.0f}% of window.", file=sys.stderr)
        print(f"  Action: reduce AGENTS.md, remove unused MCP servers, compress rules.", file=sys.stderr)
    elif pct_total >= critical_pct:
        print(f"  STATUS: CRITICAL — fixed cost is {pct_total:.0f}% of window.", file=sys.stderr)
        print(f"  Action: audit MCP servers (mcp-context-audit), compress AGENTS.md.", file=sys.stderr)
    elif pct_total >= warn_pct:
        print(f"  STATUS: WARN — fixed cost is {pct_total:.0f}% of window.", file=sys.stderr)
        print(f"  Action: monitor. Plan to reduce before adding more rules/MCP.", file=sys.stderr)
    else:
        print(f"  STATUS: OK — fixed cost is {pct_total:.0f}% of window.", file=sys.stderr)

    return 0


def main():
    ap = argparse.ArgumentParser(description="Context budget reporter")
    ap.add_argument("path", nargs="?", help="path to AGENTS.md (auto-located if omitted)")
    ap.add_argument("--json", action="store_true", help="emit JSON to stdout")
    ap.add_argument("--full", action="store_true", help="full report: AGENTS.md + MCP + skills dir")
    ap.add_argument("--model", help="model ID for window-aware thresholds (e.g. glm-5.2, claude-haiku-4.5)")
    args = ap.parse_args()

    # Drain stdin if present (hook payload) so the hook shell doesn't block.
    try:
        if not sys.stdin.isatty():
            sys.stdin.read()
    except (OSError, ValueError):
        pass

    if args.full:
        sys.exit(report_full(model_id=args.model))

    path = args.path or find_agents_md()
    if not path:
        print("context-budget: no AGENTS.md found", file=sys.stderr)
        sys.exit(0)  # fail-open: not a blocking hook
    sys.exit(report(path, as_json=args.json))


if __name__ == "__main__":
    main()
