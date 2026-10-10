# Recon Ledger, 4 Improvement Fronts

Date: 2026-10-10 · Status: research complete, issues drafted
Artifacts: `.devin/issues/ISSUE_0{1..4}_*.md`

## Extraction method (Social Media mandate)

- `webfetch` on `/embed/captioned/` → post captions only (no audio track, no `video_url` in HTML).
- Third-party transcript sites (supadata, gettranscribe, socialcrawl) → endpoints obfuscated/auth-walled; abandoned.
- Working path: `yt-dlp` (installed 2026.08.19) → IG media accessible → `-x --audio-format wav` → local `whisper.cpp` (`b5454` win-x64 build, `ggml-base.bin` 148MB multilingual) → full transcript. Deterministic, offline, reusable, candidate to become `extensions/asr/` (see Issue 04).

---

## Reel 1, DeRX9KpJPlT (@plattipusofficial, EN, ~46s)

### Transcript (raw, whisper.cpp ggml-base)

> Every camera leaves an invisible digital fingerprint. AI images leave absolute zero. Millions of pixels catch light and no two catch it equally. Tiny flaws in the silicon stamped on every photo in the exact same spot. Researchers call it PRNU. Strip the picture away. What's left is the fingerprint. In 2006, it matched 2,700 photos to nine cameras, even two of the same model. An AI image is made from math, not light. Test its noise against any camera. The match is zero. It has noise, just nobody's fingerprint. We're platypus, a research and production lab. Our research works with Gaussian splats. Real places captured from real photos.

### Caption sources cited

- Lukáš, Fridrich & Goljan, "Digital Camera Identification from Sensor Pattern Noise", IEEE TIFS 2006
- Corvi et al., ICASSP 2023 (synthetic image detection)
- plattipus.com/research/houdini-usd-gsplat

### Method extracted

1. Metadata labels fail: "AI info" tags live in the file, lost on screenshot/re-upload.
2. PRNU (photo-response non-uniformity): per-pixel sensor sensitivity variance = fixed spatial pattern stamped on every capture.
3. Pipeline: denoise image → residual noise = fingerprint candidate → correlate against camera reference pattern → presence = real capture, absence = computed image.
4. Match metric used in literature: PCE (peak-to-correlation-energy).

## Reel 2, DeNUYLkRWsz (@matheusolivsilv, PT-BR, ~73s)

### Transcript (raw, whisper.cpp ggml-base, PT)

> É muito guru que está vendendo cursos de como fazer isso, porque temos detalhes que fazem total diferença da animação… Primeiro eu gravo um vídeo e aí com o Claude eu gero uma transcrição com os tempos exatos de quando eu falei algo e o que aquele algo significa. Isso é speech-to-text mais enriquecimento de dados. E eu peço pro Claude analisar os frames e considerar o que ia aparecer na gravação. Com essas informações a gente monta um plano de cenas, acompanhando a minha explicação. Se eu falo de uma fila de pedidos, ele vai gerar uma animaçãozinho de filas e as coisas chegando. Só que tem uma etapa importante: antes de implementar renderização, eu preciso me mostrar o plano e esperar a minha aprovação. Esse é o gate do meu processo. [Cada vez que eu corrijo,] eu corrijo ali antes de ele gerar mais tokens e gastar mais tempo fazendo uma animação que eu vou descartar. Depois que eu aprovo, ele vai lá e usa skills que usam After Effects, JSX/HTML e várias outras coisas. Gera o código que vai ser renderizado com Remotion, é basicamente um código React. Nesse fluxo, a animação é feita com código. Código controla quando cada elemento aparece, como ele se move e quanto tempo fica na tela. Remotion renderiza esses frames, a animação é combinada com a minha gravação.

(Caption: modelo "Opus 5.5", multimodal, reasoning sobre frames, criatividade nas gerações.)

### Pipeline extracted

1. Narrated source video → ASR + semantic enrichment (what was said + when + meaning).
2. Multimodal frame analysis → what should appear on screen.
3. Scene plan synced to narration (mentions queue → queue animation).
4. **Mandatory approval gate before rendering**, cheap correction, no wasted generation.
5. Post-approval: skills drive After Effects / JSX / HTML → generated React code → Remotion render.
6. Code = timing authority (appear/move/duration) → frames composited over recording.

---

## Front 1, upstream compaction port (tamaratran, MIT, TS, 7.6k★)

Agent-CLI compaction plugin + npm lib. Replaces summarization compaction with **System-1 decisions** (hosted API; model superseded by `laya`, offline/free), a non-autoregressive decision model. Same primitive as our `laya`: `noul` questions (P(true)).

### Algorithm (from README, verbatim-verified)

1. Pair `tool_use`↔`tool_result` by id. Pin first message + newest `preserveRecentMessages` (default 6).
2. Build state: whole conversation, results → `ok, N chars (omitted)` notes.
3. Fit state into `maxStateTokens` (25k) via escalating stages: truncate inputs 1000→200→60 chars → abridge texts head+tail → collapse old messages → one-line tool-call summaries → drop call-less messages → fold call-only runs.
4. Per non-pinned call, two `noul` questions: keep call? keep result verbatim?
5. Batch questions under `maxRequestTokens` (30k), same state resent per request, concurrent, merge.
6. Decisions at `keepThreshold` 0.5: keepResult≥T → keep both; keepCall≥T → keep call + truncate result to `truncateHeadChars` (300); else drop both.
7. Rebuild: empty messages removed, no orphan results. Engine failure → throw → caller fallback.
8. `reductionRatio < 0.25` → not worth it, keep original.

