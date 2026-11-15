# yt-batch4 survey: 5AkurBDSYwo (2026-11-15)

Source: [China Just Open-Sourced Humanlike Memory for AI Agents (Tencent DB)](https://www.youtube.com/watch?v=5AkurBDSYwo), Cloud Codes, 740s, 2026-08-02. Transcript: ASR whisper.cpp `base` (native subs unavailable). Evidence: `.devin/scratch/yt-batch4/asr/5AkurBDSYwo.{vtt,txt}`.

## Facts reported by the source (claims, not verified by us)

- Tencent Cloud DB team open-sourced (MIT) a memory plugin for OpenClaw agent runtime (~384k stars, launched late 2025). ~10.4k stars in ~117 days.
- Benchmark claims (vendor-produced): OpenClaw harness solve rate 33% -> 50% on LongMemEval-style tasks; token use 221M -> 86M (-61%) on a 200-question run; SWE-bench 58.4 -> 64.2 on ~1/3 fewer tokens; artificial-analysis long-doc test 44 -> 47.5.
- Architecture: four layers. L0 raw conversation log; L1 atoms (fact/preference/constraint, extracted every ~5 turns); L2 scenes (grouped atoms); L3 persona (habits/conventions/defaults, rebuilt every ~50 new memories). Agent reads top-down: persona first, atoms on demand, L0 for exact wording.
- Mechanism: forgetting treated as compression, not a bug (Ebbinghaus/hippocampal-replay analogy). Episodes replayed, patterns pulled out, episode fades.
- Plumbing: local SQLite + sqlite-vec, hybrid BM25 + vector retrieval merged by RRF, ~5 results/recall, 5s timeout that skips injection rather than stalling the turn. All layers human-readable files (persona/scenes in markdown, canvas in mermaid).
- Persona-mem benchmark (preference drift tracking): 48% -> 76% (+28 points).
- Open problems named in the video: prefix-cache breakage when injecting memory into the prompt prefix (issue #120 open); search query operator escaping (177-comment thread); vendor-produced numbers, no independent reproduction yet (mem0/Zep benchmark dispute precedent); Docker image defaults to Tencent's own endpoint plus managed-memory cloud upsell launched 4 days before the repo.
- Competition context: Tencent's own Youtu team shipped a rival 6-layer plugin for the same host (-35% tokens, own numbers); mem0 ~62k stars, Letta ~24k, MemOS ~10.5k. Convergence pattern across the field: "sketch in context, evidence on disk, path between them."

## Bundle relevance (high)

Direct overlap with the bundle's memory surface:

- `project-memory` skill: plain-text notes in `.devin/`, our L0/L1 equivalent, but no consolidation to scenes/persona and no retrieval scoring.
- `memory-retrieval.py`, `memory-post-edit.py`, `memory-post-exec.py`, `memory-stop.py` hooks: memory plumbing already exists; injection and capture points are ours too.
- `context-budget.py` / `context-pressure.py` / context-folding skill: we already treat context as scarce; Tencent's numbers (if real) validate the direction and quantify the benefit.

## Assessment: ADAPT (evaluate, not adopt)

Candidate: spike-evaluate the Tencent memory plugin (and the L0-L3 layered model itself) against `project-memory`:

1. Vendor numbers are unreproduced: any adoption claim requires a held-out measurement on our own traces (same discipline as #632).
2. The L0->L3 consolidation schedule (atoms every 5 turns, persona every 50 memories) is an implementable pattern independent of their code; could extend `project-memory` without a new dependency.
3. Their open issues are our risk map: prefix-cache poisoning from injected memory blocks (check our injection hooks), search-query operator escaping.
4. Local SQLite + sqlite-vec + RRF is a plausible retrieval backend for `memory-retrieval.py` if grep-based retrieval underperforms.
5. Portability question (their own roadmap item): memory as owned artifact that survives framework switches, aligned with bundle philosophy of `.devin/` plain files.

## Decision log

- ADAPT: issue filed (evaluation spike; see GitHub issues).
- Not ADOPT: unproven vendor benchmarks, cloud upsell default, operator-escaping bug, prefix-cache regression, all named in the source itself.

## Provenance

- `.devin/scratch/yt-batch4/5AkurBDSYwo.info.json` (formats stripped)
- `.devin/scratch/yt-batch4/asr/5AkurBDSYwo.{vtt,txt}`
- `.devin/scratch/yt-batch4/metadata.md`
