"""Etapa 1 gates: sidecar v2 — session/generation/window binding, TTL,
atomic write, typed staleness rejection, fallback invalidation, and
zero-dispatch on stale hints at the mouse.py level."""
import json
import sys
import types
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent))
from cu_load import load

cu_hints = load("cu_hints")


@pytest.fixture
def sidecar(tmp_path, monkeypatch):
    f = tmp_path / "hints.json"
    monkeypatch.setattr(cu_hints, "sidecar_path", lambda: str(f))
    monkeypatch.setattr(cu_hints, "session_path",
                        lambda: str(tmp_path / "sess.json"))
    monkeypatch.setattr(cu_hints, "_window_alive", lambda hwnd: True)
    return f


def _hints():
    return [{"id": "as", "x": 100, "y": 50, "name": "Salvar",
             "type": "Button", "bounds": [90, 40, 20, 20],
             "hwnd": 1234, "enabled": True}]


def test_write_then_resolve_roundtrip(sidecar):
    data = cu_hints.write_sidecar(
        _hints(), window={"hwnd": 1234, "pid": 7},
        capture={"origin_px": [0, 0], "size_px": [100, 100]})
    assert data["schema_version"] == 2
    assert data["session_id"] and data["observation_id"] == "obs-1"
    entry, reason = cu_hints.resolve_hint("as")
    assert reason is None
    assert (entry["x"], entry["y"]) == (100, 50)
    assert entry["bounds"] == [90, 40, 20, 20]


def test_generation_increments(sidecar):
    assert cu_hints.write_sidecar(_hints())["generation"] == 1
    assert cu_hints.write_sidecar(_hints())["generation"] == 2


def test_atomic_write_and_corrupt_file(sidecar):
    cu_hints.write_sidecar(_hints())
    assert not (sidecar.parent / (sidecar.name + ".tmp")).exists()
    sidecar.write_text('{"schema_version": 2, "hints":', encoding="utf-8")
    entry, reason = cu_hints.resolve_hint("as")
    assert entry is None and reason == "no_sidecar"


def test_expired_hint_rejected(sidecar, monkeypatch):
    cu_hints.write_sidecar(_hints())
    monkeypatch.setattr(cu_hints, "HINT_TTL_S", -1)
    entry, reason = cu_hints.resolve_hint("as")
    assert entry is None and reason == "expired"


def test_foreign_session_rejected(sidecar):
    cu_hints.write_sidecar(_hints())
    entry, reason = cu_hints.resolve_hint("as", session="other-session")
    assert entry is None and reason == "session"


def test_dead_window_rejected(sidecar, monkeypatch):
    cu_hints.write_sidecar(_hints())
    monkeypatch.setattr(cu_hints, "_window_alive", lambda hwnd: False)
    entry, reason = cu_hints.resolve_hint("as")
    assert entry is None and reason == "window_gone"


def test_unknown_hint_and_invalidation(sidecar):
    cu_hints.write_sidecar(_hints())
    assert cu_hints.resolve_hint("zz")[1] == "unknown_hint"
    cu_hints.invalidate_sidecar()
    assert cu_hints.resolve_hint("as")[1] == "no_sidecar"


def test_schema_v1_rejected(sidecar):
    sidecar.write_text(json.dumps(
        {"schema_version": 1, "hints": {"as": {"x": 1, "y": 2}}}),
        encoding="utf-8")
    assert cu_hints.resolve_hint("as")[1] == "schema"


# --- mouse.py integration: stale hint must dispatch zero controller calls ---

class _FakeButton:
    left = "left"
    right = "right"
    middle = "middle"


class _FakeMouseCtl:
    instances = []

    def __init__(self):
        self.calls = []
        self._pos = (0, 0)
        _FakeMouseCtl.instances.append(self)

    @property
    def position(self):
        return self._pos

    @position.setter
    def position(self, v):
        self._pos = v
        self.calls.append(("move", v))

    def press(self, b):
        self.calls.append(("press", b))

    def release(self, b):
        self.calls.append(("release", b))

    def scroll(self, dx, dy):
        self.calls.append(("scroll", dx, dy))


