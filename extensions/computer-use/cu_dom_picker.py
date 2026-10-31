"""cu_dom_picker — JEV-6 DOM action-target suggestions (stdlib only).

A DOM/UIA snapshot becomes a deterministic shortlist of at most 8
candidates, then reuses the existing cu_decision contract: output is a
typed `suggestion` or `abstain` — there is NO click, dispatch or
coordinate path in this module. abstain never authorizes a fallback.

Actionability/staleness contract (adapts, never duplicates,
cu_decision):
- disabled (`enabled` not True), unidentifiable, `unsafe` (password
  inputs, script/iframe, caller-flagged) or `actionable is False`
  elements are filtered before candidacy; nothing left -> abstain.
- snapshot carrying `"stale": true`, or an `observation_id` that does
  not match the caller's expected observation, abstains "stale_*" —
  a candidate from an old snapshot is never suggested.
- mode off (default) -> "feature_off" abstain; shadow/assist with the
  daemon down -> "daemon_unavailable" abstain. The deterministic
  policy is the fallback, matching the existing consumer.

CLI (offline-capable, feeds scrape-tools pipelines):
  python cu_dom_picker.py --snapshot snap.json --goal "Save" \
      [--observation-id obs-1] [--config profile.json] [--mode auto]
Snapshot JSON: {"observation_id": ..., "stale": bool,
                "elements": [{id, role, name, scope, enabled, unsafe,
                              actionable}]} or scrape/parse
{"nodes": [{tag, text, attrib}]} — nodes are adapted in-process.
JSON on stdout: {"ok": true, ...recommendation fields...}.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parents[1]
                    / "laya-tools"))
import decision_contract as dc
import cu_decision as cd
import laya_client as lc

PROFILE = "ui-target-v1"
MAX_SNAPSHOT_BYTES = 5_000_000
MAX_SNAPSHOT_ELEMENTS = 10_000
UNSAFE_TAGS = {"script", "iframe", "object", "embed"}
UNSAFE_INPUT_TYPES = {"password", "hidden"}
INTERACTIVE_ROLES = {"button", "link", "menuitem", "tab", "checkbox",
                     "radio", "combobox", "textbox", "searchbox",
                     "slider", "option", "switch", "listitem",
                     "treeitem"}
_TAG_ROLE = {"button": "button", "a": "link", "input": "textbox",
             "select": "combobox", "option": "option",
             "textarea": "textbox", "summary": "button",
             "li": "listitem", "label": "text"}


def read_bounded(source, limit):
    """Bounded raw input: reads at most limit+1 bytes, before decode.
    Returns decoded text, or None when the source exceeds limit bytes.
    Raises OSError on read failures."""
    if source == "-":
        src = getattr(sys.stdin, "buffer", sys.stdin)
        raw = src.read(limit + 1)
        if isinstance(raw, str):
            raw = raw.encode("utf-8", errors="replace")
    else:
        with open(source, "rb") as f:
            raw = f.read(limit + 1)
    if len(raw) > limit:
        return None
    return raw.decode("utf-8", errors="replace")


def _is_unsafe(el):
    if el.get("unsafe") is True:
        return True
    if str(el.get("tag") or "").strip().lower() in UNSAFE_TAGS:
        return True
    if str(el.get("input_type") or "").strip().lower() \
            in UNSAFE_INPUT_TYPES:
        return True
    return False


def _is_hidden(el):
    if el.get("hidden") is True or el.get("aria_hidden") is True:
        return True
    if el.get("visible") is False:
        return True
    style = str(el.get("style") or "").replace(" ", "").lower()
    return "display:none" in style or "visibility:hidden" in style


def shortlist(elements, limit=dc.MAX_CANDIDATES):
    """Deterministic candidate element list, clamped to
    0..MAX_CANDIDATES: enabled, identified, unique-id, safe, visible,
    actionable elements only. Non-interactive roles must carry an
    explicit actionable=True; malformed actionable values disqualify.
    Interactive roles rank first, stable input order breaks ties."""
    try:
        limit = int(limit)
    except (TypeError, ValueError):
        limit = dc.MAX_CANDIDATES
    limit = max(0, min(limit, dc.MAX_CANDIDATES))
    eligible, seen = [], set()
    for el in elements or []:
        if not isinstance(el, dict):
            continue
        if el.get("enabled", True) is not True:
            continue
        act = el.get("actionable")
        if act is not None and not isinstance(act, bool):
            continue
        role = str(el.get("role") or "").strip().lower()
        if role not in INTERACTIVE_ROLES and act is not True:
            continue
        if act is False:
            continue
        cid = el.get("id")
        if not isinstance(cid, str) or not cid or cid == dc.NONE_ID:
            continue
        if cid in seen:
            continue
        if _is_unsafe(el) or _is_hidden(el):
            continue
        seen.add(cid)
        eligible.append(el)
    interactive = [e for e in eligible
                   if str(e.get("role") or "").strip().lower()
                   in INTERACTIVE_ROLES]
    rest = [e for e in eligible if e not in interactive]
    return (interactive + rest)[:limit]


def _abstain(reason, context=None, mode="shadow"):
    rec = dc.make_abstention("", reason)
    rec["context"] = dict(context or {})
    rec["mode"] = mode
    rec["profile_version"] = PROFILE
    return rec


def _stale_reason(snapshot, expected_observation_id):
    if isinstance(snapshot, dict) and snapshot.get("stale") is True:
        return "stale_snapshot"
    if expected_observation_id is not None:
        obs = (snapshot or {}).get("observation_id")
        if not obs or obs != expected_observation_id:
            return "stale_observation"
    return None


def nodes_to_elements(nodes):
    """scrape/parse node dicts -> element dicts. ids come from attrib
    id/name, else positional; password/hidden inputs and script-ish
    tags are marked unsafe so shortlist() drops them."""
    els = []
    for i, n in enumerate(nodes or []):
        if not isinstance(n, dict):
            continue
        attrib = n.get("attrib") if isinstance(n.get("attrib"), dict) \
            else {}
        tag = str(n.get("tag") or "").strip().lower()
        role = str(attrib.get("role") or _TAG_ROLE.get(tag, "element"))
        cid = attrib.get("id") or attrib.get("name") or f"node-{i}"
        itype = str(attrib.get("type") or "").strip().lower()
        disabled = "disabled" in attrib \
            or str(attrib.get("aria-disabled", "")).lower() == "true"
        hidden = "hidden" in attrib \
            or str(attrib.get("aria-hidden", "")).lower() == "true" \
            or "display:none" in str(attrib.get("style") or "") \
                .replace(" ", "").lower()
        unsafe = tag in UNSAFE_TAGS or itype in UNSAFE_INPUT_TYPES
        els.append({
            "id": str(cid), "role": role,
            "name": str(n.get("text") or attrib.get("aria-label")
                        or attrib.get("title") or "")[:200],
            "scope": tag,
            "enabled": not disabled,
            "hidden": hidden,
            "unsafe": unsafe,
            "tag": tag, "input_type": itype,
        })
    return els


def pick(client, context, goal, snapshot, *,
         expected_observation_id=None, mode="shadow", log_path=None,
         deadline_ms=1000, language=None):
    """Snapshot -> suggestion/abstain via the closed cu_decision
    contract. client may be None (deterministic paths only)."""
    if not isinstance(snapshot, dict):
        return _abstain("snapshot_invalid", context, mode)
    reason = _stale_reason(snapshot, expected_observation_id)
    if reason:
        rec = _abstain(reason, context, mode)
        rec["context"] = dict(context or {})
        return rec
    elements = snapshot.get("elements")
    if elements is None:
        elements = nodes_to_elements(snapshot.get("nodes"))
    if not isinstance(elements, list):
        return _abstain("elements_invalid", context, mode)
    candidates_els = shortlist(elements[:MAX_SNAPSHOT_ELEMENTS])
    if not candidates_els:
        return _abstain("no_actionable_candidates", context, mode)
    if client is None:
        hit = cd.exact_match(goal, cd.build_candidates(candidates_els))
        if hit is not None:
            rec = _abstain("exact_match", context, mode)
            rec.update({"outcome": "suggestion", "candidate_id": hit,
                        "reason": "exact_match"})
            return rec
        return _abstain("no_client", context, mode)
    return cd.suggest(client, context, goal, candidates_els,
                      log_path=log_path, mode=mode,
                      deadline_ms=deadline_ms, language=language)


_MODE_RANK = {"off": 0, "shadow": 1, "assist": 2}


def suggest_dom(snapshot, goal, context=None, *, config=None,
                expected_observation_id=None, mode=None,
                deadline_ms=1000, log_path=None):
    """Config-gated entry. The effective mode is dc.effective_mode(cfg)
    — already degraded to shadow when assist lacks a bound calibration.
    The `mode` argument may only LOWER that (e.g. force off/shadow in
    a caller context); it can never raise privilege above the
    calibrated config, so an off config plus mode="assist" stays off.
    off -> "feature_off" abstain (no daemon spawn); enabled ->
    deterministic exact-match short-circuit, then layad; daemon down
    -> typed abstain. Output is suggestion/abstain only."""
    cfg = dc.load_config(config)
    eff = dc.effective_mode(cfg)
    if mode in dc.MODES and _MODE_RANK[mode] < _MODE_RANK[eff]:
        eff = mode
    context = dict(context or {})
    if eff == "off":
        return _abstain("feature_off", context, "off")
    reason = _stale_reason(snapshot, expected_observation_id) \
        if isinstance(snapshot, dict) else "snapshot_invalid"
    if reason:
        return _abstain(reason, context, eff)
    elements = (snapshot or {}).get("elements")
    if elements is None:
        elements = nodes_to_elements((snapshot or {}).get("nodes"))
    if not isinstance(elements, list):
        return _abstain("elements_invalid", context, eff)
    candidates_els = shortlist(elements[:MAX_SNAPSHOT_ELEMENTS])
    if not candidates_els:
        return _abstain("no_actionable_candidates", context, eff)
    cands = cd.build_candidates(candidates_els)
    hit = cd.exact_match(goal, cands)
    if hit is not None:
        rec = _abstain("exact_match", context, eff)
        rec.update({"outcome": "suggestion", "candidate_id": hit})
        return rec
    daemon = lc.ensure_daemon(config)
    if daemon is None:
        return _abstain("daemon_unavailable", context, eff)
    request = cd.make_request(context, goal, cands, mode=eff,
                              deadline_ms=deadline_ms)
    rec = lc.recommend(request, daemon=daemon)
    if not isinstance(rec, dict):
        return _abstain("daemon_unavailable", context, eff)
    return rec


def main(argv=None):
    ap = argparse.ArgumentParser(
        description="JEV-6 DOM action-target suggestion (no clicks)")
    ap.add_argument("--snapshot", required=True,
                    help="snapshot JSON file ('-' = stdin)")
    ap.add_argument("--goal", required=True)
    ap.add_argument("--observation-id", default=None,
                    help="expected observation; mismatch abstains")
    ap.add_argument("--context-json", default=None,
                    help="JSON object with binding fields")
    ap.add_argument("--config", default=None,
                    help="laya profile.json (enables daemon path)")
    ap.add_argument("--mode", default=None, choices=list(dc.MODES),
                    help="override configured mode")
    ap.add_argument("--deadline-ms", type=int, default=1000)
    ap.add_argument("--log", default=None)
    args = ap.parse_args(argv)

    try:
        raw = read_bounded(args.snapshot, MAX_SNAPSHOT_BYTES)
    except OSError as e:
        print(json.dumps({"ok": False, "error": f"snapshot_error:{e}"}))
        return 2
    if raw is None:
        print(json.dumps({"ok": False, "error": "snapshot_too_large"}))
        return 2
    try:
        snapshot = json.loads(raw)
    except json.JSONDecodeError as e:
        print(json.dumps({"ok": False, "error": f"snapshot_error:{e}"}))
        return 2
    context = {}
    if args.context_json:
        try:
            context = json.loads(args.context_json)
            if not isinstance(context, dict):
                context = {}
        except json.JSONDecodeError:
            context = {}
    rec = suggest_dom(snapshot, args.goal, context,
                      config=args.config,
                      expected_observation_id=args.observation_id,
                      mode=args.mode, deadline_ms=args.deadline_ms,
                      log_path=args.log)
    out = {"ok": True}
    out.update({k: rec.get(k) for k in
                ("outcome", "candidate_id", "reason", "mode",
                 "adoptable", "profile_version")})
    print(json.dumps(out, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
