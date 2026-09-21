"""Persistent owned sessions: a loopback daemon holds spawned
subprocesses across CLI invocations.

Same daemon shape as computer-use terminal_sessions: JSONL
one-request-per-connection on 127.0.0.1:0, atomic pidfile, idle TTL
exit. Sessions are pipe-backed (no PTY); each child tree is bound to a
Windows Job Object / POSIX process group via sc_process so daemon death
kills every owned child.

Envelope {daemon_token, generation, op, arg}: wrong or missing token
and foreign generation are rejected before dispatch. `ping` is the
only token-less op. Per-session ops must also match the session id and
its random token.
"""

import collections
import hmac
import json
import os
import re
import secrets
import socket
import subprocess
import sys
import tempfile
import threading
import time
import uuid

import sc_contract as contract
import sc_process

PIDFILE = os.path.join(tempfile.gettempdir(), "devin-sc-sessions.json")
IDLE_TTL_S = float(os.environ.get("SC_SESSIONS_IDLE", "900"))
MAX_LINE = 1 << 20
_SEND_MAX = 65536
_CAPACITY_MAX = 65536
_IDLE_TTL_MAX = 86400
_EXITED_TTL_S = 60
_SESSION_KEYS = ("id", "token", "generation", "daemon_token", "pid",
                 "start_time", "argv", "cwd", "capacity", "created_at")

_LOCK = threading.Lock()
_SESSIONS = {}
_STREAMS = {}
_GENERATION = None
_DAEMON_TOKEN = None


# --- daemon-side session state ----------------------------------------

def _public(sess):
    return {"id": sess["id"], "token": sess["token"],
            "generation": _GENERATION, "daemon_token": _DAEMON_TOKEN,
            "pid": sess["proc"].pid, "start_time": sess["start_time"],
            "argv": sess["argv"], "cwd": sess["cwd"],
            "capacity": sess["capacity"],
            "created_at": sess["created_at"], "port": sess["port"]}


def _dropped(sess):
    return sess["next_seq"] - len(sess["buffer"])


def _reader(sess):
    proc = sess["proc"]
    try:
        while True:
            chunk = os.read(proc.stdout.fileno(), 65536)
            if not chunk:
                break
            text = chunk.decode("utf-8", "replace")
            with sess["cond"]:
                sess["next_seq"] += 1
                sess["buffer"].append(
                    {"seq": sess["next_seq"], "ts": time.time(),
                     "text": text})
                sess["cond"].notify_all()
    except Exception:
        pass
    finally:
        try:
            proc.stdout.close()
        except Exception:
            pass
        try:
            proc.wait(timeout=30)
        except Exception:
            try:
                proc.kill()
            except Exception:
                pass
            try:
                proc.wait(timeout=5)
            except Exception:
                pass
        with sess["cond"]:
            sess["exited"] = True
            sess["exit_code"] = proc.returncode
            sess["exited_at"] = time.time()
            sess["cond"].notify_all()


