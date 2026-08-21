#!/usr/bin/env python3
"""Validates mermaid diagram blocks in write/edit content.

PreToolUse hook for write and edit tools. Scans content for mermaid
fenced blocks, validates each with mermaid.parse() via Node (no Chromium),
and blocks the tool call if any block has invalid syntax.

Stdin payload (PreToolUse):
  {"hook_event_name": "PreToolUse", "tool_name": "write",
   "tool_input": {"content": "...", "file_path": "..."}}
  {"hook_event_name": "PreToolUse", "tool_name": "edit",
   "tool_input": {"new_string": "...", "file_path": "..."}}

Exit codes:
  0 = allow, 2 = block.
"""
import sys, json, os, re, subprocess

MERMAID_FENCE = re.compile(
    r"```mermaid\s*\n(.*?)```",
    re.DOTALL | re.IGNORECASE,
)

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PARSE_CHECK_JS = os.path.join(SCRIPT_DIR, "mermaid-parse-check.js")


def block(reason):
    print(json.dumps({"decision": "block", "reason": reason}))
    sys.exit(2)


def extract_mermaid_blocks(content):
    return MERMAID_FENCE.findall(content)


def validate_block(diagram):
    """Validate a mermaid diagram with mermaid.parse() via Node. Returns (ok, error_msg).

    Fail-open: if Node or mermaid is unavailable (FileNotFoundError) or the
    subprocess times out, return (True, "") — allow the write. Blocking a write
    because the validator can't run is fail-closed and breaks the user's workflow.
    All other hooks in this bundle fail open on tool unavailability.
    """
    try:
        result = subprocess.run(
            ["node", PARSE_CHECK_JS, diagram.strip()],
            capture_output=True,
            text=True,
            timeout=15,
        )
        if result.returncode == 0:
            return True, ""
        err = result.stderr.strip() or result.stdout.strip()
        return False, err[:300]
    except (subprocess.TimeoutExpired, FileNotFoundError) as e:
        # Fail-open: can't validate, don't block the write.
        print(
            f"validate-mermaid: node/mermaid unavailable, skipping validation: {e}",
            file=sys.stderr,
        )
        return True, ""


def main():
    try:
        data = json.load(sys.stdin)
    except (json.JSONDecodeError, EOFError, ValueError):
        sys.exit(0)

    if data.get("hook_event_name") != "PreToolUse":
        sys.exit(0)

    tool_name = data.get("tool_name", "")
    if tool_name not in ("write", "edit"):
        sys.exit(0)

    tool_input = data.get("tool_input") or {}
    if not isinstance(tool_input, dict):
        sys.exit(0)

    content = tool_input.get("content") or tool_input.get("new_string") or ""
    if not content:
        sys.exit(0)

    blocks = extract_mermaid_blocks(content)
    if not blocks:
        sys.exit(0)

    for i, diagram in enumerate(blocks, 1):
        ok, err = validate_block(diagram)
        if not ok:
            block(
                f"Mermaid block {i} of {len(blocks)} has invalid syntax.\n"
                f"Diagram:\n{diagram.strip()[:200]}\n\n"
                f"Parse error:\n{err}"
            )

    sys.exit(0)


if __name__ == "__main__":
    main()
