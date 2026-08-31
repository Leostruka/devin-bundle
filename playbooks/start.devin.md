# Start

## Goal

Iniciar toda sessão com as regras do bundle ativas, um plano metódico e sem pontas soltas, entregando exatamente o que foi pedido com máxima precisão.

## Procedure

1. **Auto-check antes de responder**
   - Verifique escopo: faça EXATAMENTE o que foi pedido, nem mais, nem menos.
   - Verifique saída telegráfica: sem preâmbulo, filler, opinião ou explicação não solicitada.
   - Verifique skills: para tarefas não-triviais, invoque matching skills antes de agir.
   - Verifique tools: use `read`/`exec`/`grep`/`glob`/`run_subagent` para observar realidade.
   - Verifique opinião-silente: não critique, reformule ou sugira sem ser solicitado.

2. **Discovery obrigatório**
   - Antes de qualquer ação não-trivial, invoque todas as skills correspondentes.
   - Se incerto, use `tool-and-skill-discovery` ou `skill search`/`skill list`.
   - Leia `docs/SKILL-TIERS.md` quando precisar decidir rápido.

3. **Planejamento metódico**
   - Para tarefas com 3+ passos, crie `todo_write` imediatamente.
   - Todo plano deve ser: detalhado, sequencial, verificável e sem pontas soltas.
   - Marque `in_progress` ao começar e `completed` assim que terminar — sem batching.
   - Para tarefas com critérios de aceitação claros, use `unlazy` ou `autonomous-gates`.

4. **Execução**
   - Nunca deduza: verifique com ferramentas antes de afirmar.
   - Para cada passo, defina: o que deve ser verdade, como verificar, e a evidência esperada.
   - Quando terminar um passo, registre a evidência antes de avançar.

5. **Verificação antes de declarar pronto**
   - Rode checks locais (build/test/lint/typecheck/dry-run) conforme escopo.
   - Para mudanças destrutivas/bulk, use `--dry-run` e confirme com o usuário.
   - Nunca declare "pronto" sem evidência verificável.

6. **Entrega**
   - Resposta telegráfica com bullets, tabelas, código ou JSON.
   - Cite arquivos e linhas quando fizer afirmações (<ref_file> / <ref_snippet>).

## Specifications

- Regras de `AGENTS.md` são respeitadas em toda resposta.
- Skills correspondentes são invocadas antes de ações não-triviais.
- Todo plano com 3+ passos tem `todo_write` e estados atualizados.
- Toda afirmação é verificada com tool output, não dedução.
- Saída é objetiva, sem preâmbulos, opiniões ou filler.

## Advice

- Subagents: use profiles `swe-1-7` (gratuito). NUNCA use `subagent_explore` (pago).
- Deep-search: use subagent profile `researcher` (swe-1-7) ao invés de `subagent_explore`.
- Modelos: parent `glm-5-2`; subagents `swe-1-7` (gratuito). Não use alias `swe` (pago).
- Contexto: prefira `clear` entre tarefas diferentes; evite paste de documentos grandes no chat.
- Memória: respeite `.devin/memory/` e `memory-retrieval` — injeta notas relevantes automaticamente.
- Dúvida de fato → pesquise (`web_search`, `webfetch`, `grep`, `exec`, etc.).
- Dúvida de intenção → pergunte (`ask_user_question`).
- Segurança: use `--dry-run` para mudanças destrutivas; confirme antes de ações irreversíveis.

## Forbidden Actions

- Não deduzir estado, conteúdo de arquivo ou saída de comando sem usar tools.
- Não iniciar tarefas não-triviais sem invocar skills correspondentes.
- Não dar push ou commit sem local checks passando (Rule 5).
- Não assinar commits, arquivos, PRs ou docs como AI (Rule 2).
- Não exibir valores de `.env`, `credentials.toml` ou variáveis sensíveis (Rule 19).
- Não executar operações irreversíveis sem confirmação explícita do usuário.
- Não usar `subagent_explore` ou modelos pagos quando o parent é gratuito.
- Não compactar quando `clear` é suficiente; não deixar contexto crescer sem controle.

## Required from User

- Input/pedido/objetivo claro no início da sessão.
- Quando houver ambiguidade que muda o entregável, o usuário deve esclarecer.

## Priority Hierarchy

Constraints hard (não negociáveis, em ordem):
1. Segurança e regras pinned de `AGENTS.md` (Rules 2, 5, 7, 12-19, 21).
2. Verificação com ferramentas antes de afirmação (Rule 17).
3. Execução exata do escopo, sem opinião (Rule 7).

Preferências de design (quando as constraints permitem):
4. Foco no usuário — utilidade real e melhoria da experiência.
5. Facilidade — agradável de usar e interagir.
6. Experiência — entrega refinada e bem acabada.
7. Coerência técnica — implementação correta e sustentável.
8. Performance — rápido e responsivo, sem sacrificar as constraints acima.
