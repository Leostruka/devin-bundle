"""MCP stdio server exposing computer-use CLIs to MCP-capable IDEs.

stdlib-only JSON-RPC 2.0 over newline-delimited stdin/stdout (MCP stdio
transport). Thin wrappers over the existing CLIs in this directory; no logic
lives here. Tools:

    cu_status      server/extension info (safe, no side effects)
    cu_screenshot  capture screen/region to PNG
    cu_click       mouse click at coords or UIA hint
    cu_type        type literal text or hotkey chord
    cu_terminal    read a terminal session buffer
    cu_record      short screen recording to webp
    cu_diagnose    extension environment self-check

Usage: python mcp_server.py   (stdio; one JSON-RPC message per line)
"""

import json
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))

PROTOCOL_VERSION = "2024-11-05"
SERVER_INFO = {"name": "devin-computer-use", "version": "1.0.0"}
CALL_TIMEOUT_S = 60


def _cli(script, *args):
    """Run a sibling CLI; return (ok, combined_output)."""
    try:
        proc = subprocess.run(
            [sys.executable, os.path.join(HERE, script), *args],
            capture_output=True, text=True, encoding="utf-8",
            errors="replace", timeout=CALL_TIMEOUT_S, cwd=HERE,
        )
        out = (proc.stdout or "") + (proc.stderr or "")
        return proc.returncode == 0, out.strip()
    except subprocess.TimeoutExpired:
        return False, f"{script} timed out after {CALL_TIMEOUT_S}s"


def _tool_status(_args):
    return True, json.dumps({
        "server": SERVER_INFO,
        "python": sys.version.split()[0],
        "extension": HERE,
        "tools": [t["name"] for t in TOOLS],
    })


def _tool_screenshot(args):
    path = args.get("path", "screenshot.png")
    cli = ["--out", path]
    if args.get("grid"):
        cli.append("--grid")
    return _cli("screenshot.py", *cli)


def _tool_click(args):
    if "hint" in args:
        cli = ["click", "--hint", str(args["hint"])]
    else:
        cli = ["click", str(args["x"]), str(args["y"])]
    if args.get("button"):
        cli += ["--button", args["button"]]
    return _cli("mouse.py", *cli)


def _tool_type(args):
    if "key" in args:
        return _cli("type_text.py", "--key", args["key"])
    return _cli("type_text.py", str(args.get("text", "")))


def _tool_terminal(args):
    sid = args.get("session")
    cli = ["--session", sid] if sid else []
    return _cli("terminal.py", *cli)


def _tool_record(args):
    return _cli("record.py", "--seconds", str(args.get("seconds", 5)),
                "--out", args.get("path", "record.webp"))


def _tool_diagnose(_args):
    return _cli("cu_env.py", "--check")


def _tool_task_start(args):
    cmd = args.get("command")
    if not isinstance(cmd, list) or not cmd:
        return False, "command must be a non-empty list of strings"
    tid = _runner().start([str(c) for c in cmd])
    return True, tid


def _tool_task_status(args):
    st = _runner().status(str(args.get("trace_id", "")))
    return (st is not None), json.dumps(st, indent=1)


def _tool_task_list(_args):
    return True, json.dumps(_runner().list_tasks(), indent=1)


def _tool_task_stop(args):
    st = _runner().stop(str(args.get("trace_id", "")))
    return ("error" not in st), json.dumps(st, indent=1)


def _tool_notify(args):
    res = _notify().notify(str(args.get("title", "")),
                           str(args.get("message", "")),
                           str(args.get("level", "info")))
    return True, json.dumps(res, indent=1)


_runner_mod = None
_notify_mod = None


def _load(name):
    import importlib.util
    spec = importlib.util.spec_from_file_location(
        name, os.path.join(HERE, name + ".py"))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _runner():
    global _runner_mod
    if _runner_mod is None:
        _runner_mod = _load("cu_taskrunner")
    return _runner_mod


def _notify():
    global _notify_mod
    if _notify_mod is None:
        _notify_mod = _load("cu_notify")
    return _notify_mod


def _text(content):
    return {"type": "text", "text": content}


