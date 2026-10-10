# LAYA Master Architecture: Ledger de Integração Total

Data: 2026-10-10 · Status: blueprint aprovado em Fase 1 (camadas 4 e 7 validadas) · Supersede: `ISSUE_01_laya_compaction.md` (subsumida), menções JEV (purge list §11)
Escopo: planta baixa arquitetural. **Nenhum wrapper programado nesta sessão.**

---

## 0. Axiomas de design (vinculados a evidência)

| # | Axioma | Base |
|---|---|---|
| A1 | Laya `suggestion`/`abstain` only; nunca `allow`/`execute`. Piso = veredito determinístico; Laya só escala severidade. | `decision_contract.py` (verificado) |
| A2 | Decisões que governam ação usam **perfis frozen** no contrato (`-vN`); wording e **ordem canônica das opções são imutáveis** dentro de uma versão. Ad-hoc `predict` só na Camada 10 (advisory). | Laya flipa 30% ao inverter ordem de opções (arXiv:2610.02267); swap yes/no flipa 50.5% em Jev (arXiv:2610.00346); calibração é bound a profile+checkpoint (contrato) |
| A3 | Cascata de custo: allowlist → regex → Laya → política. Tier barato absorve a maior parte do tráfego. | Estágio intent→decision-model = mesma acurácia a 0.43× custo (arXiv:2610.00346) |
| A4 | Hooks **informam** (1 linha injetada via stdout); o agente executa. Hook nunca reescreve transcript nem executa a mutação. | Contrato de hooks verificado (`config.json`, exit 0/2, stderr≠contexto) |
| A5 | Trigger de compactação = sinal **estrutural da trajetória** × banda de pressão; nunca threshold de token isolado. | SelfCompact (arXiv:2606.23525), AutoCompact (arXiv:2610.02163) |
| A6 | Thresholds medidos em held-out próprio; calibração in-sample vaza até 17% de misses. Threshold calibrado no lado caro do erro (FP em gate de segurança é barato; FN é caro). | arXiv:2610.02267, arXiv:2610.00346, Rule 15 |
| A7 | Routing zero-shot de modelo/agente está no nível do acaso. Camada 5 é determinística-first; Laya só decide após calibração. | arXiv:2610.02267 |
| A8 | Daemon residente único (`layad`) serve TODOS os perfis; hook é cliente thin. Daemon morto → fail-degraded ao tier determinístico, nunca fail-closed cego. | Latência verificada: spawn+build = segundos; predict residente <1ms routing |

---

## 1. Mapa das 10 camadas

| Camada | Função | Perfil contrato | Muscle | Brain | Trigger |
|---|---|---|---|---|---|
| 1-2 | Triage de tarefa / issue | `skill-family-v1`, `issue-category-v1` (existem) | `workflow_routing.py` (existe) | `intake`, `triage` | UserPromptSubmit |
| 3 | Composite risk score de review | `review-risk-v1` (novo) | `laya_tools.review_risk` (novo) | `code-review`, `review-cadence` | Pre-review / skill call |
| 4 | Bash confidence gating | `cmd-risk-v1` (novo) | `laya-guard.py` hook + `layad` | `implement-laya` (update) | PreToolUse `exec` |
| 5 | Model & intent routing | `agent-route-v1` (novo, gated) | `laya_tools.route` (novo) | `skill-discovery`, `dispatching-parallel-agents` | Pre-dispatch |
| 6 | LayaGuard generalizado (harness) | `write-scope-v1`, `fetch-scope-v1` (novos) | `laya-guard.py` (matchers ampliados) | `self-extend` | PreToolUse `write\|edit\|webfetch\|mcp` |
| 7 | **Self-Compacting (foco)** | `compact-gate-v1` + `compact-item-v1` (existe) | `laya-compactor` (existe) + `layad` + notice hooks | `context-hygiene` (update), `handoff` | PostToolUse/UserPromptSubmit |
| 8-9 | Cheap reads / files at scale | `filebool-v1` (novo) | `filebool.py` (`ask_laya_glob`, `ask_laya_filebool`) | `laya-orchestrator` (novo) | Skill call |
| 10 | Agentic self-query | ad-hoc `predict` (fora do contrato, fenced) | `laya_cli.py predict` (existe) | `laya-orchestrator` | Skill call |

