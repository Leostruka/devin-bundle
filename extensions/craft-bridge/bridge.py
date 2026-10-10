"""bridge — uniform command dispatch across the storytold craft suite.

Every craft app exposes the same trio (verified against the repos):
  * `<app>-cli commands`   -> catalog listing
  * `<app>-cli run ...`    -> headless one-shot command execution
  * `<app>-cli mcp`        -> stdio MCP server (JSON-RPC)
  * `--control <port>`     -> JSON-lines TCP control channel (some apps)

This is a THIN bridge, not a new engine: it normalizes
`list_commands(app)` / `run_command(app, command_id, params)` over
whichever channel the app's CLI provides. Commands are the app's own
registry entries; we never reimplement operations.

Usage (CLI):
  python bridge.py doctor                      # which CLIs are present
  python bridge.py commands photocraft         # app command catalog
  python bridge.py run photocraft crop '{"w":100,"h":100,"x":0,"y":0}'
"""
from __future__ import annotations

import argparse
import json
import shutil
import socket
import subprocess
import sys
from pathlib import Path

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


def list_commands(app, timeout=TIMEOUT_S):
    """`<app>-cli commands` -> raw catalog text (format is app-owned)."""
    cli = cli_argv(app)
    if not cli:
        return {"ok": False, "app": app,
                "error": f"{APPS[app]['cli']} not on PATH"}
    try:
        p = subprocess.run(cli + ["commands"], capture_output=True,
                           text=True, timeout=timeout)
    except (OSError, subprocess.TimeoutExpired) as e:
        return {"ok": False, "app": app, "error": f"{type(e).__name__}"}
    return {"ok": p.returncode == 0, "app": app,
            "stdout": p.stdout, "stderr": p.stderr,
            "exit": p.returncode}


def run_command(app, command_id, params=None, timeout=TIMEOUT_S,
                files=None):
    """Headless one-shot: `<app>-cli run --command <id> [--params <json>]`.

    params dict serializes to JSON on argv; `files` (input/output paths)
    pass through as repeated --file args for apps that take positional
    file operands. Returns {ok, app, command, stdout, stderr, exit}.
    """
    cli = cli_argv(app)
    if not cli:
        return {"ok": False, "app": app, "command": command_id,
                "error": f"{APPS[app]['cli']} not on PATH"}
    argv = cli + ["run", "--command", command_id]
    if params:
        argv += ["--params", json.dumps(params)]
    for f in files or []:
        argv += ["--file", str(f)]
    try:
        p = subprocess.run(argv, capture_output=True, text=True,
                           timeout=timeout)
    except (OSError, subprocess.TimeoutExpired) as e:
        return {"ok": False, "app": app, "command": command_id,
                "error": f"{type(e).__name__}"}
    return {"ok": p.returncode == 0, "app": app, "command": command_id,
            "stdout": p.stdout, "stderr": p.stderr,
            "exit": p.returncode}


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
    args = ap.parse_args(argv)
    if args.cmd == "doctor":
        print(json.dumps(doctor(), indent=2))
    elif args.cmd == "commands":
        r = list_commands(args.app)
        print(r.get("stdout", json.dumps(r)))
    elif args.cmd == "run":
        params = json.loads(args.params) if args.params else None
        print(json.dumps(run_command(args.app, args.command_id, params,
                                     files=args.file), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
