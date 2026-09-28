#!/usr/bin/env python3
"""Cross-artifact consistency audit for implementation plans (SDD 'analyze').

Read-only. Reads a plan file plus the artifacts it names
(ARCHITECTURE_MANIFEST, .devin/adr/*, .devin/ledgers/*) and reports
mismatches as JSON on stdout:

- files named in the plan that don't exist (Create-declared paths are
  reported as planned_new, not errors; Modify/bare references that are
  absent are missing_ref errors)
- completion claims while checkboxes remain open
- declared constraint tokens reappearing inside task lines
- plan paths landing outside manifest-declared top-level dirs
- referenced ledgers with ticked gates still carrying EVIDENCE: pending

Usage:
  python scripts/spec-consistency.py PLAN.md [--root DIR] [--strict]

--root defaults to the nearest ancestor of PLAN containing `.devin/`,
else the current directory. Exit 0 always (report-only); --strict exits 1
when errors are found. Exit 2 on unreadable input.
"""
import json
import os
import re
import sys

CHECKBOX_RE = re.compile(r"^\s*-\s*\[([ xX])\]")
BACKTICK_RE = re.compile(r"`([^`\n]+)`")
FILES_DECL_RE = re.compile(r"^\s*-\s*(Create|Modify|Test)\b", re.IGNORECASE)
DONE_CLAIM_RES = [
    re.compile(r"\b(status|verdict)\s*[:=]\s*(done|complete|shipped|merged)\b", re.IGNORECASE),
    re.compile(r"\b(is|are|now)\s+(complete|done|shipped|merged)\b", re.IGNORECASE),
    re.compile(r"^#+.*\b(complete|done)\b", re.IGNORECASE),
]
CREATE_HINT_RE = re.compile(
    r"\b(create|creates|creating|skeleton|new\s+\w*\s*(file|dir|extension|script|module))\b",
    re.IGNORECASE)
CONSTRAINT_HEAD_RE = re.compile(
    r"^#{1,4}\s+.*(constraint|invariant|non-goal|non goal)", re.IGNORECASE)
BANNED_LEAD_RE = re.compile(
    r"\b(no|never|forbidden|do not|must not|without)\b", re.IGNORECASE)
LEDGER_TICKED_PENDING_RE = re.compile(r"^\s*-\s*\[[xX]\]")
PATHLIKE_RE = re.compile(
    r"^(?:\.?[A-Za-z]:)?\.?/?[\w.@+-]+(?:/[\w.@+-]+)+/?$")


def find_root(plan_path):
    p = os.path.abspath(plan_path)
    d = os.path.dirname(p)
    while True:
        if os.path.isdir(os.path.join(d, ".devin")):
            return d
        parent = os.path.dirname(d)
        if parent == d:
            return os.getcwd()
        d = parent


def path_candidates(text):
    """Backticked tokens that look like repo-relative paths."""
    for tok in BACKTICK_RE.findall(text):
        t = tok.strip()
        if not t or "://" in t or t.startswith(("--", "$", "%")):
            continue
        if any(c in t for c in "*|<>:\" ") and not PATHLIKE_RE.match(t):
            continue
        if "/" in t or re.search(r"\.(py|md|json|txt|toml|ps1|sh|js|cmd|ya?ml)$", t):
            yield t


def classify_decl(line, in_files_block):
    """create | modify | ref for a path mention's line context.

    Open task lines (`- [ ]`) describe pending work: their paths are
    planned_new unless a Modify marker says otherwise. Closed tasks and
    prose reference things that should already exist.
    """
    m = FILES_DECL_RE.match(line)
    if in_files_block and m:
        return "create" if m.group(1).lower() == "create" else "modify"
    cb = CHECKBOX_RE.match(line)
    if cb:
        if cb.group(1) == " ":
            return "modify" if re.search(r"\bmodify\b", line, re.IGNORECASE) else "create"
        return "ref"
    if line.lstrip().startswith("#"):
        return "modify" if re.search(r"\bmodify\b", line, re.IGNORECASE) else "create"
    if CREATE_HINT_RE.search(line):
        return "create"
    return "ref"


