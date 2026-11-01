# Model Guide

Política de modelos do bundle, nativa SWE-2. O roteamento é por **nível de esforço** (Medium/High/Max), não por tamanho de modelo. Valores concretos estão em `data/bundle-models.json`; as variáveis de ambiente `BUNDLE_DEFAULT_MODEL`, `BUNDLE_MAX_MODEL` e `BUNDLE_MEDIUM_MODEL` podem sobrescrever os padrões. A versão validada do CLI está em `data/bundle-identity.json`.

## Effort levels (SWE-2)

No SWE-2, esforço é o nível de raciocínio embutido no `model_uid`. Não é um campo separado na config — a variante escolhida define o esforço. A UI oferece `Alt+T` para alternar.

| Nível | model_uid | Quando usar | Custo |
|---|---|---|---|
| **Medium** | `swe-2-medium` | Tarefas simples, ajustes pontuais, scripts isolados, edições mecânicas. Spec claro; sucesso verificável por um teste/build. | **Free** |
| **High** | `swe-2-high` | Tarefas que atravessam múltiplos arquivos, debugging bounded, decisões com várias constraints. **Default geral.** | **Free** |
| **Max** | `swe-2-max` | Tarefas abertas, refatorações globais, long-horizon coding, decisão custosa/irreversível. | **Free** |

**Regra prática:** comece no nível que corresponde à forma da tarefa. Suba um nível quando a verificação falhar, não antes. Ver `context-hygiene` para a base empírica.

## Primary model (parent)

O modelo primário (parent) é definido por `BUNDLE_DEFAULT_MODEL` (ou `data/bundle-models.json.default_parent_model`). Default do bundle: **`swe-2-high`** (High effort, 262K, free).

| Atributo | Valor | Fonte |
|---|---|---|
| model_uid | `{{BUNDLE_DEFAULT_MODEL}}` | `data/bundle-models.json` / `devin models list` |
| Context window | `context_window` do registro | `data/bundle-models.json` |
| Effort | definido pelo sufixo do `model_uid` | esta tabela |
| Tool use | nativo durante inferência | Devin docs |
| Custo | `cost_tier: free` para o default | `data/bundle-models.json` / `devin models list` |

### Implicações para o harness

1. **Raciocínio nativo**: SWE-2 planeja e raciocina sem instruções de
   chain-of-thought. Prompts, skills e profiles declaram O QUE deve ser feito
   e os critérios de aceitação, nunca COMO raciocinar ("pense passó a passo",
   "planeje antes de agir" são anti-padrões).

2. **Tool-use nativo**: o modelo decide quando invocar ferramentas durante
   inferência. O harness não deve over-specificar regras de tool-use —
   Rule 17 (verify with tools) alinha naturalmente.

3. **Prompt caching**: manter AGENTS.md e system prompt cache-stable. Regras pinned no topo = prefixo estável = cache hit. Não reordenar regras pinned frequentemente.

4. **Lost-in-the-middle (arXiv:2307.03172)**: curva U-shaped confirmada.
   Constraints críticas no início (pinned rules), contexto recente no fim,
   evitar dependência de informação no meio do contexto. Constraint-pinning
   (Rule 14) é a defesa correta.

5. **Budget**: porcentagens fixas da `context_window` em `data/bundle-models.json`
   são consumidas por AGENTS.md, SKILL-TIERS.md, skills invocadas e tool defs.
   O restante fica disponível para trabalho.

## Subagent models

Subagents usam os mesmos variantes SWE-2, escolhidos por nível de esforço:

| Campo | Descrição | Effort | Custo | Notas |
|---|---|---|---|---|
| `{{BUNDLE_MAX_MODEL}}` | Subagent Max (`swe-2-max`) | max | **Free** | Agents de planejamento/julgamento/review |
| `{{BUNDLE_MEDIUM_MODEL}}` | Subagent Medium (`swe-2-medium`) | medium | **Free** | Agents de execução bounded |
| `{{BUNDLE_DEFAULT_MODEL}}` | Parent (`swe-2-high`) | high | **Free** | Orquestração, raciocínio diverso |

**⚠️ CRÍTICO**: aliases não canônicos podem apontar para um modelo pago — **não use** sem verificar `data/bundle-models.json`.
Os agents/ devem fazer pin com os variantes canônicos (`{{BUNDLE_MAX_MODEL}}` / `{{BUNDLE_MEDIUM_MODEL}}`) do bundle.