---

## 2. Contrato: perfis novos (frozen authoring)

Todos seguem o envelope §5.1 existente. `STATE_ALLOWED` é fechado; texto de comando/arquivo transita em `state.snippets` como **dado não-confiável** (nunca em chaves; `STATE_FORBIDDEN` bane `command|cmd|exec|sql|token|...`).

### 2.1 Request envelope (imutável, já implementado)

```json
{
  "version": 1,
  "request_id": "<uuid>",
  "profile": "cmd-risk-v1",
  "mode": "off|shadow|assist",
  "language": "en|pt|auto",
  "context": {"policy_digest": "<sha256 of active rules+hooks>", "env_id": "<host-tag>"},
  "state": {"goal": "...", "snippets": "...", "confidence_hint": "..."},
  "candidates": [{"id": "...", "role": "...", "name": "...", "scope": "..."}],
  "deadline_ms": 1000
}
```

### 2.2 `cmd-risk-v1` (Camada 4)

```json
"state": {
  "goal":            "<current task statement, 1-2 lines>",
  "snippets":        "<RAW command + cwd + shell_flavor: untrusted data>",
  "confidence_hint": "<deterministic feature vector JSON: {pipes, redirects, sudo, writes_outside_repo, network_egress, quoted_payloads, chain_ops}>"
}
"candidates": [
  {"id": "benign",           "scope": "read-only / in-repo mutation, reversible"},
  {"id": "mutating",         "scope": "state change in-scope, reversible"},
  {"id": "irreversible",     "scope": "destroy/overwrite/force-push/no reflog"},
  {"id": "egress_or_secret", "scope": "network exfil, credential touch, secret read"},
  {"id": "ambiguous",        "scope": "insufficient evidence to classify"}
]
// canonical order FROZEN as listed; __none__ reserved → abstain → fallback T1
```

**Veredito composto (escada PASS→CONFIRM→BLOCK, Laya só sobe):**

| Laya sugere | assist | shadow/off |
|---|---|---|
| `irreversible`, `egress_or_secret` | BLOCK (exit 2 + reason) | log only |
| `mutating`, `ambiguous` + `writes_outside_repo` | CONFIRM → força PermissionRequest | log only |
| `benign`, abstain/`__none__`, deadline overrun | PASS | PASS |

### 2.3 `compact-gate-v1` (Camada 7)

```json
"state": {
  "goal":            "<first_user_task ++ LAST_user_prompt verbatim>",
  "snippets":        "<session digest: tool-name histogram, touched-files set (paths only), last-3 error heads, open blockers, turns_since_last_compact>",
  "confidence_hint": "<{p, turns, tool_output_share, user_msgs}>"
}
"candidates": [
  {"id": "continue"}, {"id": "prune"}, {"id": "fold"},
  {"id": "handoff"},  {"id": "clear"}
]
// segunda chave no mesmo request: "boundary" (choice)
//   options FROZEN: {"mid_task","stage_resolved","task_shifted","__none__"}
```

`boundary` = pergunta estrutural (SelfCompact rubric): onde a trajetória está; mid-task (suprimir), stage resolvido (janela boa), escopo mudou (contexto morto).

### 2.4 `filebool-v1` (Camadas 8-9)

```json
"state": {"goal": "<boolean question, e.g. 'contains authentication data'>",
          "snippets": "<relpath + head N chars: untrusted>"}
"candidates": [{"id": "yes"}, {"id": "no"}]
```

Ordem frozen `[yes, no]`. Abstain/`__none__` → `"abstain"` no mapa de saída; nunca descartado silenciosamente.

### 2.5 `agent-route-v1` (Camada 5, gated)

```json
"candidates": [{"id": "researcher"}, {"id": "implementer"}, {"id": "reviewer"},
               {"id": "debugger"}, {"id": "self"}]
// + chave "effort": {"medium","high","max"}: choice, ordem frozen
```

