"""sc_bench — deterministic micro-benchmark harness (stdlib only).

Measures a callable's wall-clock distribution with an injectable
monotonic clock. Warmup iterations are executed but never recorded.
Environment metadata is sanitized: no usernames, home paths, or
secrets — platform class only.
"""

import json
import math
import operator
import pathlib
import platform
import statistics
import sys
import time


def _percentile(sorted_samples, q):
    """Nearest-rank percentile on pre-sorted samples."""
    if not sorted_samples:
        return 0.0
    idx = int(math.ceil(q * len(sorted_samples))) - 1
    idx = max(0, min(idx, len(sorted_samples) - 1))
    return sorted_samples[idx]


def run(fn, *, runs, warmup=0, clock=None, env=None, scenario=None):
    """Time `fn` for `runs` measured iterations after `warmup`.

    `clock` is a monotonic callable returning seconds; defaults to
    time.perf_counter. Returns a JSON-serializable summary dict.
    """
    clock = clock or time.perf_counter
    runs = operator.index(runs)
    warmup = operator.index(warmup)
    if runs < 1 or warmup < 0:
        raise ValueError("runs must be >=1 and warmup >=0")
    for _ in range(warmup):
        fn()
    samples = []
    for _ in range(runs):
        t0 = clock()
        fn()
        t1 = clock()
        samples.append(max(0.0, (t1 - t0) * 1000.0))
    ordered = sorted(samples)
    result = {
        "scenario": scenario,
        "runs": len(samples),
        "warmup": warmup,
        "min_ms": ordered[0] if ordered else 0.0,
        "p50_ms": _percentile(ordered, 0.50),
        "p95_ms": _percentile(ordered, 0.95),
        "max_ms": ordered[-1] if ordered else 0.0,
        "mean_ms": (statistics.fmean(samples) if samples else 0.0),
    }
    if env is not None:
        result["env"] = env
    return result


def env_metadata():
    """Platform info safe to publish — no user/host identifying data."""
    return {
        "platform": platform.system() or "unknown",
        "platform_release": platform.release() or "unknown",
        "machine": platform.machine() or "unknown",
        "python_implementation": platform.python_implementation(),
        "python_version": platform.python_version(),
    }


def _main(argv):
    """CLI: `python sc_bench.py [--runs N] [--warmup N]`."""
    runs, warmup = 30, 5
    args = iter(argv)
    for a in args:
        if a == "--runs":
            runs = int(next(args, "30"))
        elif a == "--warmup":
            warmup = int(next(args, "5"))
    here = str(pathlib.Path(__file__).resolve().parent)
    if here not in sys.path:
        sys.path.insert(0, here)
    import sc_backend
    import sc_contract
    import sc_telemetry

    payload = json.dumps({
        "version": 1,
        "request_id": "bench-0001",
        "capability": "process.observe",
        "args": {"pid": 1},
        "deadline_ms": 5000,
        "target": {"pid": 1, "start_time": 0},
    })
    fixture_events = [
        sc_telemetry.normalize(
            {"pid": i % 50, "start_time": 0},
            source="bench", kind="process.sample",
            severity="error" if i % 97 == 0 else "info",
            ts=float(i))
        for i in range(1000)
    ]

    def _stream_once():
        res = sc_telemetry.open_stream(capacity=512, ttl_s=60)
        s = res["stream"]
        s.feed(fixture_events[:512])
        sc_telemetry.drain(s, limit=512)
        sc_telemetry.close_stream(s)

    scenarios = {
        "process_snapshot": lambda: sc_backend.capabilities(),
        "event_reduce": lambda: sc_telemetry.reduce_events(
            fixture_events, top_k=10),
        "json_decode": lambda: sc_contract.validate_request(
            json.loads(payload)),
        "stream_drain": _stream_once,
    }
    env = env_metadata()
    out = {name: run(fn, runs=runs, warmup=warmup,
                     env=env, scenario=name)
           for name, fn in scenarios.items()}
    print(json.dumps(out, indent=2, sort_keys=True))


if __name__ == "__main__":
    _main(sys.argv[1:])
