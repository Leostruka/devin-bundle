# SWE-2 via Devin CLI: capacidade de ação, percepção e controle

Consulta: **16/09/2026**. Alvo principal: Windows. Pesquisa, não atualização operacional.

## 0. Escopo, método e conclusão executiva

**150 vetores: 5 categorias × 3 pilares × 10 tópicos.** F = ferramentas; C = cognição/eficiência; A = arquitetura/ecossistema. Um vetor é uma perspectiva de investigação, não necessariamente um produto diferente. Repetições entre categorias são deliberadas: maturidade, lançamento e desempenho são critérios distintos.

**Maior impacto provável:** fechar o ciclo observar → identificar → validar → agir → verificar. Priorizar identidade dos alvos, coordenadas, contexto e recuperação antes de sofisticar movimentos. Esta é uma recomendação de engenharia, não ganho medido nesta máquina. [S35][S40][S41]

Ordem proposta:

1. Coordenadas corretas, hints válidos e distinção entre despacho/efeito.
2. UIA ou DOM/CDP quando disponíveis; pixels para lacunas e confirmação visual.
3. Cache UIA e consultas seletivas, reduzindo comunicação interprocessos.
4. Sessão persistente se medições justificarem amortizar inicialização.
5. DXGI/WGC e processamento regional se captura dominar a latência.
6. Modos separados: determinístico, demonstração suave e testes autorizados.

### Método e limites

- Fontes primárias: documentação oficial, repositórios dos autores, registros de pacotes e artigos originais. A seção 7 registra URLs e escopo de evidência.
- Busca exploratória, inspeção de trechos primários indexados, leitura direta de documentos e leitura do código local. Não houve auditoria integral de cada biblioteca nem reprodução de seus benchmarks.
- “Melhores” significa referência forte por finalidade, não ranking universal de setembro de 2026.
- “Recentes” inclui releases/atualizações de 2025–2026, não apenas nascimento de projetos. Datas e exceções explícitas na matriz.
- Não há comprovação de aumento exponencial, latência ponta a ponta sub-milissegundo ou ganho visual específico do SWE-2.
- Não foi encontrada, nas fontes públicas consultadas, especificação do tokenizer/encoder visual interno do SWE-2, preço por token visual ou API de manipulação de seu KV-cache. Não preencher essas lacunas com detalhes de outros modelos.
- Nenhum desktop pessoal foi capturado/controlado. Não foram instalados drivers, bibliotecas ou modelos. Benchmarks publicados são dados dos autores, não resultados locais.
- Evasão de CAPTCHA/antibot, ocultação de automação, bypass de UAC e injeção ofensiva são tratados apenas como limites e defesa, sem procedimentos.

### Divergências resolvidas

| Tema | Divergência observada | Decisão |
|---|---|---|
| ST-Lite | v1 cita 2,45×; v3 cita até 2,35× | Usar v3, 26/08/2026. [S50] |
| OSWorld-Human | v1 cita 1,4–2,7× passos; v2 cita 2,7–4,3× | Usar v2, 18/05/2026. [S40] |
| OSWorld | Original, Verified e 2.0 diferem | Não combinar scores em ranking único. [S38][S41] |
| Appium Windows | Documentação histórica diz servidor incluído | README atual: instalação separada desde v3 e alerta de manutenção. [S19] |
| Releases Rust | Índices mostram versões diferentes | Citar versão/data observadas, sem garantir “última absoluta”. [S25][S30] |
| PrintWindow | Exemplos informais sugerem flags universais | Referência consultada não garante captura de toda superfície GPU. [S06] |
| Flash–Hogan | Página editorial retornou HTTP 403 | Abstract primário indexado acessível; derivação matemática própria explicitada. [S78] |

## 1. Implementação atual e lacunas verificadas

Caminhos relativos à raiz do repositório; leitura direta dos arquivos citados.

```text
screenshot.py → mss → pixels → PNG/Pillow
       └─────→ cu_hints.py → comtypes/UIA → hints + sidecar temporário
mouse.py ────→ resolve_hint → coordenadas → pynput.mouse
       └─────→ cu_motion.py → perfil/trajetória/atrasos
type_text.py → cu_motion.py → cadência → pynput.keyboard
```

| Superfície | Evidência local | Consequência |
|---|---|---|
| Dependências | `requirements.txt:1–5`: mss 10.2.0, pynput 1.8.2, Pillow 12.2.0, uiautomation 2.0.29, comtypes 1.4.16 | Aproveitar stack existente antes de migrar linguagem. |
| Captura/UIA | `screenshot.py:153–158`: pixels antes da enumeração UIA | Snapshot imagem/árvore não é atômico; posições podem divergir durante mudanças. |
| Propriedades | `cu_hints.py:65–81`: FindAll seguido de Current por elemento | FindAllBuildCache pode reduzir round-trips; medir antes/depois. |
| Corte | `cu_hints.py:20–21,105–113`: limite após enumeração e deduplicação por tipo/centro | Limite de saída não limita custo da busca; elementos distintos podem colapsar. |
| Timeout | `cu_hints.py:90–102`: thread daemon, espera de até 6 s | Timeout não cancela chamada COM; serviço persistente precisa reciclar worker isolado. |
| Sidecar | `cu_hints.py:131–152`: caminho fixo; x/y/name/type | Sem sessão, tempo, janela ou geração; risco de hints cruzados/obsoletos. |
| Fallback | `screenshot.py:167–172` não invalida sidecar anterior | Hint anterior pode continuar resolvível; achado estático, não exploração executada. |
| Grade | `screenshot.py:69–75`: rótulos começam no zero local | Região/monitor não expressam origem global. Hints, diferentemente, aplicam ox/oy em `:80–102`. |
| Metadados | `screenshot.py:154–155` omite origem da captura | Agente não recebe transformação completa imagem → desktop. |
| Sucesso | `mouse.py:128–152`, `type_text.py:117–139` | `ok:true` confirma despacho, não mudança da aplicação. `USAGE.md:145–157` reconhece isso. |
| Tempo | `mouse.py:144–145` reporta duração de movimento; `cu_motion.py:146–149` dorme por ponto | `secs` não é latência real e não inclui todo clique/verificação. |
| Fast | `cu_motion.py:152–165`: pre-click e hold de 0,05 s cada | Movimento instantâneo não significa clique completo sub-ms. |
| Human | `cu_motion.py:107–138,185–203`: Fitts, controles aleatórios, jitter/overshoot e cadência gaussiana | Heurística, não validação biomecânica ou modelo de digramas. |
| Cleanup | `mouse.py:175–199`, `type_text.py:89–98`: press/release sem finally de gesto | Prever liberação de inputs da sessão quando houver exceção. |
| Testes | Busca em `tests/` por cu_motion, cu_hints, screenshot.py, type_text.py não retornou referências | Não prova ausência de testes indiretos; criar testes dedicados sem apagar existentes. |

## 2. Matriz dos 150 vetores

“Aplicação” e “limite” são julgamento deste relatório. Referências sustentam o mecanismo, não um ganho local. Os eixos A–F são detalhados na seção 3.

### 2.1 Categoria 1 — Referências fortes / padrão ouro por finalidade

#### Ferramentas — 10

| ID | Tópico e evidência | Aplicação proposta | Limite / trade-off |
|---|---|---|---|
| C1-F01 | Playwright: actionability e auto-waiting. [S10] | Browser autorizado por role/name, seguido de assertion. | Não controla desktop inteiro. |
| C1-F02 | FlaUI: wrappers UIA2/UIA3. [S21] | Testes nativos Windows com patterns. | Introduz .NET; UIA3 não vence em todo WinForms. |
| C1-F03 | pywinauto: Win32 e UIA. [S14] | Roteamento conforme toolkit. | Owner-drawn/canvas podem não expor controles. |
| C1-F04 | UIA nativa: propriedades e patterns em cache. [S04][S100] | Invoke/Value/Selection e leitura em lote. | Provider lento/incorreto continua possível. |
| C1-F05 | Accessibility Insights for Windows. [S71] | Inspeção de propriedades/patterns ausentes. | Inspetor não substitui executor. |
| C1-F06 | OmniParser: pixels → elementos estruturados. [S22] | Fallback para ícones sem UIA. | Inferência extra; bounding box não prova acionabilidade. |
| C1-F07 | DXcam: DXGI/WinRT, frames e buffers. [S23][S99] | Captura contínua quando necessária. | FPS não mede latência de decisão. |
| C1-F08 | windows-capture Rust/Python. [S24] | Backend WGC/DXGI orientado a eventos. | Ciclo de vida de textures e compatibilidade do SO. |
| C1-F09 | Playwright MCP: snapshots acessíveis. [S33] | Referência para contrato compacto de observação. | Não exige instalar outro servidor para copiar a ideia. |
| C1-F10 | Selenium/WebDriver BiDi. [S12] | Testes cross-browser e eventos. | Sessão/protocolo adicionam overhead. |

#### Cognição — 10

| ID | Tópico e evidência | Aplicação proposta | Limite / trade-off |
|---|---|---|---|
| C1-C01 | ReAct: observar e agir intercaladamente. [S44] | Decidir usando evidência recente. | Não exigir raciocínio interno exposto. |
| C1-C02 | Reflexion: feedback textual sem atualizar pesos. [S45] | Falha concreta e correção curta por episódio. | Autoavaliação sem oráculo pode reforçar erro. |
| C1-C03 | Planejamento hierárquico proativo. [S36] | Submetas com conclusão verificável. | Especialistas adicionais custam chamadas. |
| C1-C04 | Controller de estados e output estruturado. [S35] | Separar intenção, ação tipada e resultado. | JSON válido não garante semântica correta. |
| C1-C05 | Esperas por estado. [S10] | Condição e deadline em vez de sleep fixo. | Eventos podem faltar; polling limitado como fallback. |
| C1-C06 | Cache de propriedades UIA. [S04][S100] | Sintetizar controles relevantes em lote. | Invalidação é obrigatória. |
| C1-C07 | Grounding híbrido/especializado. [S35][S36] | Semântica para intenção, imagem para confirmação. | Árvore extensa ou errada pode ser pior que pixels. |
| C1-C08 | Estado durável e interrupções. [S47] | Checkpoints nas fronteiras da tarefa. | Retomada não pode duplicar efeitos externos. |
| C1-C09 | Esforço proporcional no SWE-2. [S01] | Menor esforço para rotina; escalar ambiguidade. | Benchmark coding não comprova benefício GUI. |
| C1-C10 | Confirmação de ações sensíveis no CUA. [S43] | Autonomia distinta de autorização. | Escalada humana acrescenta tempo. |

#### Arquitetura — 10

| ID | Tópico e evidência | Aplicação proposta | Limite / trade-off |
|---|---|---|---|
| C1-A01 | OSWorld: avaliação por execução. [S38] | Validar resultado final, não só clique. | Fixar versão, tarefas e dependências externas. |
| C1-A02 | OSWorld-Human: eficiência de trajetória. [S40] | Medir redundância e tempo por etapa. | Caminho humano não é ótimo universal para APIs. |
| C1-A03 | WindowsAgentArena/Navi. [S39] | Casos Windows com reset reproduzível. | Não extrapolar score para esta instalação. |
| C1-A04 | Cradle: memória, reflexão, skills e pixels. [S34] | Referência quando APIs são indisponíveis. | Universalidade visual custa grounding. |
| C1-A05 | UFO2: HostAgent, AppAgents, UIA+visão+API. [S35] | Roteamento por aplicação. | Não copiar AgentOS inteiro para poucos scripts. |
| C1-A06 | Agent S2: mistura de especialistas. [S36] | Separar planejamento de localização. | Mais modelos, memória e latência. |
| C1-A07 | UI-TARS: agente GUI visual nativo. [S37] | Espaço de ações e trajetórias de referência. | Não descreve internals do SWE-2. |
| C1-A08 | Claude Computer Use. [S42] | Referência histórica de treinamento visual/tool-use. | Não é declaração de liderança atual. |
| C1-A09 | OpenAI CUA. [S43] | Loop com autocorreção e intervenção sensível. | Resultados dependem de orçamento e benchmark. |
| C1-A10 | OSWorld 2.0. [S41] | Testar requisitos longos e estado implícito. | Diferente de grounding curto. |

### 2.2 Categoria 2 — Lançamentos e pesquisa recentes

#### Ferramentas/bindings — 10

Datas indicam releases observados. Scap e Enigo são de 2025, não lançamentos de 2026. Não se afirma que toda entrada seja a versão mais nova absoluta.