Gate A7: modo `assist` bloqueado até held-out accuracy > baseline determinístico; antes disso vive em `shadow` e regras Rule-20 decidem.

### 2.6 `review-risk-v1` (Camada 3)

```json
"state": {"snippets": "<diffstat + touched-paths + test-coverage flags + commit msgs>",
          "confidence_hint": "<{files_changed, insertions, deletions, has_tests, touches_auth_paths}>"}
"candidates": [{"id": "low"}, {"id": "medium"}, {"id": "high"}, {"id": "critical"}]
// + chave "rubric" score 1-5 opcional via segunda question
```

### 2.7 `write-scope-v1` / `fetch-scope-v1` (Camada 6)

```json
"write-scope-v1": candidates {"in_scope","out_of_scope","protected_path","ambiguous"}
"fetch-scope-v1": candidates {"docs_or_code","untrusted_content","credential_endpoint","ambiguous"}
```

---

## 3. Muscle: `extensions/laya-tools/` (contratos de API)

### 3.1 Daemon residente `layad.py` (NOVO, pré-requisito de todo `assist`)

```python
def serve(config_path: str, host="127.0.0.1", port=0) -> int:
    """Sobe UM Router(preload=True) + todos os perfis enabled.
       Protocolo: mesmo envelope JSON-lines do laya_worker, sobre TCP.
       Escreve .devin/laya/daemon.json:
         {pid, port, auth_token, config_sha256, model_digests, started_at}
       auth_token exigido por request (anti-abuso local).
       Idle > idle_ttl (default 30min) → exit. fail-fast se activation_errors
       e modo assist; roda em shadow se config exigir."""

def ensure_daemon(config_path) -> dict:
    """Lazy-spawn com file lock (.devin/laya/daemon.lock).
       daemon.json válido + config_sha256 confere + health OK → reuse.
       Divergência de sha → SIGTERM + respawn. Ausente → spawn."""
```

### 3.2 Cliente thin `laya_client.py` (NOVO)

```python
def recommend(request: dict, *, timeout_ms=1000) -> dict:
    """→ recommendation | {"outcome":"abstain","reason":"daemon_down|
       deadline|malformed"}. Nunca raise no hot path."""
def batch(requests: list[dict], *, max_inflight=4) -> list[dict]
```

### 3.3 Varredura em lote `filebool.py` (NOVO, Camadas 8-9)

```python
def ask_laya_filebool(paths: list[str], question: str, *,
                      head_chars=4000, max_files=500,
                      batch_size=8, deadline_ms=1000,
                      config=".devin/laya/profile.json") -> dict:
    """Para cada arquivo: state={goal:question, snippets:relpath+head}.
       Batched via layad (queue_depth). Retorna APENAS:
       {path: {"answer": "yes"|"no"|"abstain", "calibrated_probability": f}}
       Conteúdo de arquivo NUNCA entra na janela do SWE-2.
       >max_files → erro tipado (caller particiona), não trunca quieto."""

def ask_laya_glob(pattern: str, question: str, *, root=".",
                  exclude=(), **kw) -> dict:
    """glob(pattern) → filter(exclude) → ask_laya_filebool.
       Saída idêntica: mapa path→veredito; zero bytes de conteúdo."""
```

### 3.4 Hook interceptor de Bash `scripts/laya-guard.py` (NOVO)

Registrado na lista `_hookrun` de `pre-exec-guard.py` **após** `destructive-gate.py` (consolidação 1-spawn já existe; `config.json` não muda).

