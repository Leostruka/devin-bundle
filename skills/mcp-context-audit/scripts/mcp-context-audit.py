#!/usr/bin/env python3
"""MCP context-cost auditor.

Two modes:

  --config <mcp_config.json>
      Static analysis of the MCP config: lists each server, transport,
      command/url, and a bloat-risk flag. No MCP tool calls are made.

  --tools <tools.json> | --tools - (stdin)
      Estimates the token cost of MCP tool definitions. <tools.json> is the
      JSON array returned by `mcp_list_tools` (a list of tool objects with
      name/description/input_schema). Token cost is estimated as chars/4.

Exit codes: 0 = ok, 1 = usage error, 2 = bloat threshold exceeded (with
--tools, when a server exposes more than 15 tools or estimated tokens exceed
5% of a 200k window).

Usage:
  python3 mcp-context-audit.py --config mcp_config.json
  mcp_list_tools server_name="atlassian" > t.json
  python3 mcp-context-audit.py --tools t.json
  cat t.json | python3 mcp-context-audit.py --tools -
"""
import sys, json, os, re, argparse

# arXiv:2606.30317: tool-selection accuracy >90% requires <10-15 tools/server.
TOOL_COUNT_WARN = 10
TOOL_COUNT_BLOCK = 15

# 5% of a 200k window = 10k tokens of tool definitions is a hard flag.
WINDOW_200K = 200_000
TOKEN_BUDGET_PCT = 0.05
TOKEN_BUDGET = int(WINDOW_200K * TOKEN_BUDGET_PCT)

CHARS_PER_TOKEN = 4  # standard heuristic


