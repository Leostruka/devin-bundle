# r15-flaky-reap-01: POSIX group verification deadline too tight

## Problem

`test_spawn_timeout_cleans_tree` failed CI on macOS three times (PRs #267, #277, #279) with `tree_cleanup False` while the test's own `ps` diagnostic showed the process group already dead.

`_reap_posix_group` (sc_process.py): after TERM->grace->KILL and root reap, the group-absence verification loop gives up after 5s. On loaded macOS CI runners, SIGKILL delivery plus reparented-member reap by launchd can exceed 5s, producing a transient false `tree_cleanup` result. The result is cached on the tree dict, so the false verdict sticks.

## Evidence

- CI job 125547816290: `tree_cleanup False; pgid=1715 members:` (empty member list = group dead at diagnostic time, ~ms after the False verdict)
- Same test passed on rerun, all platforms, in every occurrence

## Fix

Verification deadline 5s -> 15s in `_reap_posix_group` only. Still bounded; reap path already spends up to ~10s in waits before this loop. Semantics unchanged: still returns False if members survive.
