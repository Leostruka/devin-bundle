#!/usr/bin/env python3
"""Behavioral tool-use eval harness: grading, ledgering, baseline compare.

Implements the protocol in skills/agent-eval/SKILL.md (behavioral section,
pattern verified from T3 Code PR #24635). Design constraint: the harness
never calls models. Sampling is external (manual, subagent-driven, or CI-
excluded scripts); this tool owns everything that must be deterministic
and CI-testable: case schema validation, plain-logic graders, append-only
ledger, and baseline-vs-candidate comparison.

Modes:
  validate <case.json>...     schema-check case files (CI)
  grade --case C --sample F   grade one sample output file (CI)
  record --case C --model M --run R --idx N --pass 0|1 [--cost T]
                             append one sample result to the ledger
  compare --baseline R1 --candidate R2
                             per-case pass-rate comparison, same model
                              required (cross-model numbers are meaningless)
  sample --case C --run R [--model M] [--samples N] [--timeout S]
                             NON-CI driver: run N `devin -p` sessions in
                             isolated workspaces, synthesize transcript +
                             artifact digest, grade and record each. This
                             is the external sampler the protocol refers
                             to; it calls models and must never run in CI.
                             Everything it feeds (grade/record/compare)
                             stays deterministic and CI-testable.

Exit non-zero on any failure (envelope v2 contract).
"""
import argparse
import json
import os
import re
import subprocess
import sys
import tempfile
import time
from concurrent.futures import ThreadPoolExecutor

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from bundle_envelope import bind

_stamp, _dumps = bind("behavioral-eval")

LEDGER = os.path.join(".devin", "ledgers", "behavioral-eval.jsonl")

GRADER_TYPES = {"contains", "not_contains", "regex", "not_regex", "all", "any"}


def load_case(path):
    with open(path, encoding="utf-8") as fh:
        return json.load(fh)


def validate_case(case, path):
    """Schema errors as a list; empty means valid."""
    errors = []
    for key in ("id", "source", "type", "scenario", "grader"):
        if key not in case:
            errors.append(f"{path}: missing required key {key!r}")
    if errors:
        return errors
    if case["type"] not in ("regression", "control"):
        errors.append(f"{path}: type must be regression|control")
    if not re.fullmatch(r"[a-z0-9][a-z0-9-]*", case["id"]):
        errors.append(f"{path}: id must be kebab-case")
    grader_errors = validate_grader(case["grader"], path)
    errors.extend(grader_errors)
    samples = case.get("samples", 5)
    if not isinstance(samples, int) or samples < 1:
        errors.append(f"{path}: samples must be a positive int")
    return errors


def validate_grader(grader, path, depth=0):
    if depth > 4:
        return [f"{path}: grader nesting too deep"]
    if not isinstance(grader, dict) or "type" not in grader:
        return [f"{path}: grader must be an object with a type"]
    t = grader["type"]
    if t not in GRADER_TYPES:
        return [f"{path}: unknown grader type {t!r}"]
    if t in ("contains", "not_contains") and not isinstance(
            grader.get("text"), str):
        return [f"{path}: {t} grader requires a text string"]
    if t in ("regex", "not_regex"):
        pat = grader.get("pattern")
        if not isinstance(pat, str):
            return [f"{path}: {t} grader requires a pattern string"]
        try:
            re.compile(pat)
        except re.error as exc:
            return [f"{path}: invalid regex: {exc}"]
    if t in ("all", "any"):
        children = grader.get("graders")
        if not isinstance(children, list) or not children:
            return [f"{path}: {t} grader requires non-empty graders list"]
        errors = []
        for child in children:
            errors.extend(validate_grader(child, path, depth + 1))
        return errors
    return []


def apply_grader(grader, output, imported_texts):
    """Plain-logic grading. Returns (passed, detail). imported_texts maps
    placeholder names to current source text so cases grade against live
    tool text, never copies (protocol rule 4)."""
    t = grader["type"]
    if t == "contains":
        needle = resolve_imports(grader["text"], imported_texts)
        ok = needle in output
        return ok, f"contains {needle[:40]!r}: {ok}"
    if t == "not_contains":
        needle = resolve_imports(grader["text"], imported_texts)
        ok = needle not in output
        return ok, f"not_contains {needle[:40]!r}: {ok}"
    if t == "regex":
        ok = bool(re.search(grader["pattern"], output, re.S))
        return ok, f"regex {grader['pattern'][:40]!r}: {ok}"
    if t == "not_regex":
        ok = not re.search(grader["pattern"], output, re.S)
        return ok, f"not_regex {grader['pattern'][:40]!r}: {ok}"
    if t == "all":
        results = [apply_grader(g, output, imported_texts)
                   for g in grader["graders"]]
        return all(r for r, _ in results), "; ".join(d for _, d in results)
    if t == "any":
        results = [apply_grader(g, output, imported_texts)
                   for g in grader["graders"]]
        return any(r for r, _ in results), "; ".join(d for _, d in results)
    raise ValueError(f"unknown grader type {t!r}")