def _spawn(arg):
    v = sc_process.validate_spawn(
        arg.get("argv"), cwd=arg.get("cwd"))
    capacity = arg.get("capacity", 2048)
    idle_ttl = arg.get("idle_ttl_s", 900)
    if (isinstance(capacity, bool) or not isinstance(capacity, int)
            or not 1 <= capacity <= _CAPACITY_MAX):
        return {"ok": False, "status": "rejected",
                "error": f"capacity must be an int in "
                         f"[1, {_CAPACITY_MAX}]"}
    if (isinstance(idle_ttl, bool)
            or not isinstance(idle_ttl, (int, float))
            or not 1 <= idle_ttl <= _IDLE_TTL_MAX):
        return {"ok": False, "status": "rejected",
                "error": f"idle_ttl_s must be in "
                         f"[1, {_IDLE_TTL_MAX}]"}
    kwargs = {"args": v["argv"],
              "cwd": str(v["cwd"]) if v["cwd"] is not None else None,
              "env": v["env"], "stdin": subprocess.PIPE,
              "stdout": subprocess.PIPE, "stderr": subprocess.STDOUT,
              "shell": False, "bufsize": 0}
    if os.name == "nt":
        # CREATE_SUSPENDED closes the spawn->job-assign race: a
        # grandchild cannot escape the Job before assignment.
        kwargs["creationflags"] = (subprocess.CREATE_NEW_PROCESS_GROUP
                                   | 0x00000004)
    else:
        kwargs["start_new_session"] = True
    try:
        proc = subprocess.Popen(**kwargs)
    except Exception as exc:
        return {"ok": False, "error": f"spawn failed: {exc}"}
    try:
        tree = sc_process._assign_tree(proc)
        if os.name == "nt":
            import sc_windows
            sc_windows.resume_main_thread(proc.pid)
    except BaseException as exc:
        try:
            proc.kill()
            proc.wait(timeout=5)
        except Exception:
            pass
        return {"ok": False, "error": f"tree assign failed: {exc}"}
    sess = {"id": uuid.uuid4().hex[:12],
            "token": secrets.token_hex(16), "proc": proc,
            "handle": {"process": proc, "tree": tree},
            "argv": v["argv"],
            "cwd": str(v["cwd"]) if v["cwd"] is not None else None,
            "capacity": capacity, "idle_ttl_s": idle_ttl,
            "created_at": time.time(), "start_time": time.time_ns(),
            "buffer": collections.deque(maxlen=capacity),
            "next_seq": 0, "exited": False, "exit_code": None,
            "exited_at": None, "port": _PORT,
            "last_activity": time.time(),
            "cond": threading.Condition(),
            "reader": None}
    t = threading.Thread(target=_reader, args=(sess,), daemon=True)
    sess["reader"] = t
    try:
        t.start()
    except BaseException as exc:
        try:
            sc_process._reap_tree(sess["handle"], 1)
        except Exception:
            pass
        return {"ok": False, "error": f"reader start failed: {exc}"}
    with _LOCK:
        _SESSIONS[sess["id"]] = sess
    return {"ok": True, "session": _public(sess)}


def _find_session(arg):
    """id + token + live daemon, else rejected. Never dispatches."""
    if not isinstance(arg, dict):
        return None, {"ok": False, "status": "rejected"}
    sess = _SESSIONS.get(arg.get("id"))
    tok = arg.get("token")
    if (sess is None or not isinstance(tok, str)
            or not hmac.compare_digest(sess["token"], tok)):
        return None, {"ok": False, "status": "rejected"}
    return sess, None


def _send(sess, arg):
    if sess["exited"]:
        return {"ok": False, "error": "session exited"}
    data = arg.get("data")
    if not isinstance(data, str) or not data:
        return {"ok": False, "error": "data must be a non-empty string"}
    payload = data.encode("utf-8")
    if len(payload) > _SEND_MAX:
        return {"ok": False, "error": "payload too large"}
    try:
        # Residual: a blocking write of up to 64KB can still stall the
        # single-threaded accept loop if the child never drains stdin.
        n = sess["proc"].stdin.write(payload)
        sess["proc"].stdin.flush()
    except Exception as exc:
        return {"ok": False, "error": f"send failed: {exc}"}
    sess["last_activity"] = time.time()
    return {"ok": True, "delivered": n}


def _recv(sess, arg):
    try:
        cursor = arg.get("cursor")
        if cursor is not None:
            cursor = int(cursor)
        limit = int(arg.get("limit", 200))
        tail = arg.get("tail")
        if tail is not None:
            tail = int(tail)
        timeout_s = float(arg.get("timeout_s", 10))
    except (TypeError, ValueError):
        return {"ok": False, "error": "bad recv numeric arg"}
    if limit < 0 or timeout_s < 0 or (tail is not None and tail < 0):
        return {"ok": False, "error": "bad recv numeric arg"}
    wait = arg.get("wait")
    rx = None
    if wait is not None:
        try:
            rx = re.compile(wait)
        except re.error as exc:
            return {"ok": False, "error": f"bad wait regex: {exc}"}
    deadline = time.time() + min(timeout_s, 60)
    cond = sess["cond"]
    with cond:
        while True:
            recs = [r for r in sess["buffer"]
                    if cursor is None or r["seq"] > cursor]
            matched = None
            if rx is not None:
                matched = bool(rx.search(
                    "".join(r["text"] for r in recs)))
            if rx is None or matched or sess["exited"]:
                break
            remaining = deadline - time.time()
            if remaining <= 0:
                matched = False
                break
            cond.wait(timeout=min(remaining, 0.5))
        if tail is not None:
            recs = recs[-tail:] if tail else []
        else:
            recs = recs[:limit]
        last = recs[-1]["seq"] if recs else (cursor or 0)
        out = {"ok": True, "records": recs, "cursor": last,
               "dropped": _dropped(sess), "exited": sess["exited"],
               "exit_code": sess["exit_code"]}
        if rx is not None:
            out["matched"] = bool(matched)
        sess["last_activity"] = time.time()
        return out


