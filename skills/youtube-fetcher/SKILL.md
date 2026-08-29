---
name: youtube-fetcher
description: Use when you need to turn a YouTube URL and provider-supplied caption/metadata JSON into a raw, timestamped transcript + metadata Markdown note under `.devin/notes/youtube/` for later structured extraction, without auto-installing dependencies, invoking yt-dlp/Whisper, or calling the network.
version: 1.0.0
---

# youtube-fetcher

Deterministic, stdlib-first capture of YouTube transcripts and metadata into `.devin/notes/youtube/`. The skill only accepts caption + metadata JSON from a provider or fixture; it never installs `youtube-transcript-api`, `requests`, `yt-dlp`, or Whisper, and it never calls the network.

## When to use

- A user gives you a YouTube URL and asks for a raw transcript note.
- A provider or fixture already hands you caption + metadata JSON.
- You want a deterministic Markdown artifact that separates raw transcript from any summary or inference.
- You intend to hand the note off to `structured-knowledge-extraction` for entity/relation extraction.

## When NOT to use

- You want the agent to auto-install `youtube-transcript-api`, `requests`, `yt-dlp`, or Whisper.
- You want the adapter to call YouTube, oEmbed, or any other network endpoint.
- You want summaries, bullet points, or inferred takeaways mixed into the raw transcript.
- You want to overwrite an existing `.devin/notes/youtube/` file without explicit approval.

## Core operations

All output stays inside `.devin/notes/youtube/`. Persistence requires both `--write` and `--approve`. No external dependency is installed or called by the skill.

| Operation | Purpose | Default output |
|---|---|---|
| `validate` | Check that a URL or bare ID is a supported YouTube reference. | `{ "video_id": "..." }` to stdout |
| `render` | Render provider/fixture JSON into raw transcript + metadata Markdown. | Markdown to stdout; writes note only with `--write --approve` |

## Usage

From the bundle root:

```bash
python skills/youtube-fetcher/scripts/fetch.py validate <url-or-id>
python skills/youtube-fetcher/scripts/fetch.py render <source.json> [project] [--write] [--approve] [--overwrite]
```

After installation the helper is available at `~/.config/devin/skills/youtube-fetcher/scripts/fetch.py`.

## Rules

1. **Stdlib-first, dependency-free, and network-free.** The `validate` and `render` paths use only the Python standard library. No packages are installed and no network calls are made.
2. **Provider JSON only.** Captions and metadata must be supplied by a provider or fixture JSON. The adapter does not call YouTube, oEmbed, or any other endpoint.
3. **Strict host allowlist.** Only `youtube.com`, `www.youtube.com`, `m.youtube.com`, `music.youtube.com`, and `youtu.be` are accepted for URL validation. Similar-looking hosts are rejected.
4. **Input and output size limits.** JSON inputs above 50 MiB and Markdown outputs above 100 MiB are rejected. No partial file is written on failure.
5. **Truthful language and caption type.** The note records the language and caption type supplied by the provider. Missing values are recorded as `unknown`; no value is invented.
6. **Duplicate preservation unless explicitly approved.** An existing note is never overwritten unless `--overwrite` is given in addition to `--write --approve`.
7. **Timestamps are preserved and validated, not fabricated.** Each caption line keeps its start time; the rendered Markdown only includes timestamps that exist in the source. Negative or non-finite timestamps are rejected.
8. **Raw transcript stays separate from summaries/inferences.** The `## Raw transcript` section contains only the provided text. Summaries or interpretations go through `structured-knowledge-extraction`, not into this note.
9. **Containment and atomic writes.** Output is written under `.devin/notes/youtube/` only. Symlink components that would escape `.devin` are rejected, and the temporary file is removed on any failure.
10. **Handoff to structured extraction.** Every note ends with a `## Next step` section documenting how to pass the raw note to `structured-knowledge-extraction`.

## Source and license attribution

`youtube-fetcher` is conceptually adapted from JimmySadek/youtube-fetcher-to-markdown (MIT) after source review. No code, prompts, or templates are copied from the upstream project. The core implementation uses only the Python standard library.

- youtube-fetcher-to-markdown (MIT): https://github.com/JimmySadek/youtube-fetcher-to-markdown
- README: https://github.com/JimmySadek/youtube-fetcher-to-markdown/blob/main/README.md
- Skill: https://github.com/JimmySadek/youtube-fetcher-to-markdown/blob/main/SKILL.md
- Script: https://github.com/JimmySadek/youtube-fetcher-to-markdown/blob/main/scripts/fetch_transcript.py
- License: https://github.com/JimmySadek/youtube-fetcher-to-markdown/blob/main/LICENSE

## Cross-references

- `/structured-knowledge-extraction` — extract entities, relations, and evidence from the raw note produced by this skill.
- `/research` — verify upstream source claims and integration options.
- `/mcp-context-audit` — measure tool-definition cost before enabling any MCP-based fetch provider.
