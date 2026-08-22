#!/usr/bin/env python3
"""Resolve and ensure the working-tree directory SDD uses for one plan's
short-lived artifacts: task briefs, implementer reports, review packages,
and the progress ledger. Print the plan directory's absolute path.

One directory per plan (.devin/sdd/<plan-basename>/) so a follow-up
plan in the same working tree can never read or overwrite another plan's
artifacts. A stale ledger misread as current progress makes controllers
skip whole task sequences.

The workspace lives in the working tree (not under .git/) because some
agents treat .git/ as a protected path. A self-ignoring .gitignore at
.devin/sdd/ keeps every plan's workspace out of git status.

Usage: sdd-workspace.py PLAN_FILE
"""
import os, sys, subprocess, argparse

def git_toplevel():
    result = subprocess.run(
        ["git", "rev-parse", "--show-toplevel"],
        capture_output=True, text=True, check=True
    )
    return result.stdout.strip()

def main():
    parser = argparse.ArgumentParser(description="Resolve SDD workspace for a plan.")
    parser.add_argument("plan_file", help="Path to the plan markdown file")
    args = parser.parse_args()

    plan = args.plan_file
    if not os.path.isfile(plan):
        print(f"no such plan file: {plan}", file=sys.stderr)
        sys.exit(2)

    slug = os.path.splitext(os.path.basename(plan))[0]
    if not slug or slug in (".", ".."):
        print(f"cannot derive a workspace name from: {plan}", file=sys.stderr)
        sys.exit(2)

    try:
        root = git_toplevel()
    except subprocess.CalledProcessError:
        print("not in a git repository", file=sys.stderr)
        sys.exit(2)

    base = os.path.join(root, ".devin", "sdd")
    directory = os.path.join(base, slug)
    os.makedirs(directory, exist_ok=True)

    gitignore = os.path.join(base, ".gitignore")
    if not os.path.exists(gitignore):
        with open(gitignore, "w", encoding="utf-8") as f:
            f.write("*\n")

    print(directory)

if __name__ == "__main__":
    main()
