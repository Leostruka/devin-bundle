"""Held-out completeness check for the envelope-v2 contract.

The agent-authored guard (tests/test_envelope_contract_v2.py) probes
only files listed in its PROBES table - a stamped emitter that never
got a probe row is a silent gap. This test re-derives the covered set
from the source tree: every file carrying a stamp marker AND a
`__main__` CLI surface must appear in PROBES or in an explicit
exclusion list with a reason.

Library files (marker, no __main__) are covered transitively through
the CLIs that call them - they are reported, not failed.
"""
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__))))

MARKER = re.compile(
    r"_BUNDLE_VERSION"  # covers both _BUNDLE_VERSION and _BUNDLE_VERSION_CACHE
    r"|from\s+\w*_envelope\s+import"
    r"|from\s+bundle_envelope\s+import"
    r"|import\s+st_common\b"
    r"|from\s+st_common\s+import")

# Emission styles that mean "emits JSON to stdout" - files with these
# and NO stamp marker are invisible to the marker scan, so they are
# collected separately and must be explicitly accounted for.
EMIT = re.compile(
    r"sys\.stdout\.buffer\.write"
    r"|sys\.stdout\.write\s*\(\s*json"
    r"|json\.dump\s*\([^,]+,\s*sys\.stdout"
    r"|print\s*\(\s*json\.dumps"
    r"|print\s*\(\s*_dumps"
    r"|print\s*\(\s*f?[\"']\{[\"']"  # print('{"key"' JSON literal
    r"|print\s*\(\s*f?[\"']\{\{"     # print(f'{{"key"' f-literal
)

SCAN_DIRS = ("extensions", "scripts", "skills")

# Marker-free JSON emitters intentionally outside the contract.
UNSTAMPED = {
    # hook-protocol payloads consumed by the Devin hook runtime, not
    # parsed as tool output (hookSpecificOutput / gate decisions)
    "scripts/architecture-gate.py", "scripts/behavioral-nudge.py",
    "scripts/check-ai-signature.py", "scripts/check-push-green.py",
    "scripts/compact-gate.py", "scripts/constraint-pinning.py",
    "scripts/destructive-gate.py",
    "scripts/design-lint-gate.py", "scripts/dep-audit-gate.py",
    "scripts/file-size-guard.py", "scripts/gh-pr-assignee.py",
    "scripts/git-diff-stat.py", "scripts/laya-guard.py",
    "scripts/memory-post-edit.py", "scripts/memory-post-exec.py",
    "scripts/memory-retrieval.py",
    "scripts/no-em-dash.py", "scripts/permission-gate.py",
    "scripts/refine-review-prompt.py", "scripts/rl-resume-detect.py",
    "scripts/silent-error-review.py", "scripts/skill-picker.py",
    "scripts/stuck-detect.py",
    "scripts/token-saver.py", "scripts/validate-mermaid.py",
    "scripts/validate-tool-args.py",
    "scripts/_hookrun.py",
    # config-document / transport / benchmark surfaces
    "scripts/render-user-hooks.py",
    "extensions/computer-use/mcp_server.py",
    "extensions/system-control/sc_cli.py",
    "extensions/system-control/sc_bench.py",
    "extensions/busybar/listen.py",            # daemon listener
    "skills/memory-management/scripts/query-memory.py",   # bare array
    "skills/project-memory/scripts/query-memory.py",      # bare array
    "extensions/computer-use/integration/fixtures/cu_input_probe.py",
    "scripts/status_vocab.py",  # __main__ vocab dump - config doc
}

SKIP_DIRS = {".venv", "__pycache__", "node_modules", ".git", "scratch"}

# Marker-carrying CLI files deliberately outside PROBES. Shared
# *_envelope.py helpers and st_common.py are already skipped by the
# scan (no need to list them).
EXCLUDE = {
    # protocol surface documented in CLI-CONTRACT.md: worker pipe
    # transport is raw JSON-lines; inner payloads self-stamp
    "extensions/computer-use/cu_session.py",
    # network bootstrap - every path fetches, no offline argv
    "extensions/media-tools/jxl_bootstrap.py",
    # interactive OAuth flow - browser + callback server, no offline argv
    "extensions/gcal/oauth_setup.py",
    # spawns a real node server process on every success path
    "skills/grilling/scripts/start-server.py",
    # dedicated probe that cannot ride the shared runner (stdin+tmpdir)
    "skills/context-hygiene/scripts/fold_store.py",
}


def _probes():
    sys.path.insert(0, os.path.join(ROOT, "tests"))
    from test_envelope_contract_v2 import PROBES
    return {rel for rel, _argv, _w in PROBES}


def _scan():
    stamped, libs, unmarked = [], [], []
    for top in SCAN_DIRS:
        for dirpath, dirs, files in os.walk(os.path.join(ROOT, top)):
            dirs[:] = [d for d in dirs if d not in SKIP_DIRS]
            for f in files:
                if not f.endswith(".py"):
                    continue
                rel = os.path.relpath(os.path.join(dirpath, f),
                                      ROOT).replace(os.sep, "/")
                try:
                    src = open(os.path.join(dirpath, f),
                               encoding="utf-8", errors="replace").read()
                except OSError:
                    continue
                if MARKER.search(src):
                    if f.endswith("_envelope.py") or f == "st_common.py":
                        continue
                    if "__main__" in src:
                        stamped.append(rel)
                    else:
                        libs.append(rel)
                elif EMIT.search(src):
                    unmarked.append(rel)
    return sorted(stamped), sorted(libs), sorted(unmarked)


def test_every_stamped_cli_is_probe_covered():
    probed = _probes()
    stamped, _libs, _unmarked = _scan()
    uncovered = [r for r in stamped
                 if r not in probed and r not in EXCLUDE]
    assert not uncovered, (
        "stamped CLI emitters missing from PROBES - probe or exclude "
        "with reason:\n" + "\n".join(uncovered))


def test_no_unmarked_json_emitters():
    """Marker-free files that still write JSON to stdout must be in
    UNSTAMPED (documented exclusion) - otherwise the contract has an
    invisible emitter."""
    _stamped, _libs, unmarked = _scan()
    escaped = [r for r in unmarked if r not in UNSTAMPED]
    assert not escaped, (
        "JSON emitters without stamp marker or documented exclusion:\n"
        + "\n".join(escaped))


def test_exclusions_still_carry_marker():
    stamped, libs, _unmarked = _scan()
    seen = set(stamped) | set(libs)
    stale = sorted(e for e in EXCLUDE if e not in seen)
    assert not stale, ("EXCLUDE entries lost their marker or file - "
                       "drop them: " + ", ".join(stale))


def test_unstamped_list_still_emits():
    """UNSTAMPED entries whose emit pattern disappears are stale -
    drop them so the list stays honest."""
    _stamped, _libs, unmarked = _scan()
    stale = sorted(u for u in UNSTAMPED if u not in unmarked)
    assert not stale, ("UNSTAMPED entries no longer emit JSON - "
                       "drop them: " + ", ".join(stale))
