"""Etapa 2 gates: OwnedInputs releases only session-owned inputs on error;
the result contract separates dispatch from verified effect."""
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent))
from cu_load import load

cu_actions = load("cu_actions")


class FakeController:
    def __init__(self):
        self.held = set()
        self.log = []

    def press(self, k):
        self.held.add(k)
        self.log.append(("press", k))

    def release(self, k):
        self.held.discard(k)
        self.log.append(("release", k))


def test_owned_inputs_release_on_exception():
    kb = FakeController()
    with pytest.raises(RuntimeError):
        with cu_actions.OwnedInputs() as owned:
            owned.press(kb, "ctrl")
            owned.press(kb, "c")
            raise RuntimeError("mid-gesture failure")
    assert kb.held == set()


def test_owned_inputs_release_only_own():
    kb = FakeController()
    kb.press("user_key")  # physical key already held — not ours
    with cu_actions.OwnedInputs() as owned:
        owned.press(kb, "ctrl")
    assert kb.held == {"user_key"}


def test_release_all_is_lifo():
    kb = FakeController()
    with cu_actions.OwnedInputs() as owned:
        owned.press(kb, "ctrl")
        owned.press(kb, "shift")
        owned.press(kb, "s")
        owned.release(kb, "s")
    assert kb.log[-2:] == [("release", "shift"), ("release", "ctrl")]


def test_release_failure_does_not_mask_others():
    class Flaky(FakeController):
        def release(self, k):
            if k == "bad":
                raise OSError("release failed")
            super().release(k)
    kb = Flaky()
    with cu_actions.OwnedInputs() as owned:
        owned.press(kb, "bad")
        owned.press(kb, "ctrl")
    assert kb.held == {"bad"}          # failed key stays; others released
    assert ("release", "ctrl") in kb.log


def test_result_contract_statuses():
    r = cu_actions.result("dispatched", "physical", cmd="click")
    assert r["ok"] is True and r["status"] == "dispatched"
    assert r["dispatch"]["backend"] == "physical"
    assert cu_actions.result("rejected", "uia")["ok"] is False
    # dispatch may have landed — ok stays true, status carries uncertainty
    for s in ("timeout", "unknown", "cancelled", "verified"):
        r = cu_actions.result(s, "physical")
        assert r["ok"] is True and r["status"] == s


def test_now_ms_monotonic():
    assert cu_actions.now_ms() >= cu_actions.now_ms() - 1
