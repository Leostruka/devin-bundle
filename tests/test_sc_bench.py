"""sc_bench — deterministic benchmark harness tests."""
import getpass
import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]
                      / "extensions" / "system-control"))
import sc_bench as bench  # noqa: E402


def fake_clock_factory(step_s=0.001):
    """Clock advancing `step_s` on every call."""
    state = {"t": 0.0}

    def clock():
        state["t"] += step_s
        return state["t"]

    return clock


def test_reports_required_keys_and_run_count():
    r = bench.run(lambda: None, runs=20, warmup=2, clock=fake_clock_factory())
    assert set(r) >= {"runs", "p50_ms", "p95_ms", "max_ms"}
    assert r["runs"] == 20


def test_warmup_excluded_from_run_count():
    calls = {"n": 0}

    def fn():
        calls["n"] += 1

    r = bench.run(fn, runs=30, warmup=5, clock=fake_clock_factory())
    assert r["runs"] == 30
    assert calls["n"] == 35


def test_percentile_ordering_and_nonnegative():
    r = bench.run(lambda: None, runs=30, clock=fake_clock_factory())
    assert r["p50_ms"] >= 0
    assert r["max_ms"] >= r["p95_ms"] >= r["p50_ms"]


def test_fake_clock_measures_fn_cost_only():
    # fn performs work between the two clock reads; a clock that
    # advances 1 ms per read yields ~1 ms samples.
    r = bench.run(lambda: None, runs=10, clock=fake_clock_factory(0.001))
    assert r["min_ms"] > 0
    assert r["p50_ms"] == pytest.approx(1.0, rel=0.01)


def test_env_echoed_when_passed():
    env = bench.env_metadata()
    r = bench.run(lambda: None, runs=5, clock=fake_clock_factory(), env=env)
    assert r["env"] == env


def test_env_metadata_sanitized():
    blob = json.dumps(bench.env_metadata()).lower()
    for bad in ("appdata", chr(92) + "users" + chr(92),
                "secret", "token",
                getpass.getuser().lower()):
        assert bad not in blob


def test_result_json_serializable():
    r = bench.run(lambda: None, runs=10, clock=fake_clock_factory(),
                  env=bench.env_metadata())
    assert json.loads(json.dumps(r)) == r


def test_scenario_label_and_mean():
    r = bench.run(lambda: None, runs=10, clock=fake_clock_factory(),
                  scenario="unit")
    assert r["scenario"] == "unit"
    assert r["mean_ms"] >= r["min_ms"]
