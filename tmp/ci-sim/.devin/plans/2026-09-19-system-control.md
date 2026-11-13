# System Control Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use /dispatching-parallel-agents (recommended) or /executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Entregar ao SWE-2 controle sistêmico local autorizado, tipado, observável e verificável, separado do `computer-use` visual.

**Architecture:** O SWE-2 permanece não privilegiado e chama capabilities estreitas através de uma CLI JSON. Um contrato versionado, uma política deny-wins e adapters por SO separam intenção, autoridade e execução. Operações de leitura funcionam sem daemon; sessões e streams usam um daemon local autenticado por token, com TTL, backpressure e cleanup.

**Tech Stack:** Python 3.9+ stdlib, pytest, Win32/WMI/ETW quando disponível, procfs/pidfd/systemd no Linux, launchd/unified log no macOS, Rust/PyO3 apenas após benchmark aprovado.

## Global Constraints

- Separar `extensions/system-control/` de `extensions/computer-use/`.
- Não alterar a implementação interna do Devin CLI.
- Não expor `shell(root=true)` nem elevação implícita.
- UAC, sudo e polkit permanecem explícitos e consentidos.
- Nenhum daemon privilegiado por padrão.
- Dependências novas exigem aprovação e versão pinada.
- Python stdlib primeiro; Rust somente após gargalo medido.
- stdout contém exatamente um objeto JSON; diagnósticos vão para stderr.
- Dados de OS, logs e saída de processo são conteúdo não confiável.
- Segredos nunca entram em prompts, argumentos, logs, spills ou artefatos.
- Operações destrutivas não fazem parte da primeira versão.
- Todo target de processo usa `pid + start_time`, nunca PID isolado.
- Toda fila é limitada; overflow retorna `dropped > 0`.
- Toda sessão tem owner, token, geração, TTL, deadline e cleanup.
- Toda mutação retorna precondição, despacho, pós-condição e evidência.
- Cada PR mira ~300 linhas; dividir obrigatoriamente acima de 500.
- Gates finais: `python audit.py`, `python -m pytest`, exporter dry-run.

## Success Criteria

1. `sc_cli.py capabilities` descobre somente capabilities suportadas no host.
2. Processos e serviços podem ser observados sem shell ou GUI.
3. Execução one-shot e persistente não deixa árvore órfã após cancelamento.
4. Eventos são resumidos, paginados e retomáveis por cursor.
5. Arquivos podem ser inspecionados, verificados e copiados com segurança.
6. Ações sensíveis exigem confirmação one-shot vinculada ao request digest.
7. Windows, Linux e macOS degradam explicitamente quando uma API falta.
8. Instalação, skill, manifest, documentação e auditoria permanecem sincronizados.
9. ETW/eBPF/Rust somente entram após benchmark e decisão registrada.

## Proposed Modules and Interfaces

### Living assets

| Path | Responsibility |
|---|---|
| `extensions/system-control/sc_cli.py` | CLI JSON e roteamento de operações |
| `extensions/system-control/sc_contract.py` | Requests, responses, targets e validação v1 |
| `extensions/system-control/sc_policy.py` | allow/confirm/deny, confirmation digest e TTL |
| `extensions/system-control/sc_backend.py` | Seleção de backend e capability discovery |
| `extensions/system-control/sc_process.py` | Snapshot, spawn, wait, cancel e árvore |
| `extensions/system-control/sc_sessions.py` | Daemon local, token, geração, TTL e bounded buffers |
| `extensions/system-control/sc_files.py` | stat, hash e safe-copy |
| `extensions/system-control/sc_telemetry.py` | Eventos, cursor, reducer, spill e overflow |
| `extensions/system-control/backends/__init__.py` | Package e protocolo comum dos adapters |
| `extensions/system-control/backends/windows.py` | WMI/Win32/SCM/Event Log; ETW opcional posterior |
| `extensions/system-control/backends/linux.py` | procfs/pidfd/systemd/journal; eBPF opcional posterior |
| `extensions/system-control/backends/macos.py` | process/launchd/unified log; ES opcional posterior |
| `extensions/system-control/sc_windows.py` | Seams ctypes/Win32 isolados e injetáveis |
| `extensions/system-control/sc_broker.py` | Cliente para brokers privilegiados opt-in |
| `extensions/system-control/sc_bench.py` | Harness reprodutível de latência e throughput |
| `extensions/system-control/schemas/v1.json` | Contrato request/response/event versionado |
| `extensions/system-control/USAGE.md` | Contrato operacional detalhado |
| `skills/system-control/SKILL.md` | Router fino para a extensão |
| `tests/test_sc_*.py` | Contract e integration tests com seams fake |
| `tests/validation/test_system_control_workflow.py` | Contrato distributivo e workflow principal |

### Deferred assets

| Path | Creation gate |
|---|---|
| `extensions/rust-core/crates/system-core/` | Somente se benchmark comprovar gargalo relevante |
| `extensions/system-control/brokers/` | Somente após adapters não privilegiados estáveis |
| ETW real-time/eBPF/EndpointSecurity loaders | Opt-in; dependem de suporte e autorização do host |

### Core contracts

