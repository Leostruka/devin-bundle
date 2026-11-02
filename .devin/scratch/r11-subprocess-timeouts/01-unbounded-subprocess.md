# R11-01: three unbounded subprocess.run calls

**Severity:** P3 (hang risk)
**Files:**
- extensions/computer-use/probes/probe_spawnpty.py:82 — powershell CIM
  query in a shipped diagnostic probe; if it hangs the probe hangs.
- extensions/media-tools/tests/test_cli.py:11 — runs the CLI under
  test with no bound; a hang burns until pytest/CI kills it.
- extensions/media-tools/tests/test_export.py:50 — same pattern.

Same class as R9-03 (blender POSIX ps). All sibling calls in the
bundle use timeout=.

**Fix:** timeout=15 (probe) / timeout=60 (tests).

## Answer

timeout=15 (probe) / timeout=60 (tests). Tests still pass.
