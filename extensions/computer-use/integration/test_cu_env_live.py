"""C16 LIVE gate — non-interference proof against a real running env.

This suite is OUTSIDE tests/ on purpose: it must never run in the
normal CI collection. It requires a configured, RUNNING env
(CU_LIVE_ENV or 'devin-linux' in the repo registry). A job without
the env FAILS — absence is a broken gate, not a skip.

Run:  python -m pytest extensions/computer-use/integration/test_cu_env_live.py -q

Proves: capture and input act on the SAME guest instance; remote ops
never touch host input/capture modules (traps); timings are measured,
not promised; a written report lands next to this file.
"""
import json
import os
import sys
import time
from pathlib import Path

import pytest

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))          # extensions/computer-use
sys.path.insert(0, str(HERE.parents[2] / "tests"))
from cu_load import load  # noqa: E402

cu_target = load("cu_target")
cu_backend = load("cu_backend")
cu_qmp_backend = load("cu_qmp_backend")
screenshot = load("screenshot")

ENV_ID = os.environ.get("CU_LIVE_ENV", "devin-linux")
REPORT = HERE / "live-report.json"


class Exploding:
    def __init__(self, name):
        self._name = name

    def __getattr__(self, attr):
        raise AssertionError(
            f"remote path touched host module {self._name}.{attr}")


@pytest.fixture(autouse=True)
def host_traps(monkeypatch):
    for name in ("pynput", "mss", "pyautogui", "keyboard"):
        monkeypatch.setitem(sys.modules, name, Exploding(name))
    yield


@pytest.fixture(scope="session")
def backend():
    """Real backend to the RUNNING env — or a hard failure."""
    registry = cu_target.load_registry()
    target = cu_target.resolve_target(ENV_ID, registry)
    if target.get("kind") != "qemu":
        pytest.fail(f"env_not_qemu:{ENV_ID}")
    try:
        return cu_backend.open_backend(target)
    except Exception as exc:
        pytest.fail(
            f"env_not_running:{ENV_ID} — start it first "
            f"({type(exc).__name__}: {exc})")


@pytest.fixture(scope="session")
def probe_run(backend):
    """Real probe capture: one input round-trip against the guest,
    timings measured. Frozen observations, not a constructed dict."""
    out = {"env_id": ENV_ID, "timings_ms": {}}
    t0 = time.perf_counter()
    frame0, meta0 = backend.observe()
    out["timings_ms"]["capture_cold"] = round(
        (time.perf_counter() - t0) * 1000, 1)
    out["instance_id"] = meta0.get("instance_id")
    out["geometry"] = [frame0.width, frame0.height]

    t0 = time.perf_counter()
    backend.send_events(cu_qmp_backend.encode_key("enter"))
    out["timings_ms"]["dispatch_key"] = round(
        (time.perf_counter() - t0) * 1000, 1)

    t0 = time.perf_counter()
    frame1, meta1 = backend.observe()
    out["timings_ms"]["capture_warm"] = round(
        (time.perf_counter() - t0) * 1000, 1)
    out["verification"] = cu_backend.verify_effect(
        {"cmd": "key:enter"},
        {"frame": frame0, "meta": meta0},
        {"frame": frame1, "meta": meta1},
        {"kind": "frame_changed"})
    REPORT.write_text(json.dumps(out, indent=2), encoding="utf-8")
    return out


def test_capture_and_input_same_instance(probe_run):
    assert probe_run["instance_id"]
    v = probe_run["verification"]
    # same boot on both observations — instance mismatch is a failure
    assert v.get("reason") != "instance_mismatch"


def test_effect_evidence_reported(probe_run):
    v = probe_run["verification"]
    assert "status" in v or "verified" in v
    # evidence at most — never task-complete
    assert v.get("status") != "verified"


def test_position_query_is_honest(backend):
    with pytest.raises(Exception, match="position"):
        backend.pointer_position()


def test_out_of_bounds_input_rejected(backend):
    with pytest.raises(Exception):
        cu_qmp_backend.encode_move(-5, -5, 640, 480)


def test_timings_measured(probe_run):
    t = probe_run["timings_ms"]
    assert t["capture_cold"] > 0 and t["capture_warm"] > 0
    assert t["dispatch_key"] > 0
