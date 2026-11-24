"""Tests for scripts/hook-drift.py (SessionStart advisory check)."""
import importlib.util
import io
import json
import os
import sys

import pytest

SCRIPT = os.path.join(os.path.dirname(__file__), os.pardir,
                      'scripts', 'hook-drift.py')


def _load(live_scripts):
    spec = importlib.util.spec_from_file_location('hook_drift', SCRIPT)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    mod.SCRIPTS_DIR = str(live_scripts)
    return mod


def _make_repo(root):
    (root / 'scripts').mkdir(parents=True)
    (root / 'agents').mkdir()
    (root / 'manifest.json').write_text(
        json.dumps({'name': 'devin-bundle'}), encoding='utf-8')
    (root / 'scripts' / 'a.py').write_text('x = 1\n', encoding='utf-8')
    (root / 'agents' / 'b.md').write_text('# agent\n', encoding='utf-8')


def _make_live(base):
    scripts = base / 'live' / 'scripts'
    agents = base / 'live' / 'agents'
    scripts.mkdir(parents=True)
    agents.mkdir()
    return scripts


def _run(mod, cwd):
    buf = io.StringIO(json.dumps({'hook_event_name': 'SessionStart',
                                  'cwd': str(cwd)}))
    out = io.StringIO()
    saved = (sys.stdin, sys.stdout)
    sys.stdin, sys.stdout = buf, out
    try:
        mod.main()
    finally:
        sys.stdin, sys.stdout = saved
    return out.getvalue().strip()


def test_identical_live_is_silent(tmp_path):
    repo = tmp_path / 'repo'
    _make_repo(repo)
    live = _make_live(tmp_path)
    (live / 'a.py').write_text('x = 1\n', encoding='utf-8')
    (live.parent / 'agents' / 'b.md').write_text('# agent\n', encoding='utf-8')
    assert _run(_load(live), repo) == ''


def test_drifted_file_warns(tmp_path):
    repo = tmp_path / 'repo'
    _make_repo(repo)
    live = _make_live(tmp_path)
    (live / 'a.py').write_text('x = 2  # stale\n', encoding='utf-8')
    (live.parent / 'agents' / 'b.md').write_text('# agent\n', encoding='utf-8')
    out = _run(_load(live), repo)
    obj = json.loads(out)
    ctx = obj['hookSpecificOutput']['additionalContext']
    assert 'scripts/a.py' in ctx
    assert 'hook-drift' in ctx


def test_missing_live_file_warns(tmp_path):
    repo = tmp_path / 'repo'
    _make_repo(repo)
    live = _make_live(tmp_path)  # a.py not copied
    (live.parent / 'agents' / 'b.md').write_text('# agent\n', encoding='utf-8')
    out = _run(_load(live), repo)
    obj = json.loads(out)
    assert '(missing live)' in \
        obj['hookSpecificOutput']['additionalContext']


def test_orphan_live_file_warns(tmp_path):
    repo = tmp_path / 'repo'
    _make_repo(repo)
    live = _make_live(tmp_path)
    (live / 'a.py').write_text('x = 1\n', encoding='utf-8')
    (live / 'old.py').write_text('# deleted from repo\n', encoding='utf-8')
    (live.parent / 'agents' / 'b.md').write_text('# agent\n', encoding='utf-8')
    out = _run(_load(live), repo)
    obj = json.loads(out)
    ctx = obj['hookSpecificOutput']['additionalContext']
    assert 'scripts/old.py' in ctx
    assert '(orphan live)' in ctx


def test_no_bundle_root_is_silent(tmp_path):
    bare = tmp_path / 'bare'
    bare.mkdir()
    live = _make_live(tmp_path)
    assert _run(_load(live), bare) == ''


def test_running_from_repo_is_silent(tmp_path):
    repo = tmp_path / 'repo'
    _make_repo(repo)
    # SCRIPTS_DIR inside the repo -> repo_dir == live_dir -> skip
    assert _run(_load(repo / 'scripts'), repo) == ''
