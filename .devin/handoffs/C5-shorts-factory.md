# Contract C5: `shorts-factory` skill + stock-footage fetcher

- Role: `implementer` (runs after C3 merges; wants the backend-path option)
- Lane: worktree `.worktrees/shorts-factory`, branch `skill/shorts-factory`
- Objective: MoneyPrinterTurbo-equivalent assembly from existing bundle pieces.
- Output:
  - `skills/shorts-factory/SKILL.md`: pipeline doc — script (agent) ->
    narration (`tts`, either backend) -> alignment (`extensions/asr`) ->
    scene plan JSON -> render (`remotion-render` or `animation-direction`) ->
    ffmpeg composite; aspect flags 9:16/16:9/1:1.
  - `extensions/stock-footage/fetch.py`: thin Pexels/Pixabay fetcher —
    API key from `PEXELS_API_KEY`/`PIXABAY_API_KEY` env, plain urllib HTTP,
    typed JSON errors, `missing` when no key, never fabricate.
  - `manifest.json` + counts reconciled by orchestrator (not the worker).
- Boundaries: no auto-publish, no batch daemon, no new deps.
- VFs: dry-run produces scene plan JSON without keys; skill-format + audit green.
- Report: `.devin/handoffs/C5-shorts-factory-out.md`.
