# Computer-use com ambientes isolados — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use /execution para implementar uma tarefa por vez, com TDD, revisão e gates. Delegação somente conforme autorização e ferramentas da sessão. Este documento não autoriza implementação, instalações ou ações na máquina.

**Goal:** permitir que o Devin observe e opere um desktop dedicado enquanto a pessoa continua usando seu próprio desktop, teclado e mouse.

**Architecture:** preservar o backend local e adicionar seleção explícita de ambiente. O primeiro backend isolado será uma VM QEMU, com input via QMP e captura do framebuffer da mesma VM; gerenciamento e política permanecem determinísticos. Containers com display privado e atribuição física de dispositivos são incrementos separados, não pré-requisitos para input virtual.

**Tech Stack:** Python e bibliotecas já presentes em `extensions/computer-use/`; QEMU externo, provisionado com aprovação; pytest. Rust somente mediante gargalo medido, conforme ADR 003. Laya é opcional e não participa do isolamento.

**Estado:** proposta para aprovação; nenhuma tarefa implementada ou teste de VM executado nesta análise.

**Baseline:** `main`, commit `2e11c0223cbe0bd8e625ce316b9b5b77e3f35252`, bundle `3.4.0`, consulta em 2026-09-22. Preservar `config.json` modificado e arquivos de pesquisa/template preexistentes. Alterações posteriores exigem reconciliar os caminhos antes da execução.

**Documento complementar:** [Laya: avaliação de todas as frentes de ação e plano de adoção](2026-09-22-laya-frentes-de-acao.md).

## 1. Global Constraints

- A pessoa mantém seu par físico A no host. O Devin recebe input virtual no ambiente B; comprar ou conectar um segundo par não é necessário.
- O par físico B, quando solicitado, é uma funcionalidade opcional com reserva exclusiva e reversão explícita.
- `skills/` continua sendo workflow; execução fica em `extensions/`. Hooks continuam stdlib-only e não importam extensões ou Torch.
- Nenhum fallback de ambiente isolado para desktop, clipboard, navegador ou terminal do host.
- O bundle não controla a implementação do Devin CLI. Um backend seguro não transforma todas as ferramentas nativas em ferramentas isoladas.
- Os resultados distinguem envio de input, efeito observado e cumprimento da tarefa. `ok: true` não prova sucesso.
- Preservar os testes existentes, inclusive held-out. Novos testes não podem substituir casos difíceis por mocks que já devolvem sucesso.
- Não instalar hipervisores, drivers, modelos, toolchains ou dependências automaticamente. Não desligar/reiniciar a máquina para habilitar virtualização.
- Rede do guest desabilitada por padrão; clipboard, pastas, câmera, microfone, USB e GPU passthrough desabilitados por padrão.
- QMP é interface privilegiada. Não publicar um proxy de comandos QMP arbitrários nem usar TCP sem autenticação/TLS.
- Não alterar controles de segurança do sistema para ganhar desempenho; nenhuma desativação de mitigação WHPX.
- Imagens, executáveis e eventuais dependências devem ter origem, versão, licença e digest registrados. Versões novas requerem aprovação; preferir versões publicadas há pelo menos sete dias.
- Sem commits, push, PR, instalação ou release implícitos na aprovação deste planejamento.

## 2. Requisitos e critérios de aceitação

| ID | Comportamento requerido | Prova exigida na implementação |
|---|---|---|
| R01 | Agente age apenas no ambiente escolhido | Teste real host + guest e traps nos controladores locais; zero dispatch ao host pelo backend isolado |
| R02 | Captura e ação usam a mesma instância | Rejeitar `env_id`, `instance_id`, observação ou geometria divergentes antes de enviar input |
| R03 | Dois ambientes podem coexistir | Captura, hints, perfis, filas, processos e cleanup separados por ambiente/instância |
| R04 | Teclas, atalhos e mouse funcionam no guest | Fixture independente registra key-down/up, botões, wheel, movimento absoluto/relativo e drag |
| R05 | Falha não produz repetição perigosa | ACK perdido, timeout e crash deixam resultado `unknown`/`timeout`, sem replay de ação mutante |
| R06 | Nenhuma tecla do host é liberada no cleanup remoto | Fechar, cancelar e matar worker remoto não chama `pynput` no host |
| R07 | Lifecycle é recuperável e identificado | Criar/iniciar/parar/resetar apenas ambientes próprios; discos base permanecem íntegros |
| R08 | Texto e clipboard têm contrato honesto | ASCII/layout declarado no MVP; Unicode e clipboard do guest somente com capacidade negociada |
| R09 | Aplicações Windows não dependem de containers Linux | Perfil de VM Windows separado, com imagem/licenciamento/desktop interativo verificados |
| R10 | Recursos indisponíveis são explícitos | Capacidade `supported: false` com motivo; sem sucesso simulado |
| R11 | Segundo par físico não afeta o primeiro | Teste de lease, dispositivo composto, desconexão e devolução; reserva exige seleção humana |
| R12 | Laya não decide permissões nem inventa coordenadas | Recomenda somente candidatos observados; guardas determinísticas executam antes e depois |
| R13 | Compatibilidade local é preservada | Contratos e gates atuais do computer-use continuam passando |
| R14 | Ganhos são mensurados, não prometidos | Evidência separa cold/warm, captura, transporte, dispatch, efeito e decisão opcional |

**Não objetivos:** segundo cursor universal no mesmo desktop Windows; driver VHF próprio; anti-cheat ou emulação de APIs de jogos; streaming de jogos; Kubernetes; troca de todos os backends por Laya; treinamento de modelos nesta etapa; migração automática de dados pessoais para a VM.

## 3. Estado observado no código

