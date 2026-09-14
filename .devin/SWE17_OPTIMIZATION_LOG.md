# SWE-1.7 Optimization Log

Otimização do bundle para o agente SWE-1.7 (base Kimi K2.7). Data: 2026-09-14.

## Política aplicada

- **Max (`swe-1-7`)** → perfis de julgamento/read-only (`architect`, `researcher`, `reviewer`, `domain`, `repo-reviewer`). Mitigação do overthinking: cercas com cap de leitura/busca e condições de parada explícitas.
- **Medium (`swe-1-7-medium`)** → perfis de manipulação de código e execução de scripts (`implementer`, `debugger`, `qa-ci`, `issue-tracker`, `triage-labels`). Execução direta, sem planning loops.
- **CoT explícito** → SWE-1.7 não possui planejamento longo nativo; templates de execução induzem raciocínio passo a passo.

## Arquivos modificados

### A. Correção de roteamento (docs alinhados aos pins reais)

| Arquivo | Mudança |
|---|---|
| `skills/dispatching-parallel-agents/SKILL.md` | Tabela de profiles: `implementer`/`debugger` → medium-role; adicionada role rule (Max=julgamento+fences, Medium=execução); Model Selection reescrito (perfis pinam por role, não "todos max"); `qa-ci` adicionado; task signals corrigidos para medium-role. |
| `skills/leo/SKILL.md` | `qa-ci` corrigido para medium-role (`BUNDLE_MEDIUM_MODEL`); Bundle context e Advice passam a descrever o split Max/Medium. |
| `skills/executing-plans/SKILL.md` | Pin do `qa-ci` corrigido `swe-1-7` → `swe-1-7-medium`. |
| `skills/primeagent-reference/SKILL.md` | Tabela de profiles: `implementer`/`debugger` → medium-role; adicionado `qa-ci`; nota de role rule SWE-1.7. |

### B. Fences anti-overthinking (perfis Max)

| Arquivo | Técnica |
|---|---|
| `agents/architect.md` | `## Bounds`: cap de 6 leituras, 2-3 opções, stop ao poder recomendar, 1 check por risco nomeado. |
| `agents/researcher.md` | `## Bounds`: budget de 10 lookups, stop ao responder, stop após 2 lookups sem fato novo, sem re-leitura. |
| `agents/reviewer.md` | `## Bounds`: escopo = diff, 1 check por risco, 1 run de verificação por dúvida, stop com vereditos nos 2 eixos. |
| `.devin/agents/repo-reviewer.md` | `## Bounds`: escopo = diff, 1 run por comando, stop com vereditos Standards+Spec. |
| `.devin/agents/domain.md` | `## Bounds`: responder só de CONTEXT.md/ADRs; declarar ausência em vez de varrer o codebase. |
| `skills/code-review/code-reviewer.md` | Bloco `## Bounds` no template: escopo = range nomeado, 1 check por risco, stop por seção. + linha CoT ("work through each check step by step"). |
| `skills/dispatching-parallel-agents/task-reviewer-prompt.md` | CoT no Part 1: vereditar requisito a requisito antes de avançar. |
| `skills/dispatching-parallel-agents/re-review-prompt.md` | CoT no Scope: localizar→comparar→vereditar por finding. |

### C. Re-pin Medium (perfis mecânicos)

| Arquivo | Mudança |
|---|---|
| `.devin/agents/issue-tracker.md` | `model: swe-1-7` → `swe-1-7-medium` (CRUD de Markdown = manipulação direta). |
| `.devin/agents/triage-labels.md` | `model: swe-1-7` → `swe-1-7-medium` (mapeamento estático de labels). |

### D. Injeção de CoT (templates de execução)

| Arquivo | Técnica |
|---|---|
| `skills/dispatching-parallel-agents/implementer-prompt.md` | `## Plan Before Acting`: plano de 3-5 linhas (arquivos, ordem, primeiro gate) antes de editar; execução imediata; sem leitura fora do plano. |
| `agents/implementer.md` | `## How to work`: plano explícito 3-5 linhas → executar; não re-derivar requisitos. |
| `agents/debugger.md` | Metodologia com CoT explícito (declarar hipótese + resultado esperado antes de cada teste); stop na primeira hipótese que explica todos os sintomas. |
| `agents/qa-ci.md` | `## Procedure`: 5 passos ordenados; 1 run por gate ("never re-run to make sure"). |
| `skills/implement/SKILL.md` | Linha CoT: plano de 3-5 linhas antes de editar, execução imediata. |
| `skills/afk-loop/SKILL.md` | CoT no loop por issue: plano antes de editar (failing test primeiro). |
| `skills/executing-plans/SKILL.md` | CoT no Step 2: declarar ação + resultado esperado antes de cada passo. |
| `skills/autonomous-gates/SKILL.md` | CoT no Step 2: declarar esperado, comparar observado vs esperado. |

### E. Política documentada

| Arquivo | Mudança |
|---|---|
| `AGENTS.md` | Rule 20: bullet "SWE-1.7 effort split" (Max=fences, Medium=execução+CoT). |
| `docs/MODEL-GUIDE.md` | Implicação 6: CoT explícito + fences nos perfis Max; manter cercas ao editar. |

## Não modificado (decisões)

- `data/bundle-models.json` — roles já corretos.
- `data/recipes.json` — recipes já roteiam implement→medium, refine→max.
- `docs/TOOLS-MAP.md` — já refletia o split correto (fonte da verdade).
- `scripts/*.py` (behavioral-nudge, constraint-pinning) — lógica executável, fora do escopo .md/.json/.yaml.
- `devin-N.ps1`, `devin-session-launcher.ps1`, `export.ps1`, `install.ps1` — PowerShell, fora de escopo.
- `agents/researcher.md` — mantido em Max (síntese exige julgamento); over-reading mitigado por fences, não por downgrade de modelo.

Ledger de gates: `.devin/ledgers/swe17-optimization.md`.
