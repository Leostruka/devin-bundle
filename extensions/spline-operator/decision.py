"""decision — Laya-assisted Spline tool recommendation (read-only).

Two-stage narrowing over a manifest the CALLER already fetched:
stage 1 classifies the goal into a closed domain (spline-domain-v1),
stage 2 picks one tool from the resulting shortlist of real manifest
entries (spline-tool-v1). The suggestion can only reference a tool
present in that exact manifest, pinned by manifest_hash.

This module never launches Spline, never kills it, never calls a tool,
never exports, and never produces code — `3d_run_code` gets nothing
from here. manifest_matches() is the freshness gate: a suggestion made
against an older manifest is unusable.
"""
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parents[1]
                    / "laya-tools"))
import decision_contract as dc  # noqa: E402

# Domain -> name/description markers. Deterministic substring match;
# a tool qualifies if ANY marker hits its name or description.
DOMAIN_MARKERS = {
    "scene_3d": ("3d_", "scene", "object", "camera", "light",
                 "material", "primitive"),
    "canvas_2d": ("2d_", "canvas", "shape", "path", "vector",
                  "text", "stroke", "fill"),
    "inspect": ("inspect", "get_", "list_", "describe", "snapshot",
                "read", "query"),
    "export": ("export", "render", "save_", "download", "png",
               "svg", "video"),
}


def manifest_digest(manifest):
    """Canonical sha256 over the manifest (tools + editor/scene ids).
    Binds a recommendation to the exact manifest it was made from."""
    blob = json.dumps(manifest, sort_keys=True,
                      ensure_ascii=False).encode("utf-8")
    return hashlib.sha256(blob).hexdigest()


def manifest_matches(recommendation, current_hash):
    """Pure freshness gate: the recommendation's manifest_hash must be
    a non-empty string equal to the current one."""
    if not isinstance(recommendation, dict):
        return False
    rec_hash = recommendation.get("manifest_hash")
    return isinstance(rec_hash, str) and bool(rec_hash) \
        and isinstance(current_hash, str) and bool(current_hash) \
        and rec_hash == current_hash


def shortlist(domain, manifest):
    """Tool names from the manifest matching the domain markers,
    in manifest order. Unknown domain -> empty."""
    markers = DOMAIN_MARKERS.get(domain)
    if not markers:
        return []
    tools = (manifest or {}).get("tools") or []
    out = []
    for t in tools:
        if not isinstance(t, dict) or not isinstance(t.get("name"), str):
            continue
        hay = (t["name"] + " " + str(t.get("description") or "")).lower()
        if any(m in hay for m in markers):
            out.append(t["name"])
    return out[:dc.MAX_CANDIDATES]


def _candidates(names, manifest):
    by_name = {t.get("name"): t for t in (manifest or {}).get("tools")
               or [] if isinstance(t, dict)}
    return [{"id": n, "role": "tool",
             "name": n,
             "scope": str(by_name.get(n, {}).get("description") or "")
             [:200]} for n in names]


def _request(profile, goal, candidates, mode):
    import secrets
    return {"version": dc.VERSION,
            "request_id": f"d-{secrets.token_hex(6)}",
            "profile": profile, "mode": mode,
            "context": {},
            "state": {"goal": str(goal)},
            "candidates": candidates,
            "deadline_ms": 1000}


def _abstain(request, reason, digest):
    rec = dc.make_abstention(request["request_id"], reason)
    rec["mode"] = request["mode"]
    rec["profile_version"] = request["profile"]
    rec["manifest_hash"] = digest
    return rec


def recommend(client, manifest, goal, mode="shadow"):
    """Two-stage suggestion. Result references only a tool that exists
    in `manifest`; carries manifest_hash for the freshness gate. Never
    returns args/code/permissions — suggestion only."""
    digest = manifest_digest(manifest)

    labels = dc._PROFILES["spline-domain-v1"][2]
    d_req = _request("spline-domain-v1", goal,
                     [{"id": l, "role": "domain", "name": l,
                       "scope": "spline"} for l in labels], mode)
    d_reply = client.recommend(d_req)
    if not isinstance(d_reply, dict) \
            or dc.validate_recommendation(d_reply, d_req) \
            or d_reply.get("outcome") != "suggestion":
        return _abstain(d_req, "domain_abstained", digest)

    names = shortlist(d_reply["candidate_id"], manifest)
    if not names:
        return _abstain(d_req, "empty_shortlist", digest)

    t_req = _request("spline-tool-v1", goal,
                     _candidates(names, manifest), mode)
    t_reply = client.recommend(t_req)
    manifest_names = {t.get("name") for t in (manifest or {}).get("tools")
                      or [] if isinstance(t, dict)}
    if not isinstance(t_reply, dict) \
            or dc.validate_recommendation(t_reply, t_req):
        return _abstain(t_req, "invalid_reply", digest)
    if t_reply.get("outcome") != "suggestion":
        t_reply["manifest_hash"] = digest
        return t_reply
    if t_reply["candidate_id"] not in manifest_names:
        return _abstain(t_req, "tool_not_in_manifest", digest)
    t_reply["manifest_hash"] = digest
    t_reply["domain"] = d_reply["candidate_id"]
    return t_reply