| Superfície | Evidência | Consequência para o plano |
|---|---|---|
| Input local | [`mouse.py:156-165`](../../extensions/computer-use/mouse.py#L156), [`type_text.py:116-124`](../../extensions/computer-use/type_text.py#L116) criam controladores pynput | Selecionar/rejeitar ambiente antes de criar controladores locais |
| Roteamento semântico existente | [`mouse.py:195-236`](../../extensions/computer-use/mouse.py#L195), [`type_text.py:175-212`](../../extensions/computer-use/type_text.py#L175) usam DOM/UIA com fallback | Reaproveitar os caminhos locais; fallback nunca pode cruzar ambiente |
| Captura | [`cu_capture.py:43-68`](../../extensions/computer-use/cu_capture.py#L43) tem somente `mss` | `$CU_CAPTURE` não constitui abstração completa de ambiente; capture e input devem compartilhar TargetContext |
| Evidência de ação | [`cu_actions.py:118-130`](../../extensions/computer-use/cu_actions.py#L118) separa status; [`mouse.py:270-272`](../../extensions/computer-use/mouse.py#L270) verifica apenas presença do alvo | Presença ou alteração de pixels não equivale ao objetivo do usuário |
| Cleanup | [`cu_actions.py:72-115`](../../extensions/computer-use/cu_actions.py#L72) libera modificadores globalmente; [`cu_session.py:178-192`](../../extensions/computer-use/cu_session.py#L178) chama esse cleanup ao fechar worker | Não reutilizar esse shutdown para transporte remoto sem torná-lo específico do backend |
| Estado compartilhado | [`cu_hints.py:334-387`](../../extensions/computer-use/cu_hints.py#L334), [`cu_motion.py:32-56`](../../extensions/computer-use/cu_motion.py#L32), [`screenshot.py:62`](../../extensions/computer-use/screenshot.py#L62) usam nomes fixos no temp | Separar estado por ambiente/instância; geração de hint não é identidade de VM |
| Worker | [`cu_session.py:34-72`](../../extensions/computer-use/cu_session.py#L34) aceita quatro scripts; daemon local em `84-126` | Não confundir worker de pipes com daemon de socket; não ampliar para execução arbitrária |
| Browser | [`cu_browser.py:124-190`](../../extensions/computer-use/cu_browser.py#L124) associa endpoint, PID e sessão locais | PID/HWND do host não identifica processo do guest; manter validação dentro do guest |
| Terminal | [`cu_terminal.py`](../../extensions/computer-use/cu_terminal.py), [`USAGE.md:254-301`](../../extensions/computer-use/USAGE.md#L254) distinguem terminal vinculado e PTY próprio | PTY já evita tomar terminal humano, mas não isola filesystem/rede; não apontar terminal remoto para host |
| Testes | [`tests/cu_load.py`](../../tests/cu_load.py), [`test_cu_session_isolation.py`](../../tests/test_cu_session_isolation.py), [`held-out/test_cu_workflows.py`](../../tests/held-out/test_cu_workflows.py) | Reusar carregamento lazy e fakes; testes atuais de sessão não provam isolamento entre desktops reais |

Esses são achados estáticos. Não foi reproduzido um incidente de interferência do cleanup nesta sessão; o fato observado é a existência do caminho global, suficiente para impedir sua reutilização indiscriminada.

## 4. Correções das premissas anteriores

O [relatório de viabilidade anterior](../research/virtual-env-input-isolation.md) permanece como histórico. Para implementação, prevalecem estas qualificações verificadas:

| Premissa anterior | Qualificação necessária | Fonte |
|---|---|---|
| Wolf e vuinputd seriam dois precedentes de produção | vuinputd se declara **Prototype / Alpha**, com segurança, recovery e integração entre runtimes ainda pendentes | P04 |
| Stack Linux funcionaria em WSL2 sem mudanças | Wolf afirma que WSL2 não foi devidamente testado; drivers e display precisam de qualificação própria | P03 |
| uinput dentro de container seria automaticamente privado | Os dispositivos são criados no kernel e visíveis a consumidores; seat, acesso e configuração do compositor precisam ser tratados | P02, P04, P05 |
| Containers não forneceriam segurança alguma | Namespaces/cgroups/capabilities fornecem isolamento, mas não são um kernel separado; mounts e privilégios alteram a fronteira | P06 |
| WSLg seria um desktop isolado pronto | WSLg integra janelas, alt-tab e clipboard ao Windows; não basta como garantia de não interferência | P07 |
| USB encaminhado ao WSL pertenceria a uma distribuição isoladamente | Microsoft documenta indisponibilidade no Windows durante attach e disponibilidade para distribuições WSL2; não é lease por container | P08 |
| Qualquer VM/QMP equivaleria ao mesmo backend | QMP é específico do QEMU. Hyper-V/RDP, VirtualBox e RFB exigem adapters próprios | P01, P10 |
| VM dispensaria cuidados de segurança | QMP tem privilégios do processo host; TCG não recebe as garantias de isolamento da política de segurança QEMU | P09 |

Não transferir números de latência, maturidade ou compatibilidade de outro projeto para este bundle.

## 5. Arquitetura proposta

```text
Pedido autorizado + ambiente explícito
                 |
       política e capacidades
                 |
       observação do ambiente
                 |
    alvo exato / shortlist semântica
                 |                 Laya opcional: recomenda, não executa
      validação de frescor/alvo <---------------------+
                 |
       executor determinístico
         /                 \
 local existente        QEMU/QMP da instância
 DOM/UIA/pynput          teclado + tablet virtuais
         |                 |
       reobservação independente do mesmo destino
                 |
     status + evidência + resultado incerto explícito
```

### 5.1 Fronteiras

- **Control plane no host:** criar e identificar ambientes; conferir política, ownership, recursos e capacidades; manter QMP privado.
- **Data plane no guest:** desktop, foco, cursor, aplicativos e input virtual. Para QMP básico, não há agente no guest nem acesso ao desktop host.
- **Decisão:** o agente principal entende a tarefa. Laya pode selecionar dentre alvos já observados e permitidos, nunca gerar código, autorizar recursos ou mudar o ambiente.
- **Verificação:** estado da aplicação, DOM/UIA ou fixture independente; modelo não avalia seu próprio sucesso.
- **Configuração nova:** `.devin/computer-use/` no projeto; recursos mutáveis grandes ficam em diretório privado do runtime, fora do repositório. Segredos nunca entram no spec versionado.

### 5.2 Backend inicial e alternativas

| Opção | Decisão | Limite que governa a escolha |
|---|---|---|
| QEMU + aceleração suportada + QMP | **Primeiro backend isolado** | Cobre input e framebuffer de uma VM, sem mouse físico adicional; qualificar imagem e host |
| Linux host + KVM | Primeira referência para testes de integração automatizáveis | Exige virtualização e acesso concedido a KVM |
| Windows host + WHPX | Perfil prioritário para esta máquina, após C00/C16 | Documentado em Windows 10 2004+; suporte local ainda não testado; não desabilitar mitigação |
| macOS host + HVF | Compatibilidade posterior pelo mesmo contrato | Validar arquitetura do host/guest e imagem; não prometer suporte já existente |
| QEMU/TCG | Diagnóstico com guest confiável, não perfil de segurança | Nunca fallback silencioso de aceleração ausente |
| Container Linux + Xvfb privado | Segundo perfil, para apps Linux confiáveis | Display próprio, sem montar display/input do host; kernel compartilhado |
| WSL2 executando esse container | Perfil experimental de compatibilidade | Engine pode estar em outra VM; não presumir que dispositivos da distro chegam ao Docker Desktop |
| Wolf/Wayland/inputtino | Referência e experimento GPU futuro | Não copiar flags amplas de `/dev`, docker.sock ou capacidades para o MVP |
| vuinputd | Pesquisa posterior, fora da dependência de produção | Alpha; não necessário para teclado/mouse via QMP ou Xvfb |
| Hyper-V/RDP, VirtualBox | Adapters futuros, não exigidos pelo primeiro release | Protocolos distintos e testes/licenças próprios; QMP não os controla |
| Firecracker | Fora do MVP de desktop | Modelo mínimo não oferece stack gráfico/HID geral; exigiria desktop software e canal adicional |
| Windows containers | Não usar para desktop interativo | Cenário de GUI não suportado oficialmente |

### 5.3 Interface de usuário proposta

Manter os entrypoints atuais. Acrescentar `--env ID` e `--observation ID` às ações isoladas; não criar seleção global implícita que mude o destino das próximas chamadas.

```text
env.py doctor --provider qemu
env.py create --spec .devin/computer-use/envs/devin-linux.json
env.py start devin-linux
screenshot.py --env devin-linux --grid
mouse.py click 320 180 --env devin-linux --observation obs-17
type_text.py "hello" --env devin-linux --observation obs-18
mouse.py scroll 320 180 --dy 2 --env devin-linux --observation obs-19
env.py status devin-linux
env.py stop devin-linux
```

São comandos futuros, não disponíveis hoje. IDs de observação vêm da resposta real; não reutilizar os IDs ilustrativos. `create/start/stop/reset` passam pelo consentimento explícito do operador. O modo local sem `--env` continua existindo por compatibilidade e continua atuando no host; a skill deve anunciar essa diferença.

`--via` escolhe o método **dentro** do destino. Nunca seleciona outro destino. No QMP inicial, `--via uia`/`browser` e perfis dependentes de posição atual rejeitam como indisponíveis; não simulam uma execução local.

## 6. Proposed Modules and Interfaces

Todos os arquivos desta tabela são **living**; só serão criados/modificados durante implementação aprovada.

| Arquivo | Responsabilidade e interface pública proposta |
|---|---|
| `extensions/computer-use/cu_target.py` | `resolve_target(env_id, registry) -> dict`; `validate_action(action, observation, capabilities) -> list[str]`; `state_path(root, env_id, instance_id, session_id, name) -> Path` |
| `extensions/computer-use/cu_backend.py` | `open_backend(target) -> Backend`; Backend oferece `capabilities()`, `observe(options)`, `dispatch(action)`, `release_owned()`, `close()`; todos retornam dict, exceto close |
| `extensions/computer-use/cu_local_backend.py` | Adapter do comportamento local existente, extraído incrementalmente; nada de captura remota por mss host |
| `extensions/computer-use/cu_qmp.py` | `QmpClient(reader, writer, deadline_s)`; `call(command, arguments) -> dict`; correlaciona IDs, eventos e falhas; não expõe passthrough público |
| `extensions/computer-use/cu_qmp_backend.py` | `axis_to_qmp(pixel, extent) -> int`; `encode_keys(keys, layout) -> list[dict]`; implementação de Backend no guest QEMU |
| `extensions/computer-use/cu_env.py` | `validate_spec(spec) -> list[str]`; `build_qemu_argv(spec, overlay) -> list[str]`; `EnvironmentManager.create/start/status/stop/reset`; ownership e lifecycle |
| `extensions/computer-use/env.py` | CLI de doctor/lifecycle; consentimento interativo nos verbos mutantes; JSON stdout, prompts stderr |
| `extensions/computer-use/cu_env_daemon.py` | Supervisor por ambiente; IPC privado autenticado; `handle(request) -> dict`; única fila mutante e canal QMP proprietário |
| `extensions/computer-use/cu_guest.py` | Adapter opcional para RPC delimitado do worker interativo guest; métodos enumerados, sem shell remoto genérico |
| `extensions/computer-use/guest/worker.py` | Worker dentro da sessão gráfica guest; `handle(request) -> dict`; observar/invocar/set-value/clipboard/bind explícitos |
| `extensions/computer-use/cu_container.py` | Provider posterior: display Xvfb privado, invocação restrita de Docker/Podman e RPC guest |
| `extensions/computer-use/cu_devices.py` | `validate_lease(request, inventory, active_leases) -> list[str]`; atribuição física opcional, sem wildcard |
| `extensions/computer-use/cu_decision.py` | Client opcional Laya; contrato e tarefas definidos no plano complementar |
| Arquivos existentes: `mouse.py`, `type_text.py`, `screenshot.py`, `profile.py` | Parsing e compatibilidade; resolver target antes de acessar OS |
| Existentes: `cu_hints.py`, `cu_motion.py`, `cu_capture.py`, `cu_session.py`, `cu_session_dispatch.py`, `cu_browser.py`, `browser.py`, `browser_events.py`, `cu_terminal.py`, `terminal.py`, `terminal_sessions.py` | Estado e binding por destino, cleanup contextual, sem misturar PIDs/observações |
| `tests/test_cu_env_*.py`, `tests/test_cu_qmp_*.py` | Contratos, transcript QMP e traps anti-fallback |
| `extensions/computer-use/integration/test_cu_env_live.py`, `extensions/computer-use/integration/fixtures/cu_input_probe.py` | Prova real com app controlado; somente ambientes de teste autorizados |
| `tests/held-out/test_cu_env_boundaries.py` | Casos independentes de fronteira; manter os held-out atuais |
| `.devin/templates/computer-use/` | Exemplos sem credenciais, imagens ou endpoints públicos; não ativados pelo installer |

Não criar um novo framework de plugins, um router global concorrente ou um novo MCP server nesta etapa. O seam varia porque existem dois destinos concretos: local e VM.

### 6.1 Identidade, observação e ação

Contrato proposto para ambiente; propriedades ilustrativas são dados de exemplo, não descoberta de hardware:

```json
{
  "schema_version": 1,
  "env_id": "devin-linux",
  "provider": "qemu",
  "image_ref": "approved-linux-desktop",
  "image_sha256": "digest-validado-no-provisionamento",
  "guest_os": "linux",
  "keyboard_layout": "en-us",
  "resources": {"vcpus": 2, "memory_mib": 4096},
  "network": "off",
  "clipboard": "off",
  "mounts": [],
  "physical_devices": []
}
```

O digest ilustrativo deve ser rejeitado pelo validador; specs executáveis exigem 64 caracteres hexadecimais e imagem aprovada. CPU/RAM são ponto de partida proposto, não benchmark nem requisito universal. Configurar limites conforme C00 e a carga do usuário.

```json
{
  "schema_version": 3,
  "env_id": "devin-linux",
  "instance_id": "incarnation-unique",
  "session_id": "controller-session",
  "observation_id": "obs-17",
  "generation": 17,
  "coordinate_space": "guest-frame-px",
  "origin_px": [0, 0],
  "size_px": [1280, 720],
  "image": {"path": "private-runtime-frame.png", "sha256": "frame-digest"},
  "hints": null,
  "capabilities": {"absolute_pointer": true, "unicode_text": false}
}
```

```json
{
  "version": 1,
  "request_id": "unique-per-action",
  "env_id": "devin-linux",
  "instance_id": "incarnation-unique",
  "observation_id": "obs-17",
  "op": "pointer.click",
  "args": {"x": 320, "y": 180, "button": "left", "clicks": 1},
  "deadline_ms": 3000,
  "dry_run": false
}
```

- `instance_id` muda em start/restart/reset; `generation` refere-se às observações daquela instância. Nunca confundir os dois.
- `captured_at` serve à apresentação; frescor usa relógio monotônico do supervisor que recebeu a captura. Não subtrair relógios de máquinas distintas.
- Ações devem referenciar observação existente e vigente. Atualização de geometria, troca de controle humano/agente ou reinício invalida as observações anteriores.
- `request_id` é deduplicado na instância. Uma solicitação ambígua já transmitida não pode ser repetida automaticamente com novo ID.
- Resultados preservam `status`, `dispatch.backend`, `timings_ms`; acrescentam `env_id`, `instance_id`, `request_id`, `observation_id` e `dispatch.sent` (`0`, número conhecido ou `null` se incerto).
- Acrescentar `status: planned` ao contrato v2 para dry-run. Significa plano validado, zero input. Compatibilidade v1 dos CLIs atuais será caracterizada antes de migrar.
- `verified` exige predicado explícito e evidência posterior da mesma instância. ACK QMP é apenas `dispatched`.

### 6.2 Capabilities e limitações de input

| Operação | QMP inicial | Incremento previsto |
|---|---|---|
| Captura de tela | `screendump`; PNG se negociado, PPM convertido com Pillow se necessário | Stream RFB/SPICE somente se uma medição justificar |
| Movimento absoluto | `usb-tablet`, coordenadas QMP 0..32767 | Múltiplos displays somente com mapeamento explícito |
| Movimento relativo | Eventos `rel`; efeito depende das configurações do guest | Validar no probe; não confundir unidade relativa com pixel absoluto |
| Click/double-click/drag | Eventos ordenados, botão down/up balanceado | Nenhum input passa pelo host |
| Wheel | Eventos de botão wheel conforme schema negociado | Rejeitar eixos não suportados, não ignorar silenciosamente |
| Atalhos | QKeyCode/scancode com layout explicitamente declarado | Testes PT-BR/ABNT2 em perfil qualificado |
| Texto arbitrário | Não suportado somente por QMP; ASCII mapeado no layout conhecido | C10/C11: set-value/text via worker guest |
| Clipboard | Desligado; nunca usar clipboard host para simular texto | C11: clipboard do guest, opt-in por direção e tamanho |
| Posição atual do cursor | `query-mice` não fornece posição atual | Retornar indisponível, ou observar por worker; não reportar última posição enviada como atual |
| UIA/DOM | QMP não fornece árvore de acessibilidade | C10/C11: coleta e binding dentro do guest |
| Perfis smooth/human | Só quando posição inicial e backend forem conhecidos | Inicialmente fast; rejeitar perfil incompatível em vez de adivinhar |

Conversão absoluta, decidida neste plano:

```python
def axis_to_qmp(pixel, extent):
    if isinstance(pixel, bool) or isinstance(extent, bool):
        raise ValueError("invalid_geometry")
    if not isinstance(pixel, int) or not isinstance(extent, int):
        raise ValueError("invalid_geometry")
    if extent <= 0 or not 0 <= pixel < extent:
        raise ValueError("out_of_bounds")
    return 0 if extent == 1 else round(pixel * 32767 / (extent - 1))
```

Coordenadas recebidas de screenshots com região somam `origin_px` antes da normalização. O parâmetro QMP `device` identifica o display de destino, não o nome de um teclado físico. Não aplicar DPI/CSS do host a pixels do guest.

### 6.3 Segurança e recuperação

- Supervisor possui os pipes stdin/stdout do QEMU (`-qmp stdio`), sem QMP TCP. O agente recebe somente operações tipadas, não `execute` QMP livre.
- CLI-supervisor: AF_UNIX em POSIX e named pipe com ACL de usuário no Windows. Usar `send_bytes/recv_bytes` com JSON e tamanho limitado, nunca deserialização pickle de mensagens.
- Um único controller ativo por ambiente. Demais clientes podem observar. Sessão humana dedicada pausa ações do agente; os dois compartilham o cursor do guest, não ganham dois cursores dentro dele.
- Input remoto jamais registra `cu_actions.emergency_release` no host. Cleanup mantém ownership por backend e instância.
- Fechar transporte depois de key-down não prova que houve key-up. Tentar liberar no mesmo guest; sem confirmação de recuperação, quarentenar e bloquear novas ações. Não afirmar cleanup bem-sucedido por ausência de exceção.
- Consentimento de lifecycle é humano: `env.py create/start/stop/reset` pede confirmação interativa do digest do plano no terminal e rejeita mutação sem TTY. O caminho de testes injeta consentimento fake; o caminho de produção não expõe emissão de autorização ao modelo. Futura automação não interativa exige integração de consentimento separadamente aprovada.
- Digitar uma confirmação no PTY pelo próprio agente não representa consentimento humano. O workflow não pode fazer isso.
- Root de ambiente privado; bloquear `..`, paths absolutos derivados de input, symlinks/reparse e backing chain externa não aprovada. Base read-only, overlay por instância.
- `stop` primeiro pede shutdown gracioso e preserva disco; prazo excedido não autoriza kill. Force/reset/destroy pedem nova confirmação específica.
- Rede desativada significa `-nic none`, não apenas ausência de port-forward. Egress necessário vira alteração explícita de spec e consentimento.
- Este mecanismo separa guest/host; não protege o host contra um agente principal malicioso que já possui ferramentas nativas com permissões do usuário.

## 7. Plano em slices verificáveis

Os comandos abaixo são **gates futuros**, executados somente após criar os arquivos indicados. Todos os IDs começam com checkbox desmarcado. Em cada tarefa: escrever teste RED, executar e registrar falha esperada; implementar GREEN; executar gate; revisar diff e invariantes; parar no checkpoint humano indicado. Os exemplos de teste especificam comportamento mínimo, não substituem a lista completa de casos.

Estimativa de revisão, não de prazo: cada slice visa aproximadamente 150–500 linhas incluindo testes. Se a previsão ultrapassar 500 linhas, separar o comportamento antes de iniciar; não encurtar validação para caber. Shared files impedem implementação paralela de tarefas vizinhas.

### C00 — Diagnosticar pré-requisitos sem alterar a máquina

**Depende de:** nenhuma. **Arquivos:** criar `env.py`, `cu_env.py`, `tests/test_cu_env_doctor.py`.

- [ ] Implementar `doctor` read-only: plataforma/arquitetura, executável QEMU, versão, aceleradores anunciados, espaço/RAM e presença de imagem explicitamente indicada. Não ler credentials nem testar teclados pessoais.
- [ ] Distinguir acelerador listado de acelerador realmente inicializado. Ausência gera `ready: false`, `required_user_actions`; não habilitar recursos Windows.
- [ ] Testar binário ausente, arquitetura incompatível, imagem não aprovada e subprocess timeout com injeção de runner.

```python
def test_missing_qemu_does_not_provision():
    report = cu_env.doctor(which=lambda name: None, run=forbidden_run)
    assert report["ready"] is False
    assert report["actions_performed"] == []
```

`doctor(which, run)` é seam de teste; `forbidden_run(*args, **kwargs)` lança AssertionError. **Gate:** `python -m pytest tests/test_cu_env_doctor.py -q`. **Aceite:** zero instalação/driver/VM iniciado. **Checkpoint:** usuário aprova provider, imagem, licença e orçamento de recursos antes de C04.

### C01 — Rejeitar destino remoto inválido sem tocar o host

**Depende de:** C00. **Arquivos:** criar `cu_target.py`, `cu_backend.py`, `tests/test_cu_env_routing.py`; modificar parsing em `mouse.py`, `type_text.py`, `screenshot.py`, `profile.py`.

- [ ] Resolver `--env` antes de controller, UIA, mss ou registro de cleanup.
- [ ] `resolve_target(env_id, registry)` retorna registro válido ou lança `TargetError`; desconhecido nunca equivale a local.
- [ ] Backend ainda ausente retorna rejeição tipada. Testar todas as entradas, incluindo `--dry-run`, `--via auto` e `$CU_SESSION=1`.

```python
def test_unknown_environment_is_not_local():
    with pytest.raises(cu_target.TargetError, match="unknown_environment"):
        cu_target.resolve_target("missing", {})
```

**Gate:** `python -m pytest tests/test_cu_env_routing.py tests/test_cu_action_results.py -q`. Adicionar trap de criação de `pynput.Controller` e de `emergency_release`: ambos proibidos no ramo remoto rejeitado.

### C02 — Manter estado independente por ambiente e instância

**Depende de:** C01. **Arquivos:** `cu_target.py`, `cu_hints.py`, `cu_motion.py`, `screenshot.py`; criar `tests/test_cu_env_state.py`.

- [ ] Namespaces de hints, observações, perfil, hash de captura e binding são `(env_id, instance_id, session_id)`; diretório privado e escrita atômica.
- [ ] Preservar leitura legacy somente no backend local. Migrar bindings de browser/terminal junto de C12, não reutilizá-los no remoto.
- [ ] `state_path` valida componentes; campos desconhecidos não viram paths. Reinício invalida observações sem reutilizar números antigos como identidade.

```python
def test_state_paths_do_not_collide(tmp_path):
    a = cu_target.state_path(tmp_path, "a", "i1", "s1", "hints.json")
    b = cu_target.state_path(tmp_path, "b", "i1", "s1", "hints.json")
    assert a != b
```

**Gate:** `python -m pytest tests/test_cu_env_state.py tests/test_cu_observation_contract.py tests/test_cu_motion_profiles.py -q`. Casos extras: concorrência, falha de persistência, symlink/reparse, reinício e ID com traversal.

### C03 — Consultar QMP com framing e correlação corretos

**Depende de:** C01. **Arquivos:** criar `cu_qmp.py`, `tests/test_cu_qmp_protocol.py`, `tests/fixtures/cu_qmp_transcripts.json`.

- [ ] Negociar greeting e `qmp_capabilities`; consultar comandos/schema suportados.
- [ ] Correlacionar `id`; eventos assíncronos não satisfazem resposta. Tratar leituras fragmentadas, EOF, JSON inválido e deadline.
- [ ] Manter allowlist interna separando consulta, input e lifecycle. Bloquear QMP arbitrário vindo do agente.

```python
def test_monitor_escape_is_not_a_public_operation():
    assert cu_qmp.public_operation_allowed("human-monitor-command") is False
    assert cu_qmp.public_operation_allowed("migrate") is False
```

`public_operation_allowed(name) -> bool` cobre apenas operações tipadas publicadas, não todos os comandos internos. **Gate:** `python -m pytest tests/test_cu_qmp_protocol.py -q`. Transcript de ACK vazio deve preservar sucesso de transporte sem virar efeito verificado.

### C04 — Criar e iniciar uma VM própria sem compartilhamentos implícitos

**Depende de:** C00, C02, C03. **Arquivos:** `cu_env.py`, `env.py`; criar `cu_env_daemon.py`, `tests/test_cu_env_lifecycle.py`, `tests/test_cu_env_consent.py`.

- [ ] Consumir spec aprovado; verificar digest da base e backing chain; criar overlay novo sem alterar base.
- [ ] Construir argv por lista, `shell=False`; perfis fechados de máquina/display/controlador. QMP em stdio; sem monitor/serial misturados no stdout.
- [ ] `EnvironmentManager` guarda PID + identidade de início + instance_id; não adota processo encontrado apenas por nome.
- [ ] `build_qemu_argv` inclui `-display none`, `-qmp stdio`, `-monitor none`, `-serial none`, `-nic none` no perfil default; aceleração obrigatória explícita.

```python
def test_default_vm_has_no_network(spec, overlay):
    argv = cu_env.build_qemu_argv(spec, overlay)
    assert argv[argv.index("-nic") + 1] == "none"
    assert argv[argv.index("-qmp") + 1] == "stdio"
```

`spec` é fixture validada com imagem temporária aprovada; `overlay` é path sob root privado. **Gate:** `python -m pytest tests/test_cu_env_lifecycle.py tests/test_cu_env_consent.py -q`. Falhas: consentimento ausente, spec alterado após confirmação, arquivo estrangeiro e binário trocado. **Checkpoint:** primeiro boot real autorizado; não confundir `running` com desktop pronto.

### C05 — Capturar o framebuffer correto sem mss no host

**Depende de:** C04. **Arquivos:** criar `cu_qmp_backend.py`, `tests/test_cu_env_capture.py`; modificar `cu_capture.py`, `screenshot.py`.

- [ ] `observe` executa `screendump` para arquivo novo dentro do root privado, lê dimensões reais e calcula digest.
- [ ] Negociar PNG/PPM; não assumir que build tem CONFIG_PIXMAN/PNG. Rejeitar formato/dimensões inválidos e path escapando do root.
- [ ] Gerar grid usando pixels guest. Sem UIA guest, retornar `hints: null` honestamente.

```python
def test_qmp_axis_corners():
    assert cu_qmp_backend.axis_to_qmp(0, 1280) == 0
    assert cu_qmp_backend.axis_to_qmp(1279, 1280) == 32767
```

**Gate:** `python -m pytest tests/test_cu_env_capture.py tests/test_cu_capture_frames.py tests/test_cu_screenshot.py -q`. Teste chama frontend com mss host substituído por trap; captura ainda deve ocorrer na fixture QMP.

### C06 — Enviar teclas e atalhos somente ao guest

**Depende de:** C05. **Arquivos:** `cu_qmp_backend.py`, `type_text.py`; criar `tests/test_cu_qmp_keyboard.py`.

- [ ] Mapear key names para QKeyCode/scancode negociado. Balancear modificadores e liberar em ordem reversa.
- [ ] Pré-validar todo texto antes de enviar qualquer caractere. Layout desconhecido ou caractere não representável rejeita zero input.
- [ ] Atalhos permanecem eventos do guest; nenhum `SendInput`, clipboard ou pynput host.

```python
def test_unsupported_text_never_sends_prefix():
    with pytest.raises(cu_qmp_backend.UnsupportedText):
        cu_qmp_backend.encode_text("abc漢字", layout="en-us")
```

`encode_text(text, layout) -> list[dict]` é helper puro novo. **Gate:** `python -m pytest tests/test_cu_qmp_keyboard.py -q`. Cobrir maiúsculas, caracteres de controle, AltGr/dead keys como capacidades explícitas, cancelamento no meio do chord e ACK perdido.

### C07 — Operar mouse, wheel e drag com geometria vinculada

**Depende de:** C06. **Arquivos:** `cu_qmp_backend.py`, `mouse.py`; criar `tests/test_cu_qmp_pointer.py`.

- [ ] Validar limites, região/origem, botão lógico guest e geometria atual. Não usar `SM_SWAPBUTTON` do host no guest.
- [ ] Gerar eventos down/up, relativo/absoluto e wheel conforme schema; serializar gesto como unidade cancelável.
- [ ] Rejeitar consulta de posição real quando só houver last-command cache; não inventar posição.

```python
def test_out_of_frame_is_not_clamped():
    with pytest.raises(ValueError, match="out_of_bounds"):
        cu_qmp_backend.axis_to_qmp(1280, 1280)
```

**Gate:** `python -m pytest tests/test_cu_qmp_pointer.py tests/test_cu_mouse_swap.py -q`. Adicionar casos double-click, drag interrompido, resize entre captura e click, crop, um pixel, valores booleanos e wheel horizontal indisponível.

### C08 — Cancelar e recuperar sem liberar inputs do host

**Depende de:** C07. **Arquivos:** `cu_env_daemon.py`, `cu_backend.py`, `cu_actions.py`, `cu_session.py`, `cu_session_dispatch.py`; criar `tests/test_cu_env_recovery.py`.

- [ ] Injetar cleanup de backend no worker; local mantém seu comportamento caracterizado, remoto nunca usa cleanup local.
- [ ] Deduplicar request IDs; registrar accepted/inflight/completed/unknown. Não fazer replay após envio incerto.
- [ ] EOF, heartbeat perdido e timeout levam a recuperação no mesmo guest ou quarentena; fila cancelada não executa depois de reconectar.

```python
def test_ambiguous_action_is_not_retryable():
    assert cu_backend.may_retry({"status": "unknown", "dispatch": {"sent": None}}) is False
```

`may_retry(result) -> bool` só aceita consulta read-only explicitamente identificada ou rejeição anterior a qualquer envio; este resultado não satisfaz isso. **Gate:** `python -m pytest tests/test_cu_env_recovery.py tests/test_cu_session_isolation.py tests/test_cu_stateful.py -q`. **Checkpoint:** testes de trap provam que cada saída remota deixa o host intocado.

### C09 — Reobservar efeito sem promover ACK a sucesso

**Depende de:** C08. **Arquivos:** `cu_backend.py`, `cu_actions.py`, `mouse.py`, `type_text.py`; criar `tests/test_cu_env_verification.py`.

- [ ] `verify_effect(action, before, after, predicate) -> dict` exige mesma instância e observação posterior.
- [ ] Suportar predicados fechados: valor de campo/DOM/UIA quando disponível e estado do probe de teste; mudança visual isolada gera evidência, não tarefa concluída.
- [ ] Preservar `target_present` atual como informação, não prova de ação bem-sucedida; dry-run v2 retorna `planned`.

```python
def test_ack_is_not_effect_verification():
    r = cu_backend.result_from_ack({"return": {}}, request_id="r1")
    assert r["status"] == "dispatched"
    assert "verification" not in r
```

`result_from_ack(ack, request_id)` normaliza só transporte. **Gate:** `python -m pytest tests/test_cu_env_verification.py tests/test_cu_action_results.py -q`. Imagem alterada por animação sem efeito esperado não pode aprovar o teste.

### C10 — Negociar worker guest na sessão gráfica correta

**Depende de:** C09. **Arquivos:** criar `cu_guest.py`, `guest/worker.py`, `tests/test_cu_env_guest_protocol.py`.

- [ ] Adicionar canal virtio-serial separado do QMP, conectado a pipes privados controlados pelo supervisor. Worker guest é opt-in, pré-instalado na imagem aprovada.
- [ ] Handshake informa protocol_version, guest boot/session identity e capacidades; respostas são dados não confiáveis com tamanho limitado.
- [ ] Worker iniciado no usuário gráfico, não serviço Windows Session 0. Desktop bloqueado/inacessível retorna indisponível, sem bypass de UAC ou login.

```python
def test_guest_session_zero_has_no_interactive_capability():
    caps = cu_guest.validate_handshake({"version": 1, "interactive": False, "session_id": 0})
    assert caps["text_insert"] is False
    assert caps["uia"] is False
```

`validate_handshake(reply) -> dict` não aceita capabilities alegadas incompatíveis com estado da sessão. **Gate:** `python -m pytest tests/test_cu_env_guest_protocol.py -q`. Testar tamanho, método não enumerado, resposta atrasada e troca de boot. Perfis sem driver virtio-serial seguem funcionando por QMP, com capacidades reduzidas explícitas.

### C11 — Inserir Unicode e usar clipboard somente no guest

**Depende de:** C10. **Arquivos:** `guest/worker.py`, `cu_guest.py`, `type_text.py`; criar `tests/test_cu_env_text.py`.

- [ ] Implementar SetValue na sessão Windows guest quando disponível; text-injection usa sessão guest e contrato de layout. DOM somente se C12 já fornecer binding autorizado; até lá, declarar essa capacidade indisponível.
- [ ] Clipboard é operação independente, opt-in; não sincronizar automaticamente host/guest nem preservar conteúdo secreto em logs.
- [ ] Validar string completa e tamanho antes do efeito; efeitos parciais retornam `unknown` com contagem conhecida, nunca retry cego.

```python
def test_clipboard_disabled_is_rejected():
    r = cu_guest.check_operation("clipboard.set", {"clipboard": False})
    assert r == {"allowed": False, "reason": "capability_unavailable"}
```

`check_operation(op, capabilities) -> dict` é verificador puro. **Gate:** `python -m pytest tests/test_cu_env_text.py -q`. Prova real inclui `ação`, `ç`, acentos combinantes, emoji como dado de teste solicitado na execução e newline; se uma plataforma não representar algum caso, registrar falha/capacidade, não transliterar silenciosamente.

### C12 — Vincular browser e terminal ao ambiente, não ao host

**Depende de:** C10. **Arquivos:** `cu_browser.py`, `browser.py`, `browser_events.py`, `cu_terminal.py`, `terminal.py`, `terminal_sessions.py`, `guest/worker.py`; criar `tests/test_cu_env_bindings.py`.

- [ ] Executar PID/HWND/UIA/DOM checks dentro do guest. Namespaces dos bindings incluem env/instance; remote-debugging não publicado na rede host.
- [ ] Não ampliar a allowlist loopback do browser host para aceitar IPs arbitrários. Guest bridge acessa o loopback guest.
- [ ] Terminal/exec remoto não oferece caminho para contornar DENY/CONFIRM do system-control; preserva autorização da ação e output não confiável.

```python
def test_host_binding_is_invalid_in_guest():
    assert cu_guest.binding_matches({"env_id": "host", "instance_id": "h"}, "vm-a", "a") is False
```

`binding_matches(binding, env_id, instance_id) -> bool` faz comparação exata. **Gate:** `python -m pytest tests/test_cu_env_bindings.py tests/test_cu_browser_contract.py tests/test_cu_browser_routing.py tests/test_cu_terminal_bind.py -q`. Dividir browser e terminal em dois PRs se a soma exceder o limite de revisão; não remover nenhum teste original.

### C13 — Parar e resetar ambientes próprios com reversão controlada

**Depende de:** C09. **Arquivos:** `cu_env.py`, `cu_env_daemon.py`, `env.py`; criar `tests/test_cu_env_reset.py`.

- [ ] `stop` pede shutdown gracioso; timeout mantém estado explícito. Force stop exige confirmação separada.
- [ ] `reset` arquiva overlay anterior e cria outro a partir da base aprovada; muda instance_id, descarta filas/bindings/observações antigas.
- [ ] Não remover bases ou arquivos de ambientes não próprios. Deleção definitiva fica fora do primeiro release.

```python
def test_reset_invalidates_old_instance():
    assert cu_env.same_instance({"instance_id": "before"}, {"instance_id": "after"}) is False
```

`same_instance(a, b) -> bool` exige IDs válidos e iguais. **Gate:** `python -m pytest tests/test_cu_env_reset.py tests/test_cu_env_consent.py -q`. Snapshot de RAM e retomada de device leases não são presumidos; primeiro reset é cold start com base + overlay.

### C14 — Rodar aplicações Linux em container com display privado

**Depende de:** C10, C13. **Arquivos:** criar `cu_container.py`, `guest/container-entry.py`, `tests/test_cu_env_container.py`, `.devin/templates/computer-use/container-profile.json`.

- [ ] Perfil alternativo: Xvfb + window manager + worker dentro do container; Xvfb não requer dispositivos físicos. Nenhum mount de X11/Wayland/DBus do host.
- [ ] Criar via CLI runtime aprovada, sem docker.sock dentro do container. Non-root, cap-drop, no-new-privileges, rootfs read-only quando suportado, tmpfs limitado e rede off.
- [ ] Não montar `/dev/input`, `/dev/uinput`, `/dev/dri`, `/mnt/c` ou home por conveniência. WSLg sockets não fazem parte deste perfil.

```python
def test_container_spec_rejects_host_display():
    errors = cu_container.validate_profile({"mounts": ["/tmp/.X11-unix:/tmp/.X11-unix"], "privileged": False})
    assert "host_display_mount_forbidden" in errors
```

`validate_profile(profile) -> list[str]` valida campos por allowlist. **Gate:** `python -m pytest tests/test_cu_env_container.py -q`. Qualificar Linux nativo primeiro; WSL2/Docker Desktop são linhas de matriz independentes. O suporte publicado continua limitado às combinações realmente testadas.

### C15 — Reservar um segundo par físico sem capturar o par humano

**Depende de:** C13. **Arquivos:** criar `cu_devices.py`, `tests/test_cu_env_device_leases.py`; estender `env.py` com inventário e plano de lease, não attach automático.

- [ ] Identificar dispositivo por serial/topologia/interface além de VID/PID; mostrar todos os membros de receptores compostos. Nunca atribuir por `eventN` persistido ou wildcard VID/PID.
- [ ] Pessoa declara par A protegido e confirma par B. Se receptor também contém A, recusar. Nada de capturar todos os teclados para descobrir qual é o segundo.
- [ ] Linux: passthrough USB específico para VM qualificada. Windows → guest Linux: avaliar usbipd-win com acesso restrito à rede da VM, kernel/drivers presentes e attach verificado; WSL não equivale a um container específico.
- [ ] Não prometer passthrough QEMU Windows por libusb sem validar o pacote/driver. Windows guest e dispositivos Bluetooth ficam `unsupported` até teste próprio.
- [ ] Lease com estados available/reserved/attached/releasing/lost; somente um consumidor. Disconnect pausa agente; replug exige reidentificação, não adota outro hardware.

```python
def test_protected_device_cannot_be_leased():
    errors = cu_devices.validate_lease({"device_id": "human-keyboard", "env_id": "vm-a"}, {"protected": ["human-keyboard"]}, [])
    assert "protected_host_device" in errors
```

**Gate:** `python -m pytest tests/test_cu_env_device_leases.py -q` + prova manual registrada com hardware real. **Checkpoint:** instalação/bind/attach/firewall somente com aprovação específica. Falha de suporte preserva a entrega virtual sem hardware e registra esta capacidade como não qualificada; não a declara concluída.

### C16 — Provar não interferência em ambientes reais

**Depende de:** C09, C13. **Arquivos:** criar `extensions/computer-use/integration/test_cu_env_live.py`, `extensions/computer-use/integration/fixtures/cu_input_probe.py`, `tests/held-out/test_cu_env_boundaries.py`; estender `cu_bench.py` sem alterar baseline congelado.

- [ ] Fixture guest própria registra eventos e mudanças de UI. Host usa uma janela sentinela de teste consentida, não keylogger global nem captura de texto pessoal.
- [ ] Rodar: humano digita/move A no host enquanto agente opera guest; segundo guest simultâneo; resize; foco; cancel; kill worker; perda de transporte; reconnect; queda da VM.
- [ ] Separar ausência de observação de ausência de vazamento: além de contadores host, traps garantem que backend remoto não invoca APIs locais.
- [ ] Medir cold/warm, capture/dispatch/efeito e RSS; executar controle sem Laya. Nunca importar os números de Wolf/Laya como resultados locais.

```python
def test_independent_guest_and_host(probe_run):
    assert probe_run["guest_expected_effects"] == probe_run["guest_observed_effects"]
    assert probe_run["unexpected_host_effects"] == []
    assert probe_run["remote_calls_to_local_input"] == 0
```

`probe_run` é fixture real que devolve captura congelada dos dois probes, não dict de sucesso construído pelo executor. **Gate:** `python -m pytest tests/held-out/test_cu_env_boundaries.py -q`; gate real explícito `python -m pytest extensions/computer-use/integration/test_cu_env_live.py -q`. Job habilitado sem VM configurada deve falhar, não skip. A suíte real fica em `extensions/computer-use/integration/`, fora do `tests/` coletado pela CI comum; o job explícito exige runner autorizado e falha se a VM estiver ausente. O relatório de release discrimina plataformas não executadas. Responsável pelo desenho/checagem de métricas é o mantenedor, não o implementador avaliando a própria saída.

### C17 — Distribuir e documentar sem ativação silenciosa

**Depende de:** C16. **Arquivos:** `extensions/computer-use/USAGE.md`, `skills/computer-use/SKILL.md`, `skills/system-control/SKILL.md`, `manifest.json`, `install.ps1`, `install.sh`, `.devin/docs/TOOLS-MAP.md`; criar testes de instalação apenas para o que mudar.

- [ ] Installer copia adapters/templates; não baixa imagem/hipervisor/Laya e não inicia daemon. Não alterar o `config.json` preexistente desta sessão.
- [ ] Documentar cada flag, status v2, backend/capability e limitação; manter índice da skill curto e detalhes na USAGE.
- [ ] Ensinar a preferência: API/CLI autorizada no destino → DOM/UIA vinculada → input VM → físico local somente se solicitado. Não contornar políticas por mudança de ferramenta.
- [ ] Feature permanece opt-in; Laya não é dependência necessária do computer-use.

**Gates:** `python audit.py`, `python -m pytest tests -q`, `bash -n install.sh`; gates de parser/shellcheck/instalação da CI se installers mudarem. Rodar a matriz existente de Python 3.11/3.14 × Linux/Windows/macOS sem removê-la. Nenhum sucesso da CI simulada substitui o gate real de C16.

**Rollback:** desativar uso de `--env` no workflow, parar ambientes próprios com consentimento, preservar overlays/evidência; backend local permanece disponível somente por escolha explícita. Laya tem rollback independente para `off`.

## 8. DAG e marcos

```json
{
  "C00": [],
  "C01": ["C00"],
  "C02": ["C01"],
  "C03": ["C01"],
  "C04": ["C00", "C02", "C03"],
  "C05": ["C04"],
  "C06": ["C05"],
  "C07": ["C06"],
  "C08": ["C07"],
  "C09": ["C08"],
  "C10": ["C09"],
  "C11": ["C10"],
  "C12": ["C10"],
  "C13": ["C09"],
  "C14": ["C10", "C13"],
  "C15": ["C13"],
  "C16": ["C09", "C13"],
  "C17": ["C16"]
}
```

- **M1, MVP isolado:** C00–C09 + C13 + C16 + C17. Um guest, sem hardware extra, sem clipboard, sem visão por Laya.
- **M2, integração semântica:** C10–C12; repetir C16 para as capacidades adicionadas antes de publicá-las.
- **M3, perfil leve Linux:** C14 + sua prova real; não bloqueia M1.
- **M4, par físico B:** C15 + sua prova hardware; não bloqueia M1, mas permanece capacidade solicitada a qualificar.
- **M5, Laya:** seguir plano complementar; computer-use deve continuar útil se nenhuma avaliação Laya justificar promoção.
- C02 e C03 podem avançar separadamente depois do contrato C01, mas edições nos mesmos frontends exigem integração serial. C10/C13 são ramos separados; C11/C12 compartilham worker e não devem editar esse arquivo em paralelo.

## 9. Matriz de verificação e riscos

| Risco | Caso adversarial | Resultado obrigatório |
|---|---|---|
| Fallback cruzando fronteira | QMP cai, auto selecionado | Rejeição/unknown remoto; zero input/capture host |
| Hint de outra VM | Mesmo hint `as`, envs diferentes | Rejeição antes de dispatch |
| TOCTOU | Janela/geometry mudou depois de captura | Reobservar; não clicar coordenada antiga |
| Cleanup global | Worker encerrado com Ctrl pressionado | Release só no guest; se incerto, quarentena |
| Replay | Resposta perdida depois de click | Nenhum segundo click automático |
| Falso sucesso | ACK vazio, animação ou alvo ainda presente | Não promover para verified da tarefa |
| QMP arbitrário | Pedido contém monitor/migrate/file path | Rejeição de schema/allowlist |
| Conteúdo host exposto | Mount home, clipboard, disco físico ou USB A | Recusar spec por padrão |
| Modelo errado | Laya aponta alvo desabilitado/antigo | Validação determinística recusa |
| Co-uso do guest | Humano B assume controle | Pausar fila e invalidar observação antes de devolver ao agente |
| Recursos | VM ultrapassa orçamento de RAM/disk | Falha clara; sem habilitar swap/GPU ou redimensionar silenciosamente |
| Plataforma incompleta | QEMU existe, aceleração não funciona | Reportar não qualificado; não anunciar isolamento TCG |

Permanecem dependências externas não verificadas nesta máquina: QEMU/WHPX/KVM, imagem gráfica, drivers guest, USB adicional, topologia dos dispositivos e capacidade do hardware sob carga. Nenhum desses itens impede entregar o plano; todos impedem declarar a implementação funcional sem C00/C16.

## 10. Fontes primárias diretamente consultadas

URLs documentam mecanismos; testes de integração deste projeto ainda não foram executados. A documentação QEMU consultada é `master` (11.1.50 no momento da consulta), não uma versão aprovada para instalação: a implementação deve negociar capacidades do binário escolhido.

- **P01** [QMP reference](https://www.qemu.org/docs/master/interop/qemu-qmp-ref.html): `input-send-event`, `screendump`, `InputMoveEvent`; eventos guest, range absoluto e display/head.
- **P02** [Wolf architecture](https://games-on-whales.github.io/wolf/stable/dev/how-it-works.html): compositor por app, inputtino, dispositivos visíveis no host e regras de seat.
- **P03** [Wolf quickstart](https://games-on-whales.github.io/wolf/stable/user/quickstart.html): permissões do deployment de referência e ressalva explícita WSL2.
- **P04** [vuinputd README](https://github.com/joleuger/vuinputd): proxy CUSE e seção Production Readiness, Prototype/Alpha.
- **P05** [Linux uinput](https://docs.kernel.org/input/uinput.html): dispositivos kernel, consumidores e lifecycle; não descreve namespace de input por container.
- **P06** [Docker security](https://docs.docker.com/engine/security/): namespaces/cgroups, capabilities e risco de acesso ao daemon.
- **P07** [WSLg README](https://github.com/microsoft/wslg): integração de janelas, clipboard, RDP e DISPLAY/WAYLAND_DISPLAY.
- **P08** [Microsoft WSL USB](https://learn.microsoft.com/en-us/windows/wsl/connect-usb): bind/attach, direitos, indisponibilidade no Windows, acesso por distribuições WSL2 e regra de firewall instalada.
- **P09** [QEMU security](https://www.qemu.org/docs/master/system/security.html): política de aceleradores/máquinas, TCG e privilégios do monitor.
- **P10** [Hyper-V Enhanced Session](https://learn.microsoft.com/en-us/windows-server/virtualization/hyper-v/enhanced-session-mode): RDP, recursos compartilhados e clipboard habilitado por padrão.
- **P11** [QEMU WHPX](https://www.qemu.org/docs/master/system/whpx.html): requisitos Windows, aceleração e limitações conhecidas.
- **P12** [QMP protocol](https://www.qemu.org/docs/master/interop/qmp-spec.html): greeting, capacidades, IDs, eventos e erros estruturados.
- **P13** [Xvfb manual](https://www.x.org/releases/current/doc/man/man1/Xvfb.1.xhtml): servidor X sem display ou dispositivos físicos.
- **P14** [QEMU USB](https://www.qemu.org/docs/master/system/devices/usb.html): usb-tablet absoluto, usb-kbd e passthrough dependente do host.
- **P15** [Windows containers guidance](https://learn.microsoft.com/en-us/virtualization/windowscontainers/quick-start/lift-shift-to-containers): ausência de suporte a desktop interativo.
- **P16** [Firecracker FAQ](https://firecracker-microvm.github.io/): cinco dispositivos emulados; teclado mínimo serve a shutdown, não HID de desktop.

## 11. Decisões de aprovação antes de implementar

1. Aprovar o backend inicial QEMU e o escopo M1; informar se a primeira imagem precisa executar apps Windows nativos.
2. Aprovar origem/licença da imagem, recursos máximos e eventual rede guest. C00 informa os requisitos ausentes, sem instalá-los.
3. Autorizar separadamente qualquer provisionamento, driver, USB bind/attach e alteração de firewall.
4. Aprovar M2/M3/M4 conforme necessidade; a arquitetura não presume que todos devam entrar no mesmo release.
5. Aprovar o experimento Laya separadamente. Ganho de precisão/flexibilidade permanece hipótese até avaliação do documento complementar.
