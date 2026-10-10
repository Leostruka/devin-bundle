#!/usr/bin/env python3
"""compact-gate — Layer 7 self-compacting trigger (LAYA Master §4).

Decides WHEN to compact and WHICH mode, never executes: emits a
one-line LAYA-GATE notice via hookSpecificOutput.additionalContext;
the agent runs compact.py / handoff / clear itself.

Signals:
  p        = est_tokens / window, from the context-pressure marker
             plus the same overhead model (rules + mcp + per-call).
  boundary = laya compact-boundary-v1: mid_task | stage_resolved |
             task_shifted (trajectory structure, SelfCompact rubric).
  action   = laya compact-gate-v1: continue|prune|fold|handoff|clear.

Trigger budget (EVAL_FLOOR=0.50, COMPACT_AT=0.70, FORCE_AT=0.80):
  E1 UserPromptSubmit with p>=floor      -> always evaluate
  E2 PostToolUse with p>=floor, >=K calls since last eval
  E3 p>=COMPACT_AT                        -> evaluate every call
Policy: severity floor from p; laya only escalates (A1). task_shifted
at pressure prefers clear/handoff over compacting dead context.
mode=off updates the digest only — zero subprocess, zero weight reads.
"""
import json
import os
import sys
import time

SCRIPTS_DIR = os.path.dirname(os.path.abspath(__file__))
PROFILE_ACTION = "compact-gate-v1"
PROFILE_BOUNDARY = "compact-boundary-v1"
ACTION_CANDS = [{"id": "continue"}, {"id": "prune"}, {"id": "fold"},
                {"id": "handoff"}, {"id": "clear"}]
BOUNDARY_CANDS = [{"id": "mid_task"}, {"id": "stage_resolved"},
                  {"id": "task_shifted"}]
SEVERITY = {"continue": 0, "fold": 1, "prune": 2, "handoff": 3,
            "clear": 4}
NOTICES = {
    "prune": "LAYA-GATE p={p:.2f} {b}: run "
             "extensions/laya-compactor/compact.py on this session "
             "transcript now.",
    "fold": "LAYA-GATE p={p:.2f} {b}: context-folding — offload "
            "artifacts >50k tokens to files before continuing.",
    "handoff": "LAYA-GATE p={p:.2f} {b}: invoke the handoff skill, "
               "then clear.",
    "clear": "LAYA-GATE p={p:.2f} {b}: task scope shifted — finish "
             "pending artifacts and clear; earlier context is noise.",
}
DEFAULTS = {"eval_floor": 0.50, "compact_at": 0.70, "compact_to": 0.40,
            "force_at": 0.80, "k_calls": 8, "cooldown_turns": 10,
            "max_files": 50, "max_errors": 3, "error_head": 300}
CHARS_PER_TOKEN = 4


def _devin_home():
    appdata = os.environ.get("APPDATA", "")
    if appdata:
        return os.path.join(appdata, "devin")
    xdg = os.environ.get("XDG_CONFIG_HOME", "")
    if xdg:
        return os.path.join(xdg, "devin")
    return os.path.join(os.path.expanduser("~"), ".config", "devin")


def _laya_ext_dir():
    cands = []
    env = os.environ.get("DEVIN_PROJECT_DIR")
    if env:
        cands.append(os.path.join(env, "extensions", "laya-tools"))
    cands.append(os.path.join(os.getcwd(), "extensions", "laya-tools"))
    home = _devin_home()
    cands.append(os.path.join(home, "extensions", "laya-tools"))
    cands.append(os.path.join(os.getcwd(), ".devin", "..", "extensions",
                              "laya-tools"))
    for c in cands:
        if os.path.isfile(os.path.join(c, "decision_contract.py")):
            return os.path.normpath(c)
    return None


def _profile_path():
    for base in (os.environ.get("DEVIN_PROJECT_DIR"), os.getcwd()):
        if base:
            p = os.path.join(base, ".devin", "laya", "profile.json")
            if os.path.isfile(p):
                return p
    home = _devin_home()
    for p in (os.path.join(home, ".devin", "laya", "profile.json"),
              os.path.join(home, "laya", "profile.json")):
        if os.path.isfile(p):
            return p
    return os.path.join(os.getcwd(), ".devin", "laya", "profile.json")


