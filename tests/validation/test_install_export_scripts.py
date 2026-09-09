import os
import re
import subprocess
import sys

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


def test_bash_scripts_pass_syntax_check():
    """If bash is available, validate syntax of install.sh and export.sh."""
    for name in ['install.sh', 'export.sh']:
        path = os.path.join(REPO_ROOT, name)
        # Use forward slashes for bash on Windows/WSL
        unix_path = path.replace('\\', '/')
        # If on Windows with WSL/Cygwin bash, try to convert to a Unix path
        if sys.platform == 'win32' and ':' in unix_path:
            # e.g. D:/path -> /mnt/d/path or /cygdrive/d/path
            drive, rest = unix_path.split(':', 1)
            wsl_path = f"/mnt/{drive.lower()}{rest}"
            unix_path = wsl_path
        try:
            result = subprocess.run(
                ['bash', '-n', unix_path],
                capture_output=True,
                text=True,
                timeout=10,
            )
        except (FileNotFoundError, subprocess.TimeoutExpired):
            # bash not available or timed out; skip syntax check on this platform
            continue
        assert result.returncode == 0, f"{name} has bash syntax errors: {result.stderr}"
