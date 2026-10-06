# OpenDots Adaptations Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use /dispatching-parallel-agents (recommended) or /execution to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Port the three OpenDots patterns worth having (agent-owned browser, action audit, screencast watch) plus two doc-shaped borrowings (scheduled turns, publish-gated self-improvement) into devin-bundle.

**Spec:**
- What/why (tech-agnostic): agents keep browser logins without borrowing the user's browser; every computer action leaves a forensic trail; the agent can watch a bound browser event-driven instead of polling screenshots; recurring automation runs on an OS schedule; self-improvement proposals wait for human publish.
- User stories: (1) As an agent I want my own persistent browser profile so cookies/logins survive without touching the user's browser. (2) As a reviewer I want an append-only record of every dispatched action so post-hoc forensics and refine evidence exist. (3) As an agent I want frame-on-change reperception of the bound browser so verify loops stop polling screenshots. (4) As a user I want scheduled one-shot agent turns without a daemon. (5) As a user I want self-improvement proposals to wait for my publish before applying.
- Acceptance criteria: `browser.py launch --profile X` leaves a bound agent-owned Chromium whose profile survives a stop/launch cycle; `cu_actions.result()` appends one JSONL record per call; `browser.py watch` writes screencast frames to disk on change; `skills/scheduled-turns/SKILL.md` passes `scripts/validate-skill-format.py`; `pytest -q` and `python audit.py` stay green.

**Architecture:** Reuse existing seams only. `launch` spawns a Chromium with `--remote-debugging-port` + `--user-data-dir`, discovers the real browser pid via CDP `SystemInfo.getProcessInfo`, then calls the existing `cu_browser.bind()`. `watch` rides the existing `_WSClient` reader thread + bounded events deque; `Page.screencastFrame` events already land there, so we only add ACK plus a file sink. Audit hooks `cu_actions.result()`, the single funnel every action result already passes through.

**Tech Stack:** Python 3.9+ stdlib + `websocket-client` (already required); pytest; no new dependencies.

## Global Constraints

- Manifest rules: Python stdlib only in `scripts/`; extension deps need `requirements.txt`; no new deps without user approval (`.devin/ARCHITECTURE_MANIFEST.md` §3).
- Result contract: `status` in {verified, dispatched, rejected, timeout, unknown, cancelled}; `ok:false` only when nothing dispatched (`cu_actions.py`).
- Audit MUST exclude typed values, file contents, and full commands, matching OpenDots' audit exclusion rule (docs/COMPUTERS.md).
- Loopback endpoints only; `bind()` already enforces (`cu_browser.py:131`).
- Secrets never in argv, logs, profile dir names, or JSONL (AGENTS.md Rule 19).
- `pytest -q` + `python audit.py` green before every commit (manifest §4).
- BiDi browsers (Firefox/Zen): screencast is CDP-only. Typed rejection, never a fake fallback.
- No AI signatures in any artifact (Rule 2). No em-dashes in written prose (pre-write-guard hook is active).

## Proposed Modules and Interfaces

- `extensions/computer-use/browser.py`: new subcommands `launch`/`stop` (T1) and `watch` (T2).
- `extensions/computer-use/cu_browser.py`: new functions `find_browser_exe()`, `profile_root()`, `launch_owned(profile, timeout_s)`, `launched()`, `stop_owned()`, `watch_frames(cli, seconds, out_dir, max_frames, last_only)`; new constant `LAUNCHED_PATH`.
- `extensions/computer-use/cu_audit.py` (NEW, living): `enabled()`, `audit_path()`, `record(entry)` (append + rotate).
- `extensions/computer-use/cu_actions.py`: `result()` gains one `cu_audit.record(...)` call.
- `extensions/computer-use/USAGE.md`: document `launch`/`stop`/`watch`, audit file, env vars.
- `skills/scheduled-turns/SKILL.md` (NEW, living): recipe only, no shipped scripts.
- `skills/self-improvement/SKILL.md`: one section added (proposal queue + human publish).
- Tests: `tests/test_cu_browser_launch.py`, `tests/test_cu_browser_watch.py`, `tests/test_cu_audit.py`, `tests/test_scheduled_turns_skill.py`, `tests/test_self_improvement_publish_gate.py`.

Dropped items (recorded so nobody re-adds silently): B4 per-subagent permission matrix, since `agents/*.md` `allowed-tools:` frontmatter already scopes tools per profile and ephemeral CLI subagents have no mid-run revocation surface. B12 takeover/handback, deferred until B11 lands and remote viewing is actually used.

---

### Task 1: `browser.py launch`/`stop` (agent-owned persistent browser)

**Files:**
- Modify: `extensions/computer-use/cu_browser.py` (add functions at end of file)
- Modify: `extensions/computer-use/browser.py` (add `launch`, `stop` subparsers + dispatch)
- Modify: `extensions/computer-use/USAGE.md` (new section under "Bound-browser commands")
- Test: `tests/test_cu_browser_launch.py`