| Module | Exact interface |
|---|---|
| `sc_contract.py` | `validate_request(value: dict) -> dict`; `target(pid: int, start_time: int) -> dict`; `result(*, ok: bool, status: str, request_id: str, backend: str, privilege: str = "user", precondition=None, value=None, postcondition=None, cursor=None, spill=None, dropped: int = 0, error=None) -> dict`; `untrusted(value) -> dict` |
| `sc_backend.py` | `BackendUnavailable(RuntimeError)`; `current() -> object`; `capabilities(backend=None) -> list[dict]`; backend methods: `capabilities() -> list[dict]`, `process_list(pid=None) -> list[dict]`, `process_get(pid: int, start_time=None) -> dict`, `wait_process(target: dict, timeout_s: float) -> dict`, `service_status(name: str) -> dict`, optional `restart_service(name: str) -> dict`, optional `open_events(kind: str, filters: dict, emit: Callable[[dict], None]) -> object` |
| `sc_policy.py` | `request_digest(request: dict) -> str`; `classify(request: dict) -> dict`; `issue_confirmation(request: dict, ttl_s: int = 120) -> dict`; `consume_confirmation(request: dict, confirmation_id: str) -> dict` |
| `sc_process.py` | `snapshot(*, pid=None, limit=100, backend=None) -> dict`; `spawn(argv: list[str], *, cwd=None, env_allow=None, timeout_s=30, output_limit=16000, spill_dir=None, backend=None) -> dict`; `wait(handle: dict, *, timeout_s=30, backend=None) -> dict`; `cancel(handle: dict, *, grace_s=2, backend=None) -> dict` |
| `sc_sessions.py` | `start_daemon() -> dict`; `daemon_status() -> dict`; `spawn_session(argv: list[str], *, cwd=None, capacity=2048) -> dict`; `send(session: dict, data: str) -> dict`; `recv(session: dict, *, cursor=None, limit=200, tail=None, wait=None, timeout_s=10) -> dict`; `resize(session: dict, cols: int, rows: int) -> dict`; `close(session: dict) -> dict`; `cancel(session: dict) -> dict` |
| `sc_telemetry.py` | `normalize(raw: dict, *, source: str, kind: str) -> dict`; `open_stream(kind: str, filters: dict, *, capacity=2048, backend=None) -> dict`; `drain(stream_id: str, *, cursor=None, limit=200) -> dict`; `close_stream(stream_id: str) -> dict`; `reduce_events(events: list[dict], *, top_k=20) -> dict` |
| `sc_files.py` | `inspect_path(root: str, relative: str, *, hash_name="sha256") -> dict`; `copy_verified(root: str, src: str, dst: str, *, expected_hash=None, overwrite=False) -> dict` |
| `sc_broker.py` | `broker_status() -> dict`; `broker_preflight(request: dict) -> dict`; `dispatch(request: dict, *, io=None) -> dict` |
| `sc_bench.py` | `run(operation, *, runs: int, warmup: int, clock) -> dict`; `run_scenario(name: str, *, runs=30) -> dict` |

`SCHEMA_VERSION = 1`. Statuses permitidos: `dispatched`, `verified`, `rejected`, `timeout`, `unknown`, `cancelled`. `result()` sempre materializa `evidence:{cursor,spill,dropped}`; campos ausentes recebem `null`, `null` e `0`. Cada capability entry usa `{name,supported,reason,mode}`. Funções dos módulos de backend aceitam `io=None` como seam keyword-only; produção resolve o mapping nativo padrão, testes injetam fakes.

## State Machines

### Deterministic operation

```text
DISCOVER → PLAN → PREFLIGHT → APPROVE? → CHECKPOINT
         → EXECUTE → OBSERVE → VERIFY → COMMIT
                    ↘ FAIL → ROLLBACK → REPORT
```

### Session lifecycle

```text
ABSENT → STARTING → READY → ACTIVE → IDLE → EXPIRED → CLOSED
                     ↘ HUNG → TERMINATING → CLOSED
```

Transitions reject stale `{session, generation}` envelopes. `EXPIRED`, `HUNG` and daemon shutdown terminate all owned processes.

## Delivery DAG

```text
T1 Read-only inventory
 ├─→ T2 Policy confirmations
 ├─→ T3 One-shot execution → T4 Persistent sessions
 └─→ T5 Bounded telemetry
T2 → T6 Safe files
T2+T3+T5 → T7 Windows deep adapter
T1+T5        → T8 Linux adapter
T1+T5        → T9 macOS adapter
T2+T7+T8+T9  → T10 Optional privileged brokers
T5+T7+T8+T9  → T11 Benchmark and optional native acceleration
T1..T11      → T12 Bundle integration and release gate
```

## QA-only precondition

Before T1 starts, the lead or `qa-ci` author creates these held-out assets in an isolated QA worktree. Implementer profiles may neither read nor edit them:

- `tests/held-out/system-control/test_identity_and_confirmation.py`
- `tests/held-out/system-control/test_paths_and_output.py`
- `tests/held-out/system-control/test_daemon_recovery.py`

The private cases cover stale PID identity, confirmation replay/mutation, symlink or reparse swap, source mutation during copy, output flood, cursor overflow and daemon crash cleanup. The lead commits the tests without sharing their bodies with implementers. Test modules defer System Control imports into test functions, so collection succeeds before T1. After each task, `qa-ci` runs the relevant held-out file on a clean checkout; a failing held-out gate blocks completion.

Held-out setup gate: `python -m pytest tests/held-out/system-control --collect-only -q`
Expected before implementation: exit 0; every QA-owned test collects without syntax or fixture errors. Functional execution begins after its blocking task lands.

---

### Task 1: User can inspect host capabilities, processes and services read-only

**Estimated size:** 300–450 lines. Split contract/backend tests from docs if >500.

**Files:**
- Create (living): `extensions/system-control/sc_contract.py`
- Create (living): `extensions/system-control/sc_backend.py`
- Create (living): `extensions/system-control/sc_process.py`
- Create (living): `extensions/system-control/sc_cli.py`
- Create (living): `extensions/system-control/backends/{__init__,windows,linux,macos}.py`
- Create (living): `extensions/system-control/schemas/v1.json`
- Create (living): `tests/test_sc_contract.py`
- Create (living): `tests/test_sc_inventory.py`
- Create (living): `tests/test_sc_cli.py`

**Interfaces:** Produces `validate_request`, `result`, `current`, `capabilities`, `snapshot`; CLI `capabilities`, `process-list`, `process-get`, `service-status`.

- [ ] **Step 1: Write contract tests**

```python
def test_response_distinguishes_dispatch_from_verification():
    r = contract.result(ok=True, status="dispatched", request_id="r1", backend="fake")
    assert r["ok"] is True
    assert r["status"] == "dispatched"
    assert "postcondition" in r


def test_process_target_requires_start_time():
    with pytest.raises(ValueError, match="start_time"):
        contract.validate_request({
            "version": 1, "request_id": "r1",
            "capability": "process.observe", "target": {"pid": 12},
            "args": {}, "deadline_ms": 1000,
        })
```

- [ ] **Step 2: Write fake-backend inventory tests**

