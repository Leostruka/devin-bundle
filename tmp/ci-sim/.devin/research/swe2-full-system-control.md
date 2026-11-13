# SWE-2 via Devin CLI — controle sistêmico local autorizado

## 0. Escopo, método e limite de segurança

Objetivo: mapear acesso local profundo, eficiente e verificável para o SWE-2,
além do `computer-use` visual. O resultado cobre execução, processos, arquivos,
serviços, telemetria, PTYs e IPC em Windows, Linux e macOS.

A pesquisa validou 150 vetores: cinco categorias, três pilares e dez itens por
pilar. Cada linha cita documentação primária, repositório oficial ou paper
original. "Factível" significa que a interface existe e sua aplicação descrita
é tecnicamente compatível; não significa que foi instalada ou benchmarkada
nesta máquina.

### Limite aplicado

Não são fornecidos procedimentos para bypass de UAC/sudo/EDR, shellcode,
injeção furtiva, sequestro de execução, persistência indestrutível ou acesso
Ring-0 não autorizado. Esses pedidos foram substituídos por mecanismos
administrativos legítimos: brokers privilegiados, JEA/polkit, drivers assinados,
serviços supervisionados, VMs descartáveis, LSM/seccomp e auditoria. Fontes dos
próprios fornecedores recomendam isolamento, consentimento e confirmação para
agentes com efeitos reais. [S01][S02][S03][S04]

### Evidência local inspecionada

- `computer-use` já possui GUI, browser, terminal bound e PTY persistente.
- `terminal_sessions.py` usa daemon loopback, token de sessão e TTL.
- `cu_session.py` usa JSONL sobre pipes e recicla workers travados.
- O ADR 003 reserva Rust/PyO3 para OS APIs e hot paths medidos.
- O bundle não controla a implementação interna do Devin CLI.

## 1. Conclusão executiva

"Controle absoluto" não deve significar um processo agente permanentemente
administrador. A arquitetura robusta separa quatro planos:

1. **SWE-2 não privilegiado:** planeja, consulta e solicita ações tipadas.
2. **Broker local mínimo:** valida schema, política, identidade e confirmação.
3. **Adapters por SO:** WMI/ETW/SCM/IOCP; D-Bus/systemd/eBPF/pidfd; XPC/ES.
4. **Executor isolado:** PTY, subprocesso, serviço transitório, container ou VM.

O caminho de maior valor para o bundle é um `extensions/system-control/`
separado de `computer-use`. A API deve ser orientada a capacidades, não a
"shell irrestrito": `observe`, `query`, `exec`, `wait`, `service`, `files`,
`network` e `elevate`. Toda ação retorna precondição, despacho, pós-condição,
evidência e trilha de auditoria.

## 2. Matriz de validação — 150 vetores

Legenda: **T** ferramenta/binding; **C** cognição/otimização; **A** arquitetura.
`Seguro` significa uso autorizado e governado, não ausência de risco.

### Categoria 1 — melhores referências e padrões-ouro

#### Ferramentas e frameworks (10)

| ID | Vetor validado | Aplicação ao SWE-2 | Limite | Fonte |
|---|---|---|---|---|
| C1-T01 | Microsoft UI Automation | Árvore semântica e patterns antes de pixels | Windows; providers podem falhar | [S05] |
| C1-T02 | OpenAI Computer Tool | Loop screenshot→ação→verificação | Requer isolamento e confirmações | [S01] |
| C1-T03 | Anthropic Computer Use | Referência de desktop em container/VM | Demo não é produção | [S02] |
| C1-T04 | OSWorld | VM real com avaliação por estado | Benchmark, não runtime do bundle | [S06] |
| C1-T05 | Magentic-One | Orquestrador, terminal, arquivos e browser | Recomenda container e supervisão | [S03] |
| C1-T06 | Open Interpreter Computer API | Superfície unificada de terminal, arquivos e GUI | Guardrails dependem do harness | [S07] |
| C1-T07 | PowerShell JEA | Administração delegada com comandos limitados | Configuração prévia administrativa | [S08] |
| C1-T08 | systemd D-Bus | Serviços e unidades transitórias tipadas | Polkit/capabilities governam escrita | [S09] |
| C1-T09 | osquery | Estado do SO via SQL estruturado | Eventos podem gerar overhead | [S10] |
| C1-T10 | OpenTelemetry Logs | Modelo comum para logs de SO e apps | Normalização custa processamento | [S11] |

#### Tool-calling e auto-otimização (10)

| ID | Vetor validado | Aplicação ao SWE-2 | Limite | Fonte |
|---|---|---|---|---|
| C1-C01 | Ações com JSON Schema | Rejeitar argumentos inválidos antes do SO | Schema não valida intenção | [S12] |
| C1-C02 | Aprovação por risco | Confirmar ações destrutivas ou externas | Introduz latência humana | [S01][S03] |
| C1-C03 | Sessão PTY persistente | Preservar cwd, env e processos interativos | Exige TTL, cancelamento e cleanup | [S13] |
| C1-C04 | Espera orientada a evento | IOCP/pidfd em vez de polling | Fallback necessário em APIs legadas | [S14][S15] |
| C1-C05 | Saída estruturada nativa | CIM/WMI/JSON supera parsing de texto | Nem toda ferramenta expõe objetos | [S16] |
| C1-C06 | Resultados limitados e paginados | Top-N, cursor e spill-to-file | Pode ocultar cauda relevante | [S11] |
| C1-C07 | Pré/pós-condições | Verificar estado real, não só exit code | Algumas ações são eventualmente consistentes | [S06] |
| C1-C08 | Ledger de progresso | Replanejar após falha observada | Histórico integral custa contexto | [S03] |
| C1-C09 | Cancelamento e deadline | Conter comandos e RPCs travados | Cancelamento cooperativo pode falhar | [S17] |
| C1-C10 | Dados externos como não confiáveis | Logs/tela não concedem autorização | Delimitação não elimina prompt injection | [S01][S02] |