**Interfaces:**
- Consumes: `cu_browser.bind(endpoint: str, pid: int) -> dict` (`cu_browser.py:125`); `_WSClient.call(method, params)`; existing temp-state pattern `EVENTS_PATH = tempdir/devin-cu-bevents.json` (`browser.py:21`).
- Produces:
  - `find_browser_exe() -> str | None`: `CU_BROWSER_EXE` env, then `shutil.which` for chrome/chromium/msedge/brave, then OS install dirs (`%PROGRAMFILES%\Google\Chrome\Application\chrome.exe`, `%LOCALAPPDATA%\Google\Chrome\Application\chrome.exe`, `%PROGRAMFILES(X86)%\Microsoft\Edge\Application\msedge.exe`, `%PROGRAMFILES%\Microsoft\Edge\Application\msedge.exe`).
  - `profile_root() -> str`: `$CU_PROFILE_ROOT` or `%LOCALAPPDATA%\devin\cu-profiles` (Windows) / `~/.local/share/devin-cu/profiles` (POSIX).
  - `launch_owned(profile: str, timeout_s: float = 15.0) -> dict`: returns `{"ok": True, "pid": int, "endpoint": str, "profile_dir": str, "binding": {...}}` or `{"ok": False, "error": <typed reason>}`; typed errors: `bad_profile_name`, `browser_exe_not_found`, `browser_spawn_failed:<e>`, `browser_start_timeout`, `process_info_failed`.
  - `launched() -> dict | None`: reads `LAUNCHED_PATH` if the recorded pid is alive.
  - `stop_owned() -> dict`: kills only the recorded pid when it is still alive; `not_owned:*` when the record is missing or the pid is dead; never kills a browser it did not launch.
  - `LAUNCHED_PATH = os.path.join(tempfile.gettempdir(), "devin-cu-launched.json")`

- [ ] **Step 1: Write the failing test**

```python
"""browser.py launch/stop: agent-owned Chromium lifecycle."""
import io, json, os, sys
from contextlib import redirect_stdout
import pytest

sys.path.insert(0, os.path.dirname(__file__))
import cu_load  # noqa: E402

br = cu_load.load("cu_browser")
cli_mod = cu_load.load("browser")


def test_find_browser_exe_env_wins(monkeypatch):
    monkeypatch.setenv("CU_BROWSER_EXE", "/x/fake-chrome")
    assert br.find_browser_exe() == "/x/fake-chrome"


def test_launch_records_ownership_and_binds(monkeypatch, tmp_path):
    monkeypatch.setattr(br, "find_browser_exe", lambda: "/x/chrome")
    monkeypatch.setattr(br, "_spawn_browser",
                        lambda exe, port, udd: {"pid": 4321, "proc": object()})
    monkeypatch.setattr(br, "_browser_pid_via_cdp",
                        lambda endpoint, timeout: 4321)
    monkeypatch.setattr(br, "_wait_devtools", lambda ep, t: True)
    monkeypatch.setattr(br, "_free_port", lambda: 49999)
    monkeypatch.setattr(br, "profile_root", lambda: str(tmp_path))
    bound = {}
    def _bind(ep, pid):
        bound["hit"] = (ep, pid)
        return {"ok": True}
    monkeypatch.setattr(br, "bind", _bind)
    monkeypatch.setattr(br, "LAUNCHED_PATH", str(tmp_path / "launched.json"))
    r = br.launch_owned("work")
    assert r["ok"] and r["pid"] == 4321 and r["endpoint"].endswith("49999")
    assert bound["hit"] == (r["endpoint"], 4321)
    assert json.loads(open(br.LAUNCHED_PATH).read())["pid"] == 4321


def test_stop_refuses_foreign_pid(monkeypatch, tmp_path):
    monkeypatch.setattr(br, "LAUNCHED_PATH", str(tmp_path / "x.json"))
    open(br.LAUNCHED_PATH, "w").write(json.dumps({"pid": 1}))
    monkeypatch.setattr(br, "_pid_alive", lambda pid: False)
    monkeypatch.setattr(br, "binding", lambda: None)
    r = br.stop_owned()
    assert r["ok"] is False and r["error"].startswith("not_owned")


def test_launch_cli_json(monkeypatch, tmp_path):
    monkeypatch.setattr(br, "launch_owned",
                        lambda profile, timeout_s=15.0:
                            {"ok": True, "pid": 9, "endpoint": "e",
                             "profile_dir": "d", "binding": {}})
    buf = io.StringIO()
    old = sys.argv
    sys.argv = ["browser.py", "launch", "--profile", "work"]
    try:
        with redirect_stdout(buf):
            cli_mod.main()
    finally:
        sys.argv = old
    out = json.loads(buf.getvalue())
    assert out["ok"] and out["pid"] == 9
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_cu_browser_launch.py -v`
Expected: FAIL, `AttributeError: module has no attribute 'launch_owned'`

- [ ] **Step 3: Implement `cu_browser` helpers**

Append to `cu_browser.py` (imports already present: os, json, time, tempfile,
socket, subprocess):

