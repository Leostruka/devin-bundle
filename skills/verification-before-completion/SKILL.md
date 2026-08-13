---
name: verification-before-completion
description: Use when about to claim work is complete, fixed, or passing.
---
# Verification Before Completion

## Overview

**Core principle:** Evidence before claims, always.

**Violating the letter of this rule is violating the spirit of this rule.**

## Pre-Execution Gate: Verification Functions (VFs)

Before dispatching an implementer, define Verification Functions — concrete,
checkable assertions that the completed work must satisfy. VFs distill the
spec into local checks the implementer can self-verify.

### How to define VFs

For each requirement in the spec, write a VF as a natural-language assertion
with a verification command:

```
VF1: API returns 200 for valid input → curl -s -o /dev/null -w "%{http_code}" localhost:3000/api/endpoint -d '{"valid":"data"}'
VF2: API returns 400 for invalid input → curl -s -o /dev/null -w "%{http_code}" localhost:3000/api/endpoint -d '{"invalid":"data"}'
VF3: Type checker passes → npx tsc --noEmit
VF4: All tests pass → npm test -- --grep "endpoint"
```

### When to define VFs

- Always for tasks dispatched to implementer subagents (include VFs in the brief)
- Always for tasks with clear acceptance criteria
- Optional for exploratory or research tasks (no implementation to verify)

### The dual gate

```
Gate 1 (PRE): Define VFs before dispatching implementer
  → Implementer receives VFs in brief
  → Implementer must run every VF and show output before claiming DONE

Gate 2 (POST): Fresh verification evidence before accepting DONE claim
  → Controller re-runs VFs independently (or dispatches reviewer to do so)
  → If any VF fails, implementer re-enters fix loop
```

VFs are not extra work — they are the spec made executable. If you cannot
write a VF for a requirement, the requirement is ambiguous and needs
clarification before implementation.

## The Iron Law

```
NO COMPLETION CLAIMS WITHOUT FRESH VERIFICATION EVIDENCE
```

If you haven't run the verification command in this message, you cannot claim it passes.

## The Gate Function

```
BEFORE claiming any status or expressing satisfaction:

1. IDENTIFY: What command proves this claim?
2. RUN: Execute the FULL command (fresh, complete)
3. READ: Full output, check exit code, count failures
4. VERIFY: Does output confirm the claim?
   - If NO: State actual status with evidence
   - If YES: State claim WITH evidence
5. ONLY THEN: Make the claim

Skip any step = lying, not verifying
```

## Common Failures

| Claim | Requires | Not Sufficient |
|-------|----------|----------------|
| Tests pass | Test command output: 0 failures | Previous run, "should pass" |
| Linter clean | Linter output: 0 errors | Partial check, extrapolation |
| Build succeeds | Build command: exit 0 | Linter passing, logs look good |
| Bug fixed | Test original symptom: passes | Code changed, assumed fixed |
| Regression test works | Red-green cycle verified | Test passes once |
| Agent completed | VCS diff shows changes | Agent reports "success" |
| Requirements met | Line-by-line checklist | Tests passing |

## Red Flags - STOP

- Using "should", "probably", "seems to"
- Expressing satisfaction before verification ("Great!", "Perfect!", "Done!", etc.)
- About to commit/push/PR without verification
- Trusting agent success reports
- Relying on partial verification
- Thinking "just this once"
- Tired and wanting work over
- **ANY wording implying success without having run verification**

## Rationalization Prevention

| Excuse | Reality |
|--------|---------|
| "Should work now" | RUN the verification |
| "I'm confident" | Confidence ≠ evidence |
| "Just this once" | No exceptions |
| "Linter passed" | Linter ≠ compiler |
| "Agent said success" | Verify independently |
| "I'm tired" | Exhaustion ≠ excuse |
| "Partial check is enough" | Partial proves nothing |
| "Different words so rule doesn't apply" | Spirit over letter |

## Key Patterns

**Tests:**
```
✅ [Run test command] [See: 34/34 pass] "All tests pass"
❌ "Should pass now" / "Looks correct"
```

**Regression tests (TDD Red-Green):**
```
✅ Write → Run (pass) → Revert fix → Run (MUST FAIL) → Restore → Run (pass)
❌ "I've written a regression test" (without red-green verification)
```

**Build:**
```
✅ [Run build] [See: exit 0] "Build passes"
❌ "Linter passed" (linter doesn't check compilation)
```

**Requirements:**
```
✅ Re-read plan → Create checklist → Verify each → Report gaps or completion
❌ "Tests pass, phase complete"
```

**Agent delegation:**
```
✅ Agent reports success → Check VCS diff → Verify changes → Report actual state
❌ Trust agent report
```

## When To Apply

**ALWAYS before:**
- ANY variation of success/completion claims
- ANY expression of satisfaction
- ANY positive statement about work state
- Committing, PR creation, task completion
- Moving to next task
- Delegating to agents

**Rule applies to:**
- Exact phrases
- Paraphrases and synonyms
- Implications of success
- ANY communication suggesting completion/correctness
