# Analise: RF_6XrkmKsg -- "I don't need Claude Code anymore" (GG Coder demo)

## Fonte

- URL: https://www.youtube.com/watch?v=RF_6XrkmKsg
- Duracao: 6:32. Ingles. Produto: **GG Coder**, coding-agent GUI do
  proprio criador (repo linkado na descricao, comunidade Skool paga
  pitch no final ~5:50).

## Conteudo (ASR base + contact sheet 20 frames)

Demo de produto: app GUI que substitui Claude Code segundo o autor.
Claims marketing: "30% faster, 60% less usage" (nao verificaveis).

Features mostradas:

- **Agent storage**: index Rust de samples de "milhoes de repos" --
  RAG sobre codigo GitHub ("source of truth" p/ geracao).
- Multi-window layout launcher; continua projetos Claude Code/Codex.
- Quick access: branch, PRs, issues, repo GitHub.
- **Context-usage %** display por sessao.
- **Project health score** (ex.: 99/100): file-size 800-line limit,
  repo hygiene, dead markers -> botao "Review all" -> gera prompt
  "Send to GG Coder" -> agente corrige tudo.
- **Autopilot verification agent**: pos-task, verifica o trabalho;
  chamavel manualmente via @mention.
- Multi-provider (Anthropic/OpenAI/Kimi/GLM/MiniMax/OpenRouter).
- Skills built-in + slash commands customizaveis.
- Checklist: foundation->source control->design->UX->safety->
  security->performance->shipping->handover.
- **Goal system**: nome+deadline+instrucoes -> "start goal" ->
  agente executa.
- **World**: visualizacao gamificada pixel-art (personagem anda,
  spawna 4-8 agentes, clima/dia-noite por timezone local).

## Mapa feature -> bundle

| Feature GG Coder | Equivalente no bundle |
|---|---|
| health score + fix-all | `audit.py` (31 checks) + ciclo R audit->issues->fix |
| verification agent | `agents/qa-ci.md` + `skills/autonomous-gates` + check-push-green |
| goals | `.devin/scratch/` issues + `skills/afk-loop` + ledgers |
| checklist ship | `.github/PULL_REQUEST_TEMPLATE.md` + review skills |
| context % | `scripts/context-budget.py` hook |
| skills/slash commands | 101 skills |
| multi-provider | `data/bundle-models.json` (filosofia diferente: 1 familia gratis) |
| code index de repos | avaliado no M2 (codebase-memory-mcp), gated em held-out |
| world gamificado | rtsd foi REMOVIDO deliberadamente (PR #216, e400ddf) |
| multi-window/GUI | N/A (bundle e CLI) |

## Veredito: notes-only

- Demo de produto comercial do autor + pitch de comunidade paga.
  Nenhum codigo portavel; claims de performance nao verificaveis.
- Todos os conceitos uteis ja estao cobertos pelo bundle; a
  visualizacao gamificada foi removida por decisao propria.
- Insight marginal: o loop "health score -> prompt automatico de
  fix" e exatamente o que ja fazemos manualmente (audit -> issues
  -> fix). Nenhuma implementacao adicional necessaria.

## Itens implementados

- Nenhum (notes-only).
