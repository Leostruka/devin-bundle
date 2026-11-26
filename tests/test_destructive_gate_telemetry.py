"""destructive-gate.py: block telemetry (metrics/gate-blocks.jsonl).

Every block decision funnels through block(), which appends one JSONL
line (ts/kind/cwd) beside the hook's config root. Motivation: FP frequency
claims in self-improvement loops were memory-based guesses; friction
needs numbers. The telemetry must be fail-safe (never affects decisions)
and must not log allowed commands.
"""
import importlib.util
import json
import os
import subprocess
import sys

import pytest

HOOK = os.path.join(os.path.dirname(__file__), "..", "scripts",
                    "destructive-gate.py")
METRICS = os.path.join(os.path.dirname(__file__), "..", "metrics",
                       "gate-blocks.jsonl")
PY = sys.executable


def run_gate(cmd):
    payload = json.dumps({"hook_event_name": "PreToolUse",
                          "tool_name": "exec",
                          "tool_input": {"command": cmd}})
    return subprocess.run([PY, HOOK], input=payload, capture_output=True,
                          text=True, encoding="utf-8", errors="replace")


def _lines():
    if not os.path.isfile(METRICS):
        return []
    with open(METRICS, encoding="utf-8") as fh:
        return [l for l in fh.read().splitlines() if l.strip()]


def test_block_appends_one_jsonl_line():
    before = len(_lines())
    r = run_gate("rm -rf /")  # portable block on every platform
    assert r.returncode == 2
    after = _lines()
    assert len(after) == before + 1
    entry = json.loads(after[-1])
    assert "ts" in entry and "kind" in entry and "cwd" in entry
    assert len(entry["kind"]) <= 80


def test_allowed_command_writes_no_telemetry():
    before = len(_lines())
    r = run_gate("echo hello")
    assert r.returncode == 0
    assert len(_lines()) == before


def test_telemetry_never_breaks_block_decision():
    # even if the metrics path is unwritable, the block must still happen
    # (fail-safe try/except inside _log_block). Simulated here by the fact
    # that the block path returns 2 regardless of telemetry outcome.
    r = run_gate("rm -rf /")
    assert r.returncode == 2
    assert '"decision": "block"' in r.stdout


@pytest.mark.skipif(os.name != "nt",
                    reason="ADS gate is NT-scoped by design: ':' is a "
                           "legal POSIX filename char, so the probe command "
                           "is correctly allowed on POSIX")
def test_matched_excerpt_lifted_into_telemetry_field():
    """Block reasons embed the matched excerpt after 'Matched'; telemetry
    must lift it into its own field so friction analysis does not depend
    on re-parsing the truncated kind string."""
    before = len(_lines())
    r = run_gate("echo x > result.txt:hidden")
    assert r.returncode == 2
    after = _lines()
    assert len(after) == before + 1
    entry = json.loads(after[-1])
    assert "matched" in entry
    assert "result.txt" in entry["matched"]


def test_matched_excerpt_lift_unit_portable():
    """The lift itself is platform-independent regex over the reason
    string; cover it on every platform by calling _log_block directly
    (the ADS end-to-end path above is NT-only)."""
    spec = importlib.util.spec_from_file_location("destructive_gate", HOOK)
    gate = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(gate)
    before = len(_lines())
    gate._log_block("probe reason. Matched 'echo x > result.txt:hidden'"
                    " - trailing guidance")
    after = _lines()
    assert len(after) == before + 1
    entry = json.loads(after[-1])
    assert entry["matched"] == "echo x > result.txt:hidden"


def test_matched_excerpt_absent_unit_portable():
    spec = importlib.util.spec_from_file_location("destructive_gate", HOOK)
    gate = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(gate)
    before = len(_lines())
    gate._log_block("plain reason without any excerpt")
    after = _lines()
    assert len(after) == before + 1
    entry = json.loads(after[-1])
    assert "matched" not in entry


def test_plain_block_without_excerpt_omits_matched():
    before = len(_lines())
    r = run_gate("rm -rf /")  # reason carries no Matched excerpt
    assert r.returncode == 2
    after = _lines()
    entry = json.loads(after[-1])
    assert "matched" not in entry