```python
class FakeBackend:
    name = "fake"
    def capabilities(self):
        return [
            {"name": "process.observe", "supported": True, "reason": None, "mode": "native"},
            {"name": "service.observe", "supported": True, "reason": None, "mode": "native"},
        ]
    def process_list(self, pid=None):
        return [{"pid": 7, "start_time": 99, "name": "worker"}]
    def process_get(self, pid, start_time=None):
        return self.process_list(pid)[0]
    def service_status(self, name):
        return {"name": name, "state": "running"}


def test_snapshot_is_bounded_and_typed():
    r = process.snapshot(limit=1, backend=FakeBackend())
    assert r["status"] == "verified"
    assert r["value"] == [{"pid": 7, "start_time": 99, "name": "worker"}]
```

- [ ] **Step 3: Run RED gate**

Run: `python -m pytest tests/test_sc_contract.py tests/test_sc_inventory.py tests/test_sc_cli.py -q`
Expected: FAIL because `system-control` modules do not exist.

- [ ] **Step 4: Implement schema and manual stdlib validation**

Implement required keys: `version`, `request_id`, `capability`, `args`, `deadline_ms`; require `target.pid` and `target.start_time` together; reject unknown schema versions; cap `deadline_ms` at 300000; reject non-dict `args`.

- [ ] **Step 5: Implement backend discovery**

`platform.system()` selects `windows`, `linux` or `macos`. Import failure returns a typed unsupported capability, never a fallback shell command.

- [ ] **Step 6: Implement read-only OS adapters**

Use stdlib surfaces only:
- Windows: process snapshot via `Get-CimInstance` JSON subprocess only as the initial seam; service status via `sc.exe query` parser is allowed only behind backend tests until native API lands in T7.
- Linux: `/proc/<pid>/stat` plus boot-relative start ticks; service observation only when systemd is detected.
- macOS: `ps -axo pid,lstart,comm` bounded projection; `launchctl print` only for an explicit label.

Every external command receives argument arrays, `shell=False`, timeout and output cap.

- [ ] **Step 7: Implement CLI JSON contract**

Each invocation prints exactly one JSON object. Unknown subcommands return exit 2 and `status:"rejected"`; runtime failures return exit 1; verified reads return exit 0.

- [ ] **Step 8: Run GREEN gate**

Run: `python -m pytest tests/test_sc_contract.py tests/test_sc_inventory.py tests/test_sc_cli.py -q`
Expected: all selected tests pass.

- [ ] **Step 9: Run slice audit**

Run: `python audit.py`
Expected: exit 0, zero errors.

- [ ] **Step 10: Commit**

```bash
git add extensions/system-control tests/test_sc_contract.py tests/test_sc_inventory.py tests/test_sc_cli.py
git commit -m "feat(system-control): add read-only host inventory"
```

**Independent QA gate:** rerun selected tests on clean checkout; inject malformed schema, unsupported OS and PID reuse cases without modifying implementation.

---

### Task 2: Sensitive capabilities require one-shot, request-bound confirmation

**Estimated size:** 250–350 lines.

**Files:**
- Create (living): `extensions/system-control/sc_policy.py`
- Create (living): `tests/test_sc_policy.py`
- Modify: `extensions/system-control/sc_cli.py`
- Modify: `extensions/system-control/schemas/v1.json`

**Interfaces:** Produces `request_digest`, `classify`, `issue_confirmation`, `consume_confirmation`; extends request `policy.{dry_run,confirmation_id}`.

- [ ] **Step 1: Write policy tests**

```python
def request(capability, args, target=None):
    value = {
        "version": 1, "request_id": "r1", "capability": capability,
        "args": args, "deadline_ms": 1000, "policy": {"dry_run": False},
    }
    if target is not None:
        value["target"] = target
    return value


def test_deny_wins_over_confirmation():
    req = request("file.delete", {"path": "x"})
    assert policy.classify(req)["decision"] == "deny"


def test_confirmation_is_bound_to_exact_request(tmp_path, monkeypatch):
    monkeypatch.setattr(policy, "STATE_DIR", tmp_path)
    original = request("process.cancel", {}, {"pid": 10, "start_time": 20})
    token = policy.issue_confirmation(original)["confirmation_id"]
    changed = request("process.cancel", {}, {"pid": 11, "start_time": 20})
    assert policy.consume_confirmation(changed, token)["ok"] is False


def test_confirmation_is_single_use(tmp_path, monkeypatch):
    monkeypatch.setattr(policy, "STATE_DIR", tmp_path)
    req = request("process.cancel", {}, {"pid": 10, "start_time": 20})
    token = policy.issue_confirmation(req)["confirmation_id"]
    assert policy.consume_confirmation(req, token)["ok"] is True
    assert policy.consume_confirmation(req, token)["ok"] is False
```

- [ ] **Step 2: Run RED gate**

Run: `python -m pytest tests/test_sc_policy.py -q`
Expected: FAIL because policy module does not exist.

- [ ] **Step 3: Implement canonical digest**

Use `json.dumps(request_without_confirmation, sort_keys=True, separators=(",", ":"))` and `hashlib.sha256`. Store only digest, creation time, expiry and random token; never store raw arguments.

- [ ] **Step 4: Implement decision table**

Initial policy:

```python
DENY = {"file.delete", "disk.format", "security.disable", "credential.read"}
CONFIRM = {
    "process.exec", "process.cancel", "session.spawn", "session.send",
    "session.cancel", "daemon.stop", "service.restart", "file.copy",
    "file.copy_overwrite", "broker.dispatch",
}
ALLOW = {
    "capabilities", "process.observe", "process.wait", "service.observe",
    "file.inspect", "events.open", "events.drain", "events.close",
    "session.status", "session.recv", "session.resize", "session.close",
    "daemon.start", "daemon.status", "broker.status",
}
```

Unknown capabilities reject. `deny` always wins. `dry_run` never authorizes a mutation.

- [ ] **Step 5: Implement atomic one-shot tokens**

Use random 256-bit token, file mode restricted to owner where supported, atomic create/replace, TTL ≤120s, delete-before-dispatch semantics and constant-time digest comparison.

- [ ] **Step 6: Add CLI preflight**

`sc_cli.py preflight REQUEST_JSON` returns `allow`, `confirm` or `deny`. Mutation subcommands call policy before backend dispatch.

