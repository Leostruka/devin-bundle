---
name: pr-review
description: Use when the user asks to review a Pull Request on GitHub with inline comments and code suggestions via the GitHub API. Enforces a repeatable cycle of check -> comment/suggest -> check next, with a gates ledger for evidence.
version: 1.0.0
model: swe-1-7
subagent: reviewer
---

# PR Review (Inline GitHub)

> **REQUIRED SUB-SKILLS:** `/unlazy`, `/gh`, `/writing-plans`, `/code-review`
> **MANDATORY BUDGET:** `standard` or `strict`
> **Language:** follow the PR / repository language (Portuguese if the codebase is in Portuguese)

Use this skill when the user asks for a PR review that must be published as **inline GitHub comments with ` ```suggestion ` blocks** or as a **single review with multiple comments**. It is deliberately more rigorous than a quick "looks good" — every comment is a gate that must be checked before it is posted.

## When to Use

- User explicitly says "review this PR" with the intent of publishing on GitHub.
- Review must contain concrete, applicable suggestions (not generic comments).
- Need to avoid hallucinated line numbers — the agent must confirm each target line in the head commit before posting.
- The PR has enough risk to justify the overhead of a ledger (not a one-liner fix).

## When NOT to Use

- The PR is a draft and the user only wants a high-level opinion.
- The repository is not on GitHub (no `gh` access).
- The user says "just check it quickly" and does not want comments published.

## Core Workflow

The review is executed as a series of **cycles**:

```
CHECAR  ->  COMENTAR/SUGERIR  ->  IR PARA O PRÓXIMO
```

Each cycle handles one concern (one standards or spec item). No cycle advances before the line is confirmed in the PR head and the comment is posted.

## Global Constraints

- Do **not** edit the PR's code locally; only publish review comments.
- Do **not** comment on topics the user explicitly told you to ignore (e.g., "ignore the signature part").
- Each suggestion must be **applicable in one click** on GitHub; use ` ```suggestion ` blocks.
- Use `gh api` with `--field` (not `gh pr review`, which does not support per-line positioning).
- Comments must be in the same language as the repository.
- Every comment gets a gate in the ledger.

## Pre-Flight Checklist

Before the first cycle, gather:

1. `gh pr view {N} --json headRefOid --jq .headRefOid` — the head SHA.
2. `gh pr diff {N} -- path/to/file` for each file that will be commented on.
3. A confirmed `{file: line}` map for every target comment.
4. The `.devin/ledgers/{date}-pr{N}-review.md` file created via `/unlazy`.

## Cycle Steps

For each comment target:

### 1. CHECAR

Confirm the target content exists at the head SHA. Prefer `git show HEAD:<path>` or `gh pr diff {N} -- <path>`.

Example:

```bash
gh pr diff 241 -- app/Services/TimeCardRecordPDFService.php | findstr "public static function getViewData"
```

If the expected text is not present, **stop** and re-map the line. Do not publish a comment against a stale line.

### 2. COMENTAR e SUGERIR

Build a `body` with:

- A short, actionable explanation.
- A ` ```suggestion ` block with the exact replacement, including correct indentation.
- Optional: a brief note if the suggestion is a multi-line range.

Post via `gh api`:

```bash
gh api repos/{owner}/{repo}/pulls/{pull_number}/comments \
  -X POST \
  -F commit_id="$HEAD_SHA" \
  -F path="app/Services/TimeCardRecordPDFService.php" \
  -F line=58 \
  -F side=RIGHT \
  -F body="Adicionar o tipo de retorno para manter consistência com os outros métodos do serviço.\n\n\`\`\`php\npublic static function getViewData(string $month, int $chosenEmployeeId): array\n\`\`\`"
```

For multi-line suggestions, add `start_line`:

```bash
  -F start_line=89 \
  -F line=94 \
```

### 3. IR PARA O PRÓXIMO

Mark the gate in the ledger as completed with evidence (e.g., the API response id). Advance to the next cycle.

## Single-Review Payload (Optional)

If many comments are ready and the head SHA is stable, post them in one request to reduce API calls:

```bash
gh api repos/{owner}/{repo}/pulls/{N}/reviews \
  --method POST \
  --input review-payload.json
```

`review-payload.json`:

```json
{
  "commit_id": "$HEAD_SHA",
  "event": "COMMENT",
  "body": "Review com sugestões aplicáveis.",
  "comments": [
    {
      "path": "...",
      "line": 58,
      "side": "RIGHT",
      "body": "..."
    }
  ]
}
```

**Only use this after every `line` has been independently checked.**

## Verification (After Publishing)

1. List review comments: `gh api repos/{owner}/{repo}/pulls/{N}/comments`
2. Confirm each gate: path, line, and body match the ledger.
3. Open `https://github.com/{owner}/{repo}/pull/{N}/files` and visually confirm alignment.
4. Update every ledger gate with `EVIDENCE: ok` plus the comment id.

## Ledger Format

```markdown
# GATES: PR #{N} review

- [ ] G1: comentário em app/Services/TimeCardRecordPDFService.php:58
  CHECK: gh api repos/{owner}/{repo}/pulls/{N}/comments --jq '.[] | select(.path=="..." and .line==58) | .id'
  EXPECT: non-empty
  EVIDENCE: pending

- [ ] G2: comentário multi-line em app/Livewire/Modal/ModalTimeCardRecord.php:89-94
  CHECK: gh api repos/{owner}/{repo}/pulls/{N}/comments --jq '.[] | select(.path=="..." and .start_line==89 and .line==94) | .id'
  EXPECT: non-empty
  EVIDENCE: pending
```

## Risks & Fallback

- **Line moved by a new commit:** re-run `gh pr view {N} --json headRefOid` at the start of every cycle. If it changed, abort the current payload and re-map.
- **422 from GitHub on `start_line`/`line`:** the diff range may be non-contiguous. Fragment the comment into single-line comments or fall back to a non-positional `gh pr comment` (loses the inline benefit).
- **Suggestion block not accepted by GitHub:** verify indentation matches the file exactly; GitHub is strict about whitespace inside ` ```suggestion `.
- **Missing `gh` or no permission:** ask the user to run in a repo with `gh` authenticated or with a PAT.

## Do Not

- Post a comment without re-confirming the line in the head commit.
- Mix observations in the same comment; one concern per comment.
- Use generic feedback like "please fix this"; always include a ` ```suggestion ` or a concrete alternative.
- Report "review done" while any ledger gate has `EVIDENCE: pending`.
