#!/usr/bin/env python3
"""SessionStart advisory — warns when live hook scripts differ from the
bundle repo's copies.

Motivation (2026-11-24 incident): repo fixes to destructive-gate.py never
reached %APPDATA% until re-install; the stale live gate produced phantom
self-blocks for hours. Live hooks always run this directory's content —
repo edits are inert until synced via install.

Non-blocking and bounded: byte-compares scripts/ + agents/ + skills/
(no network; skills/ is walked recursively, capped per-file size).
Emits hookSpecificOutput.additionalContext naming the drifted files so
the agent can sync before trusting probe/verify runs; silent when
identical or when no bundle repo is found above cwd.
"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _hookrun

SCRIPTS_DIR = os.path.dirname(os.path.abspath(__file__))
_CHECK_DIRS = ('scripts', 'agents')
_RECURSIVE_DIRS = ('skills',)
_SUFFIXES = ('.py', '.js', '.md', '.sh', '.ps1', '.json', '.yaml', '.yml')
_SKIP_DIRS = ('__pycache__', 'node_modules', '.venv', 'venv', '.git')
_MAX_BYTES = 2 * 1024 * 1024
_MAX_LISTED = 8


def _bundle_root(start):
    """Walk up from start for the devin-bundle repo (manifest name check)."""
    cur = os.path.abspath(start)
    for _ in range(10):
        man = os.path.join(cur, 'manifest.json')
        if os.path.isfile(man):
            try:
                with open(man, encoding='utf-8') as f:
                    if json.load(f).get('name') == 'devin-bundle':
                        return cur
            except (OSError, ValueError):
                pass
        parent = os.path.dirname(cur)
        if parent == cur:
            return None
        cur = parent
    return None


def _live_dir(rel):
    if rel == 'scripts':
        return SCRIPTS_DIR
    return os.path.join(os.path.dirname(SCRIPTS_DIR), rel)


def _same_file(repo_f, live_f):
    try:
        if os.path.getsize(repo_f) > _MAX_BYTES or \
                os.path.getsize(live_f) > _MAX_BYTES:
            return True  # too big to compare cheaply - skip, not drift
        with open(repo_f, 'rb') as a, open(live_f, 'rb') as b:
            return a.read() == b.read()
    except OSError:
        return True


def _iter_repo(repo_dir, recursive):
    if not recursive:
        for fn in sorted(os.listdir(repo_dir)):
            yield fn, os.path.join(repo_dir, fn)
        return
    for dirpath, dirnames, filenames in os.walk(repo_dir):
        dirnames[:] = [d for d in dirnames if d not in _SKIP_DIRS]
        for fn in sorted(filenames):
            full = os.path.join(dirpath, fn)
            yield os.path.relpath(full, repo_dir), full


def _drifted(root):
    out = []
    for rel in _CHECK_DIRS + _RECURSIVE_DIRS:
        recursive = rel in _RECURSIVE_DIRS
        repo_dir = os.path.join(root, rel)
        live_dir = _live_dir(rel)
        if not os.path.isdir(repo_dir) or not os.path.isdir(live_dir):
            continue
        if os.path.normcase(os.path.abspath(repo_dir)) == \
                os.path.normcase(os.path.abspath(live_dir)):
            continue  # running from the repo itself
        repo_names = set()
        for name, repo_f in _iter_repo(repo_dir, recursive):
            base = os.path.basename(name)
            if not base.endswith(_SUFFIXES):
                continue
            repo_names.add(name)
            live_f = os.path.join(live_dir, name)
            label = rel + '/' + name.replace(os.sep, '/')
            if not os.path.isfile(live_f):
                out.append(label + ' (missing live)')
                continue
            if not _same_file(repo_f, live_f):
                out.append(label)
        # install is copy-only (install.ps1) - files deleted/renamed in the
        # repo stay live forever and still execute if referenced
        for name, live_f in _iter_repo(live_dir, recursive):
            base = os.path.basename(name)
            if base.endswith(_SUFFIXES) and name not in repo_names:
                out.append(rel + '/' + name.replace(os.sep, '/') +
                           ' (orphan live)')
    return out


def main():
    try:
        _hookrun.pin_stdio_utf8(sys.stdin)
        payload = json.load(sys.stdin)
    except (json.JSONDecodeError, EOFError, ValueError):
        payload = {}
    start = payload.get('cwd') if isinstance(payload, dict) else None
    root = _bundle_root(start or os.getcwd())
    if not root:
        return
    drift = _drifted(root)
    if not drift:
        return
    shown = drift[:_MAX_LISTED]
    more = ' (+%d more)' % (len(drift) - _MAX_LISTED) \
        if len(drift) > _MAX_LISTED else ''
    print(json.dumps({
        'hookSpecificOutput': {
            'hookEventName': 'SessionStart',
            'additionalContext':
                'hook-drift: %d live file(s) differ from the bundle repo: '
                '%s%s. Live hooks run the stale copy - sync with '
                '`pwsh -File install.ps1 -Force -Backup` (or cp the listed '
                'files) before trusting hook behavior in this session.'
                % (len(drift), ', '.join(shown), more),
        }
    }))


if __name__ == '__main__':
    main()
