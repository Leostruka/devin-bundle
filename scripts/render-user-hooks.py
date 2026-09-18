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
                    h['command'] = 'python "{}/scripts/{}"'.format(home, cmd[len(PREFIX):])
    return hooks


def main():
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