| ID | Tópico e evidência | Aplicação proposta | Limite / trade-off |
|---|---|---|---|
| C2-F01 | windows-capture 2.0.1, 08/08/2026. [S24] | Adapter opcional Rust/Python WGC/DXGI. | Homologar API 2.x e builds Windows. |
| C2-F02 | xcap 0.9.7, 20/07/2026. [S25] | Captura Rust cross-platform. | Wayland e vídeo têm limitações na matriz publicada. |
| C2-F03 | uiautomation-rs 0.25.0, 05/05/2026. [S28] | Patterns/eventos UIA em worker nativo. | Rust não remove custo do provider COM. |
| C2-F04 | chromiumoxide 0.9.1, 25/02/2026. [S29] | CDP assíncrono em Rust. | Chromium, não Gecko/WebKit. |
| C2-F05 | thirtyfour 0.37.4, 23/07/2026; índice mostra 0.37.5 em 12/08. [S30] | WebDriver/CDP/BiDi em Rust. | Troca de linguagem não comprova aceleração. |
| C2-F06 | AccessKit 0.24.1, 12/06/2026. [S31] | Expor semântica em aplicação própria. | Provider/toolkit, não controlador genérico do desktop. |
| C2-F07 | DXcam 0.3.0; overhaul documentado em 2026. [S23][S99] | ROI, timestamps, recuperação e views. | Changelog lido não fixa data completa; não inventá-la. |
| C2-F08 | windows-rs/windows 0.62.2, 06/10/2025. [S32] | Bindings Win32/WinRT diretos. | Features, ownership e compilação continuam necessários. |
| C2-F09 | scap 0.1.0-beta.1, 04/08/2025. [S26] | Comparar WGC/ScreenCaptureKit/PipeWire. | Pré-release; não adotar automaticamente em produção. |
| C2-F10 | Enigo 0.6.1, 28/08/2025. [S27] | Adapter Rust portátil de input. | Sem garantia temporal ou bypass de permissões. |

#### Cognição/compressão/inferência — 10

| ID | Tópico e evidência | Aplicação proposta | Limite / trade-off |
|---|---|---|---|
| C2-C01 | GUIPruner, 26/02/2026. [S49] | Resolução temporal e poda espacial preservando layout. | Tokens internos exigem controle do VLM. |
| C2-C02 | ST-Lite v3, 26/08/2026. [S50] | Cache espaço-trajetória num grounder aberto. | Não é opção comprovada do SWE-2/CLI. |
| C2-C03 | STaR-KV, 01/06/2026. [S51] | Importância por subespaço e estabilidade temporal. | Ganhos de memória dependem do backbone. |
| C2-C04 | MementoGUI, 18/05/2026. [S52] | Memória textual com evidência visual regional. | Controller aprendido acrescenta custo. |
| C2-C05 | TRACE, 09/09/2026. [S53] | Admissão de evidência com cobertura espacial. | Paper diz que código será disponibilizado; não é pacote confirmado. |
| C2-C06 | Where and How to Prune v4, 09/08/2026. [S54] | Reuso de embeddings ViT entre etapas. | Encoder/preprocessing devem coincidir. |
| C2-C07 | GUI-KV, 2025. [S55] | Baseline espacial/temporal de compressão. | Não equivale a truncar JSON ou enviar hashes ao LLM. |
| C2-C08 | SWE-2, 10/09/2026: penalidade de custo por esforço. [S01] | Esforço alinhado à dificuldade observada. | Treinamento do fornecedor não é autotuning local. |
| C2-C09 | SWE-2 serving de rollouts: draft online e prefill agrupado. [S01] | Separar TTFT, throughput e custo total. | Não são comandos/configurações públicas do CLI. |
| C2-C10 | Speculative Macro Commit, 03/09/2026. [S56] | Macros em snapshots isolados. | Tool-use/AppWorld, não Windows; nada de especulação no desktop real. |

#### Arquitetura/ecossistema — 10

| ID | Tópico e evidência | Aplicação proposta | Limite / trade-off |
|---|---|---|---|
| C2-A01 | WebMCP preview, 10/02/2026. [S57] | Ações declarativas/imperativas em sites próprios. | Preview, não suporte universal. |
| C2-A02 | WebDriver BiDi Working Draft, 01/06/2026. [S58] | Eventos padronizados cross-browser. | Draft não é Recommendation; testar engines. |
| C2-A03 | MCP Apps, 26/01/2026. [S62] | UI interativa hospedada no cliente. | Não prova suporte no Devin CLI local nem controle do SO. |
| C2-A04 | WGC DirtyRegionMode. [S63] | Negociar capacidade por build. | “Windows 10/11” não garante essa API. |
| C2-A05 | AccessKit e adapters. [S31] | Aplicações agent-ready pela acessibilidade. | IDs/eventos corretos são essenciais. |
| C2-A06 | Portal ScreenCast/PipeWire. [S59] | Captura Wayland autorizada. | Preservar seleção e consentimento. |
| C2-A07 | libei/EIS. [S60] | Input autorizado pelo compositor. | Servidor distingue eventos para controle de acesso. |
| C2-A08 | Flutter Windows MSAA/IAccessibleEx/UIA. [S61] | Inspecionar semântica antes de OCR universal. | Canvas customizado pode permanecer opaco. |
| C2-A09 | OSWorld 2.0, revisão 13/07/2026. [S41] | Estado externo e mudanças durante tarefas. | Pin de avaliador/dados e separação de protocolos. |
| C2-A10 | Survey de eficiência GUI, 02/09/2026. [S98] | Organizar observação, memória, ação e runtime. | Survey é mapa; métricas voltam aos originais. |

### 2.3 Categoria 3 — Mainstream e pipelines consolidados

#### Ferramentas — 10

| ID | Tópico e evidência | Aplicação proposta | Limite / trade-off |
|---|---|---|---|
| C3-F01 | Selenium. [S12] | Suites multi-browser existentes. | Não controla UI externa ao browser. |
| C3-F02 | Playwright. [S10][S11] | Locators/waits e snapshots acessíveis. | Headless não reproduz tudo do desktop real. |
| C3-F03 | PyAutoGUI. [S13] | Prototipagem de mouse/teclado e fail-safe. | Coordenadas frágeis; preservar parada de emergência. |
| C3-F04 | pynput. [S20] | Manter backend inicial do bundle. | Limitações documentadas de eventos e teclas. |
| C3-F05 | Python-UIAutomation-for-Windows. [S16] | Ampliar dependência existente para patterns. | Provider determina cobertura. |
| C3-F06 | pywinauto. [S14] | UI legada/moderna por backend apropriado. | Descoberta requer inspeção por aplicação. |
| C3-F07 | xdotool/XTEST. [S17] | Ambiente de testes X11. | XWayland não concede acesso a todo Wayland. |
| C3-F08 | Robot Framework/SeleniumLibrary. [S15] | Keywords reutilizáveis e resultados legíveis. | Camada adicional, semântica ainda no Selenium. |
| C3-F09 | SikuliX. [S18] | Matching visual sem DOM/UIA. | Linhagem/fork mudou; homologar manutenção. |
| C3-F10 | Appium Windows/WinAppDriver. [S19] | Suites legadas WebDriver desktop. | README alerta servidor sem manutenção há anos. |

#### Prompting e tool-use — 10

| ID | Tópico e evidência | Aplicação proposta | Limite / trade-off |
|---|---|---|---|
| C3-C01 | ReAct. [S44] | Resultado de ferramenta como evidência externa. | Texto da tela não vira ordem autorizada. |
| C3-C02 | Few-shot de ações. [S44] | Exemplos curtos com alvo e pós-condição. | Exemplos podem fixar seletores obsoletos. |
| C3-C03 | Output estruturado. [S35] | JSON versionado com ações permitidas. | Validar também semântica, não só schema. |
| C3-C04 | Plan-and-execute hierárquico. [S36] | Objetivo longo separado do próximo passo. | Replanejar quando UI muda. |
| C3-C05 | Router por aplicação. [S35] | Escolher adapter semântico. | Não gastar chamada LLM em escolha trivial. |
| C3-C06 | Reflexão por divergência. [S45] | Ação, erro, evidência e hipótese curta. | Reflexão em todo clique gera overhead. |
| C3-C07 | Checkpoint/intervenção. [S47] | Pausar efeitos não autorizados. | Retomada requer reobservar SO. |
| C3-C08 | Memória estruturada. [S48] | Restrições, artefatos e pendências. | Histórico integral custa contexto. |
| C3-C09 | Compactação por relevância. [S46][S48] | Remover redundância, preservar negativas críticas. | Compressão lossy exige held-out. |
| C3-C10 | Separar instruções e conteúdo externo. [S73] | UIA/OCR/DOM tratados como dados. | Delimitadores não são defesa completa. |

#### Pipelines — 10

| ID | Tópico e evidência | Aplicação proposta | Limite / trade-off |
|---|---|---|---|
| C3-A01 | Fixture → browser → assertion. [S10] | Verificar estado e artefato final. | Dispatch não é assertion. |
| C3-A02 | Snapshot de acessibilidade. [S11] | Regressão de roles e estrutura. | Não verifica contraste nem todos os pixels. |
| C3-A03 | Selenium + Robot keywords. [S15] | Reuso de workflows conhecidos. | Paralelismo exige sessões/dados independentes. |
| C3-A04 | Desktop UIA por aplicação. [S14] | Vincular PID/janela antes de localizar alvo. | Reinício invalida referências. |
| C3-A05 | Appium em Windows dedicado. [S19] | Regressão de stack já existente. | Manutenção e privilégios mínimos. |
| C3-A06 | Template matching. [S18] | ROI antes/depois de ação visual. | Tema, DPI e animações afetam matching. |
| C3-A07 | OCR regional. [S87] | Texto sem árvore; segmentação adequada. | Não revela foco/enabled/recebimento de eventos. |
| C3-A08 | Extração desktop por árvore. [S16] | Tabelas/listas autorizadas. | Virtualização, scroll e deduplicação. |
| C3-A09 | Reset de VM + avaliação funcional. [S38][S39] | Repetir estado inicial controlado. | Apenas ambiente descartável autorizado. |
| C3-A10 | Pipeline Linux por compositor/toolkit. [S17][S69] | X11 ou acessibilidade conforme aplicação. | Não presumir equivalência com Windows. |

### 2.4 Categoria 4 — Nicho e testes defensivos

Ferramentas de hooking/injeção são classificadas para diagnóstico autorizado, sem instruções ofensivas, invisibilidade ou bypass.

#### Ferramentas — 10

| ID | Tópico e evidência | Aplicação proposta | Limite / trade-off |
|---|---|---|---|
| C4-F01 | Interception: biblioteca/driver. [S64] | Laboratório de compatibilidade de periféricos. | Licenciamento próprio, assinatura e risco kernel; não evasão. |
| C4-F02 | ViGEm: Xbox 360/DS4 virtuais. [S65][S101] | Inventário de legado. | Aposentado; não é teclado/mouse HID genérico. |
| C4-F03 | Virtual HID Framework. [S66] | Produto legítimo de periférico/acessibilidade. | Complexidade KMDF/WDM, não atalho UAC. |
| C4-F04 | Microsoft Detours. [S67] | Instrumentar aplicativo próprio em laboratório. | Altera execução; não adulterar terceiros. |
| C4-F05 | Frida. [S68] | Diagnóstico autorizado de falha nativa. | Não integrar instrumentação ao caminho normal de clique. |
| C4-F06 | dogtail. [S69] | GTK/GNOME por acessibilidade. | Depende de provider e compositor. |
| C4-F07 | libei/libeis. [S60] | Emulação Wayland autorizada. | Permissão controlada pelo servidor. |
| C4-F08 | libevdev/uinput. [S70] | Testes isolados de dispositivos Linux. | Acesso privilegiado ao dispositivo. |
| C4-F09 | Accerciser. [S72] | Inspeção AT-SPI. | Linux, não UIA Windows. |
| C4-F10 | Hypothesis stateful. [S74] | Sequências contra fixtures próprias. | Definir oráculo/limites antes de gerar ações. |

#### Abordagens não convencionais — 10

| ID | Tópico e evidência | Aplicação proposta | Limite / trade-off |
|---|---|---|---|
| C4-C01 | Bandit/Thompson sampling. [S95] | Seleção de adapter em sandbox por custo/sucesso. | Proposta; não explorar ações perigosas por recompensa. |
| C4-C02 | Sequências estocásticas. [S74] | Variar navegação com seed/replay. | Sem oráculo, aleatoriedade é ruído. |
| C4-C03 | Aprendizado verbal episódico. [S45] | Reutilizar falhas concretas. | Não é fine-tuning do SWE-2. |
| C4-C04 | Grounder local especializado. [S81] | Localização visual subordinada à política. | “Microscópico” não é garantia de VRAM/qualidade. |
| C4-C05 | OCR móvel em cascata. [S86] | ROI primeiro; ampliar modelo sob falha. | Pode perder símbolos/texto pequeno. |
| C4-C06 | Verificação diferencial UIA × imagem. [S35][S71] | Bloquear quando modalidades divergem. | Ambas podem refletir estado velho. |
| C4-C07 | Memória por evento/recorte. [S52] | Preservar evidência útil à submeta. | Seleção pode descartar informação futura. |
| C4-C08 | Testes metamórficos. [S74] | Variações de tema/DPI/idioma com invariantes. | Proposta; invariância precisa justificativa. |
| C4-C09 | Macros especulativas isoladas. [S56] | Pré-execução somente com rollback real. | Primeiro passo igual não garante estado externo igual. |
| C4-C10 | Grounding grosseiro → refinamento. [S22][S36] | Painel, elemento e região clicável. | Desnecessário quando UIA resolve diretamente. |

