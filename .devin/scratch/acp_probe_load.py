"""ACP cross-process continuity probe: create session, prompt, kill, reload."""
import json
import os
import subprocess
import sys
import threading
import time

env = dict(os.environ, DEVIN_MODEL="swe-2-max")


class Acp:
    def __init__(self):
        self.proc = subprocess.Popen(
            ["devin", "acp"], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT, env=env, bufsize=0)
        self.out = []
        self.lock = threading.Lock()
        self.nid = 0
        threading.Thread(target=self._reader, daemon=True).start()

    def _reader(self):
        while True:
            line = self.proc.stdout.readline()
            if not line:
                return
            try:
                rec = json.loads(line.decode("utf-8", "replace"))
            except Exception:
                continue
            with self.lock:
                self.out.append(rec)
            if isinstance(rec, dict) and "id" in rec and "method" in rec:
                # Auto-answer server->client requests.
                rid = rec["id"]
                if rec["method"] == "session/request_permission":
                    opts = rec.get("params", {}).get("options", [])
                    allow = opts[0] if opts else {}
                    self._send({"jsonrpc": "2.0", "id": rid, "result":
                                {"outcome": {"outcome": "selected", "optionId": allow.get("optionId", "")}}})
                else:
                    self._send({"jsonrpc": "2.0", "id": rid, "result": {}})

    def _send(self, msg):
        self.proc.stdin.write((json.dumps(msg) + "\n").encode())
        self.proc.stdin.flush()

    def call(self, method, params, timeout=30):
        self.nid += 1
        rid = self.nid
        self._send({"jsonrpc": "2.0", "id": rid, "method": method, "params": params})
        deadline = time.time() + timeout
        while time.time() < deadline:
            with self.lock:
                for rec in self.out:
                    if rec.get("id") == rid and "method" not in rec:
                        return rec
            time.sleep(0.1)
        return None

    def kill(self):
        self.proc.kill()


CAPS = {"protocolVersion": 1, "clientCapabilities":
        {"fs": {"readTextFile": False, "writeTextFile": False}, "terminal": False}}

# Phase 1: session, token prompt, kill.
a = Acp()
print("INIT1:", bool(a.call("initialize", CAPS)))
r = a.call("session/new", {"cwd": os.getcwd(), "mcpServers": []})
sid = r["result"]["sessionId"]
print("SID:", sid)
a.call("session/prompt", {"sessionId": sid, "prompt": [{"type": "text",
       "text": "Remember this token silently: RELOAD-5522. Reply with just OK."}]}, timeout=120)
a.kill()
time.sleep(1)

# Phase 2: new process, session/load same id, ask for the token.
b = Acp()
print("INIT2:", bool(b.call("initialize", CAPS)))
r = b.call("session/load", {"sessionId": sid, "cwd": os.getcwd(), "mcpServers": []}, timeout=30)
print("LOAD:", json.dumps(r)[:300] if r else "TIMEOUT/NONE")
if r and "error" not in r:
    b.call("session/prompt", {"sessionId": sid, "prompt": [{"type": "text",
           "text": "What token did I ask you to remember? Just the token."}]}, timeout=120)
    texts = [rec for rec in b.out if rec.get("method") == "session/update"]
    chunks = []
    for u in texts:
        upd = u.get("params", {}).get("update", {})
        if upd.get("sessionUpdate") == "agent_message_chunk":
            c = upd.get("content", {})
            if c.get("type") == "text":
                chunks.append(c.get("text", ""))
    print("RECALLED:", "".join(chunks)[-300:])
b.kill()
