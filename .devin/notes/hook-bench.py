import json, subprocess, time, glob, os, sys

N = int(sys.argv[1]) if len(sys.argv) > 1 else 10
OUT = sys.argv[2] if len(sys.argv) > 2 else ".devin/notes/hook-bench-baseline.json"

res = {}
payloads = {
    "exec": '{"tool_name":"exec","tool_input":{"command":"git status"}}',
    "write": '{"tool_name":"write","tool_input":{"file_path":"x.py","content":"a"}}',
    "prompt": '{"hook_event_name":"UserPromptSubmit","prompt":"hello"}',
    "stop": '{"hook_event_name":"Stop","stop_hook_active":false}',
}
def key_for(s):
    b = os.path.basename(s)
    if "nudge" in b or "retrieval" in b or "pinning" in b or "budget" in b:
        return "prompt"
    if "stop" in b or "refine" in b:
        return "stop"
    if "mermaid" in b or "edit" in b:
        return "write"
    return "exec"

for s in sorted(glob.glob("scripts/*.py")):
    k = key_for(s)
    ts = []
    for _ in range(N):
        t = time.perf_counter()
        subprocess.run([sys.executable, s], input=payloads[k], capture_output=True, text=True)
        ts.append(round((time.perf_counter() - t) * 1000))
    res[os.path.basename(s)] = ts

json.dump(res, open(OUT, "w"), indent=1)
print({k: f"{sum(v)/len(v):.0f}ms" for k, v in res.items()})
