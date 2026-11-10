import subprocess, json, threading, queue, sys, time
p = subprocess.Popen(["devin","acp","--agent-type","codemap"], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, text=True, encoding="utf-8", errors="replace", bufsize=1)
q = queue.Queue()
threading.Thread(target=lambda: [q.put(l) for l in p.stdout], daemon=True).start()
seq=[0]
def send(m):
    seq[0]+=1
    if 'id' in m: pass
    else: m['id']=seq[0]
    m['jsonrpc']='2.0'
    p.stdin.write(json.dumps(m)+'\n'); p.stdin.flush()
send({"id":1,"method":"initialize","params":{"protocolVersion":1,"clientCapabilities":{"fs":{"readTextFile":True,"writeTextFile":False},"terminal":True}}})
send({"method":"initialized","params":{}}); send({"id":2,"method":"authenticate","params":{"methodId":"env"}})
send({"id":3,"method":"session/new","params":{"cwd":"D:/Programing/ai_workspace/devin-bundle","mcpServers":[]}})
sid=None; t0=time.time(); out=open('.devin/scratch/acp-spike/codemap_stream.jsonl','w',encoding='utf-8')
while time.time()-t0<600:
    try: l=q.get(timeout=60).strip()
    except queue.Empty: print('idle 60s at',round(time.time()-t0)); continue
    out.write(l+'\n'); out.flush()
    try: d=json.loads(l)
    except: continue
    if d.get('id')==3 and d.get('result'): sid=d['result'].get('sessionId'); send({"id":4,"method":"session/prompt","params":{"sessionId":sid,"prompt":[{"type":"text","text":"Generate the code map for this repository: main modules, entry points, and how they connect."}]}}); print('prompted, sid=',sid)
    if d.get('id')==4: print('PROMPT DONE', json.dumps(d)[:200]); break
p.kill(); out.close()
