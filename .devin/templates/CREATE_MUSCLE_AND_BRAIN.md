# Nível de Esforço Recomendado: HIGH
# Perfil Operacional: Engenheiro de Integração de Ferramentas (Toolsmith)

# Goal
Realizar a ingestão autônoma do repositório `{peça o link ao usuario}` no ecossistema `devin-bundle`. O objetivo possui duplo propósito (Dual-Purpose):
1. **Internal Tooling (Músculo):** Empacotar a ferramenta para que você (SWE-2) possa usá-la de forma fluida via CLI (`extensions/`).
2. **Implementation Skill (Cérebro):** Criar um roteiro/documentação para que você saiba como instalar e arquitetar essa tecnologia dentro de projetos de usuários no futuro (`skills/`).

# Context
Sempre que encontramos uma ferramenta open-source poderosa, precisamos ensiná-la ao agente. No entanto, o agente precisa de duas coisas diferentes: ele precisa do binário/script pronto para ser chamado (para automatizar suas próprias tarefas) e precisa da documentação arquitetural (para saber quando recomendar essa ferramenta para um usuário e como escrever código compatível com ela).

# Acceptance Criteria
1. **Reconhecimento (Recon):** 
   - Clone ou faça o curl/fetch do `README.md` e dos arquivos estruturais principais do repositório `NandhaKishorM/laya`.
   - Entenda profundamente qual é o propósito da ferramenta, suas dependências e como ela opera nativamente.
2. **Construção do Músculo (A Extensão):**
   - Crie um *wrapper* ou script de inicialização em um diretório apropriado dentro de `extensions/` (ex: `extensions/laya-tools/`).
   - O wrapper deve seguir nosso contrato: possuir interface de linha de comando (CLI) limpa, usar o `.venv` local caso seja Python, ou binário isolado, e (idealmente) emitir saídas em JSON quando usado por agentes.
3. **Construção do Cérebro (A Skill):**
   - Crie o arquivo `skills/implement-laya/SKILL.md`.
   - Este arquivo DEVE conter:
     - **O que é:** Um resumo denso e preciso do que a ferramenta resolve.
     - **Como o Agente deve usar para si mesmo:** Exemplos de comandos invocando a extensão recém-criada.
     - **Como o Agente deve implementar para o usuário:** Padrões de código, armadilhas comuns (gotchas), instruções de como injetar a ferramenta no código-fonte de um repositório cliente.

# Scope & Non-Goals
- **IN SCOPE:** Leitura da documentação online do repositório alvo, criação do script de extensão (`extensions/`), criação da skill de conhecimento (`skills/`).
- **OUT OF SCOPE:** NÃO instale dependências globais na máquina host (use ambientes virtuais isolados na pasta da extensão).

# Execution Hints & Checkpoints
1. **Fase 1 (Ingestão de Conhecimento):** Use suas ferramentas de rede/browser para acessar o repositório `NandhaKishorM/laya`. **Pare e apresente no terminal um resumo executivo: O que é o Laya, qual linguagem utiliza e qual é o plano para empacotá-lo. Aguarde minha aprovação.**
2. **Fase 2 (O Músculo):** Crie a estrutura em `extensions/`, inclua o arquivo de dependências (se necessário) e o script/wrapper que traduz as saídas do Laya para um formato amigável ao agente.
3. **Fase 3 (O Cérebro):** Escreva o `SKILL.md` garantindo que o "How-to-implement" (Como implementar no código do usuário) esteja alinhado com as melhores práticas de código do criador original.
4. **Fase 4 (Validação):** Execute um *dry-run* invocando sua nova extensão para provar que a ferramenta está viva e funcional.