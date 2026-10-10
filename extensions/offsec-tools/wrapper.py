#!/usr/bin/env python3
"""offsec-tools: safe dispatcher for open-source offensive-security tools.

One entry point for tool discovery (doctor), catalog introspection
(capabilities), and contract-gated execution (run). Backends:
native PATH, WSL2 default distro, or Docker images.

Engagement contract (required for `run`):
  --target  declared target (host, URL, artifact path, device)
  --window  engagement window (e.g. "2026-02-10/2026-02-12 UTC")
  --roe     rules-of-engagement reference

Mode gates (per-tool in catalog):
  passive      -> runs with contract only
  active       -> additionally requires --confirm
  destructive  -> additionally requires --confirm and is flagged in output

Safety contract:
  - subprocess list-form only; no shell interpolation of user args.
  - Missing tool -> status "missing" / result "unknown"; never fabricated.
  - Unsupported platform -> "unsupported_platform".
  - No credential-harvesting tools in the catalog.
  - Bounded output (1 MiB/stream), hard timeout per call.

Output: JSON envelope on stdout.
"""
import argparse
import json
import os
import platform
import re
import shutil
import subprocess
import sys
import time

DEFAULT_TIMEOUT = 300
PROBE_TIMEOUT = 8
MAX_OUTPUT = 1024 * 1024

