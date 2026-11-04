#!/usr/bin/env python3
"""Render hooks.v1.json into a user-level config.json hooks object.

`hooks.v1.json` is the single authored source of hook bindings. Its commands
are project-relative (`python scripts/...`) so the file can drop into any
project's `.devin/` unchanged. User-level hooks live only inside
`config.json.hooks` and need absolute paths into the installed devin home —
this renderer produces that expansion so the two surfaces cannot drift.

Usage:
  render-user-hooks.py <devin_home>              print rendered hooks JSON
  render-user-hooks.py <devin_home> --merge CFG  set CFG["hooks"] = rendered
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PREFIX = 'python scripts/'


def hook_python():
    """Resolve the interpreter rendered into hook commands.

    The installers invoke this script with whichever interpreter they found
    (python / python3 / py), so sys.executable is a known-good interpreter.
    Rendering its absolute path keeps hooks working on systems where bare
    `python` is not on PATH (stock macOS, minimal Linux/WSL images), which
    matters because the PreToolUse guards are fail_closed: a missing
    interpreter would block every exec/write/edit call.

    On Windows prefer pythonw.exe next to the interpreter so hook spawns
    don't flash a console window that steals focus; stdout/stderr still
    flow through inherited pipes.
    """
    exe = sys.executable
    if os.name == 'nt':
        pythonw = os.path.join(os.path.dirname(exe), 'pythonw.exe')
        if os.path.isfile(pythonw):
            exe = pythonw
    return exe


def render(devin_home):
    src = os.path.join(ROOT, 'hooks.v1.json')
    with open(src, encoding='utf-8-sig') as fh:
        hooks = json.load(fh)
    home = devin_home.replace('\\', '/').rstrip('/')
    for entries in hooks.values():
        for entry in entries:
            for h in entry.get('hooks', []):
                cmd = h.get('command', '')
                if cmd.startswith(PREFIX):
                    h['command'] = '"{}" "{}/scripts/{}"'.format(hook_python(), home, cmd[len(PREFIX):])
    return hooks


def main():
    # Supported floor: Python >= 3.11 for bundle hook scripts.
    if sys.version_info < (3, 11):
        print('render-user-hooks: warning: Python >= 3.11 is the supported '
              'floor for hook scripts; running on '
              + sys.version.split()[0], file=sys.stderr)
    args = [a for a in sys.argv[1:] if a != '--merge']
    if len(args) < 1:
        sys.exit('usage: render-user-hooks.py <devin_home> [--merge <config.json>]')
    hooks = render(args[0])
    if '--merge' in sys.argv:
        cfg_path = args[1]
        with open(cfg_path, encoding='utf-8-sig') as fh:
            cfg = json.load(fh)
        cfg['hooks'] = hooks
        tmp = cfg_path + '.tmp'
        with open(tmp, 'w', encoding='utf-8', newline='\n') as fh:
            json.dump(cfg, fh, indent=2)
            fh.write('\n')
        os.replace(tmp, cfg_path)
    else:
        json.dump(hooks, sys.stdout, indent=2)
        sys.stdout.write('\n')


if __name__ == '__main__':
    main()
