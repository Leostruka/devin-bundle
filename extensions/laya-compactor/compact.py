"""compact — laya-driven transcript pruning CLI.

Reads a session transcript (JSON list of messages), asks the resident
laya worker for a keep/truncate/drop suggestion per unpinned tool
item, applies decisions pair-wise so no tool_result is orphaned, and
writes the pruned transcript plus a decisions/stats report.

Contract modes (from .devin/laya/profile.json via decision_contract):
  off     -> passthrough, original written unchanged
  shadow  -> decide and report, but do not apply (decisions only)
  assist  -> apply adopted suggestions (adoptable + calibrated)

Fallback contract: worker error / abstain / under-reduction -> the
item (or the whole transcript) is returned unchanged. Survivors are
always verbatim — never reworded.

Usage:
  python compact.py transcript.json -o pruned.json \
      [--report report.json] [--goal "task"] [--config path]
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

_EXT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_EXT / "laya-tools"))
sys.path.insert(0, str(_EXT / "laya-compactor"))

import decision_contract as dc          # noqa: E402
import transcript as tr                 # noqa: E402
import state as st                      # noqa: E402

PROFILE = "compact-item-v1"
CANDIDATES = [{"id": "keep"}, {"id": "truncate"}, {"id": "drop"}]

# Smart Window defaults (see skill context-hygiene decision table)
COMPACT_AT = 0.70
COMPACT_TO = 0.40
PRESERVE_RECENT = 6
KEEP_THRESHOLD = 0.5
TRUNCATE_HEAD = 300
MAX_STATE = 100_000
REDUCTION_FLOOR = 0.25


def _worker_argv(config):
    cli = _EXT / "laya-tools" / "laya_cli.py"
    return [sys.executable, str(cli), "serve-stdio",
            "--config", config or ""]


def _request(item, goal, mode, deadline_ms=5000):
    state, stage = st.build_state(item, goal=goal, max_state=MAX_STATE)
    return ({
        "version": 1,
        "request_id": item["id"],
        "profile": PROFILE,
        "mode": mode,
        "context": {"env_id": "laya-compactor",
                    "instance_id": "session",
                    "observation_id": item["id"]},
        "state": state,
        "candidates": CANDIDATES,
        "deadline_ms": deadline_ms,
    }, stage)


def _apply_pair_action(call_item, result_item, action):
    """Mutate texts per pair action. drop is handled by the caller."""
    if action == "truncate":
        for it in (call_item, result_item):
            if it is not None and (it.get("text") or ""):
                it["text"] = it["text"][:TRUNCATE_HEAD] + "\n...[snip]..."
                it["action"] = "truncate"


def decide(items, client, goal, mode):
    """Ask laya per unpinned item. Returns {item_id: action} where
    action in keep|truncate|drop; abstain/error -> keep (fail-safe)."""
    decisions = {}
    for it in items:
        if it["pinned"] or it["kind"] == "message":
            continue
        req, stage = _request(it, goal, mode)
        rec = client.recommend(req) if client else \
            dc.make_abstention(req["request_id"], "no_client")
        action = "keep"
        reason = rec.get("reason", "")
        if rec.get("outcome") == "suggestion" and rec.get("adoptable"):
            conf = rec.get("calibrated_probability")
            if conf is None or conf >= KEEP_THRESHOLD:
                cid = rec.get("candidate_id")
                if cid in ("keep", "truncate", "drop"):
                    action = cid
        decisions[it["id"]] = {
            "action": action, "stage": stage, "reason": reason,
            "outcome": rec.get("outcome")}
    return decisions


def pair_actions(items, decisions):
    """Resolve per-item actions into per-pair actions.

    Rule: drop only when both halves say drop; keep when either says
    keep; otherwise truncate. Guarantees no orphan tool_result.
    """
    pmap = tr.pairs(items)
    out = {}
    for pid, slot in pmap.items():
        acts = []
        for it in (slot["call"], slot["result"]):
            if it is None:
                continue
            acts.append(decisions.get(it["id"], {}).get("action", "keep"))
        if not acts:
            continue
        if acts.count("drop") == len(acts):
            out[pid] = "drop"
        elif "keep" in acts:
            out[pid] = "keep"
        else:
            out[pid] = "truncate"
    return out


def apply(items, decisions, pacts):
    """Return (kept_items, applied_stats). Drops whole pairs only."""
    dropped = {pid for pid, a in pacts.items() if a == "drop"}
    kept = []
    for it in items:
        if it["pair"] in dropped:
            it["action"] = "drop"
            continue
        _apply_pair_action(None, None, "keep")  # no-op, clarity anchor
        kept.append(it)
    for pid, action in pacts.items():
        if action == "truncate":
            slot = tr.pairs(items).get(pid, {})
            _apply_pair_action(slot.get("call"), slot.get("result"),
                               "truncate")
    return kept


def rebuild_messages(messages, items):
    """Rebuild messages from surviving items.

    Simplest correct form: pinned messages pass through verbatim; for
    messages containing tool blocks we rewrite block lists. Items carry
    (msg_index, block position via id) — here we apply action labels
    back onto the original message objects.
    """
    by_msg = {}
    for it in items:
        by_msg.setdefault(it["msg_index"], []).append(it)
    out = []
    for i, msg in enumerate(messages):
        its = by_msg.get(i, [])
        if not its:
            out.append(msg)
            continue
        if any(it.get("action") == "drop" for it in its):
            # whole pair dropped: remove the blocks that were dropped,
            # keep non-tool content of the same message
            pass
        c = msg.get("content")
        if not isinstance(c, list):
            out.append(msg)
            continue
        newc = []
        for j, b in enumerate(c):
            it = next((x for x in its if x["id"] == f"m{i}b{j}"), None)
            if it is None:
                newc.append(b)
                continue
            if it.get("action") == "drop":
                continue
            if it.get("action") == "truncate":
                b = dict(b)
                if b.get("type") == "tool_result":
                    b["content"] = it["text"]
                elif b.get("type") == "tool_use" \
                        and isinstance(b.get("input"), str):
                    b["input"] = it["text"]
            newc.append(b)
        if newc:
            m = dict(msg)
            m["content"] = newc
            out.append(m)
        elif all(x.get("action") == "drop" for x in its):
            continue
        else:
            out.append(msg)
    return out


def compact(messages, cfg, config_path="", goal="", client=None):
    """Main entry. Returns {messages, decisions, stats}."""
    mode = dc.effective_mode(cfg)
    items = tr.collect_items(messages, preserve_recent=PRESERVE_RECENT)
    orig_chars = sum(m.get("chars", 0) for m in items)
    stats = {"mode": mode, "original_chars": orig_chars,
             "items": len(items), "pairs": len(tr.pairs(items))}
    if mode == "off" or not stats["pairs"]:
        stats["reduction"] = 0.0
        stats["note"] = "off" if mode == "off" else "no_tool_pairs"
        return {"messages": messages, "decisions": {}, "stats": stats}

    t0 = time.time()
    decisions = decide(items, client, goal, mode)
    stats["decide_ms"] = int((time.time() - t0) * 1000)

    if mode == "shadow":
        return {"messages": messages, "decisions": decisions,
                "stats": stats}

    pacts = pair_actions(items, decisions)
    kept = apply(items, decisions, pacts)
    new_chars = sum(i["chars"] for i in kept if i.get("action") != "drop")
    stats["kept_chars"] = new_chars
    stats["reduction"] = (1 - new_chars / orig_chars) if orig_chars else 0.0
    stats["actions"] = {a: sum(1 for p in pacts.values() if p == a)
                        for a in ("keep", "truncate", "drop")}
    if stats["reduction"] < REDUCTION_FLOOR:
        stats["note"] = "under_reduction_floor:returning_original"
        return {"messages": messages, "decisions": decisions,
                "stats": stats}
    if not tr.orphan_check(kept):
        stats["note"] = "orphan_guard:returning_original"
        return {"messages": messages, "decisions": decisions,
                "stats": stats}
    return {"messages": rebuild_messages(messages, items),
            "decisions": decisions, "stats": stats}


def main(argv=None):
    ap = argparse.ArgumentParser(description="laya transcript compactor")
    ap.add_argument("transcript")
    ap.add_argument("-o", "--out", required=True)
    ap.add_argument("--report")
    ap.add_argument("--goal", default="")
    ap.add_argument("--config", default=".devin/laya/profile.json")
    args = ap.parse_args(argv)

    messages = json.loads(Path(args.transcript).read_text(
        encoding="utf-8"))
    cfg = dc.load_config(args.config if Path(args.config).exists()
                         else None)
    client = None
    if dc.enabled(cfg):
        from decision_client import DecisionClient
        client = DecisionClient(_worker_argv(args.config))
    try:
        result = compact(messages, cfg, config_path=args.config,
                         goal=args.goal, client=client)
    finally:
        if client:
            client.close()
    Path(args.out).write_text(
        json.dumps(result["messages"], ensure_ascii=False, indent=2),
        encoding="utf-8")
    report = {"decisions": result["decisions"], "stats": result["stats"]}
    if args.report:
        Path(args.report).write_text(
            json.dumps(report, ensure_ascii=False, indent=2),
            encoding="utf-8")
    print(json.dumps(report["stats"], ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
