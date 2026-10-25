"""Protocol-level tests for the computer-use MCP stdio server."""

import json
import os
import subprocess
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SERVER = os.path.join(REPO, "extensions", "computer-use", "mcp_server.py")


def _rpc(lines, timeout=20):
    """Send newline-delimited JSON-RPC lines; return parsed responses."""
    proc = subprocess.run(
        [sys.executable, SERVER], input="\n".join(lines) + "\n",
        capture_output=True, text=True, timeout=timeout,
    )
    assert proc.returncode == 0, proc.stderr
    return [json.loads(l) for l in proc.stdout.strip().splitlines() if l.strip()]


def test_initialize_and_list():
    resps = _rpc([
        json.dumps({"jsonrpc": "2.0", "id": 1, "method": "initialize",
                    "params": {}}),
        json.dumps({"jsonrpc": "2.0", "method": "notifications/initialized"}),
        json.dumps({"jsonrpc": "2.0", "id": 2, "method": "tools/list"}),
    ])
    assert len(resps) == 2  # notification produces no response
    init, listing = resps
    assert init["result"]["serverInfo"]["name"] == "devin-computer-use"
    names = {t["name"] for t in listing["result"]["tools"]}
    assert {"cu_status", "cu_screenshot", "cu_click", "cu_type",
            "cu_terminal", "cu_record", "cu_diagnose"} <= names
    for t in listing["result"]["tools"]:
        assert "inputSchema" in t and "description" in t


def test_ping_and_unknown_method():
    resps = _rpc([
        json.dumps({"jsonrpc": "2.0", "id": 1, "method": "ping"}),
        json.dumps({"jsonrpc": "2.0", "id": 2, "method": "nope/missing"}),
    ])
    assert resps[0]["result"] == {}
    assert resps[1]["error"]["code"] == -32601


def test_tools_call_status_and_unknown_tool():
    resps = _rpc([
        json.dumps({"jsonrpc": "2.0", "id": 1, "method": "tools/call",
                    "params": {"name": "cu_status", "arguments": {}}}),
        json.dumps({"jsonrpc": "2.0", "id": 2, "method": "tools/call",
                    "params": {"name": "cu_bogus", "arguments": {}}}),
    ])
    ok, bad = resps
    assert ok["result"]["isError"] is False
    payload = json.loads(ok["result"]["content"][0]["text"])
    assert payload["server"]["name"] == "devin-computer-use"
    assert "cu_status" in payload["tools"]
    assert bad["result"]["isError"] is True
    assert "unknown tool" in bad["result"]["content"][0]["text"]


def test_malformed_line_returns_parse_error():
    resps = _rpc(["not json"])
    assert resps[0]["error"]["code"] == -32700
