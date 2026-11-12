# Odyssey Systems - world models (R2, survey batch-8)

Fonte: https://odyssey.systems/ (fetch 2026-11-12). Lab de foundation world models.

## Produtos relevantes

- **Odyssey-3**: foundation world model (fisica, dinamica, causa-efeito, comportamento de agentes).
- **Agora-2**: multi-agent world model - varios participantes (humano ou AI) compartilham a MESMA simulacao em tempo real.
- **PROWL-2**: framework RL onde o time de agentes E o world model aprendem com curriculos proprios, continuamente, num unico loop de treino.
- **Starchild-1**: world model que aprende de interacao multimodal rica (alem de observacao visual).

## Onde encaixa no bundle (N areas)

1. **Evals** (.devin/evals/): conceito central = ambiente simulado reproduzivel onde o agente age e ve consequencias. Nossos evals sao estaticos (cases.json); world models sugerem evals "vivos" onde o ambiente responde. Aplicavel: design-iteration-loop, laya evals.
2. **Agent-rts / multi-agente**: Agora-2 = varios agentes no mesmo mundo. Nosso dispatch de subagents e isolado por natureza; se um dia orquestrar agentes que compartilham estado, a referencia e essa.
3. **Self-improvement loop**: PROWL-2 = agente e ambiente co-aprendem num so loop. Analogo: nosso harness melhora (skills) enquanto as tarefas mudam - o eval deveria co-evoluir, nao ficar congelado.
4. **computer-use / cu_agent_desktop**: percepcao de mundo via tree vs pixels e o mesmo trade-off (a11y tree = "world model" barato do desktop).

## Veredicto
NOTE - nivel conceitual. Nenhum componente do bundle precisa mudar agora; manter como referencia de arquitetura para futuras evals interativas. Revisitar se aparecer demanda por evals com ambiente reativo.
