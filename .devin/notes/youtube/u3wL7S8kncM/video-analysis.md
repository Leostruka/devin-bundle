# Analise: u3wL7S8kncM -- "Apps Are Over. Think Libs with Nx." (JS Poland Conf)

## Fonte

- URL: https://youtu.be/u3wL7S8kncM (JS Poland Conf, 2026-10-31)
- Palestrante: Younes Jaaidi (software coach, Lyon). 20:51, Ingles.
- Formato: skit teatral de abertura (dev + componentes acoplados
  personificados) + overview Nx + live-coding de plugin de inferencia.

## Conteudo

1. **Skit**: componente de sugestoes precisa ser reutilizado em 2
   apps; esta acoplado a store e route query params -> "reusavel"
   so com copy-paste ou repo unico. Motivacao: boundaries claras.
2. **Nx** = "progressive build companion": pega o que quiser.
   Affected-graph -> so builda/testa o que a mudanca afeta.
3. **Module boundaries**: tags por scope/type; ESLint dep constraints
   proibem feature/UI libs de importar libs de infrastructure.
   Granularidade: nem libs gigantes nem micro.
4. **Whitelist de pacotes externos por tipo de lib**: HttpClient so
   em libs `infrastructure`. Testado em times, "funciona".
5. **Project Crystal (inference)**: convencao -> Nx infere nodes/
   targets/tags sem project.json. Plugin proprio detecta index.ts
   por padrao e injeta no grafo.
6. Demo: ESLint bloqueia em tempo real o import "errado" e o hack
   com HttpClient direto na UI lib.

## Mapa conceito -> bundle

| Nx | Bundle |
|---|---|
| boundary tags + dep constraints | ARCHITECTURE_MANIFEST "Forbidden crossings" |
| whitelist externa por tipo | "stdlib-only in scripts/" |
| affected-graph (testa so o afetado) | N/A -- pytest suite completa ~3min, CI matrix |
| crystal inference (convencao->grafo) | manifest.json + audit.py checks |
| ESLint enforcement em tempo real | architecture-gate.py PreToolUse |

## Gap encontrado e corrigido (R13)

O manifest **declarava** "scripts/ hooks never import from
extensions/" mas `laya-guard.py` importa decision_contract +
laya_client de extensions/laya-tools (deliberado, fail-open) -- e
**nada enforcava** o boundary real. Corrigido:

- Manifest: boundary real = "no third-party pip deps"; laya-guard
  documentada como excecao fail-open.
- Novo teste `test_scripts_import_boundary` (tests/validation):
  todo import em scripts/*.py deve ser stdlib, sibling in-dir ou a
  excecao laya. 28/28 pass.

## Veredito: conceito absorvido

O resto e especifico de monorepo JS (Nx/ESLint/affected-graph) --
sem portabilidade direta. A licao "boundary declarada sem enforce
apodrece" virou o fix R13.
