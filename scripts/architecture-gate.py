#!/usr/bin/env python3
"""PreToolUse hook: blocks source edits in projects without an architecture manifest.

Stdin payload (per Devin CLI docs /cli/extensibility/hooks/lifecycle-hooks):
  {"hook_event_name": "PreToolUse", "tool_name": "write",
   "tool_input": {...}, "session_id": "...", "prompt_id": "..."}

Exit codes (per Devin CLI docs /cli/extensibility/hooks/overview#exit-codes):
  0 = allow, 2 = block, other = error (logged, does not block).

Gate: a Devin-managed project (any ancestor dir containing .devin/) must have
.devin/ARCHITECTURE_MANIFEST.md before source files may be written. When the
manifest is missing the agent is told to suspend code edits and elicit the
architecture from the user (grilling skill or direct questions).

Scope:
  - write/edit/notebook_edit: blocked when the target path lives inside a
    .devin-managed project that lacks the manifest — except paths inside
    .devin/ itself (manifest, ledgers, notes are agent config, not source).
  - exec: blocked only for commands that mutate the source tree (redirects,
    cp/mv/rm, sed -i, mkdir, touch, Set-Content, etc.). Read-only commands
    (ls, cat, grep, git, pytest, cargo, python) pass — the agent must stay
    free to investigate before proposing an architecture.
  - Escape hatch: any exec command mentioning ARCHITECTURE_MANIFEST is
    allowed so the manifest can be created via shell.
  - Projects without a .devin/ ancestor are not gated.
  - Fail-open on any error.
"""
import sys, json, os, re

MANIFEST_NAME = "ARCHITECTURE_MANIFEST.md"
WRITE_TOOLS = {"write", "edit", "notebook_edit"}

# Shell-level source mutations. Read-only tools are intentionally absent.
MUTATING_PATTERNS = [
    r"(?<![<>=!&|-])>{1,2}(?![>=|])",  # > or >> file redirect (not ->, >=, 2>&1)
    r"\btee\b",
    r"\bsed\s+-i\b",
    r"\bperl\s+-[a-zA-Z]*p[a-zA-Z]*i\b",
    r"\b(?:mkdir|touch|install|patch)\b",
    r"\b(?:cp|mv|rm)\b",
    r"\b(?:del|erase|copy|move|ren|rename)\b",
    r"\bRemove-Item\b",
    r"\b(?:New-Item|Set-Content|Add-Content|Out-File)\b",
]
MUTATING_RE = re.compile("|".join(MUTATING_PATTERNS), re.IGNORECASE)

SQUOTED_RE = re.compile(r"'[^']*'")
DQUOTED_RE = re.compile(r'"[^"]*"')


def block(reason):
    """Emit a block decision and exit with code 2 (deny)."""
    print(json.dumps({"decision": "block", "reason": reason}))
    sys.exit(2)


def find_project_root(start):
    """Walk up from `start`; return the first ancestor containing .devin/."""
    d = os.path.abspath(start)
    while True:
        if os.path.isdir(os.path.join(d, ".devin")):
            return d
        parent = os.path.dirname(d)
        if parent == d:
            return None
        d = parent


def manifest_path(root):
    return os.path.join(root, ".devin", MANIFEST_NAME)


def is_inside(path, directory):
    try:
        return os.path.commonpath([os.path.abspath(path), os.path.abspath(directory)]) == os.path.abspath(directory)
    except ValueError:
        return False  # different drives on Windows


def check_write_edit(tool_input):
    file_path = tool_input.get("file_path", "") or tool_input.get("notebook_path", "")
    if not file_path or not isinstance(file_path, str):
        return
    if os.path.basename(file_path) == MANIFEST_NAME:
        return  # creating the manifest is always allowed
    root = find_project_root(os.path.dirname(file_path))
    if not root:
        return  # not a managed project
    if is_inside(file_path, os.path.join(root, ".devin")):
        return  # .devin/ contents are agent config, not source code
    if not os.path.isfile(manifest_path(root)):
        block(
            f"Architecture gate: '{root}' has no .devin/{MANIFEST_NAME}. "
            "Suspend source edits. Elicit the architecture from the user "
            "(invoke the 'grilling' skill or ask directly), then create "
            f".devin/{MANIFEST_NAME} from the template at "
            "docs/templates/ARCHITECTURE_MANIFEST.md."
        )


def check_exec(tool_input):
    command = tool_input.get("command", "") or ""
    if not command.strip():
        return
    if MANIFEST_NAME in command:
        return  # escape hatch: allow creating the manifest via shell
    # Strip quoted spans so prose inside -m "a > b" does not false-positive.
    scan = DQUOTED_RE.sub('""', SQUOTED_RE.sub("''", command))
    if not MUTATING_RE.search(scan):
        return  # read-only command — always allowed
    root = find_project_root(tool_input.get("workdir") or os.getcwd())
    if not root:
        return
    if not os.path.isfile(manifest_path(root)):
        block(
            f"Architecture gate: '{root}' has no .devin/{MANIFEST_NAME}. "
            "Source mutations are blocked until it exists. Suspend code "
            "changes, elicit the architecture from the user (invoke the "
            f"'grilling' skill or ask directly), then create .devin/{MANIFEST_NAME} "
            "from the template at docs/templates/ARCHITECTURE_MANIFEST.md."
        )


def main():
    try:
        data = json.load(sys.stdin)
    except (json.JSONDecodeError, EOFError, ValueError):
        sys.exit(0)  # fail-open

    tool_name = data.get("tool_name", "")
    tool_input = data.get("tool_input") or {}
    if not isinstance(tool_input, dict):
        sys.exit(0)

    try:
        if tool_name in WRITE_TOOLS:
            check_write_edit(tool_input)
        elif tool_name == "exec":
            check_exec(tool_input)
    except SystemExit:
        raise
    except Exception:
        pass  # fail-open: a gate bug must never block work

    sys.exit(0)


if __name__ == "__main__":
    main()