#### Falhas de interface/parsing — 10

Classes de risco, não dez CVEs confirmadas neste repositório.

| ID | Tópico e evidência | Teste/defesa propostos | Limite / trade-off |
|---|---|---|---|
| C4-A01 | Prompt injection visual/OCR. [S73] | Tela não modifica política/objetivo. | Sem payload ofensivo ou promessa de filtro perfeito. |
| C4-A02 | Nome acessível malicioso/confusável. [S73][S71] | Serialização como dado e identidade estrutural. | Nome não autentica processo. |
| C4-A03 | Hint stale/TOCTOU. [L01] | Geração, janela e revalidação antes de agir. | Layout ainda pode mudar após check. |
| C4-A04 | Overlay e roubo de foco. [S10][L04] | Foreground e região acionável confirmados. | Estar no retângulo não prova recebimento. |
| C4-A05 | DPI/origem/monitores. [L03] | Transformação explícita, testes de origem negativa. | Grade local não é coordenada global. |
| C4-A06 | Provider travado/árvore excessiva. [S05][L01] | Worker reciclável e consultas limitadas. | Timeout de thread não cancela COM. |
| C4-A07 | Virtualização/reuso de itens. [S14][S71] | Reobservar conteúdo depois de scroll. | Item offscreen pode não existir na árvore. |
| C4-A08 | Unicode/IME/clipboard. [S02][S89][S94] | Testes sintéticos de composição e encoding. | Tecla, caractere e valor são diferentes. |
| C4-A09 | Mensagens assíncronas/ponteiros. [S07] | Marshaling documentado e validação no app próprio. | PostMessage não é input universal. |
| C4-A10 | Races e thread UI saturada. [S07][S74] | Sequências limitadas, watchdog e reset isolado. | Não causar indisponibilidade de terceiros. |

### 2.5 Categoria 5 — Eficiência e baixa latência

**Não há garantia comparável sub-milissegundo para os dez itens.** São caminhos candidatos. Ausência de benchmark é registrada, não preenchida com estimativas.

#### Bindings/ferramentas — 10

| ID | Tópico e evidência | Aplicação proposta | Limite / trade-off |
|---|---|---|---|
| C5-F01 | Win32 C/C++ SendInput em lote. [S02] | Menos chamadas FFI por sequência. | Inserção não mede consumo/paint; UIPI permanece. |
| C5-F02 | Rust windows-rs. [S32] | Win32/DXGI/D3D/WinRT tipados. | Não elimina IPC/sincronização GPU. |
| C5-F03 | Python ctypes. [S82] | Adapter Win32 mínimo. | ABI/alinhamento/retornos precisam exatidão. |
| C5-F04 | pywin32. [S83] | COM/GDI/janelas via Python. | Cobertura varia; wrapper não é benchmark. |
| C5-F05 | DXcam. [S23] | Frame novo, ring buffer e view local. | View sobrescrevível; FPS não é latência total. |
| C5-F06 | windows-capture. [S24] | Textures e callbacks. | Readback/encoding/Python ainda podem copiar. |
| C5-F07 | MSS. [S84] | Baseline portátil e ROI ocasional. | API latest pode diferir do pin 10.2.0. |
| C5-F08 | D3DShot. [S85] | Baseline histórico DXGI Python. | Não adotar pelo slogan “fastest”. |
| C5-F09 | xcap. [S25] | Captura Rust por monitor/janela. | Backend/OS determinam desempenho real. |
| C5-F10 | Enigo. [S27] | Input Rust portátil. | Sem garantia de invisibilidade/sucesso/deadline. |

#### Contexto/caching — 10

| ID | Tópico e evidência | Aplicação proposta | Limite / trade-off |
|---|---|---|---|
| C5-C01 | Síntese seletiva UIA. [S04][S100] | Role/name/state/bounds dos candidatos. | Preservar warnings, foco e disabled. |
| C5-C02 | Diff por identidade/geração. [S31][S04] | Upsert/remove após base conhecida. | Proposta; delta sem base exige resync. |
| C5-C03 | Cache de embeddings locais. [S54] | Reusar imagem/preprocessing idênticos. | Não manipula embeddings internos SWE-2. |
| C5-C04 | Hash exato de ROI. [S03][S54] | Evitar OCR repetido byte-identical. | Hash perceptual pode ocultar mudança de dígito. |
| C5-C05 | Envelhecer resolução histórica. [S49] | Atual nítida; antigas resumidas. | Evidência fina deve ser recuperável. |
| C5-C06 | Memória por tarefa. [S52][S48] | Restrições/resultados fora do replay bruto. | Recuperação errada também custa. |
| C5-C07 | Prefixo estável. [S48] | Menos churn; caching quando suportado. | Economia depende do backend, sem números presumidos. |
| C5-C08 | Reflexão só em divergência. [S40][S45] | Verificador barato antes de LLM. | Pode perder erro sem oráculo forte. |
| C5-C09 | Batching com barreiras. [S35] | Menos turnos sem plano cego. | Mudança de foco/estado interrompe lote. |
| C5-C10 | Poda KV específica GUI. [S50][S51] | Experimento com modelo aberto e held-out. | Fora da configuração pública comprovada do CLI. |

#### Captura/streaming — 10

| ID | Tópico e evidência | Aplicação proposta | Limite / trade-off |
|---|---|---|---|
| C5-A01 | DXGI Desktop Duplication. [S03] | Atualizações em texture D3D. | Recuperar access lost; timeout não é tela preta. |
| C5-A02 | Move rects antes de dirty rects. [S03] | Reconstruir frame na ordem correta. | Ler movimentos do frame anterior preservado. |
| C5-A03 | Pipeline GPU-residente. [S03][S91] | Readback apenas da ROI necessária. | Zero-copy descreve fronteira específica. |
| C5-A04 | Ring buffer latest-frame. [S23] | Evitar fila de frames obsoletos. | Lease/cópia para views; resync após perda de base. |
| C5-A05 | WGC por janela. [S24][S63] | Captura autorizada do alvo. | Resize, encerramento e build do SO. |
| C5-A06 | NVENC baixa latência. [S91] | Vídeo remoto quando consumidor suportar. | Texto sofre compressão; codec acrescenta atraso. |
| C5-A07 | PipeWire/DMA-BUF. [S92][S59] | Buffers Linux negociados. | Modifiers incompatíveis exigem fallback. |
| C5-A08 | ScreenCaptureKit. [S93] | Portabilidade macOS nativa. | Permissões e CMSampleBuffer; não Win32. |
| C5-A09 | Multimonitor/origem/rotação. [S03][L03] | Transformação por monitor/frame. | DPI, HDR e rotação invalidam cache. |
| C5-A10 | Eventos e backpressure. [S05][S23][S35] | Captura desacoplada; executor único de inputs. | Não enviar todos os frames ao LLM. |

## 3. Eixos A–F

### Eixo A — SWE-2, representação e autocorreção

#### A.1 O que é publicado, inferido e controlável

A Cognition descreve SWE-2 como pós-treinado sobre Kimi K3, com treinamento por reforço que considera custo e diferentes níveis de esforço. Descreve também comportamento de exploração e infraestrutura de serving de rollouts. Isso **não especifica** o encoder visual usado no Devin CLI, tamanho de patches, número de tokens por screenshot, fusão entre modalidades ou exposição de embeddings. Não é possível responder honestamente “como o SWE-2 processa internamente tokens visuais” além desse limite documental. [S01]

Em VLMs pesquisados, screenshots são convertidos em representações visuais; compressão pode ocorrer no encoder, nos tokens transmitidos ao LLM ou no KV-cache. GUIPruner, ST-Lite e o estudo de reuso de ViT atuam em pontos distintos. Transpor seus mecanismos para um modelo fechado exige suporte do fornecedor; reenviar uma imagem menor é uma transformação de entrada, não acesso ao cache interno. [S49][S50][S54]

JSON/hints são texto estruturado no contrato da ferramenta. Não existe evidência de que SWE-2 reconheça um campo `hint` como canal privilegiado ou mais confiável. A vantagem prática é reduzir inferência de coordenadas: o executor já sabe a posição associada ao alvo. Essa associação deve ser atual e verificável. [L01][L03]

| Camada | Controlável no projeto | Não assumir |
|---|---|---|
| Observação | Escopo UIA, campos, ROI, resolução, frequência, metadados | Taxa fixa bytes → tokens visuais |
| Memória | Resumo factual, checkpoints, referências a artefatos | Que compactação preserve toda restrição |
| Execução | Backend, precondições, timeout, batch e verificação | Que “input aceito” signifique sucesso |
| Modelo/serving | Seleção de modelo conforme interface documentada | Acesso a pesos, KV-cache, draft model ou scheduler |

#### A.2 Quando UIA sintetizada supera screenshot puro

UIA expõe nomes, roles, padrões e propriedades; o cache permite recuperar informações em lote, evitando várias chamadas entre processos. O ganho potencial vem de substituir localização visual ambígua por identificação semântica e de reduzir dados irrelevantes. A Microsoft destaca que cache beneficia especialmente providers server-side, como WPF. [S04][S100]

Não é superioridade universal. UIA pode estar incompleta, custar mais que uma captura, omitir conteúdo desenhado ou devolver uma árvore enorme. Screenshot é necessário para gráficos, canvas, aparência, sobreposições e comprovação visual. Mesmo uma árvore correta pode apontar retângulo coberto. UFO2 e Agent S2 justificam uma combinação, não exclusão de modalidade. [S35][S36]

Síntese proposta: `id`, `role`, `name`, `enabled`, `offscreen`, `focused`, `bounds`, `patterns`, vínculo ao contêiner e geração. Valores sensíveis ficam redigidos. Ordenar por relevância, mas preservar mensagens de erro, avisos e contexto do destino. Truncamento precisa sinalizar `truncated:true` e permitir consulta paginada; nunca fingir que a lista parcial é o desktop inteiro.

#### A.3 Clique ou digitação falhou silenciosamente

Protocolo proposto:

1. Registrar qual pós-condição deve mudar antes do despacho.
2. Verificar sessão, janela, geração e alvo enabled/acionável.
3. Despachar uma operação sem efeitos adicionais implícitos.
4. Esperar evento ou condição até deadline; coletar evidência regional.
5. Distinguir: despacho rejeitado, efeito ainda pendente, divergência, estado desconhecido.
6. Se nada mudou: reobservar foco, overlay, coordenadas e estado do controle.
7. Repetir somente operação segura/idempotente e dentro do orçamento.
8. Se houver efeito externo possivelmente concluído, consultar resultado antes de repetir.
9. Sem confirmação independente, devolver `unknown`, nunca `verified`.

Exemplos: `set_checked(true)` é preferível a “clicar checkbox de novo”; `set_value` é diferente de anexar texto; repetir envio de formulário pode duplicar efeitos. `SendInput` retorna eventos inseridos e não diagnostica UIPI de forma inequívoca. [S02][S10]

#### A.4 Tarefas longas e contexto

Checkpoint proposto contém objetivo, restrições autorizadas, submeta atual, resultados confirmados, artefatos, ações irreversíveis já realizadas, hipóteses pendentes e próxima observação necessária. Não usar apenas histórico de screenshots nem apenas memória narrativa sem proveniência. OSWorld 2.0 relata falhas de retenção, estado oculto, verificação e informações que chegam durante a execução. [S41][S48][S52]

No CLI, `/model`, continuidade/resume e exportação são superfícies documentadas; disponibilidade concreta varia por versão instalada. Não inventar flags para compressão visual ou alterar governança para acelerar. Um checkpoint permite nova sessão com contexto essencial, mas a tela deve ser reobservada: checkpoint lógico não congela a aplicação. [S97]

### Eixo B — Movimento suave e digitação: biomecânica, não evasão

#### B.1 Minimum jerk e lei de potência

Flash–Hogan modela suavidade minimizando a integral do quadrado do jerk, a terceira derivada da posição. Para movimento ponto a ponto livre, duração fixa e velocidade/aceleração nulas nas extremidades, a trajetória é reta com perfil de velocidade em sino. O modelo foi estudado para braço humano; não é prova de que um cursor sintetizado seja indistinguível de uma pessoa. [S78]

Com `u=t/T`, a solução normalizada é:

`r(t) = r0 + (r1-r0) * (10u³ - 15u⁴ + 6u⁵)`.

A lei de potência 2/3 refere-se à relação entre velocidade angular e curvatura. Em forma equivalente, velocidade tangencial `v = K * κ^(-1/3)` e velocidade angular `ω = K * κ^(2/3)`. Aplicar expoente 2/3 diretamente à velocidade tangencial seria incorreto. Em linha reta `κ=0`, a forma precisa regularização ou tratamento separado; não serve como controlador universal para qualquer caminho. O artigo comparativo discute relação e limites entre hipóteses de suavidade e desenhos periódicos. [S79]

