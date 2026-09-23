#!/usr/bin/env python3
"""env.py — environment lifecycle CLI. JSON on stdout, prompts on stderr.

`doctor` is read-only (C00). Mutating verbs (create/start/stop/reset)
require interactive human consent on a real TTY — piped stdin refuses.
"""
import argparse
import json
import sys

import cu_env


def _emit(ok, status, **kw):
    out = {"ok": ok, "status": status}
    out.update(kw)
    print(json.dumps(out, indent=2))
    return 0 if ok else 1


def _manager(env_id):
    import cu_target
    target = cu_target.resolve_target(env_id, cu_target.load_registry())
    if target["kind"] != "qemu":
        raise cu_target.TargetError(f"not_a_qemu_env:{env_id}")
    return cu_env.EnvironmentManager(target["spec"])


def _lifecycle(args):
    try:
        mgr = _manager(args.env)
    except Exception as exc:
        return _emit(False, "rejected", error=str(exc))
    try:
        if args.cmd == "create":
            overlay = mgr.create()
            return _emit(True, "dispatched", overlay=str(overlay))
        if args.cmd == "start":
            mgr.start()
            return _emit(True, "dispatched", **mgr.status())
        if args.cmd == "status":
            return _emit(True, "dispatched", **mgr.status())
        if args.cmd == "stop":
            r = mgr.stop(force=args.force)
            r.pop("ok", None)
            return _emit(r.get("status") != "unknown",
                         r.get("status", "dispatched"),
                         **{k: v for k, v in r.items()
                            if k != "status"})
        if args.cmd == "restart":
            mgr.restart()
            return _emit(True, "dispatched", **mgr.status())
        if args.cmd == "reset":
            mgr.reset()
            return _emit(True, "dispatched", **mgr.status())
        if args.cmd == "devices":
            import cu_devices
            return _emit(True, "dispatched",
                         devices=cu_devices.enumerate_devices())
        if args.cmd == "lease-plan":
            import cu_devices
            inv = cu_devices.enumerate_devices()
            pol = {"protected": list(args.protect or []),
                   "protected_serials": list(
                       args.protect_serial or [])}
            req = {"device_id": args.device, "env_id": args.env,
                   "confirmed_by_human": args.confirmed}
            errors = cu_devices.validate_lease(req, pol, inv)
            if errors:
                return _emit(False, "rejected", errors=errors)
            plan = {"op": "lease", "env_id": args.env,
                    "device_id": args.device,
                    "note": "attach is a separate approved step — "
                            "this plan performs no bind/attach"}
            plan["digest"] = cu_env.plan_digest(plan)
            return _emit(True, "planned", plan=plan)
    except cu_env.ConsentDenied:
        return _emit(False, "rejected", error="consent_denied")
    except cu_env.SpecMismatch as exc:
        return _emit(False, "rejected", error=f"spec_mismatch:{exc}")
    except TimeoutError as exc:
        return _emit(False, "timeout", error=str(exc))
    except Exception as exc:
        return _emit(False, "unknown",
                     error=f"{type(exc).__name__}:{exc}")
    return _emit(False, "rejected", error=f"unknown_cmd:{args.cmd}")


def main(argv=None):
    ap = argparse.ArgumentParser(
        prog="env.py", description="computer-use environment control")
    sub = ap.add_subparsers(dest="cmd", required=True)
    doc = sub.add_parser("doctor", help="read-only prerequisite report")
    doc.add_argument("--provider", choices=["qemu"], default="qemu")
    doc.add_argument("--image", dest="image_path", default=None)
    doc.add_argument("--image-sha256", dest="image_sha256", default=None)
    doc.add_argument("--qemu-path", dest="qemu_path", default=None,
                     help="explicit qemu-system binary (bypasses PATH)")
    for verb in ("create", "start", "status", "stop", "restart",
                 "reset"):
        p = sub.add_parser(verb, help=f"{verb} environment")
        p.add_argument("--env", required=True)
    sub.choices["stop"].add_argument("--force", action="store_true")
    dev = sub.add_parser("devices", help="list leasable devices")
    dev.add_argument("--env", required=True)
    lp = sub.add_parser("lease-plan",
                        help="validate + plan a device lease (no attach)")
    lp.add_argument("--env", required=True)
    lp.add_argument("--device", required=True)
    lp.add_argument("--protect", action="append", default=None,
                    help="protected device_id (human pair)")
    lp.add_argument("--protect-serial", action="append",
                    default=None)
    lp.add_argument("--confirmed", action="store_true",
                    help="human confirmed the SECOND pair selection")
    args = ap.parse_args(argv)

    if args.cmd == "doctor":
        print(json.dumps(cu_env.doctor(image_path=args.image_path,
                                       image_sha256=args.image_sha256,
                                       qemu_path=args.qemu_path),
                         indent=2))
        return 0
    return _lifecycle(args)


if __name__ == "__main__":
    sys.exit(main())
