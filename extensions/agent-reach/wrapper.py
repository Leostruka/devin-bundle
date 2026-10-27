#!/usr/bin/env python3
"""agent-reach: local wrapper for the agent-reach trend/source CLI.

Drives `agent-reach <channel>` on PATH (or `uv tool run agent-reach`)
through a whitelist of credential-free channels only.

Safety contract:
  - Never runs through a shell; subprocess list-form only.
  - Whitelisted channels only: github, youtube, bilibili, v2ex, web, doctor.
  - Credential/cookie channels (twitter, x, reddit, instagram,
    xiaohongshu, boss) are explicitly rejected: bundle security policy
    keeps credentialed scraping out of scope.
  - Bounded stdout/stderr; hard timeout per call.
  - Missing binary/toolchain -> {"status": "missing"}; never fabricate.

Output: JSON envelope on stdout: {status, command, stdout, stderr,
duration_s}. Exit 0 = ok, non-zero = error.
"""
import json
import platform
import shutil
import subprocess
import sys
import time

AR_BIN = "agent-reach"
DEFAULT_TIMEOUT = 120
MAX_OUTPUT = 1024 * 1024  # 1 MiB per stream

# Credential-free channels; safe under the bundle credential policy.
CHANNELS = ["github", "youtube", "bilibili", "v2ex", "web", "doctor"]

# Cookie/credential channels: rejected, not merely absent.
BLOCKED_CHANNELS = {
    "twitter": "requires account cookies/credentials",
    "x": "requires account cookies/credentials",
    "reddit": "requires API credentials",
    "instagram": "requires account cookies/credentials",
    "xiaohongshu": "requires account cookies/credentials",
    "boss": "requires account cookies/credentials",
}


def emit(payload, code=0):
    json.dump(payload, sys.stdout, indent=2, sort_keys=False)
    sys.stdout.write("\n")
    sys.exit(code)


def resolve_invoker():
    """Return argv prefix that runs agent-reach, or None."""
    binpath = shutil.which(AR_BIN)
    if binpath:
        return [binpath]
    uv = shutil.which("uv")
    if uv:
        return [uv, "tool", "run", AR_BIN]
    return None


def envelope(status, command, stdout="", stderr="", duration_s=0.0, **extra):
    env = {
        "status": status,
        "command": command,
        "stdout": stdout,
        "stderr": stderr,
        "duration_s": duration_s,
    }
    env.update(extra)
    return env


def run_cmd(argv, command, timeout=DEFAULT_TIMEOUT):
    """Run argv list-form. Returns JSON envelope dict."""
    t0 = time.time()
    try:
        proc = subprocess.run(
            argv,
            capture_output=True,
            text=True,
            timeout=timeout,
            errors="replace",
        )
    except FileNotFoundError as e:
        return envelope("missing", command, stderr=str(e),
                        duration_s=round(time.time() - t0, 2))
    except subprocess.TimeoutExpired:
        return envelope("timeout", command,
                        stderr="timeout after %ds" % timeout,
                        duration_s=round(time.time() - t0, 2))
    return envelope(
        "ok" if proc.returncode == 0 else "error",
        command,
        stdout=(proc.stdout or "")[:MAX_OUTPUT],
        stderr=(proc.stderr or "")[:MAX_OUTPUT],
        duration_s=round(time.time() - t0, 2),
        exit_code=proc.returncode,
    )


def cmd_doctor(_argv):
    report = envelope("ok", "doctor")
    report["host"] = {"os": platform.system(),
                      "python": platform.python_version()}
    report["agent_reach_bin"] = shutil.which(AR_BIN)
    report["uv"] = shutil.which("uv")
    invoker = resolve_invoker()
    report["agent_reach_invocation"] = invoker
    if not invoker:
        report["status"] = "missing"
        report["hint"] = ("install agent-reach on PATH or uv "
                          "(uv tool run agent-reach)")
        emit(report, 1)
    ver = run_cmd(invoker + ["--version"], "doctor:version")
    report["agent_reach_version"] = (ver.get("stdout") or "").strip() or None
    if ver["status"] != "ok":
        report["status"] = "degraded"
    emit(report, 0 if report["status"] == "ok" else 1)


def cmd_channel(channel, argv):
    invoker = resolve_invoker()
    if not invoker:
        emit(envelope("missing", channel,
                      stderr="agent-reach not found (need agent-reach on "
                             "PATH or uv)"), 1)
    extra = [t for t in argv if t != "--"]
    for t in extra:
        if t.startswith("-"):
            emit(envelope("rejected", channel,
                          stderr="flags not forwarded; positional "
                                 "args only: %s" % t), 2)
    run_argv = invoker + [channel] + extra
    result = run_cmd(run_argv, channel)
    emit(result, 0 if result["status"] == "ok" else 1)


def main(argv=None):
    argv = list(sys.argv[1:] if argv is None else argv)
    if not argv or argv[0] in ("-h", "--help"):
        json.dump({"usage": "wrapper.py <channel> [args]",
                   "channels": CHANNELS,
                   "blocked_channels": sorted(BLOCKED_CHANNELS)},
                  sys.stdout, indent=2)
        sys.stdout.write("\n")
        sys.exit(0 if argv else 2)
    command = argv[0]
    if command in BLOCKED_CHANNELS:
        emit(envelope("rejected", command,
                      stderr="channel requires credentials/cookies and is "
                             "out of scope: %s" % BLOCKED_CHANNELS[command],
                      policy="credential-free channels only",
                      allowed=sorted(CHANNELS)), 2)
    if command not in CHANNELS:
        emit(envelope("rejected", command,
                      stderr="channel not whitelisted: %s" % command,
                      allowed=sorted(CHANNELS)), 2)
    if command == "doctor":
        cmd_doctor(argv[1:])
    else:
        cmd_channel(command, argv[1:])


if __name__ == "__main__":
    main()