Para demonstrações, minimum jerk é simples e interpretável. Duração deve ser escolha de apresentação/acessibilidade; se Fitts for usado, coeficientes dependem do dispositivo e tarefa. Os números fixos atuais do bundle não são calibração de uma população. [L02]

#### B.2 Hesitação, overshoot e ruído

Micro-hesitação, overshoot de 2–4 px e tremor fractal são tópicos pesquisáveis, mas não foram encontrados dados que estabeleçam esses parâmetros como universais ou vantajosos para SWE-2. Não classificar jitter gaussiano independente como ruído fractal. Fractalidade exige estatística temporal/espectral e validação; uma aparência irregular não a demonstra.

Proposta para UX: trajetória suave sem erro intencional por padrão. Correção de alvo deve ser feedback real de posição/estado. Overshoot e ruído podem existir em **simulações offline de teste**, parametrizados e reproduzíveis, mas não junto a botões destrutivos ou para mascarar automação. Movimentos com via-points precisam checagem de continuidade; concatenar segmentos não garante mínimo global de jerk. [S78][S79]

#### B.3 Digramas, trigramas e teclado físico

O estudo de digitação consultado mostra relevância de pares de letras, alternância de mãos/dedos e rollover. Repetição de letra isoladamente não descreve toda velocidade. Distância QWERTY também é insuficiente: mesmo dedo, alternância, Shift, pontuação, habilidade e layout interferem. Dados desse estudo têm condições e licença próprias; não foram baixados nem ajustados nesta pesquisa. [S80]

O protótipo entrega apenas intervalos sintéticos, com lookup trigram → digram → caractere → fallback. Medianas e dispersão são entradas explícitas; os exemplos são fixtures artificiais, não estatística humana. Não inclui input do SO, erros propositais ou evasão. Para ABNT2, idiomas acentuados e IME, usar parâmetros/contextos próprios, sem reutilizar pressupostos QWERTY cegamente.

Erros com Backspace são úteis como caso de teste de editor: digitar fixture conhecida, corrigir, comparar texto final e seleção. Não são recomendação de produção. Pausas após pontuação podem tornar demonstrações legíveis, mas não medem leitura/compreensão; devem ser opcionais e configuradas para o público.

#### B.4 Turnstile, reCAPTCHA v3, DataDome e telemetria

Não há procedimento de contorno de detecção comportamental. Em aplicações próprias, usar mecanismos oficiais de teste: Turnstile documenta respostas controladas para testes; reCAPTCHA v3 alerta que scores de staging diferem de produção. DataDome deve ser integrado/testado com o proprietário conforme documentação oficial; esta pesquisa não verificou um modo genérico equivalente de chaves de teste. Ao surgir desafio em sistema alheio, pausar e solicitar intervenção. [S75][S76][S77]

Não remover marcas de input sintético nem adulterar telemetria do SO. “Natural” significa movimento legível e previsível para o usuário, não invisibilidade operacional. Nenhuma métrica de “indetectabilidade” foi medida ou proposta.

### Eixo C — Canais de input, sucesso e fronteiras de privilégio

**SendInput** coloca eventos de teclado/mouse num stream e serializa o lote sem intercalar outros eventos de input no meio daquele lote. Não aguarda renderização ou mudança semântica. Não reseta estado prévio de teclas, e respeita UIPI: aplicação de menor integridade não injeta livremente em maior integridade. [S02]

**PostMessage** insere mensagem na fila da thread da janela e retorna antes do processamento. **SendMessage** aguarda a window procedure; pode bloquear. Nenhum reproduz automaticamente todo o caminho de um dispositivo físico, estado de teclas, foco, composição de texto ou comportamento de todos os toolkits. São adequados apenas a controles/protocolos conhecidos e aplicações autorizadas. Ambos têm limites de UIPI e marshaling. [S07][S08]

**UIA patterns** operam comportamento: Invoke aciona, Value altera valor, SelectionItem seleciona, Toggle alterna, Scroll rola. O pattern precisa existir; role Button não prova suporte completo nem correto. A operação pode ser melhor semanticamente, mas não exercita os mesmos handlers de um clique físico. Teste E2E de interação deve escolher conscientemente o caminho. [S71][S103]

**Drivers virtuais:** VHF suporta fonte HID em driver kernel; Interception tem arquitetura/licença próprias; ViGEm emula gamepads e foi aposentado. Não são uma escada de fallback para “vencer bloqueios”. Janelas protegidas e secure desktop exigem interrupção e ação autorizada do operador. UIAccess é mecanismo restrito de acessibilidade, com requisitos de confiança; não passe universal de elevação e não recomendação para um agente genérico. [S09][S64][S65][S66][S101]

**Texto em bloco:** priorizar API semântica do app ou `ValuePattern` quando significado for “definir valor”. Clipboard é opção explícita em campo não sensível e com consentimento para alterar clipboard. Copiar/restaurar clipboard automaticamente pode ler informações pessoais e sobrescrever conteúdo criado pelo usuário no intervalo. Preferir não ler conteúdo prévio; se houver restauração autorizada, respeitar concorrência e todos os formatos, não apenas texto. `SetClipboardData` transfere ownership ao SO. [S89]

**Caractere a caractere:** necessário para handlers de teclado, máscara, autocomplete, atalhos e IME específicos. Entrada Unicode, scancodes e composição são mecanismos diferentes. Colagem pode disparar eventos diferentes de digitação. Sempre testar texto final no destino certo; nunca concluir pelo retorno do atalho Ctrl+V. [S02][S94]

### Eixo D — Renderização e ingestão

Renderização é como a aplicação produz pixels; UIA/DOM são semântica; captura é como o executor obtém pixels. São camadas distintas. Uma aplicação acelerada pode expor ótima acessibilidade; uma janela GDI pode ser totalmente owner-drawn.

| Família | Primeira opção de consumo | Complemento/fallback | Verificação necessária |
|---|---|---|---|
| GDI/Win32 legado | UIA/Win32 conforme controle | BitBlt/MSS; PrintWindow se app responder corretamente | HWND, client/screen coordinates, resultado não vazio. [S14][S88][S06] |
| DirectX/Direct3D | Semântica disponível + DXGI/WGC | ROI/OCR/grounder | Frames novos, device/access lost, formato/rotação. [S03][S24] |
| Vulkan | Semântica do toolkit + captura do compositor | DXGI/WGC no Windows se superfície capturável | Vulkan não implica API de screenshot universal; validar modo concreto. [S03] |
| WPF | UIA com cache/patterns | WGC/MSS para aparência | Provider, virtualização e propriedades cached/current. [S04] |
| WinUI 3 | AutomationPeers/UIA | Captura regional | Controle customizado implementa patterns corretos? [S103] |
| Flutter desktop | Semantics/ponte de acessibilidade | Pixels/OCR para lacunas | Inspecionar build e widgets efetivamente expostos. [S61] |
| Qt | QAccessible e adapter da plataforma | Pixels em widgets customizados | Eventos e providers corretamente implementados. [S96] |
| Chromium/Electron | DOM/AX/CDP autorizado | Screenshot/canvas e UIA do chrome da janela | Distinguir viewport CSS, device pixels e desktop. [S94][S33] |
| Gecko/Firefox | Playwright ou WebDriver/BiDi | AX e screenshot | Não pressupor compatibilidade CDP. [S12][S104] |
| WebKit | Playwright/automação suportada | AX e screenshot | WebKit de teste não é equivalente a toda distribuição Safari. [S104] |

**PrintWindow:** função síncrona que solicita desenho ao processo da janela. Pode bloquear e não promete reprodução de todo conteúdo GPU. `PW_CLIENTONLY` restringe área cliente; o valor informal `2/PW_RENDERFULLCONTENT` não deve virar garantia cross-version ou solução padrão sem contrato homologado. Não há suporte documentado, nas fontes consultadas, para capturar conteúdo protegido por essa via. [S06]

**DXGI:** obter frame e metadados; aplicar todos os move rects antes dos dirty rects; tratar cursor, rotação e perda de acesso. Movimentos usam pixels do estado anterior. Se buffers/frames forem perdidos, não aplicar delta sobre base arbitrária. A API pode coalescer regiões e incluir pixels que não mudaram, portanto dirty area não é sempre quantidade exata de mudança. [S03]

**WGC:** útil para captura de janela/monitor e callbacks; recursos recentes como dirty regions precisam checagem de contrato/build. Não declarar zero-copy se a cadeia inclui texture → staging → array CPU → RGB → PNG → transporte. Uma view NumPy sem cópia só elimina uma dessas fronteiras. [S23][S24][S63]

**OCR:** Tesseract permite adaptar segmentação para linha, palavra ou texto esparso; ROI, contraste e escala afetam resultado. PaddleOCR oferece modelos mobile/server, com custos diferentes. Não há garantia de OCR “ultrarrápido” em todo idioma/hardware. Medir detecção, reconhecimento, preprocessing e cold start separadamente; não usar OCR quando o texto correto já existe na árvore. [S86][S87]

**Transformações:** cada captura precisa carregar origem física, largura/altura, escala e rotação. Para imagem apenas redimensionada, sem rotação, `x_desktop = left + x_image * width_original / width_image`; analogamente para y. Coordenadas CSS do navegador exigem ainda transformação da viewport/janela; `devicePixelRatio` sozinho não inclui bordas nem posição no desktop. Grade/hints devem usar o mesmo espaço e declarar unidade. [L03][S33]

### Eixo E — Taxonomia completa de ações

A biblioteca deve separar **intenção semântica**, **gesto físico** e **política de apresentação**. A ação `set_value` não é sinônimo de `type_text`; `invoke` não é necessariamente teste de clique. Interfaces abaixo são proposta arquitetural, não funções presentes no bundle.

| Família | Ações propostas | Precondições | Pós-condição/cleanup |
|---|---|---|---|
| Observação | observe, inspect_target, wait_for | Escopo autorizado e geração conhecida | Snapshot com proveniência ou erro tipado |
| Janela/foco | focus_window, focus_element | PID/janela vinculados | Foreground/focused confirmados |
| Mouse básico | move, click, right_click, double_click | Alvo atual e acionável | Efeito semântico; botões liberados |
| Arrasto | drag_to, drag_select_text, drag_with_modifier | Origem/destino, threshold e foco conhecidos | Drop/seleção confirmados; botão e modificadores liberados |
| Rolagem | scroll_lines, scroll_pixels, scroll_to_element | Contêiner correto e unidade declarada | Âncora/posição mudou ou fim detectado |
| Tecla | key_press, chord, navigate_tab, access_key | Layout/foco/estado de modificadores | Controle esperado focado ou ação concluída |
| Texto | set_value, type_text, paste_text, select_text | Campo correto; política de dados | Valor/seleção previstos sem exposição de conteúdo sensível |
| Semântica | invoke, select_item, set_checked, expand, collapse | Pattern suportado e estado conhecido | Estado desejado confirmado |
| Híbrida | shift_click, ctrl_drag, modifier_scroll | App define significado e ownership de teclas | Verificar seleção/cópia/zoom e liberar somente inputs próprios |
| Sessão | cancel, release_owned_inputs, checkpoint | ID de sessão | Sem input preso; evidência preservada |

Duplo clique deve respeitar intervalo configurado do sistema, obtido por GetDoubleClickTime, além da estabilidade espacial do alvo. Intervalo “humanizado” aleatório fora desse limite pode virar dois cliques simples. [S102]

“Drag com inércia” é comportamento da aplicação, não propriedade universal do mouse. Uma trajetória suave não cria momentum onde o app não o implementa. Para seleção de texto, usar semântica/teclado quando isso corresponde ao teste; jitter é caso adversarial offline, não melhoria automática. Roda pode trabalhar em detents/linhas; eventos browser podem usar pixels. A conversão deve ser explícita no adapter. [S94][L04]

Atalhos globais podem afetar outra aplicação. Tab/Shift+Tab exigem verificar foco após transição e detectar ciclos, não emitir dezenas de Tabs cegamente. Alt pode ativar menu ou combinar com layout/AltGr; Shift/Ctrl em drag alteram semântica conforme aplicação. Um executor serial deve possuir seus modificadores e liberá-los em finally, sem soltar teclas físicas do usuário indiscriminadamente. [S02][S20]

### Eixo F — Máquinas de estados e exploração controlada

#### F.1 Uso comum/determinístico

```text
OBSERVE → VALIDATE_TARGET → AUTHORIZE → EXECUTE → WAIT_EFFECT → VERIFY
   ↑             ↓              ↓            ↓                ↓
   └──── REOBSERVE           HUMAN_REVIEW   UNKNOWN         CHECKPOINT → NEXT/DONE
                  falha persistente → STOP_WITH_EVIDENCE
```

A sequência proposta minimiza ações redundantes usando precondições e pós-condições. “Menor caminho cognitivo” não significa omitir verificação: verificar localmente uma propriedade pode custar menos que recuperar um fluxo errado. Batch só atravessa estados cuja validade possa ser checada pelo executor; navegação, abertura de modal e efeitos externos são barreiras naturais. [S10][S35][S40]

Pseudocódigo de controle, **não executor operacional**:

