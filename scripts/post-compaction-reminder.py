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
7. DON'T declare done without verifying — run the check, show the evidence. No verification = not done.
8. DON'T accept a summary as verification — read the primary source yourself. Subagent returns are leads, not answers. (Rule 12)
9. DON'T trust ANY subagent return without re-reading the source yourself — confirmed, refuted, or "not found" all require verification. (Rule 12)
10. DON'T assume Devin CLI is a security sandbox — it runs with your permissions. Run untrusted code externally. Guard against reward hacking in self-improvement. (Rule 13)
</post_compaction_reminder>"""

print(REMINDER)
sys.exit(0)
