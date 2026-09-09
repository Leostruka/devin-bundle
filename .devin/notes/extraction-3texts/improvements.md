# Pontos de melhoria extraídos dos 3 textos — extração sistemática

## Fontes

- `ontologies-keep-honest.md` — Frank Coyle (UC Berkeley), *Why Agentic Systems Need Ontologies*.
- `sec-needs.md` — *O mínimo que um dev precisa saber sobre segurança*.
- `good-practis.md` — Akita/Galego, *Boas Práticas de IA*.

## Método

1. Leitura completa de cada fonte com `read`.
2. `grep` direcionado para frases de recomendação (deve, não deve, nunca, sempre, cuidado, etc.).
3. Re-leitura dos trechos relevantes para confirmar a prova exata.
4. Agrupamento por pensamento/tópico, mantendo faixa de linhas e citação.
5. Mapeamento de cada ponto para `leo`, modos operantes, skills existentes ou novas.

## Observação sobre o extrator automático

O `structured-knowledge-extraction` lexical capturou apenas headings e URLs. Os conceitos centrais (guardrails, privilégio mínimo, token maxing, TDD, etc.) **não** foram extraídos automaticamente. Isso reforça a necessidade de uma camada semântica/ontológica no extrator.

---

## 1. `sec-needs.md` — Extração sistemática

### 1.1 Responsabilidade e cultura de segurança

- **L08-28**: Segurança não é feature, conjunto de features nem algo que se contrata e fica resolvido. É **cultura**. A última palavra é do especialista, mas todo dev precisa se importar.
  - *Citação*: "segurança não é uma feature, não é um conjunto de features, não é algo que você contrata alguém para configurar e do nada tá tudo seguro. Segurança é acima de tudo, cultura de segurança."
  - *Proposta*: skill `security-audit` e o `leo` router devem tratar segurança como gate cultural, não rota opcional.

- **L19-23**: Não clicar em e-mails/links duvidosos; usar multifactor authentication nas contas importantes; nunca comitar senha do banco no GitHub.
  - *Proposta*: adicionar regras de `AGENTS.md` proibindo cliques/output de links desconhecidos e vazamento de credenciais.

### 1.2 Minimizar a área de superfície

- **L72-84**: A área de superfície é quanto código/partes existem e quanto tocam o mundo real. Cada linha de código é um lugar onde pode morar bug/exploit/vulnerabilidade.
  - *Citação*: "minimizar a área de superfície... Complexidade de código é superfície de contato."
  - *Proposta*: reforçar `effort-calibration`/`context-window-hygiene` para rejeitar código desnecessário; adicionar gate "menor código possível" no `leo` build flow.

- **L85-111**: Todo input do usuário é superfície de contato e possível vulnerabilidade. Nome, e-mail, password — tudo precisa ser sanetizado/limpo antes de uso.
  - *Citação*: "Inputs do usuário, qualquer tipo de input do usuário é alguma maneira de superfície de contato... Você tem que sanetizar, sempre tá limpando ali os inputs do usuário."
  - *Proposta*: `security-audit` deve incluir validação/sanitização de inputs; `implement` deve exigir testes de input malicioso.

### 1.3 Serviços e endpoints

- **L112-137**: Serviços não autenticados e endpoints públicos são vetores. Cada endpoint sem autenticação pode ser spamado para DDOS, varrido para dados ou exploitado. Expõe o mínimo possível.
  - *Citação*: "Cada end point que não requer autenticação é um possível vetor de ataque que um bot pode spamar para fazer DDOS... expor poucos end points ao público, sempre o mínimo possível."
  - *Proposta*: novo gate em `security-audit` ou skill de scan de endpoints não autenticados; `api-design` deve exigir autenticação por padrão.

- **L138-169**: S3 com URL pública é vulnerabilidade. URLs não são senhas — ficam em histórico, cache e roteador. S3 com documentos sensíveis precisa de autenticação.
  - *Citação*: "o seu S3 também precisa ter autenticação... URLs não são como passwords. O seu browser não trata ela com a mesma segurança."
  - *Proposta*: `security-audit` deve verificar buckets/storage públicos e URLs hardcoded.