# name -> {bins:[candidates], backends, tier, mode, domain, image?, hint}
# tier: wsl2-ready | wsl2-gated | wsl2-fragile | native-linux-only | native | docker
TOOL_CATALOG = {
    # --- network / infra ---
    "nmap": {"bins": ["nmap"], "backends": ["native", "wsl"],
             "tier": "wsl2-ready", "mode": "active", "domain": "net",
             "hint": "port/service scan; active probing of target"},
    "masscan": {"bins": ["masscan"], "backends": ["native", "wsl"],
                "tier": "wsl2-ready", "mode": "active", "domain": "net",
                "hint": "high-rate scan; raw socket on Windows"},
    "netexec": {"bins": ["netexec", "nxc", "crackmapexec"],
                "backends": ["native", "wsl"], "tier": "wsl2-ready",
                "mode": "active", "domain": "net",
                "hint": "SMB/WinRM enumeration; verify-not-exploit default"},
    "enum4linux-ng": {"bins": ["enum4linux-ng"], "backends": ["native", "wsl"],
                      "tier": "wsl2-ready", "mode": "active",
                      "domain": "net", "hint": "SMB/RPC enumeration"},
    "testssl.sh": {"bins": ["testssl.sh", "testssl"],
                   "backends": ["wsl", "native"], "tier": "wsl2-ready",
                   "mode": "passive", "domain": "net",
                   "hint": "TLS configuration audit"},
    "openvas": {"bins": ["gvm-cli"], "backends": ["docker", "wsl"],
                "tier": "wsl2-gated", "mode": "active", "domain": "net",
                "image": "greenbone/openvas-scanner",
                "hint": "full scanner; heavy GVM stack"},
    # --- web ---
    "sqlmap": {"bins": ["sqlmap", "sqlmap.py"], "backends": ["native", "wsl"],
               "tier": "wsl2-ready", "mode": "active", "domain": "web",
               "hint": "SQLi detection; --batch recommended"},
    "nuclei": {"bins": ["nuclei"], "backends": ["native", "wsl"],
               "tier": "wsl2-ready", "mode": "active", "domain": "web",
               "hint": "template-based vulnerability scan"},
    "ffuf": {"bins": ["ffuf"], "backends": ["native", "wsl"],
             "tier": "wsl2-ready", "mode": "active", "domain": "web",
             "hint": "content/param fuzzing; rate-limit in ROE"},
    "zap-baseline": {"bins": ["zap-baseline.py"], "backends": ["docker"],
                     "tier": "docker", "mode": "active", "domain": "web",
                     "image": "ghcr.io/zaproxy/zaproxy:stable",
                     "hint": "OWASP ZAP baseline scan container"},
    # --- wireless / RF ---
    "aircrack-ng": {"bins": ["aircrack-ng"], "backends": ["wsl"],
                    "tier": "wsl2-fragile", "mode": "active",
                    "domain": "wireless",
                    "hint": "capture analysis ok; monitor/inject needs USB "
                            "adapter + usbipd-win"},
    "hcxdumptool": {"bins": ["hcxdumptool"], "backends": ["wsl"],
                    "tier": "wsl2-fragile", "mode": "active",
                    "domain": "wireless",
                    "hint": "capture requires usbipd-win passthrough"},
    "hcxtools": {"bins": ["hcxpcapngtool"], "backends": ["wsl", "native"],
                 "tier": "wsl2-ready", "mode": "passive",
                 "domain": "wireless",
                 "hint": "offline pcap->hash conversion; no hardware needed"},
    "kismet": {"bins": ["kismet"], "backends": ["wsl"],
               "tier": "wsl2-fragile", "mode": "active",
               "domain": "wireless",
               "hint": "capture needs adapter passthrough"},
    "bettercap": {"bins": ["bettercap"], "backends": ["wsl", "docker"],
                  "tier": "wsl2-fragile", "mode": "active",
                  "domain": "wireless",
                  "hint": "Wi-Fi workflows need monitor-mode adapter"},
    "hashcat": {"bins": ["hashcat"], "backends": ["native", "wsl"],
                "tier": "wsl2-gated", "mode": "destructive",
                "domain": "wireless",
                "hint": "offline hash recovery; high resource use"},
    "urh": {"bins": ["urh", "urh-cli"], "backends": ["wsl"],
            "tier": "wsl2-fragile", "mode": "passive",
            "domain": "wireless", "hint": "SDR signal analysis"},
    # --- firmware / embedded ---
    "binwalk": {"bins": ["binwalk"], "backends": ["wsl", "native"],
                "tier": "wsl2-ready", "mode": "passive",
                "domain": "firmware", "hint": "v3 recommended (Rust)"},
    "unblob": {"bins": ["unblob"], "backends": ["docker", "wsl"],
               "tier": "wsl2-ready", "mode": "passive",
               "domain": "firmware",
               "image": "ghcr.io/onekey-sec/unblob:latest",
               "hint": "extraction; deep deps handled in image"},
    "emba": {"bins": ["emba"], "backends": ["docker"],
             "tier": "wsl2-gated", "mode": "passive", "domain": "firmware",
             "image": "embeddedprojects/emba",
             "hint": "full firmware audit; heavy container"},
    # --- mobile ---
    "jadx": {"bins": ["jadx", "jadx.bat"], "backends": ["native", "wsl"],
             "tier": "wsl2-ready", "mode": "passive", "domain": "mobile",
             "hint": "APK/DEX decompile"},
    "apktool": {"bins": ["apktool", "apktool.bat"], "backends": ["native", "wsl"],
                "tier": "wsl2-ready", "mode": "passive", "domain": "mobile",
                "hint": "resource decode/smali"},
    "mobsf": {"bins": ["mobsf"], "backends": ["docker"], "tier": "docker",
              "mode": "passive", "domain": "mobile",
              "image": "opensecurity/mobile-security-framework-mobsf",
              "hint": "static+dynamic report engine"},
    "frida": {"bins": ["frida"], "backends": ["native", "wsl"],
              "tier": "wsl2-ready", "mode": "active", "domain": "mobile",
              "hint": "dynamic instrumentation; needs rooted emu/device"},
    "objection": {"bins": ["objection"], "backends": ["native", "wsl"],
                  "tier": "wsl2-ready", "mode": "active", "domain": "mobile",
                  "hint": "runtime exploration on instrumented app"},
    # --- reverse engineering (non-REA engines) ---
    "capa": {"bins": ["capa"], "backends": ["native", "wsl"],
             "tier": "wsl2-ready", "mode": "passive", "domain": "re",
             "hint": "capability detection"},
    "floss": {"bins": ["floss"], "backends": ["native", "wsl"],
              "tier": "wsl2-ready", "mode": "passive", "domain": "re",
              "hint": "obfuscated string extraction"},
    "yara": {"bins": ["yara"], "backends": ["native", "wsl"],
             "tier": "wsl2-ready", "mode": "passive", "domain": "re",
             "hint": "pattern match; rules file required"},
    "rizin": {"bins": ["rizin", "rz-bin"], "backends": ["native", "wsl"],
              "tier": "wsl2-ready", "mode": "passive", "domain": "re",
              "hint": "CLI disasm/analysis; radare2 fork"},
    "ghidra": {"bins": ["analyzeHeadless", "analyzeHeadless.bat"],
               "backends": ["native", "wsl"], "tier": "wsl2-gated",
               "mode": "passive", "domain": "re",
               "hint": "headless analysis; needs JDK"},
}

WINDOWS = platform.system() == "Windows"


def emit(payload, code=0):
    json.dump(payload, sys.stdout, indent=2, sort_keys=False)
    sys.stdout.write("\n")
    sys.exit(code)