def _cancel(sess):
    try:
        sc_process._reap_tree(sess["handle"], 1)
    except Exception:
        pass
    with sess["cond"]:
        sess["exited"] = True
        sess["exit_code"] = sess["proc"].returncode
        if sess["exited_at"] is None:
            sess["exited_at"] = time.time()
        sess["cond"].notify_all()
    return {"ok": True, "exited": True,
            "exit_code": sess["proc"].returncode}


def _close(sess):
    # Drain pending output briefly, then kill the tree and remove.
    t = sess["reader"]
    if t is not None and not sess["exited"]:
        t.join(timeout=0.5)
    try:
        sc_process._reap_tree(sess["handle"], 2)
    except Exception:
        pass
    if t is not None:
        t.join(timeout=5)
    with sess["cond"]:
        sess["exited"] = True
        sess["exit_code"] = sess["proc"].returncode
        if sess["exited_at"] is None:
            sess["exited_at"] = time.time()
        sess["cond"].notify_all()
    with _LOCK:
        _SESSIONS.pop(sess["id"], None)
    return {"ok": True, "exited": True,
            "exit_code": sess["proc"].returncode,
            "dropped": _dropped(sess)}


# --- daemon-side event stream state -----------------------------------

def _stream_provider(pname):
    """Map a provider name to a zero-arg callable; None is feed-only."""
    if pname in (None, ""):
        return None, None
    if pname != "process":
        return None, {"ok": False, "status": "rejected",
                      "error": f"unknown provider {pname!r}"}
    import sc_backend
    backend = sc_backend.current()
    factory = getattr(backend, "process_event_provider", None)
    if factory is None:
        return None, {"ok": False, "status": "rejected",
                      "error": "backend lacks process events"}
    return factory(), None


def _stream_poller(entry):
    """Tick provider() into feed at interval_s until stop/TTL/close."""
    stream, stop = entry["stream"], entry["stop"]
    import sc_telemetry
    while not stop.is_set() and not stream.closed \
            and not stream.expired:
        try:
            evs = sc_telemetry.provider_output(stream.provider(),
                                               source="daemon")
            if evs:
                stream.feed(evs)
        except Exception as exc:
            try:
                stream.feed([sc_telemetry.normalize(
                    {}, source="daemon", kind="provider.error",
                    severity="error",
                    attrs={"message": str(exc)})])
            except Exception:
                pass
        stop.wait(stream.interval_s)


def _stream_open(arg):
    import sc_telemetry
    provider, err = _stream_provider(arg.get("provider"))
    if err:
        return err
    r = sc_telemetry.open_stream(
        capacity=arg.get("capacity", 1024),
        ttl_s=arg.get("ttl_s", 300), provider=provider,
        interval_s=arg.get("interval_s", 5.0))
    if not r.get("ok"):
        return r
    s = r["stream"]
    s.hosted = True
    entry = {"stream": s, "stop": threading.Event(),
             "poller": None}
    if provider is not None:
        t = threading.Thread(target=_stream_poller, args=(entry,),
                             daemon=True)
        try:
            t.start()
        except BaseException as exc:
            sc_telemetry.close_stream(s.id)
            return {"ok": False,
                    "error": f"poller start failed: {exc}"}
        entry["poller"] = t
    with _LOCK:
        _STREAMS[s.id] = entry
    return {"ok": True, "stream": s.meta()}


