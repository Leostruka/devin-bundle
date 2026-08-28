---
name: using-skills
description: Use when starting any conversation and before taking any non-trivial action.
---
**If you were dispatched as a subagent to execute a specific task, ignore this skill.**

**If you think there is even a 1% chance a skill might apply to what you are doing, you ABSOLUTELY MUST invoke the skill.**

**IF A SKILL APPLIES TO YOUR TASK, YOU DO NOT HAVE A CHOICE. YOU MUST USE IT.**

This is not negotiable. You cannot rationalize your way out of this.

## The Rule

**Invoke relevant or requested skills BEFORE any response or action** — including clarifying questions, exploring the codebase, or checking files. If it turns out wrong for the situation, you don't have to use it.

**Before entering plan mode:** if you haven't already brainstormed, invoke the `/grilling` skill first.

Then announce "Using [skill] to [purpose]" and follow the skill exactly. If it has a checklist, create a todo per item.

## Skill Priority

When multiple skills apply, process skills come first — they set the approach, then implementation skills carry it out. `/grilling` and `/diagnosing-bugs` are the most common process skills, but the rule holds for any of them.

- "Let's build X" → `/grilling` first, then implementation skills.
- "Fix this bug" → `/diagnosing-bugs` first, then domain skills.
- "Just change a button color" or "rename this" → `/review-cadence` first to decide whether to skip grilling and review at the end.

## Red Flags

These thoughts mean STOP—you're rationalizing:

| Thought | Reality |
|---------|---------|
| "This is just a simple question" | Questions are tasks. Check for skills. |
| "I need more context first" | Skill check comes BEFORE clarifying questions. |
| "Let me explore the codebase first" | Skills tell you HOW to explore. Check first. |
| "I can check git/files quickly" | Files lack conversation context. Check for skills. |
| "Let me gather information first" | Skills tell you HOW to gather information. |
| "This doesn't need a formal skill" | If a skill exists, use it. |
| "I remember this skill" | Skills evolve. Read current version. |
| "This doesn't count as a task" | Action = task. Check for skills. |
| "The skill is overkill" | Simple things become complex. Use it. |
| "I'll just do this one thing first" | Check BEFORE doing anything. |
| "This feels productive" | Undisciplined action wastes time. Skills prevent this. |
| "I know what that means" | Knowing the concept ≠ using the skill. Invoke it. |

## Platform Adaptation

You are running in Devin CLI. Invoke skills with `/<skill-name>`. If a skill is not installed or you are unsure which skill applies, invoke `/tool-and-skill-discovery` first, or read `SKILL.md` files from your configured skill directories:

- Windows: `%APPDATA%\devin\skills\`
- macOS/Linux: `~/.config/devin/skills/`

## User Instructions

User instructions (`.devin/global_rules.md`, `.devin/rules/*.md`, direct requests) take precedence over skills, which in turn override default behavior. Only skip skill workflows or instructions when your human partner has explicitly told you to.