**⚠️ CRÍTICO — `subagent_explore` (built-in) pode ser pago**: o profile built-in
`subagent_explore` roda no default router do CLI, que pode cobrar por token.
Não há override local — apenas enterprise settings podem mudar isso.
**NUNCA dispatchar `subagent_explore`.** Usar o profile customizado `researcher`
(`agents/researcher.md`, pin `model: {{BUNDLE_MAX_MODEL}}`, gratuito, veja `data/bundle-models.json`)
que tem as mesmas capacidades read-only. Fonte: docs.devin.ai/cli/subagents.

### Self-compaction (diferencial chave)

Os subagentes do bundle são treinados para:
1. Escrever summaries informativos e concisos do estado de trabalho.
2. Resumir a partir desses summaries eficientemente.

Isso significa que os subagentes preservam constraints melhor que modelos genéricos
durante compaction. Mas Governance Decay (arXiv:2606.22528v2) mostra que compaction
dropa constraints em TODOS os modelos testados — constraint-pinning ainda é necessário.

O hook `constraint-pinning.py` tem heuristic `summary_retains_constraints()` que
verifica se key phrases sobreviveram. Para subagentes treinados, o summary é mais
likely de reter constraints → pinning fires less often → comportamento correto
(pin só quando necessário).

### Implicações para subagent dispatch

1. **Context window**: a janela do subagent está em `data/bundle-models.json` (262K). Subagents podem fazer mais trabalho antes de precisar compaction. Fan-out econômico.
2. **Self-compaction**: subagents podem rodar mais tempo sem perda de contexto. Menos necessidade de `context-hygiene` em subagents.
3. **Conciso por design**: SWE-2 é treinado para output conciso. Não fightar com regras verbose. Rule 8 (telegraphic) alinha.
4. **Coding strength**: para tarefas de coding (implementação, debugging, refactoring), o parent deve delegar para subagentes em vez de implementar inline.

### Matriz de routing: parent inline vs subagent

| Task type | Best function | Como executar | Por quê |
|---|---|---|---|
| Implementação de código | Subagent Medium | `implementer` subagent | Spec'd work, execução bounded |
| Debugging de código | Subagent Medium | `debugger` subagent (parent planeja) | Iteração de hipóteses |
| Code review | Subagent Max | `reviewer` subagent | Julgamento independente |
| Research/exploração | Subagent Max | `researcher` subagent | Alto contexto, free |
| Arquitetura (routine) | Subagent Max | `architect` subagent | Trade-off analysis |
| Arquitetura (high-stakes) | Parent model | inline ou `subagent_general` | Needs parent reasoning |
| Final whole-branch review | Parent model | inline ou `subagent_general` | Judgment task, max capability |
| Reasoning diverso | Parent model | inline | Primary model for diverse reasoning |
| Fix-loop escalation (R4-5) | Parent model | `subagent_general` | Fresh eyes + parent reasoning |
| Coordenação/orquestração | Parent model | inline (parent) | Parent role, never delegate |

### Subagent vs compaction: quando usar cada um

Fonte: dreaming.press/posts/subagents-vs-compaction-isolate-context

| Resposta | Mecanismo | Custo | Sobrevive reset? | Quando usar |
|---|---|---|---|---|
| **Subagent** | Fresh window, só final message retorna | ~15x tokens, sem herança automática | N/A — parent nunca teve o lixo | Subtask separável com resultado sumarizável (research sweep, file exploration, parallel review) |
| **Compaction** | Sumariza transcript, dropa verbatim | Lossy: specifics omitidos gone for good | Não — summary ainda em-window | Thread contínua de raciocínio que deve ficar coerente |
| **Context editing** | Evicta tool results antigos, keep 3 | Invalida prompt cache prefix | Parcial — results re-fetchable | Loop vivo que precisa de tool results recentes |

**Regra de composição**: subagents mantêm o orchestrator lean; compaction
mantém cada loop long-lived sob seu cap. Use subagents para evitar que
trabalho bulk entre no parent window; use compaction quando o trabalho
já está no parent e precisa continuar coerente.

Para o parent (`{{BUNDLE_DEFAULT_MODEL}}`) despachando subagents:
- Pesquisa/exploração extensa → `researcher` (Max, gratuito, retorna só síntese)
- Implementação bounded → `implementer` (Medium, gratuito)
- Debugging iterativo que precisa de contexto acumulado → inline + compaction
- Arquitetura/decisão que precisa ver tudo → inline (parent, High)

