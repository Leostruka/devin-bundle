# Plano: corrigir declarações e contagens

**Bloqueado por:** nenhum.

**Objetivo:** eliminar divergências entre contagens, versão, documentação e mensagens de release.

## Estado observado

- `python audit.py` contabiliza 71 skills no disco e no array `skills`.
- `manifest.json` declara versão `2.8.0`, mas `skill_count` permanece em `57`.
- O audit atual não compara `skill_count` com o array `skills`, portanto retorna zero erros apesar da divergência.
- O commit original do PR #6 mencionava 71 skills; o merge resultou no commit `0b086ed`.

## FASE 0

- [ ] Inventariar todas as declarações de versão e contagem.
- [ ] Identificar a fonte canônica usada por `audit.py`.
- [ ] Reproduzir cada divergência com comando exato.
- [ ] Revisar histórico de correções de contagem.
- [ ] Registrar baseline de audit e held-out.

## Ciclo 1 — fonte canônica

- [ ] Observar uma divergência reproduzível.
- [ ] Comparar três alternativas: contagem derivada, campo explícito, geração automática.
- [ ] Selecionar uma única fonte canônica.
- [ ] Adequar manifesto, README, CHANGELOG, badges e docs.
- [ ] Adicionar validação contra regressão sem tocar `tests/held-out`.
- [ ] Executar future pace e ecological check.
- [ ] Classificar o resultado com números antes/depois.

## Aceitação

- [ ] Um comando único demonstra a quantidade real de skills.
- [ ] Todas as declarações exibem o mesmo valor.
- [ ] Versão, tag e CHANGELOG são coerentes.
- [ ] `python audit.py` retorna zero erros.
- [ ] `python -m pytest tests/held-out -q` retorna zero falhas.
