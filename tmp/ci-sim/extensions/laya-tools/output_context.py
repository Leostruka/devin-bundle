"""output_context — optional context labels on tool outputs.

annotate() adds a `context_suggestion` field and nothing else. Exit
codes, status strings, stderr text and provenance pass through
unchanged — classification can contextualize an output, never rewrite
it. Source content is treated as bounded data, never executed.
"""
from __future__ import annotations

import secrets
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import decision_contract as dc  # noqa: E402

PROFILE = "output-context-v1"
LABELS = set(dc._PROFILES[PROFILE][2])
MAX_EXCERPT = 4000


def normalize(result):
    """Authoritative fields extracted for classification; content is
    a bounded excerpt (data, never executed)."""
    r = result if isinstance(result, dict) else {}
    text = " ".join(str(r.get(k) or "") for k in
                    ("stdout", "stderr", "output", "error"))
    return {
        "tool_name": str(r.get("tool") or r.get("tool_name") or ""),
        "op_kind": str(r.get("op") or r.get("operation") or ""),
        "exit_code": r.get("exit_code"),
        "status": str(r.get("status") or ""),
        "provenance": r.get("provenance")
        if isinstance(r.get("provenance"), dict) else {},
        "excerpt": text.strip()[:MAX_EXCERPT],
    }


def _label_of(suggestion):
    if not isinstance(suggestion, dict):
        return dc.NONE_ID, None
    label = suggestion.get("candidate_id") or suggestion.get("choice")
    conf = suggestion.get("raw_confidence",
                          suggestion.get("confidence"))
    return (label if label in LABELS else dc.NONE_ID), conf


def annotate(result, suggestion):
    """Copy of `result` plus context_suggestion. Authoritative fields
    are copied, not interpreted — a model label cannot change
    exit_code, status, or hide output."""
    out = dict(result) if isinstance(result, dict) else {}
    label, conf = _label_of(suggestion)
    out["context_suggestion"] = {
        "label": label,
        "confidence": conf if dc._is_num(conf) else None,
        "profile": PROFILE,
    }
    return out


def suggest(client, result, mode="shadow"):
    """Classify a tool result through the worker, then annotate.
    Invalid replies degrade to __none__; the result is never lost."""
    n = normalize(result)
    request = {
        "version": dc.VERSION,
        "request_id": f"d-{secrets.token_hex(6)}",
        "profile": PROFILE, "mode": mode, "context": {},
        "state": {"goal": "classify this tool output",
                  "snippets": n["excerpt"],
                  "app": n["tool_name"]},
        "candidates": [{"id": l, "role": "label", "name": l,
                        "scope": "output"} for l in sorted(LABELS)],
        "deadline_ms": 1000,
    }
    reply = client.recommend(request)
    if isinstance(reply, dict) \
            and not dc.validate_recommendation(reply, request):
        return annotate(result, {"choice": reply.get("candidate_id"),
                                 "raw_confidence":
                                 reply.get("raw_confidence")})
    return annotate(result, None)
