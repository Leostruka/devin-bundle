# extensions/gcal plan.py: tasks -> roteiro

status: resolved
priority: P2
source: github issue #345/#346 (app backlog)

## Evidence
Deterministic greedy packer: tasks (name, minutes, priority) into free_slots in priority order; unscheduled tasks flagged (overcommit signal).

## Task
plan.py pack(tasks, slots, day_end) -> roteiro JSON: [{task,start,end}] + {unscheduled, slack_min}. Tests cover: exact fit, overflow, priority order, empty slots.

## Answer

Shipped: extensions/gcal/plan.py - greedy first-fit by (priority, order), atomic blocks, unscheduled/slack_min/overcommit in output. Tests: exact fit, overflow, priority, empty.
