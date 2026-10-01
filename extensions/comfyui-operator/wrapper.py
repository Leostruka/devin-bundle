"""comfyui-operator: stdlib HTTP client for a local ComfyUI server.

Commands: status, queue, submit, history, download, upload.
All output is JSON on stdout; errors exit 1 with {"ok": false, ...}.
Server address: env COMFYUI_URL or --url (default http://127.0.0.1:8188).

Workflow files must be ComfyUI *API-format* JSON (the format produced by
"Export (API)" in the UI, or built programmatically): a dict of
node-id -> {"class_type": ..., "inputs": {...}}.
"""
import argparse
import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request
import uuid

DEFAULT_URL = "http://127.0.0.1:8188"


def _out(obj, code=0):
    print(json.dumps(obj, indent=2, sort_keys=True))
    sys.exit(code)


def _fail(msg, **extra):
    _out({"ok": False, "error": msg, **extra}, 1)


def _request(base, method, path, body=None, timeout=30, raw=False):
    url = base.rstrip("/") + path
    data = None
    headers = {}
    if body is not None:
        data = json.dumps(body).encode()
        headers["Content-Type"] = "application/json"
    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            payload = r.read()
            return payload if raw else json.loads(payload.decode("utf-8", "replace"))
    except urllib.error.HTTPError as e:
        detail = e.read().decode("utf-8", "replace")[:500]
        _fail(f"HTTP {e.code} {path}: {detail}")
    except (urllib.error.URLError, TimeoutError, OSError) as e:
        _fail(f"cannot reach ComfyUI at {base}: {e}. "
              "Is the server running? (python main.py --port 8188)")


def cmd_status(base):
    stats = _request(base, "GET", "/system_stats", timeout=10)
    queue = _request(base, "GET", "/queue", timeout=10)
    devices = [{"name": d.get("name"), "type": d.get("type"),
                "vram_total": d.get("vram_total"),
                "vram_free": d.get("vram_free")}
               for d in stats.get("devices", [])]
    _out({"ok": True,
          "server": base,
          "system": stats.get("system", {}),
          "devices": devices,
          "queue_running": len(queue.get("queue_running", [])),
          "queue_pending": len(queue.get("queue_pending", []))})


def cmd_queue(base):
    _out({"ok": True, **_request(base, "GET", "/queue")})


def cmd_submit(base, path, client_id):
    try:
        workflow = json.loads(open(path, encoding="utf-8").read())
    except (OSError, json.JSONDecodeError) as e:
        _fail(f"cannot read workflow {path}: {e}")
    if not isinstance(workflow, dict) or \
            not all(isinstance(v, dict) and "class_type" in v
                    for v in workflow.values()):
        _fail("workflow is not ComfyUI API format "
              "(node-id -> {class_type, inputs}). "
              "Export via 'Save (API Format)' or build programmatically.")
    resp = _request(base, "POST", "/prompt", timeout=60,
                    body={"prompt": workflow, "client_id": client_id})
    _out({"ok": True, "prompt_id": resp.get("prompt_id"),
          "number": resp.get("number")})


def _collect_outputs(entry):
    """Flatten ComfyUI history outputs -> list of file descriptors."""
    files = []
    for node_id, out in (entry.get("outputs") or {}).items():
        for key, val in out.items():
            if isinstance(val, list):
                for item in val:
                    if isinstance(item, dict) and "filename" in item:
                        files.append({"node_id": node_id, "kind": key,
                                      "filename": item["filename"],
                                      "subfolder": item.get("subfolder", ""),
                                      "type": item.get("type", "output")})
    return files


def cmd_history(base, prompt_id):
    hist = _request(base, "GET", f"/history/{prompt_id}", timeout=30)
    entry = hist.get(prompt_id)
    if entry is None:
        _out({"ok": True, "done": False,
              "note": "not in history yet; job may still be queued/running"})
    status = entry.get("status", {})
    _out({"ok": True, "done": status.get("completed", False),
          "status": status,
          "files": _collect_outputs(entry)})


def cmd_download(base, prompt_id, outdir):
    hist = _request(base, "GET", f"/history/{prompt_id}", timeout=30)
    entry = hist.get(prompt_id)
    if entry is None:
        _fail(f"{prompt_id} not in history")
    os.makedirs(outdir, exist_ok=True)
    saved = []
    for f in _collect_outputs(entry):
        q = urllib.parse.urlencode(
            {"filename": f["filename"], "subfolder": f["subfolder"],
             "type": f["type"]})
        blob = _request(base, "GET", f"/view?{q}", timeout=120, raw=True)
        name = f["subfolder"] + f["filename"] if f["subfolder"] \
            else f["filename"]
        dest = os.path.join(outdir, name.replace("/", "_"))
        with open(dest, "wb") as fh:
            fh.write(blob)
        saved.append(dest)
    _out({"ok": True, "saved": saved})


def cmd_upload(base, path):
    """Upload an input file (image/mesh) into ComfyUI's input dir."""
    boundary = uuid.uuid4().hex
    with open(path, "rb") as fh:
        blob = fh.read()
    name = os.path.basename(path)
    body = (b"--" + boundary.encode() + b"\r\n"
            b'Content-Disposition: form-data; name="image"; filename="'
            + name.encode() + b'"\r\n'
            b"Content-Type: application/octet-stream\r\n\r\n"
            + blob + b"\r\n--" + boundary.encode() + b"--\r\n")
    url = base.rstrip("/") + "/upload/image"
    req = urllib.request.Request(
        url, data=body, method="POST",
        headers={"Content-Type": f"multipart/form-data; boundary={boundary}"})
    try:
        with urllib.request.urlopen(req, timeout=120) as r:
            resp = json.loads(r.read().decode())
    except (urllib.error.URLError, OSError) as e:
        _fail(f"upload failed: {e}")
    _out({"ok": True, "uploaded": resp})


def main():
    ap = argparse.ArgumentParser(prog="comfyui-wrapper")
    ap.add_argument("--url", default=os.environ.get("COMFYUI_URL",
                                                    DEFAULT_URL))
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("status")
    sub.add_parser("queue")
    p = sub.add_parser("submit")
    p.add_argument("workflow")
    p.add_argument("--client-id", default="devin-bundle")
    p = sub.add_parser("history")
    p.add_argument("prompt_id")
    p = sub.add_parser("download")
    p.add_argument("prompt_id")
    p.add_argument("--out", default=".")
    p = sub.add_parser("upload")
    p.add_argument("file")
    a = ap.parse_args()

    {"status": lambda: cmd_status(a.url),
     "queue": lambda: cmd_queue(a.url),
     "submit": lambda: cmd_submit(a.url, a.workflow, a.client_id),
     "history": lambda: cmd_history(a.url, a.prompt_id),
     "download": lambda: cmd_download(a.url, a.prompt_id, a.out),
     "upload": lambda: cmd_upload(a.url, a.file)}[a.cmd]()


if __name__ == "__main__":
    main()