### "Smart Window" synthesis (cross-source)

| Source | Trigger | Target | Keeps |
|---|---|---|---|
| Haystack `SlidingWindowCompactor` | `compact_at` = 0.7×window | `compact_to` = 0.4×window | system + latest task + complete turns; assistant+toolResult atomic |
| Google ADK | token threshold (primary) / turn count |, | summary of evicted events |
| upstream port | caller-driven (`/compact`, auto) | scored reduction | pinned + scored-survivors, verbatim |
| **Recommended (laya port)** | **0.70×model window** (SWE-2 262k → ~183k) | **0.40× (~105k)** | system/first + newest 6 + laya-scored items |

Smart Window = adaptive effective window: trigger→target hysteresis band + per-item retention scoring instead of blind recency cut.

---

## Front 3, github.com/storytold (44 repos)

Flagship: **craft suite**, clean-room Rust reimplementations of Adobe/Office media tools (MIT/Apache-2.0):

| Repo | Domain | Note |
|---|---|---|
| artcraft | IDE for interactive image/video creation | "build the scene before you generate it": 2D/3D compositing, character posing, kitbash blocking, image→location, image→3D mesh, identity transfer |
| filmcraft | Premiere-style video edit | Rust, native + WASM/browser |
| photocraft | Photoshop | layers/masks/adjustments/type, real PSD |
| vectorcraft / wordcraft / pdfcraft / gridcraft / deckcraft / lightcraft / soundcraft / cadcraft | Illustrator/Word/Acrobat/Excel/PowerPoint/Lightroom/ProTools/AutoCAD | same clean-room Rust pattern |
| craft-libs | shared Rust crates monorepo | promotable libs (e.g. RAW support) |
| spark | 3D Gaussian Splatting renderer for THREE.js | .PLY/.SPZ/.SPLAT/.KSPLAT/.SOG; GPU splat editing, skeletal anim, shader graph, links to reel1 (gsplat needs real captures) |
| storyteller-ml / realtime-voice-conversion / vits-finetuning | audio ML | Tacotron, voice conversion |
| LiveScan3D, bevy-mocap, UE plugins | 3D capture/mocap | legacy |

### Absorbable pattern

Media ops as **deterministic code pipelines**, agent-native: craft apps dispatch every action through typed command registries exposed via CLI, JSON control channel, and built-in **MCP server** (filmcraft 650+ cmds `filmcraft-cli mcp`; photocraft 500+ cmds `photocraft-cli run`). Decision: consume their engines (MIT/Apache) via `extensions/craft-bridge`; build only seam (`scene_manifest`) + gaps. See ISSUE_03.

---

## Front 5: PPISP (NVIDIA nv-tlabs/ppisp)

Transcript (user-provided, PT-BR) describes learning the camera instead of fixing the scene. Verified = **PPISP**: learned post-processing for radiance fields: per-frame exposure + chromaticity-homography color correction, per-camera vignetting + CRF tone mapping, controller predicts corrections for novel views (auto-exposure/AWB analog), scene frozen during controller distillation. Upstream: `github.com/nv-tlabs/ppisp`, project page research.nvidia.com/labs/sil/projects/ppisp. Fixes floaters/ghosts from photometric variance in 3DGS/NeRF; links `ai3d-gen` intake + Issue 02 (PRNU vs photometric model = complementary camera signals).

## Front 6: vibe-wise (nykooi1, MIT, 3.3k)

Plugin for Claude Code/Codex: "You build. AI writes." Learning-first collaboration: agent asks user's approach before designing, presents tradeoffs, explains concepts, implements post-approval, explains diff after. Structure: `skills/learn` (SKILL.md + behavior.md + onboarding.md + state-templates.md), `skills/reset`, `hooks/` (learning-context restore/reset), plugin manifests for claude/codex/.agents. Port = adapted `learn-mode` skill + optional context hook (project-memory may suffice).

## Front 7: mattpocock/skills (MIT, aihero.dev/skills)

Upstream dirs: `engineering/` (20: code-review, codebase-design, diagnosing-bugs, domain-modeling, grill-with-docs, implement-spec, implement, improve-codebase-architecture, pr, prototype, research, retro, tdd, to-spec, to-tickets, triage, wayfinder, wizard, ask-matt, setup-*), `productivity/` (grill-me, grilling, handoff, teach, to-questionnaire, wait-what, writing-for-agents), `misc/` (git-guardrails, migrate-to-shoehorn, scaffold-exercises, setup-pre-commit). Heavy overlap with our skills (likely our seed source). Plan = port audit: diff-per-skill `port_matrix.md`, update drifted in place, port new ones agnostically, skip with reason.

## Existing bundle assets (Brain/Muscle mapping base)

- Skills: `implement-laya`, `context-folding`, `context-hygiene`, `media-tools`, `creative-engineering`, `ai3d-gen`, `operate-blender/godot/spline`, `comfyui-operator`, `computer-use`, `cu-realtime`, `scrape-tools`, `fact-check`, `mesh-utils`.
- Extensions: `laya-tools` (worker + decision contract, off→shadow→assist), `media-tools` (fx: dither/halftone/pixel_sort/vhs/noise_field/edge_detection… + `intent.py` laya routing), `ai-tools`, `scrape-tools`, `mesh-utils`, operators, `system-control`.
- Gaps: no image-forensics, no ASR extension (whisper.cpp path proven this session), no animation/remotion muscle, no compaction engine.

## Out of scope confirmed

No production code written. Issues = planning artifacts only.