def run_cmd(argv, timeout=DEFAULT_TIMEOUT):
    t0 = time.time()
    try:
        proc = subprocess.run(argv, capture_output=True, text=True,
                              timeout=timeout, errors="replace")
    except FileNotFoundError as e:
        return {"ok": False, "status": "missing", "error": str(e),
                "argv": argv}
    except subprocess.TimeoutExpired:
        return {"ok": False, "status": "timeout",
                "error": "timeout after %ds" % timeout, "argv": argv}
    except OSError as e:
        return {"ok": False, "status": "error", "error": str(e),
                "argv": argv}
    return {
        "ok": proc.returncode == 0,
        "status": "ok" if proc.returncode == 0 else "error",
        "exit_code": proc.returncode,
        "stdout": (proc.stdout or "")[:MAX_OUTPUT],
        "stderr": (proc.stderr or "")[:MAX_OUTPUT],
        "elapsed_s": round(time.time() - t0, 2),
        "argv": argv,
    }


def native_path(tool):
    for b in TOOL_CATALOG[tool]["bins"]:
        p = shutil.which(b)
        if p:
            return p
    return None


def wsl_available():
    if not WINDOWS or not shutil.which("wsl"):
        return False
    r = run_cmd(["wsl", "-e", "true"], timeout=PROBE_TIMEOUT)
    return r.get("ok", False)


def docker_available():
    if not shutil.which("docker"):
        return False
    r = run_cmd(["docker", "version", "--format", "{{.Server.Version}}"],
                timeout=PROBE_TIMEOUT)
    return r.get("ok", False)


def wsl_probe_all():
    """One WSL call probing every catalog binary. Returns {bin: path|None}."""
    bins = sorted({b for t in TOOL_CATALOG.values() for b in t["bins"]})
    script = "for t in %s; do p=$(command -v $t 2>/dev/null); echo \"$t=$p\"; done" % " ".join(bins)
    r = run_cmd(["wsl", "-e", "sh", "-c", script], timeout=30)
    found = {}
    if r.get("stdout"):
        for line in r["stdout"].splitlines():
            if "=" in line:
                k, _, v = line.partition("=")
                found[k.strip()] = v.strip() or None
    return found


def wsl_path(tool, probe):
    for b in TOOL_CATALOG[tool]["bins"]:
        if probe.get(b):
            return probe[b]
    return None


def to_wsl_arg(arg):
    """Translate drive-letter paths for WSL; leave other args verbatim."""
    m = re.match(r"^([A-Za-z]):[\\/](.*)$", arg)
    if m:
        rest = m.group(2).replace("\\", "/")
        return "/mnt/%s/%s" % (m.group(1).lower(), rest)
    return arg


def cmd_capabilities(_args):
    emit({
        "wrapper": "offsec-tools",
        "contract": ["target", "window", "roe"],
        "backends": ["native", "wsl", "docker"],
        "mode_gates": {"active": "--confirm", "destructive": "--confirm"},
        "tools": TOOL_CATALOG,
        "notes": [
            "wsl2-fragile: RF capture/inject needs usbipd-win + hardware.",
            "native-linux-only workflows (firmadyne-style emulation,",
            "monitor-mode Wi-Fi without USB adapter) report",
            "unsupported_platform rather than faking capability.",
            "No credential-harvesting tools in catalog by design.",
        ],
    })


def cmd_doctor(_args):
    wsl_ok = wsl_available()
    docker_ok = docker_available()
    wsl_probe = wsl_probe_all() if wsl_ok else {}
    tools = {}
    for name, meta in sorted(TOOL_CATALOG.items()):
        entry = {"tier": meta["tier"], "mode": meta["mode"],
                 "domain": meta["domain"], "backends": {}}
        for be in meta["backends"]:
            if be == "native":
                entry["backends"]["native"] = native_path(name) or "missing"
            elif be == "wsl":
                if not wsl_ok:
                    entry["backends"]["wsl"] = "unsupported_platform"
                else:
                    entry["backends"]["wsl"] = wsl_path(name, wsl_probe) or "missing"
            elif be == "docker":
                entry["backends"]["docker"] = (
                    meta.get("image") if docker_ok else "unsupported_platform")
        known = [v for v in entry["backends"].values()
                 if v not in ("missing", "unsupported_platform")]
        entry["status"] = "present" if known else "unknown"
        tools[name] = entry
    emit({
        "host": {"os": platform.system(), "python": platform.python_version()},
        "wsl": "available" if wsl_ok else ("unsupported_platform" if not WINDOWS
                                           else "unavailable"),
        "docker": "available" if docker_ok else "unavailable",
        "tools": tools,
    })


def require_contract(args):
    missing = [f for f in ("target", "window", "roe") if not getattr(args, f)]
    if missing:
        emit({"ok": False, "status": "contract_violation",
              "error": "missing: " + ", ".join(missing),
              "contract": {"target": "declared target",
                           "window": "engagement window",
                           "roe": "rules of engagement"}}, 2)