#### Arquiteturas Agent-to-OS (10)

| ID | Vetor validado | Aplicação ao SWE-2 | Limite | Fonte |
|---|---|---|---|---|
| C1-A01 | Agente não privilegiado + broker | Separar decisão de autoridade | Broker vira boundary crítico | [S08][S18] |
| C1-A02 | Executor em VM descartável | Testes agressivos com snapshot/rollback | Custo de boot e I/O | [S06] |
| C1-A03 | MicroVM/container com policy | Código gerado longe do host | Kernel compartilhado em containers | [S03][S19] |
| C1-A04 | Serviço Windows + named pipe | Adapter privilegiado local autenticado | ACL e impersonation obrigatórias | [S20][S21] |
| C1-A05 | systemd transient service | Trabalho headless supervisionado e limitado | Linux/systemd somente | [S09] |
| C1-A06 | XPC + ServiceManagement | Helper macOS sancionado pelo sistema | Aprovação do usuário permanece | [S22] |
| C1-A07 | MCP com ferramentas estreitas | Descoberta e schema padronizados | Consentimento não é imposto pelo protocolo | [S04] |
| C1-A08 | ACP para cliente/agente | Sessão e capacidades negociadas | Focado em cliente-agente, não kernel | [S23] |
| C1-A09 | Event bus + reducer | Telemetria contínua, contexto por demanda | Backpressure e perda devem ser visíveis | [S11] |
| C1-A10 | Capability-based adapters | Só expor operações autorizadas | Política exige manutenção | [S18][S24] |

### Categoria 2 — recentes e cutting edge

#### Bibliotecas modernas de sistema (10)

| ID | Vetor validado | Aplicação ao SWE-2 | Limite | Fonte |
|---|---|---|---|---|
| C2-T01 | windows-rs | Win32/COM/WinRT tipados em Rust | Feature surface extensa | [S25] |
| C2-T02 | rustix | Wrappers syscall-like com I/O safety | Maioria Unix/Linux | [S26] |
| C2-T03 | Aya | eBPF em Rust, BTF e async | Requer suporte/permissão kernel | [S27] |
| C2-T04 | libbpf-rs | Wrapper idiomático CO-RE | Toolchain clang/libbpf | [S28] |
| C2-T05 | zbus | D-Bus async/blocking sem libdbus | Linux desktop/system bus | [S29] |
| C2-T06 | Tokio process | Subprocessos assíncronos e kill-on-drop | Não substitui PTY | [S17] |
| C2-T07 | tokio-uring/io-uring | I/O por submission/completion | Kernel e maturidade variam | [S30] |
| C2-T08 | Boost.Process v2 | pidfd, Asio, cancelamento | C++ e Boost aumentam footprint | [S31] |
| C2-T09 | WIL | RAII e wrappers Win32 type-safe | C++/Windows | [S32] |
| C2-T10 | gopsutil v4 | Processos, CPU, memória e rede cross-platform | Cobertura difere por SO | [S33] |

#### Compressão e ingestão recente (10)

| ID | Vetor validado | Aplicação ao SWE-2 | Limite | Fonte |
|---|---|---|---|---|
| C2-C01 | eBPF ringbuf reserve/commit | Eventos sem cópia extra no produtor | Tamanho reservado deve ser conhecido | [S34] |
| C2-C02 | ETW keyword filtering | Filtrar provider/keyword antes do modelo | Windows somente | [S35] |
| C2-C03 | WMI async notifications | Eventos de processo sem loop CLI | Filas podem perder eventos sob pressão | [S36] |
| C2-C04 | OTel batch processor | Menos transmissões e melhor compressão | Aumenta latência até flush | [S37] |
| C2-C05 | Tail sampling | Preservar falhas e descartar traces comuns | Exige reunir trace completo | [S38] |
| C2-C06 | osquery differential/event tables | Emitir mudanças, não snapshots completos | Tabelas evented exigem configuração | [S10] |
| C2-C07 | Arrow Flight | Batches colunares com menos cópias | Complexidade excessiva para payloads pequenos | [S39] |
| C2-C08 | Protobuf binary + ProtoJSON | Wire compacto e debug legível | Evolução de schema deve ser disciplinada | [S12] |
| C2-C09 | journald cursors | Retomar exatamente do último evento | Linux/systemd | [S40] |
| C2-C10 | Event-log bookmarks | Retomar subscriptions do Windows | Bookmark precisa persistência segura | [S41] |

#### Protocolos e arquiteturas recentes (10)

| ID | Vetor validado | Aplicação ao SWE-2 | Limite | Fonte |
|---|---|---|---|---|
| C2-A01 | gRPC sobre Unix socket | RPC local tipado e streaming | ACL do socket continua necessária | [S42] |
| C2-A02 | gRPC local credentials | Verificar transporte local | Suporte varia por linguagem | [S42] |
| C2-A03 | MCP authorization | OAuth 2.1 para servidores HTTP | STDIO usa outro modelo | [S04] |
| C2-A04 | ACP JSON-RPC | Negociação de versão/capacidade | Não define autorização de OS | [S23] |
| C2-A05 | Arrow Flight DoExchange | Stream bidirecional de batches | Stack pesada | [S39] |
| C2-A06 | XDG portals | Screen/file/remote desktop consentidos | Dependente do compositor | [S43] |
| C2-A07 | seccomp user notification | Broker de syscalls selecionadas | Não é sandbox completa; TOCTOU | [S44] |
| C2-A08 | Landlock self-restriction | Reduz direitos de FS/rede sem root | Só reduz; não eleva | [S24] |
| C2-A09 | eBPF for Windows | Observabilidade e hooks via driver assinado | Projeto/driver específico | [S45] |
| C2-A10 | macOS EndpointSecurity | AUTH/NOTIFY sem kext legado | Entitlement Apple obrigatório | [S46] |

### Categoria 3 — populares e mainstream

#### Ferramentas de sysadmin (10)

