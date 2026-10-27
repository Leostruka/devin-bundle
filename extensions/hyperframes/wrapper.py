#!/usr/bin/env python3
"""hyperframes: local wrapper for the hyperframes HTML-animation CLI.

Drives `npx -y hyperframes@latest <subcommand>` (or `hyperframes` on PATH)
through a small whitelist: doctor, init, render. Renders HTML/data-attr
animations to MP4.

Safety contract:
  - Never runs through a shell; subprocess list-form only.
  - Whitelisted subcommands and whitelisted render flags only.
  - Bounded stdout/stderr; 600s timeout for render, 60s otherwise.
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

HF_PACKAGE = "hyperframes@latest"
HF_BIN = "hyperframes"
DEFAULT_TIMEOUT = 60
RENDER_TIMEOUT = 600
MAX_OUTPUT = 1024 * 1024  # 1 MiB per stream

SUBCOMMANDS = ["doctor", "init", "render"]

# Whitelisted render flags; anything else is rejected as flag injection.
RENDER_FLAGS = {
    "--input": "value",
    "--output": "value",
    "--fps": "value",
    "--duration": "value",
    "--width": "value",
    "--height": "value",
}


def emit(payload, code=0):
    json.dump(payload, sys.stdout, indent=2, sort_keys=False)
    sys.stdout.write("\n")
    sys.exit(code)


def resolve_invoker():
    """Return argv prefix that runs hyperframes, or None."""
    binpath = shutil.which(HF_BIN)
    if binpath:
        return [binpath]
    npx = shutil.which("npx")
    if npx:
        return [npx, "-y", HF_PACKAGE]
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
    report["node"] = shutil.which("node")
    report["npx"] = shutil.which("npx")
    report["ffmpeg"] = shutil.which("ffmpeg")
    report["hyperframes_bin"] = shutil.which(HF_BIN)

    node = shutil.which("node")
    report["node_version"] = None
    report["node_major"] = None
    report["node_ok"] = False
    if node:
        ver = run_cmd([node, "--version"], "doctor:node-version")
        v = (ver.get("stdout") or "").strip() or None
        report["node_version"] = v
        if v and v.startswith("v") and v[1:].split(".")[0].isdigit():
            report["node_major"] = int(v[1:].split(".")[0])
        report["node_ok"] = (report["node_major"] or 0) >= 22

    invoker = resolve_invoker()
    report["hyperframes_invocation"] = invoker
    if not invoker or not report["node_ok"]:
        report["status"] = "missing"
        report["hint"] = ("need Node.js >= 22 with npx (or hyperframes on "
                          "PATH); FFmpeg required for MP4 encode")
        emit(report, 1)
    emit(report, 0)


def parse_render_args(argv):
    """Validate render args against the flag whitelist.

    Returns (forwarded_argv, project_path) or emits a JSON rejection.
    """
    project = None
    fwd = []
    i = 0
    while i < len(argv):
        tok = argv[i]
        if tok == "--":
            i += 1
            continue
        if tok.startswith("--"):
            flag = tok.split("=", 1)[0]
            if flag not in RENDER_FLAGS:
                emit(envelope("rejected", "render",
                              stderr="flag not whitelisted: %s" % flag,
                              allowed_flags=sorted(RENDER_FLAGS)), 2)
            if "=" in tok:
                fwd.append(tok)
                i += 1
            else:
                if i + 1 >= len(argv):
                    emit(envelope("rejected", "render",
                                  stderr="flag missing value: %s" % flag), 2)
                fwd.extend([tok, argv[i + 1]])
                i += 2
        elif tok.startswith("-"):
            emit(envelope("rejected", "render",
                          stderr="flag not whitelisted: %s" % tok,
                          allowed_flags=sorted(RENDER_FLAGS)), 2)
        else:
            if project is not None:
                emit(envelope("rejected", "render",
                              stderr="unexpected extra positional: %s" % tok),
                     2)
            project = tok
            i += 1
    # --input flag also satisfies the project path requirement.
    has_input = project is not None or any(
        t == "--input" or t.startswith("--input=") for t in fwd)
    if not has_input:
        emit(envelope("rejected", "render",
                      stderr="render requires a project path positional "
                             "or --input <path>"), 2)
    return fwd, project


def cmd_render(argv):
    fwd, project = parse_render_args(argv)
    invoker = resolve_invoker()
    if not invoker:
        emit(envelope("missing", "render",
                      stderr="hyperframes not found (need npx or "
                             "hyperframes on PATH)"), 1)
    run_argv = invoker + ["render"] + fwd
    if project is not None:
        run_argv.append(project)
    result = run_cmd(run_argv, "render", timeout=RENDER_TIMEOUT)
    emit(result, 0 if result["status"] == "ok" else 1)


def cmd_init(argv):
    # init accepts a single optional directory positional; no flags.
    extra = [t for t in argv if t != "--"]
    for t in extra:
        if t.startswith("-"):
            emit(envelope("rejected", "init",
                          stderr="flag not whitelisted for init: %s" % t), 2)
    if len(extra) > 1:
        emit(envelope("rejected", "init",
                      stderr="init accepts at most one directory"), 2)
    invoker = resolve_invoker()
    if not invoker:
        emit(envelope("missing", "init",
                      stderr="hyperframes not found (need npx or "
                             "hyperframes on PATH)"), 1)
    run_argv = invoker + ["init"] + extra
    result = run_cmd(run_argv, "init", timeout=DEFAULT_TIMEOUT)
    emit(result, 0 if result["status"] == "ok" else 1)


def main(argv=None):
    argv = list(sys.argv[1:] if argv is None else argv)
    if not argv or argv[0] in ("-h", "--help"):
        json.dump({"usage": "wrapper.py <doctor|init|render> [args]",
                   "subcommands": SUBCOMMANDS,
                   "render_flags": sorted(RENDER_FLAGS)},
                  sys.stdout, indent=2)
        sys.stdout.write("\n")
        sys.exit(0 if argv else 2)
    command = argv[0]
    if command not in SUBCOMMANDS:
        emit(envelope("rejected", command,
                      stderr="subcommand not whitelisted: %s" % command,
                      allowed=sorted(SUBCOMMANDS)), 2)
    if command == "doctor":
        cmd_doctor(argv[1:])
    elif command == "init":
        cmd_init(argv[1:])
    else:
        cmd_render(argv[1:])


if __name__ == "__main__":
    main()