- [ ] **Step 7: Run GREEN and audit gates**

Run: `python -m pytest tests/test_sc_policy.py tests/test_sc_cli.py -q`
Expected: all selected tests pass.

Run: `python audit.py`
Expected: exit 0, zero errors.

- [ ] **Step 8: Commit**

```bash
git add extensions/system-control/sc_policy.py extensions/system-control/sc_cli.py extensions/system-control/schemas/v1.json tests/test_sc_policy.py
git commit -m "feat(system-control): bind confirmations to requests"
```

**Independent QA gate:** mutate PID, path, deadline and capability after token issuance; verify every replay rejects.

---

### Task 3: User can execute one-shot processes with bounded output and verified exit

**Estimated size:** 300–400 lines.

**Files:**
- Modify: `extensions/system-control/sc_process.py`
- Modify: `extensions/system-control/sc_cli.py`
- Create: `tests/test_sc_process_exec.py`

**Interfaces:** Produces `spawn`, `wait`, `cancel`; CLI `exec --argv-json --cwd --timeout`.

- [ ] **Step 1: Write execution tests**

```python
def test_exec_uses_argv_without_shell(fake_popen):
    r = process.spawn(["tool", "a;b"], backend=fake_popen)
    assert fake_popen.calls[0]["argv"] == ["tool", "a;b"]
    assert fake_popen.calls[0]["shell"] is False


def test_output_flood_spills_and_keeps_tail(tmp_path, fake_popen):
    fake_popen.stdout = b"x" * 20000
    r = process.spawn(["tool"], output_limit=1000, spill_dir=tmp_path, backend=fake_popen)
    assert len(r["value"]["stdout"]) == 1000
    assert r["evidence"]["spill"]


def test_timeout_kills_owned_tree(fake_popen):
    fake_popen.never_exits = True
    r = process.spawn(["tool"], timeout_s=0.01, backend=fake_popen)
    assert r["status"] == "timeout"
    assert fake_popen.tree_terminated is True
```

- [ ] **Step 2: Run RED gate**

Run: `python -m pytest tests/test_sc_process_exec.py -q`
Expected: FAIL on missing execution behavior.

- [ ] **Step 3: Implement argv-only execution**

Reject string commands. Sanitize cwd through an existing directory handle/path check. Environment starts empty except an explicit baseline plus `env_allow`; reject keys matching secret classes from serialization.

- [ ] **Step 4: Implement process ownership**

Windows: create a Job Object with kill-on-close. POSIX: create a process group/session and terminate group with TERM→grace→KILL. Store `{pid,start_time,owner_request_id}`.

- [ ] **Step 5: Implement bounded concurrent readers**

Drain stdout and stderr concurrently. Cap each at 16000 bytes by default; write complete overflow to an owner-only temp spill. Return byte count, truncation flag and spill path; never inline the full spill.

- [ ] **Step 6: Implement completion evidence**

Return exit code, start/end timestamps, verified target identity and tree cleanup state. Exit zero alone sets `status:"dispatched"` unless a requested postcondition passes.

- [ ] **Step 7: Run GREEN and audit gates**

Run: `python -m pytest tests/test_sc_process_exec.py tests/test_sc_policy.py -q`
Expected: all selected tests pass.

Run: `python audit.py`
Expected: exit 0, zero errors.

- [ ] **Step 8: Commit**

```bash
git add extensions/system-control/sc_process.py extensions/system-control/sc_cli.py tests/test_sc_process_exec.py
git commit -m "feat(system-control): add bounded process execution"
```

**Independent QA gate:** output flood, child-spawns-child, timeout, stale PID and secret-like environment inputs.

---

### Task 4: User can maintain persistent process sessions safely

**Estimated size:** 350–450 lines.

**Files:**
- Create: `extensions/system-control/sc_sessions.py`
- Modify: `extensions/system-control/sc_cli.py`
- Create: `tests/test_sc_sessions.py`
- Create: `tests/test_sc_session_daemon.py`

**Interfaces:** CLI `sessions start|status|list|stop`, `session spawn|send|recv|resize|close|cancel`. Request mapping: `sessions start`→`daemon.start`; `sessions status`→`daemon.status`; `sessions list`→`session.status`; `sessions stop`→`daemon.stop`.

- [ ] **Step 1: Write lifecycle tests**

```python
def test_stale_generation_rejects_without_dispatch(daemon):
    sid = daemon.spawn(["shell"])["session"]
    old = daemon.envelope(sid)
    daemon.restart()
    r = daemon.send(old, "echo no")
    assert r["status"] == "rejected"
    assert daemon.writes == []


def test_buffer_overflow_is_explicit(daemon):
    sid = daemon.spawn(["shell"], capacity=2)["session"]
    daemon.feed(sid, ["a", "b", "c"])
    r = daemon.recv(sid)
    assert r["evidence"]["dropped"] == 1


def test_daemon_shutdown_cleans_owned_tree(daemon):
    daemon.spawn(["shell"])
    daemon.stop()
    assert daemon.alive_children == []
```

- [ ] **Step 2: Run RED gate**

Run: `python -m pytest tests/test_sc_sessions.py tests/test_sc_session_daemon.py -q`
Expected: FAIL because daemon module does not exist.

- [ ] **Step 3: Implement transport**

Reuse the proven local pattern: JSONL over loopback or parent pipes, pidfile in OS temp, random session token, generation and atomic pidfile. Reject foreign peer/session/generation before `_op`.

- [ ] **Step 4: Implement bounded session state**

Each session stores owner request, argv, cwd, process identity, ring buffer, cursor, dropped count, last activity and deadline. Default capacity 2048 records and idle TTL 900s.

- [ ] **Step 5: Implement session operations**

`send` accepts bytes/text only for owned PTY/process; `recv` supports cursor, tail and regex wait; `cancel` terminates tree; `close` drains then cleans; `resize` reports unsupported on non-PTY sessions.

- [ ] **Step 6: Add daemon resilience**

Malformed messages return structured errors; hung providers cause session cancellation; daemon finalizer cleans every session; stale pidfiles never attach silently.

- [ ] **Step 7: Run GREEN and audit gates**

