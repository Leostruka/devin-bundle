"""Edge-audit regressions for install.sh (issues 01-05, 12, 16, 18-20, 38, 40, 80).

Functional tests run the real script under Git Bash/GNU bash against a
synthetic bundle in a temp dir with DEVIN_HOME redirected, so nothing
touches the real user config.
"""

import json
import os
import shutil
import stat
import subprocess
import sys

import pytest

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def read_script(name):
    with open(os.path.join(REPO_ROOT, name), encoding='utf-8-sig') as f:
        return f.read()


def _find_bash():
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
                               text=True, encoding="utf-8", errors="replace", timeout=10)
        except (FileNotFoundError, subprocess.TimeoutExpired, OSError):
            continue
        if r.returncode == 0 and 'GNU bash' in r.stdout:
            return exe
    return None


BASH = _find_bash()
requires_bash = pytest.mark.skipif(BASH is None, reason='no GNU bash')


def make_bundle(tmp_path, masked_creds=True, masked_mcp=True):
    """Create a minimal bundle dir with install.sh copied in."""
    bundle = tmp_path / 'bundle'
    bundle.mkdir()
    shutil.copy(os.path.join(REPO_ROOT, 'install.sh'), bundle / 'install.sh')
    (bundle / 'AGENTS.md').write_text('# agents\n', encoding='utf-8')
    (bundle / 'config.json').write_text(
        json.dumps({'org_id': 'MASKED', 'hooks': {}, 'auto_update': True}),
        encoding='utf-8')
    skill = bundle / 'skills' / 'demo'
    (skill / 'scripts' / '__pycache__').mkdir(parents=True)
    (skill / 'SKILL.md').write_text('---\nname: demo\n---\n', encoding='utf-8')
    (skill / 'scripts' / 'tool.py').write_text('x = 1\n', encoding='utf-8')
    (skill / 'scripts' / '__pycache__' / 'tool.cpython-314.pyc').write_bytes(b'\x00')
    mcp_val = 'MASKED' if masked_mcp else 'real-token'
    (bundle / 'mcp_config.json').write_text(
        json.dumps({'mcpServers': {'s': {'env': {'TOKEN': mcp_val}}}}),
        encoding='utf-8')
    creds_val = 'MASKED' if masked_creds else 'real-key-123'
    (bundle / 'credentials.toml').write_text(
        'devin_api_key = "%s"\n' % creds_val, encoding='utf-8')
    return bundle


def run_install(bundle, home, *args):
    env = dict(os.environ, DEVIN_HOME=str(home))
    return subprocess.run(
        [BASH, 'install.sh'] + list(args),
        cwd=str(bundle), env=env,
        capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=120)


# --- static assertions (portable, always run) ---


def test_sha256_tool_fallbacks():
    """Issue 03: sha256sum missing on macOS must not silently no-op."""
    c = read_script('install.sh')
    assert 'SHA256_CMD' in c
    assert 'shasum -a 256' in c
    assert 'openssl dgst -sha256' in c
    assert 'no sha256 tool found' in c


def test_strip_bom_portable():
    """Issue 04: GNU-only `sed -i` syntax breaks under BSD sed."""
    c = read_script('install.sh')
    assert "sed -i '1s/" not in c
    assert 'tail -c +4' in c


def test_backup_handles_directories():
    """Issue 05: --backup on a directory must recurse."""
    c = read_script('install.sh')
    assert 'elif [[ -d "$file" ]]' in c
    assert 'cp -r "$file" "$backup"' in c


def test_config_merge_is_deep():
    """Issue 02/18: merge must be a recursive deep-merge, not sed surgery."""
    c = read_script('install.sh')
    assert "jq -s '.[0] * .[1]'" in c
    assert 'sed-based merge' not in c
    assert 'jq not found; skipping config.json merge' in c


def test_credentials_gated_and_restricted():
    """Issues 01/80: unmasked credentials need --restore-secrets and 0600."""
    c = read_script('install.sh')
    assert 'RESTORE_SECRETS -eq 0' in c
    assert 'use --restore-secrets to install' in c
    assert 'restrict_secret_mode' in c
    assert 'chmod 600' in c


def test_masked_mcp_force_install():
    """Issue 12: --force installs masked mcp_config placeholders (ps1 parity)."""
    c = read_script('install.sh')
    assert 'MASKED placeholders' in c


def test_usage_no_false_restore_promise():
    """Issue 19: usage must not promise automatic secret restoration."""
    c = read_script('install.sh')
    usage = c.split('EOF')[0]
    assert 'cannot be restored' in c
    assert 'Restore masked values in credentials.toml' not in usage


def test_hooks_render_windows_path():
    """Issue 16: Git Bash must pass a Windows-style home to the renderer."""
    c = read_script('install.sh')
    assert 'cygpath -w "$DEVIN_HOME")' in c
    assert 'render_home' in c


def test_pycache_excluded():
    """Issue 20 (sh): skill/doc copies must drop __pycache__/.pyc."""
    c = read_script('install.sh')
    assert 'copy_tree_clean' in c
    assert "-name '__pycache__'" in c
    assert "-name '*.pyc'" in c