def extract_constraints(lines):
    """Tokens declared as banned/forbidden in constraint sections."""
    tokens = []
    in_section = False
    for line in lines:
        if CONSTRAINT_HEAD_RE.match(line):
            in_section = True
            continue
        if in_section and line.startswith("#"):
            in_section = False
        if not in_section or not BANNED_LEAD_RE.search(line):
            continue
        for tok in BACKTICK_RE.findall(line):
            tokens.append(tok.strip())
        for m in re.findall(r"[Nn]o\s+([A-Z][\w.-]+)", line):
            tokens.append(m)
    return sorted({t for t in tokens if len(t) > 2})


def manifest_dirs(root):
    """Top-level dirs declared (backticked `dir/`) in the manifest."""
    mf = os.path.join(root, ".devin", "ARCHITECTURE_MANIFEST.md")
    if not os.path.isfile(mf):
        return None, None
    try:
        text = open(mf, encoding="utf-8").read()
    except OSError:
        return None, None
    dirs = set()
    for tok in BACKTICK_RE.findall(text):
        t = tok.strip()
        m = re.match(r"^([\w.-]+)/", t)
        if m and "/" in t:
            dirs.add(m.group(1))
    return mf, dirs


def check_ledger(path):
    """Ticked gates carrying EVIDENCE: pending in one ledger file."""
    bad = []
    try:
        lines = open(path, encoding="utf-8").read().splitlines()
    except OSError:
        return [("unreadable", 0)]
    ticked = [i for i, l in enumerate(lines) if LEDGER_TICKED_PENDING_RE.match(l)]
    for i in ticked:
        block = "\n".join(lines[i:i + 8])
        if re.search(r"EVIDENCE:\s*pending", block):
            bad.append(("ticked_gate_pending_evidence", i + 1))
    return bad


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    flags = {a for a in sys.argv[1:] if a.startswith("--")}
    if not args:
        print(__doc__, file=sys.stderr)
        sys.exit(2)
    plan_path = args[0]
    root = (sys.argv[sys.argv.index("--root") + 1]
            if "--root" in sys.argv else find_root(plan_path))
    if not os.path.isfile(plan_path):
        print(json.dumps({"ok": False, "error": f"plan_not_found:{plan_path}"}))
        sys.exit(2)
    try:
        lines = open(plan_path, encoding="utf-8").read().splitlines()
    except OSError as exc:
        print(json.dumps({"ok": False, "error": f"plan_unreadable:{exc}"}))
        sys.exit(2)

    findings = []
    files_report = []
    basenames = None  # lazy filename index for unqualified mentions

    def exists_anywhere(cand):
        nonlocal basenames
        if "/" in cand or os.sep in cand:
            return os.path.exists(os.path.join(root, cand.replace("/", os.sep)))
        if basenames is None:
            basenames = set()
            for dp, dns, fns in os.walk(root):
                dns[:] = [d for d in dns
                          if d not in (".git", "__pycache__", "node_modules")]
                basenames.update(fns)
                basenames.update(dns)
        return cand.rstrip("/") in basenames

    # -- files named in plan vs disk ----------------------------------
    in_files = False
    for n, line in enumerate(lines, 1):
        if re.match(r"^\s*\*?\*?Files:\*?\*?", line):
            in_files = True
        elif line.strip().startswith("**") and "Files" not in line:
            in_files = False
        for cand in path_candidates(line):
            decl = classify_decl(line, in_files)
            exists = exists_anywhere(cand)
            if exists:
                status = "exists"
            elif decl == "modify" or (
                    decl == "ref" and CHECKBOX_RE.match(line)
                    and CHECKBOX_RE.match(line).group(1) != " "):
                status = "missing"
                findings.append({"kind": "missing_referenced_file",
                                 "severity": "error", "line": n,
                                 "detail": cand})
            elif decl == "create":
                status = "planned_new"
            else:
                status = "not_found"
                findings.append({"kind": "path_not_found",
                                 "severity": "info", "line": n,
                                 "detail": cand})
            files_report.append({"path": cand, "line": n,
                                 "declared": decl, "status": status})

    # -- checkboxes vs done claims ------------------------------------
    open_boxes = sum(1 for l in lines
                     if CHECKBOX_RE.match(l) and CHECKBOX_RE.match(l).group(1) == " ")
    done_lines = [n for n, l in enumerate(lines, 1)
                  if any(r.search(l) for r in DONE_CLAIM_RES)]
    if open_boxes and done_lines:
        findings.append({"kind": "done_claim_with_open_boxes",
                         "severity": "warning", "line": done_lines[0],
                         "detail": f"{open_boxes} unchecked boxes; "
                                   f"completion language at lines {done_lines}"})

    # -- constraint tokens inside task lines ---------------------------
    constraints = extract_constraints(lines)
    task_lines = [(n, l) for n, l in enumerate(lines, 1) if CHECKBOX_RE.match(l)]
    conflicts = []
    for tok in constraints:
        for n, l in task_lines:
            if tok in l and not BANNED_LEAD_RE.search(l):
                conflicts.append({"constraint_token": tok, "line": n})
                findings.append({"kind": "constraint_token_in_task",
                                 "severity": "warning", "line": n,
                                 "detail": f"'{tok}' banned by constraints; "
                                           f"verify negation context"})
    open_count = len([1 for _ in task_lines])

    # -- manifest boundaries ------------------------------------------
    mf, declared = manifest_dirs(root)
    boundary = []
    if declared:
        for item in files_report:
            p = item["path"].replace("\\", "/")
            if "/" not in p or p.startswith(".devin"):
                continue  # bare names can't be boundary-checked
            top = p.split("/")[0]
            if top and top not in {d.rstrip("/") for d in declared}:
                boundary.append(p)
                findings.append({"kind": "outside_manifest_dirs",
                                 "severity": "info", "line": item["line"],
                                 "detail": p})

    # -- referenced artifacts (ADR / ledger) ---------------------------
    artifacts = []
    seen = set()
    for item in files_report:
        p = item["path"].replace("\\", "/")
        if p in seen:
            continue
        seen.add(p)
        if ".devin/ledgers/" in p or ".devin/adr/" in p:
            kind = "ledger" if "ledgers" in p else "adr"
            full = os.path.join(root, p.replace("/", os.sep))
            if p.endswith("/") or not os.path.isfile(full):
                if not os.path.exists(full):
                    artifacts.append({"path": p, "kind": kind, "status": "missing"})
                    if item["declared"] in ("modify", "ref"):
                        findings.append({"kind": f"missing_{kind}",
                                         "severity": "error",
                                         "line": item["line"],
                                         "detail": p})
                continue
            artifacts.append({"path": p, "kind": kind, "status": "exists"})
            if kind == "ledger":
                for what, ln in check_ledger(full):
                    artifacts.append({"path": p, "kind": kind,
                                      "status": what, "line": ln})
                    findings.append({"kind": "ledger_" + what,
                                     "severity": "error",
                                     "line": item["line"],
                                     "detail": f"{p}:{ln}"})

    errors = sum(1 for f in findings if f["severity"] == "error")
    warnings = sum(1 for f in findings if f["severity"] == "warning")
    report = {
        "ok": errors == 0,
        "plan": plan_path,
        "root": root,
        "checks": {
            "files": files_report,
            "checkboxes": {"open": open_boxes, "task_lines": open_count,
                           "done_claim_lines": done_lines},
            "constraint_tokens": constraints,
            "constraint_conflicts": conflicts,
            "manifest_declared_dirs": sorted(declared) if declared else None,
            "outside_manifest_dirs": boundary,
            "artifacts": artifacts,
        },
        "findings": findings,
        "summary": {"errors": errors, "warnings": warnings,
                    "info": len(findings) - errors - warnings},
    }
    print(json.dumps(report, indent=2))
    sys.exit(1 if ("--strict" in flags and errors) else 0)


if __name__ == "__main__":
    main()