## Estratégia de model pin em agents/

| Agent | model: pin | Effort | Racional |
|---|---|---|---|
| researcher | `{{BUNDLE_MAX_MODEL}}` (`swe-2-max`) | Max | Read-only, gratuito, alto contexto |
| architect | `{{BUNDLE_MAX_MODEL}}` (`swe-2-max`) | Max | Trade-off analysis, gratuito |
| reviewer | `{{BUNDLE_MAX_MODEL}}` (`swe-2-max`) | Max | Julgamento independente, gratuito |
| debugger | `{{BUNDLE_MEDIUM_MODEL}}` (`swe-2-medium`) | Medium | Iteração rápida, gratuito |
| implementer | `{{BUNDLE_MEDIUM_MODEL}}` (`swe-2-medium`) | Medium | Bounded tasks, gratuito |
| qa-ci | `{{BUNDLE_MEDIUM_MODEL}}` (`swe-2-medium`) | Medium | Gate re-execution, gratuito |

**Por que pin e não alias?** Aliases não canônicos podem apontar para um modelo pago.
Use os variantes canônicos do bundle (`{{BUNDLE_MAX_MODEL}}` / `{{BUNDLE_MEDIUM_MODEL}}`)
que são gratuitos e têm a maior `context_window`. Sem pin, o router pode
resolver para um modelo pago. Quando novas versões saírem, atualize os agents/
para os novos modelos listados em `data/bundle-models.json`.

O parent (`{{BUNDLE_DEFAULT_MODEL}}`) faz trabalho complexo inline. Para implementação
que precisa do parent, usar `subagent_general` (herda parent, **gratuito**
quando parent é free) ou pin `model: {{BUNDLE_DEFAULT_MODEL}}` no agent.

### Profiles built-in vs custom agents (custo)

| Profile | Modelo | Custo | Quando usar |
|---|---|---|---|
| `subagent_general` | Herda parent (`{{BUNDLE_DEFAULT_MODEL}}`) | **Gratuito** (quando parent é free) | Implementação que precisa do parent, contexto isolado |
| `subagent_explore` | Default router do CLI | **PAGO** (possível) | **EVITAR** — usar custom agent `researcher` (gratuito) em vez |
| Custom agents (researcher, architect, etc.) | `{{BUNDLE_MAX_MODEL}}` / `{{BUNDLE_MEDIUM_MODEL}}` (pin) | **Gratuito** (quando free no registro) | Pesquisa, arquitetura, review, debug, implementação |

**⚠️ Nunca usar `subagent_explore`** — ele pode resolver para um modelo pago.
Os custom agents com os pins canônicos são gratuitos e têm mais contexto.
Fonte: docs.devin.ai/cli/subagents.

## Modelos pagos — política CONDICIONAL

**Gratuitos** na assinatura são definidos em `data/bundle-models.json`
com `cost_tier: free`:

- `{{BUNDLE_DEFAULT_MODEL}}` — parent (default, High)
- `{{BUNDLE_MAX_MODEL}}` — subagent Max
- `{{BUNDLE_MEDIUM_MODEL}}` — subagent Medium

**Pagos**: quaisquer entradas com `cost_tier: paid` em `data/bundle-models.json`,
incluindo aliases/short names. Sempre verifique o registro antes de usar um
modelo não-canônico.

### Política CONDICIONAL ao modelo do parent

**Caso 1 — Parent FREE (`cost_tier: free`): subagents DEVEM ser FREE.**

Protocolo FREE-ONLY:
1. Parent (`{{BUNDLE_DEFAULT_MODEL}}`, High) — tentativa inicial
2. Subagent fan-out (`{{BUNDLE_MAX_MODEL}}` Max / `{{BUNDLE_MEDIUM_MODEL}}` Medium) — paralelismo
3. Parent com esforço `max` (via `Alt+T` ou `/model swe-2-max`) — mais raciocínio, mesmo modelo gratuito
4. Repetir com contexto mais limpo (`clear` + recarregar apenas o necessário)
5. Se todos os gratuitos falharem: **parar e reportar ao usuário** — não escalar para pago

Neste caso: **NUNCA usar `subagent_explore`**, **NUNCA usar aliases pagos não verificados**
sem verificar `data/bundle-models.json`, **NUNCA usar modelos pagos** para subagents.

**Caso 2 — Parent PAGO (usuário escolheu um modelo pago): subagents podem usar pagos.**

