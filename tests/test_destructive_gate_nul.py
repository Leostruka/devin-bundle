"""destructive-gate.py: gate 9 `> nul` artifact (bash has no NUL device).

Reproduced failure (2026-11-24): `echo test > nul` in Git Bash creates a
literal file named `nul`; a stray `nul` was caught by qa-ci in PR review.
cmd/powershell wrappers resolve `nul` to the real Windows null device.
"""
import json
import os
import subprocess
import sys

import pytest

HOOK = os.path.join(os.path.dirname(__file__), "..", "scripts",
                    "destructive-gate.py")
PY = sys.executable


def run_gate(cmd):
    payload = json.dumps({"hook_event_name": "PreToolUse",
                          "tool_name": "exec",
                          "tool_input": {"command": cmd}})
    return subprocess.run([PY, HOOK], input=payload, capture_output=True,
                          text=True, encoding="utf-8", errors="replace")


@pytest.mark.skipif(os.name != 'nt', reason='reserved-name ghost artifacts are a Windows-only hazard')
@pytest.mark.parametrize("cmd", [
    'echo x > nul',
    'echo x >> nul',
    'pytest -q > nul 2>&1',
    'ls /missing 2> nul',
    'cmd_out=$(foo) > NUL',
    'make build &> nul',
    'echo x > nul && git status',
])
def test_nul_redirect_blocked(cmd):
    assert run_gate(cmd).returncode == 2


# Bypass regression (all verified to create ghost artifacts in Git Bash
# on Windows 2026-11-24; the original regex only caught `> nul` spaced).
@pytest.mark.parametrize("cmd", [
    'echo x>nul',
    'echo x > "nul"',
    'echo x > ./nul',
    'echo x > NUL.TXT',
    'echo x > con',
    'echo x > com1',
    'echo x > lpt9',
    'echo x > aux',
    'echo x > prn',
    'echo x | tee nul',
    'echo x | tee -a con',
    'touch nul',
    'mkdir con',
    'cp config.ini nul',
    'mv tmp.txt aux',
    'ln -s target nul',
    'install x nul',
    'echo x > nul.',
    'echo x > "nul "',
    'touch con.',
    'mkdir aux.',
])
@pytest.mark.skipif(os.name != 'nt', reason='reserved-name ghost artifacts are a Windows-only hazard')
def test_reserved_artifact_blocked(cmd):
    assert run_gate(cmd).returncode == 2


@pytest.mark.skipif(os.name != 'nt', reason='ADS only exists on NTFS')
@pytest.mark.parametrize("cmd", [
    'echo x > f.txt:hidden',
    'echo x > f.txt:ads',
    'echo x > "f.txt:ads"',
    'echo x >> a:b',
    'echo x > C:\\tmp\\f:ads',
    'tee f.txt:hidden',
    'touch note:draft.txt',
    'cp src dst:ads',
    'mv a b:c',
    'install x f:s',
])
def test_ads_stream_target_blocked(cmd):
    assert run_gate(cmd).returncode == 2


@pytest.mark.skipif(os.name != 'nt', reason='ADS only exists on NTFS')
def test_ads_block_reason_includes_matched_text():
    """2026-11-26: two false-positive blocks could not be reproduced because
    the gate never revealed which substring matched. The reason now carries
    the first 80 chars of the match so FPs are self-diagnosing."""
    proc = run_gate('echo x > f.txt:hidden')
    assert proc.returncode == 2
    assert "Matched" in proc.stdout
    assert "f.txt:" in proc.stdout


@pytest.mark.skipif(os.name != 'nt', reason='ADS gate is Windows-only')
@pytest.mark.parametrize("cmd", [
    "echo x > 'C:\\dir\\file.txt'",
    'echo x > C:\\dir\\file.txt',
    'cp src C:\\dst\\out.txt',
    'echo x > file.txt',
    'echo x > /tmp/f',
])
def test_ads_legit_targets_allowed(cmd):
    assert run_gate(cmd).returncode == 0


