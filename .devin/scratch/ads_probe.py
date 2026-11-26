"""Empirical probe: is `name:` (trailing colon, empty stream) an ADS hazard?

The destructive-gate ADS regex matches targets ending in ':' with nothing
after. If Windows treats an empty stream name as the default stream (or
errors), the match is over-inclusive - a precision bug, not a narrowing
question. Probe writes via cmd redirect and inspects with dir /r.
"""
import os
import subprocess
import tempfile

d = tempfile.mkdtemp(prefix="adsprobe-")
target = os.path.join(d, "f.txt")

# 1. write to trailing-colon target via cmd
r = subprocess.run(["cmd", "/c", f'echo probecontent > "{target}:"'],
                   capture_output=True, text=True)
print("write rc:", r.returncode, "stderr:", r.stderr.strip()[:120])

# 2. does the plain file exist and what does it contain?
plain = os.path.isfile(target)
print("plain file exists:", plain)
if plain:
    print("plain content:", open(target, encoding="utf-8", errors="replace").read().strip()[:60])

# 3. dir /r shows alternate streams
r2 = subprocess.run(["cmd", "/c", f'dir /r "{target}"'],
                    capture_output=True, text=True)
print("dir /r output:")
print(r2.stdout[-500:] if r2.stdout else r2.stderr[:200])

# 4. control: write a real ADS for comparison
r3 = subprocess.run(["cmd", "/c", f'echo adscontent > "{target}:hidden"'],
                    capture_output=True, text=True)
print("ads write rc:", r3.returncode)
r4 = subprocess.run(["cmd", "/c", f'dir /r "{target}"'],
                    capture_output=True, text=True)
print("dir /r after real ADS:")
print(r4.stdout[-500:] if r4.stdout else "")
