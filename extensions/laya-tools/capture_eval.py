#!/usr/bin/env python3
"""capture_eval — record worker replies for a maintainer-authored draft.

The maintainer writes the draft: case_id + gold + request. This tool
only adds the real worker `reply` and freezes the manifest. It never
invents cases, golds, or replies.

Draft shape (one file per eval stage):
  {"version": 1, "eval": "e1", "profile": "ui-target-v1",
   "cases": [{"case_id": "e1-001", "gold": "as",
              "request": {...§5.1 envelope fields...}}]}

Output (frozen manifest consumed by eval_decisions.py):
  {"version": 1, "frozen": true, "eval": ..., "profile": ...,
   "cases": [{"case_id", "gold", "request", "reply"}]}

One worker process serves the whole run — cold engine load is paid
once, not per case.

  .venv/Scripts/python.exe capture_eval.py \
      --draft ../../.devin/evals/laya/e1/cases.json \
      --config ../../.devin/laya/profile.json \
      --out ../../.devin/evals/laya/e1/manifest.frozen.json
"""
from __future__ import annotations

import argparse
import hashlib
import json
import queue
import subprocess
import sys
import threading
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import decision_contract as dc  # noqa: E402


def note(msg):
    print(f"[capture] {msg}", file=sys.stderr)


def _sha256(path):
    h = hashlib.sha256()
    h.update(Path(path).read_bytes())
    return h.hexdigest()


def _reader(stream, q):
    for line in stream:
        q.put(line)
    q.put(None)  # EOF


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--draft", required=True,
                   help="Maintainer-authored draft (case_id+gold+request)")
    p.add_argument("--config", required=True,
                   help="Path to .devin/laya/profile.json")
    p.add_argument("--out", required=True, help="Frozen manifest output")
    p.add_argument("--reply-timeout", type=float, default=120.0,
                   help="Seconds to wait per reply (default 120)")
    args = p.parse_args(argv)

    draft = json.loads(Path(args.draft).read_text(encoding="utf-8"))
    cases = draft.get("cases")
    if not isinstance(cases, list):
        print(json.dumps({"ok": False, "error": "draft_cases_invalid"}))
        return 2

    cfg = dc.load_config(args.config)
    if not dc.enabled(cfg):
        print(json.dumps({"ok": False, "error":
                          "config_disabled:mode is off — set shadow first"},
                         indent=2))
        return 1

    cmd = [sys.executable, str(HERE / "laya_cli.py"), "serve-stdio",
           "--config", str(Path(args.config).resolve())]
    note("spawning worker (cold engine load ~1min on CPU) ...")
    proc = subprocess.Popen(cmd, stdin=subprocess.PIPE,
                            stdout=subprocess.PIPE, stderr=sys.stderr,
                            text=True, bufsize=1, cwd=HERE)
    q = queue.Queue()
    threading.Thread(target=_reader, args=(proc.stdout, q),
                     daemon=True).start()

    out_cases = []
    try:
        for i, case in enumerate(cases):
            cid = case.get("case_id", f"case-{i}")
            req = case.get("request") or {}
            errs = dc.validate_request(req)
            if errs:
                note(f"{cid}: request invalid ({errs[0]}) — "
                     "sending anyway; worker reply will be an abstain")
            envelope = {"version": dc.VERSION,
                        "request_id": req.get("request_id") or cid,
                        "request": req}
            proc.stdin.write(json.dumps(envelope, ensure_ascii=False)
                             + "\n")
            proc.stdin.flush()
            try:
                line = q.get(timeout=args.reply_timeout)
            except queue.Empty:
                print(json.dumps({"ok": False,
                                  "error": f"reply_timeout:{cid}"}))
                return 1
            if line is None:
                print(json.dumps({"ok": False,
                                  "error": f"worker_eof:{cid}"}))
                return 1
            reply = json.loads(line)
            out_cases.append({"case_id": cid, "gold": case.get("gold"),
                              "request": req, "reply": reply})
            if i % 10 == 0:
                note(f"{i + 1}/{len(cases)} captured")
    finally:
        try:
            proc.stdin.close()
        except OSError:
            pass
        proc.wait(timeout=15)
        if proc.poll() is None:
            proc.kill()

    manifest = {
        "version": 1,
        "frozen": True,
        "eval": draft.get("eval"),
        "profile": draft.get("profile"),
        "captured_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "config_sha256": _sha256(args.config),
        "cases": out_cases,
    }
    Path(args.out).write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8")
    print(json.dumps({"ok": True, "out": str(args.out),
                      "cases": len(out_cases)}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