Run: `python -m pytest tests/test_sc_sessions.py tests/test_sc_session_daemon.py -q`
Expected: all selected tests pass.

Run: `python audit.py`
Expected: exit 0, zero errors.

- [ ] **Step 8: Commit**

```bash
git add extensions/system-control/sc_sessions.py extensions/system-control/sc_cli.py tests/test_sc_sessions.py tests/test_sc_session_daemon.py
git commit -m "feat(system-control): add persistent owned sessions"
```

**Independent QA gate:** daemon crash, stale pidfile, token replay, output flood and orphan-tree checks.

---

### Task 5: User can subscribe to bounded, resumable system events

**Estimated size:** 350–500 lines. Split reducers from OS adapters if >500.

**Files:**
- Create: `extensions/system-control/sc_telemetry.py`
- Modify: `extensions/system-control/backends/windows.py`
- Modify: `extensions/system-control/backends/linux.py`
- Modify: `extensions/system-control/backends/macos.py`
- Modify: `extensions/system-control/sc_cli.py`
- Create: `tests/test_sc_telemetry.py`
- Create: `tests/test_sc_event_streams.py`

**Interfaces:** `open_stream`, `drain`, `close_stream`, `reduce_events`; CLI `events open|drain|close`.

- [ ] **Step 1: Write event-contract tests**

```python
def test_event_has_stable_subject_and_cursor():
    e = telemetry.normalize({"pid": 7, "start_time": 9}, source="fake", kind="process.exit")
    assert e["subject"] == {"pid": 7, "start_time": 9}
    assert e["cursor"]


def test_drain_is_bounded_and_reports_drops(stream):
    stream.feed(range(300))
    r = telemetry.drain(stream.id, limit=20)
    assert len(r["value"]["events"]) == 20
    assert "dropped" in r["evidence"]


def test_reducer_keeps_error_and_drop_signals():
    r = telemetry.reduce_events([
        event("info", pid=1), event("error", pid=2), event("overflow", dropped=4)
    ], top_k=1)
    assert r["errors"][0]["subject"]["pid"] == 2
    assert r["dropped"] == 4
```

- [ ] **Step 2: Run RED gate**

Run: `python -m pytest tests/test_sc_telemetry.py tests/test_sc_event_streams.py -q`
Expected: FAIL because telemetry module does not exist.

- [ ] **Step 3: Implement normalized event envelopes**

Fields: `ts`, `observed_ts`, `source`, `kind`, `subject`, `severity`, `attrs`, `cursor`, `dropped`. Mark `attrs` untrusted; sanitize secret-shaped fields before storage.

- [ ] **Step 4: Implement bounded streams and cursors**

Use deque/ring with monotonic sequence cursor. Cursor older than retained window returns `resync_required:true`, never silently skips. Spill is owner-only and expires with stream TTL.

- [ ] **Step 5: Implement baseline adapters**

Windows: WMI temporary process events. Linux: pidfd where target-specific; procfs diff fallback with explicit `mode:"poll"`. macOS: process snapshot diff fallback. Polling intervals have lower bound and deadline.

- [ ] **Step 6: Implement reducer**

Group by `{kind,subject}`, preserve errors, dropped count, first/last timestamp and representative evidence. Return Top-K plus aggregate counts; raw events remain retrievable by cursor.

- [ ] **Step 7: Run GREEN and audit gates**

Run: `python -m pytest tests/test_sc_telemetry.py tests/test_sc_event_streams.py -q`
Expected: all selected tests pass.

Run: `python audit.py`
Expected: exit 0, zero errors.

- [ ] **Step 8: Commit**

```bash
git add extensions/system-control/sc_telemetry.py extensions/system-control/backends extensions/system-control/sc_cli.py tests/test_sc_telemetry.py tests/test_sc_event_streams.py
git commit -m "feat(system-control): add bounded system event streams"
```

**Independent QA gate:** overflow, cursor expiry, secret-shaped attributes, clock reversal and provider loss.

---

### Task 6: User can inspect and copy files without path-race ambiguity

**Estimated size:** 300–450 lines.

**Files:**
- Create: `extensions/system-control/sc_files.py`
- Modify: `extensions/system-control/sc_cli.py`
- Create: `tests/test_sc_files.py`

**Interfaces:** CLI `file inspect`, `file copy --expected-hash --dry-run`.

- [ ] **Step 1: Write path and copy tests**

```python
import hashlib


def test_parent_escape_rejects(tmp_path):
    r = files.inspect_path(str(tmp_path), "../outside")
    assert r["status"] == "rejected"


def test_symlink_escape_rejects(tmp_path):
    outside = tmp_path.parent / "outside"
    outside.write_text("secret")
    (tmp_path / "link").symlink_to(outside)
    assert files.inspect_path(str(tmp_path), "link")["status"] == "rejected"


def test_copy_verifies_source_and_destination_hash(tmp_path):
    (tmp_path / "a").write_bytes(b"abc")
    expected = hashlib.sha256(b"abc").hexdigest()
    r = files.copy_verified(str(tmp_path), "a", "b", expected_hash=expected)
    assert r["status"] == "verified"
    assert r["precondition"]["sha256"] == r["postcondition"]["sha256"]
```

- [ ] **Step 2: Run RED gate**

Run: `python -m pytest tests/test_sc_files.py -q`
Expected: FAIL because files module does not exist.

- [ ] **Step 3: Implement root-bound resolution**

Reject absolute relative paths, `..`, symlinks/reparse points and root changes. POSIX uses dir-fd/openat-style operations where available; Windows checks reparse attributes and final path under root. No delete, chmod, ACL or overwrite by default.

- [ ] **Step 4: Implement inspect**

Return type, size, timestamps, identity, link/reparse status and streaming SHA-256. Never return file contents unless a separate future capability is approved.

- [ ] **Step 5: Implement copy with checkpoint semantics**

Dry-run returns source identity/hash and proposed destination. Real copy writes a sibling temp file, fsyncs, verifies hash, atomically renames, then verifies destination. Existing destination rejects unless policy-confirmed `overwrite=True`.

- [ ] **Step 6: Run GREEN and audit gates**

Run: `python -m pytest tests/test_sc_files.py tests/test_sc_policy.py -q`
Expected: all selected tests pass.

