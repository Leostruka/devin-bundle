#!/usr/bin/env python3
"""busybar listen - device input events -> agent triggers (#491).

The push direction (focus -> display) exists; this is the reverse:
the Busy Bar as a physical control surface. Subscribes to the device
state stream and maps input events to focus/agent actions.

Sources:
  --replay FILE   JSON-lines frames, one per line (tests, captures)
  --ws URL        ws:// device state stream (stdlib raw-socket client;
                  hardware-blocked, unverified against a real device)

Event map (advisory by default — prints the action; --exec runs it):
  star/pause switch toggle -> `python scripts/focus.py start|stop`
  dial position 1..3       -> effort preset note (S/M/L)
  everything else          -> ignored (v0)

Fail-soft everywhere: unreadable frames skip with a stderr note;
unreachable device exits advisory, never blocks.
"""
import argparse
import json
import subprocess
import sys

FOCUS = [sys.executable, "scripts/focus.py"]
EFFORT = {1: "S", 2: "M", 3: "L"}


def _walk_strings(obj, key_hints=("switch", "button", "state", "event",
                                  "type", "dial", "encoder", "position",
                                  "name", "value", "pressed")):
    """Flatten any nested frame into {hint: value} — the exact wire
    schema is unverified without hardware; tolerance beats guessing."""
    out = {}

    def rec(o):
        if isinstance(o, dict):
            for k, v in o.items():
                kl = str(k).lower()
                if kl in key_hints or kl.endswith(
                        ("switch", "button", "dial", "position")):
                    out.setdefault(kl, v)
                rec(v)
        elif isinstance(o, list):
            for v in o:
                rec(v)
    rec(obj)
    return out


def map_event(frame):
    """Frame dict -> action tuple ('focus-start'|'focus-stop'|
    'effort-<SML>'|None)."""
    f = _walk_strings(frame)
    sw = str(f.get("switch") or f.get("button") or "").lower()
    st = f.get("pressed", f.get("state"))
    if isinstance(st, str):
        st = st.lower() in ("1", "true", "on", "pressed", "start")
    if sw in ("star", "pause", "play", "start"):
        return ("focus-start" if st else "focus-stop")
    for k in ("dial", "encoder", "position", "value"):
        if k in f:
            try:
                pos = int(f[k])
            except (TypeError, ValueError):
                continue
            if pos in EFFORT:
                return f"effort-{EFFORT[pos]}"
    return None


def run_action(action, exec_mode):
    cmd = {"focus-start": FOCUS + ["start"],
           "focus-stop": FOCUS + ["stop"]}.get(action)
    if action.startswith("effort-"):
        print(f"[busybar] effort preset -> {action.split('-')[1]}")
        return
    if cmd is None:
        return
    if exec_mode:
        subprocess.run(cmd, timeout=15, capture_output=True, text=True,
                       encoding="utf-8", errors="replace")
    print(f"[busybar] {action} -> {' '.join(cmd)}"
          + ("" if exec_mode else " (dry)"))


def replay(path, exec_mode):
    n = 0
    with open(path, encoding="utf-8", errors="replace") as fh:
        for ln in fh:
            ln = ln.strip()
            if not ln:
                continue
            try:
                frame = json.loads(ln)
            except ValueError:
                print(f"[busybar] unreadable frame skipped: {ln[:60]}",
                      file=sys.stderr)
                continue
            act = map_event(frame)
            if act:
                n += 1
                run_action(act, exec_mode)
    print(f'{{"ok": true, "actions": {n}}}')


def _ws_client(url):
    """Minimal ws:// client: HTTP upgrade + unmasked text-frame reads.
    RFC6455 client side; server frames are unmasked by spec. Binary/
    ping/close frames are skipped (v0 advisory listener)."""
    import base64
    import os
    import socket
    host, _, rest = url[5:].partition("/")
    port = 80
    if ":" in host:
        host, ps = host.split(":", 1)
        port = int(ps)
    s = socket.create_connection((host, port), timeout=5)
    key = base64.b64encode(os.urandom(16)).decode()
    s.sendall((f"GET /{rest} HTTP/1.1\r\nHost: {host}:{port}\r\n"
               "Upgrade: websocket\r\nConnection: Upgrade\r\n"
               f"Sec-WebSocket-Key: {key}\r\n"
               "Sec-WebSocket-Version: 13\r\n\r\n").encode())
    buf = s.recv(4096)
    if b"101" not in buf.split(b"\r\n", 1)[0]:
        s.close()
        raise OSError("ws upgrade refused")
    while True:
        hdr = s.recv(2)
        if len(hdr) < 2:
            return
        opcode = hdr[0] & 0x0F
        ln = hdr[1] & 0x7F
        if ln == 126:
            ln = int.from_bytes(s.recv(2), "big")
        elif ln == 127:
            ln = int.from_bytes(s.recv(8), "big")
        payload = b""
        while len(payload) < ln:
            chunk = s.recv(ln - len(payload))
            if not chunk:
                return
            payload += chunk
        if opcode == 1:  # text
            yield payload.decode("utf-8", errors="replace")
        elif opcode == 8:  # close
            return


def listen_ws(url, exec_mode):
    try:
        for text in _ws_client(url):
            try:
                frame = json.loads(text)
            except ValueError:
                continue
            act = map_event(frame)
            if act:
                run_action(act, exec_mode)
    except OSError as e:
        print(f"busybar unreachable ({e}) - listen skipped",
              file=sys.stderr)


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    src = ap.add_mutually_exclusive_group(required=True)
    src.add_argument("--replay")
    src.add_argument("--ws")
    ap.add_argument("--exec", action="store_true",
                    help="actually run focus commands (default: dry)")
    a = ap.parse_args()
    if a.replay:
        replay(a.replay, a.exec)
    else:
        listen_ws(a.ws, a.exec)


if __name__ == "__main__":
    main()
