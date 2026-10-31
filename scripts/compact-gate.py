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

Trigger budget (EVAL_FLOOR=0.25, COMPACT_AT=0.70, FORCE_AT=0.80):
  E1 UserPromptSubmit with p>floor       -> always evaluate
  E2 PostToolUse with p>floor, >=K calls since last eval
  E3 p>=COMPACT_AT                        -> evaluate every call
Policy: severity floor from p; laya only escalates (A1). task_shifted
at pressure prefers clear/handoff over compacting dead context.
mode=off updates the digest only — zero subprocess, zero weight reads.
"""
import hashlib
import json
import os
import socket
import subprocess
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
DEFAULTS = {"eval_floor": 0.25, "compact_at": 0.70, "compact_to": 0.40,
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


def _laya_cli_path():
    cands = []
    env = os.environ.get("DEVIN_PROJECT_DIR")
    if env:
        cands.append(os.path.join(env, "extensions", "laya-tools"))
    cands.append(os.path.join(os.getcwd(), "extensions", "laya-tools"))
    home = _devin_home()
    cands.append(os.path.join(home, "extensions", "laya-tools"))
    for d in cands:
        p = os.path.join(d, "laya_cli.py")
        if os.path.isfile(p):
            return os.path.normpath(p)
    return None


# --- laya wire mirror --------------------------------------------------------
# Stdlib-only mirror of the decision-contract config surface and the
# laya_client daemon wire protocol. Hooks must not import extensions/
# (ARCHITECTURE_MANIFEST): the daemon keeps full contract validation;
# this mirror only loads the profile, derives the effective mode, and
# speaks the documented hello/request line protocol.


def _config_digest(path):
    try:
        with open(path, "rb") as f:
            return hashlib.sha256(f.read()).hexdigest()
    except OSError:
        return ""


def _load_config(path):
    cfg = {"version": 1, "mode": "off", "calibration": None,
           "models": {}, "profiles": [], "device": "cpu",
           "deadline_ms": 1000, "queue_depth": 4}
    try:
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
    except (OSError, json.JSONDecodeError):
        data = None
    if isinstance(data, dict):
        cfg.update(data)
    return cfg


def _is_num(v):
    return isinstance(v, (int, float)) and not isinstance(v, bool)


_CALIB_REQUIRED = ("id", "checkpoint_sha256", "profile", "locale",
                   "data_source", "evaluation_id")


def _activation_errors(cfg):
    if not isinstance(cfg, dict) or cfg.get("mode") != "assist":
        return []
    errs = []
    cal = cfg.get("calibration")
    if not isinstance(cal, dict):
        return ["calibration_missing"]
    for k in _CALIB_REQUIRED:
        if not isinstance(cal.get(k), str) or not cal[k]:
            errs.append(f"calibration_{k}_missing")
    thr = cal.get("threshold")
    if not _is_num(thr) or not (0.0 <= thr <= 1.0):
        errs.append("calibration_threshold_invalid")
    card = cal.get("cardinality")
    if not isinstance(card, int) or isinstance(card, bool) \
            or not (1 <= card <= 8):
        errs.append("calibration_cardinality_invalid")
    models = cfg.get("models") or {}
    digests = {m.get("sha256") for m in models.values()
               if isinstance(m, dict)}
    if cal.get("checkpoint_sha256") not in digests:
        errs.append("calibration_checkpoint_mismatch")
    if cal.get("profile") not in (cfg.get("profiles") or []):
        errs.append("calibration_profile_mismatch")
    m = cal.get("map")
    if m is not None and (not isinstance(m, dict)
                          or m.get("kind") not in
                          ("identity", "platt", "table")):
        errs.append("calibration_map_invalid")
    return errs


def _effective_mode(cfg):
    if not isinstance(cfg, dict):
        return "off"
    mode = cfg.get("mode")
    if mode == "assist":
        return "shadow" if _activation_errors(cfg) else "assist"
    return "shadow" if mode == "shadow" else "off"


def _daemon_info(laya_dir):
    info = _load_json(os.path.join(laya_dir, "daemon.json"), None)
    if not isinstance(info, dict) or not info.get("port") \
            or not info.get("auth_token"):
        return None
    return info


def _pid_alive(pid):
    if not isinstance(pid, int) or pid <= 0:
        return False
    if os.name == "nt":
        try:
            import ctypes
            h = ctypes.windll.kernel32.OpenProcess(0x1000, False, pid)
            if not h:
                return False
            ctypes.windll.kernel32.CloseHandle(h)
            return True
        except OSError:
            return False
    try:
        os.kill(pid, 0)
        return True
    except OSError:
        return False


def _port_open(port, timeout=0.5):
    try:
        with socket.create_connection(("127.0.0.1", port),
                                      timeout=timeout):
            return True
    except OSError:
        return False


def _terminate(pid):
    try:
        if os.name == "nt":
            subprocess.run(["taskkill", "/PID", str(pid), "/F"],
                           capture_output=True, timeout=10,
                           creationflags=getattr(
                               subprocess, "CREATE_NO_WINDOW", 0))
        else:
            os.kill(pid, 15)
    except (OSError, subprocess.SubprocessError):
        pass


def _spawn_daemon(config_path):
    cli = _laya_cli_path()
    if not cli:
        return
    base = os.path.dirname(cli)
    venv_py = os.path.join(
        base, ".venv",
        "Scripts/python.exe" if os.name == "nt"
        else os.path.join("bin", "python"))
    py = venv_py if os.path.isfile(venv_py) else sys.executable
    subprocess.Popen(
        [py, cli, "serve-daemon", "--config", config_path],
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
        creationflags=(getattr(subprocess, "DETACHED_PROCESS", 0)
                       | getattr(subprocess, "CREATE_NEW_PROCESS_GROUP", 0))
        if os.name == "nt" else 0,
        start_new_session=os.name != "nt")


def _ensure_daemon(config_path, spawn_timeout_s=60.0):
    if os.environ.get("LAYA_NO_DAEMON"):
        return None
    laya_dir = os.path.dirname(config_path)
    want_sha = _config_digest(config_path)
    info = _daemon_info(laya_dir)
    if info and info.get("config_sha256") == want_sha \
            and _pid_alive(info.get("pid", -1)) \
            and _port_open(int(info["port"])):
        return info
    if info and _pid_alive(info.get("pid", -1)):
        _terminate(int(info["pid"]))
    lock_path = os.path.join(laya_dir, "daemon.lock")
    os.makedirs(laya_dir, exist_ok=True)
    try:
        fd = os.open(lock_path, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
        os.write(fd, str(os.getpid()).encode())
        os.close(fd)
        acquired = True
    except OSError:
        acquired = False
    if not acquired:
        try:
            stale = time.time() - os.stat(lock_path).st_mtime > 120
        except OSError:
            stale = True
        if stale:
            try:
                os.unlink(lock_path)
            except OSError:
                pass
        deadline = time.time() + spawn_timeout_s
        while time.time() < deadline:
            info = _daemon_info(laya_dir)
            if info and info.get("config_sha256") == want_sha \
                    and _port_open(int(info["port"])):
                return info
            time.sleep(0.5)
        return None
    try:
        info = _daemon_info(laya_dir)
        if info and info.get("config_sha256") == want_sha \
                and _pid_alive(info.get("pid", -1)) \
                and _port_open(int(info["port"])):
            return info
        _spawn_daemon(config_path)
        deadline = time.time() + spawn_timeout_s
        while time.time() < deadline:
            info = _daemon_info(laya_dir)
            if info and _port_open(int(info["port"])):
                return info
            time.sleep(0.5)
        return None
    finally:
        try:
            os.unlink(lock_path)
        except OSError:
            pass


def _abstain(rid, reason):
    return {"ok": True, "version": 1, "request_id": rid,
            "outcome": "abstain", "candidate_id": "__none__",
            "adoptable": False, "reason": reason}


def _recommend(request, daemon, timeout_s):
    rid = str(request.get("request_id", ""))
    cand_ids = {c.get("id") for c in request.get("candidates") or []
                if isinstance(c, dict)}
    if not isinstance(daemon, dict):
        return _abstain(rid, "daemon_unavailable")
    try:
        with socket.create_connection(
                ("127.0.0.1", int(daemon["port"])),
                timeout=timeout_s) as sock:
            sock.settimeout(timeout_s)
            rf = sock.makefile("r", encoding="utf-8", newline="\n")
            wf = sock.makefile("w", encoding="utf-8", newline="\n")
            try:
                wf.write(json.dumps(
                    {"op": "hello",
                     "auth_token": daemon["auth_token"]}) + "\n")
                wf.write(json.dumps(
                    {"version": 1, "request_id": rid,
                     "request": request}, ensure_ascii=False) + "\n")
                wf.flush()
                hello = json.loads(rf.readline())
                if not isinstance(hello, dict) or not hello.get("ok"):
                    return _abstain(rid, "daemon_unauthorized")
                line = rf.readline()
            finally:
                for f in (rf, wf):
                    try:
                        f.close()
                    except OSError:
                        pass
    except (OSError, ValueError, KeyError, socket.timeout):
        return _abstain(rid, "daemon_unreachable")
    try:
        reply = json.loads(line)
    except (json.JSONDecodeError, UnboundLocalError):
        return _abstain(rid, "daemon_protocol_error")
    if not isinstance(reply, dict) or reply.get("request_id") != rid:
        return _abstain(rid, "daemon_protocol_error")
    if reply.get("outcome") == "suggestion" \
            and reply.get("candidate_id") not in cand_ids:
        return _abstain(rid, "daemon_protocol_error:bad_candidate")
    return reply


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
    out = payload.get("tool_response")
    if out is None:
        out = payload.get("tool_output")
    if isinstance(out, dict):
        out = out.get("output") or out.get("stdout") \
            or out.get("error") or json.dumps(out)
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
    cli = _laya_cli_path()
    if cli is not None:
        cfg = _load_config(cfg_path)
        cfgd.update(cfg.get("compact_gate") or {})
        mode = _effective_mode(cfg)
    else:
        cfg = None
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
    due = (ev == "UserPromptSubmit" and p > floor) \
        or (p > floor
            and state["calls"] - state["last_eval_call"] >= cfgd["k_calls"]) \
        or p >= at
    if not due or mode == "off" or cli is None:
        _save_json(_state_path(), state)
        sys.exit(0)

    state["last_eval_call"] = state["calls"]
    daemon = _ensure_daemon(cfg_path)
    st = _digest_state(state, p)
    deadline = cfg.get("deadline_ms", 1000) \
        if isinstance(cfg, dict) else 1000

    def ask(profile, cands):
        req = {"version": 1,
               "request_id": f"gate-{os.getpid()}-{state['calls']}",
               "profile": profile, "mode": mode,
               "context": {"env_id": "compact-gate"},
               "state": st, "candidates": cands,
               "deadline_ms": deadline}
        return _recommend(req, daemon=daemon,
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
    if boundary == "task_shifted" and p > floor:
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