```text
para cada submeta autorizada:
    observar estado com geração
    se pós-condição já satisfeita: registrar evidência; continuar
    resolver alvo e precondições
    se alvo ambíguo ou protegido: solicitar intervenção
    executar uma ação permitida
    aguardar condição com deadline
    se confirmada: checkpoint
    senão:
        reobservar e classificar falha
        se resultado externo desconhecido: reconciliar antes de repetir
        se operação segura e orçamento disponível: tentar recuperação limitada
        senão: parar com evidência
```

#### F.2 Exploração, fuzzing e bug hunting autorizados

Objetivo diferente: encontrar transições inválidas, race conditions, problemas de foco, renderização ou acessibilidade. Imprevisível para o software sob teste, **reproduzível para o investigador**. Seed, versão da aplicação, estado inicial e sequência precisam ser registrados. Não executar exploração contra desktop pessoal ou serviços de terceiros. [S74]

```text
VERIFY_SCOPE → RESTORE_FIXTURE → GENERATE_SEQUENCE → EXECUTE_BOUNDED
                     ↑                                   ↓
                  REPLAY ← MINIMIZE_FAILURE ← CHECK_INVARIANTS
                     └────────── SAVE_REPRODUCER / NEXT_CASE
```

Famílias de testes propostas:

- Campos: vazio, limites definidos pelo contrato, Unicode, texto bidirecional, composição IME, colagem versus teclas. Sem payloads de exploração contra alvos reais.
- Ordem: voltar antes de concluir, modal interrompida, mudança de painel, foco alternado e elemento removido durante ação.
- Concorrência: ações próximas em fixture própria, com limites de taxa e quantidade; observar duplicação, eventos fora de ordem e estado inconsistente.
- Renderização: resize, DPI, tema, escala, janela parcialmente coberta e dispositivo de captura reinicializado.
- Acessibilidade: role/name/pattern divergentes, nome muito longo, árvore parcial e item virtualizado.
- Liveness: heartbeat de aplicativo de teste, thread UI responsiva, ausência de crash e invariantes de estado. Tela igual pode ser estado legítimo; não classificá-la sozinha como travamento.

Oráculo primário: estado/artefato da aplicação controlada; oráculos auxiliares: eventos, UIA e imagem. Salvar sequência mínima que reproduz a falha. Falha de render não é automaticamente vulnerabilidade de segurança; classificá-la com evidência e impacto. Reset somente de fixtures previamente autorizadas. [S38][S39][S74]

**Limite de paralelismo:** leituras independentes podem ocorrer em paralelo; mouse/teclado do mesmo desktop têm um único dono. VMs/sessões realmente isoladas permitem testes paralelos; janelas separadas não isolam foco, clipboard nem atalhos globais. [S35][L04][L05]

## 4. Comparativos e benchmarks

### 4.1 Mecanismos de input

**ND** = não foi encontrado benchmark comparável nas fontes consultadas e não houve medição local. “Métrica de homologação” indica o que medir, não um resultado. Velocidade de API, consumo pelo aplicativo e conclusão visual são métricas diferentes.

| Mecanismo | Caminho/semântica | Benchmark disponível | Métrica de homologação | Uso adequado e trade-off |
|---|---|---|---|---|
| SendInput C/C++ | Stream de eventos serializado | ND; API não dá SLA temporal | Submit p50/p95, eventos inseridos/solicitados, tempo até efeito | Input global autorizado; foco e UIPI. [S02] |
| SendInput via ctypes/windows-rs | Mesmo mecanismo com FFI/binding | ND | Separar overhead de binding, syscall e app | Menor wrapper não implica maior sucesso. [S02][S32][S82] |
| pynput | Controller multiplataforma usado localmente | ND; delays locais são parâmetros, não benchmark | Cold start, dispatch e efeito | Mantém compatibilidade; limitações de teclas/eventos documentadas. [S20][L04][L05] |
| PyAutoGUI | Abstração alto nível e fail-safe | ND | Custo de chamadas, pausas e localização | Prototipagem; não desativar proteção para ganhar benchmark. [S13] |
| Enigo | Abstração Rust de input | ND | Backend/OS, dispatch e efeito | Portabilidade; sem garantia de invisibilidade. [S27] |
| PostMessage | Enfileira mensagem da janela | ND | Enqueue separado de processamento confirmado | Controles/protocolos conhecidos; sucesso não prova consumo. [S07] |
| SendMessage | Chamada síncrona de window procedure | ND | Tempo bloqueado e deadline de teste | Pode bloquear; usar estratégia limitada em apps próprios. [S08] |
| UIA Invoke/Value/Selection | Operação semântica do provider | ND | RPC, mudança de propriedade e efeito final | Mais direto; não cobre todo caminho físico. [S71][S103] |
| pywinauto/FlaUI/uiautomation-rs | Wrappers Win32/UIA | ND | Separar descoberta, cache, pattern e wait | Comparar mesmo provider/consulta; linguagem não isola variáveis. [S14][S21][S28] |
| Clipboard + hotkey | Transferência de texto em bloco | ND | Escrita, recebimento, valor final e conflitos | Consentimento, formatos, concorrência e exposição de dados. [S89] |
| Texto Unicode/teclas/scancodes | Caractere, tecla lógica e tecla física distintos | ND | Texto final/IME/layout e latência | Testar acentos, composição e atalhos, não só ASCII. [S02][S94] |
| CDP/Playwright | Input/DOM no browser autorizado | ND comparável a desktop | Round-trip, actionability e efeito | Bom para browser; não controla secure desktop. [S10][S94] |
| Selenium/BiDi/thirtyfour | Protocolo WebDriver/browser | ND | Sessão, comando, evento e assertion | Cross-browser; separar warm/cold e versão do driver. [S12][S30] |
| Interception | Camada de driver | ND | Apenas laboratório de compatibilidade | Custo de segurança/licença não justificado para rotina. [S64] |
| VHF/Virtual HID | Driver fonte HID | ND | Driver, entrega e aplicação, em VM/lab autorizado | Produto especializado; sem promessa de bypass UAC. [S66] |
| ViGEm | Gamepad virtual Xbox 360/DS4 | Não aplicável a teclado/mouse | Compatibilidade de gamepad legado | Aposentado; excluir da atualização normal. [S65][S101] |
| XTEST/xdotool | Input X11 | ND | Comando e efeito sob servidor X definido | Não extrapolar para Wayland. [S17] |
| libei/EIS | Emulação autorizada no compositor | ND | Handshake, autorização e efeito | Controle de acesso permanece no servidor. [S60] |
| uinput/libevdev | Dispositivo virtual Linux | ND | Entrega do dispositivo e efeito no app | Uso especializado/isolado; não é binding Win32. [S70] |

Detours e Frida não entram como alternativas equivalentes de input: são instrumentação. Medir um hook que modifica diretamente estado do programa contra um clique E2E mudaria o objeto medido e invalidaria a comparação. [S67][S68]

### 4.2 Captura e renderização

| Mecanismo | Saída e cobertura | Benchmark disponível | Métrica de homologação | Trade-off |
|---|---|---|---|---|
| GDI/BitBlt | Bitmap/DC de superfície capturável | ND direto | Capture+readback por resolução | Simples, mas cópia CPU e comportamento de superfícies variam. [S88] |
| MSS | Pixels/PNG conforme uso | 75,87 FPS em comparação publicada pelo DXcam | Mesmo workload, versão e modo de retorno | Baseline portátil; número não inclui pipeline atual do agente. [S23][S84] |
| PrintWindow | Desenho solicitado à aplicação | ND | Tempo, validade/atualidade da imagem, timeout | Síncrono; pode não renderizar conteúdo desejado. [S06] |
| DXGI Desktop Duplication | Texture + metadados move/dirty/cursor | ND universal; wrappers têm comparação abaixo | Acquire/copy/map/idade do frame | Incremental, exige reconstrução e recovery corretos. [S03] |
| DXcam | Array/view e ring buffer DXGI/WinRT | 239,19 FPS no teste dos autores | Frames únicos/s, idade p95, cópias | View pode ser sobrescrita; não é zero-copy integral. [S23] |
| D3DShot | Captura DXGI em Python | 118,36 FPS no mesmo comparativo | Mesmo retorno/versão/estado visual | Referência histórica, não líder por autodescrição. [S23][S85] |
| WGC | Frame por janela/monitor | ND comparável | Frame arrival, resize, disponibilidade por build | Evita depender do WM_PRINT; não promete conteúdo protegido. [S24][S63] |
| windows-capture | Wrapper Rust/Python WGC/DXGI | ND comparável na fonte consultada | Capture/readback/conversão por backend | “Fastest” no marketing não substitui medição. [S24] |
| xcap | Captura monitor/janela cross-platform | ND | Backend/OS/ROI e frames válidos | Funcionalidades não uniformes entre plataformas. [S25] |
| scap | Frameworks nativos por SO | ND | Captura/permissões/formato | Beta e plataformas diferentes. [S26] |
| UIA tree/cache | Semântica, não pixels | ND temporal comparável | Número de RPCs, tempo e cobertura de alvos | Pequena saída possível; provider/árvore podem ser caros. [S04][S100] |
| DOM/AX/CDP | Estrutura browser e screenshot quando solicitado | ND comparável | Snapshot, tamanho e precisão de grounding | Dados CSS não são desktop pixels; canvas ainda precisa visão. [S11][S33][S94] |
| OmniParser | Detecção/captioning de elementos | Sem benchmark de latência comparável usado aqui | Grounding correto + tempo/VRAM por resolução | Inferência local adicionada ao loop. [S22] |
| Tesseract | Texto e caixas OCR | ND comparável entre os mecanismos desta tabela | ROI, idioma, segmentação, latência e erro | Ajustar preprocessing; não obtém estado semântico. [S87] |
| PaddleOCR | Detecção e reconhecimento mobile/server | Fonte publica tabelas próprias, não comparação homogênea com Tesseract/UIA | End-to-end com mesma imagem/modelo/hardware | I/O e dicionário influenciam; não usar só tempo do recognizer. [S86] |
| NVENC | Stream H.264/HEVC/AV1 conforme hardware | ND comum à captura desktop | Encode/decode/rede/qualidade de texto | Throughput e baixa latência têm compromisso com qualidade/bitrate. [S91] |
| PipeWire/DMA-BUF | Buffer compartilhado Linux | ND | Negociação, cópia fallback e idade de frame | Zero-copy depende de formatos/modifiers compatíveis. [S92] |
| ScreenCaptureKit | CMSampleBuffer e metadados | ND comparável | Frames/idade, permissões e transformação | Alternativa macOS; não comparar com Windows sem separar plataforma. [S93] |

Frameworks GDI/DirectX/Vulkan/WPF/WinUI/Flutter/Electron/Gecko/WebKit não recebem números independentes artificiais: são workloads/renderers, não APIs intercambiáveis de captura. A matriz do eixo D indica o caminho a homologar para cada um.

### 4.3 Benchmarks publicados

| Fonte/versionamento | Resultado relatado | Protocolo/contexto observado | O que não conclui |
|---|---|---|---|
| DXcam README | DXcam 239,19 FPS; MSS 75,87; D3DShot 118,36 | Cinco runs; Ryzen 5900X + RTX 3090; saída de 240 FPS e conteúdo animado; autores dizem contar frames novos | Não mede tokens, PNG do bundle, mouse→paint ou SWE-2. Versões exatas da comparação não fixadas no trecho. [S23] |
| OSWorld-Human v2 | Melhores agentes ainda usam 2,7–4,3× mais passos que necessários | Estudo de 16 agentes; análise temporal sobre OSWorld e trajetórias humanas | Não é speedup garantido de um patch local. [S40] |
| OSWorld 2.0 v2 | 108 workflows; melhor configuração relatada 20,6% conclusão binária e 54,8% parcial | Claude Opus 4.8, esforço máximo, chamadas em lote, limite de 500 passos | Não é resultado SWE-2, ranking atual universal ou comparável a OSWorld original. [S41] |
| GUIPruner v1 | Qwen2-VL-2B: 3,4× redução de FLOPs, 3,3× aceleração de encoding; acima de 94% do desempenho original | Claim do abstract; poda/resolução do modelo estudado | Não são 94% de sucesso absoluto nem 3,3× ponta a ponta. Hardware não detalhado no abstract usado. [S49] |
| ST-Lite v3 | Até 2,35× decoding com compressão cinco vezes | Sete benchmarks, dois backbones; budget de 20% na comparação principal | Não equivale a economizar 80% de todo contexto ou RAM do agente. [S50] |
| Speculative Macro Commit v1 | Telecom: 18,59% menor latência que execução sequencial; AppWorld: 44,9% | Qwen3.5-27B INT4 actor e Qwen3.5-4B drafter; AppWorld teve pequena queda na conclusão | Não comparar como ganho GUI Windows; isolamento e semântica de commit são condições essenciais. [S56] |
| SWE-2 anúncio | Medium: 58% menos turnos e 81% menor custo médio que SWE-1.7 | FrontierCode 1.1 Main, avaliação da Cognition | Não demonstra vantagem visual nem melhoria desta extensão. [S01] |
| SWE-2 rollout serving | Prefill agrupado: 10–20% melhoria de TPM/GPU e TPS/request; draft atualizado: 15% maior comprimento aceito | Infraestrutura de rollouts de RL descrita pelo fornecedor; TTFT aumenta | Não são knobs CLI nem promessa de menor latência interativa. [S01] |

