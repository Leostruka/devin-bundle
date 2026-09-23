#!/usr/bin/env python3
"""env.py — environment lifecycle CLI. JSON on stdout, prompts on stderr.

Only `doctor` is implemented (C00). Mutating verbs (create/start/stop/
reset) arrive with C04 and require interactive human consent — they are
absent on purpose, not stubs.
"""
import argparse
import json
import sys

import cu_env


def main(argv=None):
    ap = argparse.ArgumentParser(
        prog="env.py", description="computer-use environment control")
    sub = ap.add_subparsers(dest="cmd", required=True)
    doc = sub.add_parser("doctor", help="read-only prerequisite report")
    doc.add_argument("--provider", choices=["qemu"], default="qemu")
    doc.add_argument("--image", dest="image_path", default=None)
    doc.add_argument("--image-sha256", dest="image_sha256", default=None)
    args = ap.parse_args(argv)

    if args.cmd == "doctor":
        print(json.dumps(cu_env.doctor(image_path=args.image_path,
                                       image_sha256=args.image_sha256),
                         indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
