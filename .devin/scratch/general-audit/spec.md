# Auditoria geral do devin-bundle

Status: audited

## Objetivo

Auditar o working tree atual e criar issues locais acionaveis.
A branch observada e `feature/egm-runtime-rollout`, incluindo arquivos novos
nao commitados. A auditoria nao se limita ao diff recente.

## Escopo

- Governanca: CONTEXT, manifesto arquitetural, hooks e contratos.
- Distribuicao: install/export Windows e Bash, manifest e CI.
- Runtime: JEV/Laya, DOM, OpenUI, Blender/media e inferencia local/TPU.
- Qualidade: audit.py, pytest, held-out sequencial e sintaxe.
- Dependencias: inventario e disponibilidade de scanner; nao instalar pacotes.

## Nao objetivos

Nao corrigir implementacoes, modificar testes existentes, instalar runtimes,
executar jobs externos, publicar issues remotas, commitar ou fazer push.
Nao ler credenciais pessoais nem alterar artefatos cu_* existentes.

## Criterios de aceite

1. Registrar comandos e resultados atuais, sem reciclar verificacoes anteriores.
2. Cada issue deve citar fonte, linhas, impacto e reproducao segura.
3. Separar defeitos reproduzidos, analise estatica e backends simulados.
4. Deduplicar contra issues existentes; usar Status canonico e prioridade.
5. Criar map.md e relatorio de cobertura com limites explicitos.
6. Nao afirmar ausencia universal de defeitos ou validacao de TPU real.

## Evidencias

Logs locais: `.devin/ledgers/general-audit-*.log`.
Reproducoes: `reproduce.py` neste diretorio, somente fixtures sinteticas.
Issues: `issues/NN-*.md`; indice e prioridades em `map.md`.
