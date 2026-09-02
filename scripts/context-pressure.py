#!/usr/bin/env python3
"""Context pressure estimator — PostToolUse hook.

Estimates cumulative context-window consumption by tracking tool call
outputs across a session. Writes a marker file with running totals so
each invocation builds on the previous one. Warns to stderr when
estimated usage crosses thresholds (60% warn, 75% critical, 80% clear).

This is a HEURISTIC — it cannot see the actual context window. It estimates
based on:
  1. AGENTS.md token cost (measured once at SessionStart by context-budget.py)
  2. Cumulative tool output sizes (tracked via marker file)
  3. MCP tool-definition overhead (estimated from mcp_config.json)

The video "Context Windows Explained for Coding Agents" (Matt Pocock)
emphasizes: "you really do need full transparency, full understanding of
what is happening in your context window at any time" and "I would
definitely start getting scared once I had about 50K tokens left."

Since Devin CLI does not expose live token counts, this script estimates
from observable signals (tool output sizes, rules file size, MCP config).

Stdin (hook mode):
  {"hook_event_name": "PostToolUse", "tool_name": "exec", "tool_input": {...}, "tool_output": "..."}

Manual:
  python3 context-pressure.py --reset         # clear session marker
  python3 context-pressure.py --report        # show current estimate
  python3 context-pressure.py --model glm-5.2 # use specific model's window

Token estimate: chars/4 heuristic. This is an estimate, not exact.
"""
import sys, os, json, argparse, glob


def devin_home():
    """Return the Devin user config home.

    Windows: %APPDATA%\\devin
    Unix: $XDG_CONFIG_HOME/devin or ~/.config/devin
    """
    appdata = os.environ.get("APPDATA", "")
    if appdata:
        return os.path.join(appdata, "devin")
    xdg = os.environ.get("XDG_CONFIG_HOME", "")
    if xdg:
        return os.path.join(xdg, "devin")
    return os.path.join(os.path.expanduser("~"), ".config", "devin")


CHARS_PER_TOKEN = 4
DEFAULT_WINDOW = 128_000  # GLM-5.2 default; override with --model or data file

# Thresholds from data/model-context-windows.json
WARN_PCT = 60
CRITICAL_PCT = 75
CLEAR_PCT = 80

MARKER_DIR = devin_home()
MARKER_FILE = os.path.join(MARKER_DIR, "context-pressure.json")
MODEL_DATA = None  # loaded lazily


def estimate_tokens(text):
    if not text:
        return 0
    return len(text) // CHARS_PER_TOKEN


def find_bundle_root():
    """Find the devin-bundle root for data files."""
    candidates = []
    env = os.environ.get("DEVIN_PROJECT_DIR")
    if env:
        candidates.append(env)
    candidates.append(os.getcwd())
    candidates.append(devin_home())
    for c in candidates:
        data = os.path.join(c, "data", "model-context-windows.json")
        if os.path.isfile(data):
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
    """Get context window size for a model."""
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
        return WARN_PCT, CRITICAL_PCT, CLEAR_PCT
    t = data.get("thresholds", {})
    return t.get("warn_pct", WARN_PCT), t.get("critical_pct", CRITICAL_PCT), t.get("clear_recommended_pct", CLEAR_PCT)


def estimate_mcp_overhead():
    """Estimate token cost of MCP tool definitions from mcp_config.json."""
    root = find_bundle_root()
    if not root:
        return 0
    mcp_path = os.path.join(root, "mcp_config.json")
    if not os.path.isfile(mcp_path):
        return 0
    try:
        with open(mcp_path, encoding="utf-8", errors="replace") as f:
            config = json.load(f)
    except (OSError, json.JSONDecodeError):
        return 0
    # Each server injects tool definitions. We can't measure them without
    # calling mcp_list_tools, but we can estimate from the config complexity.
    # A typical MCP server with 10 tools adds ~2000-5000 tokens of definitions.
    servers = config.get("mcpServers", {})
    # Conservative estimate: 3000 tokens per configured server
    return len(servers) * 3000


def estimate_rules_cost():
    """Estimate token cost of AGENTS.md."""
    root = find_bundle_root()
    paths_to_check = []
    if root:
        paths_to_check.append(os.path.join(root, "AGENTS.md"))
    paths_to_check.append(os.path.join(devin_home(), "AGENTS.md"))
    for p in paths_to_check:
        if os.path.isfile(p):
            try:
                with open(p, encoding="utf-8", errors="replace") as f:
                    return estimate_tokens(f.read())
            except OSError:
                pass
    return 0


def load_marker():
    try:
        with open(MARKER_FILE, encoding="utf-8", errors="replace") as f:
            return json.load(f)
    except (OSError, json.JSONDecodeError):
        return {"tool_output_tokens": 0, "calls": 0, "session_start": None}


def save_marker(marker):
    try:
        os.makedirs(MARKER_DIR, exist_ok=True)
        with open(MARKER_FILE, "w", encoding="utf-8") as f:
            json.dump(marker, f)
    except OSError:
        pass  # fail-open


