# Nível de Esforço Obrigatório: MAX
# Perfil Operacional: Technical Art Director Sênior e Pesquisador de Computer Graphics

# Goal
Conduzir pesquisa extensa e profunda, com no mínimo 140 fontes validadas e renomadas (documentação oficial, papers, benchmarks da indústria, reviews de estúdios, comunidades profissionais como Polycount/CGSociety/ArtStation Magazine, relatórios de engines), para determinar a melhor ferramenta ou stack de criação e manipulação 3D cobrindo: obras hiper-realistas, cartoon/estilizado, criativo/procedural, animação, personagens e cenários. Entregar recomendação fundamentada para substituir a integração Spline atual, que produz artefatos inúteis.

# Context
Repo devin-bundle (C:\Users\Fingertech\Desktop\scripts\devin-bundle). Integração 3D atual: skills/operate-spline + extensions/spline-operator (MCP bridge ws://127.0.0.1:19692, 36 tools, daemon keeper). Resultado observado: gera artefatos inúteis para os eixos alvo. Candidatos a avaliar incluem Blender (+geometry nodes, addons), Maya, 3ds Max, Cinema 4D, Houdini, ZBrush, Unreal Engine 5, Unity, Substance 3D, Marvelous Designer, e geradores AI-3D (Tripo, Meshy, Luma Genie, Kaedim, Rodin/Hyper3D, Hunyuan3D, TRELLIS, Stable Fast 3D, ComfyUI-3D). Critério decisivo adicional: dirigibilidade por agente (API, scripting Python, headless CLI, MCP bridge, licença/custo).

# Acceptance Criteria
1. Relatório cita >= 140 fontes distintas, cada uma com URL, publicação/fonte e data de acesso
2. Fontes renomadas apenas: docs oficiais, SIGGRAPH/papers, benchmarks publicados, reviews de veículos profissionais, postmortems de estúdios - sem blogs SEO genéricos
3. Matriz comparativa por eixo: hiper-realismo, cartoon, procedural/criativo, animação/rigging, personagens, cenários
4. Coluna explícita de dirigibilidade por agente (API/script/headless/MCP) e custo/licença
5. Ranking final com recomendação única justificada + 1 alternativa
6. Veredito sobre a spline-operator: manter, limitar ou substituir, com evidência
7. Saída em Markdown em .devin/research/3d-tools-comparison.md

# Scope & Non-Goals
- **IN SCOPE:** Pesquisa web extensa (web_search, webfetch) e consolidação de fontes
- **IN SCOPE:** Matriz comparativa e ranking ponderado
- **IN SCOPE:** Avaliação de dirigibilidade por agente e custo
- **IN SCOPE:** Relatório final em .devin/research/
- **OUT OF SCOPE:** Instalar, licenciar ou pagar qualquer ferramenta
- **OUT OF SCOPE:** Escrever código de nova integração ou modificar extensions/spline-operator
- **OUT OF SCOPE:** Benchmarks executados localmente (apenas benchmarks publicados)
- **OUT OF SCOPE:** Gerar artefatos 3D nesta etapa

# Execution Hints & Checkpoints
1. **Fase 1:** Fase 1: Declarar eixos de avaliação, critérios de inclusão de fontes e lista inicial de candidatos. PARE e aguarde aprovação.
2. **Fase 2:** Fase 2: Coletar >= 140 fontes (log em .devin/scratch/3d_sources.jsonl: url, publisher, data, eixo, evidência-chave).
3. **Fase 3:** Fase 3: Construir matriz comparativa ponderada por eixo + dirigibilidade/custo.
4. **Fase 4:** Fase 4: Ranking final, recomendação e veredito sobre spline-operator.
5. **Fase 5:** Fase 5: Escrever .devin/research/3d-tools-comparison.md e verificar todos os acceptance criteria.