O usuário já optou por pagar pelo parent. Neste caso:
- `subagent_explore` (default router, possivelmente pago) é permitido se for mais barato que o parent
- `subagent_general` herda o modelo pago do parent (já está pago)
- Custom profiles com os pins canônicos continuam FREE — preferir quando possível
- Para reasoning pesado, pode-se usar o mesmo modelo do parent via `subagent_general`

**Como detectar o caso**: verificar o `cost_tier` do modelo ativo no parent em `data/bundle-models.json`. Se for `free`, é Caso 1 (FREE-ONLY). Qualquer outro modelo é Caso 2.

**Regra**: quando o parent está em modelo FREE (`cost_tier: free`), **NUNCA usar
modelos pagos** para subagents. Os modelos gratuitos canônicos cobrem 100% dos casos.
Se ambos falharem, reportar ao usuário. Quando o parent está em modelo PAGO
(usuário escolheu), subagents podem usar modelos pagos.

## Inferência local e batch fora do CLI (BitNet / TPU / offloading)

O routing principal do bundle é SWE-2 via CLI. Esta seção cobre motores
complementares para custos que o CLI não deve pagar.

### Anti-pattern: túnel Cloudflare sobre GPU T4 com layer split

Hospedar um LLM de agente numa GPU T4 dividida (layer split) atrás de um
túnel Cloudflare falha estruturalmente:

- **Prefill math**: o cenário fornecido cita 30k tokens em ~92s, equivalente
  a ~326 tok/s. Não é medição local nem propriedade universal da T4. Com
  timeout de 100s, a margem seria ~8s; a documentação atual do Cloudflare
  informa **125s** de Proxy Read Timeout padrão (margem aritmética ~33s).
  HTTP 524 depende do intervalo sem resposta do origin e da configuração,
  não apenas do total de tokens ou do número de turns.
- **Layer split em T4** troca compute por latência de transferência entre
  camadas; o pior caso é exatamente o prefill longo que agentes exigem.
- **Exposição**: um túnel público serve o endpoint a qualquer cliente que o
  alcance; código proprietário do usuário transita por um path que o bundle
  não controla.

Veredito: **não usar** para agentes. Se um endpoint remoto for necessário,
mínimo é GPU que processe 30k tokens de prefill em <30s com margem, auth no
endpoint, e nunca tráfego de código sensível por túnel público.

### Held-Out TPU Batch Recipe (opcional)

Para jobs em lote de validação held-out (Rule 15), não para o loop do agente:

- Kaggle **TPU v5e-8** + `vLLM`: ~**10.300 tok/s** é um número fornecido
  no briefing, ainda não reproduzido neste bundle. A essa taxa, 30k tokens
  levariam ~2,91s de prefill, excluindo filas, compilação e decode.
- Uso restrito a **batch offline**: avaliação de perfis Laya, replay de
  manifests congelados (`eval_decisions.py`), held-out suites.
- **Nunca** enviar código proprietário sensível: só fixtures, manifests e
  corpus público/anônimo. Não é path do agente online; sem daemon, sem hook.

Entry point implementado: `extensions/ai-tools/vllm_tpu_runner.py` -
dois caminhos, ambos honestos quanto a hardware:

- `run_tpu_batch(entries, model, ...)`: batch finito sobre manifest
  congelado validado por `heldout_batch.load_manifest` (bytes verificados
  vinculados no load), usando a API offline do vLLM
  (`from vllm import LLM, SamplingParams`; `llm.generate(prompts, sp)`).
  jax/vllm importados lazy; sem TPU retorna `backend_unavailable` real,
  nunca mock.
- `serve(model, ...)`: `vllm serve` sempre bound a `127.0.0.1` em porta
  limitada (1024-65535) - o default upstream é um listener publico sem
  auth, inaceitável; `--host`, `--port`, `--api-key`, origins/methods/
  headers em `extra_flags` são rejeitados.

Não submete cloud jobs nem cria VMs TPU. Nenhum hardware TPU foi testado
neste bundle - `--check-only` é o modo seguro.

### Local CPU-first: bitnet.cpp (1.58-bit)

`microsoft/BitNet` (`bitnet.cpp`) roda LLMs ternários 1.58-bit 100% em
CPU/RAM, sem consumir VRAM. Implementado:

