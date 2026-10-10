"""laya-compactor — transcript pairing, pair-wise apply, fallbacks.

Gates from ISSUE_01: no orphan tool_result, pinned untouched, verbatim
survivors byte-identical, under-reduction passthrough, mode contract.
"""
import json
import sys
from pathlib import Path

CMP_DIR = Path(__file__).resolve().parents[1] / \
    "extensions" / "laya-compactor"
LAYA_DIR = Path(__file__).resolve().parents[1] / "extensions" / "laya-tools"
sys.path.insert(0, str(LAYA_DIR))
sys.path.insert(0, str(CMP_DIR))

import decision_contract as dc   # noqa: E402
import transcript as tr          # noqa: E402
import state as st               # noqa: E402
import compact as cp             # noqa: E402


def make_transcript(n_pairs=4, noise_chars=5000):
    msgs = [{"role": "system", "content": "sys prompt"}]
    for i in range(n_pairs):
        msgs.append({
            "role": "assistant",
            "content": [
                {"type": "text", "text": f"step {i}"},
                {"type": "tool_use", "id": f"t{i}", "name": "exec",
                 "input": f"cmd {i}"},
            ]})
        msgs.append({
            "role": "user",
            "content": [
                {"type": "tool_result", "tool_use_id": f"t{i}",
                 "content": f"ok log {i}\n" + "x" * noise_chars},
            ]})
    msgs.append({"role": "user", "content": "final task"})
    return msgs


def items_of(msgs):
    return tr.collect_items(msgs, preserve_recent=cp.PRESERVE_RECENT)


# --- profile registration ---------------------------------------------------

def test_profile_registered_and_questions():
    errs = dc.validate_request({
        "version": 1, "request_id": "r1", "profile": cp.PROFILE,
        "mode": "shadow",
        "state": {"goal": "g", "snippets": "s"},
        "candidates": cp.CANDIDATES, "deadline_ms": 1000})
    assert errs == [], errs
    q = dc.build_questions(cp.PROFILE, cp.CANDIDATES)
    crit = q["compact"]["criteria"]
    assert set(crit) == {"keep", "truncate", "drop", dc.NONE_ID}


# --- collect_items ----------------------------------------------------------

def test_collect_pairs_and_pins():
    items = items_of(make_transcript())
    pmap = tr.pairs(items)
    assert len(pmap) == 4
    assert all(s["call"] is not None and s["result"] is not None
               for s in pmap.values())
    by_id = {i["id"]: i for i in items}
    assert by_id["m0"]["pinned"]                    # first message
    assert by_id["m0"]["kind"] == "message"
    results = [i for i in items if i["kind"] == "tool_result"]
    # last user msg pinned; only early pairs are unpinned
    assert any(i["pinned"] for i in items)
    assert any(not i["pinned"] for i in results)


def test_no_unpaired_result_orphans():
    msgs = [{"role": "user", "content": [
        {"type": "tool_result", "tool_use_id": "ghost",
         "content": "x"}]}]
    items = tr.collect_items(msgs)
    assert tr.orphan_check(items) is False


# --- state fitting ----------------------------------------------------------

def test_state_stages_shrink():
    it = {"kind": "tool_result", "name": "tool_result",
          "msg_index": 2, "text": "y" * 50_000, "chars": 50_000}
    state, stage = st.build_state(it, max_state=2000)
    assert len(state["snippets"]) <= 2000
    assert stage >= 1
    assert "note=" in state["snippets"]
    # forbidden state keys never appear
    assert set(state) <= {"goal", "snippets"}


# --- decide/apply -----------------------------------------------------------

class FakeClient:
    """Returns per-item suggestions keyed by item text marker."""
    def __init__(self, table):
        self.table = table

    def recommend(self, req):
        rid = req["request_id"]
        cid = self.table.get(rid, "keep")
        rec = dc.make_abstention(rid, "unused")
        rec.update({"outcome": "suggestion", "candidate_id": cid,
                    "adoptable": True, "calibrated_probability": 0.9,
                    "mode": "assist", "reason": "fake",
                    "model_identity": "fake",
                    "profile_version": cp.PROFILE})
        rec["context"] = req["context"]
        return rec


def cfg(mode):
    c = dict(dc._DEFAULT_CONFIG)
    c["mode"] = mode
    return c