- **L174-188**: Endpoints com IDs sequenciais permitem enumeração (ex.: mudar `/images/13` para `/images/14`, `15`, `16` e varrer dados).
  - *Citação*: "você mudar isso daqui para 1, 2, 3, 4... a pessoa conseguia varrer todas as imagens."
  - *Proposta*: `api-design`/`security-audit` devem recomendar IDs não sequenciais e autenticação em endpoints de leitura de recursos.

- **L190-219**: Serviços autenticados também são vetores. Múltiplos backends conversando, chaves SSH vazadas, senhas simples para `/admin`, máquinas antigas — tudo é superfície.
  - *Citação*: "todos esses backends podem conter vulnerabilidades e podem ser um vetor de ataque... vazou uma chave de SSH... passwords para entrar no barra admin... essa máquina aqui tá rodando há 10 anos."
  - *Proposta*: `security-audit` deve incluir credenciais hardcoded, credenciais de admin fracos e inventário de serviços/SSH.

### 1.4 Outputs e canais laterais

- **L220-234**: Outputs também são vetores. Logs que registram senhas/dados sensíveis são vulnerabilidade.
  - *Citação*: "outputs também... com seu log pode ser um vetor de ataque, dependendo do que você tá logando... se você tá logando senhas."
  - *Proposta*: regra em `AGENTS.md` proibindo logar secrets/dados sensíveis; `security-audit` scan por `console.log`/`print` de senhas.

- **L235-289**: Tempo de resposta pode vazar informação (timing attack). Senha checada letra por letra: tempos diferentes revelam caracteres corretos.
  - *Citação*: "até o tempo de resposta pode dar uma informação que vai gerar uma vulnerabilidade... a senha... demorou 0.03 ms... a gente sabe que a senha começa com G."
  - *Proposta*: `security-audit` deve alertar para comparações sensíveis a tempo (password, token) e recomendar comparação constant-time.

### 1.5 Princípio do menor privilégio

- **L290-315**: Todo serviço, funcionário e usuário deve ter o privilégio exato que precisa, não mais. Se um backend vaza mas só tem read, o dano é contido.
  - *Citação*: "Tudo deve ter o mínimo de privilégio possível... Os usuários que têm admin não devem poder fazer absolutamente tudo."
  - *Proposta*: `security-audit`/`implement` devem verificar permissões de serviços e usuários; `leo` deve exigir justificativa para permissões amplas.

- **L326-352**: Banco de dados deve ficar dentro de VPC; ninguém de fora deve acessar diretamente. Frontend não acessa DB. Se precisar acessar para migrations, use bastion/jump host via SSH, mas o bastion não deve usar as credenciais do banco fora da VPC.
  - *Citação*: "o seu banco de dados... só que tudo provavelmente vai estar dentro de uma VPC... O seu frontend não deve conseguir acessar o banco de dados... Esse carinha aqui não é recomendado que ele fora da VPC consiga usar as credenciais."
  - *Proposta*: `security-audit` deve incluir regras de network/VPC e acesso ao DB; `docker`/`deploy` podem fornecer template de bastion.

### 1.6 Defaults seguros

- **L354-393**: O padrão deve ser seguro: senha oculta por padrão (asterisco) com opção de revelar; ações destrutivas exigem confirmação; novas contas corporativas devem mudar senha padrão e ativar 2FA em uma semana.
  - *Citação*: "O padrão tem que ser seguro... Ações destrutivas... por padrão, quando você entra numa empresa, a primeira coisa que você tem que fazer é mudar o password de padrão e ativar o 2FA."
  - *Proposta*: `security-audit` checklist de defaults seguros; `AGENTS.md` regra para gerar confirmações em ações destrutivas.

### 1.7 Criptografia e updates

- **L394-403**: Dados sensíveis devem ser criptografados; usar algoritmos padrão (hash); nunca inventar criptografia em casa.
  - *Citação*: "criptografa os dados sensíveis... usa os padrões de criptografia... você não vai inventar criptografia em casa."
  - *Proposta*: `security-audit` deve detectar crypto caseira e ausência de hashing em senhas/dados sensíveis.

