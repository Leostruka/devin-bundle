#!/usr/bin/env python3
"""Extract one task's full text from an implementation plan into a file the
implementer reads in one call, so the task text never has to be pasted
through the controller's context.

Usage: task-brief.py PLAN_FILE TASK_NUMBER [OUTFILE]
Default OUTFILE: <repo-root>/.devin/sdd/<plan-basename>/task-<N>-brief.md
"""
import os, sys, re, argparse

def find_task(plan_text, n):
    lines = plan_text.splitlines()
    in_fence = False
    in_task = False
    capture = []
    pattern = re.compile(r"^#+\s+Task\s+" + re.escape(str(n)) + r"(\D|$)")

    for line in lines:
        if line.startswith("```"):
            in_fence = not in_fence
            continue
        if in_fence:
            continue
        if pattern.search(line):
            in_task = True
            capture = [line]
            continue
        if in_task:
            # Stop at next task heading of same or higher level
            if re.match(r"^#+\s+Task\s+\d+", line):
                break
            capture.append(line)

    return "\n".join(capture).strip()

def main():
    parser = argparse.ArgumentParser(description="Extract a task brief from a plan.")
    parser.add_argument("plan_file", help="Path to the plan markdown file")
    parser.add_argument("task_number", type=int, help="Task number to extract")
    parser.add_argument("outfile", nargs="?", help="Optional output file path")
    args = parser.parse_args()

    if not os.path.isfile(args.plan_file):
        print(f"no such plan file: {args.plan_file}", file=sys.stderr)
        sys.exit(2)

    with open(args.plan_file, "r", encoding="utf-8") as f:
        plan_text = f.read()

    task_text = find_task(plan_text, args.task_number)
    if not task_text:
        print(f"task {args.task_number} not found in {args.plan_file} (no heading matching 'Task {args.task_number}')", file=sys.stderr)
        sys.exit(3)

    if args.outfile:
        out = args.outfile
    else:
        script_dir = os.path.dirname(os.path.abspath(__file__))
        workspace = subprocess_run([sys.executable, os.path.join(script_dir, "sdd-workspace.py"), args.plan_file])
        slug = os.path.splitext(os.path.basename(args.plan_file))[0]
        out = os.path.join(workspace, f"task-{args.task_number}-brief.md")

    os.makedirs(os.path.dirname(out), exist_ok=True)
    with open(out, "w", encoding="utf-8") as f:
        f.write(task_text)
        f.write("\n")

    line_count = len(task_text.splitlines())
    print(f"wrote {out}: {line_count} lines")

def subprocess_run(cmd):
    import subprocess
    result = subprocess.run(cmd, capture_output=True, text=True, check=True)
    return result.stdout.strip()

if __name__ == "__main__":
    main()
