#!/usr/bin/env python3
"""rz-ops: structured wrapper for the rizin CLI toolchain.

Self-contained static/dynamic RE path that does not depend on
Hopper/Ghidra engines. Drives rizin frontends (rizin, rz-bin, rz-diff,
rz-find, rz-sign) through a whitelist of preset subcommands with JSON
output where available. Every execution subcommand requires an
engagement contract: --target, --window, --roe.

Safety contract:
  - Never runs through a shell; subprocess list-form only.
  - Whitelisted presets only; free-text never reaches the rizin -c
    command string (function/arg tokens are regex-validated).
  - `dbg` executes the target: mode active, requires --confirm.
  - Missing binaries/plugins -> {"status": "missing"}; never fabricate.

Output: JSON envelope on stdout. Exit 0 = ok, non-zero = error.
"""
import argparse
import json
import platform
import re
import shutil
import subprocess
import sys
import time

DEFAULT_TIMEOUT = 300
MAX_OUTPUT = 1024 * 1024  # 1 MiB per stream

# Binaries probed by doctor.
RZ_BINS = ["rizin", "rz-bin", "rz-asm", "rz-diff", "rz-find",
           "rz-hash", "rz-sign", "rz-ax", "rz-run"]

# Tokens interpolated into rizin -c strings must match this (symbol,
# hex address, or flag name). Anything else is rejected before exec.
VALID_TOKEN = re.compile(r"^[A-Za-z0-9_.@$-]{1,128}$")
# rizin debug commands: letter-prefixed 'd' family only (db, dc, dr,
# dso, dcu, dsi...). No shell escapes ('!'/'R!'), no write commands
# outside the d-family.
VALID_DBG_CMD = re.compile(r"^d[a-zA-Z?]{0,8}$")


def emit(payload, code=0):
    json.dump(payload, sys.stdout, indent=2, sort_keys=False)
    sys.stdout.write("\n")
    sys.exit(code)


def rz_path(name):
    return shutil.which(name)


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
        creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
    except FileNotFoundError as e:
        return {"ok": False, "status": "missing", "error": str(e),
                "argv": argv}
    except subprocess.TimeoutExpired:
        return {"ok": False, "status": "timeout",
                "error": "timeout after %ds" % timeout, "argv": argv}
    return {
        "ok": proc.returncode == 0,
        "status": "ok" if proc.returncode == 0 else "error",
        "exit_code": proc.returncode,
        "stdout": (proc.stdout or "")[:MAX_OUTPUT],
        "stderr": (proc.stderr or "")[:MAX_OUTPUT],
        "elapsed_s": round(time.time() - t0, 2),
        "argv": argv,
    }


def rizin_argv(target, cmd):
    """argv for one-shot rizin -q0 -c <cmd> <target>."""
    return [rz_path("rizin"), "-q0", "-c", cmd, target]


def require_contract(args):
    missing = [f for f in ("target", "window", "roe")
               if not getattr(args, f)]
    if missing:
        emit({"ok": False, "status": "contract_violation",
              "error": "missing required contract fields: " + ", ".join(missing),
              "contract": {
                  "target": "artifact path (binary/dump/library)",
                  "window": "engagement window",
                  "roe": "rules of engagement id/text"}}, 2)


def require_bin(name):
    path = rz_path(name)
    if not path:
        emit({"ok": False, "status": "missing",
              "error": "%s not found on PATH" % name}, 1)
    return path


def check_fcn(args):
    fcn = getattr(args, "fcn", None)
    if fcn and not VALID_TOKEN.match(fcn):
        emit({"ok": False, "status": "rejected",
              "error": "invalid --fcn token (expected symbol/hex/flag)"}, 2)
    return fcn


def cmd_doctor(_args):
    report = {
        "host": {"os": platform.system(), "python": platform.python_version()},
        "bins": {b: (rz_path(b) or "missing") for b in RZ_BINS},
    }
    rizin = rz_path("rizin")
    report["rizin_version"] = None
    if rizin:
        ver = run_cmd([rizin, "-v"], timeout=30)
        report["rizin_version"] = (ver.get("stdout") or "").splitlines()[:1]
    present = [b for b, p in report["bins"].items() if p != "missing"]
    report["status"] = "ok" if "rizin" in present else (
        "degraded" if present else "missing")
    report["notes"] = [
        "decompile depends on external plugins: jsdec (pddj) or",
        "rz-ghidra (pdgj); absence surfaces in subcommand output,",
        "never fabricated.",
    ]
    emit(report, 0 if present else 1)


def cmd_capabilities(_args):
    emit({
        "wrapper": "rz-ops",
        "contract": ["target", "window", "roe"],
        "engine": "rizin CLI (self-contained; no Hopper/Ghidra needed)",
        "passive_subcommands": [
            "info", "functions", "imports", "strings", "disasm",
            "decompile", "xrefs", "diff", "find", "sign",
        ],
        "active_subcommands": ["dbg"],
        "presets": {
            "info": "rz-bin -Ij",
            "functions": "rizin -q0 -c 'aa;aflj'",
            "imports": "rizin -q0 -c 'iij'",
            "strings": "rizin -q0 -c 'izj'",
            "disasm": "rizin -q0 -c 'aa;pdfj @ <fcn>'",
            "decompile": "rizin -q0 -c 'aa;<pddj|pdgj> [@ fcn]'",
            "xrefs": "rizin -q0 -c 'aa;axtj @ <fcn>'",
            "diff": "rz-diff -j <target> <other>",
            "find": "rz-find passthrough (-- args)",
            "sign": "rz-sign passthrough (-- args)",
            "dbg": "rizin -q0 -d -c '<dcmd>' (validated d-family only)",
        },
        "notes": [
            "Free text never reaches rizin -c; --fcn/--arg are",
            "regex-validated tokens. find/sign forward args to their",
            "own binaries in list-form.",
        ],
    })


