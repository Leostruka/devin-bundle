"""transcript — parse session transcripts into pinned tool items.

Port of the upstream compaction algorithm's collectToolCalls (MIT):
pair each tool_use with its tool_result, and mark the pin set that must
never be touched (first message, last user task, newest N messages).

Items are the unit of decision. Pairs are the unit of application: a
tool_result is never orphaned from its tool_use.
"""
from __future__ import annotations

PIN_ROLES = ("system",)


def _msg_text(msg):
    c = msg.get("content")
    if isinstance(c, str):
        return c
    if isinstance(c, list):
        return "".join(p.get("text", "") for p in c
                       if isinstance(p, dict) and p.get("type") == "text")
    return ""


def _iter_blocks(msg):
    c = msg.get("content")
    if isinstance(c, list):
        for i, b in enumerate(c):
            if isinstance(b, dict):
                yield i, b


def collect_items(messages, preserve_recent=6):
    """Flatten messages into decision items.

    Returns list of dicts:
      {id, kind: tool_use|tool_result|message, pair: pair_id|None,
       msg_index, name, text, chars, pinned}
    preserve_recent counts messages from the tail that stay pinned.
    """
    items = []
    n = len(messages)
    recent_floor = max(0, n - preserve_recent)
    last_user = max((i for i, m in enumerate(messages)
                     if m.get("role") == "user"), default=-1)
    pending = {}  # tool_use_id -> pair item indexes

    for i, msg in enumerate(messages):
        pinned = (i == 0 or i >= recent_floor or i == last_user
                  or msg.get("role") in PIN_ROLES)
        text = _msg_text(msg)
        blocks = list(_iter_blocks(msg))
        if not blocks:
            items.append({
                "id": f"m{i}", "kind": "message", "pair": None,
                "msg_index": i, "name": msg.get("role", "?"),
                "text": text, "chars": len(text), "pinned": pinned})
            continue
        for j, b in blocks:
            t = b.get("type")
            if t == "tool_use":
                iid = b.get("id") or f"m{i}b{j}"
                pair = f"p:{iid}"
                pending[b.get("id")] = pair
                items.append({
                    "id": f"m{i}b{j}", "kind": "tool_use", "pair": pair,
                    "msg_index": i, "name": b.get("name", "tool"),
                    "text": b.get("input") if isinstance(b.get("input"), str)
                    else _json(b.get("input")),
                    "chars": 0, "pinned": pinned})
                items[-1]["chars"] = len(items[-1]["text"] or "")
            elif t == "tool_result":
                pair = pending.get(b.get("tool_use_id"))
                content = b.get("content")
                txt = content if isinstance(content, str) else _json(content)
                items.append({
                    "id": f"m{i}b{j}", "kind": "tool_result",
                    "pair": pair, "msg_index": i,
                    "name": "tool_result",
                    "text": txt or "",
                    "chars": len(txt or ""), "pinned": pinned})
            else:
                items.append({
                    "id": f"m{i}b{j}", "kind": "message", "pair": None,
                    "msg_index": i, "name": t or "block",
                    "text": _json(b) if not isinstance(b, str) else b,
                    "chars": 0, "pinned": pinned})
                items[-1]["chars"] = len(items[-1]["text"] or "")
    return items


def _json(v):
    import json
    try:
        return json.dumps(v, ensure_ascii=False, default=str)
    except (TypeError, ValueError):
        return str(v)


def pairs(items):
    """Group items by pair id. Returns {pair_id: {call, result}} for
    tool pairs only."""
    out = {}
    for it in items:
        if it["pair"] is None:
            continue
        slot = out.setdefault(it["pair"], {"call": None, "result": None})
        if it["kind"] == "tool_use":
            slot["call"] = it
        elif it["kind"] == "tool_result":
            slot["result"] = it
    return out


def orphan_check(items):
    """True when every tool_result still has its tool_use present."""
    pmap = pairs(items)
    for it in items:
        if it["kind"] != "tool_result":
            continue
        slot = pmap.get(it["pair"])
        if slot is None or slot["call"] is None:
            return False
    return True
