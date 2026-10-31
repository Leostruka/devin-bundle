"""explore — two-stage code exploration (LAYA §12 JEV-3, layers 8-9).

Stage 1: ripgrep keyword filter reduces the corpus to plausible
candidates (argv-form invocation confined to --root, fnmatch excludes).
When rg is unavailable a deterministic stdlib walk matches keywords in
file heads instead.
Stage 2: candidates partition into batches <= BATCH_SIZE and pass
through filebool.ask_laya_filebool; verdicts rank a top-K shortlist.

Ranked output is a reading-order suggestion, never proof — abstain
means "check it yourself" (Rule 12). When the daemon is unavailable or
every file abstains, output falls back to deterministic stage-1 order.

CLI:
  python explore.py --root DIR --keywords kw [kw ...] --question "..." \
      [--top-k 8] [--exclude PAT ...] [--max-candidates N] [--config p]
"""
from __future__ import annotations

import argparse
import fnmatch
import json
import math
import os
import shutil
import subprocess
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import filebool

BATCH_SIZE = 20
DEFAULT_TOP_K = 8
DEFAULT_MAX_CANDIDATES = 500
READ_HEAD = 65536
BINARY_SNIFF = 512
RG_TIMEOUT_S = 60
MAX_SCAN_FILES = 20000
SAFE_EXCLUDE_DIRS = (".git", ".venv", "node_modules", "target",
                     "__pycache__")
SAFE_EXCLUDE_FILES = (".env", "credentials.toml")


def _confine(root, path):
    """Absolute path iff realpath(path) is inside realpath(root)."""
    try:
        rp = os.path.realpath(path)
        rr = os.path.realpath(root)
        if os.path.commonpath((rp, rr)) != rr:
            return None
    except (OSError, ValueError):
        return None
    return rp


def _secret_file(name):
    return name in SAFE_EXCLUDE_FILES or name.startswith(".env.")


def _rg_candidates(root, keywords, excludes):
    """rg -l -F (literal) over root; None when rg is missing/errored.
    NUL-separated output keeps space/newline filenames intact."""
    rg = shutil.which("rg")
    if rg is None:
        return None
    argv = [rg, "-l", "-i", "-F", "--null", "--no-messages",
            "--color", "never"]
    for d in SAFE_EXCLUDE_DIRS:
        argv += ["--glob", "!**/" + d + "/**"]
    argv += ["--glob", "!**/.env", "--glob", "!**/.env.*",
             "--glob", "!**/credentials.toml"]
    for e in excludes:
        argv += ["--glob", "!" + e]
    for k in keywords:
        argv += ["-e", k]
    argv += ["--", root]
    try:
        cp = subprocess.run(argv, capture_output=True, text=True,
                            timeout=RG_TIMEOUT_S,
                            creationflags=getattr(
                                subprocess, "CREATE_NO_WINDOW", 0))
    except (OSError, subprocess.SubprocessError):
        return None
    if cp.returncode not in (0, 1):
        return None
    out = []
    for item in cp.stdout.split("\0"):
        p = _confine(root, item.strip())
        if p and os.path.isfile(p):
            out.append(p)
    return sorted(set(out))


def _walk_candidates(root, keywords, excludes, limit=None):
    """Deterministic stdlib fallback: literal keyword match in file
    heads. Prunes SAFE_EXCLUDE_DIRS, skips .env*/credentials.toml, and
    stops early at limit / MAX_SCAN_FILES — callers get a bounded,
    reproducible prefix, never a silent full scan."""
    pats = [k.lower().encode("utf-8", "ignore") for k in keywords
            if k.strip()]
    if not pats:
        return []
    out = []
    scanned = 0
    for dp, dns, fns in os.walk(root):
        rel = os.path.relpath(dp, root)
        dns[:] = sorted(
            d for d in dns
            if d not in SAFE_EXCLUDE_DIRS
            and not any(fnmatch.fnmatch(d, e)
                        or fnmatch.fnmatch(os.path.join(rel, d), e)
                        for e in excludes))
        for fn in sorted(fns):
            rp = os.path.relpath(os.path.join(dp, fn), root)
            if _secret_file(fn) or any(
                    fnmatch.fnmatch(fn, e) or fnmatch.fnmatch(rp, e)
                    for e in excludes):
                continue
            cp = _confine(root, os.path.join(dp, fn))
            if not cp or not os.path.isfile(cp):
                continue
            scanned += 1
            if scanned > MAX_SCAN_FILES \
                    or (limit is not None and len(out) >= limit):
                return sorted(set(out))
            try:
                with open(cp, "rb") as f:
                    head = f.read(READ_HEAD)
            except OSError:
                continue
            if b"\x00" in head[:BINARY_SNIFF]:
                continue
            low = head.lower()
            if any(k in low for k in pats):
                out.append(cp)
    return sorted(set(out))