```python
LAUNCHED_PATH = os.path.join(tempfile.gettempdir(),
                             "devin-cu-launched.json")


def find_browser_exe():
    exe = os.environ.get("CU_BROWSER_EXE")
    if exe:
        return exe
    import shutil
    for name in ("chrome", "chromium", "chromium-browser",
                 "google-chrome", "msedge", "brave"):
        hit = shutil.which(name)
        if hit:
            return hit
    if os.name == "nt":
        roots = [os.environ.get("PROGRAMFILES", ""),
                 os.environ.get("PROGRAMFILES(X86)", ""),
                 os.environ.get("LOCALAPPDATA", "")]
        rels = [r"Google\Chrome\Application\chrome.exe",
                r"Microsoft\Edge\Application\msedge.exe"]
        for root in roots:
            for rel in rels:
                p = os.path.join(root, rel)
                if os.path.isfile(p):
                    return p
    for p in ("/usr/bin/google-chrome", "/usr/bin/chromium",
              "/snap/bin/chromium",
              "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"):
        if os.path.isfile(p):
            return p
    return None


def profile_root():
    root = os.environ.get("CU_PROFILE_ROOT")
    if root:
        return root
    if os.name == "nt":
        return os.path.join(os.environ.get("LOCALAPPDATA",
                                           tempfile.gettempdir()),
                            "devin", "cu-profiles")
    return os.path.join(os.path.expanduser("~"), ".local", "share",
                        "devin-cu", "profiles")


def _free_port():
    s = socket.socket()
    s.bind(("127.0.0.1", 0))
    port = s.getsockname()[1]
    s.close()
    return port


def _spawn_browser(exe, port, udd):
    os.makedirs(udd, exist_ok=True)
    flags = getattr(subprocess, "DETACHED_PROCESS", 0) | \
        getattr(subprocess, "CREATE_NO_WINDOW", 0)
    kw = dict(stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
              stdin=subprocess.DEVNULL, close_fds=True)
    if flags:
        kw["creationflags"] = flags
    else:
        kw["start_new_session"] = True
    proc = subprocess.Popen(
        [exe, "--remote-debugging-port=" + str(port),
         "--user-data-dir=" + udd, "--no-first-run",
         "--no-default-browser-check", "about:blank"], **kw)
    return {"pid": proc.pid, "proc": proc}


def _wait_devtools(endpoint, timeout_s):
    deadline = time.time() + timeout_s
    while time.time() < deadline:
        try:
            _http_json(endpoint + "/json/version", timeout=1.0)
            return True
        except Exception:
            time.sleep(0.2)
    return False


def _browser_pid_via_cdp(endpoint, timeout_s):
    """Real browser-process pid via CDP SystemInfo.getProcessInfo. The
    spawned launcher may hand off to a different browser process."""
    info = _http_json(endpoint + "/json/list", timeout=2.0)
    page = next((t for t in info if t.get("type") == "page"), info[0])
    ws = _WSClient(page["webSocketDebuggerUrl"], "cdp", timeout=5.0)
    try:
        r = ws.call("SystemInfo.getProcessInfo")
        for p in (r or {}).get("processInfo", []):
            if p.get("type") == "browser":
                return p.get("id")
        return None
    finally:
        ws.close()


def _pid_alive(pid):
    if os.name == "nt":
        import ctypes
        h = ctypes.windll.kernel32.OpenProcess(0x1000, False, pid)
        if not h:
            return False
        ctypes.windll.kernel32.CloseHandle(h)
        return True
    try:
        os.kill(pid, 0)
        return True
    except OSError:
        return False


def launched():
    try:
        with open(LAUNCHED_PATH, encoding="utf-8") as f:
            d = json.load(f)
    except Exception:
        return None
    if not _pid_alive(d.get("pid", 0)):
        return None
    return d


def launch_owned(profile, timeout_s=15.0):
    if (not profile or "/" in profile or "\\" in profile
            or profile in (".", "..") or len(profile) > 64):
        return {"ok": False, "error": "bad_profile_name"}
    exe = find_browser_exe()
    if not exe:
        return {"ok": False, "error": "browser_exe_not_found"}
    port = _free_port()
    udd = os.path.join(profile_root(), profile)
    try:
        spawned = _spawn_browser(exe, port, udd)
    except OSError as e:
        return {"ok": False, "error": "browser_spawn_failed:" + str(e)}
    endpoint = "http://127.0.0.1:" + str(port)
    if not _wait_devtools(endpoint, timeout_s):
        return {"ok": False, "error": "browser_start_timeout",
                "pid": spawned["pid"]}
    pid = _browser_pid_via_cdp(endpoint, timeout_s)
    if not pid:
        return {"ok": False, "error": "process_info_failed"}
    b = bind(endpoint, pid)
    if not b.get("ok"):
        return b
    rec = {"pid": pid, "endpoint": endpoint, "profile": profile,
           "profile_dir": udd, "created_at": time.time()}
    tmp = LAUNCHED_PATH + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(rec, f)
    os.replace(tmp, LAUNCHED_PATH)
    return {"ok": True, "pid": pid, "endpoint": endpoint,
            "profile_dir": udd, "binding": b.get("binding", {})}


def stop_owned():
    d = launched()
    if d is None:
        try:
            os.remove(LAUNCHED_PATH)
        except OSError:
            pass
        return {"ok": False, "error": "not_owned:no live launched record"}
    pid = d["pid"]
    b = binding()
    if b and b.get("pid") == pid:
        unbind()
    if os.name == "nt":
        subprocess.run(["taskkill", "/PID", str(pid), "/T", "/F"],
                       capture_output=True)
    else:
        try:
            os.kill(pid, 15)
        except OSError:
            pass
    try:
        os.remove(LAUNCHED_PATH)
    except OSError:
        pass
    return {"ok": True, "stopped": pid}
```