- **L404-414**: Aplicar updates de segurança o mais rápido possível. Usar ferramenta que avise (Dependabot).
  - *Citação*: "sempre fazer updates de segurança o mais rápido possível... O GitHub faz isso em algum nível, Tem lá o Dependabot."
  - *Proposta*: `security-audit` deve incluir dependências desatualizadas; `deploy` pode incluir gate de patching.

### 1.8 SAST, WAF e cultura

- **L415-450**: SAST (SonarQube) detecta SQL injection, XSS, etc., mas não resolve sozinho. Combinar com WAF. Ferramentas ajudam, mas segurança continua sendo cultura.
  - *Citação*: "SAST... vai te alertar... SQL injection... XSS... Isso ainda não resolve seu problema... você vai querer utilizar isto aliado a uma web application firewall... segurança não é uma ferramenta."
  - *Proposta*: adicionar SAST/WAF como verificação opcional/recomendada no `verification-before-completion`; `security-audit` educa sobre limites.

### 1.9 Secrets e credenciais

- **L451-458**: Senhas de banco e secrets **jamais** podem ser commitados na codebase. Se comitou, altera a senha imediatamente.
  - *Citação*: "senhas, esses passwords jamais podem ser comitados na sua Code base. Jamais. Se você comitou uma senha... altera essa senha imediatamente."
  - *Proposta*: `security-audit` + hook `check-ai-signature`/`validate-refinement-evidence` devem scanear por secrets; `AGENTS.md` proíbe output de credenciais.

- **L459-474**: Localmente usar `.env` e `.env.example`. `.env` nunca commitado (gitignore). Nunca colocar credenciais de produção no `.env` local.
  - *Citação*: "você vai ter um .env e um .env.example... esse .env aqui que vai ter alguma credencial, possivelmente não de produção... nunca vai ser comitado. Ele vai estar no gitignore."
  - *Proposta*: `project-setup` deve gerar `.env.example` e `.gitignore`; `security-audit` verifica ausência de `.env` no repo.

- **L475-500**: Usar ferramentas de secrets (GitHub Secrets, AWS Secrets Manager). Secrets injetados na aplicação no deploy, não visíveis após criação.
  - *Citação*: "Pode ser o GitHub Secrets... quando a sua aplicação for deployada, ele vai injetar essas variáveis... você não vai poder mais ver esses secrets."
  - *Proposta*: `security-audit`/`deploy` recomendam secret manager; `wizard` pode guiar migração de secrets.

- **L501-586**: Não hardcode password no backend; **jamais** fazer requisição direta do frontend para o banco com credenciais hardcoded. Story exemplifica o absurdo.
  - *Citação*: "password hard coded em vários locais... esse código acessava diretamente o banco de dados... o próprio front end fez essas requisições direto pro banco de dados."
  - *Proposta*: `security-audit` deve detectar credenciais hardcoded e queries DB no frontend; `implement` proíbe padrão front-end -> DB.

---

## 2. `good-practis.md` — Extração sistemática

### 2.1 Fonte e método

- **L71-101**: O autor baseia as práticas em experiência própria (8-10h/dia, 12 anos, CTO), artigos do Akita e conversas com Sam (Monastic), empresa de alta escala.
  - *Proposta*: `project-memory` pode capturar essas referências como regras de projeto.

### 2.2 O mito do One Shot Prompt

- **L104-123**: One-shot prompt é mito para tarefas complexas. Para tarefas muito simples funciona, mas não deve ser objetivo. Muitas maluquices de engenharia de prompt/skills/plugins não resolvem tudo de uma vez.
  - *Citação*: "É o tal do mito do One Shot Prompt... a gente vai conseguir ter uma IA que resolve tudo em one shot... a ideia é você entender que isso é um mito."
  - *Proposta*: `leo` deve rotear tarefas complexas para `grilling`/`planning-pipeline` em vez de tentar one-shot; `effort-calibration` desencoraja over-prompting.

### 2.3 `grilling` / entrevista até entendimento mútuo

