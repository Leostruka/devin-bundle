#!/usr/bin/env python3
"""PreToolUse hook: validates tool arguments before execution.

Stdin payload (per /cli/extensibility/hooks/lifecycle-hooks):
  {"hook_event_name": "PreToolUse", "tool_name": "read",
   "tool_input": {...}, "session_id": "...", "prompt_id": "..."}

Exit codes (per /cli/extensibility/hooks/overview#exit-codes):
  0 = allow, 2 = block.

Scope (ALTK SPARC, arXiv:2603.15473, ACM CAIS 2026):
  Validates arguments where hallucinated values cause real failures:
  - Path tools (read/write/edit/notebook_*): absolute path, parent dir exists
  - Search tools (grep/glob/find_file_by_name): regex validity, path exists
  - Network tools (webfetch/web_search): URL scheme, stopword-only queries
  - Delegation tools (run_subagent): profile name against VALID_PROFILES
  - MCP tools (mcp_call_tool/mcp_read_resource): required fields
  - Control tools (skill/request_scope): command/scope enum validation
  - UI tools (ask_user_question/browser_preview/todo_write): required fields,
    option counts, URL scheme, status enum

Excluded (matcher does not fire — tool fails clearly without validation):
  get_output, write_to_process, kill_shell (shell_id presence is trivial),
  read_subagent (agent_id presence is trivial),
  close_browser_preview (preview_id presence is trivial),
  mcp_list_tools, mcp_list_servers (no required args to validate),
  apply_patch (args vary; fail-open), exit_plan_mode (no required args).
  Removing these from the matcher saves Python process spawns with zero
  loss of real validation value.
"""
import sys, json, os, re

VALID_PROFILES = frozenset({
    "architect", "debugger", "domain", "implementer", "issue-tracker",
    "researcher", "reviewer", "subagent_explore", "subagent_general",
    "triage-labels",
})

# A query made up only of stopwords carries no search signal.
STOPWORDS = frozenset({
    "the", "a", "an", "is", "are", "was", "were", "be", "been", "being",
    "to", "of", "in", "on", "at", "by", "for", "with", "from", "and", "or",
    "but", "not", "no", "yes", "do", "did", "does", "it", "this", "that",
})


def block(reason):
    """Emit a block decision and exit with code 2 (deny)."""
    print(json.dumps({"decision": "block", "reason": reason}))
    sys.exit(2)


def require_abs_path(tool_name, file_path, key="file_path"):
    if not file_path:
        block(f"{tool_name} requires {key}.")
    if not isinstance(file_path, str):
        block(f"{tool_name} {key} must be a string, got {type(file_path).__name__}.")
    if not os.path.isabs(file_path):
        block(
            f"{tool_name} {key} must be an absolute path, got '{file_path}'. "
            "Devin CLI file tools require absolute paths."
        )


def check_exec(ti):
    command = ti.get("command", "")
    if not isinstance(command, str) or not command.strip():
        block("exec requires a non-empty command string.")
    if "\x00" in command:
        block("exec command contains a null byte (possible injection).")


def check_read(ti):
    require_abs_path("read", ti.get("file_path", ""))


def check_write(ti):
    file_path = ti.get("file_path", "")
    require_abs_path("write", file_path)
    parent = os.path.dirname(file_path)
    if parent and not os.path.isdir(parent):
        block(
            f"write parent directory does not exist: '{parent}'. "
            "Create it first, or correct the path."
        )


def check_edit(ti):
    require_abs_path("edit", ti.get("file_path", ""))
    if not ti.get("old_string"):
        block("edit requires a non-empty old_string.")
    if ti.get("old_string") == ti.get("new_string"):
        block("edit old_string and new_string are identical; the edit is a no-op.")


def check_notebook_read(ti):
    require_abs_path("notebook_read", ti.get("notebook_path", ""), "notebook_path")


def check_notebook_edit(ti):
    require_abs_path("notebook_edit", ti.get("notebook_path", ""), "notebook_path")


def check_grep(ti):
    pattern = ti.get("pattern", "")
    if not pattern:
        block("grep requires a pattern.")
    try:
        re.compile(pattern)
    except re.error as exc:
        block(f"grep pattern is not a valid regex: {exc}.")
    path = ti.get("path", "")
    if path and not os.path.exists(path):
        block(f"grep path does not exist: '{path}'.")


def check_glob(ti):
    if not ti.get("pattern"):
        block("glob requires a pattern.")
    path = ti.get("path", "")
    if path and not os.path.exists(path):
        block(f"glob path does not exist: '{path}'.")


def check_find_file_by_name(ti):
    if not ti.get("pattern"):
        block("find_file_by_name requires a pattern.")
    path = ti.get("path", "")
    if path and not os.path.exists(path):
        block(f"find_file_by_name path does not exist: '{path}'.")


def check_web_search(ti):
    query = ti.get("query", "")
    if not isinstance(query, str) or not query.strip():
        block("web_search requires a non-empty query.")
    tokens = [t for t in re.findall(r"[a-zA-Z']+", query.lower()) if t]
    if tokens and all(t in STOPWORDS for t in tokens):
        block(f"web_search query contains only stopwords: '{query}'.")


