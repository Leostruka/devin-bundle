#!/usr/bin/env python3
"""In-process hook runner — executes several hook scripts in one spawn.

Each bundle hook script pays ~50-80ms of Python interpreter startup while its
real work takes <10ms. `_hookrun.run()` loads sibling scripts as modules with
faked stdin/stdout, calls their `main()`, and merges their hook-protocol
output — one interpreter for N checks.

Merge semantics:
  - any `decision: block` wins (first blocker's reason kept); exit code 2
    propagates
  - `hookSpecificOutput.additionalContext` strings concatenate
  - `hookSpecificOutput.updatedInput` objects shallow-merge
  - non-JSON stdout is routed to stderr (hook stdout stays clean JSON)
  - a crashing script fails open (logged to stderr, does not block)
"""
import importlib.util
import io
import json
import os
import sys
import traceback

SCRIPTS_DIR = os.path.dirname(os.path.abspath(__file__))


def _run_one(script_name, payload):
    """Run scripts/<script_name> main() in-process. Returns (exit_code, stdout, stderr)."""
    path = os.path.join(SCRIPTS_DIR, script_name)
    spec = importlib.util.spec_from_file_location('hookmod_' + script_name.replace('-', '_'), path)
    mod = importlib.util.module_from_spec(spec)
    stdin_buf = io.StringIO(json.dumps(payload))
    stdout_buf = io.StringIO()
    stderr_buf = io.StringIO()
    saved = (sys.stdin, sys.stdout, sys.stderr, sys.argv)
    sys.stdin, sys.stdout, sys.stderr = stdin_buf, stdout_buf, stderr_buf
    sys.argv = [script_name]
    code = 0
    try:
        spec.loader.exec_module(mod)
        if hasattr(mod, 'main'):
            mod.main()
    except SystemExit as e:
        code = e.code if isinstance(e.code, int) else (0 if e.code in (None, '') else 1)
    except Exception:
        traceback.print_exc(file=sys.stderr)
        code = 0  # fail-open, same policy as the scripts themselves
    finally:
        sys.stdin, sys.stdout, sys.stderr, sys.argv = saved
    return code, stdout_buf.getvalue(), stderr_buf.getvalue()


def run(script_names, payload):
    """Run scripts in order, merge hook output, print result. Returns exit code."""
    merged = {}
    contexts = []
    updated_input = {}
    blocked = None
    final_code = 0
    for name in script_names:
        code, out, err = _run_one(name, payload)
        if err:
            sys.stderr.write(err)
        if code == 2 and final_code != 2:
            final_code = 2
        for line in out.splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                obj = json.loads(line)
            except ValueError:
                sys.stderr.write('[{}] {}\n'.format(name, line))
                continue
            if not isinstance(obj, dict):
                continue
            if obj.get('decision') == 'block' and blocked is None:
                blocked = obj
            elif 'decision' in obj and 'decision' not in merged:
                merged['decision'] = obj['decision']
                if 'reason' in obj:
                    merged['reason'] = obj.get('reason', '')
            hso = obj.get('hookSpecificOutput')
            if isinstance(hso, dict):
                ctx = hso.get('additionalContext')
                if ctx:
                    contexts.append(str(ctx))
                ui = hso.get('updatedInput')
                if isinstance(ui, dict):
                    updated_input.update(ui)
                for k, v in hso.items():
                    if k not in ('additionalContext', 'updatedInput'):
                        merged.setdefault('hookSpecificOutput', {})[k] = v
    result = {}
    if blocked is not None:
        result = blocked
    elif merged.get('decision'):
        result['decision'] = merged['decision']
        if merged.get('reason'):
            result['reason'] = merged['reason']
    hso_out = dict(merged.get('hookSpecificOutput', {}))
    if contexts:
        hso_out['additionalContext'] = '\n\n'.join(contexts)
    if updated_input:
        hso_out['updatedInput'] = updated_input
    if hso_out:
        result['hookSpecificOutput'] = hso_out
    if result:
        print(json.dumps(result))
    return 2 if blocked is not None or final_code == 2 else 0


def main(script_names):
    try:
        payload = json.load(sys.stdin)
    except (json.JSONDecodeError, EOFError, ValueError):
        payload = {}
    sys.exit(run(script_names, payload))


if __name__ == '__main__':
    sys.exit('usage: import _hookrun from a consolidated hook script (see pre-exec-guard.py)')