- [ ] **Step 4: Wire CLI subcommands in `browser.py`**

In `main()` parser block (after the `pin` parser, ~line 213) add:

```python
    l = sub.add_parser("launch")
    l.add_argument("--profile", required=True)
    l.add_argument("--timeout", type=float, default=15.0)
    sub.add_parser("stop")
```

In the dispatch block (after the `status` handler, ~line 246) add:

```python
    if args.cmd == "launch":
        print(json.dumps(cu_browser.launch_owned(args.profile,
                                               args.timeout)))
        return
    if args.cmd == "stop":
        print(json.dumps(cu_browser.stop_owned()))
        return
```

Both paths run before `cli = _client()` since launch/stop must work
unbound.

- [ ] **Step 5: Run test to verify it passes**

Run: `pytest tests/test_cu_browser_launch.py -v`
Expected: 4 PASSED

- [ ] **Step 6: Document in USAGE.md + commit**

Add under "Bound-browser commands" (after the `unbind` example):

```markdown
`launch` spawns an agent-owned Chromium with a persistent profile:
cookies/logins survive `stop`/`launch` cycles because the user-data-dir
is stable (`$CU_PROFILE_ROOT` or `%LOCALAPPDATA%\devin\cu-profiles`).
`stop` kills only a pid recorded by `launch` and still alive; it refuses
foreign pids. The spawned browser binds to this session like any `bind`
(same TTL + session rules).
```

```bash
git add extensions/computer-use/cu_browser.py extensions/computer-use/browser.py extensions/computer-use/USAGE.md tests/test_cu_browser_launch.py
git commit -m "feat(computer-use): agent-owned persistent browser via launch/stop"
```

---

### Task 2: `browser.py watch` (CDP screencast frames to disk)

**Files:**
- Modify: `extensions/computer-use/cu_browser.py` (add `watch_frames`)
- Modify: `extensions/computer-use/browser.py` (add `watch` subparser + dispatch)
- Modify: `extensions/computer-use/USAGE.md` (watch section)
- Test: `tests/test_cu_browser_watch.py`

**Interfaces:**
- Consumes: `_cdp_client()` -> `BrowserClient`; `cli._ws` (`_WSClient` with `call()`, `start_reader()`, `events` deque, `close()`); `cli.dialect`.
- Produces: `watch_frames(cli, seconds, out_dir, max_frames=100, last_only=False) -> {"ok","frames","dir","last"}`. Frame files `frame-0001.jpg` (or `latest.jpg` when `last_only`). Typed errors: `screencast_cdp_only`, `no_binding`.

- [ ] **Step 1: Write the failing test**

```python
"""browser.py watch: CDP screencast -> jpeg frames on disk."""
import base64, io, json, os, sys
from contextlib import redirect_stdout
import pytest

sys.path.insert(0, os.path.dirname(__file__))
import cu_load  # noqa: E402

br = cu_load.load("cu_browser")
cli_mod = cu_load.load("browser")

FRAME = base64.b64encode(b"\xff\xd8fakejpeg").decode()


class FakeWS:
    def __init__(self, frames):
        import collections
        self.dialect = "cdp"
        self.events = collections.deque(frames)
        self.sent = []

    def call(self, method, params=None, timeout=None):
        self.sent.append((method, params))
        return {}

    def start_reader(self):
        pass

    def close(self):
        pass


class FakeCli:
    def __init__(self, ws, dialect="cdp"):
        self._ws = ws
        self.dialect = dialect
        self.endpoint = "x"


def _frame(i):
    return {"method": "Page.screencastFrame",
            "params": {"data": FRAME, "sessionId": i,
                       "metadata": {"deviceWidth": 10,
                                    "deviceHeight": 10}}}


def test_watch_writes_frames_and_acks(monkeypatch, tmp_path):
    ws = FakeWS([_frame(1), _frame(2)])
    cli = FakeCli(ws)
    r = br.watch_frames(cli, seconds=0.1, out_dir=str(tmp_path))
    assert r["ok"] and r["frames"] == 2
    assert os.path.isfile(tmp_path / "frame-0001.jpg")
    acks = [m for m, p in ws.sent if m == "Page.screencastFrameAck"]
    assert len(acks) == 2
    sent_methods = [m for m, _ in ws.sent]
    assert "Page.startScreencast" in sent_methods
    assert "Page.stopScreencast" in sent_methods


def test_watch_rejects_bidi(tmp_path):
    cli = FakeCli(FakeWS([]), dialect="bidi")
    r = br.watch_frames(cli, seconds=0.1, out_dir=str(tmp_path))
    assert r["ok"] is False and r["error"] == "screencast_cdp_only"


def test_watch_last_only(tmp_path):
    ws = FakeWS([_frame(1), _frame(2)])
    r = br.watch_frames(FakeCli(ws), seconds=0.1,
                        out_dir=str(tmp_path), last_only=True)
    assert r["ok"] and os.path.isfile(tmp_path / "latest.jpg")
    assert not os.path.isfile(tmp_path / "frame-0001.jpg")
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_cu_browser_watch.py -v`
Expected: FAIL, `AttributeError: ... 'watch_frames'`

