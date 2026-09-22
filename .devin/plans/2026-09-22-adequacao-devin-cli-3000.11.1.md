# Plano: adequar o bundle ao Devin CLI v3000.11.1

> **For agentic workers:** REQUIRED SUB-SKILL: Use /dispatching-parallel-agents (recommended) or /execution to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Objetivo:** alinhar declaração de versão, tabela de capacidades e docs de runtime ao CLI instalado `3000.11.1` (delta desde o último alinhamento: `3000.10.27` validado / `3000.10.31` auditado).

**Arquitetura:** nenhuma mudança de config ou hook é proposta — a release 3000.11.1 não introduz chave nova obrigatória. O trabalho é: verificar empiricamente 3 mudanças de comportamento que tocam o bundle, documentar decisões na tabela de compatibilidade, e bump do pin de versão.

**Stack:** docs Markdown, `data/bundle-identity.json`, verificação via `devin doctor`, `audit.py`, `pytest`.

## Estado observado

- `devin --version`: `3000.11.1 (cc4e349ca55e)`.
- Pin atual: `"validated_cli_version": "3000.10.27"` em `data/bundle-identity.json:8`; README.md:40 hardcoded; audit brutal cobriu `3000.10.31`.
- `devin doctor` já valida ambiente OTEL ("otel exporter environment" — pass).
- `.devin/rules/` contém apenas `README.md` (dir intencionalmente vazio — regras ficam no projeto consumidor).
- `agents/*.md` usam `allowed-tools`; `implementer.md` já lista `write`; `researcher.md`/`reviewer.md`/`architect.md`/`debugger.md`/`qa-ci.md` omitem `write` de propósito.
- Bundle não tem regras `Exec(...)` em `permissions` — só `Write`/`Read` deny de segredos.
- Nenhum workaround de PowerShell nos scripts de hook (grep vazio) — os fixes upstream não exigem remoção.

## Delta 3000.10.31 → 3000.11.1 que toca o bundle

| Item | Superfície do bundle | Ação |
|---|---|---|
| Regras descobertas recursivamente em `.devin/rules/` | `.devin/rules/README.md` pode ser injetado como regra | verificar `devin rules list`; se virar regra, mover/renomear o README |
| `allowed-tools` passa a conceder `write` de fato | `agents/*.md` — implementer ganha write real; read-only profiles ficam enforceáveis | verificar com subagent de teste; documentar |
| Subagents herdam always-on rules globais+workspace | perfis de subagent; constraint-pinning passa a valer em subagents (custo de contexto maior) | documentar; sem mudança de código |
| `Exec` deny > allow/ask amplos; `Exec(*)` casa tudo (3000.10.31) | `permissions.deny` do config template | sem mudança; nota na tabela |
| `devin --cloud`, `/cloud`, `/handoff`, `/pickup`, `devin ssh`, `/ssh` | TOOLS-MAP; futuras skills | documentar comandos novos |
| `otel` block / `OTEL_EXPORTER_OTLP_*` | config template | decisão: não adotar (sem collector); já coberto pelo doctor |
| Plugins org/enterprise via Customize | seção Plugins do compat doc | nota: carregam no CLI por org |
| `/loop` com reviews em subagent read-only | skills que mencionam loop | doc apenas |
| Bypass mode sem editor review; interrupt estaciona subagents; fixes PowerShell Windows | comportamento de runtime | doc apenas |
| ACP (modelos/effort via session config, auth cache) | bundle não usa ACP | não adotado |

## Fontes primárias

- https://docs.devin.ai/cli/changelog/stable (v3000.11.1, 2026-09-21; v3000.10.31, 2026-09-16)
- `devin --help`, `devin doctor`, `devin rules` no binário instalado

## Global Constraints

- Sem chaves novas em `config.json` a menos que a verificação prove necessidade.
- Decisões seguem o formato existente da tabela em `docs/DEVIN-CLI-COMPATIBILITY.md` (Capability | Decision | Rationale).
- Nada de placeholders `{{...}}` fora dos já existentes (`{{VALIDATED_CLI_VERSION}}` resolve via bundle-identity.json).
- Docs do repo em PT-BR seguindo a convenção dos planos anteriores.

