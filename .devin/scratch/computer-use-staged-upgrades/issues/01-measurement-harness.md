# 01 — Measurement harness + baseline (protocol 4.4)

**Intent:** every remaining adapter decision needs per-boundary latency
evidence; today there is none. Delivers `cu_bench.py` producing frozen JSON.

**What to build:** `extensions/computer-use/cu_bench.py` measuring, per run:
import/subprocess startup, MSS grab (full + region), PNG encode, UIA hint
enum, pynput dispatch round-trip, effect-wait sample. p50/p95 + raw samples
+ machine metadata (python, monitors, DPI scale). Output: JSON to stdout and
optional --out file. Never saves screen content beyond the bench artifact.

**Proposed modules:** new `cu_bench.py`; reads cu_hints/cu_motion only.

**Estimated size (lines):** ~150

**Input / Output:** `--runs N --out <file>` → `{"ok":true,"boundaries":{...p50/p95},"meta":{...}}`

**Blocked by:** None — can start immediately.

**Gate:** `<venv>/python cu_bench.py --runs 10 --dry-run` then a real `--runs 10`

**Expect:** exit 0; all boundaries have p50/p95; raw sample counts == runs

**Evidence:** `.devin/research/cu-benchmark-baseline.json`

**Status:** resolved

- [ ] all six boundaries measured and labeled
- [ ] p50/p95 + raw samples, no fabricated numbers
- [ ] stdout stays single-JSON

## Answer

`cu_bench.py` landed; baseline frozen at `.devin/research/cu-benchmark-baseline.json`
(20 runs): startup 141.7ms p50, png_encode 101.8ms, hints_enum 30.9ms,
capture_full 20.5ms, input_dispatch 0.002ms. Evidence: pytest green +
baseline JSON.