- [ ] **Step 3: Implement `watch_frames`**

Append to `cu_browser.py`:

```python
def watch_frames(cli, seconds, out_dir, max_frames=100, last_only=False):
    """CDP screencast -> jpeg files. Chrome pushes one frame per page
    change; every frame MUST be acked or Chrome stalls (the pattern in
    OpenBot's screencast.ts). BiDi has no equivalent: typed rejection."""
    if cli.dialect != "cdp":
        return {"ok": False, "error": "screencast_cdp_only"}
    import base64
    os.makedirs(out_dir, exist_ok=True)
    ws = cli._ws
    ws.start_reader()
    ws.call("Page.startScreencast",
            {"format": "jpeg", "quality": 70,
             "maxWidth": 1280, "maxHeight": 800, "everyNthFrame": 1})
    written = 0
    latest = None
    deadline = time.time() + seconds
    try:
        while time.time() < deadline and written < max_frames:
            pulled = False
            while ws.events:
                pulled = True
                ev = ws.events.popleft()
                if ev.get("method") != "Page.screencastFrame":
                    continue
                p = ev["params"]
                ws.call("Page.screencastFrameAck",
                        {"sessionId": p["sessionId"]})
                written += 1
                raw = base64.b64decode(p["data"])
                if last_only:
                    latest = raw
                else:
                    path = os.path.join(
                        out_dir, "frame-%04d.jpg" % written)
                    with open(path, "wb") as f:
                        f.write(raw)
            if not pulled:
                time.sleep(0.05)
    finally:
        try:
            ws.call("Page.stopScreencast")
        except Exception:
            pass
    if last_only and latest is not None:
        with open(os.path.join(out_dir, "latest.jpg"), "wb") as f:
            f.write(latest)
    return {"ok": True, "frames": written, "dir": out_dir,
            "last": (os.path.join(out_dir, "latest.jpg")
                     if last_only and latest is not None else None)}
```

- [ ] **Step 4: Wire `watch` subcommand**

In `browser.py` parser (after `wait` parser, ~line 192):

```python
    wc = sub.add_parser("watch")
    wc.add_argument("--seconds", type=float, default=10.0)
    wc.add_argument("--out", default=None)
    wc.add_argument("--max-frames", type=int, default=100)
    wc.add_argument("--last", action="store_true",
                    help="keep only the newest frame as latest.jpg")
```

Dispatch (inside the `cli = _client()` block, before the final `else`):

```python
        elif args.cmd == "watch":
            out_dir = args.out or os.path.join(
                tempfile.gettempdir(),
                "devin-cu-watch-%d" % int(time.time()))
            out = cu_browser.watch_frames(
                cli, seconds=args.seconds, out_dir=out_dir,
                max_frames=args.max_frames, last_only=args.last)
```

`browser.py` already imports `os` and `tempfile`; add `import time` if absent.

- [ ] **Step 5: Run test to verify it passes**

Run: `pytest tests/test_cu_browser_watch.py -v`
Expected: 3 PASSED

- [ ] **Step 6: Document + commit**

USAGE.md, append to the browser section:

```markdown
`watch` streams the bound browser over CDP `Page.startScreencast` (one
JPEG per page change, acked per frame) into a temp dir the agent can
read. `--last` keeps only `latest.jpg` (single-frame reperception).
CDP only; bound BiDi browsers reject with `screencast_cdp_only`.
```

```bash
git add extensions/computer-use/cu_browser.py extensions/computer-use/browser.py extensions/computer-use/USAGE.md tests/test_cu_browser_watch.py
git commit -m "feat(computer-use): browser watch via CDP screencast"
```

---

### Task 3: `cu_audit.py` (append-only action audit trail)

**Files:**
- Create (living): `extensions/computer-use/cu_audit.py`
- Modify: `extensions/computer-use/cu_actions.py:118-130` (`result()`)
- Modify: `extensions/computer-use/USAGE.md` (Contract section)
- Test: `tests/test_cu_audit.py`

**Interfaces:**
- Consumes: stdlib only; called by `cu_actions.result()`.
- Produces: `enabled() -> bool` (`$CU_AUDIT` unset or not in `{"0","off","false"}`); `audit_path() -> str` (`$CU_AUDIT_PATH` or `tempdir/devin-cu-audit.jsonl`); `record(entry: dict) -> None` (append one JSON line, rotate to last 1000 lines when file exceeds 256 KiB; never raises).

