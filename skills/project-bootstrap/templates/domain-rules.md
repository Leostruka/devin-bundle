---
trigger: glob
globs:
  - "src/**"
  - "app/**"
description: Domain and business rules for this project — edit globs to match the paths where they apply
---

# Domain rules

<!-- Business rules and domain invariants. Keep it short and action-oriented;
detail lives in .devin/CONTEXT.md and .devin/adr/. Do NOT duplicate global
AGENTS.md rules — this file injects only when the globs match. -->

- <!-- Example: monetary values use integer cents; never floats. -->
- <!-- Example: `Order` state transitions only via src/domain/order_fsm.py. -->
