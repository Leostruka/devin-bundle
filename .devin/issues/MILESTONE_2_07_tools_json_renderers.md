# MILESTONE 2 / ISSUE 07: `tools.json` - contrato de renderizadores multi-CLI (devin primeiro)

Status: resolved · Source: github.com/msitarzewski/agency-agents (MIT; `tools.json`, `scripts/convert.sh`, `scripts/lib.sh`, `scripts/check-tools.sh`) · Matrix: `.devin/research/MILESTONE_NEXTGEN_MATRIX.md` sec B#6/E · Blocked-by: M2_06 · Blocks: none

## Contexto & Valor

- O bundle hoje renderiza para um unico alvo (Devin CLI). Upstream prova o contrato: `tools.json` keyed por ferramenta com `format`, `installKind`, `dest` templates, `detect`; regra de ouro "same format => byte-identical" enforced por check em CI.
- `render-user-hooks.py` ja e o nosso primeiro renderer deterministico; falta o manifesto declarativo + teste de byte-identidade.
- Valor: base para a branch `platform/gemini-argus` (ausente hoje - flag registrado) renderizar o mesmo corpus para Gemini/Claude/Codex sem divergir; ate la, devin e a unica row ativa.

## Brain (Skill)

- Doc curto no `devin-config`: "como adicionar uma ferramenta em tools.json" (campos obrigatorios + check byte-identical).

## Muscle (Data + Scripts + CI)

- `tools.json` na raiz: `{ "devin": { label, format: "devin-hooks+skills", installKind: "roster", dest: "%APPDATA%/devin", detect: [...] } }` + placeholders `gemini`/`claude`/`codex` com `"enabled": false` ate a branch existir.
- `scripts/check-tools.py` (stdlib): valida schema de tools.json; garante que 2 renderizacoes do mesmo formato produzem bytes identicos (roda `render-user-hooks.py` 2x e compara); usado em `audit.py` e CI.
- Renderer devin formalizado: `scripts/render-user-hooks.py` continua a implementacao de referencia (como convert.sh upstream); `install-ledger.py record` consome `rendered_hash`.

## Step-by-step

0. Escrever `tools.json` com row devin completa + 3 disabled.
1. `check-tools.py` schema+determinismo; wire em `audit.py`.
2. CI: adicionar step `python scripts/check-tools.py` ao workflow.
3. Gate: `pytest` (byte-identical test falha se renderer emitir timestamp); `audit.py` 0 errors; CI verde.

## Non-goals

Sem renderers reais para gemini/claude/codex (dependem da branch ausente); sem Tauri/GUI; sem converter o catalogo de personas upstream.

## Answer

- `tools.json` na raiz: row `devin` enabled (format `devin-hooks+skills`, renderer `render-user-hooks.py`, dest `%APPDATA%/devin`) + placeholders gemini/claude/codex com `enabled: false`.
- `scripts/check-tools.py` (stdlib): valida schema (label/format/installKind/dest/enabled + enabled requer renderer) e garante byte-identidade (renderer roda 2x, stdout comparado). Devin PASS: 3471 bytes identicos.
- `audit.py` check 35 roda check-tools; falha de renderer = erro de audit.
- devin-config doc: como adicionar tool + regra byte-identical.
- 8 testes: schema (3), byte-identity (deterministico/nondeterministico/exit!=0), expand_dest, main verde no repo.
- Desvio do spec: `install-ledger.py record` consome `rendered_hash` ja existente (file sha), sem mudanca de contrato.
