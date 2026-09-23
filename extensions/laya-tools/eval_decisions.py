"""eval_decisions — deterministic evaluation over FROZEN captures.

Consumes a frozen manifest: labeled cases with the exact request sent
and the exact reply recorded. It never calls an engine, never
dispatches tools, never reads production data, never flips a feature
flag. Report content depends only on manifest bytes.

  eval_decisions.py --manifest frozen.json --mode evaluate --out r.json

Manifest shape (authored by the maintainer, not generated to favor a
result):
  {"version": 1, "frozen": true,
   "cases": [{"case_id", "gold": candidate_id|"__none__",
              "request": {...§5.1...}, "reply": {...§5.1...}}]}
"""
from __future__ import annotations

import argparse
import json
import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import decision_contract as dc  # noqa: E402

OUTCOMES = ("correct", "wrong", "abstained", "correct_abstain",
            "shortlist_miss")


def wilson_lower(k, n, z=1.645):
    """Wilson score lower bound for k successes in n trials.
    z=1.645 gives a one-sided 95% lower confidence bound — the right
    shape for a floor (two-sided 95% would use 1.96)."""
    if n <= 0:
        return 0.0
    p = k / n
    denom = 1.0 + z * z / n
    center = p + z * z / (2 * n)
    spread = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n))
    return min(1.0, max(0.0, (center - spread) / denom))


def score_case(case):
    """Classify one frozen case. Gold '__none__' means the correct
    answer was abstention."""
    gold = case.get("gold")
    req = case.get("request") or {}
    reply = case.get("reply") or {}
    cands = {c.get("id") for c in req.get("candidates") or []
             if isinstance(c, dict)}
    picked = reply.get("candidate_id")
    if gold not in cands and gold != dc.NONE_ID:
        return {"case_id": case.get("case_id"), "outcome":
                "shortlist_miss", "gold": gold, "picked": picked}
    if picked in (None, dc.NONE_ID) or \
            reply.get("outcome") == "abstain":
        return {"case_id": case.get("case_id"),
                "outcome": "correct_abstain" if gold == dc.NONE_ID
                else "abstained",
                "gold": gold, "picked": picked}
    return {"case_id": case.get("case_id"),
            "outcome": "correct" if picked == gold else "wrong",
            "gold": gold, "picked": picked}


def evaluate(cases, name="eval"):
    """Aggregate metrics over frozen cases in their manifest order."""
    scored = [score_case(c) for c in cases]
    total = len(scored)
    counts = {o: sum(1 for s in scored if s["outcome"] == o)
              for o in OUTCOMES}
    decided = counts["correct"] + counts["wrong"]
    decided_gold = total - counts["shortlist_miss"]
    return {
        "name": name,
        "total": total,
        **counts,
        "decided": decided,
        "accuracy": (counts["correct"] / decided) if decided else None,
        "wilson_accuracy_low": wilson_lower(counts["correct"], decided)
        if decided else None,
        "coverage": (decided / decided_gold) if decided_gold else None,
        "abstain_precision": (
            counts["correct_abstain"]
            / (counts["correct_abstain"] + counts["abstained"]))
        if (counts["correct_abstain"] + counts["abstained"]) else None,
        "cases": scored,
    }


def compare(report_b0, report_b1):
    """Same candidates, same case order — delta of headline metrics."""
    def _d(key):
        a, b = report_b0.get(key), report_b1.get(key)
        return None if a is None or b is None else b - a
    return {
        "names": [report_b0.get("name"), report_b1.get("name")],
        "accuracy_delta": _d("accuracy"),
        "coverage_delta": _d("coverage"),
        "abstained_delta": report_b1.get("abstained", 0)
        - report_b0.get("abstained", 0),
        "shortlist_miss_delta": report_b1.get("shortlist_miss", 0)
        - report_b0.get("shortlist_miss", 0),
    }


def _emit(obj, code=0):
    print(json.dumps(obj, ensure_ascii=False))
    return code


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--manifest", required=True)
    p.add_argument("--mode", choices=["evaluate"], required=True)
    p.add_argument("--out", required=True)
    p.add_argument("--name", default="eval")
    args = p.parse_args(argv)

    try:
        manifest = json.loads(
            Path(args.manifest).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as e:
        return _emit({"ok": False, "error": f"manifest_unreadable:{e}"}, 2)
    if not isinstance(manifest, dict) or manifest.get("frozen") is not True:
        return _emit({"ok": False, "error":
                      "manifest_not_frozen:evaluate only consumes "
                      "frozen captures"}, 2)
    cases = manifest.get("cases")
    if not isinstance(cases, list):
        return _emit({"ok": False, "error": "manifest_cases_invalid"}, 2)
    report = evaluate(cases, name=args.name)
    Path(args.out).write_text(
        json.dumps(report, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8")
    return _emit({"ok": True, "out": str(args.out),
                  "total": report["total"],
                  "accuracy": report["accuracy"],
                  "coverage": report["coverage"]})


if __name__ == "__main__":
    sys.exit(main())
