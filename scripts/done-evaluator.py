#!/usr/bin/env python3
"""done-evaluator - grade a claimed 'done' against transcript evidence.

Writer is not the grader: the worker model declares done, this evaluator
checks the claim against what the transcript actually shows.

Pass 1 (deterministic, free): contradiction markers after/near a done
claim (FAILED tests, tracebacks, unchecked acceptance boxes, "did not
run" admissions) -> not_done. Claim with no verification output at all
-> uncertain. Claim + verification evidence + no contradictions -> done.

Pass 2 (--emit-brief): emit a grading brief for a separate model tier
(swe-2-medium) so ambiguous cases get a real second opinion instead of
self-trust. The orchestrator dispatches the brief and reads the verdict.

Usage:
    python scripts/done-evaluator.py --transcript FILE [--task FILE]
    python scripts/done-evaluator.py --emit-brief --transcript FILE
    ... --strict    exit 4 when verdict is not_done (loop gate)
"""
import argparse
import json
import os
import re
import sys
from pathlib import Path

_BUNDLE_VERSION_CACHE = None


def _bundle_version():
    """Nearest ancestor manifest.json with a "name" marker, else ""."""
    global _BUNDLE_VERSION_CACHE
    if _BUNDLE_VERSION_CACHE is not None:
        return _BUNDLE_VERSION_CACHE
    import json as _json
    for parent in Path(__file__).absolute().parents:
        manifest = parent / "manifest.json"
        if manifest.is_file():
            try:
                data = _json.loads(
                    manifest.read_text(encoding="utf-8"))
            except (OSError, ValueError):
                break
            if isinstance(data, dict) and data.get("name"):
                _BUNDLE_VERSION_CACHE = str(data.get("version") or "")
            else:
                _BUNDLE_VERSION_CACHE = ""
            return _BUNDLE_VERSION_CACHE
    _BUNDLE_VERSION_CACHE = ""
    return _BUNDLE_VERSION_CACHE


def _answered_by():
    return {"bundle": _bundle_version(), "wrapper": "done-evaluator"}


def _stamp(payload):
    if not isinstance(payload, dict):
        return payload
    payload["api_version"] = 2
    if not isinstance(payload.get("meta"), dict):
        payload["meta"] = {}
    payload["meta"].setdefault("answered_by", _answered_by())
    return payload


def _dumps(payload, **kw):
    return json.dumps(_stamp(payload), **kw)


if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")


_DONE_RE = re.compile(
    r"\b(done|complete[ds]?|finished|all tests pass|resolved|fixed it|"
    r"task complete|work is done|shipped)\b", re.I)
_FAIL_RE = re.compile(
    r"\b(FAILED?|ERRORS?|Traceback|assertion error|did not run|"
    r"could not|unable to|blocked|not resolved|exception)\b", re.I)
_PASS_EVIDENCE_RE = re.compile(
    r"(\d+\s*(passed|tests? (pass|green))|exit code:?\s*0\b|"
    r"0 errors|0 failures|all checks (pass|green)|build succeeded)",
    re.I)
_ADMIT_SKIP_RE = re.compile(
    r"(didn'?t run|did not run|haven'?t run|skipped|not verified|"
    r"couldn'?t (test|verify)|no tests? (were )?(run|added))",
    re.I)
_UNCHECKED_RE = re.compile(r"^\s*[-*]\s*\[ \]", re.M)
_ACCEPT_BLOCK_RE = re.compile(
    r"^\s*(#{1,6}\s*)?(acceptance( criteria)?|done when|verify|checks?)"
    r"\s*:?\s*$", re.I | re.M)


def _read(path):
    with open(path, encoding="utf-8", errors="replace") as f:
        return f.read()


def _test_run_state(tail):
    """Last pytest-style summary line decides: failing|passing|None."""
    lines = [l for l in tail.splitlines()
             if re.search(r"\d+\s*(passed|failed)", l)]
    if not lines:
        return None
    last = lines[-1]
    f = re.search(r"(\d+)\s*failed", last)
    if f and int(f.group(1)) > 0:
        return "failing"
    p = re.search(r"(\d+)\s*passed", last)
    if p and int(p.group(1)) > 0:
        return "passing"
    return None


