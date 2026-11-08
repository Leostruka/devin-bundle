# Eval: PR-Agent (issue #426) - 2026-11-09

Source video: youtu.be/gEJ26rECifc (DevOps Toolbox).

## What it is

`The-PR-Agent/pr-agent` (ex `qodo-ai/pr-agent`) - Qodo handed the project
to a community org; license returned to **Apache-2.0** (was AGPL v3;
PyPI shows MIT - either way permissive). ~15.5k stars, v0.46.0, explicitly
"community-maintained legacy project", distinct from Qodo's commercial
offering.

Tools: `/review`, `/improve`, `/ask`, `/describe` - each a single LLM
call (~30s). "PR Compression" handles large diffs. JSON-configurable
prompts. Providers via litellm: OpenAI, Anthropic, Gemini, Ollama/local,
any OpenAI-compatible endpoint. VCS: GitHub, GitLab, Bitbucket,
Azure DevOps, Gitea, CodeCommit. Runs as GH Action (prebuilt Docker) or
CLI (`pip install "pr-agent[github]"`, `pr-agent --pr_url ... review`).

## Live verification (this machine)

- `pip show pr-agent` → not installed; `litellm` not installed.
- `credentials.toml` → only `[gcal]`; **no LLM provider key** present.
- `ollama` → not installed.

=> Cannot execute a real review locally without adding a provider
(Ollama install or an API key). That is itself the eval finding.

## Fit with devin-bundle

- Our review stack: `code-review` skill, `reviewer`/`repo-reviewer`
  subagent profiles, `qa-ci` gate - all **same-model** review (SWE-2).
  PR-Agent's value proposition is precisely a *different* model's eyes.
- Adoption paths:
  a) GH Action on this repo - needs an `OPENAI_KEY`/provider secret;
     reviews every PR automatically. Zero local deps.
  b) Local CLI + Ollama - fully offline, but adds a local LLM runtime
     (~GBs) for a secondary reviewer.
  c) Skip - same-model review + held-out tests already gate pushes.
- Cost/benefit: single-call ~30s reviews are cheap; the compressed
  snapshot approach is a good pattern regardless (could inform our own
  reviewer prompts).

## Recommendation

**TRACK, not adopt yet.** Real, permissive, maintained - but requires an
LLM provider we don't have locally. If the user adds an OpenAI/Anthropic
key or wants automated PR review on GitHub, path (a) is a ~15min setup.
Until then the marginal value over same-model review is unproven - a
proper held-out comparison (PR-Agent vs reviewer subagent on the same
PR) needs a provider first. Revisit when a key exists.

## Evidence

- Repo: github.com/The-PR-Agent/pr-agent (Apache-2.0 per repo, MIT on
  PyPI v0.46.0)
- Handover post: qodo.ai/blog/qodo-is-handing-pr-agent-over-to-the-community
- Local check: no provider key/Ollama on this machine (commands above)
