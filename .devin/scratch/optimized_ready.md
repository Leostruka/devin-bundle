# Nível de Esforço Obrigatório: MAX
# Perfil Operacional: Red Team Lead / Staff Security Engineer

# Goal
Avaliar em profundidade o repo https://github.com/rizinorg/rizin (fork do radare2: framework C de engenharia reversa - disasm multi-arq, analise binaria, debugger, ESIL, rz-diff, rz-bin, rzpipe, decompiler via rz-ghidra/rz-dec) e produzir analise de gaps bidirecional contra a lane ofensiva ja existente no devin-bundle: o que o rizin tem que a lane nao tem, o que ja esta coberto, e o que vale agregar/adotar/ignorar. Veredito tecnico frio sobre se e como integrar rizin melhora a capability local de RE no Windows, nao uma lista de features.

# Context
Lane red existente (verificar todos com read antes de afirmar): skills/red-team/SKILL.md (roteador sobre engagement contract target/window/ROE), skills/re-binary, skills/web-probe, skills/net-probe, skills/wireless-probe, skills/firmware-probe, skills/mobile-probe; extensions/rea-ops/wrapper.py (passthrough whitelist para rea-agents CLI - engines Hopper/Ghidra via doctor); extensions/offsec-tools/wrapper.py (catalogo offsec); agente agents/red-team-lead.md; implementado em PR #88 (commit d990e75). Convencoes: extensions em Python stdlib-only com deps lazy, skills SKILL.md <=~10KB com frontmatter 'Use when...', tests em tests/validation/test_*.py por tokens de contrato, install.ps1 -> %APPDATA%\devin. Regras: Rule 13 (engagement autorizado, sem permission theater, mas toda capability ofensiva declara escopo alvo/janela/ROE; nada de credential harvesting), Rule 12 (verify com ferramentas, citar path/URL por afirmacao), Rule 18 (menor solucao), Rule 2 (sem assinatura de IA). Preferencia do bundle a tooling free/open-source; rizin e LGPL e roda Windows nativo - checar distribuicao (meson build, releases, rzpipe PyPI). Modelo de engenharia reversa atual depende de Hopper/Ghidra pre-instalados via rea-agents; rizin e a alternativa self-contained.

# Acceptance Criteria
1. Arquitetura do rizin mapeada com fontes primarias citadas (arquivos do repo rizinorg/rizin, docs.rizin.re): subsistemas (librz_*), frontends CLI (rizin, rz-bin, rz-diff, rz-asm, rz-gg, rz-find, rz-hash, rz-sign), decompilers disponiveis (rz-ghidra, rz-dec), suporte a arquiteturas, debugger, ESIL, rzpipe/scripting, formato de projeto, distribuicao Windows
2. Mapeamento da lane red do bundle com paths citados: capabilities reais de rea-ops (lista exata de tools expostas pelo wrapper), catalogo de offsec-tools, escopo de cada skill *-probe e do red-team-lead
3. Matriz capability x {rizin, bundle/red} bidirecional cobrindo: disasm/analise estatica multi-arq, decompilacao, analise dinamica/debugger, binary diffing, carving/forensics de binarios, signature analysis, scripting/automacao, integracao headless para agente
4. Lista de gaps priorizada (impacto x esforco), cada um com evidencia (path ou URL) e recomendacao adotar/adaptar/ignorar - incluindo forma de integracao candidata (novo extension wrapper, ampliar rea-ops, rzpipe via Python, ou nada)
5. Veredito final: para RE local no Windows dentro do bundle, rizin agrega o que; nenhuma afirmacao sem citacao
6. Relatorio salvo em .devin/research/rizin-gap-analysis.md; ledger .devin/ledgers/rizin-gap-analysis.md com gates e evidencia

# Scope & Non-Goals
- **IN SCOPE:** Pesquisa de fontes primarias do rizin (webfetch/web_search, GitHub repo files, docs oficiais)
- **IN SCOPE:** Leitura e mapeamento da lane red do bundle (skills/red-team*, skills/*-probe, extensions/rea-ops, extensions/offsec-tools, agents/red-team-lead.md)
- **IN SCOPE:** Relatorio tecnico markdown com citacoes, matriz e gaps priorizados
- **OUT OF SCOPE:** Implementar wrappers, skills, extensions ou profiles novos
- **OUT OF SCOPE:** Instalar rizin ou qualquer binario no host
- **OUT OF SCOPE:** Executar scans, analises ou ataques contra qualquer alvo real
- **OUT OF SCOPE:** Commits, PRs ou mudancas fora de .devin/
- **OUT OF SCOPE:** Avaliar marketing, comunidade ou pricing

# Execution Hints & Checkpoints
1. **Fase 1:** Fase 1: Mapear rizin via fontes primarias (repo tree, README, docs.rizin.re, releases): subsistemas, frontends, decompilers, arquiteturas suportadas, debugger/ESIL, rzpipe, distribuicao Windows. Notas com citacoes em .devin/research/. PARE e aguarde aprovacao.
2. **Fase 2:** Fase 2: Mapear lane red do bundle lendo SKILL.md/wrapper.py citados - tabela de capabilities com paths.
3. **Fase 3:** Fase 3: Gap analysis bidirecional - matriz capability, gaps priorizados com evidencia e recomendacao.
4. **Fase 4:** Fase 4: Veredito + relatorio final salvo; revisar contra acceptance criteria antes de declarar pronto.