```python
TIERS:
  T0 allowlist prefix (git status, ls, rg, cat…)            → PASS   # ~0ms
  T1 destructive-gate existente (regex)                     → BLOCK
  T2 feature extract + Laya via daemon (só gray zone)       → sugg|abstain
  T3 policy merge: escada PASS→CONFIRM→BLOCK, só sobe

def guard(payload):
    cmd  = payload["tool_input"]["command"]
    if t0_allowlisted(cmd):                      return PASS
    feats = extract_features(cmd)                # pipes, egress, alvos, cwd
    if feats.trivially_safe:                     return PASS
    if not laya_enabled(cfg):                    return PASS       # mode off
    rec = laya_client.recommend(req(cmd, feats), timeout_ms=cfg.deadline_ms)
    audit_log(cmd, feats, rec)                   # sempre (alimenta calibração)
    if mode != "assist":                         return PASS       # shadow
    return merge_escada(rec, feats)              # §2.2

# Camada 6 = mesma função com matchers "^(write|edit)$" → write-scope-v1
# e "^(webfetch|mcp_call_tool)$" → fetch-scope-v1, em pre-write-guard.py
```

`extract_features` é determinístico e barato; inclui classificador léxico de comando (stage 1 da cascata A3) que resolve sozinho ~70% dos casos sem tocar a Laya.

---

## 4. Camada 7: Intelligent Compaction Blueprint (FOCO)

### 4.1 Sinais (todos já mensuráveis)

```
p        = est_tokens / window          # context-pressure.py (262144, chars/4)
digest   = session digest construído no hook (snippets §2.3)
boundary = chave laya: mid_task | stage_resolved | task_shifted
```

### 4.2 Banda de pressão + pontos de avaliação

```
EVAL_FLOOR = 0.50    # abaixo: Laya nunca consultada (custo zero)
COMPACT_AT = 0.70    # ~183k: headroom p/ próximo batch de tools
COMPACT_TO = 0.40    # ~105k: histerese, anti-thrash
FORCE_AT   = 0.80    # ação obrigatória; Laya só escolhe o modo

Avaliação dispara SOMENTE quando:
  E1: UserPromptSubmit ∧ p ≥ EVAL_FLOOR        # prompt novo = sonda de fronteira, sempre
  E2: PostToolUse ∧ p ≥ EVAL_FLOOR ∧ Δcalls ≥ K=8 desde última aval
  E3: p ≥ COMPACT_AT                            # cada chamada avalia
```

### 4.3 Algoritmo (pseudocódigo normativo)

```python
def compact_gate(event, marker):
    p = marker.pressure()
    if not trigger_due(event, p, marker):      # §4.2
        return CONTINUE
    rec  = laya_client.recommend(req("compact-gate-v1", digest(marker)),
                                 timeout_ms=1000)
    marker.last_eval = now()

    floor = "continue" if p < COMPACT_AT else "prune"
    if p >= FORCE_AT: floor = "prune"          # forçado mesmo com abstain

    b = rec["boundary"];  a = rec["action"]

    # Supressores SelfCompact: rubrica vence pressão dentro da banda
    if b == "mid_task" and pending_tool_batch and p < FORCE_AT:
        a = min_severity(a, "continue")        # adia ≤ K calls
    # Escopo morto: clear > prune (compactar ruído é desperdício)
    if b == "task_shifted" and p >= EVAL_FLOOR:
        a = "handoff" if retention_signal(marker) else "clear"

    action = max_severity(a, floor)            # A1: Laya nunca relaxa o piso
    if cooldown(marker) < 10 turns:            return CONTINUE
    return inject_notice(action, p, b)         # §4.4
```

### 4.4 Entrega ao agente (A4: hook informa, agente executa)

Injeção de 1 linha (stdout em UserPromptSubmit; reason string em PreToolUse quando tool-call é a avaliação):

| action | Linha injetada |
|---|---|
| `prune` | `LAYA-GATE p=0.72 stage_resolved → rodar extensions/laya-compactor/compact.py sobre o transcript da sessão agora` |
| `fold` | `LAYA-GATE → context-folding: offload artefatos >50k p/ arquivo antes de continuar` |
| `handoff` | `LAYA-GATE → executar skill handoff → depois clear` |
| `clear` | `LAYA-GATE p=0.68 task_shifted → finalize artefatos pendentes e clear; contexto anterior é ruído` |

### 4.5 Retenção lógica garantida (sem perda)

Compactação = **Selection Game** (retenção por item, arXiv:2608.01326), não Generation Game. Camadas de sobrevivência:

