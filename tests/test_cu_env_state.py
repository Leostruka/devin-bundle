"""Gate for C02: per-environment state isolation.

Namespaces are (env_id, instance_id, session_id); state_path validates
every component (no traversal, confinement under root). Legacy fixed-name
temp files remain the local backend's path — scope=None keeps them.
"""
import json
import os
import sys
import threading
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent))
from cu_load import load  # noqa: E402

cu_target = load("cu_target")
cu_hints = load("cu_hints")
cu_motion = load("cu_motion")


@pytest.fixture
def state_root(tmp_path, monkeypatch):
    root = tmp_path / "cu-envs"
    monkeypatch.setenv("CU_STATE_ROOT", str(root))
    return root


# --- state_path / state_dir --------------------------------------------------

def test_state_paths_do_not_collide(tmp_path):
    a = cu_target.state_path(tmp_path, "a", "i1", "s1", "hints.json")
    b = cu_target.state_path(tmp_path, "b", "i1", "s1", "hints.json")
    assert a != b


def test_state_path_components(tmp_path):
    p = cu_target.state_path(tmp_path, "env", "inst", "sess", "f.json")
    assert p == tmp_path / "env" / "inst" / "sess" / "f.json"


@pytest.mark.parametrize("bad", ["..", "a/b", "a\\b", "", ".", "x y",
                                 "a;b", "a\x00b"])
def test_state_path_rejects_bad_component(tmp_path, bad):
    with pytest.raises(ValueError):
        cu_target.state_path(tmp_path, bad, "i1", "s1", "f.json")
    with pytest.raises(ValueError):
        cu_target.state_path(tmp_path, "e", bad, "s1", "f.json")
    with pytest.raises(ValueError):
        cu_target.state_path(tmp_path, "e", "i1", bad, "f.json")


@pytest.mark.parametrize("bad", ["..", "../x", "a/b", "", ".hidden",
                                 "a..b", "con", "NUL"])
def test_state_path_rejects_bad_name(tmp_path, bad):
    with pytest.raises(ValueError):
        cu_target.state_path(tmp_path, "e", "i", "s", bad)


def test_state_path_confined_under_root(tmp_path):
    p = cu_target.state_path(tmp_path, "e", "i", "s", "f.json")
    assert os.path.commonpath([str(p.resolve()), str(tmp_path.resolve())]) \
        == str(tmp_path.resolve())


def test_state_path_rejects_symlink_escape(tmp_path):
    outside = tmp_path / "outside"
    outside.mkdir()
    root = tmp_path / "root"
    root.mkdir()
    (root / "evil").symlink_to(outside, target_is_directory=True)
    with pytest.raises(ValueError, match="escape"):
        cu_target.state_path(root, "evil", "i", "s", "f.json",
                             require_within=True)


# --- scoped hint sidecar ------------------------------------------------------

def _hint(hid="a", x=10, y=20):
    return {"id": hid, "x": x, "y": y, "name": "Btn", "type": "Button",
            "bounds": [x - 5, y - 5, 10, 10], "hwnd": None, "enabled": True}


def test_scoped_sidecar_isolated(state_root):
    s1 = ("env-a", "i1", "sess-1")
    s2 = ("env-b", "i1", "sess-1")
    data = cu_hints.write_sidecar([_hint()], scope=s1)
    entry, reason = cu_hints.resolve_hint(
        "a", session=data["session_id"], scope=s1)
    assert reason is None and entry["x"] == 10
    entry, reason = cu_hints.resolve_hint(
        "a", session=data["session_id"], scope=s2)
    assert entry is None and reason == "no_sidecar"


def test_restart_invalidates_observations(state_root):
    old = cu_hints.write_sidecar([_hint()], scope=("e", "i1", "s"))
    entry, reason = cu_hints.resolve_hint(
        "a", session=old["session_id"], scope=("e", "i2", "s"))
    assert entry is None and reason == "no_sidecar"


def test_session_ids_differ_per_scope(state_root):
    a = cu_hints.session_id(scope=("e", "i1", "s1"))
    b = cu_hints.session_id(scope=("e", "i1", "s2"))
    assert a and b and a != b
    assert cu_hints.session_id(scope=("e", "i1", "s1")) == a


def test_generations_monotonic_under_concurrency(state_root):
    scope = ("e", "i1", "s")
    gens = []

    def worker():
        gens.append(cu_hints.write_sidecar(
            [_hint()], scope=scope)["generation"])

    ts = [threading.Thread(target=worker) for _ in range(6)]
    for t in ts:
        t.start()
    for t in ts:
        t.join()
    assert sorted(gens) == list(range(1, 7))


def test_failed_write_keeps_prior_state(state_root, monkeypatch):
    scope = ("e", "i1", "s")
    good = cu_hints.write_sidecar([_hint()], scope=scope)

    def explode(*a, **k):
        raise OSError("disk full")
    monkeypatch.setattr(os, "replace", explode)
    with pytest.raises(OSError):
        cu_hints.write_sidecar([_hint("b")], scope=scope)

    entry, reason = cu_hints.resolve_hint(
        "a", session=good["session_id"], scope=scope)
    assert reason is None  # prior observation intact


def test_legacy_sidecar_untouched_by_scope(state_root, monkeypatch,
                                           tmp_path):
    """scope=None keeps the legacy tempdir path — local compat."""
    monkeypatch.setenv("CU_HINT_TTL", "120")
    legacy = cu_hints.sidecar_path()
    assert "devin-cu-hints.json" in legacy
    assert str(state_root) not in legacy
    scoped = cu_hints.sidecar_path(scope=("e", "i", "s"))
    assert str(state_root) in scoped


# --- scoped profile -----------------------------------------------------------

def test_scoped_profile_independent(state_root):
    s1, s2 = ("e1", "i1", "s"), ("e2", "i1", "s")
    cu_motion.set_profile("human", scope=s1)
    assert cu_motion.get_profile(scope=s1) == "human"
    assert cu_motion.get_profile(scope=s2) == "fast"  # default, not s1's


def test_legacy_profile_path_unscoped():
    assert cu_motion.profile_path().endswith("devin-cu-profile.json")


# --- screenshot shot-state ----------------------------------------------------

def test_scoped_shotstate_path(state_root):
    screenshot = load("screenshot")
    scoped = screenshot._shot_state_path(scope=("e", "i", "s"))
    legacy = screenshot._shot_state_path()
    assert str(state_root) in scoped
    assert str(state_root) not in legacy
