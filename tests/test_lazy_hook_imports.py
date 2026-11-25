"""Lazy stdlib import pins for consolidated hook children."""
import json
import os
import subprocess
import sys

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCRIPTS = os.path.join(ROOT, "scripts")

PROBE = r'''
import importlib.util
import json
import os
import sys

path = sys.argv[1]
sys.path.insert(0, os.path.dirname(path))
import _hookrun  # production consolidated runner is already loaded
spec = importlib.util.spec_from_file_location("lazy_import_probe", path)
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)
print(json.dumps({
    "subprocess": "subprocess" in sys.modules,
    "socket": "socket" in sys.modules,
    "_gitscan": "_gitscan" in sys.modules,
    "shutil": "shutil" in sys.modules,
    "argparse": "argparse" in sys.modules,
}))
'''

CASES = [
    ("check-ai-signature.py", {"subprocess", "_gitscan"}),
    ("check-push-green.py", {"subprocess"}),
    ("no-em-dash.py", {"subprocess", "_gitscan"}),
    ("dep-audit-gate.py", {"subprocess", "shutil"}),
    ("compact-gate.py", {"subprocess", "socket"}),
    ("context-pressure.py", {"argparse"}),
    ("gh-pr-assignee.py", {"subprocess"}),
    ("git-diff-stat.py", {"subprocess"}),
]


@pytest.mark.parametrize("script,forbidden", CASES)
def test_hook_import_does_not_load_rarely_needed_modules(script, forbidden):
    path = os.path.join(SCRIPTS, script)
    proc = subprocess.run(
        [sys.executable, "-c", PROBE, path],
        capture_output=True, text=True, encoding="utf-8", errors="replace",
        timeout=15)
    assert proc.returncode == 0, proc.stderr
    loaded = json.loads(proc.stdout)
    assert not {name for name in forbidden if loaded[name]}


HOOKRUN_PROBE = r'''
import json
import sys

sys.path.insert(0, sys.argv[1])
import _hookrun  # noqa: F401
print(json.dumps({
    "traceback": "traceback" in sys.modules,
    "hashlib": "hashlib" in sys.modules,
}))
'''


def test_hookrun_import_does_not_load_crash_only_modules():
    """traceback is only for the child-crash path; hashlib only for
    write_to_process payload keys. Neither may load at import time -
    every consolidated spawn pays the cost otherwise."""
    proc = subprocess.run(
        [sys.executable, "-c", HOOKRUN_PROBE, SCRIPTS],
        capture_output=True, text=True, encoding="utf-8", errors="replace",
        timeout=15)
    assert proc.returncode == 0, proc.stderr
    loaded = json.loads(proc.stdout)
    assert not loaded["traceback"], "traceback loaded at import time"
    assert not loaded["hashlib"], "hashlib loaded at import time"
