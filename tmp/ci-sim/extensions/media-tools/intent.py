"""intent — Laya-assisted media workflow/preset suggestion.

Exact aliases and explicit names always win; the model only classifies
textual description + declared media kind against the existing catalog.
The result references an existing preset/workflow for PREVIEW — output
files, parameters, camera, overwrite and delete stay outside the model.
`brag`, `impeccable`, diagrams are workflow destinations, not renderer
variants.
"""
from __future__ import annotations

import re
import secrets
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]
                    / "laya-tools"))
import decision_contract as dc  # noqa: E402

INTENT_PROFILE = "media-intent-v1"
PRESET_PROFILE = "media-preset-v1"
PRESET_INTENTS = {"stylize_image", "stylize_video"}


def resolve_explicit(name, available):
    """Membership check only — no inference. Returns the name when it
    exists in the catalog, else None."""
    if isinstance(name, str) and name in (available or ()):
        return name
    return None


def _explicit_in_text(text, available):
    """Exact preset id appearing as a whole token wins outright."""
    if not isinstance(text, str):
        return None
    for name in available or []:
        if re.search(rf"(?<![\w-]){re.escape(name)}(?![\w-])",
                     text, re.I):
            return name
    return None


def _request(profile, goal, candidates, mode):
    return {"version": dc.VERSION,
            "request_id": f"d-{secrets.token_hex(6)}",
            "profile": profile, "mode": mode, "context": {},
            "state": {"goal": str(goal)},
            "candidates": candidates,
            "deadline_ms": 1000}


def _abstain(request, reason):
    rec = dc.make_abstention(request["request_id"], reason)
    rec["mode"] = request["mode"]
    rec["profile_version"] = request["profile"]
    return rec


def suggest(client, text, presets, media_kind=None, mode="shadow"):
    """explicit -> intent -> preset. Suggestion only: the result names
    a workflow destination or an existing preset id. It never carries
    params, output paths, camera, overwrite or delete decisions."""
    presets = [p for p in (presets or []) if isinstance(p, str) and p]

    hit = _explicit_in_text(text, presets)
    if hit:
        rec = dc.make_abstention("", "explicit_name")
        rec.update({"outcome": "suggestion", "candidate_id": hit,
                    "reason": "explicit_name", "mode": mode,
                    "profile_version": PRESET_PROFILE})
        return rec

    i_labels = dc._PROFILES[INTENT_PROFILE][2]
    i_req = _request(INTENT_PROFILE, text,
                     [{"id": l, "role": "intent", "name": l,
                       "scope": "media"} for l in i_labels], mode)
    i_reply = client.recommend(i_req)
    if not isinstance(i_reply, dict) \
            or dc.validate_recommendation(i_reply, i_req) \
            or i_reply.get("outcome") != "suggestion":
        return _abstain(i_req, "intent_abstained")
    intent = i_reply["candidate_id"]

    if intent not in PRESET_INTENTS:
        i_reply["intent"] = intent     # workflow destination, done
        return i_reply

    names = presets[:dc.MAX_CANDIDATES]
    if not names:
        return _abstain(i_req, "no_presets_available")
    p_req = _request(PRESET_PROFILE, text,
                     [{"id": n, "role": "preset", "name": n,
                       "scope": str(media_kind or "")}
                      for n in names], mode)
    p_reply = client.recommend(p_req)
    if not isinstance(p_reply, dict) \
            or dc.validate_recommendation(p_reply, p_req):
        return _abstain(p_req, "invalid_reply")
    if p_reply.get("outcome") == "suggestion":
        if p_reply["candidate_id"] not in presets:
            return _abstain(p_req, "preset_not_in_catalog")
        p_reply["intent"] = intent
    return p_reply