def test_skip_receipt_and_summary():
    """Issue 40: degraded steps must be listed and persisted."""
    c = read_script('install.sh')
    assert 'record_skip' in c
    assert '.install-receipt.json' in c
    assert 'Skipped steps' in c


def test_cli_version_drift_notice():
    """Issue 38: runtime check against validated_cli_version."""
    c = read_script('install.sh')
    assert 'validated_cli_version' in c
    assert 'devin --version' in c


def test_single_python_resolution():
    """Issues 11/16-adjacent: one interpreter resolved once."""
    c = read_script('install.sh')
    assert 'PY="python3"' in c
    assert 'python() {' in c


@requires_bash
def test_bash_syntax():
    r = subprocess.run([BASH, '-n', os.path.join(REPO_ROOT, 'install.sh')],
                       capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=10)
    assert r.returncode == 0, r.stderr


# --- functional tests ---


@requires_bash
def test_unmasked_credentials_skipped_without_flag(tmp_path):
    """Issue 01: real credentials must not install without opt-in."""
    bundle = make_bundle(tmp_path, masked_creds=False)
    home = tmp_path / 'home'
    r = run_install(bundle, home)
    assert r.returncode == 0, r.stderr
    assert not (home / 'credentials.toml').exists()
    assert '--restore-secrets' in r.stdout


@requires_bash
def test_unmasked_credentials_install_with_flag_mode_600(tmp_path):
    """Issues 01/80: opt-in installs credentials with owner-only mode."""
    bundle = make_bundle(tmp_path, masked_creds=False)
    home = tmp_path / 'home'
    r = run_install(bundle, home, '--restore-secrets')
    assert r.returncode == 0, r.stderr
    creds = home / 'credentials.toml'
    assert creds.exists()
    assert 'real-key-123' in creds.read_text(encoding="utf-8")
    if sys.platform != 'win32':
        mode = stat.S_IMODE(os.stat(creds).st_mode)
        assert mode == 0o600, oct(mode)


@requires_bash
def test_masked_mcp_skipped_then_force_installed(tmp_path):
    """Issue 12: masked mcp_config skips by default, installs with --force."""
    bundle = make_bundle(tmp_path, masked_mcp=True)
    home = tmp_path / 'home'
    r = run_install(bundle, home)
    assert r.returncode == 0
    assert not (home / 'mcp_config.json').exists()
    r = run_install(bundle, home, '--force')
    assert r.returncode == 0
    assert (home / 'mcp_config.json').exists()
    assert 'MASKED' in (home / 'mcp_config.json').read_text(encoding="utf-8")


@requires_bash
def test_backup_directory_contains_files(tmp_path):
    """Issue 05: --backup of a skill dir copies contents, not an empty dir."""
    bundle = make_bundle(tmp_path)
    home = tmp_path / 'home'
    assert run_install(bundle, home).returncode == 0
    # Diverge the installed skill, then force+backup.
    (home / 'skills' / 'demo' / 'extra.txt').write_text('local', encoding="utf-8")
    r = run_install(bundle, home, '--force', '--backup')
    assert r.returncode == 0, r.stderr
    backups = list(home.glob('skills/demo.backup.*'))
    assert backups, 'no directory backup created'
    assert (backups[0] / 'SKILL.md').exists()


@requires_bash
def test_pycache_not_installed(tmp_path):
    """Issue 20: __pycache__ in bundle skills must not reach the target."""
    bundle = make_bundle(tmp_path)
    home = tmp_path / 'home'
    r = run_install(bundle, home)
    assert r.returncode == 0, r.stderr
    assert not (home / 'skills' / 'demo' / 'scripts' / '__pycache__').exists()


@requires_bash
def test_install_receipt_written(tmp_path):
    """Issue 40: a durable record of the install is written."""
    bundle = make_bundle(tmp_path)
    home = tmp_path / 'home'
    r = run_install(bundle, home)
    assert r.returncode == 0, r.stderr
    receipt = home / '.install-receipt.json'
    assert receipt.exists()
    data = json.loads(receipt.read_text(encoding="utf-8"))
    assert isinstance(data['skipped'], list)
    # masked creds + masked mcp must appear as recorded skips
    assert any('credentials.toml' in s for s in data['skipped'])


@requires_bash
def test_jq_deep_merge_preserves_local_keys(tmp_path):
    """Issue 02: local-only config keys survive the merge."""
    if shutil.which('jq') is None:
        pytest.skip('jq not installed')
    bundle = make_bundle(tmp_path)
    home = tmp_path / 'home'
    (home).mkdir(parents=True)
    (home / 'config.json').write_text(
        json.dumps({'org_id': 'real-org', 'theme': 'dark',
                    'devin': {'org_id': 'real-devin-org'}}),
        encoding='utf-8')
    r = run_install(bundle, home)
    assert r.returncode == 0, r.stderr
    merged = json.loads((home / 'config.json').read_text(encoding='utf-8-sig'))
    assert merged['theme'] == 'dark'
    assert merged['org_id'] == 'real-org'
    assert merged['devin']['org_id'] == 'real-devin-org'
    assert merged['auto_update'] is True
