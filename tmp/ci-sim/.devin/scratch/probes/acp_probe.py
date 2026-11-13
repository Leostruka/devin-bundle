"""Minimal ACP stdio probe: does `devin acp` give a persistent second session?

Sends initialize -> session/new -> session/prompt("PONG") -> a second prompt
on the SAME sessionId to prove in-session continuity. Prints what happened.
"""
import json
import os
import subprocess
import sys
import threading
import time

DEVIN = "devin"
env = dict(os.environ, DEVIN_MODEL="swe-2-max")

proc = subprocess.Popen(
    [DEVIN, "acp"],
    stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
    env=env, bufsize=0,
)

_out = []
_lock = threading.Lock()
_next_id = [0]


def send(method, params, is_response=False, rid=None):
    if is_response:
        msg = {"jsonrpc": "2.0", "id": rid, "result": params}
    else:
        _next_id[0] += 1
        msg = {"jsonrpc": "2.0", "id": _next_id[0], "method": method, "params": params}
    proc.stdin.write((json.dumps(msg) + "\n").encode())
    proc.stdin.flush()
    return msg.get("id")


def reader():
    while True:
        line = proc.stdout.readline()
        if not line:
            with _lock:
                _out.append(("EOF", None))
            return
        try:
            rec = json.loads(line.decode("utf-8", "replace"))
        except Exception:
            rec = {"raw": line.decode("utf-8", "replace")[:300]}
        with _lock:
            _out.append(("msg", rec))
        # Answer server->client requests so the turn can proceed.
        if isinstance(rec, dict) and "id" in rec and "method" in rec:
            if rec["method"] == "session/request_permission":
                opts = rec.get("params", {}).get("options", [])
                allow = next((o for o in opts if "allow" in str(o.get("kind", "")).lower()
                              or "allow" in str(o.get("name", "")).lower()), opts[0] if opts else {})
                send(None, {"outcome": {"outcome": "selected", "optionId": allow.get("optionId", "")}},
                     is_response=True, rid=rec["id"])
            elif rec["method"] in ("fs/read_text_file", "fs/readTextFile"):
                send(None, {"content": ""}, is_response=True, rid=rec["id"])
            else:
                send(None, {}, is_response=True, rid=rec["id"])


def wait_for_response(rid, timeout):
    deadline = time.time() + timeout
    while time.time() < deadline:
        with _lock:
            for tag, rec in _out:
                if tag == "msg" and isinstance(rec, dict) and rec.get("id") == rid and "method" not in rec:
                    return rec
        time.sleep(0.1)
    return None


t = threading.Thread(target=reader, daemon=True)
t.start()

try:
    rid = send("initialize", {"protocolVersion": 1,
                              "clientCapabilities": {"fs": {"readTextFile": False, "writeTextFile": False},
                                                     "terminal": False}})
    r = wait_for_response(rid, 15)
    print("INIT:", json.dumps(r)[:400] if r else "TIMEOUT")
    if not r:
        sys.exit(2)

    rid = send("session/new", {"cwd": os.getcwd(), "mcpServers": []})
    r = wait_for_response(rid, 30)
    print("NEW:", json.dumps(r)[:400] if r else "TIMEOUT")
    sid = (r or {}).get("result", {}).get("sessionId")
    if not sid:
        sys.exit(3)

    rid = send("session/prompt", {"sessionId": sid,
                                  "prompt": [{"type": "text",
                                              "text": "Reply with exactly this token: ACP-PONG-9911. Then stop."}]})
    r = wait_for_response(rid, 120)
    print("PROMPT1:", json.dumps(r)[:400] if r else "TIMEOUT")

    rid = send("session/prompt", {"sessionId": sid,
                                  "prompt": [{"type": "text",
                                              "text": "What token did I ask you to reply with? Just the token."}]})
    r = wait_for_response(rid, 120)
    print("PROMPT2:", json.dumps(r)[:400] if r else "TIMEOUT")

    # Show last few session/update text chunks as evidence of the answer.
    with _lock:
        texts = [rec for tag, rec in _out if tag == "msg" and isinstance(rec, dict)
                 and rec.get("method") == "session/update"]
    chunks = []
    for u in texts[-40:]:
        upd = u.get("params", {}).get("update", {})
        if upd.get("sessionUpdate") == "agent_message_chunk":
            c = upd.get("content", {})
            if c.get("type") == "text":
                chunks.append(c.get("text", ""))
    print("AGENT_TEXT_TAIL:", "".join(chunks)[-500:])
finally:
    proc.kill()
