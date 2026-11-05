#!/usr/bin/env python3
"""PostToolUse(write|edit) hook: warn when an edited file crosses the
big-file threshold where agent context starts rotting (reels-2 R2-13).

Warn-only: never blocks. Fires once per threshold band (800, 1200,
1600, ...) so a huge file does not nag on every edit; state lives in
.devin/memory/.file-size-guard.json.

Output: hookSpecificOutput.additionalContext when warning; silent exit
0 otherwise.
"""
import json
import os
import sys

THRESHOLD = int(os.environ.get('BUNDLE_FILESIZE_WARN', '800'))
BAND = 400
CODE_EXTS = {'.py', '.ts', '.tsx', '.js', '.jsx', '.go', '.rs', '.java',
             '.cs', '.cpp', '.c', '.h', '.rb', '.php', '.sh', '.ps1'}
SKIP_PARTS = {'node_modules', 'vendor', 'dist', 'build', '.git',
              'generated', '__pycache__', 'site-packages'}


def _state_path(project_dir):
    return os.path.join(project_dir, '.devin', 'memory',
                        '.file-size-guard.json')


def main():
    try:
        payload = json.loads(sys.stdin.read() or '{}')
    except Exception:
        return
    path = (payload.get('tool_input') or {}).get('file_path') or ''
    if not path:
        return
    ext = os.path.splitext(path)[1].lower()
    parts = set(os.path.normpath(path).lower().split(os.sep))
    if ext not in CODE_EXTS or parts & SKIP_PARTS:
        return
    try:
        with open(path, encoding='utf-8', errors='replace') as f:
            lines = sum(1 for _ in f)
    except OSError:
        return
    if lines < THRESHOLD:
        return

    band = lines // BAND
    project = os.environ.get('DEVIN_PROJECT_DIR') or os.getcwd()
    sp = _state_path(project)
    try:
        state = json.load(open(sp, encoding='utf-8'))
    except Exception:
        state = {}
    key = os.path.abspath(path)
    if state.get(key, 0) >= band:
        return
    state[key] = band
    try:
        os.makedirs(os.path.dirname(sp), exist_ok=True)
        json.dump(state, open(sp, 'w', encoding='utf-8'))
    except OSError:
        pass

    msg = (f'file-size-guard: {os.path.basename(path)} is now {lines} lines '
           f'(threshold {THRESHOLD}). Files this size truncate reads and '
           'rot context; consider the big-file-refactor skill before the '
           'next large change.')
    print(json.dumps({
        'hookSpecificOutput': {
            'hookEventName': 'PostToolUse',
            'additionalContext': msg,
        }
    }))


if __name__ == '__main__':
    main()
