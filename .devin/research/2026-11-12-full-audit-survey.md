# Full-bundle audit survey - 2026-11-12

Metodo: 4 waves paralelas (A baseline local, B hooks interacao, C skills x185, D scripts x54, F CI/docs/agents via subagents) + spot-verificacao manual dos achados de maior impacto. Baseline: audit.py 40/40 (1 warn drift benigna), pytest 2476 pass.

## Achados confirmados (spot-verified)

| # | Item | Severidade | Cascata |
|---|---|---|---|
| 1 | context-pressure le `tool_output` mas payload real e `tool_response` | alta | metrica morta; stderr spam |
| 2 | marker context-pressure.json nunca reseta por sessao (session_start=2026-09-07, 26975 calls) | alta | p=2059% permanente |
| 3 | cascata 1+2: compact-gate sempre `due` -> 2 daemon asks (~3.6-4.2s) por PostToolUse | alta | latencia em toda tool call |
| 4 | compact-gate._ensure_daemon sem fail-fast proc.poll() (patch existe em laya_client, nao propagado) | media | hang 60s in-hook |
| 5 | audit.py nunca sai non-zero - step de CI vacuo | alta | gate falso-verde |
| 6 | job `ci` needs omite `changes` - skip de changes pode dar verde | media | gate incompleto |
| 7 | manifest.json skills[14] original_path com BEL char (`arena` corrompido) | media | path quebrado no install |
| 8 | rag: 2 pointers quebrados (.devin/research/rag-practices.md, .devin/adr/004) | media | dead refs |
| 9 | leo + ask-bundle referenciam docs/DEVIN-CLI-COMPATIBILITY.md ausente do manifest docs[] | media | dead pointer no live |
| 10 | scripts: envelope exit-0-com-ok:false (subagent-trace, install-ledger, spec-consistency) | media | contrato [36] |
| 11 | subprocess utf-8 pins faltando: gh-pr-assignee:52, validate-mermaid:55 | baixa | cp1252 corruption |
| 12 | main(argv) obrigatorio latente: simplify-scan, pulse, rules-coverage, subagent-trace | baixa | crash se entrar em chain |
| 13 | docs staleness: README hooks 11->13, TOOLS-MAP 12/11 contraditorio, HOOKS-PIPELINE "ten commands", SKILL-TIERS 178->185, README rules 28->24, COMPATIBILITY 12.17/TOOLS-MAP 11.234 vs registry 12.43, agents/README 6->21, VALID_PROFILES 27->28 | media | docs mentem |
| 14 | COMPATIBILITY.md clama audit.py checa bundle-identity - nao checa | media | phantom guardrail |
| 15 | profiles: sentinel sem write; reviewer exec vs PROFILE_DENY; coverage.json dangling x2 | media | subagent quebrado |
| 16 | ci.yml `^docs/` dead pattern; actions pinning inconsistente (pages SHA, ci/release float) | baixa | padrao morto/supply-chain |
| 17 | social-midia nested names != dir basename (8) | baixa | convencao? |
| 18 | SKILL-TIERS mojibake CJK char | trivial | typo |

## Nao-defeitos verificados

- `\\\\` em original_path = escape JSON legitimo de path Windows
- config drift = preferencia do usuario + hooks-block legacy (esperado)
- PermissionRequest vazio: evento existe, sem binding por design (falta de surface)
- todos os 27 modulos referenciados nas chains existem; _hookrun fail-open cobre `main(argv)` ausentes das chains
- `_hookrun` timing: pre-exec 37ms total; session-start 191ms; pre-write 119ms - todos sob budget exceto compact-gate (#3)

## Issues

Agrupadas abaixo.