def _state_path():
    d = os.path.dirname(_profile_path())
    return os.path.join(d, "gate-state.json")


def _load_json(path, default):
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    except (OSError, json.JSONDecodeError):
        return default


def _save_json(path, obj):
    try:
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(obj, f)
    except OSError:
        pass


def _pressure():
    """p = estimated tokens / window, mirroring context-pressure.py."""
    marker = _load_json(
        os.path.join(_devin_home(), "context-pressure.json"), {})
    window = 262144
    for base in (os.environ.get("DEVIN_PROJECT_DIR"), os.getcwd(),
                 _devin_home()):
        if not base:
            continue
        data = _load_json(os.path.join(base, "data",
                                       "bundle-models.json"), None)
        if data:
            for m in data.get("models", []):
                if m.get("is_default_parent"):
                    window = m.get("context_window", window)
                    break
            break
    rules_tokens = 0
    for p in (os.path.join(os.getcwd(), "AGENTS.md"),
              os.path.join(_devin_home(), "AGENTS.md")):
        try:
            with open(p, encoding="utf-8", errors="replace") as f:
                rules_tokens = len(f.read()) // CHARS_PER_TOKEN
                break
        except OSError:
            continue
    mcp_tokens = 0
    mcp = _load_json(os.path.join(os.getcwd(), "mcp_config.json"), None)
    if mcp:
        mcp_tokens = len(mcp.get("mcpServers", {})) * 3000
    calls = int(marker.get("calls", 0))
    total = (int(marker.get("tool_output_tokens", 0)) + calls * 200
             + rules_tokens + mcp_tokens)
    return total / window if window else 0.0


def _update_digest(state, payload, cfgd):
    ev = payload.get("hook_event_name", "")
    if ev == "UserPromptSubmit":
        text = (payload.get("prompt") or payload.get("user_prompt")
                or payload.get("text") or "")
        if isinstance(text, str) and text.strip():
            if not state["digest"].get("first_task"):
                state["digest"]["first_task"] = text.strip()[:2000]
            state["digest"]["last_task"] = text.strip()[:2000]
        return
    tool = payload.get("tool_name", "?")
    hist = state["digest"].setdefault("tool_hist", {})
    hist[tool] = hist.get(tool, 0) + 1
    ti = payload.get("tool_input") or {}
    for k in ("file_path", "notebook_path"):
        v = ti.get(k)
        if isinstance(v, str) and v:
            files = state["digest"].setdefault("files", [])
            if v not in files:
                files.append(v)
                del files[:-cfgd["max_files"]]
    out = payload.get("tool_output")
    if isinstance(out, dict):
        out = json.dumps(out)
    if isinstance(out, str) and ("error" in out[:400].lower()
                                or "traceback" in out[:400].lower()):
        errs = state["digest"].setdefault("errors", [])
        errs.append(out[:cfgd["error_head"]])
        del errs[:-cfgd["max_errors"]]


def _digest_state(state, p):
    d = state["digest"]
    return {
        "goal": (d.get("first_task", "") + "\n\nLATEST: "
                 + d.get("last_task", "")).strip(),
        "snippets": json.dumps({
            "tool_hist": d.get("tool_hist", {}),
            "files": d.get("files", [])[-15:],
            "recent_errors": d.get("errors", []),
            "turns_since_last_compact": state.get("turns", 0),
        }, ensure_ascii=False)[:8000],
        "confidence_hint": json.dumps({
            "p": round(p, 3), "calls": state.get("calls", 0),
        }),
    }


def _inject(text):
    print(json.dumps({"hookSpecificOutput":
                      {"additionalContext": text}}))


