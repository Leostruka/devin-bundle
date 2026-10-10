"""state — build the bounded decision state for one item.

Port of fast-jev's fitState: staged shrinking until the serialized
state fits max_state chars. Stages mirror upstream:

  stage 0  full content (up to max_state)
  stage 1  head+tail abridged at 1000 chars per side
  stage 2  head+tail abridged at 200 chars per side
  stage 3  head+tail abridged at 60 chars per side
  stage 4  message collapse: metadata only, no content

Tool results never ship raw blobs: they are summarized as
`ok, N chars` notes plus the fitted excerpt — exit codes and error
text survive verbatim inside the head budget.
"""
from __future__ import annotations

ABRIDGE_STAGES = (1000, 200, 60)


def abridge(text, side):
    if len(text) <= side * 2 + 16:
        return text
    return text[:side] + "\n...[snip]...\n" + text[-side:]


def _note(item):
    if item["kind"] == "tool_result":
        text = item.get("text") or ""
        ok = "error" not in text[:200].lower()
        return f"{'ok' if ok else 'error'}, {item['chars']} chars"
    return f"{item['name']}, {item['chars']} chars"


def build_state(item, goal="", max_state=100_000):
    """Serialize item into the contract's `snippets` state field.

    Returns {state, stage}: state fits the decision_contract allowlist
    (goal + snippets strings only); stage records how hard it had to
    be compressed — useful for threshold calibration later.
    """
    meta = (f"kind={item['kind']} name={item['name']} "
            f"msg={item['msg_index']} note={_note(item)}")
    text = item.get("text") or ""
    for stage, side in enumerate([None] + list(ABRIDGE_STAGES)):
        body = text if side is None else abridge(text, side)
        snippet = f"[{meta}]\n{body}"
        if len(snippet) <= max_state:
            return {"goal": goal, "snippets": snippet}, stage
    return {"goal": goal, "snippets": f"[{meta}]"}, len(ABRIDGE_STAGES) + 1