def test_assist_drop_only_when_both_say_drop():
    msgs = make_transcript()
    items = items_of(msgs)
    # pair 0: call drop, result keep -> survives (no orphan)
    dec = {"m1b1": {"action": "drop"}, "m2b0": {"action": "keep"}}
    pacts = cp.pair_actions(items, _full_dec(items, dec))
    pid = items[1]["pair"] if items[1]["kind"] == "message" else None
    # find pair containing m1b1
    pmap = tr.pairs(items)
    target = [k for k, s in pmap.items()
              if s["call"] and s["call"]["id"] == "m1b1"][0]
    assert pacts[target] == "keep"


def _full_dec(items, overrides):
    d = {i["id"]: {"action": "keep"} for i in items}
    for k, v in overrides.items():
        d[k] = v
    return d


def test_both_drop_removes_pair_verbatim_survivors():
    msgs = make_transcript(n_pairs=2)
    items = items_of(msgs)
    pmap = tr.pairs(items)
    victim = sorted(pmap)[0]
    dec = _full_dec(items, {})
    slot = pmap[victim]
    dec[slot["call"]["id"]] = {"action": "drop"}
    dec[slot["result"]["id"]] = {"action": "drop"}
    pacts = cp.pair_actions(items, dec)
    assert pacts[victim] == "drop"
    kept = cp.apply(items, dec, pacts)
    assert tr.orphan_check(kept)
    # survivor texts byte-identical
    orig = {i["id"]: i["text"] for i in tr.collect_items(msgs)}
    for i in kept:
        if i.get("action") != "truncate":
            assert i["text"] == orig[i["id"]]


def test_truncate_head_applied():
    msgs = make_transcript(n_pairs=2, noise_chars=2000)
    items = items_of(msgs)
    pmap = tr.pairs(items)
    victim = sorted(pmap)[0]
    dec = _full_dec(items, {})
    for it in pmap[victim].values():
        dec[it["id"]] = {"action": "truncate"}
    pacts = cp.pair_actions(items, dec)
    cp.apply(items, dec, pacts)
    for it in pmap[victim].values():
        assert len(it["text"]) <= cp.TRUNCATE_HEAD + 16


def test_mode_off_passthrough():
    msgs = make_transcript()
    out = cp.compact(msgs, cfg("off"))
    assert out["messages"] is msgs
    assert out["stats"]["mode"] == "off"


def test_shadow_decides_but_never_applies():
    msgs = make_transcript()
    out = cp.compact(msgs, cfg("shadow"), client=FakeClient({}))
    assert out["messages"] is msgs
    assert out["stats"]["mode"] == "shadow"


def test_assist_under_reduction_floor_returns_original():
    # tiny transcript: nothing unpinned worth dropping
    msgs = [{"role": "system", "content": "s"},
            {"role": "user", "content": "hi"}]
    out = cp.compact(msgs, cfg("assist"), client=FakeClient({}))
    assert out["messages"] is msgs


def test_abstain_means_keep():
    msgs = make_transcript()
    items = items_of(msgs)
    dec = cp.decide(items, None, "", "assist")  # client=None -> abstain
    assert all(d["action"] == "keep" for d in dec.values())


# --- rebuild ----------------------------------------------------------------

def test_rebuild_drops_pair_blocks():
    msgs = make_transcript(n_pairs=2)
    items = items_of(msgs)
    pmap = tr.pairs(items)
    victim = sorted(pmap)[0]
    dec = _full_dec(items, {})
    for it in pmap[victim].values():
        dec[it["id"]] = {"action": "drop"}
    pacts = cp.pair_actions(items, dec)
    kept = cp.apply(items, dec, pacts)
    rebuilt = cp.rebuild_messages(msgs, items)
    flat = json.dumps(rebuilt)
    assert "cmd 0" not in flat or "tool_result" not in flat
    assert "final task" in flat
    # no orphaned tool_result anywhere in rebuilt output
    ids = set()
    for m in rebuilt:
        c = m.get("content")
        if isinstance(c, list):
            for b in c:
                if b.get("type") == "tool_use":
                    ids.add(b.get("id"))
    for m in rebuilt:
        c = m.get("content")
        if isinstance(c, list):
            for b in c:
                if b.get("type") == "tool_result":
                    assert b.get("tool_use_id") in ids
