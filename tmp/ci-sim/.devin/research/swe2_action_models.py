import math
import random


def minimum_jerk(start, end, duration, samples):
    if len(start) != 2 or len(end) != 2:
        raise ValueError("two-dimensional endpoints required")
    if not all(math.isfinite(v) for v in (*start, *end, duration)):
        raise ValueError("finite values required")
    if duration <= 0 or isinstance(samples, bool) or not isinstance(samples, int) or not 2 <= samples <= 10000:
        raise ValueError("positive duration and 2..10000 samples required")
    points = []
    for i in range(samples):
        u = i / (samples - 1)
        s = u ** 3 * (10 + u * (-15 + 6 * u))
        points.append((u * duration, start[0] + (end[0] - start[0]) * s, start[1] + (end[1] - start[1]) * s))
    points[0] = (0.0, *start)
    points[-1] = (duration, *end)
    return points


def typing_intervals(text, medians, fallback, sigma, bounds, seed):
    low, high = bounds
    if not all(math.isfinite(v) for v in (fallback, sigma, low, high)) or not 0 < low <= fallback <= high or sigma < 0:
        raise ValueError("invalid timing parameters")
    if any(not isinstance(k, str) or not 1 <= len(k) <= 3 or not math.isfinite(v) or not low <= v <= high for k, v in medians.items()):
        raise ValueError("invalid context medians")
    rng = random.Random(seed)
    intervals = []
    for i in range(len(text)):
        contexts = (text[max(0, i - n + 1):i + 1] for n in (3, 2, 1))
        median = next((medians[k] for k in contexts if k in medians), fallback)
        delay = rng.lognormvariate(math.log(median), sigma)
        intervals.append(min(high, max(low, delay)))
    return intervals


if __name__ == "__main__":
    path = minimum_jerk((0, 0), (100, -50), 1.0, 101)
    assert path[0] == (0.0, 0, 0)
    assert path[-1] == (1.0, 100, -50)
    assert all(a[0] < b[0] and a[1] <= b[1] and a[2] >= b[2] for a, b in zip(path, path[1:]))
    assert path[50] == (0.5, 50.0, -25.0)
    assert minimum_jerk((3, 3), (3, 3), 1, 2) == [(0.0, 3, 3), (1, 3, 3)]
    args = ("teste.", {"te": 0.08, "ste": 0.12, ".": 0.2}, 0.1, 0.2, (0.01, 0.4), 7)
    delays = typing_intervals(*args)
    assert delays == typing_intervals(*args)
    assert len(delays) == 6 and all(0.01 <= x <= 0.4 for x in delays)
    deterministic = typing_intervals("abc", {"a": 0.1, "ab": 0.2, "abc": 0.3}, 0.15, 0, (0.01, 0.4), 7)
    assert all(math.isclose(a, b) for a, b in zip(deterministic, (0.1, 0.2, 0.3)))
    assert typing_intervals("", {}, 0.1, 0, (0.01, 0.4), 7) == []
    invalid = [lambda: minimum_jerk((0, 0), (1, 1), 0, 3), lambda: minimum_jerk((0, 0), (1, 1), 1, 1), lambda: minimum_jerk((0, 0), (math.nan, 1), 1, 3), lambda: typing_intervals("a", {}, -1, 0, (0.01, 1), 7)]
    for operation in invalid:
        try:
            operation()
        except ValueError:
            pass
        else:
            raise AssertionError("invalid parameters accepted")
    print("offline mathematical checks: PASS")