FPS é throughput; não converter `1/FPS` em latência de ação sem conhecer filas, sincronização e pipeline. Recontar um mesmo buffer em loop pode produzir FPS enormes sem uma única tela nova. O próprio DXcam alerta sobre esse problema. [S23]

Uma otimização parcial obedece ao limite de Amdahl: se a fração `f` do tempo for acelerada por `s`, o speedup ideal é `1 / ((1-f) + f/s)`, antes de overhead adicional. Se inferência/verificação dominam, otimizar somente captura não produz aumento exponencial. A fórmula é derivação analítica, não medição local.

### 4.4 Protocolo local proposto

**Não executado nesta pesquisa.** A primeira implementação deverá medir em aplicação/VM de teste, nunca no desktop pessoal por conveniência.

Modelo de tempo por etapa:

`T_etapa = T_startup + T_observe + T_encode + T_transport + T_infer + T_dispatch + T_effect_wait + T_verify`.

Se etapas se sobrepõem, registrar intervalos e caminho crítico; somar tempos sobrepostos inflaria o total. Registrar monotonic clock e tempo total de parede. `time.sleep` pode durar mais que solicitado; frequência pretendida de trajetória não é frequência garantida. [S90]

Plano de medição previamente fixado:

1. Workloads: formulário Win32, lista virtualizada WPF/WinUI, página Chromium, modal Electron, canvas acelerado e editor Unicode/IME. Usar fixtures sintéticas próprias; fixar hash/versão.
2. Estratos: cold/warm separados; display 100%/150% DPI; janela/monitor/região; conteúdo estático/animado; origem negativa em segundo monitor. Registrar CPU/GPU/driver/build Windows, resolução, refresh e versões exatas.
3. Comparar cada candidato com baseline no mesmo estrato e mesma sequência, alternando ordem para reduzir viés térmico/caching. Como protocolo exploratório proposto, usar 30 pares por estrato e não interromper ao obter resultado favorável. Não tratar esse tamanho como garantia de poder estatístico.
4. Latência: reportar p50/p95 e amostras brutas por fronteira. Throughput: frames distintos/s e idade do frame no momento da decisão. Registrar timeout, stale frame, erro e resultado desconhecido, sem removê-los do denominador de sucesso.
5. Correção: task success sobre todas as tentativas; false-success separado; ações redundantes; recuperações; custo por tarefa concluída e custo de falhas. Tempo de sucesso condicionado a sucesso deve vir acompanhado de taxa de sucesso.
6. Tokens: usar contagem real retornada pelo serviço quando disponível; registrar modelo e cache. Se não existir telemetria, reportar bytes/nós/imagens como proxies, **não tokens estimados como fatos**.
7. Held-out: separar tarefas/layouts antes de ajustes. Não escolher novos thresholds depois de observar held-out. Avaliador consulta artefato/estado da fixture, não a autoafirmação do agente.
8. Critério de decisão: melhoria de latência/custo com correção preservada nos casos de segurança e incerteza estatística explicitada. Não lançar driver, modelo local ou serviço persistente somente por um microbenchmark favorável.
9. Guardar dados brutos sem texto sensível e metadados de execução. Congelar captura de resultados antes de gerar tabelas; rerenderizar tabelas não deve rerodar experimento.

Sub-milissegundo só pode ser investigado para uma fronteira estreita, por exemplo custo de enqueue, em configuração documentada. Feedback visual depende também da aplicação, compositor, refresh, captura, transporte e modelo. Nenhuma API aqui garante todo esse caminho abaixo de 1 ms.

## 5. Protótipos matemáticos offline

Arquivo complementar: [`swe2_action_models.py`](swe2_action_models.py). Usa somente biblioteca padrão. **Não captura tela, não lê teclado, não envia input, não acessa rede e não executa evasão.** Os geradores retornam dados para estudo/UX/testes sintéticos. Não constituem validação de naturalidade humana.

### 5.1 Minimum jerk

Derivação: minimizar `J = ∫₀ᵀ ||r'''(t)||² dt`, com posição, velocidade e aceleração fixadas nas extremidades. Euler–Lagrange para essa função de terceira derivada produz `r⁽⁶⁾=0`; logo, uma solução polinomial de grau cinco. Impor `s(0)=0`, `s(1)=1`, `s'(0)=s'(1)=s''(0)=s''(1)=0` resulta em `s(u)=10u³−15u⁴+6u⁵`. A convexidade quadrática do funcional com essas condições sustenta o mínimo. Esta derivação não depende de afirmar conhecimento interno do SWE-2. [S78]

`ds/du=30u²(1−u)² ≥ 0` no intervalo: progressão monotônica. O endpoint é exato no gerador; não existe overshoot. Para percurso com obstáculo/via-point, o problema e suas restrições mudam.

Implementação incluída no arquivo complementar:

```python
import math


def minimum_jerk(start, end, duration, samples):
    if len(start) != 2 or len(end) != 2:
        raise ValueError("two-dimensional endpoints required")
    if not all(math.isfinite(v) for v in (*start, *end, duration)):
        raise ValueError("finite values required")
    if duration <= 0 or isinstance(samples, bool) or not isinstance(samples, int) or not 2 <= samples <= 10000:
        raise ValueError("positive duration and 2..10000 samples required")
    points = []
    for i in range(samples):
        u = i / (samples - 1)
        s = u ** 3 * (10 + u * (-15 + 6 * u))
        points.append((u * duration, start[0] + (end[0] - start[0]) * s, start[1] + (end[1] - start[1]) * s))
    points[0] = (0.0, *start)
    points[-1] = (duration, *end)
    return points
```

Exemplo sintético: `(0,0) → (100,-50)`, `T=1`, 101 amostras. A metade do percurso ocorre em `(0.5,50,-25)`. Os números são uma fixture matemática, não biomecânica calibrada ou benchmark de agendamento.

Arredondar para pixels só na fronteira de apresentação; manter floats no gerador evita quantização antecipada. Não derivar suavidade contínua a partir de diferenças finitas de pontos já arredondados. Um futuro player deve usar deadlines absolutos e cancelamento, não acumular erro de `sleep(dt)`; esta pesquisa não implementa esse player.

### 5.2 Digramas e trigramas

Modelo proposto para **simulação offline**: a mediana depende do contexto textual mais específico disponível. Para mediana `m` e dispersão `σ`, amostrar `exp(log(m)+σZ)`, `Z~N(0,1)`, e limitar ao intervalo configurado. Após clipping, a distribuição não é mais lognormal pura; não usá-la como inferência estatística sem considerar censura. O modelo é uma heurística demonstrativa inspirada na relevância empírica de pares, não um ajuste do dataset de digitação. [S80]

```python
import math
import random


def typing_intervals(text, medians, fallback, sigma, bounds, seed):
    low, high = bounds
    if not all(math.isfinite(v) for v in (fallback, sigma, low, high)) or not 0 < low <= fallback <= high or sigma < 0:
        raise ValueError("invalid timing parameters")
    if any(not isinstance(k, str) or not 1 <= len(k) <= 3 or not math.isfinite(v) or not low <= v <= high for k, v in medians.items()):
        raise ValueError("invalid context medians")
    rng = random.Random(seed)
    intervals = []
    for i in range(len(text)):
        contexts = (text[max(0, i - n + 1):i + 1] for n in (3, 2, 1))
        median = next((medians[k] for k in contexts if k in medians), fallback)
        delay = rng.lognormvariate(math.log(median), sigma)
        intervals.append(min(high, max(low, delay)))
    return intervals
```

Cada posição recebe um intervalo sintético associado ao caractere, incluindo espera inicial. Não é scheduler de keydown/keyup nem captura de biometria. Para estudar rollover, seria necessário outro modelo de tempos de pressionamento/liberação e dados consentidos; o gerador atual não o simula. Trigramas são contextos de caracteres Python, não grafemas compostos nem posição física de teclas.

A matriz `medians` pode ser estimada futuramente com dados consentidos, separando layout, dispositivo e população. Reservar participantes/textos de validação; não ajustar no mesmo conjunto usado para alegar realismo. Não há taxas recomendadas de erros intencionais ou pausas para passar por humano.

### 5.3 Verificação reproduzível dos protótipos

Da raiz do repositório:

```text
python .devin/research/swe2_action_models.py
python .devin/research/verify_swe2_research.py
```

O primeiro comando verifica endpoints, ponto médio, monotonicidade, trajetória sem deslocamento, seed determinística, limites, prioridade de trigramas/digramas, texto vazio e rejeição de parâmetros inválidos selecionados. O segundo também verifica a matriz e estrutura do relatório. Não é teste exaustivo de tipos arbitrários nem benchmark do SO.

Separação de evidência: os asserts provam propriedades das fixtures offline. Não provam que mouse físico seguirá o mesmo tempo, que digitação será natural ou que SWE-2 ficará mais rápido. Validação empírica permanece parte do plano de atualização, não um resultado já obtido.

## 6. Plano incremental de arquitetura

**Objetivo:** ações corretas, verificáveis e recuperáveis com menor overhead, preservando a interface dos scripts existentes.

**Arquitetura:** Python continua coordenando comandos JSON. Observação, alvo, transporte de input e verificação recebem contratos explícitos. UIA e MSS são a base inicial; CDP e captura GPU entram como adapters opcionais, somente quando evidência de workload justificar.

**Não executado:** esta seção é o plano solicitado. Nenhuma etapa operacional foi implementada. Os arquivos de pesquisa são anexos duráveis; os protótipos offline não devem ser importados automaticamente pela extensão.

**Restrições globais:** não alterar comentários existentes sem solicitação; preservar testes; não reduzir políticas de segurança; não instalar drivers no fluxo padrão; não alterar globalmente permissões; não armazenar conteúdo sensível; não usar clipboard sem consentimento; não repetir efeito externo desconhecido; não confundir sessão persistente com sandbox; manter saída JSON única para cada chamada CLI.

### 6.1 Contratos

Contrato de observação proposto:

```json
{
  "schema_version": 2,
  "ok": true,
  "session_id": "test-session",
  "observation_id": "obs-17",
  "generation": 17,
  "window": {"pid": 1234, "hwnd": "0x100", "foreground": true},
  "capture": {
    "origin_px": [-1920, 0],
    "size_px": [1920, 1080],
    "image_size_px": [960, 540],
    "rotation_deg": 0,
    "captured_monotonic_ns": 1000000000,
    "uia_monotonic_ns": 1001000000
  },
  "elements": [{
    "id": "element-5",
    "hint": "as",
    "role": "Button",
    "name": "Salvar",
    "bounds_px": [-1600, 200, 100, 40],
    "enabled": true,
    "offscreen": false,
    "focused": false,
    "patterns": ["Invoke"]
  }],
  "truncated": false,
  "fallback": null
}
```

Valores são fictícios. `bounds_px` significa `[left,top,width,height]`. Timestamps monotônicos só se comparam dentro da mesma instância de runtime; reinício muda identidade da sessão. `hwnd` sozinho pode ser reutilizado pelo SO; associar PID, geração de processo e revalidação. `element.id` é chave opaca de sessão, não índice espacial permanente. Diferença de timestamps mede skew observado, não atomicidade.

Contrato de ação/resultado proposto:

```json
{
  "action_id": "act-18",
  "session_id": "test-session",
  "observation_id": "obs-17",
  "kind": "invoke",
  "target_id": "element-5",
  "expected": {"kind": "element_present", "role": "Text", "name": "Salvo"},
  "presentation": "fast"
}
```

```json
{
  "ok": true,
  "action_id": "act-18",
  "status": "verified",
  "dispatch": {"accepted": true, "backend": "uia"},
  "effect": {"verified": true, "observation_id": "obs-18"},
  "timings_ms": {"dispatch": null, "wait_effect": null, "total": null}
}
```

O exemplo usa `null` para tempos não medidos; implementações devem preencher com relógio real quando houver medição. Não emitir zeros como latência real desconhecida. Estados finais: `verified`, `dispatched`, `rejected`, `timeout`, `unknown`, `cancelled`. `ok` preserva compatibilidade de execução do comando, enquanto `status` declara evidência; consumidor legado não pode interpretar `ok` como task success. Submissão de alto impacto exige autorização separada, não um booleano produzido pelo modelo.

Interfaces conceituais propostas:

```text
observe(scope, session_id) -> Observation
resolve_target(observation_id, target_id) -> Target | StaleTarget
plan_action(action, observation) -> ValidatedPlan | Rejection
execute(plan) -> DispatchResult
verify(expected, deadline, observation_source) -> VerificationResult
cancel(session_id) -> CleanupResult
```

