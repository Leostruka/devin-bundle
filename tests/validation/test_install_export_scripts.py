import os
import re
import subprocess
import sys

import pytest

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def read_script(name):
    path = os.path.join(REPO_ROOT, name)
    with open(path, encoding='utf-8-sig') as f:
        return f.read()


def test_export_ps1_has_security_gate():
    content = read_script('export.ps1')
    assert '[switch]$NoMask' in content
    assert '[switch]$Push' in content
    assert 'if ($Push -and $NoMask -and -not $DryRun)' in content
    assert 'aborting commit/push' in content.lower()


def test_export_ps1_runs_audit_and_pytest_on_push():
    content = read_script('export.ps1')
    assert 'audit.py' in content
    assert 'pytest -q' in content
    assert 'python' in content


def test_export_sh_has_security_gate():
    content = read_script('export.sh')
    assert 'NO_MASK=0' in content
    assert 'PUSH=0' in content
    assert 'if [[ $PUSH -eq 1 && $NO_MASK -eq 1 && $DRY_RUN -eq 0 ]]' in content
    assert 'FATAL' in content


def test_export_sh_runs_audit_and_pytest_on_push():
    content = read_script('export.sh')
    assert 'audit.py' in content
    assert 'pytest -q' in content


def test_install_ps1_has_expected_parameters():
    content = read_script('install.ps1')
    assert '[switch]$DryRun' in content
    assert '[switch]$Force' in content
    assert '[switch]$Backup' in content
    assert '[switch]$RestoreSecrets' in content
    assert '{{APPDATA}}' in content


def test_install_sh_has_expected_parameters():
    content = read_script('install.sh')
    assert '--dry-run' in content
    assert '--force' in content
    assert '--backup' in content
    assert '--restore-secrets' in content
    assert '{{APPDATA}}' in content
    assert content.startswith('#!')


def test_install_sh_skips_empty_extension_dirs():
    content = read_script('install.sh')
    assert 'mindepth 1 -type f -print -quit' in content
    assert 'is empty' in content


def test_export_ps1_has_expected_parameters():
    content = read_script('export.ps1')
    assert '[switch]$DryRun' in content
    assert '[switch]$Commit' in content
    assert '[switch]$Push' in content
    assert '[switch]$NoMask' in content
    assert 'normalize_config_paths' in content or '{{APPDATA}}' in content


def test_export_sh_has_expected_parameters():
    content = read_script('export.sh')
    assert 'DRY_RUN=0' in content
    assert 'COMMIT=0' in content
    assert 'PUSH=0' in content
    assert 'NO_MASK=0' in content
    assert 'normalize_config_paths' in content
    assert content.startswith('#!')


def _find_bash():
    """Locate a real GNU bash: (exe, path_style) or (None, None).

    On Windows CI runners, PATH 'bash' is the WSL stub in System32 (no
    distro → fails with UTF-16 error output). Prefer Git for Windows
    bash; accept PATH bash only if it answers --version like GNU bash.
    """
    candidates = []
    if sys.platform == 'win32':
        for env in ('PROGRAMFILES', 'PROGRAMFILES(X86)'):
            root = os.environ.get(env)
            if root:
                candidates.append(os.path.join(root, 'Git', 'bin', 'bash.exe'))
    candidates.append('bash')
    for exe in candidates:
        try:
            r = subprocess.run([exe, '--version'], capture_output=True,
                               text=True, timeout=10)
        except (FileNotFoundError, subprocess.TimeoutExpired, OSError):
            continue
        if r.returncode == 0 and 'GNU bash' in r.stdout:
            return exe, sys.platform == 'win32' and exe == 'bash'
    return None, False


def test_bash_scripts_pass_syntax_check():
    """If bash is available, validate syntax of install.sh and export.sh."""
    bash, needs_mount = _find_bash()
    if bash is None:
        pytest.skip('no GNU bash on this platform')
    for name in ['install.sh', 'export.sh']:
        path = os.path.join(REPO_ROOT, name)
        unix_path = path.replace('\\', '/')
        # Git bash accepts D:/path directly; a real WSL bash needs /mnt/d/path
        if needs_mount and ':' in unix_path:
            drive, rest = unix_path.split(':', 1)
            unix_path = f"/mnt/{drive.lower()}{rest}"
        result = subprocess.run(
            [bash, '-n', unix_path],
            capture_output=True,
            text=True,
            timeout=10,
        )
        assert result.returncode == 0, f"{name} has bash syntax errors: {result.stderr}"


