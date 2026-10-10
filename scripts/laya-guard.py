#!/usr/bin/env python3
"""PreToolUse(^exec$) — laya semantic risk tier (LAYA Master §3.4).

Runs AFTER destructive-gate inside pre-exec-guard's single spawn.
Cascade:
  T0 allowlist prefix          -> PASS (~0ms, most traffic)
  T1 deterministic features    -> PASS when trivially safe
  T2 laya cmd-risk-v1 via layad-> suggestion | abstain (never "allow")
  T3 policy merge              -> ladder only goes UP:
      assist:  irreversible|egress_or_secret -> BLOCK (exit 2)
               mutating|ambiguous + outside-repo -> WARN context + PASS
      shadow:  everything logged to .devin/laya/shadow.jsonl, PASS
      off:     T0/T1 only, zero subprocess

Laya output is a suggestion, never proof: it can only raise severity
above the deterministic floor, never relax a T1 block. Daemon down,
deadline, or malformed reply -> typed abstain -> PASS (fail-open onto
the existing deterministic gates, never blind-closed).
"""
import json
import os
import re
import sys
import time

SCRIPTS_DIR = os.path.dirname(os.path.abspath(__file__))


def _laya_dir():
    """extensions/laya-tools dir: project first, then installed home."""
    cands = []
    env = os.environ.get("DEVIN_PROJECT_DIR")
    if env:
        cands.append(os.path.join(env, "extensions", "laya-tools"))
    cands.append(os.path.join(os.getcwd(), "extensions", "laya-tools"))
    appdata = os.environ.get("APPDATA", "")
    if appdata:
        cands.append(os.path.join(appdata, "devin", "extensions",
                                  "laya-tools"))
    else:
        cands.append(os.path.join(os.path.expanduser("~"),
                                  ".config", "devin", "extensions",
                                  "laya-tools"))
    for c in cands:
        if os.path.isfile(os.path.join(c, "decision_contract.py")):
            return c
    return None


def _profile_path():
    for base in (os.environ.get("DEVIN_PROJECT_DIR"), os.getcwd()):
        if base:
            p = os.path.join(base, ".devin", "laya", "profile.json")
            if os.path.isfile(p):
                return p
    appdata = os.environ.get("APPDATA", "")
    home = os.path.join(appdata, "devin") if appdata else \
        os.path.join(os.path.expanduser("~"), ".config", "devin")
    for p in (os.path.join(home, ".devin", "laya", "profile.json"),
              os.path.join(home, "laya", "profile.json")):
        if os.path.isfile(p):
            return p
    return os.path.join(os.getcwd(), ".devin", "laya", "profile.json")


# T0: read-only command prefixes — never reach laya.
T0_ALLOW = re.compile(
    r"^\s*(?:"
    r"git\s+(?:status|diff|log|show|branch\b|rev-parse|ls-files|blame|"
    r"remote -v|stash list)\b|"
    r"ls\b|dir\b|pwd\b|cd\b|echo\b|cat\b|type\b|rg\b|grep\b|findstr\b|"
    r"head\b|tail\b|wc\b|which\b|where\b|whoami\b|hostname\b|"
    r"Get-ChildItem|Get-Content|Get-Location|Select-String|"
    r"python(?:3)?\s+(?:--version|-V)\b|pip(?:3)?\s+(?:list|show)\b|"
    r"node\s+--version|npm\s+(?:list|ls)\b|gh\s+(?:pr|issue|repo)\s+(?:view|list|status)\b"
    r")",
    re.IGNORECASE)

META_CHARS = re.compile(r"[|&;><`$(){}[\]!*?~]")
EGRESS = re.compile(
    r"\b(?:curl|wget|Invoke-WebRequest|iwr|ssh|scp|sftp|nc|ncat|netcat|"
    r"ftp|telnet|rsync\b.*[:@]|git\s+push\b|npm\s+publish|pip\s+install\b)",
    re.IGNORECASE)
SECRET_TOUCH = re.compile(
    r"\.env\b|credential|id_rsa|id_ed25519|\.pem\b|\.pfx\b|secret|"
    r"passwd|\.aws/|\.ssh/|keychain|token\s*=|api[_-]?key",
    re.IGNORECASE)
ADMIN = re.compile(r"\bsudo\b|runas\b|Start-Process.*-Verb\s+RunAs|"
                   r"\bsu\b\s|\bchmod\b|\bchown\b|icacls\b|takeown\b",
                   re.IGNORECASE)
SYSTEM_SCOPE = re.compile(
    r"/etc/|/usr/|/bin/|/sbin/|C:\\Windows|C:\\Program Files|"
    r"\bHKLM\b|HKEY_LOCAL_MACHINE|registry\b.*\bset\b|"
    r"launchctl|systemctl\s+(?:start|stop|enable|disable)|sc\.exe\s+"
    r"(?:create|delete|config)|taskkill|shutdown\b|reboot\b",
    re.IGNORECASE)
OUTSIDE_REPO = re.compile(r"\.\.[\\/]|^[A-Za-z]:[\\/]|^\s*/")