`Observation` é o snapshot acima. `Target` contém vínculo de janela/elemento, geração, bounds e capacidades. `ValidatedPlan` contém ação permitida e alvo revalidado; nunca código arbitrário. `DispatchResult` contém backend, aceitação e erro nativo redigido. `VerificationResult` contém estado verificado/unknown e evidência posterior. `CleanupResult` informa liberação somente dos inputs da sessão. `StaleTarget` e `Rejection` são erros tipados sem despacho.

### 6.2 Etapas e critérios de aceite

Cada etapa é uma entrega vertical demonstrável. Os caminhos de testes abaixo são **propostos** e serão criados durante implementação; comandos não foram executados nesta pesquisa. Ciclo obrigatório em cada etapa: teste inicialmente falha pelo comportamento ausente → mudança mínima → teste passa → revisão. Não se promete commit/push automático.

#### Etapa 1 — Clique por hint chega ao alvo correto ou é rejeitado

- [ ] Modificar `extensions/computer-use/cu_hints.py` e `screenshot.py`: sidecar por sessão, geração, vínculo à janela, escrita atômica, invalidação em fallback e metadados de origem.
- [ ] Modificar `mouse.py`: exigir observação válida para hint, revalidar alvo e declarar motivo de rejeição.
- [ ] Manter coordenada explícita compatível; corrigir rótulos da grade para espaço físico global ou declarar claramente conversão local.
- [ ] Criar teste durável `tests/test_cu_observation_contract.py` com stubs de captura/UIA/foreground e fake clock.

Casos exatos: origem `(-1920,0)`; região `(100,200)`; imagem reduzida pela metade; hint de sessão diferente; mudança de HWND/PID; fallback após captura válida; dois snapshots simultâneos; clique stale deve emitir **zero** chamadas ao controller. Escrita interrompida não deixa JSON parcial. Janela inválida não amplia consulta para desktop inteiro silenciosamente.

Gate futuro: `python -m pytest tests/test_cu_observation_contract.py -q`. Aceite: todas as transformações esperadas coincidem; alvo inválido não é despachado; contrato antigo de saída continua parseável.

#### Etapa 2 — Resultado diferencia despacho de efeito

- [ ] Criar `extensions/computer-use/cu_actions.py` como dono de validação/resultado/cleanup; integrar `mouse.py` e `type_text.py`.
- [ ] Implementar verificação de pós-condição e reconciliação de resultado desconhecido, sem retries cegos.
- [ ] Gerenciar botões/modificadores da sessão com finally; preservar estado físico não pertencente à sessão.
- [ ] Criar `tests/test_cu_action_results.py` com controller fake, fonte de observação fake e relógio fake.

Casos: dispatch aceito sem mudança → não verified; efeito atrasado dentro do deadline → verified; deadline expirado → timeout/unknown conforme evidência; erro depois de keydown → liberação própria; foco muda antes de texto → rejeição; envio possivelmente concluído não é repetido.

Gate futuro: `python -m pytest tests/test_cu_action_results.py -q`. Aceite: nenhum falso `verified` nas fixtures; resultado inclui backend e timings reais separados de duração planejada.

#### Etapa 3 — Campo e botão são operados semanticamente quando apropriado

- [ ] Ampliar `cu_hints.py` com `FindAllBuildCache` e propriedades selecionadas, consultando apenas janela/subárvore relevante.
- [ ] Ampliar `cu_actions.py` para Invoke/Value/Selection/Scroll e fallback explícito ao controller existente.
- [ ] Criar `tests/test_cu_uia_actions.py`: provider fake registra chamadas/propriedades e simula ausência de pattern, elemento removido, read-only e timeout.

Casos: pattern ausente não gera sucesso; Value em read-only rejeita; cache invalida por geração; nome duplicado exige vínculo estrutural; corte de saída sinaliza truncamento; provider lento não bloqueia indefinidamente. Comparar número de round-trips com baseline para mesma consulta, sem reduzir informação necessária.

Gate futuro: `python -m pytest tests/test_cu_uia_actions.py -q`. Aceite: semântica correta e correção preservada; depois, benchmark do protocolo 4.4 decide benefício temporal.

#### Etapa 4 — Browser autorizado usa DOM/AX sem perder cobertura visual

- [ ] Criar adapter opcional `extensions/computer-use/cu_browser.py`; não habilitar remote debugging na sessão pessoal automaticamente.
- [ ] Integrar roteamento em `cu_actions.py`: apenas browser de teste explicitamente vinculado; usar locators com actionability, CDP quando necessário e screenshots de canvas.
- [ ] Criar `tests/test_cu_browser_contract.py` com cliente browser fake; fixture E2E posterior usa página própria.

Casos: origem browser não autorizada rejeita; alvo encoberto aguarda/falha; iframe/shadow context não é confundido; CSS/desktop pixels não se misturam; canvas sem DOM usa fallback; WebKit/Gecko não recebem chamadas CDP Chromium.

Gate futuro: `python -m pytest tests/test_cu_browser_contract.py -q`. Aceite: roteamento e contratos passam; dependência/browser só são adicionados após aprovação de ambiente e revisão de versão.

#### Etapa 5 — Sessão persistente reduz startup sem vazar estado

- [ ] Executar apenas se medições mostrarem custo relevante de inicialização/COM/captura repetidos.
- [ ] Criar `extensions/computer-use/cu_session.py`: worker local por sessão, IPC local com ACL do usuário e um executor de input; frontends CLI preservam JSON único.
- [ ] Isolar UIA que possa travar em processo reciclável, não acumular threads daemon; cleanup de recursos por sessão.
- [ ] Criar `tests/test_cu_session_isolation.py` com workers fake e simulação de falha/reinício.

Casos: sessão A não usa hints B; reinício invalida IDs/relógio; provider pendurado é encerrado/recriado pelo supervisor de laboratório; usuário cancela durante gesto; fila não dispara ações após cancelamento; nenhuma porta de rede pública é criada.

Gate futuro: `python -m pytest tests/test_cu_session_isolation.py -q`. Aceite: isolamento lógico e cleanup; persistência não é apresentada como sandbox de segurança.

#### Etapa 6 — Captura GPU reduz custo mantendo imagem correta

- [ ] Executar apenas se captura/encoding dominarem workload medido.
- [ ] Criar `extensions/computer-use/cu_capture.py` com interface MSS existente e adapter opcional DXcam inicialmente; manter WGC/windows-capture como alternativa homologada, não dependências simultâneas obrigatórias.
- [ ] Integrar `screenshot.py` com origem/rotação/timestamps, ROI e saída compatível. Views só atravessam fronteiras com ownership explícito.
- [ ] Criar `tests/test_cu_capture_frames.py` com frames sintéticos, move/dirty rects, resize, perdas e rotação.

Casos: movimentos sobrepostos usam base anterior; dirty aplicado depois; frame perdido gera resync; access lost recria backend; pointer-only update considerado; buffer não é lido após sobrescrita; captura sem nova tela não vira frame novo.

Gate futuro: `python -m pytest tests/test_cu_capture_frames.py -q`. Aceite: reconstrução byte-exata das fixtures e benchmark pareado válido. Migrar para Rust/C++ somente se profiling apontar gargalo não resolvido pelo adapter Python.

#### Etapa 7 — Demonstração suave é reproduzível e cancelável

- [ ] Modificar `cu_motion.py`: gerador minimum-jerk como opção de apresentação, seed para testes e duração planejada distinta de tempo real.
- [ ] Manter fast como caminho determinístico. Não introduzir erros intencionais no texto real, tremor para evasão ou overshoot perto de ações sensíveis.
- [ ] Criar `tests/test_cu_motion_profiles.py` reutilizando propriedades matemáticas, não importando automaticamente o anexo de pesquisa.

Casos: zero distância; coordenadas negativas; endpoints; monotonicidade temporal; ausência de overshoot; cancelamento libera inputs próprios; duplo clique respeita configuração; repetição com seed tem mesmo plano; agendamento usa deadline e não acumula sleeps.

Gate futuro: `python -m pytest tests/test_cu_motion_profiles.py -q`. Aceite: UX e segurança previsíveis; “naturalidade humana” só pode ser alegada após estudo específico, não por esses asserts.

#### Etapa 8 — Teste adversarial reproduzível e validação held-out

- [ ] Criar fixtures próprias e `tests/validation/test_cu_workflows.py`, `tests/held-out/test_cu_workflows.py`, `tests/test_cu_stateful.py`.
- [ ] Adicionar geração limitada de sequências com seed e registro mínimo de reprodução, sem acesso ao desktop pessoal.
- [ ] Executar protocolo 4.4, congelar dados, gerar relatório comparativo e revisar invariantes de segurança.

Casos: Unicode/IME, modais, reordenação, foco, resize/DPI, listas virtualizadas, falha de provider, ação aceita sem efeito, repetição potencial de submissão e perda de frame. Held-out não altera políticas/thresholds depois de observado. Bug encontrado exige replay mínimo, não screenshot isolado.

Gates futuros: `python -m pytest tests/validation/test_cu_workflows.py -q`, `python -m pytest tests/held-out/test_cu_workflows.py -q`, `python -m pytest tests/test_cu_stateful.py -q`. Aceite: correção de segurança preservada e medições honestas, inclusive falhas; não apagar/skipping testes para aprovar rollout.

### 6.3 Dependências, rollback e não objetivos

Dependências: etapas 1→2→3; browser depende de 2; persistência depende de contratos 1/2; captura GPU depende de 1 e profiling, podendo aproveitar 5; apresentação suave depende de cleanup de 2; avaliação final cobre todas as etapas adotadas. Cada adapter novo deve poder ser desabilitado sem perder o caminho baseline.

Rollback: selecionar backend anterior, invalidar todos os hints/snapshots do runtime substituído e reobservar. Não fazer replay automático da última ação nem reset de dados reais. Remoção de driver, exclusão de arquivos ou reset de VM fora da fixture exigem autorização própria.

Fora do plano padrão: treino/fine-tuning SWE-2, manipulação de KV-cache proprietário, instalador de drivers virtuais, hooking de processos de terceiros, evasão antibot, bypass de UAC, gravação permanente do desktop e infraestrutura distribuída de observabilidade. Essas exclusões não eliminam a pesquisa: a matriz explica por que tais mecanismos não são a primeira atualização apropriada.

**Decisão final de arquitetura:** começar por contratos e semântica com a stack existente. GPU/Rust entram mediante medição; movimento suave entra como UX opcional. O ganho procurado é mais tarefas corretamente concluídas por unidade de tempo/custo, não maior volume de cliques ou aparência enganosa.

## 7. Fontes e rastreabilidade

Consulta de todas as fontes: 16/09/2026. URLs de documentação/repositórios são mutáveis; papers versionados fixam a revisão relevante. Releases citados na matriz são os observados, não resolução de dependências para instalação.

**Escopo da verificação:** fontes primárias consultadas diretamente ou por seu conteúdo indexado. Leitura direta substancial incluiu SWE-2, APIs Windows de input/captura/segurança/cache, DXcam, UFO2, OSWorld 2.0, artigos recentes de compressão, CUA, estudo de digitação, WebMCP e README atual Appium. Entradas de inventário apoiadas em trechos indexados comprovam o mecanismo descrito, não auditoria integral do projeto. O verificador local resolve referências e conta cobertura; não certifica a verdade de páginas externas.

**Limitações de acesso:** Flash–Hogan editorial retornou 403; PubMed exigiu cookies. A descrição do critério mínimo-jerk foi consultada no abstract primário indexado. Crates.io/thirtyfour retornou 403 no fetch; documentação versionada docs.rs forneceu datas e funcionalidades. PyPI/DXcam apresentou client challenge; README/changelog oficiais foram usados. Nenhum desafio de acesso foi contornado.

**Números congelados para a síntese:** DXcam/MSS/D3DShot 239,19/75,87/118,36 FPS no README dos autores; OSWorld-Human v2 2,7–4,3× passos; ST-Lite v3 até 2,35× decoding; GUIPruner/Qwen2-VL-2B 3,3× encoding e 3,4× redução de FLOPs; OSWorld 2.0 v2 108 tarefas e 20,6% conclusão binária na configuração especificada. Não recalculados a partir de leaderboards agregados. Contextos na seção 4.

### Registro bibliográfico