def pick_backend(meta, requested):
    if requested:
        if requested not in meta["backends"]:
            return None, "unsupported_platform"
        return requested, None
    for be in meta["backends"]:
        if be == "native" and native_path_probe(meta):
            return "native", None
        if be == "wsl" and WSL_OK:
            return "wsl", None
        if be == "docker" and DOCKER_OK:
            return "docker", None
    return None, "missing"


def native_path_probe(meta):
    for b in meta["bins"]:
        if shutil.which(b):
            return shutil.which(b)
    return None


WSL_OK = None
DOCKER_OK = None


def build_argv(tool, meta, backend, target, extra):
    if backend == "native":
        binary = native_path_probe(meta)
        if not binary:
            return None, "missing"
        return [binary] + extra, None
    if backend == "wsl":
        if not WSL_OK:
            return None, "unsupported_platform"
        binary = meta["bins"][0]
        return (["wsl", "-e", binary] +
                [to_wsl_arg(a) for a in extra]), None
    if backend == "docker":
        if not DOCKER_OK:
            return None, "unsupported_platform"
        image = meta.get("image")
        if not image:
            return None, "missing"
        argv = ["docker", "run", "--rm"]
        args = list(extra)
        if target and os.path.exists(target):
            mount_dir = os.path.abspath(target if os.path.isdir(target)
                                        else os.path.dirname(target))
            argv += ["-v", "%s:/work:ro" % mount_dir]
            base = os.path.basename(target.rstrip("\\/"))
            args = ["/work/" + base if a == target else a for a in args]
        argv += [image] + args
        return argv, None
    return None, "unsupported_platform"


def cmd_run(args):
    require_contract(args)
    meta = TOOL_CATALOG.get(args.tool)
    if not meta:
        emit({"ok": False, "status": "rejected",
              "error": "tool not in catalog: %s" % args.tool,
              "catalog": sorted(TOOL_CATALOG)}, 2)
    if meta["mode"] in ("active", "destructive") and not args.confirm:
        emit({"ok": False, "status": "requires_confirmation",
              "mode": meta["mode"],
              "error": "tool mode '%s' requires --confirm" % meta["mode"],
              "hint": meta.get("hint")}, 3)

    global WSL_OK, DOCKER_OK
    if WSL_OK is None:
        WSL_OK = wsl_available()
    if DOCKER_OK is None:
        DOCKER_OK = docker_available()

    extra = list(args.tool_args or [])
    if extra and extra[0] == "--":
        extra = extra[1:]
    if not extra:
        extra = [target_arg(meta, args.target)]

    backend, err = pick_backend(meta, args.backend)
    if err:
        emit({"ok": False, "status": err,
              "tool": args.tool, "backend": args.backend or "auto"}, 1)
    argv, err = build_argv(args.tool, meta, backend, args.target, extra)
    if err:
        emit({"ok": False, "status": err, "tool": args.tool,
              "backend": backend}, 1)

    result = run_cmd(argv, timeout=args.timeout)
    result.update({
        "tool": args.tool, "backend": backend, "mode": meta["mode"],
        "destructive": meta["mode"] == "destructive",
        "contract": {"target": args.target, "window": args.window,
                     "roe": args.roe},
    })
    emit(result, 0 if result.get("ok") else 1)


def target_arg(meta, target):
    """Fallback target flag when user passes no explicit tool args."""
    if meta["domain"] in ("net", "web"):
        return target
    return target


def main():
    ap = argparse.ArgumentParser(
        prog="offsec-tools",
        description="Contract-gated dispatcher for OSS offensive tools")
    ap.add_argument("--self-test", action="store_true",
                    help="alias for `doctor`")
    sub = ap.add_subparsers(dest="command")
    sub.add_parser("doctor", help="probe tools/backends")
    sub.add_parser("capabilities", help="dump tool catalog")
    p = sub.add_parser("run", help="run a catalog tool under contract")
    p.add_argument("--tool", required=True, help="catalog tool name")
    p.add_argument("--target", help="declared target")
    p.add_argument("--window", help="engagement window")
    p.add_argument("--roe", help="rules of engagement")
    p.add_argument("--backend", choices=["native", "wsl", "docker"])
    p.add_argument("--confirm", action="store_true",
                   help="acknowledge active/destructive mode")
    p.add_argument("--timeout", type=int, default=DEFAULT_TIMEOUT)
    p.add_argument("tool_args", nargs=argparse.REMAINDER,
                   help="args after -- forwarded verbatim")

    args = ap.parse_args()
    if args.self_test or args.command in (None, "doctor"):
        cmd_doctor(args)
    elif args.command == "capabilities":
        cmd_capabilities(args)
    elif args.command == "run":
        cmd_run(args)
    else:
        ap.print_help()
        sys.exit(2)


if __name__ == "__main__":
    main()