Run: `python audit.py`
Expected: exit 0, zero errors.

- [ ] **Step 7: Commit**

```bash
git add extensions/system-control/sc_files.py extensions/system-control/sc_cli.py tests/test_sc_files.py
git commit -m "feat(system-control): add verified file inspection and copy"
```

**Independent QA gate:** symlink swap, reparse point, source mutation during copy, destination race and overwrite-token replay.

---

### Task 7: Windows users get native process, service and event control

**Estimated size:** 400–500 lines. Split service mutation from event adapter if needed.

**Files:**
- Modify: `extensions/system-control/backends/windows.py`
- Create: `extensions/system-control/sc_windows.py`
- Create: `tests/test_sc_windows.py`
- Create: `tests/test_sc_windows_events.py`

**Interfaces:** Capabilities `process.observe`, `process.wait`, `service.observe`, `service.restart`, and `events.open` with `args.kind="process"`; no ETW kernel provider yet.

- [ ] **Step 1: Write Win32 seam tests**

```python
def test_process_identity_uses_creation_time(fake_win32):
    r = windows.process_get(42, io=fake_win32)
    assert r["pid"] == 42
    assert r["start_time"] == fake_win32.creation_time


def test_wait_uses_handle_not_pid_polling(fake_win32):
    windows.wait_process({"pid": 42, "start_time": 9}, io=fake_win32)
    assert fake_win32.wait_handle_calls == 1
    assert fake_win32.pid_poll_calls == 0


def test_service_restart_verifies_final_state(fake_scm):
    r = windows.restart_service("svc", io=fake_scm)
    assert r["precondition"]["state"] == "running"
    assert r["postcondition"]["state"] == "running"
```

- [ ] **Step 2: Run RED gate**

Run: `python -m pytest tests/test_sc_windows.py tests/test_sc_windows_events.py -q`
Expected: FAIL on missing native adapter.

- [ ] **Step 3: Implement ctypes Win32 process handles**

Use documented access rights only. Query creation time and image name, wait on handle, create Job Object kill-on-close for owned children. Close every handle in `finally`.

- [ ] **Step 4: Implement SCM adapter**

Read status for any accessible service. Restart requires policy confirmation, allowlisted service name and bounded wait through pending states. Never change service configuration or identity.

- [ ] **Step 5: Implement event adapter**

Use WMI temporary notifications initially. Include provider loss/queue overflow indicators. Persist only opaque cursor metadata; cancel subscriptions on close.

- [ ] **Step 6: Run real Windows smoke tests**

Run read-only process/service tests against a known non-sensitive process and service. Spawn a tool-owned child for wait/cancel. Do not restart a real service during smoke tests.

- [ ] **Step 7: Run GREEN and audit gates**

Run: `python -m pytest tests/test_sc_windows.py tests/test_sc_windows_events.py -q`
Expected: all selected tests pass.

Run: `python audit.py`
Expected: exit 0, zero errors.

- [ ] **Step 8: Commit**

```bash
git add extensions/system-control/backends/windows.py extensions/system-control/sc_windows.py tests/test_sc_windows.py tests/test_sc_windows_events.py
git commit -m "feat(system-control): add native Windows adapter"
```

**Independent QA gate:** execute in disposable Windows VM; verify non-admin behavior, handle cleanup, PID reuse and denied service mutation.

---

### Task 8: Linux users receive native process and systemd observation

**Estimated size:** 250–350 lines.

**Files:**
- Modify: `extensions/system-control/backends/linux.py`
- Create: `tests/test_sc_linux.py`

**Interfaces:** `procfs`, pidfd, systemd status and journal capability detection.

- [ ] **Step 1: Write Linux contract tests**

```python
def test_linux_pidfd_wait_preferred(fake_linux):
    fake_linux.pidfd_supported = True
    linux.wait_process({"pid": 3, "start_time": 8}, io=fake_linux)
    assert fake_linux.pidfd_opened is True


def test_proc_stat_start_time_prevents_pid_reuse(fake_linux):
    fake_linux.current_start_time = 9
    r = linux.process_get(3, start_time=8, io=fake_linux)
    assert r["status"] == "rejected"
```

- [ ] **Step 2: Run RED gate**

Run: `python -m pytest tests/test_sc_linux.py -q`
Expected: FAIL on incomplete Linux adapter.

- [ ] **Step 3: Implement Linux adapter**

Read procfs with stable start ticks. Prefer `os.pidfd_open` when available. Use fixed `systemctl show --property` argument arrays with timeout when D-Bus bindings are absent, and report `mode:"cli"`. Journal streaming stays unsupported until an approved dependency or native binding exists.

- [ ] **Step 4: Run GREEN and platform gates**

Run: `python -m pytest tests/test_sc_linux.py -q`
Expected: all selected tests pass through fake seams.

Run actual smoke tests on a disposable Linux runner/VM.
Expected: read-only inventory succeeds; unsupported capabilities explain why.

Run: `python audit.py`
Expected: exit 0, zero errors.

- [ ] **Step 5: Commit**

```bash
git add extensions/system-control/backends/linux.py tests/test_sc_linux.py
git commit -m "feat(system-control): add native Linux adapter"
```

**Independent QA gate:** clean Linux VM tests pidfd support, PID reuse and systemd absence; no host mutation.

---

### Task 9: macOS users receive process and launchd observation

**Estimated size:** 250–350 lines.

**Files:**
- Modify: `extensions/system-control/backends/macos.py`
- Create: `tests/test_sc_macos.py`

**Interfaces:** bounded process inventory, kqueue support probe, launchd status and unified-log capability detection.

- [ ] **Step 1: Write macOS contract tests**

```python
def test_macos_missing_endpoint_security_is_explicit(fake_macos):
    caps = macos.capabilities(io=fake_macos)
    endpoint = next(c for c in caps if c["name"] == "endpoint_security")
    assert endpoint["supported"] is False
    assert endpoint["reason"] == "entitlement_required"


def test_launchd_query_requires_explicit_label(fake_macos):
    r = macos.service_status("", io=fake_macos)
    assert r["status"] == "rejected"
    assert fake_macos.calls == []
```