- **L124-149**: Substituir one-shot por conversa iterativa/grilling. Skill popular "Grill me about this plan until we reach mutual understanding". Falar quase como outra pessoa até chegar a acordo.
  - *Citação*: "Entreviste-me incansavelmente sobre cada aspecto desse plano até chegarmos a um entendimento mútuo."
  - *Proposta*: `grilling` já existe; garantir que seja acionada antes de `planning-pipeline`/`implement` para tarefas não-triviais.

### 2.4 Intenção clara

- **L150-165**: Modelos novos se importam com intenção. Descrever o objetivo final, onde a feature vai e como afeta o usuário reduz caminhos errôneos.
  - *Citação*: "as IAs se importam com intenção... se você deixar claro qual que é a intenção, aonde que aquela feature vai, como que ela vai afetar o usuário, isso costuma diminuir a quantidade de coisas que vai para um caminho totalmente sem noção."
  - *Proposta*: `planning-pipeline`/`writing-plans` deve exigir campo "intenção" em cada ticket/spec; `grilling` valida intenção antes de codar.

### 2.5 Fluxo padrão vs fluxo melhorado (PRD primeiro)

- **L166-187**: Fluxo comum: issue/task -> Cloud Code/Codex -> código -> revisão (humano/Code Rabbit) -> merge. Está OK.
  - *Proposta*: manter como fallback, mas não como padrão para features novas.

- **L188-205**: Fluxo melhorado: ao invés de só revisar código, conversar com a IA para criar um PRD. Usar skill de PRD. Quando PRD estiver acordado, jogar para IA fazer o código.
  - *Citação*: "eu e meu amigo Cloud Code/Codex vamos conversar com o objetivo de criar um PRD... quando a gente chegar na conclusão de que esse PRD é o que de fato vai ser implementado, aí a gente vai jogar esse PRD para fazer o código."
  - *Proposta*: adicionar `writing-plans`/`planning-pipeline` como gate obrigatório antes de `implement` no `leo` router para tarefas médias/grandes.

### 2.6 Tamanho de tarefas e fronteiras

- **L206-247**: Tarefas pequenas são melhores. PR ideal ~300 linhas. Tarefa >500 linhas deve ser quebrada em subtarefas. Nomenclatura (Epic/Milestone/Story) é irrelevante; o que importa é tamanho e fronteiras claras (input/output).
  - *Citação*: "isso vai se traduzir num PR de mais ou menos 300 linhas... uma tarefa muito grande que vai levar mais do que 500 linhas de código... ela precisa ser quebrada em subtarefas... específico nas boundaries... Se for uma API, qual que é o input/output dessa API?"
  - *Proposta*: `planning-pipeline` deve estimar tamanho de PR e quebrar; `implement`/`tdd` trabalham em slices; `leo` recusa tarefas grandes sem decomposição.

- **L248-274**: Incluir no ticket **por que** aquilo está sendo feito. Tarefa pequena com pouco contexto pode ser mal interpretada, gerando retrabalho.
  - *Citação*: "no ticket é interessante que você inclua o por que esse ticket tá sendo feito... uma tarefa pequena com pouco contexto pode ser mal interpretada pela IA e isso vai aumentar o seu trabalho na hora de revisar."
  - *Proposta*: template de issue/ticket do `planning-pipeline` deve incluir "Intenção" e "Contexto mínimo".

### 2.7 TDD

- **L275-288**: TDD é bom. Antes devs não faziam por preguiça; agora IA pode fazer TDD por você, custa pouco de token. Criar um ferramental de TDD (script/handler) e incluir em agents.md.
  - *Citação*: "TDD é bom... agora o Cloud pode fazer por você TDD e não vai te custar muito a mais... Você pode então criar um ferramental de TDD ali... incluir isso daqui no agents.md."
  - *Proposta*: `tdd` deve ser gate padrão no `leo` build flow; `setup-pre-commit` roda testes; `AGENTS.md` instrui a não deletar testes.

### 2.8 `agents.md` / regras de projeto

