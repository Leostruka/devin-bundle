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
import hashlib
import importlib.util
import io
import json
import os
import re
import sys
import time
import traceback

SCRIPTS_DIR = os.path.dirname(os.path.abspath(__file__))
METRICS_MAX_BYTES = 512 * 1024
SLOW_SCRIPT_MS = 5000


def pin_stdio_utf8(stream):
    """Reconfigure a stdio stream to UTF-8 with replace errors.

    Windows consoles default to cp1252; hook stdin/stdout carrying
    non-ASCII payloads would corrupt or crash. No-op when the stream
    lacks reconfigure (redirected pipes on some platforms).
    """
    recfg = getattr(stream, "reconfigure", None)
    if recfg:
        try:
            recfg(encoding="utf-8", errors="replace")
        except (OSError, ValueError):
            pass


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
    # Walk well past any realistic subtree depth: 4 hops missed
    # tests/held-out/mutation/x (5 levels) and created a stray
    # <deep>/.devin/ledgers tree (same class as the Temp\.devin leak).
    for _ in range(10):
        if os.path.isdir(os.path.join(cur, ".devin")):
            return os.path.join(cur, ".devin", "ledgers", "metrics.jsonl")
        man = os.path.join(cur, "manifest.json")
        if os.path.isfile(man):
            try:
                import json as _json
                with open(man, encoding="utf-8") as f:
                    d = _json.load(f)
                if isinstance(d, dict) and d.get("name") == "devin-bundle":
                    return os.path.join(
                        cur, ".devin", "ledgers", "metrics.jsonl")
            except (OSError, ValueError):
                pass
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


_WTP_SPECIAL = re.compile(r"<[^>]*>")
_WTP_CLEAR = re.compile(r"(?i)<C-c>|<C-u>")
# Line-editing controls the pending model cannot replicate inject a \x1e
# sentinel - a submit carrying it means "executing text the gate cannot
# inspect": history recall (<UP>/<C-r>...) sources unseen HISTFILE text;
# cursor moves/edits (<LEFT>/<C-a>/<C-w>/<TAB>) change the line in ways
# the append-model cannot reproduce (an insert at a moved cursor position
# can shift a pattern boundary - under-detection).
_WTP_RECALL = re.compile(
    r"(?i)<UP>|<DOWN>|<LEFT>|<RIGHT>|<HOME>|<END>|<INSERT>|<DELETE>|"
    r"<BS>|<BACKSPACE>|<TAB>|<ESC>|"
    # C-a/C-b/C-d/C-e/C-f/C-k/C-n/C-p/C-r/C-t/C-w/C-y/C-_: edit/recall.
    # C-l (clear screen) is line-neutral; C-m IS carriage-return.
    # Deletes count too: a deleted char can complete a pattern boundary
    # (git push --forceX<BS> submits git push --force) - under-detection.
    r"<C-[abdefhknprtwy_]>")
# Literal control bytes with the same edit semantics in raw text_input.
_WTP_LIT_EDIT = re.compile(r"[\x08\x7f]")
# Keep the HEAD of an oversized line: gated verbs/flags lead the command,
# so tail-truncation preserves detection. A >4KB single line still scans
# only its first 4KB (paste-size residual).
_WTP_BUF_CAP = 4096


def _devin_home():
    appdata = os.environ.get("APPDATA", "")
    if appdata:
        return os.path.join(appdata, "devin")
    return os.path.join(os.path.expanduser("~"), ".config", "devin")


def _wtp_buf_path(payload, tool_input):
    """Per-shell pending-line buffer for write_to_process (split-write
    bypass: dangerous text can arrive in one call and the CR in the next,
    so the gate must model the shell's current input line across calls)."""
    try:
        key = "|".join([
            str(payload.get("session_id", "")),
            # prompt_id rotates per user prompt while the shell's input
            # line persists - including it would re-open the split-write
            # bypass across prompt boundaries.
            # Pre- and post-event hooks each see the same stdin stream and
            # must model the pending line independently - sharing one
            # buffer would double-count the text.
            str(payload.get("hook_event_name", "")),
            str(tool_input.get("shell_id", ""))])
        h = hashlib.sha256(key.encode("utf-8")).hexdigest()[:16]
        d = os.environ.get("DEVIN_STATE_DIR") or os.path.join(
            _devin_home(), "state")
        os.makedirs(d, exist_ok=True)
        return os.path.join(d, "wtp-" + h + ".txt")
    except Exception:
        return None


# Same-payload re-extraction window (seconds): _normalize_wtp consumes
# the stdin stream once, then every downstream gate re-extracts the SAME
# payload. The buffer file records the last input hash so a repeat call
# inside this window returns the prior output without double-consuming.
# Outside the window an identical payload is a genuinely new keystroke
# and must consume normally (legit repeated input appends again).
_WTP_DEDUP_S = 30.0


def _wtp_input_key(payload, tool_input, is_bytes, raw):
    """sha256 of the raw stdin inputs - the dedup anchor. Derives from
    attacker-visible fields only, but lives in the gated buffer file so
    a forged '_wtp_normalized'/'command' pair cannot fake it."""
    key = "|".join([
        str(payload.get("session_id", "")),
        str(payload.get("hook_event_name", "")),
        str(tool_input.get("shell_id", "")),
        "b" if is_bytes else "t", raw])
    return hashlib.sha256(key.encode("utf-8")).hexdigest()[:24]