- `extensions/ai-tools/bitnet_adapter.py`: subprocess do `llama-cli`
  compilado com `-ngl 0` (CPU puro), contrato upstream de
  `run_inference.py`. `run()` nunca levanta exceção - binary/GGUF ausente
  retorna `backend_unavailable`; saída passa por `_clean_output` (extrai
  só a cauda após o echo `> <prompt>`, remove o footer de timing do
  llama-cli); captura em UTF-8 com `errors="replace"`; em Windows recusa
  backend `.bat`/`.cmd` (batch roda via cmd.exe mesmo com shell=False -
  só executável nativo); `extra_flags` não pode sobrepor contrato
  CPU/modelo/prompt nem buscar remoto. `suggest()` devolve
  `{"type": "suggestion"|"abstain", "authority": false}` so quando o
  `choice` parseado é um candidate id valido. `--self-test` roda checagens
  de contrato offline.
- `extensions/ai-tools/heldout_batch.py`: batch runner sobre manifest
  congelado - `load_manifest` valida tipo dos campos, split `heldout`,
  sources `public`/`synthetic`, paths sensiveis, escape de root, tamanho
  por entrada (<=8192 B), sha256 e vincula os bytes verificados na entrada
  (`_data`); arquivo adulterado após o load não executa sob hash stale.
  Limites: `MAX_ENTRIES=1024`, `max_jobs=64`, manifest <=4 MiB. CLI exige
  `--binary` + `--model` reais. Records deterministicos (sha256 de
  input/output, sem timestamps). Nunca importado por hooks.
- Runtime caches ficam FORA do repo, em
  `C:/Users/leand/AppData/Local/devin-cache/egm-runtime-install/`
  (binary + GGUF) e `.../openui-browser/`. O antigo
  `.devin/scratch/egm-runtime-install/smoke.json` é histórico superseded.
- Evidência real: `devin-cache/egm-runtime-install/cli_proof2.json` - run
  nativo real do llama-cli retornou `ok: true` com output limpo, mas a
  completion estava semanticamente errada: o pipeline executa, a
  qualidade do modelo NÃO está estabelecida.

Candidato como motor local para `laya-tools` / decisões tipadas leves quando
o snapshot dedicado não estiver disponível (mantém o contrato
`suggestion`/`abstain` inalterado). Avaliação pendente: latência e qualidade
de decisão tipada vs snapshot Laya atual, medidos em held-out (G5) antes de
qualquer adoção. Fora do caminho crítico: hooks stdlib-only não podem
depender dele. Nenhuma adoção está feita: o adapter existe, nenhum perfil
Laya o consome ainda.

### Lookup / Expert Offloading (VRAM + System RAM)

Padrão para modelos grandes em hardware limitado: hot path (atenção, experts
ativos) em VRAM, pesos frios (experts inativos, embeddings de lookup) em
system RAM. Implementado: `extensions/ai-tools/offload_plan.py`
(`build_argv`), só flags reais verificadas contra upstream:

- `bitnet.cpp`: retorna `["-ngl", "0"]`; flags de expert offloading são
  rejeitadas (b1.58 é denso, sem MoE).
- `llama.cpp`: `-ngl N`, `--cpu-moe`, `--n-cpu-moe N`,
  `--override-tensor "regex=BUFFER"` (buffers `CPU`/`CUDA0..3`). Flags MoE
  exigem `model_is_moe=True`; `--cpu-moe` e `--n-cpu-moe` são mutuamente
  exclusivos.

É um construtor de argv, não um executor; nenhum kernel de offload foi
medido neste hardware. A métrica que decide adoção é prefill/decode real no
hardware do usuário, não o marketing do backend.

### Local audio: LFM3 family (avaliado, não adotado)

`liquid-ai/LFM3` (open weights): família 1.7B-2B -- texto (`LFM3 1.7B`),
visão (`LFMVL 2B`), audio bidirecional (`LFM3 Audio 2B`: ouve, transcreve,
fala), omni (`LFM Omni 2B`), decisão (`D1 Omni 2B`). Formatos: FP8, NVFP4,
MLX, ONNX.

- **LFM3 Audio 2B** é o único candidato relevante ao bundle:
  speech-in/speech-out + STT + TTS num modelo só, streaming de voz com
  baixa latência, pt-BR suportado. Dois modos observados: streaming
  (responde rápido, pt sai com sotaque EN) vs sequencial (resposta pt
  correta, latência maior e escolha de voz/idioma explícita).
- **Limitações confirmadas em demo** (não medidas aqui): 2B se confunde
  em consultas complexas (LLM -> "lentes/molduras"), às vezes repete a
  pergunta, confiabilidade insuficiente para tool-calling sensível.