- **L289-324**: `agents.md` (ou `cloud.md`) é um pré-prompt incluído em todos os prompts. Regras exemplo: pense antes de codar; declare presunções; pergunte em vez de adivinhar; simplicidade; menor código possível; mudanças cirúrgicas; execução baseada em objetivos; testes verificam intenção, não apenas comportamento.
  - *Citação*: "regra número um, pense antes de codar... Declare suas presunções explicitamente... Estiver incerto, pergunte ao invés de adivinhar. Simplicidade. Primeiro, o menor código possível que resolve o problema. Mudanças cirúrgicas e goal-driven execution... testes que verificam intenção e não apenas comportamento."
  - *Proposta*: `project-setup` deve gerar/validar `agents.md`; `global_rules.md` deve incorporar essas regras; `verification-before-completion` verifica intenção.

- **L325-331**: Criar guidelines específicas por projeto em `agents.md`, e.g., "nunca usar `any` em TypeScript", "rodar linters após terminar a tarefa".
  - *Citação*: "num meu agents.md que eu trabalho com TypeScript, eu explicitamente mando a IA nunca usar any, nunca usar any. Eu explicitamente mando a IA rodar os linters."
  - *Proposta*: `project-setup`/`writing-skills` pode orientar criação de `agents.md` por stack.

### 2.9 APIs detalhadas / OpenAPI

- **L336-363**: Desenvolvimento web é CRUD (API + backend). Se a API está bem detalhada (input/output/comportamento), a IA consegue ler e trabalhar. Criar OpenAPI spec como contexto reduz erros e trabalho.
  - *Citação*: "Se a sua API tá super bem detalhada em qual que é o input, qual que é o output e o que que vai acontecer, a IA consegue ler isso daqui... Joga esse Open API Spec como contexto pra própria IA que ela vai tender a se perder menos."
  - *Proposta*: `api-design` deve gerar/consumir OpenAPI; `planning-pipeline` inclui spec de API antes de `implement`.

### 2.10 Ferramentas: Codex, Code Rabbit, MCP

- **L364-373**: Codex é mais barato que Cloud Code; preferir Codex quando custo importa.
  - *Citação*: "Hoje em dia tem sido o Codex porque ele é mais barato... O Cloud Code eu estouro $200 muito rápido, enquanto o Codex eu não estouro."
  - *Proposta*: `leo`/`cost-optimization` pode sugerir Codex para tarefas de código; `model-interface-preflight` considera custo.

- **L374-415**: Code Rabbit para revisão de código. Há formas de automatizar o loop: Code Rabbit sugere, Codex aplica, volta para o código, sem precisar de input humano até revisão final. MCPs úteis são GitHub e task manager; evitar MCPs desnecessários.
  - *Citação*: "Code Rabbit pra revisão de código... as sugestões sugeridas pelo Code Rabbit voltam aqui pro Codex e depois isso volta aqui pro código... Para mim é GitHub e o Task Manager são os dois mais importantes."
  - *Proposta*: adicionar integração Code Rabbit como skill/fluxo; `mcp-context-audit`/`mcp-lazy-enablement` filtram MCPs; `gh`/`jira` são prioritários.

### 2.11 Testes, pre-commit e dev container

- **L424-429**: Testes estão baratos. Adicionar muitos testes. **Nunca** deletar testes sem aprovação. Escrever essa regra nos MDs.
  - *Citação*: "Testes estão muito baratos. Adiciona um monte de teste... não deletar testes... Ela nunca pode deletar um teste sem que você aceite que o delete, escreve isso aí nos MDs."
  - *Proposta*: `tdd` + `AGENTS.md` regra explícita de preservação de testes; `setup-pre-commit` bloqueia delete sem aprovação.

- **L430-442**: Usar pre-commit hooks. Commits só em branches não-críticas (main protegida). Pre-commit força rodar testes antes de commit.
  - *Citação*: "você pode ter os precommit... quando você manda a IA comitar algo... a sua branch main vai estar protegida... ela consegue ler ali o precommit hook e ver se passou ou não passou... obrigada a testar e ver se passa o teste antes de conseguir comitar."
  - *Proposta*: `setup-pre-commit` deve ser parte de `project-setup` e do fluxo `leo` de build/change.

