"""Edge-audit regressions for export.sh (issues 03, 04, 06, 07, 09, 11, 20, 36).

Functional tests run the real script under GNU bash with DEVIN_HOME
redirected at a synthetic live config; the script exports into the temp
bundle dir it lives in.
"""

import json
import os
import shutil
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


def make_export_fixture(tmp_path):
    """Bundle dir (export target) + fake live DEVIN_HOME with secrets."""
    bundle = tmp_path / 'bundle'
    bundle.mkdir()
    shutil.copy(os.path.join(REPO_ROOT, 'export.sh'), bundle / 'export.sh')
    live = tmp_path / 'live'
    (live / 'skills' / 'demo' / '__pycache__').mkdir(parents=True)
    (live / 'AGENTS.md').write_text('# agents\n', encoding='utf-8')
    (live / 'config.json').write_text(json.dumps({
        'org_id': 'real-org-id',
        'api_token': 'secret123',
        'devin': {'org_id': 'real-devin-org'},
        'hooks': {'PreToolUse': [{'command': 'x'}]},
    }), encoding='utf-8')
    (live / 'mcp_config.json').write_text(json.dumps({
        'mcpServers': {'srv': {'env': {'CUSTOM_NAME': 'envsecret'}}},
    }), encoding='utf-8')
    (live / 'credentials.toml').write_text(
        'devin_api_key = "livekey"\n', encoding='utf-8')
    (live / 'skills' / 'demo' / 'SKILL.md').write_text('x\n', encoding='utf-8')
    (live / 'skills' / 'demo' / '__pycache__' / 'a.pyc').write_bytes(b'\x00')
    return bundle, live


def run_export(bundle, live, *args):
    env = dict(os.environ, DEVIN_HOME=str(live))
    return subprocess.run(
        [BASH, 'export.sh'] + list(args),
        cwd=str(bundle), env=env,
        capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=120)


# --- static assertions ---


def test_sha256_tool_fallbacks():
    """Issue 03: no hasher must hard-fail, not compare empty strings."""
    c = read_script('export.sh')
    assert 'SHA256_CMD' in c
    assert 'shasum -a 256' in c
    assert 'openssl dgst -sha256' in c
    assert 'no sha256 tool found' in c


def test_strip_bom_portable():
    """Issue 04: GNU-only sed -i breaks on macOS BSD sed."""
    c = read_script('export.sh')
    assert "sed -i '1s/" not in c
    assert 'tail -c +4' in c


def test_shared_mask_routine():
    """Issues 06/36: one masking routine, broadened key vocabulary."""
    c = read_script('export.sh')
    assert 'mask_json_file' in c
    assert c.count('mask_json_file "$') == 2  # config.json + mcp_config.json
    for pat in ('token', 'secret', 'api[_-]?key', 'bearer', 'credential',
                'pat', 'session', 'cookie', 'jwt', 'dsn',
                'connection_string', 'org_id', 'user_id', 'email'):
        assert pat in c, pat


def test_env_blocks_fully_masked():
    """Issue 36: env dict values are masked wholesale, not by key name."""
    c = read_script('export.sh')
    assert "key == 'env'" in c


def test_fail_closed_without_python():
    """Issue 07: masked export aborts instead of copying secrets raw."""
    c = read_script('export.sh')
    assert 'require_python_for_masking' in c
    assert 'refusing to export unmasked' in c
    assert 'without masking' not in c


def test_no_pycompile_side_effects():
    """Issue 09: syntax validation must not write __pycache__."""
    c = read_script('export.sh')
    assert 'py_compile' not in c
    assert 'ast.parse' in c


def test_single_python_resolution():
    """Issue 11: one interpreter for masking, audit, and pytest."""
    c = read_script('export.sh')
    assert 'PY="python3"' in c
    assert 'python() {' in c
    # audit/pytest keep their literal command names but route through the
    # resolved interpreter via the python() function
    assert 'cd "$BUNDLE_DIR" && python audit.py' in c
    assert 'cd "$BUNDLE_DIR" && python -m pytest' in c


def test_pycache_excluded_from_export():
    """Issue 20 (sh): skill exports must not ship __pycache__."""
    c = read_script('export.sh')
    assert 'copy_tree_clean' in c


@requires_bash
def test_bash_syntax():
    r = subprocess.run([BASH, '-n', os.path.join(REPO_ROOT, 'export.sh')],
                       capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=10)
    assert r.returncode == 0, r.stderr


# --- functional tests ---


@requires_bash
def test_masked_export_hides_all_secret_kinds(tmp_path):
    """Issues 06/36: org_id, custom token keys, and env values all masked."""
    bundle, live = make_export_fixture(tmp_path)
    r = run_export(bundle, live)
    assert r.returncode == 0, r.stderr
    cfg = json.loads((bundle / 'config.json').read_text(encoding='utf-8-sig'))
    assert cfg['org_id'] == 'MASKED'
    assert cfg['api_token'] == 'MASKED'
    assert cfg['devin']['org_id'] == 'MASKED'
    assert cfg['hooks'] == {}
    raw = (bundle / 'config.json').read_text()
    assert 'secret123' not in raw
    mcp = json.loads((bundle / 'mcp_config.json').read_text(encoding='utf-8-sig'))
    assert mcp['mcpServers']['srv']['env']['CUSTOM_NAME'] == 'MASKED'
    creds = (bundle / 'credentials.toml').read_text()
    assert 'livekey' not in creds
    assert 'MASKED' in creds


@requires_bash
def test_pycache_not_exported(tmp_path):
    """Issue 20: __pycache__ in live skills must not reach the bundle."""
    bundle, live = make_export_fixture(tmp_path)
    r = run_export(bundle, live)
    assert r.returncode == 0, r.stderr
    assert not (bundle / 'skills' / 'demo' / '__pycache__').exists()


@requires_bash
def test_masked_export_without_python_fails(tmp_path):
    """Issue 07: with no python on PATH the masked path must abort, not
    copy secrets unmasked."""
    if sys.platform == 'win32':
        pytest.skip('PATH-stripping trick is POSIX-only')
    bundle, live = make_export_fixture(tmp_path)
    # Minimal PATH with coreutils but no python: reuse real dirs minus
    # python by shadowing -- simpler: create dir of symlinks is heavy, so
    # run with PATH that excludes python install dirs via `env -i`.
    env = {'PATH': '/usr/bin:/bin', 'HOME': os.environ.get('HOME', '/tmp'),
           'DEVIN_HOME': str(live)}
    if shutil.which('python3') is None and shutil.which('python') is None:
        pytest.skip('no python to remove')
    # If a python interpreter exists inside the minimal PATH itself the
    # strip cannot hide it (CI runners ship /usr/bin/python3).
    if any(os.path.exists(os.path.join(d, c))
           for d in ('/usr/bin', '/bin') for c in ('python3', 'python')):
        pytest.skip('python lives in the minimal PATH')
    r = subprocess.run([BASH, 'export.sh'], cwd=str(bundle), env=env,
                       capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=120)
    assert r.returncode != 0
    assert 'refusing to export unmasked' in r.stdout + r.stderr
    assert not (bundle / 'config.json').exists() or \
        'real-org-id' not in (bundle / 'config.json').read_text()
