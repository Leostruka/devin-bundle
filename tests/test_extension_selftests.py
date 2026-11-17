"""Run each extension selftest.py as a subprocess so its CLI-level
contracts stay guarded inside pytest.

harness-tree's `tree.py snapshot` once shipped broken (envelope stamp
mutated the caller's component tree) because only library functions were
unit-tested — the selftest existed but nothing ran it.
"""
import glob
import os
import subprocess
import sys

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PY = sys.executable


def _selftests():
    return sorted(glob.glob(
        os.path.join(ROOT, "extensions", "*", "selftest.py")))


@pytest.mark.parametrize("path", _selftests(),
                         ids=lambda p: os.path.basename(os.path.dirname(p)))
def test_extension_selftest(path):
    r = subprocess.run([PY, path], capture_output=True, text=True,
                       encoding="utf-8", errors="replace",
                       cwd=os.path.dirname(path), timeout=120)
    assert r.returncode == 0, \
        f"{os.path.basename(path)} selftest failed:\n{r.stdout}\n{r.stderr}"