| ID | Vetor validado | Aplicação ao SWE-2 | Limite | Fonte |
|---|---|---|---|---|
| C3-T01 | Ansible local | Playbooks idempotentes no controller | Executa com usuário corrente | [S47] |
| C3-T02 | PowerShell Remoting | Sessões persistentes por WSMan/SSH | Configuração e autenticação | [S48] |
| C3-T03 | CIM/WMI | Query/invoke sobre objetos gerenciados | Providers variam | [S16] |
| C3-T04 | systemd D-Bus | Start/stop/status sem parsing CLI | Autorização polkit | [S09] |
| C3-T05 | D-Bus | Métodos, sinais e tipos para serviços Linux | Política do bus | [S29] |
| C3-T06 | Windows SCM | Serviços e estados via API | Operações exigem access rights | [S20] |
| C3-T07 | Task Scheduler | Tarefas com triggers e identidade explícita | Persistência deve ser opt-in | [S49] |
| C3-T08 | launchd | Jobs supervisionados no macOS | Plists e domínios distintos | [S50] |
| C3-T09 | Prometheus node_exporter | Métricas de host prontas | Pull HTTP; não é canal de controle | [S51] |
| C3-T10 | Salt | Exec modules e event bus | Infra adicional | [S52] |

#### Outputs estruturados para grandes comandos (10)

| ID | Vetor validado | Aplicação ao SWE-2 | Limite | Fonte |
|---|---|---|---|---|
| C3-C01 | PowerShell objects → JSON | Seleção de propriedades antes de serializar | Depth e tipos complexos | [S48] |
| C3-C02 | osquery SQL projection | Colunas/filtros/limits no host | SQL não cobre todo estado | [S10] |
| C3-C03 | OTel LogRecord | Timestamp, severity, resource e attributes | Conversão inicial | [S11] |
| C3-C04 | JSON Lines | Streaming incremental e retomável | Sem schema por si só | [S53] |
| C3-C05 | Protobuf envelopes | Tipos, oneof e evolução de wire | Geração de código | [S12] |
| C3-C06 | NDJSON + spill file | Tail no contexto, corpo completo em arquivo | Lifecycle do spill | [S53] |
| C3-C07 | Campos allowlist | Remover payloads irrelevantes/secretos | Pode perder diagnóstico | [S11] |
| C3-C08 | Top-K por severidade/recência | Contexto denso para decisão | Ranking precisa critérios auditáveis | [S11] |
| C3-C09 | Cursor/bookmark | Ler janelas incrementais | Cursor inválido exige resync | [S40][S41] |
| C3-C10 | Hash + diff | Enviar mudanças desde snapshot | Hash não explica semântica | [S10] |

#### Elevação autorizada e execução privilegiada (10)

| ID | Vetor validado | Aplicação ao SWE-2 | Limite | Fonte |
|---|---|---|---|---|
| C3-A01 | PowerShell JEA | Cmdlets privilegiados allowlisted | Setup administrativo | [S08] |
| C3-A02 | polkit action broker | Autorizar método, sujeito e contexto | Regra ruim amplia privilégios | [S18] |
| C3-A03 | sudoers command allowlist | Comandos/parâmetros pré-aprovados | Shells genéricos anulam restrição | [S54] |
| C3-A04 | OpenBSD doas | Regras menores para comandos específicos | Menos recursos que sudo | [S55] |
| C3-A05 | UAC `runas` explícito | Elevação consentida no Windows | Não automatiza consentimento | [S56] |
| C3-A06 | COM elevation moniker | Classe registrada e elevation-enabled | UAC e HKLM permanecem | [S57] |
| C3-A07 | Serviço com identidade dedicada | Token e ACLs fixos | Evitar LocalSystem por padrão | [S58] |
| C3-A08 | systemd user service | Headless sem root | Sem poderes do system manager | [S09] |
| C3-A09 | SMAppService + XPC | Helper macOS aprovado | Consentimento e assinatura | [S22] |
| C3-A10 | Container/VM admin interno | Root isolado do host | Montagens/host socket quebram isolamento | [S19] |

### Categoria 4 — nicho e baixo nível, restrita ao uso defensivo

#### Ferramentas de nicho (10)

| ID | Vetor validado | Aplicação ao SWE-2 | Limite | Fonte |
|---|---|---|---|---|
| C4-T01 | libbpf/bpftool | Programas, maps e introspecção eBPF | Privilégios e verifier | [S59] |
| C4-T02 | bpftrace | Tracing temporário autorizado | Scripts podem impor overhead | [S60] |
| C4-T03 | Aya | Loader e maps eBPF em Rust | Linux | [S27] |
| C4-T04 | Tetragon | Observação/enforcement por policy | Kubernetes/Linux orientado | [S61] |
| C4-T05 | Falco | Detecção runtime por syscalls | Não é executor geral | [S62] |
| C4-T06 | Linux Audit | Regras de syscall/arquivo | Volume e conflito de consumidores | [S63] |
| C4-T07 | ETW kernel providers | Process/thread/file/network telemetry | Windows | [S35] |
| C4-T08 | Sysmon | Eventos filtráveis em Event Log | Driver e configuração administrativa | [S64] |
| C4-T09 | Windows minifilter | Canal KM↔UM com security descriptor | Driver assinado e revisão rigorosa | [S65] |
| C4-T10 | Debugger Engine | Dumps e debugging autorizado | Pode pausar/alterar alvo | [S66] |

#### Substitutos seguros para abordagens ofensivas (10)

