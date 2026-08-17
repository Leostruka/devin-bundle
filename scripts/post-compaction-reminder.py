#!/usr/bin/env python3
"""PostCompaction hook: re-injects critical rule reminders after context compaction.

Evidence: instruction compliance decays 5.6% per generation step (arXiv:2605.10039).
Post-compaction re-priming counters this decay by re-injecting the highest-priority
negative constraints that are most likely to be forgotten.

Outputs reminder text to stdout (injected as context). Exit 0 = success.
"""
import sys

REMINDER = """<post_compaction_reminder>
Context was compacted. Re-priming critical rules (negative constraints only — these are the individually beneficial rule type per arXiv:2604.11088):

1. NO AI signatures in commits, files, PRs, or any deliverable. No "Generated with Devin", no "Co-Authored-By: Devin".
2. NO push without green — run local checks before committing. Fix failures in the inner loop.
3. DON'T do more than asked — action bias fails 35-65% of cases. If the bug is already fixed, inaction is correct.
4. DON'T start non-trivial tasks without checking for matching skills first.
5. DON'T volunteer architecture opinions or unsolicited alternatives. Execute clear tasks.
6. Telegraphic output — no filler, no preamble, no narration of tool calls. Start with the answer.
</post_compaction_reminder>"""

print(REMINDER)
sys.exit(0)
