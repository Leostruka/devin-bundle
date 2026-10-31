"""review_gate — JEV-4 seven-question pre-review triage (stdlib only).

Deterministic boolean triage over a unified diff, run BEFORE a deep
code review is scheduled. Answers seven questions:

  q1 secret indication in added lines   -> yes = high risk
  q2 protected paths touched            -> yes = high risk
  q3 dependency files changed           -> yes = high risk
  q4 tests present for changed source   -> missing tests escalate
  q5 network/egress indicators          -> yes escalates
  q6 diff larger than 400 lines         -> yes escalates
  q7 commit message states the why      -> missing rationale escalates

Polarity: yes on q1-q3 is a high-risk POSITIVE signal; for q4/q7 a
"no" answer is the dangerous one and escalates. The output is triage
metadata only — "risk" + "requires_deep_review". It contains no
allow/approve/merge field and can never authorize an action; a low
result merely means the deterministic gate found nothing to escalate.

Secret safety: findings record the detector id and file path ONLY.
Matched text is never returned, logged or printed.

Optional Laya shadow: when the profile config enables shadow/assist,
the flag vector is sent to `review-risk-v1` as a suggestion request.
Daemon unavailable or mode off -> typed abstain; the deterministic
risk level never depends on the model.

CLI:
  python review_gate.py --diff change.diff [--commit-msg-file msg.txt]
      [--commit-msg "text"] [--config profile.json] [--max-lines 400]
Exit 0 always on parse success; JSON on stdout.
"""
from __future__ import annotations

import argparse
import json
import re
import secrets
import shlex
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import decision_contract as dc
import laya_client as lc

PROFILE = "review-risk-v1"
DEFAULT_MAX_LINES = 400
MAX_SNIPPET = 60_000

PROTECTED_PATHS = (
    "hooks.v1.json",
    "hooks.json",
    "manifest.json",
    "config.json",
)
PROTECTED_GLOBS = (
    re.compile(r"(^|/)scripts/[^/]*guard[^/]*\.(py|ps1|sh)$"),
    re.compile(r"(^|/)tests/held-out/"),
)
DEPENDENCY_FILES = re.compile(
    r"(^|/)(requirements[^/]*\.txt|pyproject\.toml|setup\.py|setup\.cfg|"
    r"package\.json|package-lock\.json|yarn\.lock|pnpm-lock\.yaml|"
    r"Cargo\.toml|Cargo\.lock|Gemfile(\.lock)?|go\.mod|go\.sum|"
    r"\.venv|constraints[^/]*\.txt)$")
TEST_PATH = re.compile(
    r"(^|/)(tests?)/|(^|/)test_[^/]*\.|(^|/)[^/]*_test\.|"
    r"(^|/)conftest\.py$", re.I)
DOC_PATH = re.compile(
    r"(^|/)(docs?|\.devin|skills?/[^/]+/SKILL)|\.(md|rst|adoc|txt)$",
    re.I)
EGRESS = re.compile(
    r"\b(requests|urllib|urlopen|httpx|aiohttp|socket|fetch\(|"
    r"curl|wget|Invoke-WebRequest|https?://)", re.I)