- **Licença**: LFM Open License -- uso comercial permitido até US$10M/ano
  de receita; NÃO é MIT/Apache. Checar threshold antes de distribuir.
- **Candidato a backend** para `extensions/voicebox/` (wrapper HTTP já
  existe, backend-swappable) e alternativa unificada a
  `extensions/asr/` (whisper.cpp segue mais leve para STT puro).
  Adoção exige runner local (llama.cpp-style/MLX/ONNX) + medição de
  latência e WER pt-BR em held-out -- nenhuma implementada.

## Context budget (parent model)

```
System prompt + tool defs    ~???? tok (Devin runtime, não mensurável aqui)
AGENTS.md                    ~???? tok (medir com context-budget.py)
SKILL-TIERS.md (se lido)     ~???? tok
Skills invocadas (1-3)       ~1000-9700 tok
MCP tool defs (configured)   ~???? tok (medir com mcp-governance)
─────────────────────────────────────────────
Disponível para trabalho     consulte `context_window` em `data/bundle-models.json`
```

> Nota: este arquivo (MODEL-GUIDE.md) é leitura opcional — não carrega automaticamente.

## Verificação de fontes (Rule 12)

Especificações de modelos devem ser verificadas contra
`data/bundle-models.json`, `devin models list` e os sites dos providers.

| Citação | Status | URL primária |
|---|---|---|
| arXiv:2307.03172 (Lost in the Middle) | Verificado | aclanthology.org/2024.tacl-1.9 |
| arXiv:2606.22528v2 (Governance Decay) | Verificado | arxiv.org/abs/2606.22528v2 |
| arXiv:2607.13083 (Phantom Guardrails) | Verificado | arxiv.org/html/2607.13083 |
| arXiv:2606.30317 (MCP Patterns) | Verificado | arxiv.org/html/2606.30317 |
| arXiv:2607.25152 (Progress Mirage) | Verificado | arxiv.org/abs/2607.25152v1 |
| ICLR 2026 Workshop (Reward Hacking) | Verificado | iclr.cc/virtual/2026/10018648 |
| arXiv:2605.10039 (Instruction Adherence) | Verificado | arxiv.org/abs/2605.10039 |
| arXiv:2605.21384 (SpecBench) | Verificado | arxiv.org/abs/2605.21384 |
| arXiv:2603.15473 (ALTK) | Verificado | arxiv.org/abs/2603.15473 |
| arXiv:2607.07405 (Reason Less, Verify More) | Verificado | arxiv.org/abs/2607.07405 |
| arXiv:2605.09998 (Continual Harness) | Verificado | arxiv.org/abs/2605.09998 |
| arXiv:2607.17641 (VRR-Stop) | Verificado | arxiv.org/abs/2607.17641 |
| arXiv:2607.28802 (Model or Harness?) | Verificado | arxiv.org/abs/2607.28802 |
| arXiv:2512.24601 (Recursive Language Models) | Verificado | arxiv.org/abs/2512.24601 |
| arXiv:2602.03786 (AOrchestra) | Verificado | arxiv.org/abs/2602.03786 |
| arXiv:2603.02615 (RLM depth reproduction) | Verificado | arxiv.org/abs/2603.02615 |
| arXiv:2606.20629 (AgentCARD) | Verificado | arxiv.org/abs/2606.20629 |
| arXiv:2608.03535 (CodeAssay) | Verificado | arxiv.org/abs/2608.03535 |
| arXiv:2605.20251 (ProcCtrlBench) | Verificado | arxiv.org/abs/2605.20251 |
| arXiv:2607.20972 (Delivery, Not Storage) | Verificado | arxiv.org/abs/2607.20972 |
| arXiv:2608.15008 (Harness the Memory) | Verificado | arxiv.org/abs/2608.15008 |
| `swe-2-*` variantes e custo | Verificado | `devin models list` (262K, Free) |
| microsoft/BitNet (bitnet.cpp) | Repo primário | github.com/microsoft/BitNet |
| Cloudflare Proxy Read Timeout / 524 | Verificado: padrão 125s | https://developers.cloudflare.com/support/troubleshooting/http-status-codes/cloudflare-5xx-errors/error-524/ |
| Kaggle TPU v5e-8 + vLLM ~10.3k tok/s prefill | Fonte secundária (vídeo benchmark) | medir localmente antes de adoção |