## Ciclos sequenciais

### Ciclo 1 — verificações de comportamento (gates empíricos)

- [ ] Rodar `devin rules list` num projeto com `.devin/rules/README.md` presente.
  - gate: saída do comando; expect: README.md NÃO listado como regra, ou se listado → Task extra: mover o README para `.devin/docs/` e atualizar referência.
  - evidence: output do comando no ledger.
- [ ] Verificar grant de `write` via `allowed-tools`: dispatch subagent `implementer` pedindo para criar `tmp_write_gate.txt`; depois `researcher` pedindo o mesmo.
  - gate: existência do arquivo; expect: implementer cria, researcher falha/não cria.
  - evidence: `ls tmp_write_gate.txt` após cada dispatch; deletar o arquivo no fim.
- [ ] Confirmar que subagent recebe always-on rules: dispatch `researcher` perguntando "qual a regra 2 do AGENTS.md global".
  - gate: resposta cita conteúdo real do AGENTS.md; expect: cita "No AI signatures".
  - evidence: resposta do subagent.
- [ ] `devin doctor` — expect: 0 failures (inclui check otel).

### Ciclo 2 — tabela de capacidades 3000.11.x

- [ ] Adicionar seção `## 3000.11.x capabilities (verified <data>, CLI 3000.11.1)` em `.devin/docs/DEVIN-CLI-COMPATIBILITY.md` com uma linha por item do delta acima (Capability | Decision | Rationale), incluindo as duas linhas de 3000.10.31 (`Exec` precedence, `Exec(*)`).
  - gate: `grep -c "3000.11" .devin/docs/DEVIN-CLI-COMPATIBILITY.md` ≥ 1; tabela cobre todos os itens do delta.
- [ ] Atualizar seção Plugins com a nota sobre plugins org/enterprise via Customize.
- [ ] Remover a seção duplicada "3000.10.x capabilities" + "`read_config_from` policy" duplicada se ainda presente (o arquivo tem o bloco repetido nas linhas 9-30 e 42-62 — consolidar numa só).
  - gate: `grep -c "## 3000.10.x capabilities"` == 1.

### Ciclo 3 — pin de versão e docs de runtime

- [ ] `data/bundle-identity.json`: `"validated_cli_version": "3000.11.1"`.
- [ ] `README.md:40`: `3000.10.27` → `3000.11.1`.
- [ ] `.devin/docs/TOOLS-MAP.md`: adicionar comandos novos à seção de comandos (`--cloud`/`/cloud`, `/handoff`, `/pickup`, `devin ssh`/`/ssh`); nota sobre bloco `otel` no config.
- [ ] `CHANGELOG.md`: entrada `3000.11.1 alignment` listando decisões (unreleased/next version section).
- [ ] Se Ciclo 1 revelou que `.devin/rules/README.md` vira regra: mover doc e ajustar texto que aponta para ele.

### Ciclo 4 — gate final

- [ ] `devin --version` == `3000.11.1` == `bundle-identity.json`.
- [ ] `python audit.py` — 0 erros.
- [ ] `python -m pytest` — verde incluindo held-out.
- [ ] `devin doctor` — 0 failures.
- [ ] Install simulado em APPDATA temporário — completa sem erro (conforme seção "Installer verification" do compat doc).

## Aceitação

- [ ] `bundle-identity.json`, README e `devin --version` em paridade (`3000.11.1`).
- [ ] Tabela 3000.11.x cobre todo o delta 3000.10.31→3000.11.1 com decisão explícita por item.
- [ ] Comportamento de `allowed-tools: write`, regras recursivas e herança de always-on rules verificado com evidência reproduzível (não deduzido).
- [ ] Audit + pytest + doctor verdes; install temporário ok.
- [ ] Nenhum `tmp_*` sobrevive no commit final.