def extract_features(cmd):
    """Deterministic feature vector — stage-1 cascade classifier."""
    return {
        "pipes": "|" in cmd,
        "redirects": bool(re.search(r"(?<![0-9&])>{1,2}", cmd)),
        "chain_ops": bool(re.search(r"&&|\|\||;", cmd)),
        "admin": bool(ADMIN.search(cmd)),
        "egress": bool(EGRESS.search(cmd)),
        "secret_touch": bool(SECRET_TOUCH.search(cmd)),
        "system_scope": bool(SYSTEM_SCOPE.search(cmd)),
        "outside_repo": bool(OUTSIDE_REPO.search(cmd)),
        "len": len(cmd),
    }


def trivially_safe(cmd, feats):
    """Single-token or short command with no metachars and no risky
    feature — resolved without laya."""
    if feats["len"] <= 200 and not META_CHARS.search(cmd) \
            and not any(feats[k] for k in
                        ("admin", "egress", "secret_touch",
                         "system_scope", "outside_repo")):
        return True
    return False


def shadow_log(entry):
    try:
        logdir = os.path.dirname(_profile_path())
        os.makedirs(logdir, exist_ok=True)
        log = os.path.join(logdir, "shadow.jsonl")
        if os.path.isfile(log) and os.path.getsize(log) > 2_000_000:
            return
        with open(log, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")
    except OSError:
        pass


def block(reason):
    print(json.dumps({"decision": "block", "reason": reason}))
    sys.exit(2)


def warn_ctx(text):
    print(json.dumps({"hookSpecificOutput": {"additionalContext": text}}))
    sys.exit(0)


def main():
    try:
        payload = json.load(sys.stdin)
    except (json.JSONDecodeError, EOFError, ValueError):
        sys.exit(0)
    if payload.get("hook_event_name") != "PreToolUse" \
            or payload.get("tool_name") != "exec":
        sys.exit(0)
    cmd = ((payload.get("tool_input") or {}).get("command") or "").strip()
    if not cmd:
        sys.exit(0)

    if T0_ALLOW.search(cmd):
        sys.exit(0)
    feats = extract_features(cmd)
    if trivially_safe(cmd, feats):
        sys.exit(0)

    laya_dir = _laya_dir()
    if laya_dir is None:
        sys.exit(0)
    sys.path.insert(0, laya_dir)
    try:
        import decision_contract as dc
        import laya_client as lc
    except ImportError:
        sys.exit(0)

    config_path = _profile_path()
    cfg = dc.load_config(config_path)
    mode = dc.effective_mode(cfg)
    if mode == "off":
        sys.exit(0)

    state = {
        "goal": "",
        "snippets": cmd + "\n\ncwd: " + os.getcwd()
                    + "\nshell: " + ("powershell" if os.name == "nt"
                                   else "bash"),
        "confidence_hint": json.dumps(feats, sort_keys=True),
    }
    request = {
        "version": dc.VERSION,
        "request_id": f"guard-{os.getpid()}-{int(time.time())}",
        "profile": "cmd-risk-v1",
        "mode": mode,
        "context": {"env_id": "laya-guard"},
        "state": state,
        "candidates": [{"id": "benign"}, {"id": "mutating"},
                       {"id": "irreversible"},
                       {"id": "egress_or_secret"}, {"id": "ambiguous"}],
        "deadline_ms": int(cfg.get("deadline_ms") or 1000),
    }

    started = time.monotonic()
    daemon = lc.ensure_daemon(config_path) if mode != "off" else None
    rec = lc.recommend(request, daemon=daemon,
                       timeout_s=max(2.0, request["deadline_ms"] / 1000 + 1))
    latency_ms = int((time.monotonic() - started) * 1000)

    cand = rec.get("candidate_id") if rec.get("outcome") == "suggestion" \
        else None
    verdict = "PASS"
    if mode == "assist" and rec.get("adoptable"):
        if cand in ("irreversible", "egress_or_secret"):
            verdict = "BLOCK"
        elif cand in ("mutating", "ambiguous") \
                and (feats["outside_repo"] or feats["system_scope"]):
            verdict = "WARN"
    shadow_log({
        "ts": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "session_id": payload.get("session_id", ""),
        "profile": "cmd-risk-v1",
        "request_id": request["request_id"],
        "features": feats, "candidates_n": 5,
        "recommendation": {"outcome": rec.get("outcome"),
                           "candidate_id": cand,
                           "calibrated_probability":
                               rec.get("calibrated_probability")},
        "tier_used": "T2", "latency_ms": latency_ms,
        "final_verdict": verdict,
    })

    if verdict == "BLOCK":
        block(f"laya cmd-risk-v1: {cand} — command classified "
              f"high-risk by calibrated model. Run manually if "
              f"intentional.")
    if verdict == "WARN":
        warn_ctx(f"LAYA-GUARD: command class '{cand}' touches "
                 f"outside-repo/system scope. Proceed only if this "
                 f"is the intended target.")
    sys.exit(0)


if __name__ == "__main__":
    main()
