"""Reserved Windows device-name gate in validate-tool-args.py (C16).

Repro 2026-11-24: open('nul','w') silently discards data and
os.path.exists('nul') returns True on the device - the write tool would
report success while producing no file. Windows-only check (os.name).
"""
import json
import os
import subprocess
import sys

import pytest

HOOK = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                    'scripts', 'validate-tool-args.py')
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
EXISTING_DIR = os.path.dirname(os.path.abspath(__file__))


def run_hook(tool_name, file_path):
    if tool_name == 'notebook_edit':
        tool_input = {'notebook_path': file_path}
    else:
        tool_input = {'file_path': file_path}
        if tool_name == 'edit':
            tool_input.update({'old_string': 'a', 'new_string': 'b'})
    payload = json.dumps({'tool_name': tool_name,
                          'tool_input': tool_input,
                          'hook_event_name': 'PreToolUse'})
    return subprocess.run([sys.executable, HOOK], input=payload,
                          capture_output=True, text=True, encoding='utf-8',
                          errors='replace')


@pytest.mark.skipif(os.name != 'nt', reason='Windows device-name gate only fires on win32')
@pytest.mark.parametrize('name', ['nul', 'NUL', 'nul.txt', 'con', 'aux', 'prn',
                                  'com1', 'com9', 'lpt1', 'lpt9.py',
                                  # trailing space/dot normalize to the
                                  # device in Win32 - silent discard
                                  'nul ', 'nul.', 'nul..', 'nul .txt',
                                  'con.', 'con ', 'aux .py'])
def test_write_to_device_basename_blocked(name):
    r = run_hook('write', os.path.join(EXISTING_DIR, name))
    assert r.returncode == 2, f'{name} should be blocked'


@pytest.mark.skipif(os.name != 'nt', reason='Windows device-name gate only fires on win32')
def test_edit_and_notebook_blocked():
    assert run_hook('edit', os.path.join(EXISTING_DIR, 'aux.py')).returncode == 2
    assert run_hook('notebook_edit', os.path.join(EXISTING_DIR, 'nul.ipynb')).returncode == 2


@pytest.mark.skipif(os.name != 'nt', reason='ADS only exists on NTFS/win32')
@pytest.mark.parametrize('name', ['f.txt:hidden', 'note:draft.txt', 'a:b',
                                  'f.txt:ads:with:colons'])
def test_ads_colon_basename_blocked(name):
    # ':' in the basename is an NTFS stream separator - content diverts to a
    # hidden stream while the named file stays 0 bytes (repro 2026-11-24).
    r = run_hook('write', os.path.join(EXISTING_DIR, name))
    assert r.returncode == 2, f'{name} should be blocked (alternate stream)'


@pytest.mark.skipif(os.name != 'nt', reason='Win32 trailing-dot/space strip is win32-only')
@pytest.mark.parametrize('name', ['file.', 'file ', 'file..', 'x.py ',
                                  'x.py.'])
def test_trailing_dot_space_blocked(name):
    # 'file.' and 'file ' silently resolve to 'file' - multiple "different"
    # names collapse onto one path (repro 2026-11-24).
    r = run_hook('write', os.path.join(EXISTING_DIR, name))
    assert r.returncode == 2, f'{name} should be blocked (trailing dot/space)'


@pytest.mark.parametrize('name', ['normal.py', 'null.py', 'console.txt',
                                  'conftest.py', 'compile.py', 'lpt10.py',
                                  'com10.py', 'annul.py', 'icon.py',
                                  '.gitignore', 'x.y.z'])
def test_legit_names_allowed(name):
    r = run_hook('write', os.path.join(EXISTING_DIR, name))
    assert r.returncode != 2, f'{name} must not be reserved-blocked'


def test_read_of_device_name_not_blocked_by_reserved_check():
    # Reading nul is legitimate (device read); reserved check only guards
    # write-side tools. read only requires absolute path.
    r = run_hook('read', os.path.join(EXISTING_DIR, 'nul'))
    assert r.returncode != 2 or 'reserved' not in r.stderr.lower()


# Integration: production path reaches the check via the consolidated
# pre-write-guard runner (_hookrun chain), not a direct script call.
PRE_WRITE_GUARD = os.path.join(ROOT, 'scripts', 'pre-write-guard.py')


@pytest.mark.skipif(os.name != 'nt', reason='Windows device-name gate only fires on win32')
@pytest.mark.parametrize('name,blocked', [('nul', True), ('con.py', True),
                                          ('ok.py', False)])
def test_fires_through_pre_write_guard(name, blocked):
    payload = json.dumps({'tool_name': 'write',
                          'tool_input': {'file_path': os.path.join(EXISTING_DIR, name)},
                          'hook_event_name': 'PreToolUse'})
    r = subprocess.run([sys.executable, PRE_WRITE_GUARD], input=payload,
                       capture_output=True, text=True, encoding='utf-8',
                       errors='replace')
    assert (r.returncode == 2) == blocked
