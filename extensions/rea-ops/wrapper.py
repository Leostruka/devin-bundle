#!/usr/bin/env python3
"""rea-ops: local wrapper for the morluto/rea reverse-engineering CLI.

Drives `npx -y rea-agents@latest <subcommand>` (or `rea-agents` on PATH)
through a whitelist of read-only analysis subcommands. Every execution
subcommand requires an engagement contract: --target, --window, --roe.

Safety contract:
  - Never runs through a shell; subprocess list-form only.
  - Whitelisted subcommands only; no arbitrary REA flag injection.
  - Bounded stdout/stderr; hard timeout per call.
  - Missing binary/toolchain -> {"status": "missing"}; never fabricate.
  - Analysis is read-only against the declared --target artifact.

Output: JSON envelope on stdout. Exit 0 = ok, non-zero = error.
"""
import argparse
import json
import platform
import shutil
import subprocess
import sys
import time

REA_PACKAGE = "rea-agents@latest"
REA_BIN = "rea-agents"
DEFAULT_TIMEOUT = 300
MAX_OUTPUT = 1024 * 1024  # 1 MiB per stream

# Whitelisted REA subcommands (read-only analysis surface).
EXEC_SUBCOMMANDS = [
    "analyze",
    "inspect",
    "search",
    "function",
    "xrefs",
    "trace",
    "compare",
]


def emit(payload, code=0):
    json.dump(payload, sys.stdout, indent=2, sort_keys=False)
    sys.stdout.write("\n")
    sys.exit(code)


def resolve_invoker():
    """Return argv prefix that runs the REA CLI, or None."""
    binpath = shutil.which(REA_BIN)
    if binpath:
        return [binpath]
    npx = shutil.which("npx")
    if npx:
        return [npx, "-y", REA_PACKAGE]
    return None


def run_cmd(argv, timeout=DEFAULT_TIMEOUT):
    """Run argv list-form. Returns dict envelope."""
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
        return {"ok": False, "status": "missing", "error": str(e), "argv": argv}
    except subprocess.TimeoutExpired:
        return {
            "ok": False,
            "status": "timeout",
            "error": "timeout after %ds" % timeout,
            "argv": argv,
        }
    return {
        "ok": proc.returncode == 0,
        "status": "ok" if proc.returncode == 0 else "error",
        "exit_code": proc.returncode,
        "stdout": (proc.stdout or "")[:MAX_OUTPUT],
        "stderr": (proc.stderr or "")[:MAX_OUTPUT],
        "elapsed_s": round(time.time() - t0, 2),
        "argv": argv,
    }


def cmd_doctor(_args):
    report = {
        "host": {"os": platform.system(), "python": platform.python_version()},
        "node": shutil.which("node"),
        "npx": shutil.which("npx"),
        "rea_bin": shutil.which(REA_BIN),
        "rea_invocation": None,
        "rea_version": None,
        "rea_doctor": None,
    }
    invoker = resolve_invoker()
    if not invoker:
        report["status"] = "missing"
        report["hint"] = "install Node.js (npx) or rea-agents on PATH"
        emit(report, 1)
    report["rea_invocation"] = invoker

    ver = run_cmd(invoker + ["--version"], timeout=120)
    report["rea_version"] = (ver.get("stdout") or "").strip() or ver.get("stderr")
    report["rea_doctor"] = run_cmd(invoker + ["doctor", "--json"], timeout=180)
    report["status"] = "ok" if ver.get("ok") else "degraded"
    emit(report, 0)


def cmd_capabilities(_args):
    emit({
        "wrapper": "rea-ops",
        "exec_subcommands": EXEC_SUBCOMMANDS,
        "contract": ["target", "window", "roe"],
        "rea_package": REA_PACKAGE,
        "invoker": resolve_invoker(),
        "notes": [
            "REA MCP server intentionally not used: 126 tools exceed the",
            "15-tools-per-server budget. CLI passthrough preserves the",
            "REA contract/evidence model at the bundle boundary.",
            "Engines (Hopper/Ghidra) are probed by `rea doctor`; absent",
            "engines surface as unknown capability, never fabricated.",
        ],
    })


def require_contract(args):
    missing = [f for f in ("target", "window", "roe") if not getattr(args, f)]
    if missing:
        emit({
            "ok": False,
            "status": "contract_violation",
            "error": "missing required contract fields: " + ", ".join(missing),
            "contract": {
                "target": "artifact path (binary/apk/firmware image)",
                "window": "engagement window",
                "roe": "rules of engagement id/text",
            },
        }, 2)


def cmd_exec(args):
    require_contract(args)
    if args.subcommand not in EXEC_SUBCOMMANDS:
        emit({"ok": False, "status": "rejected",
              "error": "subcommand not whitelisted: %s" % args.subcommand}, 2)
    invoker = resolve_invoker()
    if not invoker:
        emit({"ok": False, "status": "missing",
              "error": "rea-agents not found (need npx or rea-agents on PATH)"}, 1)

    extra = list(args.rea_args or [])
    if extra and extra[0] == "--":
        extra = extra[1:]
    argv = invoker + [args.subcommand, args.target] + extra
    result = run_cmd(argv, timeout=args.timeout)
    result["contract"] = {"target": args.target, "window": args.window,
                          "roe": args.roe}
    emit(result, 0 if result.get("ok") else 1)


def main():
    ap = argparse.ArgumentParser(
        prog="rea-ops",
        description="Wrapper for rea-agents reverse-engineering CLI")
    ap.add_argument("--self-test", action="store_true",
                    help="alias for `doctor`")
    sub = ap.add_subparsers(dest="command")

    sub.add_parser("doctor", help="probe REA CLI + engines")
    sub.add_parser("capabilities", help="wrapper/tool catalog")

    for name in EXEC_SUBCOMMANDS:
        p = sub.add_parser(name, help="rea %s passthrough" % name)
        p.add_argument("--target",
                       help="artifact path (binary/apk/firmware)")
        p.add_argument("--window", help="engagement window")
        p.add_argument("--roe", help="rules of engagement")
        p.add_argument("--timeout", type=int, default=DEFAULT_TIMEOUT)
        p.add_argument("rea_args", nargs=argparse.REMAINDER,
                       help="extra args after -- forwarded to rea")

    args = ap.parse_args()
    if args.self_test or args.command in (None, "doctor"):
        cmd_doctor(args)
    elif args.command == "capabilities":
        cmd_capabilities(args)
    elif args.command in EXEC_SUBCOMMANDS:
        args.subcommand = args.command
        cmd_exec(args)
    else:
        ap.print_help()
        sys.exit(2)


if __name__ == "__main__":
    main()