def _acceptance_items(task_text):
    """Unchecked boxes inside an Acceptance/Done-when/Verify block."""
    if not task_text:
        return 0
    m = _ACCEPT_BLOCK_RE.search(task_text)
    block = task_text[m.end():m.end() + 2000] if m else task_text
    return len(_UNCHECKED_RE.findall(block))


def grade(transcript, task_text=""):
    """Return (verdict, signals). verdict in done|not_done|uncertain."""
    signals = []
    tail = transcript[-8000:]
    # "0 failed" / "no errors" are success counts, not failure markers.
    clean = re.sub(r"\b0\s+(failed|errors?|failures?)\b", "", tail,
                   flags=re.I)
    clean = re.sub(r"\b(errors?|failures?|failed)\s*[:=]\s*0\b", "", clean,
                   flags=re.I)
    clean = re.sub(r"\bno\s+(errors?|failures?)\b", "", clean, flags=re.I)
    claims = bool(_DONE_RE.search(tail))
    fails = sorted(set(m.lower() for m in _FAIL_RE.findall(clean)))
    admits = bool(_ADMIT_SKIP_RE.search(tail))
    evidence = bool(_PASS_EVIDENCE_RE.search(clean))
    run = _test_run_state(tail)
    unchecked = _acceptance_items(task_text)

    if run == "failing":
        signals.append("test_run:failing")
        evidence = False
        if "failed" not in fails:
            fails.append("failed")
    elif run == "passing":
        signals.append("test_run:passing")
    if claims:
        signals.append("done_claim")
    if fails:
        signals.append("fail_markers:" + ",".join(fails[:6]))
    if admits:
        signals.append("admitted_skip")
    if evidence:
        signals.append("verify_evidence")
    if unchecked:
        signals.append("unchecked_acceptance:%d" % unchecked)

    if not claims:
        return "uncertain", signals + ["no_done_claim"]
    if unchecked or admits or (fails and not evidence):
        return "not_done", signals
    if fails and evidence:
        # failures AND passing output - newest state ambiguous
        return "uncertain", signals + ["mixed_evidence"]
    if not evidence:
        return "uncertain", signals + ["no_verify_evidence"]
    return "done", signals


def emit_brief(transcript, task_text, verdict, signals):
    """Grading brief for a separate model tier (writer != grader)."""
    return {
        "role": "done_grader",
        "model_hint": "swe-2-medium",
        "instruction": (
            "You are grading whether a worker's DONE claim is real. "
            "Read the task, then the transcript tail. Verdict JSON only: "
            '{"done": true|false, "missing": ["<gap>", ...], '
            '"confidence": 0..1}. Grade evidence, not confidence.'),
        "task": (task_text or "")[:4000],
        "deterministic_signals": signals,
        "deterministic_verdict": verdict,
        "transcript_tail": transcript[-6000:],
        "required_output": {"done": "bool", "missing": ["str"],
                            "confidence": "float"},
    }


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--transcript", help="turn transcript file")
    ap.add_argument("--task", help="task/issue file with acceptance")
    ap.add_argument("--emit-brief", action="store_true",
                    help="also emit grading brief for a separate model")
    ap.add_argument("--strict", action="store_true",
                    help="exit 4 when verdict is not_done")
    ap.add_argument("--stdin", action="store_true",
                    help="read transcript from stdin")
    args = ap.parse_args(argv)

    try:
        if args.stdin:
            sys.stdin.reconfigure(encoding="utf-8", errors="replace")
            transcript = sys.stdin.read()
        elif args.transcript:
            transcript = _read(args.transcript)
        else:
            transcript = ""
    except OSError as e:
        print(_dumps({"ok": False, "error": str(e)}))
        return 1

    task_text = ""
    if args.task:
        try:
            task_text = _read(args.task)
        except OSError:
            pass

    verdict, signals = grade(transcript, task_text)
    out = {"ok": True, "verdict": verdict, "signals": signals}
    if args.emit_brief:
        out["brief"] = emit_brief(transcript, task_text, verdict, signals)
    print(_dumps(out, ensure_ascii=False, indent=1))
    if args.strict and verdict == "not_done":
        return 4
    return 0


if __name__ == "__main__":
    sys.exit(main())