# SECURITY REGRESSION (2026-11-26 adversarial review, verdict UNSAFE):
# a regex-based heredoc-body stripper was reverted after the reviewer
# verified 7 working bypasses with real artifact-creating probes. Heredoc
# stdin for interpreters is executable code (os.system etc), so bodies
# are scanned like the rest of the command. Cost: writing payloads whose
# string literals mention ADS/reserved names inside a heredoc is blocked
# (accepted FP; workaround: write the file with the write tool instead).
# These cases pin the fail-closed behavior; do NOT re-narrow without a
# real shell parser.
@pytest.mark.skipif(os.name != 'nt', reason='ADS gate is Windows-only')
@pytest.mark.parametrize("cmd", [
    # accepted-FP cases: inert-looking but unprovable without a real
    # shell parser - blocked by design (fail closed)
    "python - <<'PY'\nx = 'echo a > f.txt:hidden'\nPY",
    "python3 - <<'EOF'\ns = 'touch con'\nEOF",
    "node <<'JS'\nvar s = 'echo x > f.txt:ads'\nJS",
    # bypass vectors verified against the reverted narrowing - every one
    # must stay blocked forever
    "# <<true\necho x > nul\ntrue",
    ": '<<true'\necho x > f.txt:hidden\ntrue",
    "python - <<'true-x'\nprint(1)\ntrue-x\necho x > nul\ntrue",
    "python <<A <<B\nprint('x')\nA\n# <<true\nB\necho x > nul\ntrue",
    's=/bin/s; t=h; s=$s$t\n"$s" <<\'EOF\'\necho x > nul\nEOF',
    "cmd <<'EOF'\necho x > f.txt:hidden\nexit\nEOF",
    "echo '<\\<true'\necho x > n\\ul\ntrue",
    "python - <<'PY'\nimport os\nos.system('echo x > f.txt:hidden')\nPY",
    # shell recipient bodies execute - always scanned
    "sh <<'EOF'\necho x > f.txt:hidden\nEOF",
    "bash <<EOF\necho x > nul\nEOF",
    "cat <<EOF | sh\necho x > f.txt:hidden\nEOF",
    # redirect in the command portion (not the body) always scans
    "cat > f.txt:hidden <<EOF\nx\nEOF",
    # unclosed heredoc fails safe: body kept in scan
    "python <<'PY'\necho x > f.txt:hidden",
])
def test_heredoc_bodies_scanned_fail_closed(cmd):
    assert run_gate(cmd).returncode == 2


@pytest.mark.skipif(os.name != 'nt', reason='ADS gate is Windows-only')
@pytest.mark.parametrize("cmd", [
    # control: a heredoc with no artifact patterns must not block
    "python - <<'PY'\nprint('hello')\nPY",
    # 'x > nul' is single-quoted even to a real shell - no redirect exists
    # in any interpretation, so this must pass
    "python <<'PY'\nprint('x > nul')\nPY",
])
def test_plain_python_heredoc_passes(cmd):
    assert run_gate(cmd).returncode == 0


@pytest.mark.parametrize("cmd", [
    'cmd /c "echo x > nul"',
    'cmd //c "echo x > nul"',
    'cmd.exe /c "foo > NUL 2>&1"',
    'powershell -NoProfile -Command "x > $null"',
    'pwsh -c "x > nul"',
    'powershell.exe -c "x > con"',
    'echo x > /dev/null',
    'echo x > null',
    'echo x > annul.txt',
    'cat > nul_file.log',
    'echo "null is fine"',
    'grep null log.txt > results.txt',
    'echo x > console.txt',
    'mkdir conf',
    'cp src dst',
    'touch config.py',
    'tee output.log',
    'grep con file.txt',
    'cat nul.txt',
    'echo x > icon.py',
])
def test_nul_redirect_allowed(cmd):
    assert run_gate(cmd).returncode == 0
