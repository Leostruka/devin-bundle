#!/usr/bin/env python3
"""find-polluter.py - bisect which test file creates an unwanted artifact.

Usage:
    python find-polluter.py <watch-path> <test-glob> [-- <extra pytest args>]

For each test file matching <test-glob>, runs it alone via pytest and
checks whether <watch-path> appeared (or changed mtime) afterwards.
Stops at the first polluter. The watch path is never deleted or touched -
run this from the workdir where the pollution shows up.

Exit codes: 0 = no polluter found, 1 = polluter found, 2 = usage error.
"""
import argparse
import glob
import os
import subprocess
import sys


def _stat_key(path):
    try:
        st = os.stat(path)
        return (True, st.st_mtime_ns, st.st_size)
    except OSError:
        return (False, 0, 0)


def main(argv=None):
    ap = argparse.ArgumentParser(
        description="Bisect which test file creates an unwanted artifact.")
    ap.add_argument("watch", help="path whose creation/mutation marks pollution")
    ap.add_argument("tests", help="glob for test files, e.g. 'src/**/*.test.ts'")
    ap.add_argument("--runner", default="pytest",
                    help="test command template, must contain {test} "
                         "(default: 'pytest {test} -x -q')")
    args, extra = ap.parse_known_args(argv)

    files = sorted(glob.glob(args.tests, recursive=True))
    if not files:
        print("no test files match: " + args.tests, file=sys.stderr)
        return 2
    cmd_tpl = args.runner if "{test}" in args.runner else args.runner + " {test}"

    print("bisecting %d files; watch=%s" % (len(files), args.watch))
    for f in files:
        before = _stat_key(args.watch)
        cmd = cmd_tpl.format(test=f).split() + extra
        r = subprocess.run(cmd, capture_output=True, text=True,
                           encoding="utf-8", errors="replace")
        after = _stat_key(args.watch)
        polluted = after != before and (after[0] or not before[0])
        if polluted:
            print("POLLUTER: %s (rc=%d)" % (f, r.returncode))
            print("  watch %s: %s -> %s" % (args.watch, before, after))
            return 1
        print("clean: %s (rc=%d)" % (f, r.returncode))
    print("no polluter found")
    return 0


if __name__ == "__main__":
    sys.exit(main())
