# Plano: melhoria dos videos + self-improvement (2026-11-26, deadline 18:00 BRT)

STATUS 11:00 BRT: I-01..I-11 TODOS APLICADOS E PUSHADOS. Campanha adicional completa:
CI healing 21->0 falhas (fetch-depth 2 + fixtures), incidente de seguranca resolvido
(narrowing revertido pos-veredito UNSAFE do council), behavioral-eval loop fechado
com baseline real 3/3. Ledger: `.devin/ledgers/self-improvement-20261126.md`.

Fontes: `.devin/research/media-osint-20261126/bundle_refinement_report.md` (8 fontes)
e `.devin/research/media-osint-20261126-yt2/bundle_refinement_report.md` (2 fontes).

DELEGATION: disabled (usuario nao autorizou subagentes explicitamente).
VERSIONAMENTO: usuario ordenou commits com boas praticas (sobrepoe default da skill).
SCOPE: skills/, scripts/, config.json, data/, tests/ (aditivos), .devin/plans/.
FORA DE SCOPE: tests/held-out/ (anti-trapaca), segredos, assinaturas IA.

## Ondas priorizadas (valor x esforco)

### Wave 1 - quick wins
- I-01 typescript-node: exemplos Parameters/ReturnType/Awaited (batch1 P2)
- I-02 impeccable: ocultar alvo dos juizes, pacote comparativo, variancia, escalacao barata-first (batch2 P0+P1)
- I-03 prototype: variant matrix + decision ledger + worktree default + export (batch2 P1)

### Wave 2 - medio
- I-04 council: modo opcional multi-provider de review (batch2 P1)
- I-05 agent-behavior-eval: casos comportamentais MCP/tool-use (batch2 P0)
- I-06 media-osint: preflight disco, cache externo, fallback 429->ASR, notas incrementais, cleanup (batch1 meta)

### Wave 3 - grande
- I-07 animation-direction: VIDEO.md duravel, anti-patterns, preview, notas timestamped, video-fixer, medicao-antes-de-screenshot, gate de render (batch1 P0)
- I-08 inference-optimisation skill nova (batch1 P1)
- I-09 frontend-design/impeccable: coreografia motion + staggers aplicados; break-ui parcial; learn-taste e Sakuga NAO importados (deferidos, commit 83109ed)

### Wave 4 - restante
- I-10 resiliencia de downloads Prism-like (batch1 P2)
- I-11 .devin/design/<surface>/ contexto espacial persistente (batch2 P2)

### Rejeitado com evidencia
- Trunk/Branches Isaque 2.0: preprint auto-publicado, sem replicacao independente (batch1)
- OpenMAIC: adjacente apenas, sem lacuna direta (batch1 P3)
- Copiar canvas/GUI do Onlook para o bundle (batch2)
- Loops de $400 como default: budget caps obrigatorios (batch2)

## Protocolo por item (10 passos condensados)
1. Reproduzir gap com comando/leitura exata
2. Ligar a regra/fonte; intencao positiva separada
3. 3 alternativas com risco/metrica
4. Patch minimo em SCOPE
5. Validar: pytest + audit + held-out quando aplicavel
6-7. Future pace + ecological check no ledger
8. Dry-run/install quando hook/script
9. Classificar MELHOROU/NEUTRO/INCONCLUSIVO (MELHOROU exige held-out)
10. Commit assinado, mensagem neutra, proximo item