def resolve_imports(text, imported_texts):
    """${import:name} placeholders resolve to current source file content,
    so graders track the live text instead of snapshots."""
    def _sub(m):
        return imported_texts.get(m.group(1), "")
    return re.sub(r"\$\{import:([^}]+)\}", _sub, text)


def load_imports(case, case_dir):
    """Read every file the case declares in `imports` (name -> relpath).
    Paths resolve against the repo root; missing files are empty strings
    so grading degrades to a visible failure rather than a crash."""
    texts = {}
    for name, rel in (case.get("imports") or {}).items():
        try:
            with open(rel, encoding="utf-8", errors="replace") as fh:
                texts[name] = fh.read()
        except OSError:
            texts[name] = ""
    return texts


def read_ledger(path=LEDGER):
    entries = []
    if not os.path.isfile(path):
        return entries
    with open(path, encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if line:
                entries.append(json.loads(line))
    return entries


def compare_runs(baseline, candidate, entries):
    """Per-case pass rates for two run ids. Same-model enforcement: the
    comparison is meaningless across models (protocol rule 6)."""
    def rows(run_id):
        return [e for e in entries if e.get("run") == run_id]
    b, c = rows(baseline), rows(candidate)
    if not b or not c:
        return None, "one or both run ids absent from ledger"
    b_models = {e.get("model") for e in b}
    c_models = {e.get("model") for e in c}
    if b_models != c_models:
        return None, (f"model mismatch: baseline {sorted(b_models)} vs "
                      f"candidate {sorted(c_models)} - compare same-model only")
    cases = sorted({e.get("case") for e in b + c})

    def rate(run_rows, case_id):
        samples = [e for e in run_rows if e.get("case") == case_id]
        if not samples:
            return None, 0
        # protocol rule 5: a case fails when half or more of samples fail
        passed = sum(1 for e in samples if e.get("passed"))
        return passed / len(samples), len(samples)

    table = []
    regressions = []
    for case_id in cases:
        br, bn = rate(b, case_id)
        cr, cn = rate(c, case_id)
        row = {"case": case_id, "baseline": br, "candidate": cr,
               "baseline_samples": bn, "candidate_samples": cn}
        table.append(row)
        if br is not None and cr is not None and cr < br:
            regressions.append(case_id)
    return {"cases": table, "regressions": regressions,
            "verdict": "regressed" if regressions else "improved-or-equal"}, None


def synthesize_output(workspace, transcript):
    """Grading input: the sample transcript plus a deterministic digest of
    text artifacts the sampled agent produced in its workspace. Graders
    therefore see both behavior (transcript) and outcome (files) without
    any parsing ambiguity. Binary/large/generated files are skipped."""
    parts = [transcript, "\n\n--- workspace artifacts ---"]
    skip_dirs = {".git", "__pycache__", "node_modules", ".venv"}
    for dirpath, dirnames, filenames in os.walk(workspace):
        dirnames[:] = [d for d in sorted(dirnames) if d not in skip_dirs]
        for fn in sorted(filenames):
            full = os.path.join(dirpath, fn)
            rel = os.path.relpath(full, workspace)
            try:
                if os.path.getsize(full) > 32768:
                    continue
                with open(full, encoding="utf-8", errors="strict") as fh:
                    content = fh.read()
                if "\x00" in content:
                    continue  # null byte = binary, not inspectable text
            except (OSError, UnicodeDecodeError):
                continue
            parts.append(f"### {rel}\n{content[:4000]}")
    return "\n".join(parts)


def run_one_sample(case, idx, model, timeout):
    """Run one devin -p session in an isolated temp workspace. Returns
    (synthesized_output, meta). The bundle's live hooks apply inside the
    sample exactly as they do in real work - that is the point."""
    workspace = tempfile.mkdtemp(prefix=f"beval-{case['id']}-{idx}-")
    for rel, content in (case.get("workspace_files") or {}).items():
        dest = os.path.join(workspace, rel)
        os.makedirs(os.path.dirname(dest) or workspace, exist_ok=True)
        with open(dest, "w", encoding="utf-8") as fh:
            fh.write(content)
    cmd = ["devin", "-p", case["prompt"], "--permission-mode",
           case.get("permission_mode", "smart")]
    if model:
        cmd += ["--model", model]
    try:
        proc = subprocess.run(cmd, cwd=workspace, capture_output=True,
                              text=True, encoding="utf-8", errors="replace",
                              timeout=timeout)
        transcript = proc.stdout + ("\n[stderr]\n" + proc.stderr
                                    if proc.stderr.strip() else "")
        timed_out = False
    except subprocess.TimeoutExpired:
        transcript = "[TIMEOUT]"
        timed_out = True
    output = synthesize_output(workspace, transcript)
    meta = {"workspace": workspace, "timed_out": timed_out, "idx": idx}
    return output, meta


def main():
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="mode", required=True)

    p_val = sub.add_parser("validate")
    p_val.add_argument("cases", nargs="+")

    p_smp = sub.add_parser("sample")
    p_smp.add_argument("--case", required=True)
    p_smp.add_argument("--run", required=True,
                       help="run id recorded to the ledger")
    p_smp.add_argument("--model", default=None)
    p_smp.add_argument("--samples", type=int, default=None,
                       help="override the case's sample count")
    p_smp.add_argument("--timeout", type=int, default=None,
                       help="per-sample wall-clock cap in seconds")

    p_grade = sub.add_parser("grade")
    p_grade.add_argument("--case", required=True)
    p_grade.add_argument("--sample", required=True)

    p_rec = sub.add_parser("record")
    p_rec.add_argument("--case", required=True)
    p_rec.add_argument("--model", required=True)
    p_rec.add_argument("--run", required=True)
    p_rec.add_argument("--idx", type=int, required=True)
    p_rec.add_argument("--passed", type=int, choices=(0, 1), required=True)
    p_rec.add_argument("--cost", type=int, default=0,
                       help="tokens consumed by this sample")

    p_cmp = sub.add_parser("compare")
    p_cmp.add_argument("--baseline", required=True)
    p_cmp.add_argument("--candidate", required=True)

    args = parser.parse_args()

    if args.mode == "validate":
        all_errors = []
        checked = 0
        for path in args.cases:
            try:
                case = load_case(path)
            except (OSError, json.JSONDecodeError) as exc:
                all_errors.append(f"{path}: unreadable: {exc}")
                continue
            checked += 1
            all_errors.extend(validate_case(case, path))
        if all_errors:
            print(_dumps({"ok": False, "errors": all_errors,
                          "checked": checked}))
            return 1
        print(_dumps({"ok": True, "checked": checked}))
        return 0

    if args.mode == "grade":
        try:
            case = load_case(args.case)
            with open(args.sample, encoding="utf-8", errors="replace") as fh:
                output = fh.read()
        except (OSError, json.JSONDecodeError) as exc:
            print(_dumps({"ok": False, "error": str(exc)}))
            return 1
        errors = validate_case(case, args.case)
        if errors:
            print(_dumps({"ok": False, "errors": errors}))
            return 1
        imported = load_imports(case, os.path.dirname(args.case))
        passed, detail = apply_grader(case["grader"], output, imported)
        print(_dumps({"ok": True, "passed": passed, "detail": detail,
                      "case": case["id"]}))
        return 0 if passed else 1

    if args.mode == "record":
        entry = {"ts": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                 "case": args.case, "model": args.model, "run": args.run,
                 "idx": args.idx, "passed": bool(args.passed),
                 "cost_tokens": args.cost}
        os.makedirs(os.path.dirname(LEDGER), exist_ok=True)
        with open(LEDGER, "a", encoding="utf-8") as fh:
            fh.write(json.dumps(entry, ensure_ascii=False) + "\n")
        print(_dumps({"ok": True, "recorded": entry}))
        return 0

    if args.mode == "sample":
        try:
            case = load_case(args.case)
        except (OSError, json.JSONDecodeError) as exc:
            print(_dumps({"ok": False, "error": str(exc)}))
            return 1
        errors = validate_case(case, args.case)
        if errors:
            print(_dumps({"ok": False, "errors": errors}))
            return 1
        if not isinstance(case.get("prompt"), str) or not case["prompt"]:
            print(_dumps({"ok": False, "error":
                          "case has no prompt - sampling needs the exact "
                          "task text, not just a scenario description"}))
            return 1
        n = args.samples or case.get("samples", 5)
        timeout = args.timeout or case.get("sample_timeout_sec", 420)
        imported = load_imports(case, os.path.dirname(args.case))
        model = args.model or "default"

        def one(idx):
            output, meta = run_one_sample(case, idx, args.model, timeout)
            passed, detail = apply_grader(case["grader"], output, imported)
            return idx, passed, detail, meta

        results = []
        with ThreadPoolExecutor(max_workers=min(n, 3)) as pool:
            for idx, passed, detail, meta in pool.map(one, range(n)):
                entry = {"ts": time.strftime("%Y-%m-%dT%H:%M:%SZ",
                                             time.gmtime()),
                         "case": case["id"], "model": model,
                         "run": args.run, "idx": idx, "passed": passed,
                         "cost_tokens": 0}
                os.makedirs(os.path.dirname(LEDGER), exist_ok=True)
                with open(LEDGER, "a", encoding="utf-8") as fh:
                    fh.write(json.dumps(entry, ensure_ascii=False) + "\n")
                results.append({"idx": idx, "passed": passed,
                                "timed_out": meta["timed_out"],
                                "detail": detail[:200]})
        passed_n = sum(1 for r in results if r["passed"])
        # protocol: the case fails when half or more samples fail
        case_passed = passed_n * 2 > len(results)
        print(_dumps({"ok": True, "case": case["id"], "run": args.run,
                      "model": model, "passed": passed_n,
                      "total": len(results), "case_passed": case_passed,
                      "samples": results}))
        return 0 if case_passed else 1

    if args.mode == "compare":
        entries = read_ledger()
        result, error = compare_runs(args.baseline, args.candidate, entries)
        if error:
            print(_dumps({"ok": False, "error": error}))
            return 1
        print(_dumps({"ok": True, **result}))
        return 1 if result["regressions"] else 0

    return 2


if __name__ == "__main__":
    sys.exit(main())