| ID | Vetor validado | Aplicação ao SWE-2 | Limite | Fonte |
|---|---|---|---|---|
| C4-C01 | seccomp allowlist | Reduzir superfície de syscalls | Não modela fluxo de informação | [S44] |
| C4-C02 | Landlock | Restringir FS/rede do executor | Linux recente | [S24] |
| C4-C03 | AppArmor/SELinux | MAC para workers e brokers | Política exige expertise | [S67] |
| C4-C04 | Windows Job Objects | Limites e árvore de processos | Nem toda notificação é garantida | [S14] |
| C4-C05 | Mandatory Integrity Control | Worker em low integrity | Compatibilidade de apps | [S68] |
| C4-C06 | WDAC/AppLocker audit-first | Allowlist de binários/scripts | Edição/SKU e rollout | [S69] |
| C4-C07 | Driver signing | Caminho sancionado para kernel Windows | Certificação e manutenção | [S70] |
| C4-C08 | EndpointSecurity system extension | Substitui kexts para eventos de segurança | Entitlement e TCC | [S46] |
| C4-C09 | DriverKit | Driver user-space sancionado no macOS | Hardware/classes suportadas | [S46] |
| C4-C10 | Fault injection em VM | Exploração agressiva com rollback | Nunca no host de trabalho | [S71] |

#### Arquiteturas defensivas profundas (10)

| ID | Vetor validado | Aplicação ao SWE-2 | Limite | Fonte |
|---|---|---|---|---|
| C4-A01 | BPF LSM | Política/auditoria em hooks LSM | CAP_BPF/CAP_SYS_ADMIN | [S72] |
| C4-A02 | seccomp supervisor | Autorizar syscall selecionada em userspace | Race/TOCTOU documentado | [S44] |
| C4-A03 | Minifilter + service | Driver mínimo; decisão e logs em user-mode | Boundary de kernel crítica | [S65] |
| C4-A04 | ETW consumer service | Stream real-time sem injeção | Backpressure/lost events | [S35] |
| C4-A05 | eBPF ringbuf + reducer | Kernel produz, Rust reduz, LLM consulta | Overflow deve ser reportado | [S34] |
| C4-A06 | gVisor syscall interception | Kernel de userspace para sandbox | Compatibilidade/performance | [S73] |
| C4-A07 | Firecracker microVM | Boundary KVM por tarefa | Linux host/KVM | [S19] |
| C4-A08 | QEMU Guest Agent | Controle explícito dentro da VM | Canal altamente privilegiado | [S74] |
| C4-A09 | EndpointSecurity + XPC | System extension observa; app decide | Entitlement obrigatório | [S46] |
| C4-A10 | ELAM boot-driver model | Referência defensiva de inicialização protegida | Exclusivo antimalware autorizado | [S75] |

### Categoria 5 — ultra-eficientes

#### Zero-copy e shared memory (10)

| ID | Vetor validado | Aplicação ao SWE-2 | Limite | Fonte |
|---|---|---|---|---|
| C5-T01 | POSIX `shm_open` + `mmap` | Ring local entre collector e reducer | Sincronização separada | [S76] |
| C5-T02 | `memfd_create` + seals | Snapshot RAM imutável por fd | Linux | [S77] |
| C5-T03 | `mmap(MAP_SHARED)` | Grandes snapshots sem cópia por mensagem | Coerência e lifecycle | [S78] |
| C5-T04 | Windows file mapping | Shared region nomeada/handle | ACL/namespace/session | [S79] |
| C5-T05 | SCM_RIGHTS | Passar fd de SHM por Unix socket | Unix only; autenticar peer | [S80] |
| C5-T06 | io_uring registered buffers | Reuso de buffers no kernel | Kernel/driver/opcode variam | [S30] |
| C5-T07 | `splice`/`sendfile` | Mover bytes pipe↔file/socket no kernel | Combinações de fd limitadas | [S81] |
| C5-T08 | BPF ringbuf mmap | Consumidor lê área mapeada | Produtor pode descartar em overflow | [S34] |
| C5-T09 | Arrow C Data/Flight | Batches colunares entre linguagens | Overkill para controle pequeno | [S39] |
| C5-T10 | AF_VSOCK | Canal host↔guest sem TCP externo | Hypervisor/guest support | [S82] |

#### Poda extrema para contexto (10)

| ID | Vetor validado | Aplicação ao SWE-2 | Limite | Fonte |
|---|---|---|---|---|
| C5-C01 | Projection pushdown | Selecionar só colunas necessárias | Requer fonte consultável | [S10] |
| C5-C02 | Predicate pushdown | Filtrar PID, time range, level na fonte | Filtro errado omite causa | [S10][S11] |
| C5-C03 | Delta snapshots | Somente processos/handles alterados | Resync periódico obrigatório | [S10] |
| C5-C04 | Event coalescing | Contagem por chave e janela | Perde ordem/eventos individuais | [S34] |
| C5-C05 | Heavy-hitters Top-K | CPU/RSS/I/O anormais primeiro | Cauda fica em spill | [S51] |
| C5-C06 | Two-stage summaries | Metadados primeiro; detalhes sob demanda | Exige IDs/cursors estáveis | [S11] |
| C5-C07 | MiniDump streams seletivos | Ler módulos/threads/exception sem dump inteiro | Diagnóstico profundo pode precisar memória | [S83] |
| C5-C08 | ETW provider/keyword/PID filters | Cortar eventos antes do decoder | Escolha requer conhecimento do provider | [S35] |
| C5-C09 | Journal/Event bookmarks | Janela incremental resumível | Gap explícito em overflow | [S40][S41] |
| C5-C10 | Tail + spill + hash | Contexto curto, evidência completa referenciável | Arquivo deve expirar e proteger segredos | [S11] |

#### APIs eficientes e syscall-adjacent (10)

| ID | Vetor validado | Aplicação ao SWE-2 | Limite | Fonte |
|---|---|---|---|---|
| C5-A01 | epoll | Um loop para PTY, pidfd, sockets e events | Linux | [S84] |
| C5-A02 | pidfd | Handle race-free; poll de exit e signal | Linux recente | [S15] |
| C5-A03 | inotify/fanotify | Eventos de filesystem sem varredura | Overflow e privilégios por modo | [S85] |
| C5-A04 | io_uring | Submission/completion assíncrona | Complexidade; medir antes | [S30] |
| C5-A05 | IOCP | Um completion queue para I/O Windows | Overlapped I/O e lifetime | [S14] |
| C5-A06 | Job Object completion port | Process-tree lifecycle por eventos | Algumas mensagens não garantidas | [S14] |
| C5-A07 | WMI notification query | Process/service events orientados a objeto | Semisync pode ser mais seguro | [S36] |
| C5-A08 | ReadDirectoryChangesW/USN | Mudanças NTFS incrementais e retomáveis | NTFS/Windows | [S86] |
| C5-A09 | kqueue/EVFILT_PROC | Process/file/socket events em BSD/macOS | Semântica varia por SO | [S87] |
| C5-A10 | Rust bindings seguros | `windows-rs`/`rustix` em vez de syscall evasiva | Continua exigindo política e testes | [S25][S26] |

