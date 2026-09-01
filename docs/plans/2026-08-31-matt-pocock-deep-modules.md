# Plano: incentivar módulos profundos (deep modules)

**Bloqueado por:** nenhum.

**Objetivo:** evoluir `improve-codebase-architecture` para avaliar profundidade de módulos (interface pequena, funcionalidade grande) e sugerir refactorings que reduzam dependências rasas.

## Evidência de entrada

- URL: `https://www.youtube.com/watch?v=-QFHIoCo-Ko`
- Timestamps: `01:14:14.800–01:23:01.760`
- Fonte: John Ousterhout, *A Philosophy of Software Design*.
- Conceitos: shallow modules (muitos pequenos, muitas dependências) vs deep modules (interface pequena, grande funcionalidade).

## Hipóteses a testar

1. `improve-codebase-architecture` não menciona explícitamente profundidade de módulos.
2. IA tende a gerar módulos rasos se não supervisionada.
3. Testar por fora de um módulo profundo é mais fácil e barato.

## Falha a observar

- `skills/improve-codebase-architecture/SKILL.md` não cita Ousterhout nem profundidade.
- Não há heurística para detectar módulos rasos no bundle.

## FASE 0 — obrigatória

- [ ] 0.1 — Ler `skills/improve-codebase-architecture/SKILL.md`.
- [ ] 0.2 — Confirmar `agents/` ou `scripts/` com métricas de arquitetura.
- [ ] 0.3 — Buscar citação primária de Ousterhout.

## FASE 1 — Observar

Comando: `grep -n "deep\|shallow\|Ousterhout" skills/improve-codebase-architecture/SKILL.md`
Resultado: ausência.

## FASE 2 — Criticar

- Regra violada: Rule 3 (update wrong skills).
- Comportamento: skill genérica de arquitetura sem heurística de profundidade.
- Intenção: apontar oportunidades de melhoria arquitetural.
- Falha: não detecta o padrão específico que Pocock destaca.

## FASE 3 — Gerar alternativas

1. Adicionar seção "Deep vs shallow modules" em `improve-codebase-architecture`.
2. Criar novo script `scripts/audit-module-depth.py`.
3. Criar skill `deep-modules` separada.

## FASE 4 — Revisar

Aplicar alternativa 1 (menor blast radius).

## FASE 5 — Validar

- Teste: invocar skill em um repo de teste e ver se ela fala em profundidade.
- Held-out: `python -m pytest tests/held-out/ -q`.

## FASE 6 — Future pace

1. Agentes notam módulos rasos. Ajuda? Sim.
2. Refactorings sugeridos são mais acionáveis. Ajuda? Sim.
3. Tests se tornam mais fáceis. Ajuda? Sim.

## FASE 7 — Ecological check

- Não criar dependência de parser AST agora.
- Sugestões textuais são aceitáveis para começar.

## Arquivos esperados

- `skills/improve-codebase-architecture/SKILL.md` (atualizado)
- `ledgers/deep-modules-pocock.md`
