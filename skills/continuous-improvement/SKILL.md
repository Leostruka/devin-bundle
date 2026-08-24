---
name: continuous-improvement
description: Use when starting a self-improvement session. Enforces FASE 0 deep research and the 10-step improvement loop so no step is skipped, no phantom failure is invented, and every change is validated with held-out tests.
version: 1.0.0
model: swe-1-7
subagent: implementer
---

# Continuous Improvement Skill

Runs the agent through a self-improvement loop based on Constitutional AI critique, RISE recursive introspection, Six-Step Reframing, and held-out validation.

## When to invoke

- User asks for self-improvement, autonomy improvement, or "continue the improvement loop".
- Any session where the agent should inspect its own bundle (rules, skills, hooks, scripts) for real, reproducible failures.
- Before declaring a bundle "done" — final convergence gate.

## Permissibility

You may edit any bundle file (`AGENTS.md`, `config.json`, `hooks.v1.json`, `scripts/*.py`, `skills/*/SKILL.md`) to reduce real failures. You may NOT:
- edit `tests/held-out/`
- display or log secrets
- add AI signatures to deliverables
- push or commit (unless explicitly asked)

## FASE 0 — Deep Research (mandatory, in order)

1. **Devin CLI docs**: confirm hooks, events, model names, config locations with `web_search`/`webfetch` on docs.devin.ai.
2. **Bundle reality**: `exec`, `read`, `grep`, `glob` to verify doc vs disk.
3. **Reliable sources**: prefer arXiv, docs.z.ai, cognition.com, docs.devin.ai; reject unsourced blogs.
4. **Best practices**: context window (200K GLM-5.2 / 262K SWE-1.7), tool-use, lost-in-the-middle mitigation.
5. **Git history**: `git log --oneline -30` and `git log --diff-filter=D` to avoid repeated mistakes.
6. **Baseline**: `python audit.py` and `python -m pytest tests/held-out/ tests/validation/ -q`.
7. **Synthesize**: list prioritized improvement candidates with evidence.

## LOOP (10 steps, do not skip)

1. **OBSERVAR**: reproduce a concrete failure with an exact command/tool-call. If you cannot reproduce it, stop — it is a deduction, not a failure.
2. **CRITICAR**: identify the violated `AGENTS.md` rule; separate current behavior from positive intent.
3. **GERAR ALTERNATIVAS**: produce at least 3 alternatives preserving the positive intent and fixing the failure.
4. **REVISAR**: apply the best alternative.
5. **VALIDAR**: run chosen tests + held-out tests. Held-out failure = discard change.
6. **FUTURE PACE**: project the fix into 3 future scenarios; at least 2 must benefit.
7. **ECOLOGICAL CHECK**: check side effects on other rules, hooks, skills, and context budget.
8. **SIMULAR**: `install.ps1` (or equivalent), `python audit.py`, `python -m pytest tests/held-out/ tests/validation/ -q`, and self-assessment of behavioral impact.
9. **CLASSIFICAR**: MELHOROU / PIOROU / NEUTRO / INCONCLUSIVO with real metrics.
10. **REPETIR OU CONVERGIR**: take the next candidate; stop only when no reproducible failure remains.

## Output format

```
MELHORIA: <título>
FASE0_RESEARCH: <fontes verificadas com URLs>
FALHA_REPRODUZIDA: <comando> → <saída>
REGRA_VIOLADA: <Rule #>
INTENÇÃO_POSITIVA: <texto>
ALTERNATIVA_APLICADA: <#> de <N>
HELD_OUT: <passou|falhou|inexistente>
SIMULAÇÃO: <install OK? audit 0? held-out 0? impacto comportamental>
MÉTRICA_REAL: <número vs baseline>
CLASSIFICAÇÃO: <MELHOROU|PIOROU|NEUTRO|INCONCLUSIVO>
ESTADO: <validada|não_validada|estagnada|revertida>
ARQUIVOS_ALTERADOS: <lista>
PUSH_COMMIT: <não feito>
```

## Anti early-stop

A single iteration without improvement does not stop the loop. Reformulate the angle of critique (max 3 times). After 3, record stagnation and stop.

## Convergence criterion

All candidates from FASE 0.7 applied and classified, and no new reproducible failure is found. State: the bundle is optimal for GLM-5.2 High (200K) + SWE-1.7 Max/Medium (262K).