def _stream_close(stream_id):
    import sc_telemetry
    with _LOCK:
        entry = _STREAMS.pop(stream_id, None)
    if entry is not None:
        entry["stop"].set()
        t = entry["poller"]
        if t is not None:
            t.join(timeout=2)
    return sc_telemetry.close_stream(stream_id)


def _stream_op(op, arg):
    import sc_telemetry
    _reap_streams()
    if op == "stream.open":
        if not isinstance(arg, dict):
            return {"ok": False, "status": "rejected"}
        return _stream_open(arg)
    if op == "stream.list":
        return {"ok": True,
                "streams": [e["stream"].meta()
                            for e in list(_STREAMS.values())
                            if not e["stream"].closed
                            and not e["stream"].expired]}
    sid = arg.get("id") if isinstance(arg, dict) else None
    if op == "stream.drain":
        if not isinstance(sid, str):
            return {"ok": False, "status": "rejected"}
        return sc_telemetry.drain(sid, cursor=arg.get("cursor"),
                                  limit=arg.get("limit", 100))
    if op == "stream.close":
        if not isinstance(sid, str):
            return {"ok": False, "status": "rejected"}
        return _stream_close(sid)
    return {"ok": False, "error": f"unknown op {op!r}"}


def _reap_streams():
    for sid, entry in list(_STREAMS.items()):
        s = entry["stream"]
        if s.closed or s.expired:
            try:
                _stream_close(sid)
            except Exception:
                pass


def _op(env):
    op = env.get("op")
    arg = env.get("arg") or {}
    if op == "status":
        return {"ok": True, "generation": _GENERATION,
                "sessions": len(_SESSIONS),
                "streams": len(_STREAMS)}
    if op.startswith("stream."):
        return _stream_op(op, arg)
    if op == "list":
        return {"ok": True,
                "sessions": [_public(s) for s in
                             list(_SESSIONS.values())]}
    if op == "spawn":
        try:
            return _spawn(arg)
        except contract.InvalidRequest as exc:
            return {"ok": False, "status": "rejected",
                    "error": str(exc)}
    if op == "resize":
        sess, err = _find_session(arg)
        if err:
            return err
        return {"ok": False,
                "error": "unsupported: session has no PTY"}
    if op == "stop":
        return {"ok": True, "stopped": True}
    if op in ("send", "recv", "close", "cancel", "session_status"):
        sess, err = _find_session(arg)
        if err:
            return err
        if op == "send":
            return _send(sess, arg)
        if op == "recv":
            return _recv(sess, arg)
        if op == "close":
            return _close(sess)
        if op == "cancel":
            return _cancel(sess)
        return {"ok": True, "session": _public(sess),
                "exited": sess["exited"],
                "exit_code": sess["exit_code"]}
    return {"ok": False, "error": f"unknown op {op!r}"}


# --- daemon entrypoint -------------------------------------------------

def _write_pidfile(port):
    data = {"pid": os.getpid(), "port": port,
            "generation": _GENERATION, "daemon_token": _DAEMON_TOKEN,
            "started": time.time()}
    _atomic_write(PIDFILE, data)


def _atomic_write(path, data):
    """Owner-only atomic write: mkstemp sibling (0o600), fsync, replace."""
    fd, tmp = tempfile.mkstemp(dir=os.path.dirname(path) or ".",
                               prefix=".sc-sessions-")
    try:
        try:
            os.chmod(tmp, 0o600)
        except OSError:
            pass
        with os.fdopen(fd, "w", encoding="utf-8") as fh:
            json.dump(data, fh)
            fh.flush()
            os.fsync(fh.fileno())
        os.replace(tmp, path)
    except BaseException:
        try:
            os.unlink(tmp)
        except OSError:
            pass
        raise


def _reap_idle_sessions():
    now = time.time()
    for sess in list(_SESSIONS.values()):
        if sess["exited"]:
            exited_at = sess["exited_at"] or sess["last_activity"]
            if now - exited_at > _EXITED_TTL_S:
                try:
                    _close(sess)
                except Exception:
                    pass
        elif now - sess["last_activity"] > sess["idle_ttl_s"]:
            _cancel(sess)


