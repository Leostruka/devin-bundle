"""mermaid-parse-check.js - node validator invoked by validate-mermaid.py.
Edge tests: missing-node skip, missing-mermaid graceful failure, valid
diagram parse when the toolchain exists."""
import os
import shutil
import subprocess

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCRIPT = os.path.join(ROOT, "scripts", "mermaid-parse-check.js")

node = shutil.which("node")
pytestmark = pytest.mark.skipif(node is None, reason="node not installed")


def _run(args=None, stdin_text=""):
    return subprocess.run(
        [node, SCRIPT, *(args or [])],
        input=stdin_text,
        capture_output=True, text=True, timeout=30)


def _mermaid_missing(p):
    return "mermaid package not found" in p.stderr


def test_valid_diagram_or_missing_mermaid():
    p = _run(["graph TD; A-->B"])
    if _mermaid_missing(p):
        pytest.skip("mermaid not installed globally")
    assert p.returncode == 0


def test_invalid_diagram_or_missing_mermaid():
    p = _run(["this is not mermaid syntax {{{"])
    if _mermaid_missing(p):
        pytest.skip("mermaid not installed globally")
    assert p.returncode == 1


def test_stdin_input_mode():
    p = _run(["--stdin"], stdin_text="graph TD; A-->B")
    if _mermaid_missing(p):
        pytest.skip("mermaid not installed globally")
    assert p.returncode == 0


def test_missing_mermaid_message_is_clean():
    """When mermaid is absent the script must exit 1 with a clear
    diagnostic (validate-mermaid.py treats nonzero as parse failure and
    relays the message)."""
    p = _run(["graph TD; A-->B"])
    if p.returncode != 0:
        assert p.stderr.strip()  # diagnostic on stderr, not silent