def _rank(cands, results):
    """yes > abstain > no, prob desc, stage-1 order as final tiebreak."""
    pos = {p: i for i, p in enumerate(cands)}

    def key(p):
        v = results.get(p) or {}
        rank = {"yes": 0, "abstain": 1, "no": 2}.get(v.get("answer"), 1)
        prob = v.get("calibrated_probability")
        prob = prob if isinstance(prob, (int, float)) \
            and not isinstance(prob, bool) and math.isfinite(prob) \
            else 0.0
        return (rank, -prob, pos[p])
    return sorted(cands, key=key)


def explore(root, keywords, question, *, top_k=DEFAULT_TOP_K,
            excludes=(), max_candidates=DEFAULT_MAX_CANDIDATES,
            config=None, deadline_ms=1000):
    """Two-stage explore. Returns the output document dict.

    Raises ValueError (typed) on a missing root, empty keywords or
    question, or non-positive top_k/max_candidates/deadline — callers
    fix arguments, we never slice on bad input.
    """
    if not isinstance(root, str) or not os.path.isdir(root):
        raise ValueError("root_not_found")
    keywords = [k for k in (keywords or [])
                if isinstance(k, str) and k.strip()]
    if not keywords:
        raise ValueError("keywords_empty")
    if not isinstance(question, str) or not question.strip():
        raise ValueError("question_empty")
    if not isinstance(top_k, int) or isinstance(top_k, bool) or top_k < 0:
        raise ValueError("top_k_invalid")
    if not isinstance(max_candidates, int) \
            or isinstance(max_candidates, bool) or max_candidates < 1:
        raise ValueError("max_candidates_invalid")
    if not isinstance(deadline_ms, int) \
            or isinstance(deadline_ms, bool) or deadline_ms <= 0:
        raise ValueError("deadline_invalid")

    t0 = time.time()
    cands = _rg_candidates(root, keywords, excludes)
    via = "rg"
    if cands is None:
        via = "walk"
        cands = _walk_candidates(root, keywords, excludes,
                                 limit=max_candidates + 1)
    truncated = len(cands) > max_candidates
    cands = cands[:max_candidates]
    batches = [cands[i:i + BATCH_SIZE]
               for i in range(0, len(cands), BATCH_SIZE)]
    results = {}
    for b in batches:
        results.update(filebool.ask_laya_filebool(
            b, question, root=root, config=config,
            deadline_ms=deadline_ms))
    ranked = _rank(cands, results)
    suggested = []
    for p in ranked[:top_k]:
        v = dict(results.get(p)
                 or {"answer": "abstain", "reason": "no_verdict"})
        try:
            v["path"] = os.path.relpath(p, root)
        except ValueError:
            v["path"] = p
        suggested.append(v)
    answered = sum(1 for v in results.values()
                   if v.get("answer") in ("yes", "no"))
    return {
        "ok": True,
        "question": question,
        "via": via,
        "suggested": suggested,
        "stats": {"candidates": len(cands), "batches": len(batches),
                  "truncated": truncated, "answered": answered,
                  "abstained": len(results) - answered,
                  "ms": int((time.time() - t0) * 1000)},
        "note": "ranked reading-order suggestion, not proof; "
                "abstain means verify the file yourself",
    }


def main(argv=None):
    ap = argparse.ArgumentParser(
        description="Two-stage explore: rg filter -> filebool top-K")
    ap.add_argument("--root", default=".")
    ap.add_argument("--keywords", nargs="+", required=True)
    ap.add_argument("--question", required=True)
    ap.add_argument("--top-k", type=int, default=DEFAULT_TOP_K)
    ap.add_argument("--exclude", action="append", default=[],
                    help="fnmatch exclude pattern (repeatable)")
    ap.add_argument("--max-candidates", type=int,
                    default=DEFAULT_MAX_CANDIDATES)
    ap.add_argument("--deadline-ms", type=int, default=1000)
    ap.add_argument("--config", help="Path to laya profile.json")
    args = ap.parse_args(argv)

    root = os.path.abspath(args.root)
    try:
        doc = explore(root, args.keywords, args.question,
                      top_k=args.top_k,
                      excludes=tuple(args.exclude),
                      max_candidates=args.max_candidates,
                      config=args.config,
                      deadline_ms=args.deadline_ms)
    except ValueError as e:
        print(json.dumps({"ok": False, "error": str(e)}))
        return 2
    print(json.dumps(doc, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
