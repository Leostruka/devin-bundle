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
import sys, os, re, json, argparse, glob


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


def get_parent_model():
    """Read the active parent model from the Devin CLI config, if available.

    The bundle pins `agent.model` to `glm-5-2` by default, but the user may
    have switched to a different model. Use this as the fallback window when
    the hook payload does not provide a model and no data file is present.
    """
    cfg_path = os.path.join(devin_home(), "config.json")
    try:
        with open(cfg_path, encoding="utf-8", errors="replace") as f:
            cfg = json.load(f)
    except (OSError, json.JSONDecodeError):
        return ""
    agent = cfg.get("agent", {})
    if isinstance(agent, dict):
        return agent.get("model", "")
    return ""


CHARS_PER_TOKEN = 4
DEFAULT_WINDOW = 200_000  # GLM-5.2 High default; override with --model or data file
SELECTED_MODEL = None  # set by --model in report mode

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
    """Get context window size for a model.

    If no model is provided, infer the active parent model from the Devin CLI
    config so the estimate matches the real primary model (GLM-5.2 200K by
    default, or the user-selected model).
    """
    data = load_model_data()
    if not model_id:
        model_id = get_parent_model()
    if not model_id:
        return DEFAULT_WINDOW
    if data:
        for m in data.get("models", []):
            mid = m.get("id", "").lower()
            name = m.get("name", "").lower()
            if model_id.lower() in mid or model_id.lower() in name:
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

    # Get model window (hook payload may provide model; otherwise infer from config)
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
    window = get_model_window(SELECTED_MODEL)
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
    global DEFAULT_WINDOW, SELECTED_MODEL
    ap = argparse.ArgumentParser(description="Context pressure estimator")
    ap.add_argument("--reset", action="store_true", help="clear session marker")
    ap.add_argument("--report", action="store_true", help="show current estimate")
    ap.add_argument("--model", help="model ID for window size (e.g. glm-5.2, claude-haiku-4.5)")
    args = ap.parse_args()

    if args.model:
        SELECTED_MODEL = args.model
        DEFAULT_WINDOW = get_model_window(args.model)

    if args.reset:
        sys.exit(reset())
    if args.report:
        sys.exit(report())

    # Hook mode: read stdin
    payload = read_stdin()
    sys.exit(process_hook(payload))


# --- Prompt bloat / refinement cost-benefit gate ---

def measure_permanent_context(root=None):
    """Estimate always-loaded tokens from rules, skills, profiles, and hooks.

    Always-loaded context is the text that is present in every session:
    AGENTS.md (rules), agent profiles, skill SKILL.md files, and hook configs.
    On-demand context (individual tool outputs, user prompt, retrieved memory)
    is not counted here.
    """
    root = root or find_bundle_root() or os.getcwd()
    total_chars = 0
    paths = []
    # Global rules
    agents_md = os.path.join(root, "AGENTS.md")
    if os.path.isfile(agents_md):
        paths.append(agents_md)
    # Agent profiles
    agents_dir = os.path.join(root, "agents")
    if os.path.isdir(agents_dir):
        paths.extend(os.path.join(agents_dir, f) for f in os.listdir(agents_dir) if f.endswith(".md"))
    # Skills
    skills_dir = os.path.join(root, "skills")
    if os.path.isdir(skills_dir):
        for skill in os.listdir(skills_dir):
            skill_md = os.path.join(skills_dir, skill, "SKILL.md")
            if os.path.isfile(skill_md):
                paths.append(skill_md)
    # Hook configs
    for cfg in ("hooks.v1.json", "config.json"):
        p = os.path.join(root, cfg)
        if os.path.isfile(p):
            paths.append(p)
    for p in paths:
        try:
            with open(p, encoding="utf-8", errors="replace") as f:
                total_chars += len(f.read())
        except OSError:
            pass
    return total_chars // CHARS_PER_TOKEN


def evaluate_refinement_cost_benefit(before_tokens, after_tokens, benefit_score,
                                    max_cost_benefit_ratio=1.0, min_benefit=0.05):
    """Decide whether a refinement's permanent context growth is justified.

    benefit_score is a normalized improvement (e.g. 0.1 = 10% better).
    Cost is the token increase. A refinement is rejected when the ratio of
    cost growth to context-window size exceeds the benefit by
    max_cost_benefit_ratio, or when the benefit is below min_benefit.

    Returns a dict with verdict and reason.
    """
    delta = after_tokens - before_tokens
    if delta <= 0:
        return {
            "verdict": "accepted",
            "reason": "no permanent context growth",
            "delta_tokens": delta,
            "benefit_score": benefit_score,
        }
    if benefit_score < min_benefit:
        return {
            "verdict": "rejected",
            "reason": f"benefit {benefit_score:.3f} below minimum {min_benefit}",
            "delta_tokens": delta,
            "benefit_score": benefit_score,
        }
    # Normalize cost by a reference window so the ratio is interpretable.
    reference_window = DEFAULT_WINDOW
    normalized_cost = delta / reference_window
    if normalized_cost > benefit_score * max_cost_benefit_ratio:
        return {
            "verdict": "rejected",
            "reason": f"context cost {normalized_cost:.4f} exceeds benefit {benefit_score:.4f} * {max_cost_benefit_ratio}",
            "delta_tokens": delta,
            "benefit_score": benefit_score,
        }
    return {
        "verdict": "accepted",
        "reason": "context growth justified by measured benefit",
        "delta_tokens": delta,
        "benefit_score": benefit_score,
    }


