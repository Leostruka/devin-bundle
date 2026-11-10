import subprocess, json, threading, queue, sys, time

AGENT = sys.argv[1] if len(sys.argv) > 1 else "review"
PROMPT_FILE = sys.argv[2] if len(sys.argv) > 2 else None

p = subprocess.Popen(["devin", "acp", "--agent-type", AGENT],
                     stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                     stderr=subprocess.PIPE, text=True,
                     encoding="utf-8", errors="replace", bufsize=1)
q, eq = queue.Queue(), queue.Queue()
threading.Thread(target=lambda: [q.put(l) for l in p.stdout], daemon=True).start()
threading.Thread(target=lambda: [eq.put(l) for l in p.stderr], daemon=True).start()

seq = [0]
def send(method, params=None, is_notif=False):
    seq[0] += 1
    m = {"jsonrpc": "2.0", "method": method}
    if not is_notif:
        m["id"] = seq[0]
    if params is not None:
        m["params"] = params
    p.stdin.write(json.dumps(m) + "\n")
    p.stdin.flush()
    return m.get("id")

def wait_for(rid, timeout=60):
    got = []
    t0 = time.time()
    while time.time() - t0 < timeout:
        try:
            l = q.get(timeout=max(1, timeout - (time.time() - t0))).strip()
        except queue.Empty:
            break
        if not l:
            continue
        got.append(l)
        try:
            d = json.loads(l)
        except Exception:
            continue
        if d.get("id") == rid:
            return d, got
    return None, got

send("initialize", {"protocolVersion": 1,
                    "clientCapabilities": {"fs": {"readTextFile": True,
                                                  "writeTextFile": False}}})
resp, _ = wait_for(1)
print("INIT:", json.dumps(resp)[:300] if resp else "TIMEOUT")

send("initialized", {}, is_notif=True)
send("authenticate", {"methodId": "env"})
resp2, _ = wait_for(2, timeout=15)
print("AUTH:", json.dumps(resp2)[:200] if resp2 else "skip")

rid3 = send("session/new", {"cwd": "D:/Programing/ai_workspace/devin-bundle",
                            "mcpServers": []})
resp3, extra = wait_for(rid3, timeout=30)
print("SESSION:", json.dumps(resp3)[:400] if resp3 else "TIMEOUT")
if not (resp3 and resp3.get("result")):
    print("extra:", [x[:150] for x in extra])
    p.kill(); sys.exit(1)

sid = resp3["result"].get("sessionId")
MODE = sys.argv[3] if len(sys.argv) > 3 else None
if MODE:
    ridm = send("session/set_mode", {"sessionId": sid, "modeId": MODE})
    respm, _ = wait_for(ridm, timeout=15)
    print("MODE:", json.dumps(respm)[:200] if respm else "TIMEOUT")
text = open(PROMPT_FILE, encoding="utf-8").read() if PROMPT_FILE else \
    "Review this diff for bugs:\n```diff\n+def divide(a,b):\n+    return a/b\n+x = divide(10, 0)\n```"
rid4 = send("session/prompt", {"sessionId": sid,
                               "prompt": [{"type": "text", "text": text}]})
chunks, final = [], None
t0 = time.time()
while time.time() - t0 < 300:
    try:
        l = q.get(timeout=240).strip()
    except queue.Empty:
        break
    try:
        d = json.loads(l)
    except Exception:
        continue
    upd = (d.get("params") or {}).get("update") or {}
    if upd.get("sessionUpdate") == "agent_message_chunk":
        chunks.append((upd.get("content") or {}).get("text", ""))
    elif d.get("method") and "id" in d:
        print("SERVER->CLIENT REQ:", d.get("method"), json.dumps(d.get("params"))[:200])
        # auto-answer fs/read_text_file so ask/plan modes don't deadlock
        if d.get("method") == "fs/read_text_file":
            path = (d.get("params") or {}).get("path", "")
            try:
                body = open(path, encoding="utf-8", errors="replace").read()
            except OSError as e:
                send("requests/deny", None, is_notif=True)
                body = None
            if body is not None:
                p.stdin.write(json.dumps({"jsonrpc": "2.0", "id": d["id"],
                    "result": {"content": body}}) + "\n")
                p.stdin.flush()
    if d.get("id") == rid4:
        final = d
        break
print("REVIEW:", "".join(chunks)[:2000] or "(no chunks)")
print("FINAL:", json.dumps(final)[:200] if final else "none")
try:
    print("STDERR:", eq.get_nowait()[:300])
except queue.Empty:
    pass
p.kill()