def check_webfetch(ti):
    url = ti.get("url", "")
    if not isinstance(url, str) or not url.strip():
        block("webfetch requires a url.")
    if not url.startswith(("http://", "https://")):
        block(
            f"webfetch url must start with http:// or https://, got '{url[:60]}'."
        )


def check_run_subagent(ti):
    task = ti.get("task", "")
    if not isinstance(task, str) or not task.strip():
        block("run_subagent requires a non-empty task.")
    profile = ti.get("profile", "")
    if profile and profile not in VALID_PROFILES:
        block(
            f"run_subagent profile '{profile}' is not valid. Must be one of: "
            + ", ".join(sorted(VALID_PROFILES))
        )
    is_bg = ti.get("is_background")
    if is_bg is not None and not isinstance(is_bg, bool):
        block("run_subagent is_background must be a boolean if provided.")


def check_mcp_call_tool(ti):
    if not ti.get("server_name"):
        block("mcp_call_tool requires server_name.")
    if not ti.get("tool_name"):
        block("mcp_call_tool requires tool_name.")


def check_mcp_read_resource(ti):
    if not ti.get("server_name"):
        block("mcp_read_resource requires server_name.")
    if not ti.get("resource_uri"):
        block("mcp_read_resource requires resource_uri.")


def check_skill(ti):
    cmd = ti.get("command") or "invoke"
    if cmd not in ("invoke", "list", "search"):
        block("skill command must be 'invoke', 'list', or 'search', got '" + str(cmd) + "'.")


def check_request_scope(ti):
    if not ti.get("scope"):
        block("request_scope requires a scope.")
    if ti.get("scope") not in ("read", "write"):
        block("request_scope scope must be 'read' or 'write'.")
    if not ti.get("path"):
        block("request_scope requires a path.")


def check_mcp_list_tools(ti):
    pass  # server_name is optional; no required args — kept for documentation


def check_mcp_list_servers(ti):
    pass  # no required args — kept for documentation


def check_ask_user_question(ti):
    questions = ti.get("questions")
    if not isinstance(questions, list) or not questions:
        block("ask_user_question requires a non-empty questions array.")
    if len(questions) > 4:
        block(f"ask_user_question supports at most 4 questions, got {len(questions)}.")
    for i, q in enumerate(questions):
        if not isinstance(q, dict):
            block(f"ask_user_question questions[{i}] must be an object.")
        if not q.get("question"):
            block(f"ask_user_question questions[{i}] requires a question.")
        if not q.get("header"):
            block(f"ask_user_question questions[{i}] requires a header.")
        opts = q.get("options")
        if not isinstance(opts, list) or len(opts) < 2:
            block(f"ask_user_question questions[{i}] requires at least 2 options.")
        if len(opts) > 4:
            block(f"ask_user_question questions[{i}] supports at most 4 options, got {len(opts)}.")


def check_browser_preview(ti):
    url = ti.get("url", "")
    if not isinstance(url, str) or not url.strip():
        block("browser_preview requires a url.")
    if not url.startswith(("http://", "https://")):
        block(f"browser_preview url must start with http:// or https://, got '{url[:60]}'.")
    if not ti.get("name"):
        block("browser_preview requires a name.")


def check_todo_write(ti):
    todos = ti.get("todos")
    if not isinstance(todos, list):
        block("todo_write requires a todos array.")
    valid_statuses = {"pending", "in_progress", "completed"}
    in_progress_count = 0
    for i, t in enumerate(todos):
        if not isinstance(t, dict):
            block(f"todo_write todos[{i}] must be an object.")
        if not t.get("content"):
            block(f"todo_write todos[{i}] requires content.")
        status = t.get("status", "")
        if status not in valid_statuses:
            block(f"todo_write todos[{i}] status must be one of {sorted(valid_statuses)}, got '{status}'.")
        if status == "in_progress":
            in_progress_count += 1
    if in_progress_count > 1:
        block(f"todo_write must have exactly ONE in_progress item, got {in_progress_count}.")


CHECKS = {
    "exec": check_exec,
    "read": check_read,
    "write": check_write,
    "edit": check_edit,
    "notebook_read": check_notebook_read,
    "notebook_edit": check_notebook_edit,
    "grep": check_grep,
    "glob": check_glob,
    "find_file_by_name": check_find_file_by_name,
    "web_search": check_web_search,
    "webfetch": check_webfetch,
    "run_subagent": check_run_subagent,
    "mcp_call_tool": check_mcp_call_tool,
    "mcp_read_resource": check_mcp_read_resource,
    "skill": check_skill,
    "request_scope": check_request_scope,
    "ask_user_question": check_ask_user_question,
    "browser_preview": check_browser_preview,
    "todo_write": check_todo_write,
}


def main():
    try:
        data = json.load(sys.stdin)
    except (json.JSONDecodeError, EOFError, ValueError):
        sys.exit(0)  # fail-open

    tool_name = data.get("tool_name", "") or ""
    tool_input = data.get("tool_input") or {}

    if not isinstance(tool_input, dict):
        sys.exit(0)

    check = CHECKS.get(tool_name)
    if check is None:
        sys.exit(0)

    try:
        check(tool_input)
    except SystemExit:
        raise
    except Exception:
        sys.exit(0)  # fail-open on unexpected validator error

    sys.exit(0)


if __name__ == "__main__":
    main()