def wtp_submitted_text(payload):
    """Return the lines a write_to_process call actually submits to the
    target shell.

    A line runs only when followed by CR/LF - trailing text stays on the
    shell's input line and is buffered per shell across calls. C-c/C-u
    clear-controls discard the pending line. bytes_input uses
    angle-bracket notation (<CR>, <C-c>) decoded to real chars first.

    Idempotent within _WTP_DEDUP_S for the same inputs: downstream gates
    always call this on wtp payloads (a 'command' or '_wtp_normalized'
    key supplied by the caller is untrusted and ignored) - the dedup
    record in the gated buffer file proves whether this input was
    already consumed, so re-extraction cannot corrupt the pending model.
    """
    tool_input = payload.get("tool_input")
    if not isinstance(tool_input, dict):
        return ""
    is_bytes = False
    text = tool_input.get("text_input")
    if not isinstance(text, str) or not text:
        text = tool_input.get("bytes_input")
        is_bytes = True
        if not isinstance(text, str) or not text:
            return ""
    raw = text
    if is_bytes:
        text = re.sub(r"(?i)<CR>|<LF>|<C-m>|<C-j>|\r\n?", "\n", text)
        # Control-byte equivalents: C-g aborts the line like C-c;
        # C-i is TAB (line-edit oracle).
        text = re.sub(r"(?i)<C-g>", "\x03", text)
        text = re.sub(r"(?i)<C-i>", "\x1e", text)
        text = _WTP_CLEAR.sub("\x03", text)
        text = _WTP_RECALL.sub("\x1e", text)
        text = _WTP_SPECIAL.sub("", text)
    # Literal BS/DEL bytes are the same unmodelable edits as their tokens.
    text = _WTP_LIT_EDIT.sub("\x1e", text)
    in_key = _wtp_input_key(payload, tool_input, is_bytes, raw)
    pending = ""
    dedup_i = ""
    buf = _wtp_buf_path(payload, tool_input)
    if buf:
        try:
            rec = ""
            fresh = False
            if os.path.isfile(buf):
                fresh = time.time() - os.path.getmtime(buf) < _WTP_DEDUP_S
                with open(buf, encoding="utf-8", errors="replace") as fh:
                    rec = fh.read()
            try:
                obj = json.loads(rec)
            except ValueError:
                obj = None
            if isinstance(obj, dict):
                pending = str(obj.get("p", ""))[:_WTP_BUF_CAP]
                dedup_i = str(obj.get("i", "")) if fresh else ""
            elif rec:
                # Legacy plain-text pending line (pre-JSON buffers).
                pending = rec[:_WTP_BUF_CAP]
            if dedup_i == in_key:
                # Same stdin input already consumed in this hook
                # invocation - return the prior output untouched.
                return str(obj.get("o", ""))
        except OSError:
            pending = ""
    combined = pending + text
    # C-c / C-u discards the CURRENT input line only - a submitted line
    # (before its newline) already ran and must stay in the model, so
    # clear applies per segment, never across a newline boundary.
    lines = [seg.rsplit("\x03", 1)[-1]
             for seg in re.split(r"\r\n|\r|\n", combined)]
    tail = lines[-1]
    if len(tail) > _WTP_BUF_CAP:
        # Truncated tail is uninspectable - mark it tainted so a submit
        # carrying it blocks instead of under-scanning.
        tail = "\x1e" + tail[:_WTP_BUF_CAP]
    out = "\n".join(lines[:-1])
    if buf:
        try:
            with open(buf, "w", encoding="utf-8") as fh:
                fh.write(json.dumps({"p": tail, "i": in_key, "o": out}))
        except OSError:
            pass
    return out


def _normalize_wtp(payload):
    """write_to_process carries shell stdin, not a command field - inject
    the submitted lines as tool_input.command so every inner gate sees the
    real commands (C90/C91: otherwise each gate silently no-ops)."""
    try:
        if payload.get("tool_name") != "write_to_process":
            return
        ti = payload.get("tool_input")
        if not isinstance(ti, dict):
            return
        # Always overwrite: a 'command' key on a wtp payload is not part of
        # the tool schema - an injected one would defeat normalization.
        # No trust marker is written: any payload-visible flag could be
        # forged by the caller. Extraction is idempotent instead (dedup
        # record in the gated buffer file), so gates re-extract safely.
        ti["command"] = wtp_submitted_text(payload)
    except Exception:
        pass


def _run_one(script_name, payload):
    """Run scripts/<script_name> main() in-process. Returns (exit_code, stdout, stderr)."""
    path = os.path.join(SCRIPTS_DIR, script_name)
    if SCRIPTS_DIR not in sys.path:
        sys.path.append(SCRIPTS_DIR)
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
    _normalize_wtp(payload)
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
        # Same rule as the slow-script note above: child stderr (incl.
        # crash tracebacks) must not reach the hook's stderr under
        # fail_closed, or the CLI rejects the tool call.
        if err and os.environ.get("DEVIN_HOOKRUN_DEBUG"):
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
                if os.environ.get("DEVIN_HOOKRUN_DEBUG"):
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
        # The CLI rejects hookSpecificOutput without hookEventName (parse
        # fail -> the whole hook call "fails" -> fail_closed blocks the
        # tool call with an opaque error). Synthesize it from the payload
        # when no child emitted one (C84).
        if 'hookEventName' not in hso_out:
            ev = payload.get('hook_event_name') or payload.get('hookEventName')
            if ev:
                hso_out['hookEventName'] = ev
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
    if not isinstance(payload, dict):
        payload = {}
    sys.exit(run(script_names, payload))


if __name__ == '__main__':
    sys.exit('usage: import _hookrun from a consolidated hook script (see pre-exec-guard.py)')