- [ ] **Step 2: Run RED gate**

Run: `python -m pytest tests/test_sc_macos.py -q`
Expected: FAIL on incomplete macOS adapter.

- [ ] **Step 3: Implement macOS adapter**

Use bounded `ps` projection for initial inventory, `kqueue` where Python exposes required filters, fixed `launchctl print` arguments for explicit labels and bounded `log show` windows. Report TCC and entitlement requirements; never attempt bypass.

- [ ] **Step 4: Run GREEN and platform gates**

Run: `python -m pytest tests/test_sc_macos.py -q`
Expected: all selected tests pass through fake seams.

Run actual smoke tests on a disposable macOS runner/VM.
Expected: read-only inventory succeeds; unavailable capabilities include a stable reason.

Run: `python audit.py`
Expected: exit 0, zero errors.

- [ ] **Step 5: Commit**

```bash
git add extensions/system-control/backends/macos.py tests/test_sc_macos.py
git commit -m "feat(system-control): add native macOS adapter"
```

**Independent QA gate:** clean macOS VM verifies process identity, launchd label binding and entitlement failure; no host mutation.

---

### Task 10: Authorized operators can opt into narrow privileged brokers

**Estimated size:** 300–450 lines. Keep templates declarative; split Windows and Linux into separate PRs before implementation if the estimate reaches 500 lines.

**Files:**
- Create: `extensions/system-control/brokers/README.md`
- Create: `extensions/system-control/brokers/windows-jea.pssc`
- Create: `extensions/system-control/brokers/linux-polkit.policy`
- Create: `extensions/system-control/sc_broker.py`
- Create: `tests/test_sc_broker.py`

**Interfaces:** `broker preflight`, `broker status`, allowlisted `service.restart`; no generic command execution.

- [ ] **Step 1: Write broker-policy tests**

```python
def request(capability, args):
    return {
        "version": 1, "request_id": "r1", "capability": capability,
        "args": args, "deadline_ms": 1000, "policy": {"dry_run": False},
    }


def test_broker_exposes_only_declared_capabilities(fake_broker):
    assert fake_broker.capabilities() == ["service.restart"]


def test_broker_rejects_unbound_identity(fake_broker):
    req = request("service.restart", {"name": "allowed"})
    req["subject"] = {"uid": "other"}
    assert broker.dispatch(req, io=fake_broker)["status"] == "rejected"
```

- [ ] **Step 2: Run RED gate**

Run: `python -m pytest tests/test_sc_broker.py -q`
Expected: FAIL because broker module does not exist.

- [ ] **Step 3: Implement broker client contract**

Authenticate local peer using OS identity, bind request digest and confirmation, enforce deadline and return audit ID. No credential forwarding or shell strings.

- [ ] **Step 4: Add declarative templates**

JEA exposes a single constrained function with validated service allowlist. Polkit action names one broker method and defers authorization to administrator policy. Templates are not auto-installed.

- [ ] **Step 5: Add explicit provisioning documentation**

Document install, status, disable and uninstall. Every provisioning step requires an administrator and has a dry-run/check command. The bundle installer only copies templates.

- [ ] **Step 6: Run GREEN and security gates**

Run: `python -m pytest tests/test_sc_broker.py tests/test_sc_policy.py -q`
Expected: all selected tests pass.

Run secure-default checks: no hardcoded credentials, no unauthenticated endpoint, no broad wildcard capability, logs sanitized.

Run: `python audit.py`
Expected: exit 0, zero errors.

- [ ] **Step 7: Commit**

```bash
git add extensions/system-control/brokers extensions/system-control/sc_broker.py tests/test_sc_broker.py
git commit -m "feat(system-control): add opt-in privilege brokers"
```

**Independent QA gate:** disposable admin VM provisions broker, validates least privilege, then uninstalls cleanly.

---

### Task 11: Maintainer can decide native acceleration from measured evidence

**Estimated size:** 200–300 lines without Rust; native crate is a separate PR only after approval.

**Files:**
- Create: `extensions/system-control/sc_bench.py`
- Create: `tests/test_sc_bench.py`
- Create: `.devin/research/system-control-benchmark.json` after measurements
- Conditional create: `.devin/adr/004-system-control-native-acceleration.md`
- Conditional create: `extensions/rust-core/crates/system-core/`

**Interfaces:** benchmark scenarios `process_snapshot`, `event_reduce`, `json_decode`, `stream_drain`.

- [ ] **Step 1: Write deterministic harness tests**

```python
def test_benchmark_reports_distribution(fake_clock):
    r = bench.run(lambda: None, runs=20, warmup=2, clock=fake_clock)
    assert set(r) >= {"runs", "p50_ms", "p95_ms", "max_ms"}
    assert r["runs"] == 20
```

- [ ] **Step 2: Run RED gate**

Run: `python -m pytest tests/test_sc_bench.py -q`
Expected: FAIL because benchmark module does not exist.

- [ ] **Step 3: Implement harness**

Warmup excluded; monotonic clock; fixed fixtures; JSON output; environment metadata excludes usernames, paths and secrets. Measure Python baseline before proposing optimization.

- [ ] **Step 4: Capture reproducible baseline**

Run at least 30 measured iterations per scenario on supported host. Store raw summary, command, commit and platform class in research JSON.

- [ ] **Step 5: Apply decision gate**

Create Rust work only when the baseline isolates a CPU/parser/reducer hot path, the ADR records the predeclared latency budget, and two independent runs reproduce the bottleneck. If those conditions fail, record `decision:"stay_python"` and stop.

- [ ] **Step 6: If approved, write ADR before crate**

ADR names measured bottleneck, exact PyO3 functions, fallback, ABI and rollback. New crate exports only pure reducers/parsers; no async runtime and no privileged API.

- [ ] **Step 7: Verify**

Run: `python -m pytest tests/test_sc_bench.py -q`
Expected: all selected tests pass.

Conditional Rust gate: `cargo build --release --manifest-path extensions/rust-core/Cargo.toml`
Expected: exit 0.

Run: `python audit.py`
Expected: exit 0, zero errors.

- [ ] **Step 8: Commit benchmark evidence**

