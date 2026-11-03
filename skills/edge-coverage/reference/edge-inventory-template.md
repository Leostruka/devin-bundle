# Edge Inventory: <unit/feature>

Scope: <files/functions under test>  Date: <ts>  Author: <agent>
Rule: write this table BEFORE implementing tests. Every row -> >=1 test.
Every test -> >=1 row. Orphans are defects.

## Input boundaries

| ID | Category | Input/state | Boundary exercised | Expected | Test name | Status |
|----|----------|-------------|--------------------|----------|-----------|--------|
| B1 | numeric  | n = limit-1 | upper bound below | accept   | test_foo_limit_minus1_ok | DONE |
| B2 | numeric  | n = limit   | upper bound exact | accept   | test_foo_limit_ok | DONE |
| B3 | numeric  | n = limit+1 | upper bound over  | reject Err | test_foo_limit_plus1_err | TODO |
| B4 | degenerate | input=[]  | empty             | empty out, no crash | test_foo_empty_ok | TODO |
| B5 | encoding | s=BOM+CRLF  | encoding edge     | normalized | test_foo_bom_crlf | TODO |

## State / transitions

| ID | From | Event | Expected transition | Illegal variant | Test name | Status |
|----|------|-------|---------------------|-----------------|-----------|--------|
| S1 | init | submit | init -> running | submit from closed must reject | test_state_submit_closed_err | TODO |

## Error paths

| ID | Branch | Trigger | Asserted (type + payload + post-state) | Test name | Status |
|----|--------|---------|----------------------------------------|-----------|--------|
| E1 | timeout | clock > limit | TimeoutError, op=None, no partial write | test_fetch_timeout_cleans | TODO |

## Concurrency / resources

| ID | Edge | Method | Expected | Test name | Status |
|----|------|--------|----------|-----------|--------|
| C1 | same op twice concurrently | two threads, barrier | one wins, one errors | test_op_double_submit | TODO |
| R1 | queue at capacity+1 | fill then +1 | backpressure, no loss | test_queue_overflow | TODO |

## Oracle summary

| Row groups | Oracle used |
|------------|-------------|
| B1-B5 | expected output |
| S1 | reference state machine |
| E1, C1, R1 | invariant assertions |

## Coverage report (fill at close)

Rows total: <n>  Covered: <n>  Deliberately skipped + reason: <n>
Surviving mutants reviewed: <n killed / n justified>