1. **Pin set determinístico** (nunca vai à Laya): system prompt, first msg, última task do usuário, `preserve_recent=6`, e **keep-overrides regex**: paths referenciados por edits pendentes, testes ativos, IDs de regras pinned.
2. **Scored survivors** (`compact-item-v1`, existe): keep/truncate/drop por item; abstain → keep (fail-safe já implementado).
3. **Memória externa** (ACM): `handoff` doc + ledgers `.devin/` = long-term condensada; fold = retrieval on-demand.
4. **Pós-compactação**: `constraint-pinning.py` (PostCompaction, existe) re-injeta constraints governamentais.
5. **Qualidade**: `reduction < 0.25` → no-op; G3 held-out = tarefa downstream a partir do transcript compactado deve resolver paths/comandos referenciados (ISSUE_01).

---

## 5. Brain: `skills/laya-orchestrator/SKILL.md` (design)

```yaml
---
name: laya-orchestrator
description: Use when a cheap typed check beats reading files into context -
  batch file classification (auth data? has tests?), risk scoring, triage -
  or before dispatching subagents/choosing effort. Not a substitute for
  reading primary sources (Rule 12); Laya ranks and abstains, never proves.
---
```

Conteúdo normativo da skill:

1. **Quando interrogar** (Camadas 8-10): `>10 arquivos` e pergunta booleana → `ask_laya_glob`; "meu diff é arriscado?" → `review-risk-v1`; "qual subagente?" → `agent-route-v1` (shadow até calibrado); suposição recorrente → propor promoção a perfil frozen.
2. **Quando NÃO usar**: verdade disponível via `read`/`grep` direto → verificar, não perguntar (Rule 12). Laya responde *o que ler primeiro*, nunca *qual é o fato*.
3. **Doutrina de saída**: `abstain` = "verifique você mesmo"; `yes/no` = priorização de leitura, não conclusão. Nunca citar resposta Laya como evidência ao usuário sem confirmação por ferramenta.
4. **Fencing Camada 10**: `laya_cli.py predict --questions-file` é advisory; saída JAMAIS alimenta hook/policy/script de gating. Recorrente → escala para perfil no contrato.
5. **Orquestração da Camada 7**: tabela trigger→ação §4; como interpretar a linha `LAYA-GATE` injetada; obrigação de executar a ação dentro do turno (não entre tool calls pendentes de um batch).
6. **Tabela de custos**: filebool ~200ms por arquivo em CPU com batch de 8 inflight; guard abaixo de 50ms amortizado pois T0/T1 absorvem a maior parte; avaliação do gate no máximo uma vez a cada 8 calls no piso.

Updates a skills existentes: `context-hygiene` (tabela Smart Window → apontar para este ledger; remover menção "fast-jev"), `implement-laya` (seção "self-use guard/compact profiles"), `handoff` (cross-ref como executor do `clear`).

---

## 6. Config & lifecycle

```json
// .devin/laya/profile.json (criado a partir de templates/laya/profile.example.json)
{
  "mode": "off",
  "profiles": ["compact-item-v1","compact-gate-v1","cmd-risk-v1","filebool-v1",
               "review-risk-v1","agent-route-v1","write-scope-v1","fetch-scope-v1"],
  "models": {"typed-decisions": {"path": "<local>", "sha256": "<hex>"}},
  "daemon": {"idle_ttl_s": 1800, "max_inflight": 4, "deadline_ms": 1000},
  "compact_gate": {"eval_floor": 0.50, "compact_at": 0.70, "compact_to": 0.40,
                   "force_at": 0.80, "k_calls": 8, "cooldown_turns": 10}
}
```

`mode` promove off → shadow → assist por perfil via `calibration.profiles`. Hooks a registrar (execução futura): `laya-guard.py` dentro de `pre-exec-guard.py`; `write-scope`/`fetch-scope` em `pre-write-guard.py`; `compact-gate.py` em PostToolUse (após `context-pressure.py`) + UserPromptSubmit (após `user-prompt.py`).

---

## 7. Payloads de auditoria (shadow log → calibração)

