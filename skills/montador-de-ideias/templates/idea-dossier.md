---
schema_version: 1
artifact: .devin/specs/<slug>-idea-dossier.md
skill: montador-de-ideias
original_prompt_sha256: <sha256_of_verbatim_seed_prompt>
status: APPROVED
date: YYYY-MM-DD
---

# Dossie Mestre da Ideia: <Project Name>

## 1. Filosofia, Problema Raiz e Dor (Alinhado com o Usuario)

- **Filosofia Central e Visao de Mundo**: <core philosophy confirmed via ask_user_question>
- **Problema Raiz (Causa Estrutural vs. Sintoma)**: <root problem statement>
- **Dor Aguda a Sanar (Quem sofre, frequencia, custo atual)**: <pain point profile>
- **North Star Metric**: <primary measurable metric>
- **Counter-Metric (Guardrail de Qualidade)**: <counter-metric that prevents gaming>
- **Non-Goals (O que a ferramenta se recusa a ser)**:
  - <Non-goal 1>
  - <Non-goal 2>

## 2. Dossie Investigativo & OSINT de Mercado ("Olhar de Jornalista")

### 2.1 Fontes Primarias, Fragmentos e Furos Investigados

| Fonte / Canal OSINT | Tipo (Issue, Vaga, Changelog, Review, Pacote, Wayback) | Evidencia Verificada (URL / Citacao / Hash) | O que Revela sobre o Mercado |
|---|---|---|---|
| `<Source 1>` | `<Type>` | `<Evidence>` | `<Insight>` |

### 2.2 Teardown Competitivo e Matriz de Superioridade Absoluta

| Concorrente / Alternativa | Arquitetura Real Observada | Falha Estrutural / Gargalo Provado | Dor Gerada no Usuario | Nossa Vantagem Estrutural + Metrica de Superioridade |
|---|---|---|---|---|
| `<Incumbent 1>` | `<Observed architecture>` | `<Cited bottleneck>` | `<User pain>` | `<Why and how we beat it measurably>` |

## 3. Justificativa por Primeiros Principios (Verdade Fundamental de Cada Area)

| Decisao / Pilar do Produto | Axioma Fisico, Matematico ou Cognitivo (Fundamento da Area) | Derivacao por Primeiros Principios | Por que Vence Qualquer Abordagem Convencional |
|---|---|---|---|
| `<Decision 1>` | `<Doherty / Cache locality / Shannon / etc.>` | `<Mechanism>` | `<Measurable proof>` |

## 4. Arquitetura Master (Product Manager + Tech Lead + Staff Architect)

### 4.1 JTBD & Backlog Priorizado (RICE + Kano)

| ID | Job Story (JTBD) | Kano (Basic / Performance / Delighter) | Reach | Impact | Confidence | Effort | RICE Score | Criterio de Sucesso Mensuravel |
|---|---|---|---|---|---|---|---|---|
| F1 | `When ..., I want ..., so I can ...` | `<Class>` | `<R>` | `<I>` | `<C>` | `<E>` | `<Score>` | `<Pass/fail metric>` |

### 4.2 Deep Modules, Fronteiras e Contratos

| Modulo | Interface Publica (Minima e Tipada) | Complexidade Encapsulada Internamente | Invariantes Garantidos |
|---|---|---|---|
| `<Module 1>` | `<Signatures / CLI / API>` | `<Internal mechanics>` | `<Invariants>` |

### 4.3 ADRs com Alternativa Rejeitada e Kill Criterion

- **ADR-01: <Decision Title>**
  - **Contexto**: <problem and constraints>
  - **Decisao**: <chosen architecture>
  - **Alternativa Rejeitada**: <runner-up option and why it lost>
  - **Kill Criterion**: <exact quantitative threshold that forces revisiting this ADR>

### 4.4 Orcamentos de Requisitos Nao-Funcionais (NFR Budgets)

| Eixo | Meta (p50) | Teto Maximo (p95 / p99) | Como Sera Medido (VF) |
|---|---|---|---|
| Latencia / Tempo de Resposta | `<val>` | `<val>` | `<command/probe>` |
| Consumo de Memoria / Recursos | `<val>` | `<val>` | `<command/probe>` |
| Time-to-Value (Onboarding) | `<val>` | `<val>` | `<command/probe>` |

## 5. Hardening e Otimizacao (Nivel Atomico e Nivel Modular)

### 5.1 Nivel Atomico (Funcoes, Inputs, Queries, Payloads, I/O)

| Componente Atomico | Hardening (Sanitizacao, Tipos, Timeouts, Segredos, Idempotencia) | Otimizacao (Complexidade, Memoria, Streaming, Rust/Stdlib) | Gate de Verificacao |
|---|---|---|---|
| `<Atom 1>` | `<Atomic hardening controls>` | `<Atomic optimization controls>` | `<Test / command>` |

### 5.2 Nivel Modular (Subsistemas, Seams, IPC, Isolamento, DAG)

| Fronteira Modular | Hardening (Least Privilege, Fail-Closed, Envelope v2, Bulkhead) | Otimizacao (Caminho Critico, Batching, Cache Conteudo-Enderecado) | Gate de Verificacao |
|---|---|---|---|
| `<Module Boundary 1>` | `<Modular hardening controls>` | `<Modular optimization controls>` | `<Test / command>` |

## 6. Superficies de Contato (Facilitar, Resolver, Impressionar, Ser Intuitivo)

| Superficie de Contato | Ator | Como Vai Facilitar (TTV e Zero-Config) | Como Vai Resolver (Ponta a Ponta + Recuperacao de Erro) | Como Vai Impressionar (Velocidade, Craft e Delight) | Como Sera Intuitivo (Modelo Mental e Poka-Yoke) |
|---|---|---|---|---|---|
| `<Surface 1: CLI / UI / API / Onboarding>` | `<Human / Agent>` | `<Facilitate spec>` | `<Resolve spec>` | `<Impress spec>` | `<Intuitive spec>` |