SECRET_DETECTORS = (
    ("aws_access_key", re.compile(r"\bAKIA[0-9A-Z]{16}\b")),
    ("private_key_block",
     re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----")),
    ("generic_token_assignment",
     re.compile(r"(?i)\b(api[_-]?key|secret|token|password|passwd|"
                r"client_secret)\b\s*[:=]\s*[\"'][^\"']{8,}[\"']")),
    ("github_token", re.compile(r"\b(ghp|gho|ghu|ghs|ghr|github_pat)_"
                                r"[A-Za-z0-9_]{20,}\b")),
    ("slack_or_bearer",
     re.compile(r"\b(xox[baprs]-[A-Za-z0-9-]{10,}|Bearer "
                r"[A-Za-z0-9._-]{20,})\b")),
)
RATIONALE_MARKERS = re.compile(
    r"(?i)\b(because|why|so that|in order|reason|rationale|"
    r"fix(e[ds])?|root cause|regression|motivation)\b")


_HEADER_TS = re.compile(r"\s+\d{4}-\d{2}-\d{2}.*$")


def _norm_path(p):
    """Normalize a diff header path: GNU ---/+++ headers may append a
    tab- or space-separated timestamp; git may quote the path. Strip
    the timestamp, a//b/ prefixes, quotes and backslashes. Returns
    None for /dev/null, absolute, parent-escaping or control-char
    paths — callers count those as anomalies, never as clean."""
    p = _HEADER_TS.sub("", p.split("\t", 1)[0]).strip()
    if p.startswith('"') and p.endswith('"') and len(p) >= 2:
        p = p[1:-1]
    p = p.replace("\\", "/")
    if any(ord(c) < 32 for c in p):
        return None
    if p in ("", "/dev/null") or p.startswith("/") or ":" in p:
        return None
    parts = [seg for seg in p.split("/") if seg not in ("", ".")]
    if any(seg == ".." for seg in parts):
        return None
    for pre in ("a/", "b/"):
        if parts and parts[0] == pre[0] and len(parts) > 1:
            parts = parts[1:]
            break
    return "/".join(parts) if parts else None


def _parse_diff(diff_text):
    """Unified diff -> (files, added_lines_per_file, deleted_paths,
    total_diff_lines, anomalies). Tracks `diff --git` pairs, `--- `
    old paths, `+++ ` new paths, `rename from/to` and `Binary files`
    metadata so deletions, rename-only and binary changes still
    register the touched path. Headers that fail to normalize count
    as anomalies — an unreadable diff must escalate, never look
    clean. Secret scanning only ever sees real `+` added lines;
    added-line TEXT never leaves this function."""
    files, deleted, added = [], set(), {}
    cur = None
    n_lines = 0
    anomalies = 0

    def _record(p):
        nonlocal anomalies
        p = _norm_path(p)
        if p is None:
            anomalies += 1
        elif p not in files:
            files.append(p)
        return p

    for line in diff_text.splitlines():
        n_lines += 1
        if line.startswith("diff --git "):
            try:
                rest = shlex.split(line[len("diff --git "):],
                                   posix=True)
            except ValueError:
                rest = line[len("diff --git "):].split()
            if len(rest) != 2:
                anomalies += 1
            for tok in rest[:2]:
                _record(tok)
            cur = None
        elif line.startswith("rename from "):
            _record(line[len("rename from "):])
        elif line.startswith("rename to "):
            _record(line[len("rename to "):])
        elif line.startswith("Binary files "):
            for tok in line[len("Binary files "):].replace(
                    " and ", " ").replace("differ", "").split():
                _record(tok)
        elif line.startswith("--- "):
            raw = line[4:].split("\t", 1)[0].strip().strip('"')
            if raw == "/dev/null":
                cur = None
                continue
            p = _norm_path(line[4:])
            if p:
                if p not in files:
                    files.append(p)
            else:
                anomalies += 1
            cur = p
        elif line.startswith("+++ "):
            raw = line[4:].split("\t", 1)[0].strip().strip('"')
            if raw == "/dev/null":
                if cur:
                    deleted.add(cur)
                cur = None
            else:
                cur = _record(line[4:])
                if cur:
                    added.setdefault(cur, [])
        elif line.startswith("+") and not line.startswith("+++"):
            if cur is not None:
                added[cur].append(line[1:])
    return files, added, deleted, n_lines, anomalies


def _secret_findings(added):
    """[{path, detector}] — never the matched text."""
    findings = []
    for path, lines in added.items():
        for line in lines:
            for det_id, rx in SECRET_DETECTORS:
                if rx.search(line):
                    findings.append({"path": path, "detector": det_id})
                    break
    return findings


def _protected_hit(path):
    return path in PROTECTED_PATHS or any(
        g.search(path) for g in PROTECTED_GLOBS)


def _has_rationale(msg):
    """Non-trivial message AND a reason marker. 'wip', 'x', one-word
    messages do not count as declaring the why."""
    if not isinstance(msg, str):
        return False
    m = msg.strip()
    return len(m.split()) >= 4 and bool(RATIONALE_MARKERS.search(m))


def triage_diff(diff_text, commit_msg="", *, config=None,
                max_lines=DEFAULT_MAX_LINES, deadline_ms=1000):
    """Seven-question triage. Returns the result dict; the optional
    Laya suggestion lands under 'laya' and never changes 'risk'."""
    files, added, deleted, n_lines, anomalies = \
        _parse_diff(diff_text or "")
    secrets_found = _secret_findings(added)
    protected = sorted(p for p in files if _protected_hit(p))
    deps = sorted(p for p in files if DEPENDENCY_FILES.search(p))
    test_paths = sorted(p for p in files
                        if TEST_PATH.search(p) and p not in deleted)
    source_paths = sorted(
        p for p in files
        if p not in deleted
        and not TEST_PATH.search(p) and not DEPENDENCY_FILES.search(p)
        and not DOC_PATH.search(p))
    egress = sorted({p for p, lines in added.items()
                     if any(EGRESS.search(l) for l in lines)})
    has_tests = bool(test_paths) or not source_paths
    rationale = _has_rationale(commit_msg)

    questions = {
        "q1_secret_indication": {
            "answer": bool(secrets_found), "findings": secrets_found},
        "q2_protected_paths": {"answer": bool(protected),
                               "paths": protected},
        "q3_dependency_changes": {"answer": bool(deps), "paths": deps},
        "q4_has_tests": {"answer": has_tests,
                         "test_paths": test_paths,
                         "source_paths": source_paths},
        "q5_egress": {"answer": bool(egress), "paths": egress},
        "q6_large_diff": {"answer": n_lines > max_lines,
                          "lines": n_lines},
        "q7_commit_rationale": {"answer": rationale},
    }

    if questions["q1_secret_indication"]["answer"] \
            or questions["q2_protected_paths"]["answer"] \
            or questions["q3_dependency_changes"]["answer"]:
        risk = "high"
    elif (not has_tests) or egress or anomalies \
            or questions["q6_large_diff"]["answer"] or not rationale:
        risk = "medium"
    else:
        risk = "low"

    result = {
        "ok": True,
        "risk": risk,
        "requires_deep_review": risk != "low",
        "questions": questions,
        "files_changed": files,
        "parse_anomalies": anomalies,
        "laya": _laya_suggestion(
            questions, files, n_lines, has_tests,
            config=config, deadline_ms=deadline_ms),
    }
    return result


def _laya_suggestion(questions, files, n_lines, has_tests, *,
                     config=None, deadline_ms=1000):
    """Optional review-risk-v1 shadow suggestion. off mode or missing
    daemon -> typed abstain; suggestion is advisory only."""
    cfg = dc.load_config(config)
    mode = dc.effective_mode(cfg)
    if mode == "off" or PROFILE not in (cfg.get("profiles") or [PROFILE]):
        rec = dc.make_abstention("", "feature_off")
        rec["profile_version"] = PROFILE
        return rec
    hint = {
        "files_changed": len(files),
        "diff_lines": n_lines,
        "has_tests": has_tests,
        "q1": questions["q1_secret_indication"]["answer"],
        "q2": questions["q2_protected_paths"]["answer"],
        "q3": questions["q3_dependency_changes"]["answer"],
        "q5": questions["q5_egress"]["answer"],
        "q6": questions["q6_large_diff"]["answer"],
        "q7": questions["q7_commit_rationale"]["answer"],
    }
    request = {
        "version": dc.VERSION,
        "request_id": f"rr-{secrets.token_hex(6)}",
        "profile": PROFILE,
        "mode": mode,
        "context": {"env_id": "review_gate"},
        "state": {"goal": "classify review risk of this diff",
                  "snippets": json.dumps(hint)[:MAX_SNIPPET],
                  "confidence_hint": "0.0"},
        "candidates": [{"id": r} for r in
                       ("low", "medium", "high", "critical")],
        "deadline_ms": int(deadline_ms),
    }
    daemon = lc.ensure_daemon(config)
    rec = lc.recommend(request, daemon=daemon)
    if not isinstance(rec, dict):
        rec = dc.make_abstention(request["request_id"],
                                 "daemon_unavailable")
    rec.setdefault("profile_version", PROFILE)
    return rec


def main(argv=None):
    ap = argparse.ArgumentParser(
        description="JEV-4 seven-question diff triage")
    src = ap.add_mutually_exclusive_group()
    src.add_argument("--diff", help="unified diff file ('-' = stdin)")
    ap.add_argument("--commit-msg", default="")
    ap.add_argument("--commit-msg-file", default=None)
    ap.add_argument("--config", default=None,
                    help="laya profile.json; enables shadow suggestion")
    ap.add_argument("--max-lines", type=int, default=DEFAULT_MAX_LINES)
    ap.add_argument("--deadline-ms", type=int, default=1000)
    args = ap.parse_args(argv)

    try:
        if args.diff and args.diff != "-":
            diff_text = Path(args.diff).read_text(encoding="utf-8",
                                                  errors="replace")
        else:
            diff_text = sys.stdin.read()
    except OSError as e:
        print(json.dumps({"ok": False, "error": f"read_error:{e}"}))
        return 2
    msg = args.commit_msg
    if args.commit_msg_file:
        try:
            msg = Path(args.commit_msg_file).read_text(
                encoding="utf-8", errors="replace")
        except OSError as e:
            print(json.dumps({"ok": False,
                              "error": f"read_error:{e}"}))
            return 2
    out = triage_diff(diff_text, commit_msg=msg, config=args.config,
                      max_lines=args.max_lines,
                      deadline_ms=args.deadline_ms)
    print(json.dumps(out, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