- **L443-457**: Para "loucuras" com IA, usar dev container. Com `dangerously skip permissions` a IA pode deletar pastas do computador; raro, mas em escala acontece.
  - *Citação*: "se você quiser fazer muita loucura com IA, cara, cria um dev contêiner... se você rodar é com tipo assim dangerously skip permissions o tempo todo, alguma hora a IA vai deletar uma pasta."
  - *Proposta*: `docker`/`project-setup` oferece dev container para sessões destrutivas; `leo` recomenda dev container para high-risk tasks.

### 2.12 A IA não reduz o trabalho total

- **L458-475**: A IA faz a maior parte do **código**, mas não reduz criação de tarefas, revisão, setup, conversa, entendimento de codebase/docs/cliente. Vai acelerar, não facilitar a vida.
  - *Citação*: "A IA vai fazer a maior parte do código... Você consegue enxergar como a criação dessas tarefas é uma tarefa muito grande, a revisão desse código é uma tarefa muito grande... Isso daqui vai te acelerar, mas não vai te facilitar a vida."
  - *Proposta*: `leo`/`planning-pipeline` devem reservar tempo humano para revisão e tarefização; `effort-calibration` ajusta expectativas.

### 2.13 Prompt/skill bloat

- **L476-491**: Não inflar prompts/skills com 1000 linhas. O meio do prompt é esquecido. Quanto mais informação, mais diluída, até a IA ignorar instruções.
  - *Citação*: "Você vai chegar num ponto que os seus prompts vão ter tipo assim 1000 linhas. Não faz isso... tudo que tiver lá no meio... vai ser meio que esquecido... quanto mais informação você adicionar, mais aquela informação vai ser diluída."
  - *Proposta*: `context-window-hygiene`/`prompt_bloat_gate` monitora tamanho de prompts/skills; `writing-skills` exige concisão.

### 2.14 Overengineering e token maxing

- **L492-516**: Cuidado com overengineering e token maxing. Gastar mais tokens não significa melhor resultado; só gasta mais dinheiro. Menos código é melhor (não code golf). Token maxing gera código prolixo, repetido, deteriora codebase, introduz mais vulnerabilidades/dependências, pior UX, lentidão.
  - *Citação*: "Toma cuidado com overengineering, toma cuidado com o tal de token maxing... você tá gastando mais tokens, não quer dizer absolutamente nada... Quanto menos código possível para resolver um problema, melhor... Token Maxing leva a muito código... vai sinceramente deteriorar sua codebase e acabar introduzindo mais vulnerabilidades, mais dependências."
  - *Proposta*: `cost-optimization`/`context-window-hygiene` devem alertar sobre token maxing; `effort-calibration` prioriza soluções simples; `AGENTS.md` regra "menor código possível".

### 2.15 Simplicidade e precisão

- **L517-530**: Documento de 1-2 páginas é melhor que 6-7 páginas, mesmo sendo mais difícil de escrever. Precisão é valiosa.
  - *Citação*: "se você conseguir, me traz um documento de uma até duas páginas... um de uma a duas vai ser muito melhor, porque a nossa precisão é algo extremamente valioso."
  - *Proposta*: `writing-plans`/`planning-pipeline` impõe limite de tamanho em specs/PRDs; `grilling` refina até ser conciso.

### 2.16 Paralelismo

- **L531-556**: Limite de agentes paralelos: 1 bom, 2 ótimo, 3 útil em contextos específicos; passou de 4 vira malabarismo e o humano não consegue revisar.
  - *Citação*: "um agente é bom, dois é ótimo, três pode ser útil... Passou de quatro, cara, eu me perdi... Tô jogando malabarismo pro alto e rezando para dar tudo certo."
  - *Proposta*: `dispatching-parallel-agents` e `leo` devem limitar padrão a 1-3 agentes; configurável, mas alertar acima de 3.

### 2.17 System Design