# --- R7 export-hardening regressions ---


def test_export_sh_audit_and_pytest_run_inside_bundle_dir():
    """audit.py is cwd-dependent (walks '.', reads manifest.json) -- the
    pre-push gate must cd into BUNDLE_DIR or it audits the caller's tree."""
    content = read_script('export.sh')
    assert 'cd "$BUNDLE_DIR" && python audit.py' in content
    assert 'cd "$BUNDLE_DIR" && python -m pytest' in content


def test_export_ps1_audit_and_pytest_run_inside_bundle_dir():
    content = read_script('export.ps1')
    audit_idx = content.find('python audit.py')
    push_idx = content.rfind('Push-Location $bundleRoot', 0, audit_idx)
    assert audit_idx != -1 and push_idx != -1, (
        'audit.py must run under Push-Location $bundleRoot')


def test_export_sh_commit_stages_only_export_paths():
    """git add -A sweeps unrelated dirty files into the export commit."""
    content = read_script('export.sh')
    assert 'git add -A' not in content
    assert 'git add -- AGENTS.md' in content


def test_export_ps1_commit_stages_only_export_paths():
    content = read_script('export.ps1')
    assert 'git add -A' not in content
    assert '$exportPaths' in content
    assert 'git add -- $exportPaths' in content


def test_export_sh_mcp_mask_matches_key_names():
    """Value-only masking leaks secrets under custom keys (GITHUB_PAT,
    Authorization). The mask must also inspect key names."""
    content = read_script('export.sh')
    assert 'SECRET_KEY' in content
    for pat in ('token', 'secret', 'api[_-]?key', 'bearer', 'credential', 'pat'):
        assert pat in content


def test_export_ps1_mcp_mask_matches_key_names():
    content = read_script('export.ps1')
    assert 'token|secret|key|password|passwd|auth|bearer|credential|private|pat' in content


def test_export_sh_python_blocks_use_argv_paths():
    """Interpolating '$var' paths into python -c source mangles quotes and
    backslashes; paths must arrive via sys.argv."""
    content = read_script('export.sh')
    assert "'$config_src'" not in content
    assert "'$mcp_src'" not in content
    assert "'$mcp_dst'" not in content
    assert 'sys.argv[1]' in content


def test_export_sh_toml_mask_drops_multiline_continuations():
    """sed 's/=.*/MASKED/' leaks multiline TOML values (lines inside
    `key = [ ... ]` have no `=`). Masking must track the opener."""
    content = read_script('export.sh')
    assert "sed 's/=.*/" not in content
    assert 'skip_until' in content
    assert 'report_stale' in content


def test_export_ps1_toml_mask_drops_multiline_continuations():
    content = read_script('export.ps1')
    assert '$skipUntil' in content


def test_export_stale_entry_reporting():
    assert 'report_stale' in read_script('export.sh')
    assert 'Report-Stale' in read_script('export.ps1')


# --- R8 install-target regressions ---


def test_install_sh_resolves_appdata_on_windows():
    """Git Bash on Windows must target %APPDATA%\\devin -- the CLI does
    not read ~/.config/devin there (shadow dir bug)."""
    content = read_script('install.sh')
    assert 'MINGW*|MSYS*|CYGWIN*' in content
    assert 'cygpath' in content
    assert '${APPDATA:-}' in content


def test_install_ps1_skips_empty_extension_dirs():
    """Parity with the install.sh R6 guard."""
    content = read_script('install.ps1')
    assert 'is empty' in content
    assert '-Recurse -File' in content


def test_audit_prefers_appdata_on_windows():
    """On os.name == 'nt' the CLI reads %APPDATA%/devin; auditing the
    .config shadow instead masks real drift."""
    content = read_script('audit.py')
    assert "os.name == 'nt'" in content
    assert 'shadow config dir' in content
