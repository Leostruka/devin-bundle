"""PreToolUse matcher coverage for validate-tool-args CHECKS.

Repro 2026-11-24 (dead-wire): CHECKS defined 18 tool validators but the
hooks.v1.json matchers only fired for exec/write/edit/notebook_edit -
run_subagent budget + profile-deny enforcement never ran in production.

Every CHECKS key must either match a PreToolUse matcher in hooks.v1.json
or be a documented hot-path exclusion (per-call hook spawn cost outweighs
pure arg-shape checks the CLI itself already enforces).
"""
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "scripts"))

import importlib.util
spec = importlib.util.spec_from_file_location(
    "vta", os.path.join(ROOT, "scripts", "validate-tool-args.py"))
vta = importlib.util.module_from_spec(spec)
spec.loader.exec_module(vta)

# Hot read-path tools: a per-call hook spawn costs ~100ms+ on every
# read/grep/glob while the gate only adds arg-shape checks the CLI already
# enforces itself. Excluding them is deliberate - do not "fix" the test by
# adding them to a matcher without weighing the latency.
HOT_READ_PATH = {"read", "notebook_read", "grep", "glob", "find_file_by_name"}


def _pretool_matchers():
    cfg = json.load(open(os.path.join(ROOT, "hooks.v1.json"),
                         encoding="utf-8-sig"))
    return [g["matcher"] for g in cfg["PreToolUse"]]


def _matched_tools():
    covered = set()
    for m in _pretool_matchers():
        pattern = m.lstrip("^").rstrip("$")
        pattern = pattern.strip("()")
        for alt in pattern.split("|"):
            covered.add(alt)
    return covered


def test_every_checks_key_covered_or_excluded():
    covered = _matched_tools()
    missing = {k for k in vta.CHECKS if k not in covered and k not in HOT_READ_PATH}
    assert not missing, (
        f"validate-tool-args CHECKS keys with no PreToolUse matcher "
        f"(dead code in production): {sorted(missing)}")


def test_excluded_tools_are_hot_read_path_only():
    """No session-state tool may be silently excluded - run_subagent carries
    budget/profile enforcement that only exists on the hook path."""
    covered = _matched_tools()
    excluded = {k for k in vta.CHECKS if k not in covered}
    assert excluded == HOT_READ_PATH, (
        f"exclusion set drifted: {sorted(excluded ^ HOT_READ_PATH)}")


def test_run_subagent_fires_validator():
    """The budget/profile-deny path must actually dispatch on run_subagent."""
    assert any("run_subagent" in m for m in _pretool_matchers()), \
        "run_subagent missing from all PreToolUse matchers"


def test_pretool_matchers_compile_and_match():
    """A malformed matcher regex silently unfires every hook on the event -
    same dead-wire class as a missing matcher."""
    for m in _pretool_matchers():
        pattern = re.compile(m)
        for tool in m.lstrip("^").rstrip("$").strip("()").split("|"):
            assert pattern.fullmatch(tool), \
                f"matcher {m!r} does not match its own tool {tool!r}"


def test_hook_commands_resolve_to_real_scripts():
    """A typo'd command with fail_closed blocks every call at runtime -
    catch it at test time instead."""
    cfg = json.load(open(os.path.join(ROOT, "hooks.v1.json"),
                         encoding="utf-8-sig"))
    missing = []
    for event, groups in cfg.items():
        for g in groups:
            for h in g.get("hooks", []):
                cmd = h.get("command", "")
                m = re.match(r"^python (scripts/\S+\.py)$", cmd)
                if m and not os.path.isfile(os.path.join(ROOT, m.group(1))):
                    missing.append((event, cmd))
    assert not missing, f"hook commands point at missing scripts: {missing}"


def _runner_inner_scripts():
    """Scripts hosted inside _hookrun consolidated runners."""
    import glob as g
    inner = set()
    for runner in g.glob(os.path.join(ROOT, "scripts", "*.py")):
        src = open(runner, encoding="utf-8", errors="replace").read()
        if "_hookrun.main" not in src:
            continue
        for m in re.finditer(r"_hookrun\.main\(\[([^\]]*)\]", src):
            inner.update(re.findall(r"'([^']+\.py)'", m.group(1)))
    return inner


def test_runner_scripts_no_dead_stderr():
    """C80: _hookrun drops child stderr (the CLI treats hook stderr as a
    failure under fail_closed). An inner script that prints user-facing
    text to stderr without also emitting additionalContext is a dead
    channel - the advisory reaches nobody in production."""
    # memory-stop is listed in stop-guard but self-gates to SessionEnd; its
    # only live path is the direct SessionEnd entry where stderr reaches the
    # CLI - a designed channel, not a dead one.
    DIRECT_EVENT = {"memory-stop.py"}
    dead = []
    for name in _runner_inner_scripts():
        if name in DIRECT_EVENT:
            continue
        path = os.path.join(ROOT, "scripts", name)
        if not os.path.isfile(path):
            continue
        src = open(path, encoding="utf-8", errors="replace").read()
        if "file=sys.stderr" in src and "additionalContext" not in src:
            dead.append(name)
    assert not dead, (
        f"runner-hosted scripts print to stderr but never emit "
        f"additionalContext (advisories dropped by _hookrun): {dead}")


def test_hook_specific_output_carries_event_name():
    """C84: the CLI fails to parse hookSpecificOutput lacking hookEventName -
    the whole hook call then 'fails' and fail_closed blocks the tool call
    with an opaque error (observed 2026-11-24). Every emission site must
    include hookEventName."""
    import glob as g
    bad = []
    for p in g.glob(os.path.join(ROOT, "scripts", "*.py")):
        if os.path.basename(p) == "_hookrun.py":
            continue  # the merger synthesizes hookEventName when absent
        src = open(p, encoding="utf-8", errors="replace").read()
        for m in re.finditer(r'["\']hookSpecificOutput["\']', src):
            seg = src[m.start():m.start() + 400]
            stmt_end = seg.find("))")
            stmt = seg[:stmt_end + 2] if stmt_end >= 0 else seg
            if ("hookEventName" not in stmt
                    and ("dumps(" in stmt or "print(" in stmt)):
                ln = src[:m.start()].count("\n") + 1
                bad.append((os.path.basename(p), ln))
    assert not bad, (
        f"hookSpecificOutput emissions missing hookEventName (CLI rejects "
        f"the hook output, blocking the call): {bad}")
