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
    r"_BUNDLE_VERSION_CACHE"
    r"|from\s+\w*_envelope\s+import"
    r"|from\s+bundle_envelope\s+import"
    r"|import\s+st_common\b"
    r"|from\s+st_common\s+import")

SCAN_DIRS = ("extensions", "scripts", "skills")

# Marker-carrying CLI files deliberately outside PROBES. Shared
# *_envelope.py helpers and st_common.py are already skipped by the
# scan (no need to list them).
EXCLUDE = {
    # protocol surface documented in CLI-CONTRACT.md: worker pipe
    # transport is raw JSON-lines; inner payloads self-stamp
    "extensions/computer-use/cu_session.py",
    # network bootstrap - every path fetches, no offline argv
    "extensions/media-tools/jxl_bootstrap.py",
    # dedicated probe that cannot ride the shared runner (stdin+tmpdir)
    "skills/context-hygiene/scripts/fold_store.py",
}


def _probes():
    sys.path.insert(0, os.path.join(ROOT, "tests"))
    from test_envelope_contract_v2 import PROBES
    return {rel for rel, _argv, _w in PROBES}


def _scan():
    stamped, libs = [], []
    for top in SCAN_DIRS:
        for dirpath, _dirs, files in os.walk(os.path.join(ROOT, top)):
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
                if not MARKER.search(src):
                    continue
                if f.endswith("_envelope.py") or f == "st_common.py":
                    continue
                if "__main__" in src:
                    stamped.append(rel)
                else:
                    libs.append(rel)
    return sorted(stamped), sorted(libs)


def test_every_stamped_cli_is_probe_covered():
    probed = _probes()
    stamped, _libs = _scan()
    uncovered = [r for r in stamped
                 if r not in probed and r not in EXCLUDE]
    assert not uncovered, (
        "stamped CLI emitters missing from PROBES - probe or exclude "
        "with reason:\n" + "\n".join(uncovered))


def test_exclusions_still_carry_marker():
    stamped, libs = _scan()
    seen = set(stamped) | set(libs)
    stale = sorted(e for e in EXCLUDE if e not in seen)
    assert not stale, ("EXCLUDE entries lost their marker or file - "
                       "drop them: " + ", ".join(stale))
