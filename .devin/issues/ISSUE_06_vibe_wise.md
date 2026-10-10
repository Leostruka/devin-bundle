# ISSUE 06: Adapt `nykooi1/vibe-wise`, learning-first collaboration mode

Status: planned (research done) · Source: `github.com/nykooi1/vibe-wise` (MIT, 3.3k) · Ledger: `.devin/research/4_fronts_recon.md`

## Contexto & Valor

- VibeWise = plugin ("You build. AI writes"): AI asks the user's approach first, explores tradeoffs, explains unfamiliar concepts; user owns design decisions; AI implements then explains what changed and why. Structure: `skills/learn` (SKILL.md + behavior.md + onboarding + state-templates), `skills/reset`, `hooks/` for learning-context restore/reset, `.agents/plugins` + `.claude-plugin` + `.codex-plugin` packaging.
- Value: an opt-in mentor mode. Differs from `grilling` (stress-tests a plan) and `intake` (captures intent): VibeWise flips who proposes first, the user designs, the agent teaches and executes. Good for unfamiliar stacks, junior ramp-up, deliberate-practice sessions.
- Port cost is low: it's prompt/skill-shaped, no engine. Adapt to our hooks + `project-memory` for learning notes instead of their state templates.

## Brain (Skill)

- **New `learn-mode` skill** (adapted, not copied): when-to-use (unfamiliar stack, user wants ownership), behavior contract: agent asks approach questions before designing, presents tradeoffs, pauses for user decisions, implements after approval, then explains diff + why.
- **Touch `grilling`**: cross-reference, grilling = adversarial plan stress-test; learn-mode = pedagogical co-design. Keep distinct.
- Learning notes: route to `project-memory` skill (existing) instead of VibeWise's reset hooks.

## Muscle (Extension)

- Minimal: optional `hooks/` addition, a `learn-context.py` restore/reset hook adapted from their Python scripts (state file under `.devin/memory/learn/`), only if session-persistence proves needed; otherwise the skill + project-memory covers it.
- No extension strictly required; evaluate their `hooks/` source during step 1 before writing anything.

## Step-by-step (on authorization)

0. Clone repo, read `skills/learn/*` (SKILL.md, behavior.md, onboarding.md, state-templates.md) and `hooks/` scripts; diff their prompt structure vs our `writing-skills` checklist.
1. Draft `learn-mode/SKILL.md` in our format (when-to-use, behavior contract, gates, off-ramp to `implement`/`execution` once design is approved).
2. Optional `learn-context.py` hook only if notes persistence earns it (verify `project-memory` gap first).
3. Gate: run one unfamiliar-stack task in learn-mode; verify agent asked approach first, waited for approval, explained the diff after.
4. Update `ask-bundle`/`leo` router entry.

## Non-goals

No plugin packaging copy, no reset-hook cargo-cult if `project-memory` suffices, no forced mode (opt-in only, mirrors Rule 7 execute-first default).
