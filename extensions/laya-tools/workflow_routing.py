"""workflow_routing — optional Laya assist for skill/triage routing.

Assists ONLY ambiguity: explicit triggers always win and never reach
the model. Two stages over the existing manifest catalog: family
(closed labels) -> at most 8 catalog entries -> suggested skill name.

The decision process performs no side effects: no tracker calls, no
comments, no transitions, no process spawning, no writes. It hands a
label to the responsible agent and stops.
"""
from __future__ import annotations

import secrets
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import decision_contract as dc  # noqa: E402

FAMILIES = dc._PROFILES["skill-family-v1"][2]

# Deterministic keyword map from manifest purpose text to a family.
# Maintainer-owned; a miss lands in "assistance", never in a guess.
FAMILY_MARKERS = {
    "development": ("code", "implement", "refactor", "test", "build",
                    "debug", "fix", "git", "review", "tdd"),
    "investigation": ("research", "explore", "analyz", "audit",
                      "diagnos", "investigat", "search", "inspect"),
    "operations": ("deploy", "ci", "release", "merge", "branch",
                   "install", "docker", "infra", "monitor", "hook"),
    "data": ("data", "sql", "database", "query", "chart", "dataset",
             "csv", "metric"),
    "visual": ("spline", "image", "video", "media", "design", "ui",
               "screenshot", "render", "3d", "canvas"),
    "knowledge": ("memory", "knowledge", "ontology", "obsidian",
                  "note", "document", "extract", "learn"),
    "assistance": ("ask", "intake", "triage", "plan", "question",
                   "handoff", "route", "skill"),
}


def requires_model(explicit_skill, candidates=None):
    """Explicit triggers bypass the model entirely. The model is only
    for requests with no explicit skill selection."""
    return not (isinstance(explicit_skill, str)
                and explicit_skill.strip())


def load_catalog(manifest):
    """manifest.json -> [{id, purpose}] preserving manifest order."""
    skills = (manifest or {}).get("skills") or []
    return [{"id": s["name"], "purpose": str(s.get("purpose") or "")}
            for s in skills
            if isinstance(s, dict) and isinstance(s.get("name"), str)]


def assign_family(entry):
    """Deterministic family for a catalog entry; unclassified ->
    'assistance'."""
    hay = (entry.get("id", "") + " " + entry.get("purpose", "")).lower()
    for fam, markers in FAMILY_MARKERS.items():
        if any(m in hay for m in markers):
            return fam
    return "assistance"


def shortlist(family, catalog, limit=dc.MAX_CANDIDATES):
    """Catalog entries assigned to `family`, in manifest order,
    capped at 8."""
    return [e for e in catalog or [] if assign_family(e) == family
            ][:limit]


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


def recommend(client, catalog, goal, mode="shadow"):
    """family -> <=8 candidates -> suggested skill name. Returns a
    recommendation dict; callers act on `candidate_id` only after
    their own checks. No side effects here."""
    f_req = _request("skill-family-v1", goal,
                     [{"id": f, "role": "family", "name": f,
                       "scope": "routing"} for f in FAMILIES], mode)
    f_reply = client.recommend(f_req)
    if not isinstance(f_reply, dict) \
            or dc.validate_recommendation(f_reply, f_req) \
            or f_reply.get("outcome") != "suggestion":
        return _abstain(f_req, "family_abstained")

    entries = shortlist(f_reply["candidate_id"], catalog)
    if not entries:
        return _abstain(f_req, "empty_family_shortlist")

    s_req = _request("skill-pick-v1", goal,
                     [{"id": e["id"], "role": "skill",
                       "name": e["id"],
                       "scope": e["purpose"][:200]}
                      for e in entries], mode)
    s_reply = client.recommend(s_req)
    if not isinstance(s_reply, dict) \
            or dc.validate_recommendation(s_reply, s_req):
        return _abstain(s_req, "invalid_reply")
    if s_reply.get("outcome") == "suggestion":
        s_reply["family"] = f_reply["candidate_id"]
    return s_reply