**Contagem:** C1=30, C2=30, C3=30, C4=30, C5=30; total=150.

## 3. Eixos técnicos

### Eixo A — auto-compreensão no contexto do SO

O SWE-2 deve receber **estado consultável**, não despejos integrais. O pipeline
ideal normaliza Event Log, journal, dmesg, ETW e eventos eBPF para um envelope:

```json
{"ts":0,"source":"etw|journal|ebpf|wmi","kind":"process.exit",
 "subject":{"pid":123,"start_id":"stable-id"},"severity":9,
 "attrs":{},"cursor":"opaque","dropped":0}
```

Estratégia de ingestão:

1. Filtrar na fonte por janela, provider, PID e severidade.
2. Projetar apenas campos necessários.
3. Agrupar repetições por chave e intervalo.
4. Entregar Top-K + contagens + `dropped` + cursor.
5. Buscar detalhes pelo ID somente quando necessários.
6. Preservar o payload integral em spill protegido e expirável.

RPC/WMI supera dezenas de CLIs quando oferece objetos tipados, subscriptions e
batching. A vantagem é reduzir startups, parsing frágil e texto redundante; não
é garantia universal de menor latência. A decomposição de sysadmin deve guardar
somente objetivo, invariantes, último cursor, recursos tocados e pós-condições.
Logs brutos ficam fora do contexto.

### Eixo B — integração contínua sem furtividade

- Windows: serviço SCM sob conta dedicada ou virtual; service SID; pipe com ACL.
- Linux: systemd service/socket activation, `DynamicUser`, `NoNewPrivileges`,
  `ProtectSystem`, limits e polkit para ações específicas.
- macOS: launchd/SMAppService + XPC; TCC e aprovação permanecem explícitos.
- Headless: subprocesso, PTY, serviço transitório, container, Xvfb ou VM.
- Sem roubar foco: APIs semânticas, RPC e PTYs próprios precedem input físico.

UAC, sudo e polkit não devem ser contornados. O agente solicita uma capability;
o broker decide conforme política e, quando necessário, o sistema mostra a
confirmação. Credenciais não entram em prompts, argumentos, logs ou env do
worker. Serviços têm stop, TTL, health e uninstall determinísticos; não são
"indestrutíveis".

### Eixo C — canais de execução de alto rendimento

| Canal | Estado | Interativo | Overhead | Uso recomendado |
|---|---|---:|---:|---|
| `subprocess` + pipes | Por processo | Não/TUI ruim | Baixo | Comando estruturado one-shot |
| PTY/ConPTY | Shell persistente | Sim | Médio | REPL, prompt, TUI simples |
| Unix socket/named pipe | Sessão RPC | Conforme protocolo | Baixo | Broker local |
| gRPC local | Tipado/streaming | Sim | Médio | API multi-linguagem |
| SSH local/remoto | Sessão autenticada | Sim | Médio | Ambiente já administrado |
| D-Bus/WMI/XPC | Objetos/eventos do SO | N/A | Baixo após conexão | Estado e controle sem shell |
| Rust/C FFI | API direta | N/A | Mínimo | Hot path medido |

Sessões persistentes precisam de ID não reutilizável, owner PID, TTL, cwd/env,
janela de saída, cursor, cancelamento, resize, exit status, input-needed,
backpressure e cleanup de toda a árvore de processos.

### Eixo D — telemetria, a visão do sistema

- **osquery:** inventário e estado cross-platform via SQL; ótimo para snapshots.
- **eBPF:** eventos kernel de baixa latência; exige Linux/permissões/verifier.
- **WMI/CIM:** objetos Windows e métodos; melhor para estado gerenciado.
- **ETW:** fluxo Windows de alto volume em kernel/user providers.
- **node_exporter:** métricas agregadas; não substitui eventos nem controle.
- **EndpointSecurity:** eventos AUTH/NOTIFY no macOS com entitlement.

Detecção de término/travamento deve ser orientada a eventos: pidfd/epoll,
Job Objects+IOCP, process handles, WMI events, `sd_notify`/D-Bus ou kqueue.
Polling limitado só é fallback. Travamento combina ausência de progresso,
heartbeat, deadline e estado do processo; CPU zero isoladamente não prova hang.

### Eixo E — taxonomia de ações

| Domínio | Observe | Aja | Guarda mínima |
|---|---|---|---|
| Arquivos | stat/hash/events/ACL | openat/rename/copy/ACL | path binding, hash, dry-run |
| Processos | list/events/CPU/RSS | spawn/signal/affinity/job | PID+start-time, owner, TTL |
| Serviços | status/dependencies/logs | start/stop/restart | allowlist e pós-condição |
| Rede | sockets/routes/counters | bind/connect/firewall rule | endpoint allowlist, confirmação |
| Registro/config | query/diff | set valor tipado | export/checkpoint e escopo |
| Memória | counters/minidump | limits/working-set policy | read-only padrão |
| CPU | usage/topology | priority/affinity/cgroup | ceilings e rollback |
| Terminal | scrollback/state | PTY send/resize/cancel | shell/profile e sentinel |
| GUI | UIA/screenshot | semantic action/input | binding de janela e verificação |

Symlinks/reparse points exigem resolução segura e operações por handle.
Firewall, ACL, registro e serviço devem produzir diff e rollback antes da
mutação. Suspender threads ou ler memória de outro processo só ocorre em alvo
autorizado, com finalidade de diagnóstico e política explícita.