- **L619-621**: System design é importante na criação de tarefas para definir fronteiras de cada tarefa.
  - *Citação*: "definir as fronteiras de cada tarefa... Tá importantíssimo também o system design."
  - *Proposta*: `api-design`/`database`/`planning-pipeline` devem incluir decisões de system design antes de quebrar em tickets.

---

## 3. `ontologies-keep-honest.md` — Extração sistemática

### 3.1 Neuro-symbolic AI e guardrails

- **L124-128**: LLMs são probabilísticos; neuro-symbolic AI mantém o LLM nos trilhos.
  - *Citação*: "neuro-symbolic AI sort of represents a way to keep the LLM on its guardrails, because LLMs are by nature probabilistic."

### 3.2 Ontologia como especificação formal

- **L246-258**: Ontologia é uma graph data structure com entidades, relações e inferências (RDFS domain/range, OWL).
  - *Citação*: "ontology... think of it as a graph data structure... RDFS. Domain and range... if I say Bob teaches Scooter, I can infer that Bob is a teacher."

### 3.3 Perigos dos loops

- **L313-355**: Loops dão poder computacional (Turing-completo), mas podem quebrar, sair dos trilhos e custar tokens.
  - *Citação*: "Agents are now have loops. Loops give us the last piece... The danger though of loops is that they can break... Loops can drift... loops can cost you money. Token counts crank up."

### 3.4 Validador ontológico no loop

- **L420-435**: Após chamar ferramenta, colocar resultado em forma que o validador possa usar com ontologias do domínio para decidir se é razoável. Se não for, volta ao LLM ou human-in-the-loop.
  - *Citação*: "Call a tool, check the stop reason. If it's a reasonable result, then let's go with it. If it's not reasonable, go back to the LLM. Or get a human in the loop."

### 3.5 Pydantic e ontologia

- **L444-458**: "Pydantic at the door, ontology at the ledger". Validar tipos com Pydantic, resultados com ontologia. Agentes devem ter poucos/sem efeitos colaterais até a validação.
  - *Citação*: "Pydantic is a way to specify the types... check your types with Pydantic and then check your results with the ontology... your agents should try to have no side effects."

### 3.6 Reasoner ontológico

- **L500-506**: Usar reasoner baseado em ontologia para manter LLM honesto, com guardrails baseados em RDFS/OWL.
  - *Citação*: "you can have a reasoner built on ontology to check keep the LLM on track, have guardrails to keep it honest."

---

## 4. Propostas mapeadas para o bundle

A seguir, todas as propostas derivadas dos três textos, organizadas por alvo.

### 4.1 `skills/leo/SKILL.md` (situation router e fluxos)

1. **Build/Change padrão**: issue/task -> `grilling` (intenção) -> `planning-pipeline` (PRD + quebra em tarefas pequenas) -> `implement` + `tdd` -> `code-review` -> `verification-before-completion` -> `finishing-a-development-branch`.
2. **Gate de segurança obrigatório**: `security-audit` antes de `implement` para qualquer mudança que toque API, DB, secrets, endpoints ou infra.
3. **Intenção**: `grilling` deve capturar objetivo final, onde a feature vai e como afeta o usuário antes de gerar PRD.
4. **Tamanho de tarefa**: `planning-pipeline` deve estimar tamanho do PR; quebrar se >500 linhas; PR ideal ~300 linhas.
5. **TDD por padrão**: `tdd` não é opcional; `leo` roteia `implement` junto com `tdd`.
6. **Pre-commit**: `setup-pre-commit` como passo padrão de `project-setup` e build flow.
7. **Dev container para alto risco**: `leo` sugere `docker`/`dev container` quando a tarefa envolve deleções, scripts shell, instalações ou permissões perigosas.
8. **Paralelismo**: `dispatching-parallel-agents` default 1-3 agentes; alerta se >3.
9. **Ferramentas por custo**: `leo`/`cost-optimization` pode sugerir Codex para tarefas simples de código; Cloud Code quando interação IDE justifica.
10. **MCP**: antes de habilitar MCP, `leo` invoca `mcp-context-audit`/`mcp-lazy-enablement`; priorizar GitHub e task manager.
11. **Code Rabbit**: adicionar rota `code-review` com integração Code Rabbit para loop automático de sugestão/aplicação antes da revisão humana final.
12. **Loop ontológico**: após execução de ferramentas críticas, `leo` deve passar resultado por validação (Pydantic + ontologia) antes de aplicar side effects.