def _handle_conn(c):
    """One request per connection. Returns (response, stop_flag)."""
    try:
        c.settimeout(30)
        data = b""
        deadline = time.monotonic() + 30
        while not data.endswith(b"\n"):
            if len(data) > MAX_LINE:
                return {"ok": False, "error": "request too large"}, False
            if time.monotonic() >= deadline:
                return {"ok": False, "error": "read timeout"}, False
            chunk = c.recv(65536)
            if not chunk:
                break
            data += chunk
        if len(data) > MAX_LINE:
            return {"ok": False, "error": "request too large"}, False
        try:
            env = json.loads(data.decode("utf-8"))
        except (ValueError, UnicodeError):
            return {"ok": False, "error": "malformed request"}, False
        if not isinstance(env, dict):
            return {"ok": False, "error": "malformed request"}, False
        if env.get("op") == "ping":
            return {"ok": True, "generation": _GENERATION}, False
        # Fail closed: wrong/missing token or foreign generation is
        # rejected before any dispatch.
        tok = env.get("daemon_token")
        if (env.get("generation") != _GENERATION
                or not isinstance(tok, str)
                or not hmac.compare_digest(_DAEMON_TOKEN, tok)):
            return {"ok": False, "status": "rejected"}, False
        resp = _op(env)
        return resp, env.get("op") == "stop"
    except socket.timeout:
        return {"ok": False, "error": "read timeout"}, False
    except Exception as exc:
        return {"ok": False, "error": f"request failed: {exc}"}, False


_PORT = 0


def daemon_main(pidfile=None, idle_ttl_s=None):
    global _GENERATION, _DAEMON_TOKEN, _PORT, PIDFILE, IDLE_TTL_S
    if pidfile:
        PIDFILE = pidfile
    if idle_ttl_s is not None:
        IDLE_TTL_S = float(idle_ttl_s)
    _GENERATION = uuid.uuid4().hex
    _DAEMON_TOKEN = secrets.token_hex(16)
    srv = socket.socket()
    srv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    srv.bind(("127.0.0.1", 0))
    srv.listen(8)
    srv.settimeout(1.0)
    _PORT = srv.getsockname()[1]
    _write_pidfile(_PORT)
    last = time.time()
    stopping = False
    try:
        while not stopping and time.time() - last < IDLE_TTL_S:
            try:
                c, _ = srv.accept()
            except socket.timeout:
                _reap_idle_sessions()
                _reap_streams()
                continue
            except OSError:
                break
            with c:
                try:
                    resp, stopping = _handle_conn(c)
                    c.sendall(json.dumps(resp).encode() + b"\n")
                except Exception:
                    pass
            last = time.time()
    finally:
        srv.close()
        for sid in list(_STREAMS):
            try:
                _stream_close(sid)
            except Exception:
                pass
        for sess in list(_SESSIONS.values()):
            try:
                _close(sess)
            except Exception:
                pass
        try:
            os.remove(PIDFILE)
        except OSError:
            pass


# --- client surface ----------------------------------------------------

def _read_pidfile():
    try:
        with open(PIDFILE, encoding="utf-8") as fh:
            d = json.load(fh)
        if (isinstance(d, dict) and isinstance(d.get("pid"), int)
                and isinstance(d.get("port"), int)):
            return d
    except Exception:
        pass
    return None


def _pid_alive(pid):
    try:
        if os.name == "nt":
            import ctypes
            h = ctypes.windll.kernel32.OpenProcess(0x1000, False, pid)
            if not h:
                return False
            ctypes.windll.kernel32.CloseHandle(h)
            return True
        os.kill(pid, 0)
        # A zombie (dead child never waitpid'ed) still answers signal-0.
        # waitpid reaps it only if it is ours; ChildProcessError means a
        # foreign process — kill() already proved it exists.
        try:
            if os.waitpid(pid, os.WNOHANG)[0] == pid:
                return False
        except OSError:
            pass
        return True
    except Exception:
        return False