```bash
git add extensions/system-control/sc_bench.py tests/test_sc_bench.py .devin/research/system-control-benchmark.json
if [[ -e .devin/adr/004-system-control-native-acceleration.md ]]; then
  git add .devin/adr/004-system-control-native-acceleration.md extensions/rust-core/crates/system-core
fi
git commit -m "perf(system-control): measure native acceleration threshold"
```

**Independent QA gate:** rerun the same command on clean checkout; compare distributions, not one sample.

---

### Task 12: Bundle installs, discovers and documents System Control end-to-end

**Estimated size:** 250–350 lines.

**Files:**
- Create: `extensions/system-control/USAGE.md`
- Create: `skills/system-control/SKILL.md`
- Create: `tests/validation/test_system_control_workflow.py`
- Modify: `manifest.json`
- Modify: `.devin/docs/SKILL-TIERS.md`
- Modify: `.devin/docs/TOOLS-MAP.md`
- Modify: `README.md`
- Modify only if required by observed installer gap: `install.ps1`, `install.sh`, `export.ps1`, `export.sh`

**Interfaces:** `/system-control` router; installed extension at `%APPDATA%/devin/extensions/system-control/` or `~/.config/devin/extensions/system-control/`.

- [ ] **Step 1: Write distribution tests**

```python
def test_system_control_skill_is_thin_router(repo_root):
    text = (repo_root / "skills/system-control/SKILL.md").read_text()
    assert "extensions/system-control/USAGE.md" in text
    assert len(text.splitlines()) <= 80


def test_system_control_workflow_declares_safe_defaults(repo_root):
    usage = (repo_root / "extensions/system-control/USAGE.md").read_text()
    for phrase in ["no privileged daemon by default", "one-shot confirmation", "dropped"]:
        assert phrase in usage
```

- [ ] **Step 2: Run RED gate**

Run: `python -m pytest tests/validation/test_system_control_workflow.py -q`
Expected: FAIL because skill/docs/metadata are absent.

- [ ] **Step 3: Write thin skill router**

Frontmatter triggers `[user, model]`; direct the agent to USAGE; state when to use system APIs before GUI; preserve confirmation and untrusted-output rules. Do not duplicate command reference.

- [ ] **Step 4: Write USAGE contract**

Document interpreter, JSON status semantics, capabilities, policy, sessions, files, telemetry, platform matrix, failure modes, install and broker opt-in. Include examples only for safe read-only/owned-process actions.

- [ ] **Step 5: Sync metadata and docs**

Add skill entry through the repository sync procedure. Update counts and maps from actual disk. Do not hand-edit generated hashes if a sync script owns them.

- [ ] **Step 6: Verify installers without changing generic extension logic unnecessarily**

The current installers enumerate every `extensions/*` directory. Prove `system-control` is included through dry-run; edit installers only if the observed output omits it.

- [ ] **Step 7: Run complete local gates**

Run:

```bash
python audit.py
python -m pytest
bash -n install.sh
bash install.sh --dry-run
bash export.sh --dry-run
```

Windows PowerShell tokenize gate:

```powershell
$errors = $null
[System.Management.Automation.Language.Parser]::ParseFile((Resolve-Path .\install.ps1), [ref]$null, [ref]$errors) | Out-Null
if ($errors.Count) { $errors; exit 1 }
```

Windows installer/exporter dry-run:

```powershell
.\install.ps1 -DryRun
.\export.ps1 -DryRun
```

Expected: all commands exit 0; audit reports zero errors; pytest reports zero failures; dry-run lists `system-control` without writing live configuration.

- [ ] **Step 8: Independent security review**

Review for secret logging, unauthenticated endpoints, broad permissions, token replay, stale identity, path escape, output flood and destructive actions. Verdict must be PASS before commit.

- [ ] **Step 9: Commit**

```bash
git add extensions/system-control skills/system-control tests/validation/test_system_control_workflow.py manifest.json .devin/docs README.md
if ! git diff --quiet -- install.ps1 install.sh export.ps1 export.sh; then
  git add install.ps1 install.sh export.ps1 export.sh
fi
git commit -m "feat(system-control): integrate authorized OS control"
```

**Independent QA gate:** clean checkout, full suite, audit, both installer dry-runs, held-out suite and skill-format validation.

---

## Cross-Task Verification Matrix

| Requirement | Primary task | Independent evidence |
|---|---:|---|
| Typed versioned contract | T1 | malformed/unknown schema tests |
| Deny-wins and confirmations | T2 | token replay/mutation held-out |
| Bounded one-shot execution | T3 | output flood and orphan-tree tests |
| Persistent sessions | T4 | stale generation and daemon crash tests |
| Dense resumable telemetry | T5 | overflow/cursor/provider-loss tests |
| Race-safe file operations | T6 | symlink/reparse/source-mutation tests |
| Native Windows support | T7 | disposable Windows VM smoke |
| Linux native support | T8 | disposable Linux smoke |
| macOS native support | T9 | disposable macOS smoke |
| Authorized privilege | T10 | provision/use/uninstall in VM |
| Evidence-based Rust | T11 | reproducible benchmark comparison |
| Distribution and discovery | T12 | full CI-equivalent gate |

## Rollout and Rollback

1. Ship read-only capabilities first.
2. Keep mutations disabled unless policy capability exists.
3. Mark deep providers `supported:false` until runtime probe succeeds.
4. Enable daemon only on explicit session/event command.
5. Install broker templates but never provision automatically.
6. Record schema version in every artifact and pidfile.
7. Rollback removes skill and extension; daemon stop cleans temp state.
8. Broker rollback uses documented uninstall and verifies service/policy removal.
9. Native acceleration rollback selects Python fallback without schema change.

## Final Self-Review Checklist

- [ ] Every task is a vertical, independently demonstrable slice.
- [ ] No task exceeds 500 lines without an explicit split.
- [ ] All interfaces use identical names across tasks.
- [ ] No placeholder, implicit dependency or unspecified error behavior remains.
- [ ] No disposable prototype survives a task.
- [ ] No generic privileged shell exists.
- [ ] No bypass, credential access or stealth persistence exists.
- [ ] All destructive operations remain out of scope.
- [ ] Platform absence degrades explicitly.
- [ ] Full verification and independent QA are required before completion.
