# SDD ledger — plan: .devin/plans/2026-09-19-system-control.md

## Index
- QA precondition: complete (2 held-out tests collected; RED confirmed)
- Task 1: complete (commit b02cdec, review clean)
- Task 2: complete (policy, one-shot confirmation, review clean)
- Task 3: complete (bounded one-shot execution, review clean)
- Task 4: complete (persistent owned sessions, review clean after rework)
- Task 5: complete (bounded event streams, review clean after rework)
- Task 6: complete (verified file ops, review clean after rework)
- Task 7: complete (native Windows adapter, review clean after rework)
- Task 8: complete (native Linux adapter, review clean after rework)
- Task 9: complete (native macOS adapter, review clean after rework)
- Task 10: pending
- Task 11: pending
- Task 12: pending

## Commit Boundaries
- 3b3aa5e: branch base
- b02cdec: Task 1 complete — safe recovery point
- Task 2: b8867ab — safe recovery point
- Task 3: cee94aa — safe recovery point
- Task 4: 75d179d — safe recovery point
- Task 5: 80ae8e6 — safe recovery point
- Task 6: bcca26f — safe recovery point
- Task 7: 8d34289 — safe recovery point
- Task 8: c3f6658 — safe recovery point
- Task 9: <pending commit> — safe recovery point

## Detail Log
QA precondition: worktree created at `D:/Programing/ai_workspace/devin-bundle-system-control`.
QA precondition: `pytest --collect-only` found 2 tests; direct run failed on missing `sc_contract` as expected.
Task 1: fix round 1/5 (9 reviewer findings addressed, 0 open; 47 visible tests green).
Task 1: fix round 2/5 (stale identity and negative numeric inputs addressed, 0 open; 51 visible tests green).
Task 1: minor (deferred): bounded-drain join can wait on inherited grandchild pipe handles.
Task 1: minor (deferred): consolidate strict numeric helper across OS adapters.
Task 1: minor (deferred): top-level schema remains intentionally extensible; document before v1 freeze.
Task 1: complete (commit 3b3aa5e..b02cdec, review clean).
Task 2: RED confirmed; three review rounds closed atomicity, Windows read races, and malformed metadata handling.
Task 2: 668 passed, 1 skipped; audit 0 errors; independent Spec/Standards review PASS.
Task 3: RED confirmed; review rounds fixed cleanup evidence, exception ownership, token burn, and spill residue.
Task 3: 708 passed, 1 skipped; 128 targeted/held-out passed; audit 0 errors.
Task 3: committed cee94aa.
Task 4: RED confirmed (held-out daemon recovery authored first).
Task 4: review found blocker (live-pidfile respawn) + 4 majors; rework closed all.
Task 4: 749 passed, 12 skipped (11 pending held-out T5/T6); audit 0 errors.
Task 4: committed 75d179d.
Task 5: held-out `test_event_integrity.py` authored first (6 contracts).
Task 5: review Spec PASS/Standards FAIL — provider double-poll race, nested secret leak; rework closed all.
Task 5: 782 passed, 6 skipped; audit 0 errors; held-out 6/6.
Task 5: committed 80ae8e6.
Task 6: held-out `test_file_integrity.py` authored first (5 contracts).
Task 6: review Spec/Standards FAIL — dirfd opens missing, non-atomic overwrite, streamed-hash trust; rework closed all 10.
Task 6: 829 passed, 3 skipped; audit 0 errors; held-out 5/5.
Task 6: committed bcca26f.
Task 7: held-out `test_windows_adapter.py` authored first (5 contracts, real host).
Task 7: review Spec PASS/Standards FAIL — double CloseHandle, argtypes, fake recursion; rework closed all 6.
Task 7: T3 deferred Popen->Job race CLOSED via CREATE_SUSPENDED + Toolhelp resume.
Task 7: lead fixed held-out epoch bug + os.kill probe + module-pop pollution; CIM fallback ordering.
Task 7: 863 passed, 3 skipped; audit 0 errors; held-out 5/5.
Task 8: held-out `test_linux_adapter.py` authored first (6 contracts, seam-based).
Task 8: review Spec PASS/Standards FAIL — waitid EINVAL 5.3-5.4, untyped parse errors, verify->open reuse window, start_time optional; rework closed all.
Task 8: 906 passed, 3+6 skipped (6 pending held-out T10); audit 0 errors; held-out 6/6.
Task 9: held-out `test_macos_adapter.py` + brief authored first; broker held-out `test_broker_contract.py` authored (skip-guarded until T10).
Task 9: review Spec/Standards FAIL — bogus `select.EVFILT_PROC` (real: `KQ_FILTER_PROC`), `ps -p` rc!=0 mis-typed as BackendUnavailable; rework closed all 7.
Task 9: 906 passed, 9 skipped; audit 0 errors; diff --check clean; held-out 5/5.