def _rpc(port, env, timeout=30):
    try:
        s = socket.create_connection(("127.0.0.1", port),
                                     timeout=timeout)
        with s:
            s.sendall(json.dumps(env).encode() + b"\n")
            data = b""
            while not data.endswith(b"\n"):
                if len(data) > MAX_LINE:
                    return {"ok": False, "error": "response too large"}
                chunk = s.recv(65536)
                if not chunk:
                    break
                data += chunk
        return json.loads(data.decode("utf-8"))
    except Exception as exc:
        return {"ok": False, "error": f"sessions daemon: {exc}"}


def _authed(op, arg=None, session=None, timeout=30):
    """Build an authenticated envelope from pidfile or session dict."""
    d = _read_pidfile()
    if session is not None:
        # Fail closed before any socket IO: a session dict is bound to
        # the daemon generation that spawned it. If the pidfile is gone
        # or names a different generation, the stored port is stale (or
        # foreign) — never connect to it.
        if d is None or d.get("generation") != session["generation"]:
            return {"ok": False, "status": "rejected",
                    "error": "stale daemon generation"}
        port, gen, tok = d["port"], d["generation"], \
            session["daemon_token"]
    else:
        if d is None:
            return {"ok": False, "error": "sessions daemon not running"}
        port, gen, tok = d["port"], d.get("generation"), \
            d.get("daemon_token")
    env = {"op": op, "arg": arg or {},
           "generation": gen, "daemon_token": tok}
    return _rpc(port, env, timeout=timeout)


def _valid_session(session):
    """Required keys before any socket IO; returns an error dict or None."""
    if not isinstance(session, dict):
        return {"ok": False, "status": "rejected",
                "error": "invalid session dict"}
    for key in _SESSION_KEYS:
        if key not in session:
            return {"ok": False, "status": "rejected",
                    "error": f"session missing key: {key}"}
    if (not isinstance(session["id"], str)
            or not isinstance(session["token"], str)
            or not isinstance(session["generation"], str)
            or not isinstance(session["daemon_token"], str)
            or isinstance(session["pid"], bool)
            or not isinstance(session["pid"], int)):
        return {"ok": False, "status": "rejected",
                "error": "invalid session dict"}
    return None


def start_daemon():
    """Start the sessions daemon; no-op if a live one answers ping.

    A pidfile whose pid is alive but unreachable is never deleted or
    respawned over — that would orphan a live daemon's sessions.
    """
    # Alive-but-unreachable may mean mid-shutdown: the daemon acks stop,
    # then closes the socket, reaps sessions, and removes the pidfile
    # last. Wait for it instead of orphaning a live daemon or racing its
    # pidfile; a different generation appearing means a new daemon won
    # the race — ping that one.
    deadline = time.time() + 15
    while True:
        d = _read_pidfile()
        if d is not None and _pid_alive(d["pid"]):
            r = _rpc(d["port"], {"op": "ping"}, timeout=5)
            if r.get("ok"):
                return {"ok": True, "started": False,
                        "daemon": {"pid": d["pid"], "port": d["port"],
                                   "generation": d.get("generation")}}
            if time.time() >= deadline:
                return {"ok": False,
                        "error": "daemon busy or unresponsive"}
            time.sleep(0.1)
            continue
        if d is not None:
            try:  # stale pidfile: dead pid
                os.remove(PIDFILE)
            except OSError:
                pass
        break
    kw = {"stdout": subprocess.DEVNULL, "stderr": subprocess.DEVNULL,
          "stdin": subprocess.DEVNULL, "close_fds": True}
    if os.name == "nt":
        kw["creationflags"] = (
            getattr(subprocess, "DETACHED_PROCESS", 0)
            | getattr(subprocess, "CREATE_NEW_PROCESS_GROUP", 0)
            | getattr(subprocess, "CREATE_NO_WINDOW", 0))
    else:
        kw["start_new_session"] = True
    subprocess.Popen([sys.executable,
                      os.path.abspath(__file__), "--daemon",
                      PIDFILE, str(IDLE_TTL_S)], **kw)
    deadline = time.time() + 5
    while time.time() < deadline:
        d = _read_pidfile()
        if d is not None:
            if not _pid_alive(d["pid"]):
                time.sleep(0.05)
                continue
            r = _rpc(d["port"], {"op": "ping"}, timeout=5)
            if r.get("ok"):
                return {"ok": True, "started": True,
                        "daemon": {"pid": d["pid"], "port": d["port"],
                                   "generation": d.get("generation")}}
        time.sleep(0.05)
    return {"ok": False, "error": "daemon did not write pidfile"}


