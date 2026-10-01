#!/usr/bin/env python3
"""blender_server: in-Blender exec server for blender-operator.

Run by the wrapper as:

    blender -b --factory-startup --python blender_server.py -- --port 19693

Blender stays alive because this script blocks in an accept loop on
127.0.0.1:PORT. Protocol is newline-delimited JSON (JSONL over TCP):

    request : {"id": "w1", "op": "ping"}            -> {"id","ok","blender"}
              {"id": "w1", "op": "exec", "code": "..."}
                                                 -> {"id","ok","result","stdout",
                                                     "stderr","error"}
              {"id": "w1", "op": "shutdown"}       -> {"id","ok"} then exits

exec semantics: `code` is compiled; if it parses as an expression it is
eval()ed and repr() returned in "result"; otherwise it is exec()ed in a
persistent namespace preloaded with `bpy`. If the code assigns `_result`,
its value is JSON-serialized into "result_json" (fallback: repr). stdout/
stderr of the executed code are captured and truncated to 64KB each.
"""
import contextlib
import io
import json
import socket
import sys
import traceback

import bpy  # noqa: F401  (preloaded into the exec namespace)

MAX_STREAM = 65536
NS = {"bpy": bpy, "_result": None}


def _run_exec(code):
    buf_out, buf_err = io.StringIO(), io.StringIO()
    result, result_json, error = None, None, None
    NS["_result"] = None
    try:
        with contextlib.redirect_stdout(buf_out), \
                contextlib.redirect_stderr(buf_err):
            try:
                result = eval(compile(code, "<agent>", "eval"), NS)
            except SyntaxError:
                exec(compile(code, "<agent>", "exec"), NS)
        if NS.get("_result") is not None:
            try:
                result_json = json.dumps(NS["_result"], default=repr)
            except (TypeError, ValueError):
                result_json = json.dumps(repr(NS["_result"]))
    except Exception:
        error = traceback.format_exc(limit=8)
    return {
        "result": None if result is None else repr(result)[:8192],
        "result_json": result_json,
        "stdout": buf_out.getvalue()[-MAX_STREAM:],
        "stderr": buf_err.getvalue()[-MAX_STREAM:],
        "error": error,
    }


def _handle(req):
    op = req.get("op", "exec")
    if op == "ping":
        return {"ok": True, "blender": bpy.app.version_string,
                "scene": bpy.context.scene.name if bpy.context.scene else None}
    if op == "shutdown":
        return {"ok": True, "shutdown": True}
    if op == "exec":
        code = req.get("code")
        if not isinstance(code, str):
            return {"ok": False, "error": "missing 'code' string"}
        out = {"ok": True}
        out.update(_run_exec(code))
        if out["error"]:
            out["ok"] = False
        return out
    return {"ok": False, "error": f"unknown op '{op}'"}


def serve(port):
    srv = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    srv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    srv.bind(("127.0.0.1", port))
    srv.listen(4)
    print(f"[blender_server] listening on 127.0.0.1:{port}", flush=True)
    while True:
        conn, _ = srv.accept()
        with conn:
            f = conn.makefile("rw", encoding="utf-8", newline="\n")
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    req = json.loads(line)
                except json.JSONDecodeError as e:
                    f.write(json.dumps({"ok": False,
                                        "error": f"bad json: {e}"}) + "\n")
                    f.flush()
                    continue
                resp = _handle(req)
                resp["id"] = req.get("id")
                f.write(json.dumps(resp, default=repr) + "\n")
                f.flush()
                if req.get("op") == "shutdown":
                    srv.close()
                    bpy.ops.wm.quit_blender()
                    return


def _argv_tail():
    return sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []


if __name__ == "__main__":
    tail = _argv_tail()
    port = int(tail[tail.index("--port") + 1]) if "--port" in tail else 19693
    serve(port)
