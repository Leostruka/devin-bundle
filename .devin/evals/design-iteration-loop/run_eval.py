#!/usr/bin/env python3
"""Eval for the bounded design-iteration contract (R7-13 / GH #446 / #516).

Simulates the contract in skills/impeccable/SKILL.md "Bounded iteration"
against synthetic lint-finding streams and asserts the loop terminates
with the right verdict for each scenario:

  - gate pass: findings reach 0 (or all waived) before N -> "pass"
  - plateau: a cycle closes nothing -> early "plateau" abort
  - accretion: file grows >20% in a cycle that closes nothing -> abort
  - escalation: N=3 reached with open findings -> "escalate", audit written

Each case supplies cycles as observed deltas:
  {closed: n, open_after: n, checklist_progress: bool, size_delta_pct: f,
   waived_after: n}
The runner replays them through the contract state machine and compares
the produced verdict + stop cycle against expectations.

Usage: python run_eval.py [--cases cases.json] [--report report.json]
"""
import json
import os
import sys

MAX_CYCLES = 3
ACCRETION_PCT = 20.0


def run_contract(cycles):
    """Replay the bounded-iteration contract. Returns verdict dict."""
    for i, c in enumerate(cycles, start=1):
        if i > MAX_CYCLES:
            return {"verdict": "escalate", "stop_cycle": MAX_CYCLES,
                    "reason": "max cycles reached with open findings"}
        closed = c.get("closed", 0)
        open_after = c.get("open_after", 0)
        waived = c.get("waived_after", 0)
        progress = c.get("checklist_progress", False)
        delta = c.get("size_delta_pct", 0.0)

        # Gate: nothing open, or everything left is waived.
        if open_after == 0 or (open_after > 0 and waived >= open_after):
            return {"verdict": "pass", "stop_cycle": i,
                    "reason": "gate met (open==0 or all waived)"}
        # Accretion guard: big growth while closing nothing -> distill.
        if delta > ACCRETION_PCT and closed == 0:
            return {"verdict": "accretion", "stop_cycle": i,
                    "reason": "growth >20% without closing findings"}
        # Progress rule: must close a finding or a checklist item.
        if closed == 0 and not progress:
            return {"verdict": "plateau", "stop_cycle": i,
                    "reason": "cycle closed nothing"}
    return {"verdict": "escalate", "stop_cycle": MAX_CYCLES,
            "reason": "max cycles reached with open findings"}


def main():
    here = os.path.dirname(os.path.abspath(__file__))
    cases_path = sys.argv[sys.argv.index("--cases") + 1] if "--cases" in sys.argv \
        else os.path.join(here, "cases.json")
    report_path = sys.argv[sys.argv.index("--report") + 1] if "--report" in sys.argv \
        else os.path.join(here, "report.json")

    with open(cases_path, encoding="utf-8") as f:
        cases = json.load(f)["cases"]

    results, failures = [], []
    for case in cases:
        got = run_contract(case["cycles"])
        exp = case["expect"]
        ok = got["verdict"] == exp["verdict"] and \
            got["stop_cycle"] == exp["stop_cycle"]
        results.append({"id": case["id"], "expect": exp, "got": got, "ok": ok})
        if not ok:
            failures.append(case["id"])

    report = {"eval": "design-iteration-loop", "total": len(cases),
              "passed": len(cases) - len(failures), "failures": failures,
              "results": results}
    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    print(json.dumps({"ok": not failures, "passed": report["passed"],
                      "total": len(cases), "failures": failures}))
    return 0 if not failures else 1


if __name__ == "__main__":
    sys.exit(main())