def cmd_exec(args):
    require_contract(args)
    sub = args.command
    extra = list(args.extra or [])
    if extra and extra[0] == "--":
        extra = extra[1:]

    if sub == "dbg":
        if not args.confirm:
            emit({"ok": False, "status": "requires_confirmation",
                  "mode": "active",
                  "error": "dbg executes the target; requires --confirm"}, 3)
        if not args.dcmd or not VALID_DBG_CMD.match(args.dcmd):
            emit({"ok": False, "status": "rejected",
                  "error": "--dcmd must be a rizin d-family command "
                           "(e.g. db, dc, dr, dso)"}, 2)
        cmd = args.dcmd
        if args.darg:
            if not VALID_TOKEN.match(args.darg):
                emit({"ok": False, "status": "rejected",
                      "error": "invalid --darg token"}, 2)
            cmd = "%s %s" % (args.dcmd, args.darg)
        require_bin("rizin")
        argv = [rz_path("rizin"), "-q0", "-d", "-c", cmd, args.target]
    elif sub == "info":
        argv = [require_bin("rz-bin"), "-Ij", args.target]
    elif sub == "diff":
        other = extra[0] if extra else None
        if not other:
            emit({"ok": False, "status": "rejected",
                  "error": "diff needs a second artifact: -- <other>"}, 2)
        argv = [require_bin("rz-diff"), "-j", args.target, other]
    elif sub in ("find", "sign"):
        tool = "rz-%s" % sub
        argv = [require_bin(tool)] + extra + [args.target]
    else:
        fcn = check_fcn(args)
        require_bin("rizin")
        at = " @ %s" % fcn if fcn else ""
        if sub == "functions":
            rzcmd = "aa;aflj"
        elif sub == "imports":
            rzcmd = "iij"
        elif sub == "strings":
            rzcmd = "izj"
        elif sub == "disasm":
            rzcmd = "aa;pdfj%s" % at
        elif sub == "xrefs":
            rzcmd = "aa;axtj%s" % at
        elif sub == "decompile":
            engine = args.engine or "jsdec"
            rzcmd = "aa;%s%s" % ("pddj" if engine == "jsdec" else "pdgj", at)
        else:
            emit({"ok": False, "status": "rejected",
                  "error": "unknown subcommand: %s" % sub}, 2)
        argv = rizin_argv(args.target, rzcmd)

    result = run_cmd(argv, timeout=args.timeout)
    result["subcommand"] = sub
    result["mode"] = "active" if sub == "dbg" else "passive"
    result["contract"] = {"target": args.target, "window": args.window,
                          "roe": args.roe}
    emit(result, 0 if result.get("ok") else 1)


EXEC_SUBCOMMANDS = ["info", "functions", "imports", "strings", "disasm",
                    "decompile", "xrefs", "diff", "find", "sign", "dbg"]


def main():
    ap = argparse.ArgumentParser(
        prog="rz-ops",
        description="Structured wrapper for the rizin CLI toolchain")
    ap.add_argument("--self-test", action="store_true",
                    help="alias for `doctor`")
    sub = ap.add_subparsers(dest="command")
    sub.add_parser("doctor", help="probe rizin binaries + version")
    sub.add_parser("capabilities", help="preset catalog + contract")

    for name in EXEC_SUBCOMMANDS:
        p = sub.add_parser(name, help="rz %s preset" % name)
        p.add_argument("--target", help="artifact path")
        p.add_argument("--window", help="engagement window")
        p.add_argument("--roe", help="rules of engagement")
        p.add_argument("--fcn", help="function addr/name (validated token)")
        p.add_argument("--engine", choices=["jsdec", "ghidra"],
                       help="decompile backend: jsdec(pddj) or ghidra(pdgj)")
        p.add_argument("--dcmd", help="dbg: rizin d-family command")
        p.add_argument("--darg", help="dbg: optional validated arg")
        p.add_argument("--confirm", action="store_true",
                       help="acknowledge active mode (dbg)")
        p.add_argument("--timeout", type=int, default=DEFAULT_TIMEOUT)
        p.add_argument("extra", nargs=argparse.REMAINDER,
                       help="args after -- (diff other / find / sign)")

    args = ap.parse_args()
    if args.self_test or args.command in (None, "doctor"):
        cmd_doctor(args)
    elif args.command == "capabilities":
        cmd_capabilities(args)
    elif args.command in EXEC_SUBCOMMANDS:
        cmd_exec(args)
    else:
        ap.print_help()
        sys.exit(2)


if __name__ == "__main__":
    main()