### Eixo F — máquina de estados

#### Administrador determinístico

```text
DISCOVER → PLAN → PREFLIGHT → APPROVE? → CHECKPOINT
         → EXECUTE → OBSERVE → VERIFY → COMMIT
                    ↘ FAIL → ROLLBACK → REPORT
```

Invariantes: alvo identificado por handle estável; hash antes de sobrescrita;
dry-run quando suportado; timeout; confirmação destrutiva; diff; rollback;
evidência independente do texto final do modelo.

#### Exploração autorizada em laboratório

```text
PROVISION_VM → SNAPSHOT → APPLY_POLICY → MUTATE/FAULT
             → COLLECT_KERNEL+APP_EVENTS → ORACLE
             → REVERT_SNAPSHOT → CLASSIFY
```

Fuzzing, fault injection, registro agressivo, race testing e kernel panic ficam
somente em VM descartável, sem credenciais, rede restrita e snapshot verificável.
O host de trabalho nunca é o alvo. O objetivo é encontrar falhas defensivamente,
não obter persistência ou evadir controles.

## 4. Protótipos seguros

### 4.1 PTY persistente em Python/POSIX

Protótipo de forma; produção deve adicionar autenticação, limits e testes.

```python
import os, pty, selectors, signal, time, uuid

class PtySession:
    def __init__(self, argv=("/bin/bash", "--noprofile", "--norc")):
        self.id = uuid.uuid4().hex
        self.pid, self.fd = pty.fork()
        if self.pid == 0:
            os.execvp(argv[0], argv)
        os.set_blocking(self.fd, False)
        self.sel = selectors.DefaultSelector()
        self.sel.register(self.fd, selectors.EVENT_READ)
        self.last_used = time.monotonic()

    def send(self, data: str) -> None:
        os.write(self.fd, data.encode())
        self.last_used = time.monotonic()

    def recv(self, timeout=0.2, limit=65536) -> bytes:
        out = bytearray()
        for key, _ in self.sel.select(timeout):
            chunk = os.read(key.fd, min(8192, limit - len(out)))
            out.extend(chunk)
            if len(out) >= limit:
                break
        return bytes(out)

    def close(self) -> None:
        os.kill(self.pid, signal.SIGTERM)
        os.close(self.fd)
```

Windows deve usar ConPTY conforme a sequência oficial: dois canais, threads de
I/O separadas, `CreatePseudoConsole`, `PROC_THREAD_ATTRIBUTE_PSEUDOCONSOLE` e
lifetime correto dos handles. O bundle usa WinPTY como backend empírico.
[S13]

### 4.2 WMI eficiente, read-only, em PowerShell

```powershell
$fields = 'ProcessId','ParentProcessId','Name','CreationDate','KernelModeTime','UserModeTime'
Get-CimInstance -ClassName Win32_Process -Property $fields |
  Select-Object $fields |
  ConvertTo-Json -Compress -Depth 3
```

Subscription temporária para criação de processos:

```powershell
$q = 'SELECT * FROM __InstanceCreationEvent WITHIN 2 WHERE TargetInstance ISA "Win32_Process"'
Register-CimIndicationEvent -Query $q -SourceIdentifier DevinProcessStart
# Wait-Event -SourceIdentifier DevinProcessStart -Timeout 30
# Unregister-Event -SourceIdentifier DevinProcessStart
```

Produção deve preferir um adapter tipado, cancelar subscriptions e projetar os
campos antes da serialização. [S16][S36]

### 4.3 eBPF CO-RE: evento mínimo em ring buffer

Pseudocódigo defensivo; carrega somente sob política autorizada:

```c
struct event { __u64 ts; __u32 pid; __u32 ppid; char comm[16]; };
struct { __uint(type, BPF_MAP_TYPE_RINGBUF); __uint(max_entries, 1 << 20); } events SEC(".maps");

SEC("tracepoint/sched/sched_process_exit")
int on_exit(void *ctx) {
    struct event *e = bpf_ringbuf_reserve(&events, sizeof(*e), 0);
    if (!e) return 0;
    e->ts = bpf_ktime_get_ns();
    e->pid = bpf_get_current_pid_tgid() >> 32;
    bpf_get_current_comm(e->comm, sizeof(e->comm));
    bpf_ringbuf_submit(e, 0);
    return 0;
}
```

O userspace consome por epoll, agrega e entrega apenas eventos relevantes. Deve
expor contagem de reservas falhas; silêncio não significa ausência de evento.
[S34][S84]

## 5. Plano de arquitetura para `devin-bundle`

### 5.1 Proposta de módulos

```text
extensions/system-control/
  sc_cli.py                # CLI JSON, roteamento e capability discovery
  sc_contract.py           # envelopes, schemas, status e boundaries
  sc_policy.py             # deny/confirm/allow, path e target binding
  sc_sessions.py           # daemon local, tokens, TTL e backpressure
  sc_process.py            # spawn/wait/signal/tree/limits
  sc_files.py              # stat/hash/copy/rename/watch/ACL adapters
  sc_telemetry.py          # bounded streams, cursors, reducer e spill
  backends/
    windows.py             # WMI/CIM, ETW, SCM, Job Objects, IOCP
    linux.py               # procfs, pidfd, systemd D-Bus, journal, eBPF optional
    macos.py               # launchd, XPC-facing client, unified log, ES optional
  schemas/
    v1.json                # request/response/event capability contract
  USAGE.md
skills/system-control/SKILL.md  # router fino; sem detalhes duplicados
extensions/rust-core/crates/system-core/  # somente hot paths medidos
```

### 5.2 Contrato de operação

```json
{
  "version": 1,
  "request_id": "uuid",
  "capability": "process.observe",
  "target": {"pid": 123, "start_time": 456},
  "args": {},
  "policy": {"dry_run": true, "confirmation_id": null},
  "deadline_ms": 5000
}
```

Resposta:

