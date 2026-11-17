"""bridge — uniform command dispatch across the storytold craft suite.

Every craft app exposes the same surface (verified against the repos
and the filmcraft-cli 0.20.1 release binary):
  * `<app>-cli commands [filter] --json` -> catalog listing
  * `<app>-cli exec <id> [json|key=value]` -> headless one-shot command
  * `<app>-cli run <script.jsonl | ->` -> batch, one {"id","params"} per line
  * `<app>-cli mcp`        -> stdio MCP server (JSON-RPC)
  * `--control <port>`     -> JSON-lines TCP control channel (some apps)

This is a THIN bridge, not a new engine: it normalizes
`list_commands(app)` / `run_command(app, command_id, params)` /
`run_script(app, lines)` / `McpClient(app)` over whichever channel the
app's CLI provides. Commands are the app's own registry entries; we
never reimplement operations.

Usage (CLI):
  python bridge.py doctor                      # which CLIs are present
  python bridge.py commands photocraft         # app command catalog
  python bridge.py run photocraft crop '{"w":100,"h":100,"x":0,"y":0}'
  python bridge.py script filmcraft plan.jsonl # batch JSONL (or - for stdin)
"""
from __future__ import annotations

import argparse
import json
import shutil
import socket
import subprocess
import sys

from pathlib import Path

from craft_envelope import _stamp, _dumps


# Verified inventory (gh api users/storytold/repos, 2026-10):
# all craft apps Apache-2.0; spark (npm @sparkjsdev/spark) MIT.
APPS = {
    "filmcraft":   {"cli": "filmcraft-cli",   "domain": "video"},
    "photocraft":  {"cli": "photocraft-cli",  "domain": "image"},
    "vectorcraft": {"cli": "vectorcraft-cli", "domain": "vector"},
    "wordcraft":   {"cli": "wordcraft-cli",   "domain": "doc"},
    "pdfcraft":    {"cli": "pdfcraft-cli",    "domain": "pdf"},
    "gridcraft":   {"cli": "gridcraft-cli",   "domain": "sheet"},
    "deckcraft":   {"cli": "deckcraft-cli",   "domain": "slide"},
    "cadcraft":    {"cli": "cadcraft-cli",    "domain": "cad"},
    "lightcraft":  {"cli": "lightcraft-cli",  "domain": "photo-dev"},
    "soundcraft":  {"cli": "soundcraft-cli",  "domain": "audio"},
}
DOMAIN_TO_APP = {v["domain"]: k for k, v in APPS.items()}

CONTROL_PORTS = {  # defaults; override per attach() call
    "vectorcraft": 7979,
}
TIMEOUT_S = 30


def cli_path(app):
    """Resolve the app's CLI binary on PATH (None when absent)."""
    spec = APPS.get(app)
    if spec is None:
        raise KeyError(f"unknown craft app: {app}")
    if isinstance(spec["cli"], list):
        return spec["cli"][0] if shutil.which(spec["cli"][0]) else None
    return shutil.which(spec["cli"])


def cli_argv(app):
    """Full argv prefix for the app CLI (None when absent).

    `cli` may be a string (binary on PATH) or an argv list (e.g.
    ["cargo", "run", "-p", "filmcraft-cli", "--"]) for dev checkouts.
    """
    spec = APPS.get(app)
    if spec is None:
        raise KeyError(f"unknown craft app: {app}")
    if isinstance(spec["cli"], list):
        return list(spec["cli"]) if shutil.which(spec["cli"][0]) else None
    path = shutil.which(spec["cli"])
    return [path] if path else None


def doctor():
    """Presence report per app: cli found, channels assumed available."""
    out = {}
    for app, spec in APPS.items():
        argv = cli_argv(app)
        out[app] = {
            "cli": spec["cli"], "found": bool(argv),
            "path": cli_path(app),
            "channels": ["cli", "mcp", "control"] if argv else []}
    return out


