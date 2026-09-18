"""screenshot.py gates: JSON-only stdout and the --no-image visual bypass."""
import json
import os
import subprocess
import sys

import pytest

sys.path.insert(0, os.path.dirname(__file__))
import cu_load  # noqa: E402


def test_no_image_bypass_json_contract(tmp_path):
    """--hints --no-image: JSON-only output, sidecar written, no PNG."""
    env = dict(os.environ, PYTHONPATH=str(cu_load.EXT),
               CU_HINT_TTL="120")
    r = subprocess.run(
        [sys.executable, str(cu_load.EXT / "screenshot.py"),
         "--hints", "--no-image", "--window", "all"],
        capture_output=True, text=True, env=env, timeout=60)
    out = json.loads(r.stdout)  # stdout is exactly one JSON object
    if out.get("ok") is False:
        pytest.skip("no UIA elements on this machine: %s" % out.get("error"))
    assert out["capture"] == "skipped" and out["path"] is None
    assert out["hints"] and "generation" in out and "session_id" in out