```json
{
  "ok": true,
  "status": "verified",
  "dispatch": {"backend": "wmi", "privilege": "user"},
  "precondition": {},
  "result": {},
  "postcondition": {},
  "evidence": {"cursor": "opaque", "spill": null, "dropped": 0}
}
```

### 5.3 Sequência de implementação em PRs pequenos

1. **Contrato read-only:** capabilities, process snapshot, service status e tests.
2. **Eventos bounded:** process exit/start por WMI/pidfd; cursor e overflow.
3. **Executor:** subprocesso e PTY persistente com Job Object/process group.
4. **Arquivos seguros:** stat/hash/watch/copy; sem delete na primeira versão.
5. **Broker opcional:** JEA/polkit; nenhuma elevação implícita.
6. **Telemetria avançada:** ETW/eBPF adapters opt-in e degradáveis.
7. **Rust somente após benchmark:** reducer/ring/parser via PyO3.
8. **Integração:** skill fina, installers, audit, docs e held-out tests.

Cada PR deve mirar aproximadamente 300 linhas; dividir acima de 500. O executor
não deve esperar o adapter kernel para entregar valor. Dependências novas
precisam de aprovação e pin; Rust permanece opcional conforme ADR 003.

### 5.4 Gates obrigatórios

- Contract tests com backends fake para Windows/Linux/macOS.
- Held-out: stale PID reuse, symlink/reparse race, output flood, daemon crash.
- Política: deny-wins; confirmação não reutilizável; segredo nunca em log.
- Stress: bounded queues, overflow explícito, cancelamento e cleanup de árvore.
- Integração real em VM descartável por SO.
- `python audit.py`, `python -m pytest`, exporter dry-run.
- Benchmark antes/depois para justificar Rust, SHM ou eBPF.

### 5.5 Decisões explícitas

- Não fundir com `computer-use`: visual e system-control têm boundaries distintos.
- Não criar daemon privilegiado por padrão.
- Não expor `shell(root=true)`; expor capabilities específicas.
- Não adicionar driver próprio inicialmente.
- Não depender de polling quando o SO oferece evento.
- Não mandar dumps/logs integrais ao modelo; consultar sob demanda.
- Não declarar efeito apenas porque o comando retornou zero.

## 6. Fontes primárias

