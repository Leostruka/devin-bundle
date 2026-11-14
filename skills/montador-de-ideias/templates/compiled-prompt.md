---
schema_version: 1
artifact: .devin/specs/<slug>-compiled-prompt.md
dossier_ref: .devin/specs/<slug>-idea-dossier.md
original_prompt_sha256: <sha256_of_verbatim_seed_prompt>
status: APPROVED
date: YYYY-MM-DD
---

# Super-Prompt Compilado: <Project Name>

## 1. Prompt Original (Preservado Intacto)

> SHA-256: `<sha256_of_verbatim_seed_prompt>`

```text
<EXACT_VERBATIM_USER_PROMPT_WITHOUT_ANY_MODIFICATION>
```

## 2. Registro de Mudancas Aprovadas pelo Usuario

Todas as expansoes e refinamentos abaixo foram submetidos ao usuario via `ask_user_question` com opcoes e trade-offs antes de compilar o prompt final:

| ID | Trecho / Ideia Original | Expansao / Refinamento Proposto | Opcao Escolhida pelo Usuario | Justificativa (Filosofia + Dor + Primeiros Principios) |
|---|---|---|---|---|
| D1 | `<Original excerpt or implicit gap>` | `<Proposed refinement>` | `<Approved option>` | `<Why this honors the philosophy and heals the pain>` |

## 3. Super-Prompt Compilado (Pronto para Execucao)

```markdown
# Nivel de Esforco Obrigatorio: MAX
# Perfil Operacional: Staff Product Architect + Principal Tech Lead + Security & Performance Engineer
# Referencia de Dossie: .devin/specs/<slug>-idea-dossier.md

## 1. Missao, Filosofia Inegociavel e Dor a Sanar
<Compiled mission, philosophy, root problem, acute pain point, North Star metric, counter-metric, and aggressive non-goals>

## 2. Superioridade de Mercado e Evidencia OSINT
<Synthesized competitive teardown rules: competitor traps to avoid and structural advantages to enforce>

## 3. Arquitetura de Primeiros Principios, Modulos Profundos e NFR Budgets
<Deep modules, bounded contexts, ADRs with kill criteria, and strict numeric NFR budgets>

## 4. Requisitos Obrigatorios de Hardening e Otimizacao Atomica
<Parse-don't-validate boundaries, timeouts, overwrite refusal, UTF-8 pinning, secret hygiene, complexity floors, streaming, and native acceleration rules>

## 5. Requisitos Obrigatorios de Hardening e Otimizacao Modular
<Narrow seams, fail-closed gates, Envelope v2 provenance, blast-radius isolation, batching, and critical-path rules>

## 6. Especificacao de Cada Superficie de Contato (Facilitar, Resolver, Impressionar, Ser Intuitivo)
<Per-surface requirements with TTV targets, step-count caps, error recovery messages, and UX/DX craft bar>

## 7. Criterios de Aceite e Verification Functions (VFs)
<Numbered acceptance criteria with exact gate/expect/evidence commands and held-out verification>
```