- [ ] **Step 1: Write the failing test**

```python
"""cu_audit: append-only JSONL trail for dispatched actions."""
import json, os, sys
import pytest

sys.path.insert(0, os.path.dirname(__file__))
import cu_load  # noqa: E402

ca = cu_load.load("cu_actions")
au = cu_load.load("cu_audit")


def test_result_writes_audit(monkeypatch, tmp_path):
    p = tmp_path / "a.jsonl"
    monkeypatch.setenv("CU_AUDIT_PATH", str(p))
    monkeypatch.setattr(sys, "argv", ["mouse.py", "click", "500", "300"])
    r = ca.result("dispatched", "physical", timings_ms={"total": 3})
    lines = p.read_text().strip().splitlines()
    assert len(lines) == 1
    rec = json.loads(lines[0])
    assert rec["status"] == "dispatched" and rec["tool"] == "mouse.py"
    assert rec["backend"] == "physical" and "500" not in lines[0]


def test_audit_disabled(monkeypatch, tmp_path):
    p = tmp_path / "a.jsonl"
    monkeypatch.setenv("CU_AUDIT_PATH", str(p))
    monkeypatch.setenv("CU_AUDIT", "off")
    ca.result("dispatched", "physical")
    assert not p.exists()


def test_rotation_keeps_tail(monkeypatch, tmp_path):
    p = tmp_path / "a.jsonl"
    monkeypatch.setenv("CU_AUDIT_PATH", str(p))
    monkeypatch.setenv("CU_AUDIT_MAX_BYTES", "1024")
    monkeypatch.setattr(sys, "argv", ["type_text.py", "x"])
    for i in range(60):
        ca.result("dispatched", "physical", n=i)
    lines = p.read_text().strip().splitlines()
    assert len(lines) <= 1000
    assert json.loads(lines[-1])["extra"]["n"] == 59


def test_audit_failure_never_raises(monkeypatch, tmp_path):
    monkeypatch.setattr(au, "audit_path",
                        lambda: str(tmp_path / "x\x00bad.jsonl"))
    r = ca.result("dispatched", "physical")  # must not raise
    assert r["status"] == "dispatched"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_cu_audit.py -v`
Expected: FAIL, `ModuleNotFoundError` / missing `cu_audit`

- [ ] **Step 3: Create `cu_audit.py`**

```python
#!/usr/bin/env python3
"""Append-only action audit for computer-use (OpenDots parity).

One JSONL record per dispatched action: {ts, tool, cmd, status, backend,
timings_ms}. Deliberately excludes typed values, file contents, and full
command strings, matching OpenDots' computer audit exclusion rule
(docs/COMPUTERS.md). Audit failure is swallowed: it must never break or
block the action it describes.
"""
import json
import os
import tempfile
import time

_MAX_BYTES = int(os.environ.get("CU_AUDIT_MAX_BYTES", str(256 * 1024)))
_KEEP_LINES = 1000


def enabled():
    return os.environ.get("CU_AUDIT", "").lower() not in (
        "0", "off", "false")


def audit_path():
    return os.environ.get(
        "CU_AUDIT_PATH",
        os.path.join(tempfile.gettempdir(), "devin-cu-audit.jsonl"))


def _rotate(path):
    try:
        if os.path.getsize(path) <= _MAX_BYTES:
            return
        with open(path, encoding="utf-8", errors="replace") as f:
            lines = f.readlines()
        tmp = path + ".tmp"
        with open(tmp, "w", encoding="utf-8") as f:
            f.writelines(lines[-_KEEP_LINES:])
        os.replace(tmp, path)
    except OSError:
        pass


def record(entry):
    if not enabled():
        return
    try:
        path = audit_path()
        _rotate(path)
        entry = dict(entry)
        entry["ts"] = entry.get("ts", round(time.time(), 3))
        with open(path, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry, separators=(",", ":")) + "\n")
    except Exception:
        pass
```

- [ ] **Step 4: Hook `result()` in cu_actions.py**

At the end of `result()` (before `return out`, line ~130):

```python
    try:
        import cu_audit
        tool = os.path.basename(sys.argv[0]) if sys.argv else "?"
        cmd = sys.argv[1] if len(sys.argv) > 1 else None
        cu_audit.record({"tool": tool, "cmd": cmd, "status": status,
                         "backend": backend, "extra": kw or None,
                         "timings_ms": kw.get("timings_ms")})
    except Exception:
        pass
    return out
```

Note: `extra` carries contract fields only, never raw typed text (text
args live in `sys.argv` beyond index 1 and are not recorded). `cmd` is
the subcommand name (`click`, `exec`), not its arguments.

- [ ] **Step 5: Run test to verify it passes**

Run: `pytest tests/test_cu_audit.py -v`
Expected: 4 PASSED

- [ ] **Step 6: Document + commit**

