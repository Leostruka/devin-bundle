"""Held-out benchmark-harness contracts; lead-owned."""
import importlib
import json
import sys
from pathlib import Path

import pytest


EXT = Path(__file__).resolve().parents[3] / "extensions" / "system-control"


def load(name):
    sys.path.insert(0, str(EXT))
    return importlib.import_module(name)


@pytest.fixture
def bench():
    try:
        return load("sc_bench")
    except ModuleNotFoundError:
        pytest.skip("sc_bench not implemented yet")


class FakeClock:
    """Monotonic fake clock; callable returns seconds."""

    def __init__(self):
        self.t = 0.0

    def __call__(self):
        return self.t

    def advance(self, dt):
        self.t += dt


def test_distribution_fields_and_run_count(bench):
    r = bench.run(lambda: None, runs=20, warmup=2)
    for k in ("runs", "p50_ms", "p95_ms", "max_ms"):
        assert k in r
    assert r["runs"] == 20


def test_warmup_excluded_from_stats(bench):
    calls = {"n": 0}

    def work():
        calls["n"] += 1

    r = bench.run(work, runs=5, warmup=3)
    assert calls["n"] == 8
    assert r["runs"] == 5


def test_clock_is_monotonic(bench):
    clock = FakeClock()
    ticks = iter([0, 1, 2, 3, 4, 5, 6, 7])

    def work():
        next(ticks)

    r = bench.run(work, runs=3, warmup=1,
                  clock=lambda: clock.advance(0.001) or clock.t)
    assert r["max_ms"] >= r["p95_ms"] >= r["p50_ms"] >= 0


def test_env_metadata_excludes_sensitive(bench):
    r = bench.run(lambda: None, runs=2, warmup=0,
                  env=bench.env_metadata())
    assert isinstance(r["env"], dict)
    blob = json.dumps(r["env"]).lower()
    for bad in ("appdata", "\\users\\", "leand", "secret", "token"):
        assert bad not in blob


def test_result_is_json_serializable(bench):
    r = bench.run(lambda: None, runs=3, warmup=0)
    json.dumps(r)