### 4.2 `AGENTS.md` / `global_rules.md`

1. **Pense antes de codar**.
2. **Declare presunções explicitamente**; pergunte se incerto.
3. **Menor código possível** que resolve o problema; mudanças cirúrgicas.
4. **Goal-driven execution**: testes verificam intenção, não apenas comportamento.
5. **Nunca logar/outputar secrets** (senhas, tokens, chaves).
6. **Não comitar secrets**; se detectado, alertar para rotação imediata.
7. **Não deletar testes sem aprovação explícita**.
8. **Sempre sanitizar inputs de usuário**.
9. **Endpoints e S3 públicos precisam de justificativa documentada**.
10. **Ações destrutivas exigem confirmação**.
11. **Evitar token maxing/overengineering**; preferir simplicidade.
12. **Limitar prompts/skills a tamanho que preserve atenção do modelo**.

### 4.3 Skills existentes a fortalecer

- `security-audit`: adicionar checklist completo dos 5 princípios (superfície, privilégio, defaults, criptografia, updates) + SAST/WAF + secrets + logging + timing.
- `tdd`: tornar passo padrão; incluir handler/script de testes; preservação de testes.
- `setup-pre-commit`: integrar ao fluxo padrão.
- `api-design`: exigir input/output detalhados; gerar/consumir OpenAPI spec.
- `planning-pipeline`: adicionar campos intenção, tamanho de PR, boundaries; quebra automática de tarefas grandes.
- `grilling`: usar para PRD/intenção antes de implementação.
- `cost-optimization`/`context-window-hygiene`: detectar token maxing e prompt/skill bloat.
- `docker`: fornecer dev container template.
- `mcp-context-audit`/`mcp-lazy-enablement`: gatear habilitação de MCP.
- `verification-before-completion`: incluir SAST, WAF, secret scan, lint, testes de intenção, validação ontológica.
- `using-skills`: alertar sobre one-shot myth e importância de `grilling`.
- `implement`: rejeitar tarefas sem testes, spec clara ou intenção.
- `code-review`: integrar Code Rabbit.

### 4.4 Novas skills / gates candidatas

1. **`ontology-validator`**: validar outputs de ferramentas contra `.devin/notes/structured-knowledge-extraction/knowledge.json` e regras OWL/RDFS mínimas.
2. **`task-sizer`**: estimar tamanho de PR e sugerir quebra quando >500 linhas ou fronteiras ausentes.
3. **`secure-defaults-check`**: verificar `.env.example`, ausência de `.env` no repo, S3/URLs públicos, endpoints sem auth, confirmação em ações destrutivas.
4. **`agent-cost-guard`**: monitorar tokens por loop, alertar sobre token maxing, limitar subagentes.
5. **`intention-capture`**: exigir e validar campo "intenção" em tickets/specs.
6. **`api-context-spec`**: gerar/manter OpenAPI specs como contexto para IA.

### 4.5 Modos operantes

- **`verification-before-completion`**: saída só após SAST, WAF/Dependabot, secret scan, testes (incluindo held-out), lint, validação ontológica e revisão de intenção.
- **`autonomous-gates`/`unlazy`**: cada gate registra evidência; validação não pode ser apenas self-report.
- **`lower-effort`/fast mode**: rápido não é one-shot; mesmo tarefas pequenas precisam de intenção e teste.
- **`continuous-improvement`**: ao alterar skills, usar FASE 0 de pesquisa, reproduzir falha, teste held-out e métrica real.

---

## 5. Limitações encontradas na extração atual

- `structured-knowledge-extraction` lexical não capturou os conceitos-chave; só headings e URLs. Isso sugere melhorar o extrator ou criar `ontology-validator` semântico.
- O `audit.py` e `pytest` revelaram divergência pré-existente entre `config.json` live e bundle, não causada por esta tarefa.