USAGE.md Contract section, append:

```markdown
**Audit:** every `result()` appends one line to
`%TEMP%/devin-cu-audit.jsonl` (`$CU_AUDIT_PATH`): tool, subcommand name,
status, backend, timings. Never typed text, file contents, or full
commands. Rotates at 256 KiB keeping the last 1000 lines.
`CU_AUDIT=off` disables.
```

```bash
git add extensions/computer-use/cu_audit.py extensions/computer-use/cu_actions.py extensions/computer-use/USAGE.md tests/test_cu_audit.py
git commit -m "feat(computer-use): append-only action audit trail"
```

---

### Task 4: `skills/scheduled-turns/` (always-on recipe without a daemon)

**Files:**
- Create (living): `skills/scheduled-turns/SKILL.md`
- Test: `tests/test_scheduled_turns_skill.py`

**Interfaces:**
- Consumes: skill format rules enforced by `scripts/validate-skill-format.py` (frontmatter `name`/`description`, "Use when" opening).
- Produces: `skills/scheduled-turns/SKILL.md`, a recipe doc only (no shipped scripts; the skill tells the agent how to write the schedule into the user's project).

- [ ] **Step 1: Write the failing test**

```python
"""scheduled-turns skill exists and passes format validation."""
import os, re


def test_skill_file_has_valid_frontmatter():
    p = os.path.join("skills", "scheduled-turns", "SKILL.md")
    assert os.path.isfile(p)
    text = open(p, encoding="utf-8").read()
    m = re.match(r"^---\s*\n(.*?)\n---\s*\n", text, re.DOTALL)
    assert m, "missing frontmatter"
    assert "name: scheduled-turns" in m.group(1)
    assert "description:" in m.group(1)
    assert re.search(r"description:\s*Use when", m.group(1))


def test_skill_has_required_sections():
    text = open(os.path.join("skills", "scheduled-turns",
                             "SKILL.md"), encoding="utf-8").read()
    for section in ("## When to Use", "## Recipe", "## Guards",
                    "## Disable"):
        assert section in text, "missing " + section
    assert "schtasks" in text or "Register-ScheduledTask" in text
    assert ".devin/ledgers/" in text
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_scheduled_turns_skill.py -v`
Expected: FAIL, file does not exist

- [ ] **Step 3: Write `skills/scheduled-turns/SKILL.md`**

```markdown
---
name: scheduled-turns
description: Use when a task needs recurring or always-on agent turns (periodic checks, polling workflows, run-this-every-morning jobs) without adding a daemon. OS scheduler plus one-shot headless Devin turns writing to ledgers.
---

# Scheduled Turns

Runs an agent turn on an OS schedule. Each fire is a FRESH one-shot
session (`devin -p`), never re-entry into a live session, never a
daemon, matching the runtime's single-process model (AGENTS.md Rule 18;
heartbeat/session-checkpoint emulations were pruned for this reason).

## When to Use

- Recurring chores: inbox triage, dep-update checks, report generation
- "Always-on" behavior for an otherwise session-bound agent

## When NOT to Use

- Sub-hour cadence or real-time reaction: use `cu-realtime` or
  `browser.py events` inside a live session
- Anything needing conversation continuity: each turn is amnesiac, so
  persist state in files the next turn reads

## Recipe

1. Write the turn prompt to the project as `.devin/scheduled/<name>.md`
   (what to check, where to write results, when to stop).
2. Register one OS scheduled task per turn:

   Windows (PowerShell, run once by the user):
   ```powershell
   $act = New-ScheduledTaskAction -Execute "devin" `
     -Argument "-p --prompt-file .devin/scheduled/<name>.md --respect-workspace-trust false" `
     -WorkingDirectory "C:\path\to\project"
   $trg = New-ScheduledTaskTrigger -Daily -At 09:00
   Register-ScheduledTask -TaskName "devin-<name>" `
     -Action $act -Trigger $trg
   ```

   POSIX cron equivalent:
   `0 9 * * * cd /path && devin -p --prompt-file .devin/scheduled/<name>.md --respect-workspace-trust false >> .devin/ledgers/scheduled-<name>.log 2>&1`

3. Each run appends outcome evidence to
   `.devin/ledgers/scheduled-<name>.md`: outcome, what ran, next check.
   The ledger is the inter-turn memory; prompts must name the files a
   turn should read first.

## Guards

- One instance per task: the scheduled script writes a lock file and
  exits when it exists (stale locks older than 24h are removed).
- Schedules are user-approved once; the agent never registers or edits
  a task itself. It writes the prompt file and the user runs the
  register command.
- No secrets in prompt files, task arguments, or ledger output.
- Turns are bounded: the prompt must state a hard stop condition and a
  max runtime expectation; a turn that cannot finish writes
  `ABANDON: <reason>` to its ledger instead of hanging.

## Disable

```powershell
Unregister-ScheduledTask -TaskName "devin-<name>" -Confirm:$false
# cron: remove the crontab line
```

Delete `.devin/scheduled/<name>.md` to retire the turn's instructions.
```

- [ ] **Step 4: Run tests + format validator**

Run: `pytest tests/test_scheduled_turns_skill.py -v`
Expected: 2 PASSED
Run: `python scripts/validate-skill-format.py skills/`
Expected: no error mentioning `scheduled-turns`

- [ ] **Step 5: Commit**

```bash
git add skills/scheduled-turns/SKILL.md tests/test_scheduled_turns_skill.py
git commit -m "feat(skills): scheduled-turns recipe for always-on agent turns"
```

---

### Task 5: `self-improvement` (human publish gate for proposals)

**Files:**
- Modify: `skills/self-improvement/SKILL.md` (add one section)
- Test: `tests/test_self_improvement_publish_gate.py`

**Interfaces:**
- Consumes: existing `self-improvement` skill content (read it first, locate the section where proposed changes land).
- Produces: a "Proposal queue and publish" section stating that proposed edits are queued as proposals and applied only after user publish, mirroring OpenDots' Learning review-then-publish flow (docs/SETUP.md "Automatic Learning").

- [ ] **Step 1: Write the failing test**

```python
"""self-improvement skill documents the human publish gate."""
import os


def test_publish_gate_section():
    p = os.path.join("skills", "self-improvement", "SKILL.md")
    text = open(p, encoding="utf-8").read().lower()
    assert "publish" in text
    assert "proposal" in text
    # the gate must bind publish to a human decision
    assert "human" in text or "user" in text
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_self_improvement_publish_gate.py -v`
Expected: FAIL, no "publish" section

- [ ] **Step 3: Read the skill and add the section**

Read `skills/self-improvement/SKILL.md` first, then insert a section in
the workflow area (before the evidence/validation part) matching the
file's existing style:

```markdown
## Proposal queue and publish

Refine output lands as PROPOSALS, not edits. A proposal is a queued
record {target file, diff, evidence, expected effect} that the user
reviews and publishes. Nothing is applied on the loop's own authority,
mirroring OpenDots' Automatic Learning flow where proposed skills are
reviewed and published in Intelligence before delivery. Their delivery
denial fails the turn; ours fails the proposal. Already-implemented
proposals cite their ledger evidence; rejected ones keep the reason.
```

- [ ] **Step 4: Run test + validate**

Run: `pytest tests/test_self_improvement_publish_gate.py -v`
Expected: 1 PASSED
Run: `python scripts/validate-skill-format.py skills/`
Expected: clean

- [ ] **Step 5: Commit**

```bash
git add skills/self-improvement/SKILL.md tests/test_self_improvement_publish_gate.py
git commit -m "docs(self-improvement): proposals queue behind human publish"
```

---

### Task 6: Final gate (full suite + audit)

- [ ] **Step 1: Run the repo gates**

Run: `python audit.py`
Expected: `0 errors` in final summary

Run: `pytest -q`
Expected: all collected tests pass (1588 + new ~11)

- [ ] **Step 2: Update the gap report**

Mark B1/B2/B3/B10/B11 adopted in `.devin/scratch/opendots-gap-analysis.md`
(one-line status per row); record B4 dropped (allowed-tools exists) and
B12 deferred.

- [ ] **Step 3: Commit**

```bash
git add -A
git commit -m "docs: record opendots adaptation status"
```

## Dependency notes

- T1/T2/T3 are independent; T2 works on any bound browser (T1 makes the
  pairing nicer but is not required).
- T4/T5 are doc-only and independent.
- Execution order suggestion: T3 (smallest) -> T1 -> T2 -> T4 -> T5 -> T6.

## Self-review

1. Spec coverage: 5 user stories -> T1 (persistent profile), T3 (audit),
   T2 (event-driven watch), T4 (scheduled turns), T5 (publish gate). Each
   acceptance criterion maps to a checkable task output.
2. Placeholder scan: no TODO/TBD/FIXME; every task has real test code and
   real implementation code.
3. Type consistency: `launch_owned(profile, timeout_s)` signature identical
   in interface spec, monkeypatch in test, and implementation. `watch_frames`
   params match between test call and signature. Audit fields match between
   `record()` writes and test asserts (`status`, `tool`, `backend`, `extra`,
   `timings_ms`).
4. Ordering: tasks are vertical slices (feature file + test + doc + commit
   each); no horizontal layer phases.
5. Disposable files: none; all created files are living (new extension
   module, new skill, new tests).
6. Security: `bad_profile_name` guards path traversal; loopback-only bind
   preserved; audit excludes typed values; `stop_owned` refuses foreign
   pids; scheduled-turns skill forbids agent self-registration.
7. Known risks: `_browser_pid_via_cdp` assumes the first CDP connection
   exposes `SystemInfo.getProcessInfo` (true on modern Chromium; Edge/Brave
   included via `find_browser_exe`). `launch` on non-Chromium (Firefox)
   fails with `browser_start_timeout`, an acceptable typed failure. The
   `watch` drain loop polls `ws.events` at 50ms; frames arriving between
   polls are picked up next tick, bounded by `seconds`/`max_frames`.
