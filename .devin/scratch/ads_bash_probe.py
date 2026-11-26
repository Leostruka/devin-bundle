"""Probe: bash (MSYS/Git Bash) semantics for trailing-colon redirect targets.

Complements ads_probe.py (cmd probe): cmd errors loudly on empty stream
names. Question: does bash on Windows behave the same, or does MSYS path
translation silently write somewhere?
"""
import os
import subprocess
import tempfile

d = tempfile.mkdtemp(prefix="adsbash-")
os.chdir(d)

r = subprocess.run(["bash", "-c", "echo x > probe.txt:"],
                   capture_output=True, text=True)
print("bash rc:", r.returncode)
print("bash stderr:", r.stderr.strip()[:150])
print("probe.txt exists:", os.path.isfile("probe.txt"))
print("dir contents:", sorted(os.listdir(".")))

# control: real ADS in bash
r2 = subprocess.run(["bash", "-c", "echo x > real.txt:hidden"],
                    capture_output=True, text=True)
print("real-ads bash rc:", r2.returncode, "stderr:", r2.stderr.strip()[:100])
print("real.txt exists:", os.path.isfile("real.txt"),
      "size:", os.path.getsize("real.txt") if os.path.isfile("real.txt") else "-")
print("dir contents after:", sorted(os.listdir(".")))