def read_stdin():
    try:
        if not sys.stdin.isatty():
            return sys.stdin.read()
    except (OSError, ValueError):
        pass
    return ""


def process_hook(payload_str):
    """Process a PostToolUse hook payload and update the marker."""
    try:
        payload = json.loads(payload_str) if payload_str else {}
    except json.JSONDecodeError:
        payload = {}

    tool_output = payload.get("tool_output", "")
    # tool_output can be a string or structured
    if isinstance(tool_output, dict):
        tool_output = json.dumps(tool_output)
    elif not isinstance(tool_output, str):
        tool_output = str(tool_output)

    output_tokens = estimate_tokens(tool_output)

    marker = load_marker()
    if not marker.get("session_start"):
        import datetime
        marker["session_start"] = datetime.datetime.now().isoformat()

    marker["tool_output_tokens"] = marker.get("tool_output_tokens", 0) + output_tokens
    marker["calls"] = marker.get("calls", 0) + 1

    # Estimate total context
    rules_tokens = estimate_rules_cost()
    mcp_tokens = estimate_mcp_overhead()
    # Estimate conversation overhead: each turn has input + output overhead
    # beyond what we track. Rough: 200 tokens per call for input/metadata.
    conv_overhead = marker["calls"] * 200
    total_est = rules_tokens + mcp_tokens + marker["tool_output_tokens"] + conv_overhead

    # Get model window
    model_id = payload.get("model", "")
    window = get_model_window(model_id)
    warn_pct, critical_pct, clear_pct = get_thresholds()

    pct = 100.0 * total_est / window if window > 0 else 0

    save_marker(marker)

    # Report to stderr (does NOT inject into context — avoids bloat)
    if pct >= warn_pct:
        level = "WARN" if pct < critical_pct else ("CRITICAL" if pct < clear_pct else "CLEAR NOW")
        print(f"context-pressure: {level} — ~{total_est}/{window} tokens ({pct:.0f}%)", file=sys.stderr)
        print(f"  rules: ~{rules_tokens}  mcp: ~{mcp_tokens}  tool-output: ~{marker['tool_output_tokens']}  calls: {marker['calls']}", file=sys.stderr)
        if pct >= clear_pct:
            print(f"  ACTION: clear or compact now. Lost-in-the-middle is severe at {pct:.0f}%.", file=sys.stderr)
            print(f"  Default: clear (blank slate). Use compact only to preserve current task intent.", file=sys.stderr)
        elif pct >= critical_pct:
            print(f"  ACTION: clear or compact soon. Consider context-folding for large docs.", file=sys.stderr)
        else:
            print(f"  Monitor: approaching pressure zone. Plan to clear/compact before {critical_pct}%.", file=sys.stderr)

    return 0


def report():
    marker = load_marker()
    rules_tokens = estimate_rules_cost()
    mcp_tokens = estimate_mcp_overhead()
    conv_overhead = marker.get("calls", 0) * 200
    total_est = rules_tokens + mcp_tokens + marker.get("tool_output_tokens", 0) + conv_overhead
    window = get_model_window()
    warn_pct, critical_pct, clear_pct = get_thresholds()
    pct = 100.0 * total_est / window if window > 0 else 0

    print(f"context-pressure report")
    print(f"  session_start: {marker.get('session_start', 'unknown')}")
    print(f"  tool calls:    {marker.get('calls', 0)}")
    print(f"  rules:         ~{rules_tokens} tokens")
    print(f"  mcp overhead:  ~{mcp_tokens} tokens")
    print(f"  tool output:   ~{marker.get('tool_output_tokens', 0)} tokens")
    print(f"  conv overhead: ~{conv_overhead} tokens")
    print(f"  total est:     ~{total_est} / {window} tokens ({pct:.1f}%)")
    print(f"  thresholds:    warn={warn_pct}%  critical={critical_pct}%  clear={clear_pct}%")
    if pct >= clear_pct:
        print(f"  STATUS: CLEAR NOW — lost-in-the-middle is severe")
    elif pct >= critical_pct:
        print(f"  STATUS: CRITICAL — clear or compact soon")
    elif pct >= warn_pct:
        print(f"  STATUS: WARN — approaching pressure zone")
    else:
        print(f"  STATUS: OK")
    return 0


def reset():
    try:
        os.remove(MARKER_FILE)
        print("context-pressure: marker reset", file=sys.stderr)
    except OSError:
        pass
    return 0


def main():
    global DEFAULT_WINDOW
    ap = argparse.ArgumentParser(description="Context pressure estimator")
    ap.add_argument("--reset", action="store_true", help="clear session marker")
    ap.add_argument("--report", action="store_true", help="show current estimate")
    ap.add_argument("--model", help="model ID for window size (e.g. glm-5.2, claude-haiku-4.5)")
    args = ap.parse_args()

    if args.model:
        DEFAULT_WINDOW = get_model_window(args.model)

    if args.reset:
        sys.exit(reset())
    if args.report:
        sys.exit(report())

    # Hook mode: read stdin
    payload = read_stdin()
    sys.exit(process_hook(payload))


if __name__ == "__main__":
    main()
