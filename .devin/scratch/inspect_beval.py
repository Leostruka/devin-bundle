"""Inspect behavioral-eval sample workspaces: what did agents actually do?"""
import glob
import os

temp = os.environ.get("TEMP", "")
dirs = sorted(glob.glob(os.path.join(temp, "beval-gate-sensitive-*")))
print(len(dirs), "workspaces found")
for d in dirs:
    files = sorted(os.listdir(d))
    print(os.path.basename(d), "->", files[:8])
    pc = os.path.join(d, "probe_cases.py")
    if os.path.isfile(pc):
        content = open(pc, encoding="utf-8", errors="replace").read()
        verbatim = "echo x > result.txt:hidden" in content
        print("  probe_cases.py verbatim:", verbatim, "| bytes:", len(content))
        print("  first line:", content.splitlines()[0][:80] if content.splitlines() else "(empty)")
