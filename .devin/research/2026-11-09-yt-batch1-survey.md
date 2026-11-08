# YouTube batch-1 survey (2026-11-09)

6 links (metadata pre-fetched to `.devin/scratch/yt-batch1/meta.txt`).
Transcripts: `.devin/scratch/yt-batch1/transcripts/<id>.json` (whisper.cpp
base via extensions/asr/transcribe.py; PT video ASR is rough but legible).

| # | Video | Conteudo real | Veredito |
|---|---|---|---|
| 1 | iEhCLn9utDU Agent Desktop (Prism Labs/Virsel) | "Agent browser for your whole computer": asks OS Accessibility API for live UI tree instead of screenshots - 50-200ms vs 3-8s, ref-stable elements, observe-act-observe, free+OSS, Mac/Win/Linux | EVAL -> computer-use: AX-tree perception path (P2) |
| 2 | of628n5754g stage show (Benji Taylor @ X) | Claude skill encoding X design lead's full process for landing-page product demos; solves "agents have no taste" via step-by-step process, not rule lists | EVAL -> design-intelligence/media: process-as-skill pattern (P3) |
| 3 | anqN-iDO3uw Astra edita pesos do Qwen (pt-BR) | MIT study: frontier LLM edita pesos de modelo menor (Qwen) diretamente, sem gradiente/retrain, ganhos sobre base | NOTE - pesquisa ML, nao e tooling de bundle |
| 4 | z5kcsAmoZRo cancelled Claude Code | weekly limits + ToS anti-competitor; migrou p/ Dropstone (dropstone.io): CLI agent em open weights (DeepSeek/GLM/Kimi), tiers rotativos Fast/Pro/Heavy re-avaliados mensal, memoria cross-surface, safety fora do modelo (5 camadas) | EVAL -> model-routing/safety pattern (P3) |
| 5 | gEJ26rECifc PR-Agent | ex-produto comercial do CodiumAI agora OSS (13k+ stars): describe/review/improve PRs, qualquer LLM incl. local, token-aware compressed snapshots, GitHub/GitLab/Azure DevOps | EVAL -> code-review/qa-ci complement (P3) |
| 6 | g_NgCLTibiM graph engineering (Neo4j) | taxonomia: execution graphs (workflows), context graphs (decision traces), procedural graphs (skills-as-graph); "design agent work as explicit graph" | NOTE - conceitual; mapear p/ DAGs existentes depois |

## Decisoes

- YT-01 agent-desktop-eval (P2): unico caminho de percepcao sub-200ms sem
  screenshot; nosso computer-use depende de captura de tela (cu-perception
  archived). Eval: repo real (virsel-labs?), licenca, cobertura AX nos 3
  OS, se substitui/complementa o pipeline de screenshot+OCR atual.
- YT-02 stage-show-eval (P3): skill como processo completo (nao lista de
  regras) e padrao reutilizavel p/ skills de design/media do bundle; eval o
  formato do skill e o que daria p/ destilar p/ design-intelligence.
- YT-03 dropstone-eval (P3): rotacao mensal de modelos por tier vs nosso
  bundle-models.json estatico; safety-em-camadas-fora-do-modelo vs nossos
  hooks PreToolUse. Eval: licenca, self-host real, se ha licao de routing.
- YT-04 pr-agent-eval (P3): reviewer OSS maduro c/ snapshot comprimido por
  tokens; eval se agrega ao code-review skill (contexto diferente = menos
  falso positivo) ou e redundante.

Sem issues para videos 3 e 6 (pesquisa/conceitual - registrar-only).

## Evidencia

- Transcripts: `.devin/scratch/yt-batch1/transcripts/*.json`.
- Dropstone verificado: dropstone.io + docs.dropstone.io (lineup 1.8:
  Fast=DeepSeek V4.1 Flash, Pro=GLM-5.3 Flash, Heavy=Kimi K3).
- Pesquisa pendente nos evals: repo Agent Desktop, repo stage-show,
  licenca/self-host do PR-Agent, docs Dropstone safety layers.