def estimate_tokens(char_count):
    """Estimate tokens from a char count (or string length)."""
    if isinstance(char_count, str):
        char_count = len(char_count)
    if not char_count:
        return 0
    return max(1, char_count // CHARS_PER_TOKEN)


def cmd_config(path):
    if not os.path.exists(path):
        print(f"config not found: {path}", file=sys.stderr)
        return 1
    try:
        with open(path, encoding="utf-8-sig") as f:
            cfg = json.load(f)
    except (json.JSONDecodeError, OSError) as e:
        print(f"cannot parse config: {e}", file=sys.stderr)
        return 1
    servers = cfg.get("mcpServers", {}) or {}
    if not servers:
        print("No MCP servers configured.")
        return 0
    print(f"MCP servers configured: {len(servers)}\n")
    for name, scfg in servers.items():
        if not isinstance(scfg, dict):
            print(f"  {name}: (invalid config)")
            continue
        transport = "http" if "url" in scfg else "stdio"
        target = scfg.get("url") or scfg.get("command") or "?"
        # Static bloat heuristic: servers with many args/env keys tend to be
        # heavier; real measurement needs --tools.
        keys = len(scfg)
        risk = "low"
        if keys >= 4:
            risk = "medium"
        if keys >= 6:
            risk = "high"
        print(f"  {name}")
        print(f"    transport: {transport}")
        print(f"    target:    {target}")
        print(f"    config keys: {keys}  (static bloat risk: {risk})")
        print(f"    NOTE: real cost requires `mcp_list_tools` + --tools mode.")
        print()
    print("Run `mcp_list_tools` per server and pass the result to --tools")
    print("to measure actual tool-definition token cost.")
    return 0


def _coerce_tools(data):
    """Accept either a bare list of tools or an object wrapping one."""
    if isinstance(data, list):
        return data
    if isinstance(data, dict):
        for k in ("tools", "result", "data"):
            v = data.get(k)
            if isinstance(v, list):
                return v
        # Single tool object
        if "name" in data:
            return [data]
    return []


def cmd_tools(source):
    raw = sys.stdin.read() if source == "-" else open(source, encoding="utf-8").read()
    try:
        data = json.loads(raw)
    except json.JSONDecodeError as e:
        print(f"cannot parse tools json: {e}", file=sys.stderr)
        return 1
    tools = _coerce_tools(data)
    if not tools:
        print("No tools found in input.", file=sys.stderr)
        return 1
    total_chars = 0
    print(f"Tools: {len(tools)}\n")
    for t in tools:
        if not isinstance(t, dict):
            continue
        name = t.get("name", "?")
        desc = t.get("description", "") or ""
        schema = t.get("input_schema", "") or t.get("inputSchema", "")
        if isinstance(schema, (dict, list)):
            schema = json.dumps(schema)
        tool_chars = len(name) + len(desc) + len(str(schema))
        total_chars += tool_chars
        print(f"  {name}: {tool_chars} chars (~{estimate_tokens(tool_chars)} tok)")
    total_tok = estimate_tokens(total_chars)
    print(f"\nTotal tool-definition chars: {total_chars}")
    print(f"Estimated tokens: ~{total_tok} (chars/4 heuristic)")
    print(f"Window share (200k): {100*total_tok/WINDOW_200K:.2f}%")
    print(f"Budget (5% of 200k): {TOKEN_BUDGET} tok")
    flags = []
    if len(tools) > TOOL_COUNT_BLOCK:
        flags.append(f"tool count {len(tools)} > {TOOL_COUNT_BLOCK} (selection accuracy degrades, arXiv:2606.30317)")
    elif len(tools) > TOOL_COUNT_WARN:
        flags.append(f"tool count {len(tools)} > {TOOL_COUNT_WARN} (warn threshold)")
    if total_tok > TOKEN_BUDGET:
        flags.append(f"token cost {total_tok} > {TOKEN_BUDGET} (5% of 200k window)")
    if flags:
        print("\nBLOAT FLAGS:")
        for fl in flags:
            print(f"  - {fl}")
        return 2
    print("\nWithin budget.")
    return 0


def main():
    ap = argparse.ArgumentParser(description="MCP context-cost auditor")
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--config", metavar="PATH", help="mcp_config.json to analyze")
    g.add_argument("--tools", metavar="PATH", help="tools json from mcp_list_tools (- for stdin)")
    args = ap.parse_args()
    if args.config:
        return cmd_config(args.config)
    return cmd_tools(args.tools)


# --- Code-mode prototype: progressive tool discovery and result filtering ---


def discover_tools_progressive(server_names, all_tools, batch_size=5, budget_tokens=TOKEN_BUDGET):
    """Discover tool definitions in small batches, stopping early if budget is exceeded.

    Direct loading would send every tool definition into the context in one pass.
    Code mode discovers them progressively and only returns the final filtered set.
    """
    discovered = []
    intermediate_tokens = 0
    for i in range(0, len(all_tools), batch_size):
        batch = all_tools[i : i + batch_size]
        for t in batch:
            name = t.get("name", "?")
            desc = t.get("description", "") or ""
            schema = t.get("input_schema", "") or t.get("inputSchema", "")
            if isinstance(schema, (dict, list)):
                schema = json.dumps(schema)
            tok = estimate_tokens(len(name) + len(desc) + len(str(schema)))
            intermediate_tokens += tok
            discovered.append({
                "name": name,
                "description": desc,
                "input_schema": schema,
                "estimated_tokens": tok,
            })
        if intermediate_tokens > budget_tokens:
            break
    return {
        "discovered": discovered,
        "intermediate_tokens": intermediate_tokens,
        "stopped_early": intermediate_tokens > budget_tokens,
    }


def filter_intermediate_results(discovered_tools, required_tool=None):
    """Filter intermediate tool definitions before returning them to the model.

    If a required tool is named, keep only tools whose names, descriptions,
    or schemas mention the same topic. Otherwise return the full filtered set
    with credentials and env values redacted.
    """
    redacted = []
    for t in discovered_tools:
        cleaned = {
            "name": t["name"],
            "description": t["description"],
            "input_schema": _redact_schema(t["input_schema"]),
            "estimated_tokens": t["estimated_tokens"],
        }
        redacted.append(cleaned)

    if not required_tool:
        return redacted

    query = required_tool.lower()
    filtered = [
        t for t in redacted
        if query in t["name"].lower()
        or query in t["description"].lower()
        or query in str(t["input_schema"]).lower()
    ]
    return filtered or redacted


def _redact_schema(schema):
    """Redact any obvious credential or secret fields from a JSON schema string."""
    if not schema:
        return schema
    redacted = schema
    for keyword in ("password", "token", "secret", "key", "credential", "api_key"):
        # Mask the value following the keyword pattern without exposing it.
        redacted = re.sub(
            rf'("{keyword}"[^:]*:[^"\n]*").*?"',
            r'\1<redacted>"',
            redacted,
            flags=re.IGNORECASE,
        )
    return redacted


def _tool_tokens(t):
    name = t.get("name", "?")
    desc = t.get("description", "") or ""
    schema = t.get("input_schema", "") or t.get("inputSchema", "")
    if isinstance(schema, (dict, list)):
        schema = json.dumps(schema)
    return estimate_tokens(len(name) + len(desc) + len(str(schema)))


def compare_code_mode_to_direct(all_tools, budget_tokens=TOKEN_BUDGET):
    """Return token counts for direct loading versus progressive code-mode loading."""
    direct_total = sum(_tool_tokens(t) for t in all_tools)
    progressive = discover_tools_progressive(["*"], all_tools, budget_tokens=budget_tokens)
    filtered = filter_intermediate_results(progressive["discovered"])
    return {
        "direct_tokens": direct_total,
        "intermediate_tokens": progressive["intermediate_tokens"],
        "returned_tools": len(filtered),
        "saved_tokens": direct_total - progressive["intermediate_tokens"],
        "stopped_early": progressive["stopped_early"],
    }


if __name__ == "__main__":
    sys.exit(main())