def list_commands(app, filter=None, timeout=TIMEOUT_S):
    """`<app>-cli commands [filter] --json` -> raw catalog text."""
    cli = cli_argv(app)
    if not cli:
        return {"ok": False, "app": app,
                "error": f"{APPS[app]['cli']} not on PATH"}
    argv = cli + ["commands"]
    if filter:
        argv.append(filter)
    argv.append("--json")
    try:
        p = subprocess.run(argv, capture_output=True,
                           text=True, encoding="utf-8", errors="replace",
                           timeout=timeout, creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
    except (OSError, subprocess.TimeoutExpired) as e:
        return {"ok": False, "app": app, "error": f"{type(e).__name__}"}
    return {"ok": p.returncode == 0, "app": app,
            "stdout": p.stdout, "stderr": p.stderr,
            "exit": p.returncode}


def run_command(app, command_id, params=None, timeout=TIMEOUT_S,
                files=None):
    """Headless one-shot: `<app>-cli exec <id> [<json params>]`.

    Verified against filmcraft-cli 0.20.1: `exec` takes the command id,
    optional key=value args, or one JSON object arg. `files` are appended
    as positional args (real apps take file operands through command
    params like `file.import`, not flags). Returns
    {ok, app, command, stdout, stderr, exit}.
    """
    cli = cli_argv(app)
    if not cli:
        return {"ok": False, "app": app, "command": command_id,
                "error": f"{APPS[app]['cli']} not on PATH"}
    argv = cli + ["exec", command_id]
    if params is not None:
        argv.append(json.dumps(params))
    for f in files or []:
        argv.append(str(f))
    try:
        p = subprocess.run(argv, capture_output=True, text=True,
                           encoding="utf-8", errors="replace",
                           timeout=timeout, creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
    except (OSError, subprocess.TimeoutExpired) as e:
        return {"ok": False, "app": app, "command": command_id,
                "error": f"{type(e).__name__}"}
    return {"ok": p.returncode == 0, "app": app, "command": command_id,
            "stdout": p.stdout, "stderr": p.stderr,
            "exit": p.returncode}


def run_script(app, lines, demo=False, timeout=TIMEOUT_S):
    """Batch path: `<app>-cli run [-]`, one {"id","params"} per line.

    `lines` is a list of dicts (or raw JSONL strings). Per-line results
    come back as {"id","line","ok","result"|"error"} envelopes; a bad
    line does not abort the batch. `demo=True` adds `--demo` for the
    bundled demo project (verified on filmcraft 0.20.1). Returns
    {ok, app, results, stderr, exit}.
    """
    cli = cli_argv(app)
    if not cli:
        return {"ok": False, "app": app,
                "error": f"{APPS[app]['cli']} not on PATH"}
    argv = cli + ["run"]
    if demo:
        argv.append("--demo")
    argv.append("-")
    payload = "\n".join(
        line if isinstance(line, str) else json.dumps(line)
        for line in lines)
    try:
        p = subprocess.run(argv, input=payload, capture_output=True,
                           text=True, encoding="utf-8", errors="replace",
                           timeout=timeout, creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
    except (OSError, subprocess.TimeoutExpired) as e:
        return {"ok": False, "app": app, "error": f"{type(e).__name__}"}
    results = []
    for raw in p.stdout.splitlines():
        raw = raw.strip()
        if raw.startswith("{"):
            try:
                results.append(json.loads(raw))
            except json.JSONDecodeError:
                results.append({"ok": False, "raw": raw})
    return {"ok": p.returncode == 0, "app": app, "results": results,
            "stderr": p.stderr, "exit": p.returncode}


class McpClient:
    """stdio MCP channel: `<app>-cli mcp [--demo]` (JSON-RPC 2.0).

    Handshake is the standard MCP trio: `initialize` ->
    `notifications/initialized` -> `tools/call`. Verified on
    filmcraft-cli 0.20.1: 17 tools incl. command_run/command_batch/
    command_list/doc_inspect/media_import/render_frame. Tool results
    arrive as {"content":[{"type":"text","text":<json>}]} - the text
    payload is parsed back to an object when possible.
    """

    def __init__(self, app, demo=False):
        self.app = app
        cli = cli_argv(app)
        if not cli:
            raise FileNotFoundError(f"{APPS[app]['cli']} not on PATH")
        argv = cli + ["mcp"] + (["--demo"] if demo else [])
        self._proc = subprocess.Popen(
            argv, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
            text=True, encoding="utf-8", errors="replace",
            creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
        self._id = 0
        self._send({"jsonrpc": "2.0", "id": self._next(),
                    "method": "initialize",
                    "params": {"protocolVersion": "2025-06-18",
                               "capabilities": {},
                               "clientInfo": {"name": "craft-bridge",
                                              "version": "1"}}})
        self._send({"jsonrpc": "2.0",
                    "method": "notifications/initialized"})

    def _next(self):
        self._id += 1
        return self._id

    def _send(self, msg):
        self._proc.stdin.write(json.dumps(msg) + "\n")
        self._proc.stdin.flush()

    def _recv(self):
        line = self._proc.stdout.readline()
        if not line:
            return {"ok": False, "app": self.app,
                    "error": "mcp server closed stdout"}
        return json.loads(line)

    def call(self, tool, arguments=None):
        """tools/call -> {"ok", "app", "tool", "result"|"error"}."""
        rid = self._next()
        self._send({"jsonrpc": "2.0", "id": rid, "method": "tools/call",
                    "params": {"name": tool,
                               "arguments": arguments or {}}})
        while True:
            r = self._recv()
            if r.get("id") == rid or ("id" not in r and "error" in r):
                break  # skip server notifications/requests
        result = r.get("result") or {}
        if "error" in r or result.get("isError"):
            return {"ok": False, "app": self.app, "tool": tool,
                    "error": r.get("error", result.get("content"))}
        content = result.get("content") or []
        text = content[0].get("text", "") if content else ""
        try:
            result = json.loads(text)
        except (TypeError, json.JSONDecodeError):
            result = text
        return {"ok": True, "app": self.app, "tool": tool,
                "result": result}

    def command_run(self, command_id, params=None):
        """Run one engine command via the app's `command_run` tool."""
        return self.call("command_run",
                         {"id": command_id, "params": params or {}})

    def tools(self):
        """tools/list -> [tool names]."""
        rid = self._next()
        self._send({"jsonrpc": "2.0", "id": rid,
                    "method": "tools/list", "params": {}})
        while True:
            r = self._recv()
            if r.get("id") == rid or ("id" not in r and "error" in r):
                break
        return [t["name"] for t in
                (r.get("result") or {}).get("tools", [])]

    def close(self):
        try:
            self._proc.stdin.close()
        except OSError:
            pass
        self._proc.terminate()
        try:
            self._proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            self._proc.kill()

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        self.close()


class ControlChannel:
    """JSON-lines TCP channel (`--control <port>` apps, e.g. vectorcraft).

    One message per line each way:
      send {"command": <id>, "params": {...}, "id": <n>}
      recv {"id": <n>, "ok": bool, "result"|"error": ...}
    """

    def __init__(self, app, host="127.0.0.1", port=None, timeout=10):
        self.app = app
        self.host = host
        self.port = port or CONTROL_PORTS.get(app)
        if not self.port:
            raise ValueError(f"no control port known for {app}")
        self.timeout = timeout
        self._seq = 0

    def call(self, command_id, params=None):
        self._seq += 1
        msg = {"id": self._seq, "command": command_id,
               "params": params or {}}
        with socket.create_connection((self.host, self.port),
                                      timeout=self.timeout) as s:
            s.sendall((json.dumps(msg) + "\n").encode("utf-8"))
            buf = b""
            while b"\n" not in buf:
                chunk = s.recv(65536)
                if not chunk:
                    break
                buf += chunk
        line = buf.split(b"\n", 1)[0]
        reply = json.loads(line.decode("utf-8")) if line.strip() else {}
        reply.setdefault("ok", False)
        reply["app"] = self.app
        reply["command"] = command_id
        return reply


def attach(app, host="127.0.0.1", port=None):
    """Attach to a running app's control channel."""
    return ControlChannel(app, host=host, port=port)


def main(argv=None):
    reconfigure = getattr(sys.stdin, "reconfigure", None)
    if reconfigure:
        try:
            reconfigure(encoding="utf-8", errors="replace")
        except (OSError, ValueError):
            pass
    ap = argparse.ArgumentParser(description="craft suite bridge")
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("doctor")
    pc = sub.add_parser("commands")
    pc.add_argument("app")
    pr = sub.add_parser("run")
    pr.add_argument("app")
    pr.add_argument("command_id")
    pr.add_argument("params", nargs="?", default=None)
    pr.add_argument("--file", action="append", default=[])
    ps = sub.add_parser("script")
    ps.add_argument("app")
    ps.add_argument("file", nargs="?", default="-",
                    help="JSONL path, or - for stdin")
    ps.add_argument("--demo", action="store_true")
    args = ap.parse_args(argv)
    if args.cmd == "doctor":
        res = doctor()
        print(_dumps(res, indent=2))
    elif args.cmd == "commands":
        res = list_commands(args.app)
        print(res.get("stdout", _dumps(res)))
    elif args.cmd == "run":
        params = json.loads(args.params) if args.params else None
        res = run_command(args.app, args.command_id, params,
                          files=args.file)
        print(_dumps(res, indent=2))
    elif args.cmd == "script":
        src = (sys.stdin.read() if args.file == "-"
               else Path(args.file).read_text(encoding="utf-8"))
        res = run_script(args.app,
                         [l for l in src.splitlines() if l.strip()],
                         demo=args.demo)
        print(_dumps(res, indent=2))
    return 0 if res.get("ok") else 1


if __name__ == "__main__":
    raise SystemExit(main())
