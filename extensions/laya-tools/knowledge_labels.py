"""knowledge_labels — Laya labels on already-extracted spans.

attach() returns an annotated COPY: source_hash, quote and line refs
pass through untouched and the label sits under `annotation` with
confirmed=False. Unconfirmed suggestions never join the factual base —
write/merge still goes through the existing approval and deterministic
validation. Raw transcripts, source cues and user preferences are
never edited to match a prediction. No generated summary counts as
evidence.
"""
from __future__ import annotations

import secrets
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import decision_contract as dc  # noqa: E402

PROFILE = "knowledge-label-v1"
ONTOLOGY = frozenset(dc._PROFILES[PROFILE][2])


def attach(span, label, confidence=None):
    """Annotated copy of `span`. Label must be in the approved
    ontology; span must carry provenance (source_hash + quote)."""
    if not isinstance(span, dict) or not span.get("source_hash") \
            or not span.get("quote"):
        raise ValueError("span_provenance_missing:need source_hash+quote")
    if label not in ONTOLOGY:
        raise ValueError(f"label_not_in_ontology:{label}")
    out = dict(span)
    ann = {"label": label, "confirmed": False, "source": "laya",
           "profile": PROFILE}
    if dc._is_num(confidence):
        ann["confidence"] = float(confidence)
    out["annotation"] = ann
    return out


def suggest(client, span, mode="shadow"):
    """Classify a span's quote against the ontology. Invalid replies
    leave the span unlabelled; nothing is persisted here."""
    if not isinstance(span, dict) or not span.get("source_hash") \
            or not span.get("quote"):
        raise ValueError("span_provenance_missing:need source_hash+quote")
    request = {
        "version": dc.VERSION,
        "request_id": f"d-{secrets.token_hex(6)}",
        "profile": PROFILE, "mode": mode, "context": {},
        "state": {"goal": "label this extracted span",
                  "element_text": str(span.get("quote"))[:2000]},
        "candidates": [{"id": l, "role": "label", "name": l,
                        "scope": "knowledge"} for l in sorted(ONTOLOGY)],
        "deadline_ms": 1000,
    }
    reply = client.recommend(request)
    if not isinstance(reply, dict) \
            or dc.validate_recommendation(reply, request) \
            or reply.get("outcome") != "suggestion":
        return dict(span)          # unlabelled copy, evidence intact
    try:
        return attach(span, reply["candidate_id"],
                      confidence=reply.get("raw_confidence"))
    except ValueError:
        return dict(span)
