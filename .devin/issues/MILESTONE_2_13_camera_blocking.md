# MILESTONE 2 / ISSUE 13: `skills/camera-blocking/` + presets Blender - workflow video-to-hero

Status: planned · Source: youtube.com/watch?v=mvfo3pUiCCA (Kyle Skelly; corroborado via moderncreator.app + qiita reproduction; template de prompt nao publicado - template e design nosso) · Matrix: `.devin/research/MILESTONE_NEXTGEN_MATRIX.md` sec B#9/G · Blocked-by: none · Blocks: none

## Contexto & Valor

- Pipeline verificada: blockout low-poly em Blender + camera path automatico -> playblast MP4 -> LLM multimodal extrai prompt segundo-a-segundo -> Seedance 2.5 repinta mantendo camera/framing (imagens de referencia do produto real melhoram aderencia) -> hero de site com scroll-scrub.
- `blender-operator` ja e o musculo generico (exec loop bpy completo); faltam os presets de blocking/playblast e a skill que orquestra o fluxo.
- Valor: transforma Blender headless em ferramenta de direcao de camera para video-AI; saida web = scaffold deterministico (playhead bound to scrollY).

## Brain (Skill)

- `skills/camera-blocking/SKILL.md` (nova, frontmatter padrao):
  - Convencoes de blockout: greybox low-poly, so camera importa, look irrelevante.
  - Fluxo: `wrapper.py launch` -> preset blockout -> `camera_rig.py` -> `playblast.py` (mp4) -> agente (multimodal) gera prompt segundo-a-segundo no formato template -> handoff externo (Seedance-class) -> scaffold scroll.
  - Template de prompt: referencias nomeadas + "hard location map" (proibe invencao de camera) + beats por timestamp `t=0.0s..t=Ns`.
  - Scaffold scroll: HTML/JS gerado no projeto do usuario (video pausado, `currentTime` = f(scrollY)); nunca autoplay/loop solto.
  - Cross-links: `operate-blender` (musculo), `creative-engineering` (estilo de repintura), `animation-direction` (beats/timestamps).

## Muscle (Extension)

- `extensions/blender-operator/presets/`:
  - `blockout.py` - kit de primitivas (boxes/cylinders, material cinza flat, ground plane, luz basica).
  - `camera_rig.py` - helpers de path (orbit, dolly, crane, tracking target, exploded-view spread via keyframes de escala/posicao).
  - `playblast.py` - render rapido viewport/EEVEE -> mp4 (args: fps, res, in/out frames).
- Todos invocaveis via `wrapper.py exec --file presets/x.py -- --args`.

## Step-by-step

0. Presets + self-test em cena minima (camera orbita box, renderiza 24f mp4).
1. SKILL.md com fluxo + template + scaffold snippet.
2. `validate-skill-format.py`; entrada no `manifest.json`/`skill-discovery` routing.
3. Gate: `pytest` (contrato: presets existem e sao chamaveis; skill valida); smoke real se blender presente (`wrapper.py --self-test` + playblast 1s); `audit.py` 0 errors.

## Non-goals

Sem client Seedance/Higgsfield (SaaS externo = template apenas); sem MCP bridge (exec loop existente basta); sem gerar video real no CI; sem assets pesados no repo.