@pytest.fixture
def fake_pynput(monkeypatch):
    _FakeMouseCtl.instances = []
    pm = types.ModuleType("pynput.mouse")
    pm.Button = _FakeButton
    pm.Controller = _FakeMouseCtl
    pkg = types.ModuleType("pynput")
    pkg.mouse = pm
    monkeypatch.setitem(sys.modules, "pynput", pkg)
    monkeypatch.setitem(sys.modules, "pynput.mouse", pm)
    monkeypatch.setenv("COMPUTER_USE_PROFILE", "fast")  # deterministic
    return _FakeMouseCtl


def _run_mouse(monkeypatch, capsys, argv):
    mouse = load("mouse")
    monkeypatch.setattr(sys, "argv", argv)
    try:
        mouse.main()
    except SystemExit:
        pass
    lines = [l for l in capsys.readouterr().out.strip().splitlines() if l]
    return json.loads(lines[-1])


def test_stale_hint_dispatches_nothing(fake_pynput, sidecar, monkeypatch,
                                       capsys):
    out = _run_mouse(monkeypatch, capsys,
                     ["mouse.py", "click", "--hint", "as"])
    assert out["ok"] is False and "rejected" in out["error"]
    # rejection precedes even controller construction — zero calls OR
    # zero instances both satisfy "dispatches nothing"
    assert all(c.calls == [] for c in fake_pynput.instances)


def test_fresh_hint_physical_click_dispatches(fake_pynput, sidecar,
                                              monkeypatch, capsys):
    cu_hints.write_sidecar(_hints())
    out = _run_mouse(monkeypatch, capsys,
                     ["mouse.py", "click", "--hint", "as",
                      "--via", "physical"])
    assert out["ok"] is True and out["status"] == "dispatched"
    calls = fake_pynput.instances[0].calls
    assert ("press", "left") in calls and ("release", "left") in calls
    assert out["x"] == 100 and out["y"] == 50
    assert out["timings_ms"]["total"] is not None


def test_click_dry_run_status_contract(fake_pynput, monkeypatch, capsys):
    out = _run_mouse(monkeypatch, capsys,
                     ["mouse.py", "click", "10", "20", "--dry-run"])
    assert out["ok"] is True and out["status"] == "dispatched"
    assert out["dry_run"] is True and out["dispatch"]["backend"] == "physical"
    assert fake_pynput.instances[0].calls == []


def test_concurrent_sidecar_writes_never_torn(sidecar):
    """Ticket 16: writers racing write_sidecar must leave a parseable
    file; the winner's generation is the max."""
    import threading
    results = []
    lock = threading.Lock()

    def w(tag):
        d = cu_hints.write_sidecar(
            [{"id": "a", "x": 1, "y": 1, "name": tag, "type": "Button",
              "bounds": [0, 0, 9, 9], "hwnd": 1, "enabled": True}])
        with lock:
            results.append(d["generation"])
    threads = [threading.Thread(target=w, args=(f"t{i}",))
               for i in range(8)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    data = cu_hints._read_sidecar()
    assert data is not None  # always parses
    assert data["generation"] == max(results)  # a writer's gen won


def test_interrupted_write_preserves_previous(sidecar):
    """Ticket 16: a tmp file abandoned mid-write must not corrupt or
    shadow the last committed sidecar."""
    committed = cu_hints.write_sidecar(
        [{"id": "a", "x": 5, "y": 5, "name": "ok", "type": "Button",
          "bounds": [0, 0, 9, 9], "hwnd": 1, "enabled": True}])
    # simulate crash between tmp write and os.replace
    with open(cu_hints.sidecar_path() + ".tmp", "w", encoding="utf-8") as f:
        f.write('{"schema_version": 2, "partial": tru')  # torn JSON
    data = cu_hints._read_sidecar()
    assert data["generation"] == committed["generation"]
    assert data["hints"]["a"]["name"] == "ok"
