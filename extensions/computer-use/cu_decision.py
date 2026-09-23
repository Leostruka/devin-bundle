"""cu_decision — Laya-powered target suggestions for computer-use.

Shadow plumbing only: observed elements (UIA/DOM) become a closed set
of at most 8 candidates; a worker recommendation is validated,
sanitized and logged. There is NO execution path here — this module
cannot click, type, or dispatch anything.

Adoption gate: adoptable() requires every binding field
(env/instance/observation/capabilities/policy) to match the CURRENT
context, plus mode="assist" and adoptable=True on a validated
recommendation. A stale or shadow suggestion is never eligible.
The user chooses the environment; Laya never changes it.
"""
from __future__ import annotations

import json
import secrets
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parents[1]
                    / "laya-tools"))
import decision_contract as dc  # noqa: E402

BINDING_FIELDS = ("env_id", "instance_id", "observation_id",
                  "capabilities_digest", "policy_digest")


def build_candidates(elements, limit=dc.MAX_CANDIDATES):
    """Observed UIA/DOM nodes -> closed candidate set. Only enabled,
    identified elements qualify; ids are made unique deterministically."""
    cands, seen = [], set()
    for el in elements or []:
        if not isinstance(el, dict):
            continue
        if el.get("enabled", True) is not True:
            continue
        cid = el.get("id")
        if not isinstance(cid, str) or not cid or cid == dc.NONE_ID:
            continue
        if cid in seen:
            cid = f"{cid}#{len(seen)}"
        seen.add(cid)
        cands.append({
            "id": cid,
            "role": str(el.get("role") or "element"),
            "name": str(el.get("name") or ""),
            "scope": str(el.get("scope") or ""),
        })
        if len(cands) >= limit:
            break
    return cands


def exact_match(goal, candidates):
    """Deterministic short-circuit: a goal that exactly equals one
    candidate name returns that id without ever calling the model."""
    if not isinstance(goal, str):
        return None
    g = goal.strip().casefold()
    if not g:
        return None
    hits = [c["id"] for c in candidates
            if c["name"].strip().casefold() == g]
    return hits[0] if len(hits) == 1 else None


def make_request(context, goal, candidates, mode="shadow",
                 deadline_ms=1000, language=None):
    req = {
        "version": dc.VERSION,
        "request_id": f"d-{secrets.token_hex(6)}",
        "profile": "ui-target-v1",
        "mode": mode,
        "context": {k: v for k, v in (context or {}).items()
                    if k in BINDING_FIELDS},
        "state": {"goal": str(goal)},
        "candidates": candidates,
        "deadline_ms": int(deadline_ms),
    }
    if language:
        req["language"] = str(language)
    return req


def _sanitized(rec):
    """What gets logged: ids, digests, outcome — never goal text,
    never element contents."""
    return {k: rec.get(k) for k in
            ("request_id", "outcome", "candidate_id", "reason",
             "mode", "adoptable", "model_identity", "profile_version",
             "raw_confidence", "raw_top_probability",
             "calibrated_probability", "calibration_id", "context")}


def suggest(client, context, goal, elements, log_path=None,
            mode="shadow", deadline_ms=1000, language=None):
    """Closed-set suggestion. Zero candidates or an exact match never
    reach the model. The returned dict has no execution semantics."""
    candidates = build_candidates(elements)
    if not candidates:
        rec = dc.make_abstention("", "no_candidates")
        rec["context"] = dict(context or {})
        rec["mode"] = mode
        rec["profile_version"] = "ui-target-v1"
        _log(log_path, rec)
        return rec
    hit = exact_match(goal, candidates)
    if hit is not None:
        rec = dc.make_abstention("", "exact_match")
        rec.update({"outcome": "suggestion", "candidate_id": hit,
                    "reason": "exact_match",
                    "context": dict(context or {}), "mode": mode,
                    "profile_version": "ui-target-v1"})
        _log(log_path, rec)
        return rec
    request = make_request(context, goal, candidates, mode=mode,
                           deadline_ms=deadline_ms, language=language)
    reply = client.recommend(request)
    errs = dc.validate_recommendation(reply, request) \
        if isinstance(reply, dict) else ["reply_not_object"]
    if errs:
        rec = dc.make_abstention(request["request_id"],
                                 "invalid_reply:" + errs[0])
        rec["context"] = dict(request["context"])
        rec["mode"] = mode
        rec["profile_version"] = "ui-target-v1"
        _log(log_path, rec)
        return rec
    _log(log_path, reply)
    return reply


def _log(log_path, rec):
    if not log_path:
        return
    try:
        with open(log_path, "a", encoding="utf-8") as f:
            f.write(json.dumps(_sanitized(rec), ensure_ascii=False)
                    + "\n")
    except OSError:
        pass


def adoptable(recommendation, current_context):
    """The only gate a future assist path may use: suggestion outcome,
    mode assist, adoptable flag, and EVERY binding field matching the
    current context. Missing fields fail closed."""
    if not isinstance(recommendation, dict) \
            or not isinstance(current_context, dict):
        return False
    if recommendation.get("outcome") != "suggestion":
        return False
    if recommendation.get("adoptable") is not True:
        return False
    if recommendation.get("mode") != "assist":
        return False
    rec_ctx = recommendation.get("context")
    if not isinstance(rec_ctx, dict):
        rec_ctx = recommendation
    for f in BINDING_FIELDS:
        if not rec_ctx.get(f) or rec_ctx.get(f) != current_context.get(f):
            return False
    return True
