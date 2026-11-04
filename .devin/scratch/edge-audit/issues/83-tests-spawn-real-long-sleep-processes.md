# 83 -- tests spawn real processes with multi-second sleeps and taskkill
- **Status**: open
- **Category**: test-coverage
- **Severity**: P3
- **File**: tests/test_cu_taskrunner.py:62, tests/test_sc_inventory.py:211, tests/test_laya_worker.py:291
## Evidence
Several tests depend on wall-clock timing against real spawned processes:
- `test_cu_taskrunner.py:62` starts `python -c "import time; time.sleep(60)"` then asserts `stop()` behaviour inside a 0.2s poll window; the 60s child relies on `taskkill /F /T` (Windows) or SIGTERM actually reaping it, or the process leaks for a minute.
- `test_sc_inventory.py:211` spawns a 60s sleeper with `timeout=1`.
- `test_cu_env_guest_protocol.py:98` sleeps 2s; `test_laya_worker.py:291` a 30s sleeper.
These are fixed sleeps, not condition polling, so loaded CI machines flake (assert fires before the child reaches the expected state) and every failure leaves stray 30-60s processes.
## Recommendation
Replace fixed sleeps with poll-until-condition helpers (deadline loop on observable state), use short sleeps (0.5-2s) where the child only needs to be "alive", and add try/finally cleanup that kills spawned PIDs even on assertion failure.
## Verification
Run `pytest tests/test_cu_taskrunner.py tests/test_sc_inventory.py -x` under `pytest-repeat`/load; observe timing failures and orphaned `time.sleep` processes via `ps`/`Get-Process`.

## Answer
test_cu_taskrunner sleeper 60s -> 20s with try/finally `stop()` cleanup; test_sc_inventory timeout sleeper 60s -> 10s; test_laya_worker timeout worker 30s -> 5s; test_cu_env_guest_protocol hung reader 2s -> 0.5s. All still exercise the same code paths with bounded stray-process risk.

Status: resolved