[S01]: https://cognition.com/blog/swe-2 "Cognition, Introducing SWE-2, 10/09/2026; comportamento e serving de rollouts"
[S02]: https://learn.microsoft.com/en-us/windows/win32/api/winuser/nf-winuser-sendinput "Microsoft: SendInput, retorno, serialização e UIPI"
[S03]: https://learn.microsoft.com/en-us/windows/win32/direct3ddxgi/desktop-dup-api "Microsoft: Desktop Duplication, move/dirty rectangles e rotação"
[S04]: https://learn.microsoft.com/en-us/dotnet/framework/ui-automation/caching-in-ui-automation-clients "Microsoft: caching UIA e round-trips"
[S05]: https://learn.microsoft.com/en-us/dotnet/framework/ui-automation/ui-automation-threading-issues "Microsoft: threading UIA"
[S06]: https://learn.microsoft.com/en-us/windows/win32/api/winuser/nf-winuser-printwindow "Microsoft: PrintWindow, flags documentadas e bloqueio"
[S07]: https://learn.microsoft.com/en-us/windows/win32/api/winuser/nf-winuser-postmessagew "Microsoft: PostMessageW, fila, marshaling e UIPI"
[S08]: https://learn.microsoft.com/en-us/windows/win32/api/winuser/nf-winuser-sendmessage "Microsoft: SendMessage síncrono e UIPI"
[S09]: https://learn.microsoft.com/en-us/windows/win32/winauto/uiauto-securityoverview "Microsoft: segurança de assistive technologies, atualizado em 2026"
[S10]: https://playwright.dev/docs/actionability "Playwright: auto-waiting e assertions"
[S11]: https://playwright.dev/docs/aria-snapshots "Playwright: snapshots da árvore acessível"
[S12]: https://www.selenium.dev/documentation/webdriver/bidi/ "Selenium: comunicação bidirecional"
[S13]: https://pyautogui.readthedocs.io/en/latest/quickstart.html "PyAutoGUI: input e fail-safe"
[S14]: https://pywinauto.readthedocs.io/en/stable/getting_started.html "pywinauto: backends e inspeção"
[S15]: https://docs.robotframework.org/docs/different_libraries/selenium "Robot Framework: SeleniumLibrary"
[S16]: https://github.com/yinkaisheng/Python-UIAutomation-for-Windows/ "Wrapper Python UIAutomation"
[S17]: https://github.com/jordansissel/xdotool/ "xdotool: X11/XTEST"
[S18]: https://github.com/oculix-org/SikuliX1 "Linhagem SikuliX: matching visual e aviso de continuação"
[S19]: https://raw.githubusercontent.com/appium/appium-windows-driver/master/README.md "Appium Windows atual: compatibilidade e alerta WinAppDriver"
[S20]: https://pynput.readthedocs.io/en/latest/limitations.html "pynput: limitações por plataforma"
[S21]: https://github.com/FlaUI/FlaUI/ "FlaUI: diferenças UIA2/UIA3"
[S22]: https://github.com/microsoft/OmniParser "OmniParser: parsing de tela e V2, fevereiro de 2025"
[S23]: https://github.com/ra1nty/DXcam/ "DXcam: APIs, buffers e benchmark dos autores"
[S24]: https://crates.io/crates/windows-capture "windows-capture: release 2.0.1 e documentação dos autores"
[S25]: https://crates.io/crates/xcap "xcap: release 0.9.7 e matriz de suporte"
[S26]: https://crates.io/crates/scap "scap: release beta de 2025 e backends"
[S27]: https://crates.io/crates/enigo/versions?sort=date "Enigo: release 0.6.1 de 2025"
[S28]: https://crates.io/crates/uiautomation "uiautomation-rs: release 0.25.0 e features"
[S29]: https://crates.io/crates/chromiumoxide "chromiumoxide: release 0.9.1 e CDP assíncrono"
[S30]: https://docs.rs/crate/thirtyfour/0.37.4 "thirtyfour: documentação e histórico versionados"
[S31]: https://crates.io/crates/accesskit "AccessKit: árvore, ações e adapters; release 0.24.1"
[S32]: https://crates.io/crates/Windows "windows-rs: release 0.62.2 e bindings"
[S33]: https://github.com/microsoft/playwright-mcp "Playwright MCP: snapshots estruturados"
[S34]: https://arxiv.org/abs/2403.03186v3 "Cradle: General Computer Control"
[S35]: https://arxiv.org/html/2504.14603v2 "UFO2: Desktop AgentOS, 25/04/2025"
[S36]: https://arxiv.org/html/2504.00906 "Agent S2: generalistas, especialistas e planejamento"
[S37]: https://arxiv.org/html/2501.12326v1 "UI-TARS: agente visual nativo, 2025"
[S38]: https://github.com/xlang-ai/OSWorld "OSWorld: original e anúncio Verified em 28/07/2025"
[S39]: https://arxiv.org/html/2409.08264 "WindowsAgentArena: ambiente, Navi e avaliação"
[S40]: https://arxiv.org/abs/2506.16042v2 "OSWorld-Human, revisão de 18/05/2026"
[S41]: https://arxiv.org/html/2606.29537v2 "OSWorld 2.0, revisão de 13/07/2026"
[S42]: https://www.anthropic.com/research/developing-computer-use "Anthropic: desenvolvimento de Computer Use"
[S43]: https://openai.com/index/computer-using-agent/ "OpenAI CUA, 23/01/2025"
[S44]: https://arxiv.org/abs/2210.03629v1 "ReAct: reasoning e acting intercalados"
[S45]: https://arxiv.org/html/2303.11366 "Reflexion: feedback verbal, sem atualização de pesos"
[S46]: https://arxiv.org/html/2403.12968 "LLMLingua-2: compressão textual"
[S47]: https://docs.langchain.com/oss/python/langgraph/interrupts "LangGraph: interrupções e persistência"
[S48]: https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents "Engenharia de contexto: compactação e memória"
[S49]: https://arxiv.org/abs/2602.23235v1 "GUIPruner, 26/02/2026"
[S50]: https://arxiv.org/abs/2603.00188v3 "ST-Lite v3, 26/08/2026; usar valores desta revisão"
[S51]: https://arxiv.org/abs/2606.01790v1 "STaR-KV, 01/06/2026"
[S52]: https://arxiv.org/abs/2605.18652v1 "MementoGUI, 18/05/2026"
[S53]: https://arxiv.org/abs/2609.10297v1 "TRACE, 09/09/2026; código anunciado para disponibilização futura"
[S54]: https://arxiv.org/abs/2603.26041v4 "Where and How to Prune, 09/08/2026; não usar v2 retirada"
[S55]: https://arxiv.org/html/2510.00536v1 "GUI-KV, 2025"
[S56]: https://arxiv.org/abs/2609.03236v1 "Speculative Macro Commit, 03/09/2026"
[S57]: https://developer.chrome.com/blog/webmcp-epp "WebMCP early preview, 10/02/2026"
[S58]: https://www.w3.org/TR/2026/WD-webdriver-bidi-20260601/ "WebDriver BiDi Working Draft, 01/06/2026"
[S59]: https://flatpak.github.io/xdg-desktop-portal/docs/doc-org.freedesktop.portal.ScreenCast.html "XDG Portal ScreenCast e PipeWire"
[S60]: https://libinput.pages.freedesktop.org/libei/index.html "libei: protocolo EI/EIS e permissões"
[S61]: https://github.com/flutter/flutter/blob/master/docs/platforms/desktop/windows/Accessibility-on-Windows.md "Flutter: acessibilidade Windows"
[S62]: https://blog.modelcontextprotocol.io/posts/2026-01-26-mcp-apps/ "MCP Apps: extensão de UI, 26/01/2026"
[S63]: https://learn.microsoft.com/en-us/uwp/api/windows.graphics.capture.direct3d11captureframe.dirtyregionmode?view=winrt-26100 "WGC DirtyRegionMode: verificar disponibilidade por contrato/build"
[S64]: https://github.com/oblitum/interception "Interception: descrição e licenciamento"
[S65]: https://docs.nefarius.at/projects/ViGEm/End-of-Life/ "ViGEm: aposentadoria e riscos de updater legado"
[S66]: https://learn.microsoft.com/en-us/windows-hardware/drivers/hid/virtual-hid-framework--vhf- "Microsoft: VHF e HID source drivers"
[S67]: https://github.com/microsoft/detours/ "Microsoft Detours: instrumentação de APIs"
[S68]: https://frida.re/docs/home/ "Frida: instrumentação dinâmica"
[S69]: https://github.com/vhumpa/dogtail "dogtail: automação acessível GNOME/Wayland"
[S70]: https://kernel.org/doc/html/latest/input/uinput.html "Linux kernel: uinput e recomendação libevdev"
[S71]: https://accessibilityinsights.io/docs/windows/getstarted/inspect/ "Accessibility Insights: propriedades e patterns UIA"
[S72]: https://gitlab.gnome.org/GNOME/accerciser/-/raw/master/README.md "GNOME Accerciser: inspeção e controle AT-SPI2"
[S73]: https://cheatsheetseries.owasp.org/cheatsheets/LLM_Prompt_Injection_Prevention_Cheat_Sheet.html "OWASP: injeção multimodal e defesa"
[S74]: https://hypothesis.readthedocs.io/en/latest/stateful.html "Hypothesis: geração de sequências por máquina de estados"
[S75]: https://developers.cloudflare.com/turnstile/troubleshooting/testing/ "Cloudflare: modo de teste oficial para Turnstile"
[S76]: https://developers.google.com/recaptcha/docs/v3 "Google: reCAPTCHA v3 e diferenças staging/produção"
[S77]: https://docs.datadome.co/docs/integrations "DataDome: integrações oficiais; não descreve bypass"
[S78]: https://www.jneurosci.org/content/5/7/1688 "Flash e Hogan, 1985: critério mínimo-jerk; abstract primário indexado"
[S79]: https://www.jneurosci.org/content/22/18/8201 "Comparação entre movimentos suaves e lei de potência 2/3"
[S80]: https://userinterfaces.aalto.fi/136Mkeystrokes/ "Dhakal et al., CHI 2018: pares, dedos e rollover"
[S81]: https://arxiv.org/html/2401.10935v2 "SeeClick: grounding GUI e ScreenSpot"
[S82]: https://docs.python.org/3/library/ctypes.html "Python: FFI e convenções de chamada"
[S83]: https://github.com/mhammond/pywin32/ "pywin32: APIs Windows e COM"
[S84]: https://python-mss.readthedocs.io/latest/examples.html "MSS: exemplos de captura, ROI e buffers"
[S85]: https://github.com/SerpentAI/D3DShot/blob/dev/README.md "D3DShot: Desktop Duplication Python"
[S86]: https://www.paddleocr.ai/latest/en/version3.x/algorithm/PP-OCRv5/PP-OCRv5.html "PaddleOCR: modelos e protocolos de desempenho"
[S87]: https://github.com/tesseract-ocr/tessdoc/blob/f5d77b62/ImproveQuality.md "Tesseract: qualidade e modos de segmentação"
[S88]: https://learn.microsoft.com/en-us/windows/win32/gdi/capturing-an-image "Microsoft: captura GDI/BitBlt"
[S89]: https://learn.microsoft.com/en-us/windows/win32/api/winuser/nf-winuser-setclipboarddata "Microsoft: clipboard e ownership"
[S90]: https://docs.python.org/3/library/time.html "Python: sleep não garante deadline exato"
[S91]: https://docs.nvidia.com/video-technologies/video-codec-sdk/13.1/nvenc-video-encoder-api-prog-guide/ "NVIDIA: NVENC, throughput/qualidade/latência"
[S92]: https://docs.pipewire.org/1.4/page_dma_buf.html "PipeWire: negociação DMA-BUF e fallback"
[S93]: https://developer.apple.com/documentation/screencapturekit "Apple: ScreenCaptureKit"
[S94]: https://chromium.googlesource.com/chromium/src/+/master/content/browser/devtools/protocol/input_handler.cc "Chromium: implementação de input CDP"
[S95]: https://arxiv.org/abs/1707.02038v3 "Tutorial de Thompson sampling"
[S96]: https://doc.qt.io/QT-6/accessible-qwidget.html "Qt: interfaces e eventos de acessibilidade"
[S97]: https://docs.devin.ai/cli/reference/commands "Devin CLI: modelo, plano, continuidade e exportação"
[S98]: https://arxiv.org/abs/2609.02309 "Survey de eficiência GUI, 02/09/2026"
[S99]: https://raw.githubusercontent.com/ra1nty/DXcam/main/CHANGELOG.md "DXcam: evolução de ROI, timestamps e buffers"
[S100]: https://learn.microsoft.com/en-us/windows/win32/api/uiautomationclient/nf-uiautomationclient-iuiautomationelement-findallbuildcache "Microsoft: FindAllBuildCache nativo"
[S101]: https://docs.nefarius.at/projects/ViGEm/ "ViGEm: emulação Xbox 360/DS4, não teclado/mouse genérico"
[S102]: https://learn.microsoft.com/en-us/windows/win32/api/winuser/nf-winuser-getdoubleclicktime "Microsoft: limite de tempo de duplo clique"
[S103]: https://learn.microsoft.com/en-us/windows/apps/design/accessibility/custom-automation-peers "Microsoft: AutomationPeers e patterns em controles modernos"
[S104]: https://playwright.dev/docs/browsers "Playwright: Chromium, Firefox e WebKit"
[L01]: ../../extensions/computer-use/cu_hints.py "Código local: enumeração, timeout e sidecar"
[L02]: ../../extensions/computer-use/cu_motion.py "Código local: perfis e geradores de movimento/cadência"
[L03]: ../../extensions/computer-use/screenshot.py "Código local: captura, origem, grade e hints"
[L04]: ../../extensions/computer-use/mouse.py "Código local: despacho de mouse"
[L05]: ../../extensions/computer-use/type_text.py "Código local: despacho de teclado"

