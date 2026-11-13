#!/usr/bin/env python3
"""Dory loop-sweep eval runner (issue #441).

Scores a running llama.cpp-dory server (already loaded with a chosen
n_recurrent_loops override) on a frozen laya heldout manifest. For each
case: prompt = goal + candidate shortlist -> first predicted token(s)
matched against candidate ids -> accuracy + per-call latency.

  python dory_sweep.py --cases cases.heldout.json --loops 2 \
      --server http://127.0.0.1:8377 --out report.json
"""
import argparse
import json
import sys
import urllib.request

from ai_envelope import _stamp, _dumps




def fail(msg, code=1):
    print(_dumps({"ok": False, "error": msg}))
    sys.exit(code)


def build_prompt(case):
    req = case["request"]
    goal = req.get("state", {}).get("goal", "")
    cands = req.get("candidates", [])
    lines = ["Goal: " + str(goal), "Candidates:"]
    for c in cands:
        scope = (c.get("scope") or c.get("name") or "")[:160]
        lines.append("- %s: %s" % (c["id"], scope))
    lines.append("- __none__: none of the above fit")
    lines.append("Best candidate id (answer with only the id):")
    return "\n".join(lines)


def predict(server, prompt, n_predict=10):
    body = json.dumps({
        "prompt": prompt, "n_predict": n_predict, "temperature": 0.0,
        "cache_prompt": True,
    }).encode("utf-8")
    r = urllib.request.Request(
        server.rstrip("/") + "/completion", data=body,
        headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(r, timeout=300) as resp:
        return json.loads(resp.read().decode("utf-8"))


def match(text, candidates):
    head = text.strip().split("\n")[0].strip().lower().strip('`"\' .')
    ids = [c["id"] for c in candidates] + ["__none__"]
    for cid in ids:
        if head == cid.lower():
            return cid
    for cid in ids:
        if cid.lower() in head:
            return cid
    return None


def main():
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--cases", required=True)
    ap.add_argument("--loops", type=int, required=True)
    ap.add_argument("--server", default="http://127.0.0.1:8377")
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--out")
    args = ap.parse_args()

    try:
        data = json.load(open(args.cases, encoding="utf-8"))
    except (OSError, ValueError) as e:
        fail("cases load: %s" % e, 2)
    cases = data["cases"][:args.limit or None]

    rows = []
    lat = []
    for i, c in enumerate(cases):
        try:
            r = predict(args.server, build_prompt(c))
        except Exception as e:
            rows.append({"case_id": c["case_id"], "gold": c["gold"],
                         "pred": None, "ok": False, "err": str(e)[:80]})
            continue
        text = r.get("content", "")
        pred = match(text, c["request"]["candidates"])
        t = r.get("timings", {})
        ms = (t.get("prompt_ms", 0) + t.get("predicted_ms", 0))
        lat.append(ms)
        rows.append({"case_id": c["case_id"], "gold": c["gold"],
                     "pred": pred, "ok": pred == c["gold"], "ms": round(ms),
                     "raw": text[:80]})
        print("  %d/%d %s gold=%s pred=%s %dms" % (
            i + 1, len(cases), c["case_id"], c["gold"], pred, ms),
            file=sys.stderr)

    n_ok = sum(1 for x in rows if x["ok"])
    lat_s = sorted(lat)
    p = lambda q: (lat_s[int(q * (len(lat_s) - 1))] if lat_s else 0)
    rep = {"ok": True, "loops": args.loops, "cases": len(rows),
           "acc": round(n_ok / len(rows), 4) if rows else 0,
           "correct": n_ok,
           "ms_p50": round(p(0.5)), "ms_p95": round(p(0.95)),
           "ms_mean": round(sum(lat) / len(lat)) if lat else 0,
           "laya_budget_ms": 200,
           "rows": rows}
    out = _dumps(rep, indent=1, ensure_ascii=False)
    if args.out:
        with open(args.out, "w", encoding="utf-8") as f:
            f.write(out + "\n")
    print(out)


if __name__ == "__main__":
    main()
