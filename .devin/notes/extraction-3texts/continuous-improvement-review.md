# Revisão da skill `continuous-improvement`

## Objetivo da revisão

Verificar por que a skill pode deixar de seguir fontes, itens do usuário e itens descobertos durante a própria execução. A revisão foi feita lendo diretamente:

- `skills/continuous-improvement/SKILL.md`
- `skills/unlazy/SKILL.md`
- `skills/verification-before-completion/SKILL.md`
- `skills/leo/SKILL.md`
- `AGENTS.md`
- `.devin/global_rules.md`
- `skills/writing-for-agents/SKILL-MECHANICS.md`
- `docs/MODEL-GUIDE.md`
- `D:\Programing\ai_workspace\devin-bundle\.devin\notes\extraction-3texts\improvements.md`
- `D:\Programing\ai_workspace\devin-bundle\.devin\notes\extraction-3texts\plan.md`

Também foram consultadas as páginas primárias do Devin CLI:

- <https://docs.devin.ai/cli/extensibility/skills/creating-skills>
- <https://docs.devin.ai/cli/extensibility/skills/overview>
- <https://docs.devin.ai/cli/subagents>

## Matriz de lacunas verificadas

| ID | Evidência primária | Lacuna observada | Correção planejada | Gate |
|---|---|---|---|---|
| CI-01 | `SKILL.md` L05-07; Devin CLI `creating-skills`, “Running Skills as Subagents” | `subagent: true` + `agent: implementer` faz a skill rodar em worker independente. Esse worker não recebe automaticamente o histórico da conversa; itens e fontes fornecidos no contexto podem desaparecer. | Remover o despacho automático da skill. Executar inline por padrão. Registrar no início se delegação está autorizada; quando o usuário proibir subagentes, não chamar `run_subagent`. | Frontmatter sem `subagent`/`agent`; execução mantém o registro de inputs. |
| CI-02 | `SKILL.md` L20-35, L80-120 | O objetivo e a FASE 0 não possuem um registro obrigatório dos arquivos, fontes, pedidos e candidatos que precisam ser processados. | Criar `INPUT_REGISTER` no ledger: cada item recebe ID, origem, localização, requisito, status e evidência. Nenhum item pode desaparecer silenciosamente. | Auditoria do ledger mostra todos os itens como `applied`, `deferred` ou `rejected` com justificativa. |
| CI-03 | `SKILL.md` L80-120 | Os subpassos 0.1–0.7 descrevem outputs, mas não possuem `CHECK`, `EXPECT` e `EVIDENCE` executáveis por subpasso. | Converter cada subpasso em gate explícito; bloquear avanço quando o gate anterior estiver `pending`, vazio ou sem evidência. | Gate anterior não-pendente e evidência reproduzível antes do próximo passo. |
| CI-04 | `SKILL.md` L55-66; `.gitignore` L16-25 | A skill exige `.devin/ledgers/<melhoria>.md`, mas o bundle ignora novos arquivos nesse diretório e mantém os ledgers rastreados em `ledgers/`. | Resolver o caminho pelo convention/disco antes de iniciar; registrar o caminho efetivamente usado. | Ledger existe, não está ignorado quando precisa ser entregue, e é encontrado por `git status`/`git ls-files`. |
| CI-05 | `SKILL.md` L95-105 | “Fonte confiável” é descrita em termos gerais, sem exigir leitura da fonte primária, citação localizável, autor, data, URL/path e decisão de aceitação. | Adicionar registro de proveniência por fonte e separar fonte primária, fonte secundária, claim e interpretação. | Cada claim citado tem URL/path, autor/data quando aplicável e citação verificável. |
| CI-06 | `AGENTS.md` L68-78, L114-123; `verification-before-completion` L63-77 | A skill afirma verificação, mas o formato atual permite preencher placeholders ou declarar resultado sem um VF definido antes da alteração. | Definir VFs antes de editar; cada VF tem comando, expect e evidência. | Todos os VFs executados novamente após a alteração. |
| CI-07 | `SKILL.md` L129-204 | Os dez passos têm campos `___`, mas não têm gates completos nem critério operacional uniforme. Future pace e ecological check podem permanecer opinião textual. | Padronizar cada passo com `OUTCOME`, `CHECK`, `EXPECT`, `EVIDENCE`; para avaliações qualitativas, exigir matriz verificável e não apenas afirmação. | Nenhum passo marcado sem evidência; critérios qualitativos têm artefato ou comando associado. |
| CI-08 | `SKILL.md` L161-165, L231-246 | Held-out inexistente é tratado no passo 5, mas o checklist final não diferencia claramente `não validada` de `validada`. | Proibir estado `validada` sem held-out; usar `INCONCLUSIVO`/`não_validada` quando a suíte independente não existir. | Saída final contém estado e motivo compatíveis com as suítes disponíveis. |
| CI-09 | `SKILL.md` L181-200; `AGENTS.md` L80-89 | `install.ps1 -Force` e `git checkout` aparecem como ações genéricas. Podem sobrescrever configuração live ou alterações não relacionadas. | Exigir dry-run/revisão antes de instalar; reverter somente arquivos próprios por patch direcionado; não usar checkout amplo. | Diff antes/depois e lista de arquivos autorizados registrados. |
| CI-10 | `SKILL.md` L192-215 | “Convergência ótima” não é uma métrica operacional; pode transformar ausência de descoberta em afirmação de optimalidade. | Trocar por “conjunto de candidatos reproduzíveis processado”; exigir métrica numérica, baseline, unidade e método. | Toda classificação contém baseline, pós-estado, delta e fonte do número. |
| CI-11 | `SKILL.md` L167-179 | Future pace/ecological check não exigem cobertura de todos os arquivos, regras, hooks e skills afetados. | Adicionar matriz de impacto: regras, skills, hooks, scripts, instalação, contexto e segurança; cada célula tem `sem impacto` ou evidência. | Matriz completa, sem célula omitida. |
| CI-12 | `SKILL.md` L231-246; `AGENTS.md` L41-46, L139-147 | O checklist final não exige `check-ai-signature.py`, `git diff --check`, segredo/output scan e registro de arquivos não intencionais. | Adicionar gates de deliverable, segredo, assinatura, whitespace, diff e working tree. | Comandos executados e saída registrada. |
| CI-13 | `SKILL.md` L156-159 | O passo de revisão registra apenas “diff resumido”; não exige que a alteração seja diretamente ligada à falha reproduzida e ao requisito de entrada. | Exigir mapa `falha → regra → alternativa → arquivo → teste`. | Mapa presente no ledger e no review. |
| CI-14 | `SKILL.md` L206-215 | O critério de parada declara uma conjuntura ótima de modelo, mas não exige que todos os itens de `improvements.md` ou do pedido atual tenham disposição. | Usar rastreabilidade por IDs e parar somente quando todos tiverem disposição verificável ou quando houver bloqueio explícito. | Nenhum input sem status final. |
| CI-15 | `SKILL.md` L35, L231-246; regra do pedido atual | A skill proíbe commit/push, mas não registra outras restrições da sessão, como “não usar subagentes”. | Adicionar contrato de sessão: restrições do usuário têm precedência e são copiadas para o ledger antes do loop. | Execução não chama subagentes quando `DELEGATION=disabled`. |
| CI-16 | `SKILL.md` L124-165 | Não há exigência de TDD ou classificação do tipo de mudança. Alterações de script podem ser feitas sem teste de regressão. | Classificar mudança como `doc-only`, `skill-only`, `script-behavior` ou `config`; para comportamento, exigir red-green ou teste de regressão equivalente. | Gate de teste correspondente ao tipo da mudança. |
| CI-17 | `SKILL.md` L250-266 | O formato final concentra o resumo, mas não aponta obrigatoriamente para o ledger completo, fonte por fonte e itens adiados/rejeitados. | Saída curta aponta para ledger/review; ledger conserva evidência completa. | Saída e ledger têm os mesmos IDs e estados. |

## Causa principal

A skill possui uma boa intenção declarativa, mas o fluxo atual é principalmente um prompt longo com placeholders. Ele não transforma entradas em uma lista fechada, não bloqueia transições por evidência e não preserva automaticamente o histórico quando executado como subagente. Assim, uma execução pode parecer completa mesmo sem ter processado todas as fontes ou recomendações.

## Correções da Fase 0

1. Executar `continuous-improvement` inline por padrão.
2. Registrar contrato da sessão e todos os inputs antes da FASE 0.
3. Usar ledger rastreável com gates por subpasso e por passo.
4. Exigir proveniência verificável para cada fonte e claim.
5. Definir VFs antes de qualquer alteração.
6. Diferenciar `validada`, `não_validada`, `estagnada`, `revertida` e `inconclusiva`.
7. Proteger instalação, reversão, segredos, assinaturas e mudanças não relacionadas.
8. Exigir rastreabilidade completa e métrica real antes de declarar melhoria.

## Restrição desta execução

Esta execução está em modo `DELEGATION=disabled`: não usar `run_subagent`, `read_subagent` nem qualquer skill executada como subagente. A validação será feita diretamente com ferramentas locais e fontes primárias lidas.
