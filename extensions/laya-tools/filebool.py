"""filebool — batch boolean classification over files (layers 8-9).

Answers a yes/no question per file through the resident layad daemon:
"does this file contain authentication data?" over 100 paths costs
N forward passes on the daemon and returns ONLY a path->verdict map —
file contents never enter the agent's context window.

Answers are suggestions, never proof: abstain means "check it
yourself". Use verdicts to rank reading order, not to conclude facts.

CLI:
  python filebool.py --glob "src/**/*.py" --question "has tests" \
      [--root .] [--exclude PAT ...] [--config profile.json]
  python filebool.py --files a.py b.py --question "contains auth data"
"""
from __future__ import annotations

import argparse
import fnmatch
import glob
import json
import os
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import decision_contract as dc   # noqa: E402
import laya_client as lc          # noqa: E402

PROFILE = "filebool-v1"
CANDIDATES = [{"id": "yes"}, {"id": "no"}]
DEFAULT_HEAD = 4000
DEFAULT_MAX_FILES = 500
BINARY_SNIFF = 512


def _read_head(path, head_chars):
    """First head_chars chars of a text file; None for binary/unreadable."""
    try:
        with open(path, "rb") as f:
            sniff = f.read(BINARY_SNIFF)
        if b"\x00" in sniff:
            return None
        with open(path, encoding="utf-8", errors="replace") as f:
            return f.read(head_chars)
    except OSError:
        return None


def _verdict(rec):
    """Map a recommendation to the public verdict shape."""
    if rec.get("outcome") == "suggestion" \
            and rec.get("candidate_id") in ("yes", "no"):
        return {"answer": rec["candidate_id"],
                "calibrated_probability":
                    rec.get("calibrated_probability"),
                "adoptable": bool(rec.get("adoptable"))}
    return {"answer": "abstain",
            "reason": rec.get("reason", "abstain")}


def ask_laya_filebool(paths, question, *, head_chars=DEFAULT_HEAD,
                      max_files=DEFAULT_MAX_FILES, deadline_ms=1000,
                      config=None, root="."):
    """{path: {"answer": yes|no|abstain, ...}} for each path.

    Raises ValueError (typed) when paths exceed max_files or the
    question is empty — callers partition, we never truncate quietly.
    """
    if not isinstance(question, str) or not question.strip():
        raise ValueError("question_empty")
    paths = list(paths)
    if len(paths) > max_files:
        raise ValueError(f"too_many_files:{len(paths)}>{max_files}")
    cfg = dc.load_config(config)
    mode = dc.effective_mode(cfg)
    results = {}
    if mode == "off" or not paths:
        for p in paths:
            results[p] = {"answer": "abstain", "reason": "feature_off"}
        return results
    daemon = lc.ensure_daemon(config)
    if daemon is None:
        for p in paths:
            results[p] = {"answer": "abstain",
                          "reason": "daemon_unavailable"}
        return results

    requests = []
    order = []
    for p in paths:
        try:
            rel = os.path.relpath(p, root)
        except ValueError:
            rel = p
        head = _read_head(p, head_chars)
        if head is None:
            results[p] = {"answer": "abstain", "reason": "unreadable"}
            continue
        order.append(p)
        requests.append({
            "version": dc.VERSION,
            "request_id": f"fb-{len(order)}",
            "profile": PROFILE,
            "mode": mode,
            "context": {"env_id": "filebool"},
            "state": {"goal": question.strip(),
                      "snippets": f"file: {rel}\n\n{head}"},
            "candidates": CANDIDATES,
            "deadline_ms": int(deadline_ms),
        })
    replies = lc.batch(requests, daemon=daemon,
                       timeout_s=max(5.0, deadline_ms / 1000 + 2))
    for p, rec in zip(order, replies):
        results[p] = _verdict(rec)
    return results


def ask_laya_glob(pattern, question, *, root=".", exclude=(), **kw):
    """glob(pattern) -> filter(exclude) -> ask_laya_filebool.
    Only files (not dirs); deterministic sort order."""
    files = sorted(
        f for f in glob.glob(pattern, root_dir=root, recursive=True)
        if os.path.isfile(os.path.join(root, f)))
    if exclude:
        files = [f for f in files
                 if not any(fnmatch.fnmatch(f, e) for e in exclude)]
    return ask_laya_filebool(
        [os.path.join(root, f) for f in files], question,
        root=root, **kw)


def main(argv=None):
    ap = argparse.ArgumentParser(
        description="Batch boolean file classification via layad")
    src = ap.add_mutually_exclusive_group(required=True)
    src.add_argument("--glob", dest="globpat",
                     help="Glob pattern, e.g. 'src/**/*.py'")
    src.add_argument("--files", nargs="+", help="Explicit file list")
    ap.add_argument("--question", required=True)
    ap.add_argument("--root", default=".")
    ap.add_argument("--exclude", action="append", default=[],
                    help="fnmatch exclude pattern (repeatable)")
    ap.add_argument("--head-chars", type=int, default=DEFAULT_HEAD)
    ap.add_argument("--max-files", type=int, default=DEFAULT_MAX_FILES)
    ap.add_argument("--deadline-ms", type=int, default=1000)
    ap.add_argument("--config", help="Path to laya profile.json")
    args = ap.parse_args(argv)

    t0 = time.time()
    try:
        if args.globpat:
            results = ask_laya_glob(
                args.globpat, args.question, root=args.root,
                exclude=tuple(args.exclude),
                head_chars=args.head_chars,
                max_files=args.max_files,
                deadline_ms=args.deadline_ms,
                config=args.config)
        else:
            results = ask_laya_filebool(
                args.files, args.question, root=args.root,
                head_chars=args.head_chars,
                max_files=args.max_files,
                deadline_ms=args.deadline_ms,
                config=args.config)
    except ValueError as e:
        print(json.dumps({"ok": False, "error": str(e)}))
        return 2
    answered = sum(1 for v in results.values()
                   if v["answer"] in ("yes", "no"))
    print(json.dumps({
        "ok": True,
        "question": args.question,
        "results": results,
        "stats": {"files": len(results), "answered": answered,
                  "abstained": len(results) - answered,
                  "ms": int((time.time() - t0) * 1000)},
    }, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