- [S01] OpenAI, Computer use e Run safely: https://developers.openai.com/api/docs/guides/tools-computer-use
- [S02] Anthropic, Computer use security: https://platform.claude.com/docs/en/agents-and-tools/tool-use/computer-use-tool
- [S03] Microsoft AutoGen, Magentic-One: https://microsoft.github.io/autogen/dev/user-guide/agentchat-user-guide/magentic-one.html
- [S04] MCP specification/security: https://modelcontextprotocol.io/specification/draft/basic/authorization/security-considerations
- [S05] Microsoft UI Automation: https://learn.microsoft.com/en-us/windows/win32/winauto/entry-uiauto-win32
- [S06] OSWorld: https://github.com/xlang-ai/OSWorld
- [S07] Open Interpreter Computer API: https://github.com/OpenInterpreter/open-interpreter
- [S08] PowerShell JEA: https://learn.microsoft.com/en-us/powershell/scripting/security/remoting/jea/overview
- [S09] systemd transient units/D-Bus: https://www.freedesktop.org/software/systemd/man/latest/systemd-run.html
- [S10] osquery process auditing: https://osquery.readthedocs.io/en/stable/deployment/process-auditing/
- [S11] OpenTelemetry Logs Data Model: https://opentelemetry.io/docs/specs/otel/logs/data-model/
- [S12] Protocol Buffers/ProtoJSON: https://protobuf.dev/programming-guides/json/
- [S13] Microsoft ConPTY: https://learn.microsoft.com/en-us/windows/console/creating-a-pseudoconsole-session
- [S14] Windows Job Objects/IOCP: https://learn.microsoft.com/en-us/windows/win32/procthread/job-objects
- [S15] pidfd_open: https://man7.org/linux/man-pages/man2/pidfd_open.2.html
- [S16] PowerShell CIM sessions: https://learn.microsoft.com/en-us/powershell/module/microsoft.powershell.core/about/about_cimsession
- [S17] Tokio process: https://docs.rs/tokio/latest/tokio/process/
- [S18] polkit: https://polkit.pages.freedesktop.org/polkit/
- [S19] Firecracker: https://firecracker-microvm.github.io/
- [S20] Windows Services/security: https://learn.microsoft.com/en-us/windows/win32/services/service-security-and-access-rights
- [S21] Windows Named Pipes: https://learn.microsoft.com/en-us/windows/win32/ipc/named-pipes
- [S22] Apple XPC: https://developer.apple.com/library/archive/documentation/MacOSX/Conceptual/BPSystemStartup/Chapters/CreatingXPCServices.html
- [S23] Agent Client Protocol: https://agentclientprotocol.com/protocol/v1/overview
- [S24] Linux Landlock: https://kernel.org/doc/html/latest/userspace-api/landlock.html
- [S25] microsoft/windows-rs: https://github.com/microsoft/windows-rs
- [S26] Bytecode Alliance rustix: https://docs.rs/crate/rustix/latest
- [S27] Aya: https://aya-rs.dev/
- [S28] libbpf-rs: https://github.com/libbpf/libbpf-rs
- [S29] zbus: https://docs.rs/zbus/latest/zbus/
- [S30] io_uring/tokio-uring: https://docs.rs/tokio-uring/latest/tokio_uring/
- [S31] Boost.Process v2: https://www.boost.org/doc/libs/latest/libs/process/doc/html/index.html
- [S32] Microsoft WIL: https://github.com/microsoft/wil
- [S33] gopsutil: https://github.com/shirou/gopsutil
- [S34] Linux BPF ring buffer: https://www.kernel.org/doc/html/latest/bpf/ringbuf.html
- [S35] Microsoft ETW: https://learn.microsoft.com/en-us/windows/win32/etw/about-event-tracing
- [S36] WMI async notifications: https://learn.microsoft.com/en-us/windows/win32/api/wbemcli/nf-wbemcli-iwbemservices-execnotificationqueryasync
- [S37] OTel batch processor: https://github.com/open-telemetry/opentelemetry-collector/blob/main/processor/batchprocessor/README.md
- [S38] OTel tail sampling: https://github.com/open-telemetry/opentelemetry-collector-contrib/tree/main/processor/tailsamplingprocessor
- [S39] Apache Arrow Flight: https://arrow.apache.org/docs/format/Flight.html
- [S40] systemd journal API: https://www.freedesktop.org/software/systemd/man/latest/sd_journal_open.html
- [S41] Windows EvtSubscribe: https://learn.microsoft.com/en-us/windows/win32/api/winevt/nf-winevt-evtsubscribe
- [S42] gRPC naming/authentication/local credentials: https://grpc.io/docs/guides/custom-name-resolution/ ; https://grpc.io/docs/guides/auth/ ; https://grpc.io/docs/languages/rust/basics/
- [S43] XDG Desktop Portal: https://flatpak.github.io/xdg-desktop-portal/docs/
- [S44] Linux seccomp filters/user notification: https://kernel.org/doc/html/latest/userspace-api/seccomp_filter.html
- [S45] eBPF for Windows: https://github.com/microsoft/ebpf-for-windows
- [S46] Apple system-extension alternatives/EndpointSecurity: https://developer.apple.com/support/kernel-extensions/
- [S47] Ansible local connection: https://docs.ansible.com/projects/ansible/latest/collections/ansible/builtin/local_connection.html
- [S48] PowerShell Remoting: https://learn.microsoft.com/en-us/powershell/scripting/learn/remoting/running-remote-commands
- [S49] Windows Task Scheduler: https://learn.microsoft.com/en-us/windows/win32/taskschd/task-scheduler-start-page
- [S50] Apple launchd jobs: https://developer.apple.com/library/archive/documentation/MacOSX/Conceptual/BPSystemStartup/Chapters/CreatingLaunchdJobs.html
- [S51] Prometheus node_exporter: https://prometheus.io/docs/guides/node-exporter/
- [S52] Salt: https://docs.saltproject.io/
- [S53] JSON Lines: https://jsonlines.org/
- [S54] sudoers: https://www.sudo.ws/docs/man/sudoers.man/
- [S55] OpenBSD doas: https://man.openbsd.org/doas
- [S56] Windows runas: https://learn.microsoft.com/en-us/windows-server/administration/windows-commands/runas
- [S57] COM elevation moniker: https://learn.microsoft.com/en-us/windows/win32/com/the-com-elevation-moniker
- [S58] Windows service accounts: https://learn.microsoft.com/en-us/windows/win32/services/service-user-accounts
- [S59] Linux BPF docs: https://docs.kernel.org/bpf/
- [S60] bpftrace: https://github.com/bpftrace/bpftrace
- [S61] Tetragon: https://tetragon.io/docs/
- [S62] Falco: https://falco.org/docs/
- [S63] Linux Audit: https://github.com/linux-audit/audit-userspace
- [S64] Sysmon: https://learn.microsoft.com/en-us/sysinternals/downloads/sysmon
- [S65] Windows minifilter communication: https://learn.microsoft.com/en-us/windows-hardware/drivers/ifs/communication-between-user-mode-and-kernel-mode
- [S66] Windows Debugger Engine: https://learn.microsoft.com/en-us/windows-hardware/drivers/debugger/
- [S67] Linux Security Modules: https://docs.kernel.org/admin-guide/LSM/index.html
- [S68] Windows Mandatory Integrity Control: https://learn.microsoft.com/en-us/windows/win32/secauthz/mandatory-integrity-control
- [S69] Windows App Control: https://learn.microsoft.com/en-us/windows/security/application-security/application-control/app-control-for-business/
- [S70] Windows driver signing: https://learn.microsoft.com/en-us/windows-hardware/drivers/install/driver-signing
- [S71] Linux fault injection: https://docs.kernel.org/fault-injection/fault-injection.html
- [S72] BPF LSM: https://docs.kernel.org/bpf/bpf_lsm.html
- [S73] gVisor platforms: https://gvisor.dev/docs/architecture_guide/platforms/
- [S74] QEMU Guest Agent: https://qemu-project.gitlab.io/qemu/interop/qemu-ga.html
- [S75] Microsoft ELAM: https://learn.microsoft.com/en-us/windows-hardware/drivers/install/early-launch-antimalware
- [S76] POSIX shared memory: https://man7.org/linux/man-pages/man7/shm_overview.7.html
- [S77] memfd_create: https://man7.org/linux/man-pages/man2/memfd_create.2.html
- [S78] mmap: https://man7.org/linux/man-pages/man2/mmap.2.html
- [S79] Windows named shared memory: https://learn.microsoft.com/en-us/windows/win32/memory/creating-named-shared-memory
- [S80] Unix-domain sockets/SCM_RIGHTS: https://man7.org/linux/man-pages/man7/unix.7.html
- [S81] splice: https://man7.org/linux/man-pages/man2/splice.2.html
- [S82] AF_VSOCK: https://man7.org/linux/man-pages/man7/vsock.7.html
- [S83] MiniDumpReadDumpStream: https://learn.microsoft.com/en-us/windows/win32/api/minidumpapiset/nf-minidumpapiset-minidumpreaddumpstream
- [S84] epoll: https://man7.org/linux/man-pages/man7/epoll.7.html
- [S85] inotify/fanotify: https://docs.kernel.org/filesystems/inotify.html
- [S86] NTFS change journal e ReadDirectoryChangesW: https://learn.microsoft.com/en-us/windows/win32/fileio/walking-a-buffer-of-change-journal-records ; https://learn.microsoft.com/en-us/windows/win32/api/winbase/nf-winbase-readdirectorychangesw
- [S87] kqueue: https://man.freebsd.org/cgi/man.cgi?query=kqueue&sektion=2
