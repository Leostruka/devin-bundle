#!/usr/bin/env python3
"""Fake `gh` — logs every invocation as JSONL to $FAKE_GH_LOG.

gh-pr-assignee's E2E: the hook calls `gh pr edit <url> --add-assignee X`
via a REAL subprocess; this shim proves the argv crossing the process
boundary. `gh pr create` (never actually invoked by the hook, payload is
synthetic) would print a URL for completeness.
"""
import json
import os
import sys


def main():
    argv = sys.argv[1:]
    path = os.environ.get("FAKE_GH_LOG")
    if path:
        with open(path, "a", encoding="utf-8") as f:
            f.write(json.dumps({"argv": argv, "cwd": os.getcwd()}) + "\n")
    if argv[:2] == ["pr", "create"]:
        sys.stdout.write("https://github.com/Acme/widgets/pull/42\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
