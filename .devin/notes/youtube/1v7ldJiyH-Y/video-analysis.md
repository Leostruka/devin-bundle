# Analise: 1v7ldJiyH-Y -- Tiny Software Factories Lesson 1 (IndyDevDan)

## Conteudo

Intro de uma serie de mini-curso: "Tiny Software Factories" (TSF) --
sistemas agenticos pequenos e rapidamente deployaveis que trabalham
"near the loop" (voce responde, o agente executa), posicionados
deliberadamente como anti-patterns ("agentic engineering DONE WRONG")
para ir de zero a valor rapido, vs o curso maior IA3 ("out of loop",
sistemas autonomos completos).

Demo do app TSF (empty factory template):

- Agente duravel na sidebar direita + listas na esquerda + foco ao
  centro (a coisa que voce e o agente operam).
- **Agent access parity**: todo controle da UI tem uma tool de agente
  correspondente; o agente pode fazer tudo que o humano faz.
- **Core control**: contexto, modelo, prompt e tools do agente
  expostos nas settings.
- **Cron prompts**: prompts agendados (nome + schedule + prompt) que
  seguem rodando com o browser fechado (app duravel + trigger em
  sandbox = agente proativo; "trabalha antes de voce acordar").
- **DX/UX customizavel**: temas, navbars, hotkeys, animacoes -- tudo
  mutavel pelo proprio agente ("liquid software").
- **Feedback flywheel**: seu feedback de near-loop melhora a fabrica.
- Feature map: 4 niveis de fabrica; cada feature pontuada em
  valor/esforco/skill.

## Mapa TSF -> bundle (todos ja cobertos)

| Conceito TSF | Equivalente no bundle |
|---|---|
| cron prompts | `skills/scheduled-turns` |
| durable agent + trigger (proativo) | `skills/afk-loop` + hooks.v1.json |
| agent access parity | extensions/* + skills/* (cada capacidade e tool) |
| empty factory template | `skills/project-bootstrap`, `.devin/templates/` |
| feedback flywheel | `skills/self-improvement`, scripts/memory-* |
| feature map valor/esforco | RICE no agente `product-manager` |
| near the loop (voce responde) | workflow padrao hooks+skills |

## Veredito: notes-only, nada a implementar

- E o Lesson 1 de um curso comercial: demo de produto, nao fonte
  tecnica com capacidade portavel. O vocabulario pode se repetir nas
  proximas licoes -- este mapa serve de indice.
- Insight conceitual marginal: "agent access parity" (todo controle
  UI vira tool de agente) ja e a filosofia das extensions.

## Itens implementados

- Nenhum (notes-only).
