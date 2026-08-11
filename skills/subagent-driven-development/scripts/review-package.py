#!/usr/bin/env python3
"""Generate a review package: commit list, stat summary, and the net
diff with extended context, written to a file the reviewer reads in one call.
Using the recorded per-task BASE (not HEAD~1) keeps multi-commit tasks intact.

Usage: review-package.py PLAN_FILE BASE HEAD [OUTFILE]
Default OUTFILE: <repo-root>/.devin/sdd/<plan-basename>/review-<base7>..<head7>.diff
"""
import os, sys, re, argparse, subprocess

def git_rev_parse(ref, verify=True):
    cmd = ["git", "rev-parse"]
    if verify:
        cmd.extend(["--verify", ref])
    else:
        cmd.append(ref)
    result = subprocess.run(cmd, capture_output=True, text=True, check=True)
    return result.stdout.strip()

def git_log(base, head):
    result = subprocess.run(["git", "log", "--oneline", f"{base}..{head}"], capture_output=True, text=True, check=True)
    return result.stdout

def git_diff_stat(base, head):
    result = subprocess.run(["git", "diff", "--stat", f"{base}..{head}"], capture_output=True, text=True, check=True)
    return result.stdout

def git_diff(base, head):
    result = subprocess.run(["git", "diff", "-U10", f"{base}..{head}"], capture_output=True, text=True, check=True)
    return result.stdout

def git_rev_list_count(base, head):
    result = subprocess.run(["git", "rev-list", "--count", f"{base}..{head}"], capture_output=True, text=True, check=True)
    return int(result.stdout.strip())

def git_short(ref):
    result = subprocess.run(["git", "rev-parse", "--short", ref], capture_output=True, text=True, check=True)
    return result.stdout.strip()

def main():
    parser = argparse.ArgumentParser(description="Generate a review package.")
    parser.add_argument("plan_file", help="Path to the plan markdown file")
    parser.add_argument("base", help="BASE commit SHA")
    parser.add_argument("head", help="HEAD commit SHA")
    parser.add_argument("outfile", nargs="?", help="Optional output file path")
    args = parser.parse_args()

    if not os.path.isfile(args.plan_file):
        print(f"no such plan file: {args.plan_file}", file=sys.stderr)
        sys.exit(2)

    try:
        git_rev_parse(args.base, verify=True)
        git_rev_parse(args.head, verify=True)
    except subprocess.CalledProcessError as e:
        print(f"bad ref: {e}", file=sys.stderr)
        sys.exit(2)

    if args.outfile:
        out = args.outfile
    else:
        script_dir = os.path.dirname(os.path.abspath(__file__))
        workspace = subprocess.run([sys.executable, os.path.join(script_dir, "sdd-workspace.py"), args.plan_file], capture_output=True, text=True, check=True).stdout.strip()
        short_base = git_short(args.base)
        short_head = git_short(args.head)
        out = os.path.join(workspace, f"review-{short_base}..{short_head}.diff")

    commits = git_log(args.base, args.head)
    stat = git_diff_stat(args.base, args.head)
    diff = git_diff(args.base, args.head)
    commit_count = git_rev_list_count(args.base, args.head)

    os.makedirs(os.path.dirname(out), exist_ok=True)
    with open(out, "w", encoding="utf-8") as f:
        f.write(f"# Review package: {args.base}..{args.head}\n\n")
        f.write("## Commits\n")
        f.write(commits)
        f.write("\n\n## Files changed\n")
        f.write(stat)
        f.write("\n\n## Diff\n")
        f.write(diff)

    size = os.path.getsize(out)
    print(f"wrote {out}: {commit_count} commit(s), {size} bytes")

if __name__ == "__main__":
    main()
