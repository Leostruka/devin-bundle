"""Issue 37: sh/ps1 parity smoke test.

install.sh/install.ps1 and export.sh/export.ps1 implement the same
contract in two languages; this checklist asserts the user-visible
semantics line up where they can be checked statically. Where the .sh
side diverges deliberately (documented in .devin/scratch/edge-audit),
the ps1 behavior is the reference.
"""

import os
import re

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def read_script(name):
    with open(os.path.join(REPO_ROOT, name), encoding='utf-8-sig') as f:
        return f.read()


# --- install.sh vs install.ps1 ---


def test_flag_surface_parity():
    sh = read_script('install.sh')
    ps1 = read_script('install.ps1')
    pairs = [('--dry-run', 'DryRun'), ('--force', 'Force'),
             ('--backup', 'Backup'), ('--restore-secrets', 'RestoreSecrets')]
    for sh_flag, ps_flag in pairs:
        assert sh_flag in sh, sh_flag
        assert '$' + ps_flag in ps1, ps_flag


def test_credentials_optin_parity():
    """Both installers must gate unmasked credentials behind the secrets
    flag rather than copying silently."""
    sh = read_script('install.sh')
    ps1 = read_script('install.ps1')
    assert 'RestoreSecrets' in ps1
    assert 'RESTORE_SECRETS -eq 0' in sh


def test_masked_mcp_force_parity():
    """-Force / --force installs the masked mcp_config placeholders."""
    sh = read_script('install.sh')
    ps1 = read_script('install.ps1')
    assert 'MASKED placeholders' in sh
    assert re.search(r'Force.*masked|masked.*Force', ps1, re.I | re.S)


def test_config_merge_preserves_local_parity():
    """Both sides do a recursive merge where local keys win."""
    sh = read_script('install.sh')
    ps1 = read_script('install.ps1')
    assert "jq -s '.[0] * .[1]'" in sh
    assert 'Merge-Hashtables' in ps1


def test_hooks_render_parity():
    """Both render user hooks from hooks.v1.json via the shared renderer."""
    sh = read_script('install.sh')
    ps1 = read_script('install.ps1')
    assert 'render-user-hooks.py' in sh
    assert 'render-user-hooks.py' in ps1
    assert 'hooks.v1.json' in sh and 'hooks.v1.json' in ps1


def test_empty_extension_dir_parity():
    sh = read_script('install.sh')
    ps1 = read_script('install.ps1')
    assert 'is empty' in sh and 'is empty' in ps1


# --- export.sh vs export.ps1 ---


def test_export_flag_surface_parity():
    sh = read_script('export.sh')
    ps1 = read_script('export.ps1')
    for flag in ('DryRun', 'Commit', 'Push', 'NoMask'):
        assert '$' + flag in ps1, flag
    for flag in ('DRY_RUN', 'COMMIT', 'PUSH', 'NO_MASK'):
        assert flag + '=0' in sh, flag


def test_push_nomask_gate_parity():
    """Both exporters hard-block --push/--no-mask (would commit secrets)."""
    sh = read_script('export.sh')
    ps1 = read_script('export.ps1')
    assert 'FATAL' in sh
    assert 'NoMask' in ps1 and 'Push' in ps1


def test_masking_vocabulary_parity():
    """The .sh SECRET_KEY regex must cover the ps1 keyword set."""
    sh = read_script('export.sh')
    ps1 = read_script('export.ps1')
    m = re.search(r'(token\|secret\|key\|password\|passwd\|auth\|bearer'
                  r'\|credential\|private\|pat)', ps1)
    assert m, 'ps1 key-name mask regex not found'
    ps1_words = set(m.group(1).split('|'))
    for word in ps1_words:
        assert word in sh, f'ps1 mask keyword {word!r} missing in export.sh'


def test_hooks_not_exported_parity():
    """Exported config.json must carry empty hooks on both sides."""
    sh = read_script('export.sh')
    ps1 = read_script('export.ps1')
    assert 'hooks' in sh and 'strip_config_hooks' in sh
    assert 'hooks' in ps1


def test_prepush_validation_parity():
    """Both run audit.py + pytest inside the bundle before pushing."""
    sh = read_script('export.sh')
    ps1 = read_script('export.ps1')
    for name, c in (('sh', sh), ('ps1', ps1)):
        assert 'audit.py' in c, name
        assert 'pytest' in c, name


def test_bom_strip_parity():
    for name in ('install.sh', 'export.sh'):
        assert 'tail -c +4' in read_script(name)