def daemon_status():
    d = _read_pidfile()
    if d is None or not _pid_alive(d["pid"]):
        if d is not None:
            try:
                os.remove(PIDFILE)
            except OSError:
                pass
        return {"ok": True, "running": False, "generation": None,
                "daemon": None, "sessions": 0}
    r = _authed("status")
    if not r.get("ok"):
        return {"ok": True, "running": False, "generation": None,
                "daemon": None, "sessions": 0}
    return {"ok": True, "running": True,
            "generation": r.get("generation"),
            "daemon": {"pid": d["pid"], "port": d["port"],
                       "generation": d.get("generation")},
            "sessions": r.get("sessions", 0)}


def stop_daemon():
    d = _read_pidfile()
    if d is None or not _pid_alive(d["pid"]):
        if d is not None:
            try:
                os.remove(PIDFILE)
            except OSError:
                pass
        return {"ok": True, "running": False}
    r = _authed("stop")
    if not r.get("ok"):
        # Daemon is alive but unreachable: report truthfully, keep the
        # pidfile so a later stop/status can still find it.
        return {"ok": False, "running": True, "stopped": False,
                "error": r.get("error", "stop failed")}
    return {"ok": True, "stopped": True}


def list_sessions():
    d = _read_pidfile()
    if d is None or not _pid_alive(d["pid"]):
        return {"ok": True, "running": False, "sessions": []}
    r = _authed("list")
    if r.get("ok"):
        r["running"] = True
    return r


def spawn_session(argv, *, cwd=None, capacity=2048, idle_ttl_s=900):
    try:
        sc_process.validate_spawn(argv, cwd=cwd)
    except contract.InvalidRequest as exc:
        return {"ok": False, "status": "rejected", "error": str(exc)}
    st = start_daemon()
    if not st.get("ok"):
        return st
    return _authed("spawn", {"argv": list(argv), "cwd": cwd,
                             "capacity": capacity,
                             "idle_ttl_s": idle_ttl_s})


def send(session, data):
    err = _valid_session(session)
    if err:
        return err
    if not isinstance(data, str) or not data:
        return {"ok": False, "status": "rejected",
                "error": "data must be a non-empty string"}
    if len(data.encode("utf-8")) > _SEND_MAX:
        return {"ok": False, "status": "rejected",
                "error": "payload too large"}
    return _authed("send", {"id": session["id"],
                            "token": session["token"], "data": data},
                   session=session)


def recv(session, *, cursor=None, limit=200, tail=None, wait=None,
         timeout_s=10):
    err = _valid_session(session)
    if err:
        return err
    arg = {"id": session["id"], "token": session["token"],
           "limit": limit, "timeout_s": timeout_s}
    if cursor is not None:
        arg["cursor"] = cursor
    if tail is not None:
        arg["tail"] = tail
    if wait is not None:
        arg["wait"] = wait
    return _authed("recv", arg, session=session,
                   timeout=min(float(timeout_s), 60) + 15)


def resize(session, cols, rows):
    err = _valid_session(session)
    if err:
        return err
    return _authed("resize", {"id": session["id"],
                              "token": session["token"],
                              "cols": cols, "rows": rows},
                   session=session)


def close(session):
    err = _valid_session(session)
    if err:
        return err
    return _authed("close", {"id": session["id"],
                             "token": session["token"]},
                   session=session)


def cancel(session):
    err = _valid_session(session)
    if err:
        return err
    return _authed("cancel", {"id": session["id"],
                              "token": session["token"]},
                   session=session)


if __name__ == "__main__":
    if "--daemon" in sys.argv:
        i = sys.argv.index("--daemon")
        daemon_main(*sys.argv[i + 1:i + 3])