# --- Task-adaptive harness recipes ---

RECIPES = {
    "audit": {
        "name": "audit",
        "instruction_signals": {"audit", "lint", "validate", "check"},
        "preferred_model": "glm-5-2",
        "tools": ["read", "grep", "exec", "find_file_by_name"],
        "sidekick_profile": "qa-ci",
        "main_responsible_for": ["plan", "final_review"],
    },
    "refine": {
        "name": "refine",
        "instruction_signals": {"refine", "improve", "rewrite", "polish"},
        "preferred_model": "claude-sonnet-4-6",
        "tools": ["read", "edit", "write"],
        "sidekick_profile": "reviewer",
        "main_responsible_for": ["ambiguity_resolution", "final_review"],
    },
    "implement": {
        "name": "implement",
        "instruction_signals": {"implement", "add", "feature", "fix"},
        "preferred_model": "swe-1-7",
        "tools": ["read", "edit", "write", "exec"],
        "sidekick_profile": "implementer",
        "main_responsible_for": ["plan", "ambiguity_resolution", "final_review"],
    },
    "research": {
        "name": "research",
        "instruction_signals": {"research", "find", "compare", "source"},
        "preferred_model": "gemini-3-7-flash",
        "tools": ["web_search", "webfetch", "mcp_call_tool", "read"],
        "sidekick_profile": "researcher",
        "main_responsible_for": ["final_review"],
    },
    "explore": {
        "name": "explore",
        "instruction_signals": {"explore", "understand", "map"},
        "preferred_model": "glm-5-2",
        "tools": ["glob", "find_file_by_name", "read", "grep"],
        "sidekick_profile": "subagent_explore",
        "main_responsible_for": ["plan", "final_review"],
    },
}


def score_recipe(recipe, instruction, tools, model, confidence_threshold=0.25):
    """Score how well a recipe matches task evidence."""
    instruction = (instruction or "").lower()
    tokens = set(re.findall(r"\w+", instruction))
    overlap = len(tokens & recipe["instruction_signals"])
    instruction_score = min(1.0, overlap / max(1, len(recipe["instruction_signals"])))

    tool_score = 0.0
    if tools:
        available = set(t.lower() for t in tools)
        needed = set(t.lower() for t in recipe["tools"])
        tool_score = len(available & needed) / max(1, len(needed))

    model_score = 1.0 if not model or model.lower() in recipe["preferred_model"].lower() else 0.0

    score = 0.5 * instruction_score + 0.3 * tool_score + 0.2 * model_score
    return {
        "recipe": recipe["name"],
        "score": score,
        "instruction_score": instruction_score,
        "tool_score": tool_score,
        "model_score": model_score,
    }


def select_recipe(instruction, tools=None, model=None, recipes=None, confidence_threshold=0.25):
    """Select the best recipe or fall back to the default when uncertain.

    Routing changes are allowed at cache-miss (no confident recipe) or
    compaction boundaries. We do not assume recipes transfer between runtime
    models; the model score is permissive, not mandatory.
    """
    recipes = recipes or RECIPES
    scored = [score_recipe(r, instruction, tools, model) for r in recipes.values()]
    scored.sort(key=lambda x: x["score"], reverse=True)

    best = scored[0] if scored else None
    if best and best["score"] >= confidence_threshold:
        return {
            "verdict": "routed",
            "recipe": best["recipe"],
            "confidence": best["score"],
            "ranking": scored,
        }
    return {
        "verdict": "fallback",
        "recipe": "default",
        "confidence": best["score"] if best else 0.0,
        "reason": "no recipe met the confidence threshold",
        "ranking": scored,
    }


def evaluate_recipe_against_baseline(recipe_name, task_score, baseline_score, context_budget_tokens, estimated_tokens):
    """Return whether a selected recipe is worth using over the static baseline."""
    if estimated_tokens > context_budget_tokens:
        return {
            "verdict": "rejected",
            "reason": "estimated context exceeds budget",
            "delta_tokens": estimated_tokens - context_budget_tokens,
        }
    if task_score < baseline_score:
        return {
            "verdict": "rejected",
            "reason": "recipe underperforms static baseline",
            "delta_score": task_score - baseline_score,
        }
    return {
        "verdict": "accepted",
        "reason": "recipe matches or beats baseline within budget",
        "delta_score": task_score - baseline_score,
    }


if __name__ == "__main__":
    main()