def main():
    try:
        payload = json.load(sys.stdin)
    except (json.JSONDecodeError, EOFError, ValueError):
        sys.exit(0)
    ev = payload.get("hook_event_name", "")
    if ev not in ("PostToolUse", "UserPromptSubmit"):
        sys.exit(0)

    cfg_path = _profile_path()
    cfgd = dict(DEFAULTS)
    laya_dir = _laya_ext_dir()
    dc = lc = None
    if laya_dir:
        sys.path.insert(0, laya_dir)
        try:
            import decision_contract as dc_mod
            import laya_client as lc_mod
            dc, lc = dc_mod, lc_mod
        except ImportError:
            dc = lc = None
    if dc is not None:
        cfg = dc.load_config(cfg_path)
        cfgd.update(cfg.get("compact_gate") or {})
        mode = dc.effective_mode(cfg)
    else:
        mode = "off"

    state = _load_json(_state_path(), {"digest": {}, "calls": 0,
                                       "turns": 0, "last_eval_call": -999,
                                       "last_action_ts": 0,
                                       "session_id": ""})
    sid = payload.get("session_id", "")
    if sid and state.get("session_id") and state["session_id"] != sid:
        state = {"digest": {}, "calls": 0, "turns": 0,
                 "last_eval_call": -999, "last_action_ts": 0,
                 "session_id": sid}
    state["session_id"] = sid or state.get("session_id", "")
    state["calls"] = state.get("calls", 0) + 1
    if ev == "UserPromptSubmit":
        state["turns"] = state.get("turns", 0) + 1
    _update_digest(state, payload, cfgd)

    p = _pressure()
    floor, at, force = (cfgd["eval_floor"], cfgd["compact_at"],
                        cfgd["force_at"])
    due = (ev == "UserPromptSubmit" and p >= floor) \
        or (p >= floor
            and state["calls"] - state["last_eval_call"] >= cfgd["k_calls"]) \
        or p >= at
    if not due or mode == "off" or dc is None:
        _save_json(_state_path(), state)
        sys.exit(0)

    state["last_eval_call"] = state["calls"]
    daemon = lc.ensure_daemon(cfg_path)
    st = _digest_state(state, p)
    deadline = 1000

    def ask(profile, cands):
        req = {"version": dc.VERSION,
               "request_id": f"gate-{os.getpid()}-{state['calls']}",
               "profile": profile, "mode": mode,
               "context": {"env_id": "compact-gate"},
               "state": st, "candidates": cands,
               "deadline_ms": deadline}
        return lc.recommend(req, daemon=daemon,
                            timeout_s=deadline / 1000 + 1)

    b_rec = ask(PROFILE_BOUNDARY, BOUNDARY_CANDS)
    a_rec = ask(PROFILE_ACTION, ACTION_CANDS)
    boundary = b_rec.get("candidate_id") \
        if b_rec.get("outcome") == "suggestion" else "__none__"
    action = a_rec.get("candidate_id") \
        if a_rec.get("outcome") == "suggestion" else "continue"
    adoptable = bool(a_rec.get("adoptable"))

    floor_action = "continue" if p < at else "prune"
    if p >= force:
        floor_action = "prune"
    if boundary == "mid_task" and p < force:
        action = "continue" if SEVERITY.get(action, 0) \
            < SEVERITY["fold"] else action
    if boundary == "task_shifted" and p >= floor:
        action = "handoff" if state["digest"].get("last_task") \
            else "clear"
    if SEVERITY.get(action, 0) < SEVERITY.get(floor_action, 0):
        action = floor_action
    cooldown = state.get("cooldown_until_turn", -1)
    if action != "continue" and state["turns"] <= cooldown:
        action = "continue"

    shadow_entry = {
        "ts": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "session_id": sid, "profile": "compact-gate",
        "p": round(p, 3), "boundary": boundary, "action": action,
        "adoptable": adoptable,
        "a_reason": a_rec.get("reason"), "b_reason": b_rec.get("reason"),
    }
    try:
        logdir = os.path.dirname(cfg_path)
        os.makedirs(logdir, exist_ok=True)
        log = os.path.join(logdir, "shadow.jsonl")
        if not os.path.isfile(log) or os.path.getsize(log) < 2_000_000:
            with open(log, "a", encoding="utf-8") as f:
                f.write(json.dumps(shadow_entry,
                                   ensure_ascii=False) + "\n")
    except OSError:
        pass

    notice = None
    if mode == "assist" and action != "continue":
        notice = NOTICES.get(action, "").format(p=p, b=boundary)
        state["cooldown_until_turn"] = \
            state["turns"] + cfgd["cooldown_turns"]
        state["last_action_ts"] = time.time()
    _save_json(_state_path(), state)
    if notice:
        _inject(notice)
    sys.exit(0)


if __name__ == "__main__":
    main()
