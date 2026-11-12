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

Sub-script contract (issue #408): scripts run in-process and MUST be
non-blocking - bounded CPU/regex work only, no network calls or unbounded
disk scans. A hung script hangs the whole consolidated phase until the
outer hook timeout kills everything; hooks.v1.json `timeout` is the only
bound. Keep each script well under its phase budget.
"""
import importlib.util
import io
import json
import os
import sys
import time
import traceback

SCRIPTS_DIR = os.path.dirname(os.path.abspath(__file__))
METRICS_MAX_BYTES = 512 * 1024
SLOW_SCRIPT_MS = 5000


def metrics_sink_path():
    """Append-only JSONL metric sink (gitignored via '.devin/ledgers/*').

    Anchors to the project root by walking up from cwd looking for `.devin/`
    or `manifest.json` — a hook spawned with cwd=scripts/ must not create a
    stray `scripts/.devin/` tree."""
    explicit = os.environ.get("DEVIN_PROJECT_DIR")
    if explicit:
        return os.path.join(explicit, ".devin", "ledgers", "metrics.jsonl")
    start = os.getcwd()
    cur = os.path.abspath(start)
    for _ in range(4):
        if os.path.isdir(os.path.join(cur, ".devin")) \
                or os.path.isfile(os.path.join(cur, "manifest.json")):
            return os.path.join(cur, ".devin", "ledgers", "metrics.jsonl")
        parent = os.path.dirname(cur)
        if parent == cur:
            break
        cur = parent
    return os.path.join(start, ".devin", "ledgers", "metrics.jsonl")


def emit_metric(event, **fields):
    """Append one JSON line to the metrics sink. Never raises.
    Rotates at METRICS_MAX_BYTES keeping the newest half (issue #408 -
    the sink grew unbounded, ~10k lines / 2.2MB on one machine)."""
    try:
        path = metrics_sink_path()
        os.makedirs(os.path.dirname(path), exist_ok=True)
        rec = {"t": int(time.time()), "event": event}
        rec.update(fields)
        line = json.dumps(rec, default=str) + "\n"
        try:
            if os.path.getsize(path) > METRICS_MAX_BYTES:
                with open(path, "rb") as f:
                    f.seek(-METRICS_MAX_BYTES // 2, os.SEEK_END)
                    tail = f.read()
                nl = tail.find(b"\n")
                if nl >= 0:
                    tail = tail[nl + 1:]
                with open(path, "wb") as f:
                    f.write(tail)
        except OSError:
            pass
        with open(path, "a", encoding="utf-8") as f:
            f.write(line)
    except Exception:
        pass  # fail-soft: cleanup; preserve primary error


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
    t0 = time.time()
    timings = {}
    for name in script_names:
        ts = time.time()
        code, out, err = _run_one(name, payload)
        ms = int((time.time() - ts) * 1000)
        timings[name] = ms
        # Slow scripts are observable via the timings_ms metric below. Do NOT
        # warn on stderr: under `fail_closed: true` the CLI treats hook stderr
        # as failure and rejects the tool call (audit-2026-11-12 #544).
        if ms > SLOW_SCRIPT_MS and os.environ.get("DEVIN_HOOKRUN_DEBUG"):
            sys.stderr.write(
                f"[hookrun] slow script {name}: {ms}ms\n")
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
    rc = 2 if blocked is not None or final_code == 2 else 0
    emit_metric(
        'hookrun',
        hook_event=payload.get('hook_event_name', ''),
        scripts=','.join(script_names),
        duration_ms=int((time.time() - t0) * 1000),
        exit_code=rc,
        timings_ms=timings,
    )
    return rc


def main(script_names):
    try:
        _recfg = getattr(sys.stdin, "reconfigure", None)
        if _recfg:
            try:
                _recfg(encoding="utf-8", errors="replace")
            except (OSError, ValueError):
                pass
        payload = json.load(sys.stdin)
    except (json.JSONDecodeError, EOFError, ValueError):
        payload = {}
    sys.exit(run(script_names, payload))


if __name__ == '__main__':
    sys.exit('usage: import _hookrun from a consolidated hook script (see pre-exec-guard.py)')
