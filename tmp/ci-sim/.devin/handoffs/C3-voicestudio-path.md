# Contract C3: VoiceStudio backend path in voicebox wrapper

- Role: `implementer`
- Lane: worktree `D:\Programing\ai_workspace\devin-bundle\.worktrees\voicestudio-path`, branch `feat/voicestudio-path`
  - setup: `git worktree add .worktrees/voicestudio-path -b feat/voicestudio-path`
- Objective: `extensions/voicebox/wrapper.py` gains a VoiceStudio backend
  targeting `http://127.0.0.1:3900` (OpenAI-compatible `/v1/audio/speech`
  and `/v1/models`). Selection: `--backend voicestudio` flag or
  `VB_BACKEND=voicestudio` env; default stays `voicebox` (:17493, jamiepine API).
- Requirements:
  - Same safety contract: loopback-only host validation (apply to :3900 too),
    whitelisted actions (doctor/generate/models), bounded bodies, timeouts,
    typed JSON envelope, `status: missing` + hint when backend down.
  - `generate` maps to POST /v1/audio/speech {model,voice,input,response_format:wav}
    and writes the returned audio bytes to --out.
  - `models` maps to GET /v1/models.
  - Update `skills/tts/SKILL.md`: document `--backend voicestudio` +
    AGPL-3.0 / default-engine non-commercial caveat.
- Boundaries: don't remove or break the voicebox path; no model downloads;
  no new deps (stdlib only). No em-dash prose.
- Termination: max 25 turns.
- VFs (in worktree): `python extensions/voicebox/wrapper.py doctor` ->
  `status: missing` on unreachable :17493; `--backend voicestudio doctor` ->
  `status: missing` on unreachable :3900; existing
  `pytest -q tests/test_voicebox_wrapper.py` green.
- Report: `.devin/handoffs/C3-voicestudio-path-out.md`.