```json
// .devin/laya/shadow.jsonl: uma linha por decisão, sempre, todo modo
{"ts": "...", "session_id": "...", "profile": "cmd-risk-v1",
 "request_id": "...", "features": {...}, "candidates_n": 5,
 "recommendation": {"outcome": "suggestion", "candidate_id": "mutating",
                    "calibrated_probability": 0.81},
 "tier_used": "T2", "latency_ms": 187, "final_verdict": "PASS",
 "option_order_hash": "<sha256 da ordem canônica enviada>"}
```

`option_order_hash` detecta regressão de ordenação (30% flip risk) no replay.

---

## 8. Plano de evidência (Rule 15: validação vs held-out)

| Gate | Corpus | Métrica-alvo |
|---|---|---|
| G0 baseline | shadow.jsonl ≥500 execs reais | distribuição de tiers; T0+T1 ≥ 70% do tráfego |
| G1 replay | fixtures de comandos benignos | FP-block < 2% em `assist` |
| G2 adversarial | comandos destrutivos ofuscados (variações rm/del/SQL) | FN-block = 0 nas classes T1; `irreversible`/`egress` recall ≥ 0.95 |
| G3 compaction | 5 transcripts reais (ISSUE_01) + retenção downstream | paths/comandos referenciados resolvíveis pós-compact; reduction ≥ 0.25 |
| G4 flip test | cada perfil, ordem de candidatos permutada | flip rate < 5% (aborta assist se maior) |
| G5 held-out | split congelado, nunca usado em calibração | miss rate no risco-alvo declarado; threshold fixado antes do held-out |
| G6 routing | prompts reais de dispatch | `agent-route-v1` assist só se > baseline Rule-20 determinístico |

`eval_decisions.py` (existe) roda G1/G2/G5 sobre manifests congelados. Latência p50/p95 reportada por perfil; deadline overrun conta como abstain.

---

## 9. Riscos & limites declarados (da literatura)

- **Sensibilidade à ordem**: mitigar com ordem canônica frozen + `option_order_hash` + G4.
- **Cardinalidade**: manter ≤8 candidatos (contrato já força); >8 → shortlist determinística antes da Laya.
- **Zero-shot routing fraco**: Camada 5 shadow até G6; regras Rule-20 permanecem o default.
- **Confidence ≠ correção**: entropy score; thresholds próprios por perfil/checkpoint/locale; troca de checkpoint invalida calibração (contrato já força).
- **Estimador de pressão**: chars/4 é heurístico; `p` pode errar ±15%. Por isso bandas + histerese + `FORCE_AT` conservador.
- **Efeito canal**: injection FP varia com canal nativo do conteúdo (arXiv:2610.02267). Corpus de calibração deve vir de transcripts reais do harness, não de fontes externas.

---

## 10. Sequência de execução (futura, fora desta sessão)

1. `layad.py` + `laya_client.py` + `profile.json` (mode `off`, boot saudável).
2. Perfis `cmd-risk-v1`, `compact-gate-v1`, `filebool-v1` no contrato (bump `-vN`).
3. `laya-guard.py` + hooks notice (`compact-gate.py`) em **shadow**; acumular G0.
4. Calibrar thresholds por perfil → `assist` por perfil (G1/G2/G4/G5 green).
5. `filebool.py` + skill `laya-orchestrator`; update `context-hygiene`/`implement-laya`.
6. Purge JEV (§11) + fechar ISSUE_01.

## 11. JEV purge list (execução)

| Arquivo | Ação |
|---|---|
| `extensions/laya-compactor/transcript.py:3`, `state.py:3` | comentário "fast-jev" → "upstream algorithm (MIT port)" |
| `skills/context-hygiene/SKILL.md:50,52` | "fast-jev default" → "upstream port default" |
| `.devin/issues/ISSUE_01_laya_compaction.md` | marcar `status: superseded-by LAYA_MASTER_ARCHITECTURE.md` |
| `.devin/research/4_fronts_recon.md:52-76` | manter como registro histórico do upstream; menções a `Jev` passam a "hosted model replaced by laya" |