TOOLS = [
    {"name": "cu_status", "description": "Server and extension info. Safe to call first.",
     "inputSchema": {"type": "object", "properties": {}}, "handler": _tool_status},
    {"name": "cu_screenshot", "description": "Capture the screen to a PNG; optional grid overlay.",
     "inputSchema": {"type": "object", "properties": {
         "path": {"type": "string"}, "grid": {"type": "boolean"}}},
     "handler": _tool_screenshot},
    {"name": "cu_click", "description": "Click at absolute coordinates or a UIA hint label.",
     "inputSchema": {"type": "object", "properties": {
         "x": {"type": "integer"}, "y": {"type": "integer"},
         "hint": {"type": "string"}, "button": {"type": "string", "enum": ["left", "right", "middle"]}}},
     "handler": _tool_click},
    {"name": "cu_type", "description": "Type literal text, or a key/hotkey chord via 'key'.",
     "inputSchema": {"type": "object", "properties": {
         "text": {"type": "string"}, "key": {"type": "string"}}},
     "handler": _tool_type},
    {"name": "cu_terminal", "description": "Read a terminal session buffer (all sessions if none given).",
     "inputSchema": {"type": "object", "properties": {
         "session": {"type": "string"}}}, "handler": _tool_terminal},
    {"name": "cu_record", "description": "Record the screen for N seconds to webp.",
     "inputSchema": {"type": "object", "properties": {
         "seconds": {"type": "integer"}, "path": {"type": "string"}}},
     "handler": _tool_record},
    {"name": "cu_diagnose", "description": "Environment self-check. Call first when a tool fails.",
     "inputSchema": {"type": "object", "properties": {}}, "handler": _tool_diagnose},
    {"name": "cu_task_start", "description": "Start a detached background task; returns trace_id.",
     "inputSchema": {"type": "object", "properties": {
         "command": {"type": "array", "items": {"type": "string"}},
     }, "required": ["command"]}, "handler": _tool_task_start},
    {"name": "cu_task_status", "description": "Read a task's lifecycle status.json.",
     "inputSchema": {"type": "object", "properties": {
         "trace_id": {"type": "string"}}, "required": ["trace_id"]},
     "handler": _tool_task_status},
    {"name": "cu_task_list", "description": "List all tasks in the trace store.",
     "inputSchema": {"type": "object", "properties": {}}, "handler": _tool_task_list},
    {"name": "cu_task_stop", "description": "Terminate a running task and its children.",
     "inputSchema": {"type": "object", "properties": {
         "trace_id": {"type": "string"}}, "required": ["trace_id"]},
     "handler": _tool_task_stop},
    {"name": "cu_notify", "description": "Dispatch a notification (file log, toast, webhook, script hook).",
     "inputSchema": {"type": "object", "properties": {
         "title": {"type": "string"}, "message": {"type": "string"},
         "level": {"type": "string", "enum": ["info", "warning", "error"]}},
         "required": ["title", "message"]}, "handler": _tool_notify},
]


def _result(msg_id, result):
    return {"jsonrpc": "2.0", "id": msg_id, "result": result}


def _error(msg_id, code, message):
    return {"jsonrpc": "2.0", "id": msg_id,
            "error": {"code": code, "message": message}}


def _handle(msg):
    method = msg.get("method", "")
    msg_id = msg.get("id")

    if method == "initialize":
        return _result(msg_id, {
            "protocolVersion": PROTOCOL_VERSION,
            "capabilities": {"tools": {}},
            "serverInfo": SERVER_INFO,
        })
    if method == "ping":
        return _result(msg_id, {})
    if method == "tools/list":
        return _result(msg_id, {"tools": [
            {k: t[k] for k in ("name", "description", "inputSchema")}
            for t in TOOLS]})
    if method == "tools/call":
        params = msg.get("params") or {}
        name = params.get("name")
        tool = next((t for t in TOOLS if t["name"] == name), None)
        if not tool:
            return _result(msg_id, {
                "content": [_text(f"unknown tool: {name}")], "isError": True})
        try:
            ok, out = tool["handler"](params.get("arguments") or {})
        except Exception as exc:
            return _result(msg_id, {
                "content": [_text(f"{name} raised: {exc}")], "isError": True})
        return _result(msg_id, {
            "content": [_text(out or "(no output)")], "isError": not ok})
    if method.startswith("notifications/"):
        return None  # notifications take no response
    if msg_id is None:
        return None
    return _error(msg_id, -32601, f"method not found: {method}")


def main():
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        try:
            msg = json.loads(line)
        except json.JSONDecodeError:
            sys.stdout.write(json.dumps(_error(None, -32700, "parse error")) + "\n")
            sys.stdout.flush()
            continue
        resp = _handle(msg)
        if resp is not None:
            sys.stdout.write(json.dumps(resp) + "\n")
            sys.stdout.flush()


if __name__ == "__main__":
    main()
