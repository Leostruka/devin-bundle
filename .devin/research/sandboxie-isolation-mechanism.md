# How Sandboxie Achieves Program-Level Separation – Research Report

Date: 2026-09-22. Question: if a second independent cursor/focus doesn't exist as an OS feature (conclusion of `virtual-input-devices.md`), how does Sandboxie separate programs? 166 deduplicated sources in `sandboxie-isolation-sources.md` (IDs referenced below).

## 1. Direct answer

**Sandboxie does not separate input.** It separates *resource access*. The separation is **asymmetric and blocking**, not a second channel: a sandboxed program is forbidden to touch the outside world's files, registry keys, named objects, windows, processes, IPC endpoints and network – while the unsandboxed world keeps normal access. Nothing in the architecture creates an independent keyboard, mouse, cursor, or focus.

The official docs and architecture discussion state the model explicitly [A1, A2]:

1. Create the process with a **heavily restricted primary token** (deny-only SIDs, stripped privileges, Untrusted integrity) – it can't access almost anything and would crash immediately.
2. **Hook** its API surface (user-mode SbieDll on ntdll + Win32 DLLs; kernel SbieDrv on FS/registry/objects/syscalls) and **mediate** permitted calls through brokers – driver + SbieSvc service – so the program still works.
3. If the program bypasses the hooks (direct syscall), the restricted token and UIPI deny the operation anyway. Two-choice model: comply → brokered; bypass → access denied.

This is the same model as the Chromium renderer sandbox (restricted token + job object + alternate desktop + integrity levels [J1–J5]) – process-level isolation is always built from **token + namespace + message-filter + brokered IPC**, never from input devices. Microsoft's own AppContainer doc is explicit: "keyboard and mouse are always available" to the sandboxed app – **input devices are not the isolation boundary** [G2].

## 2. The mechanism stack (verified in source)

### 2.1 Startup: token replacement before the program runs

- SbieDrv's process-create callback identifies the box [B12]; SbieSvc's DriverAssist injects `LowLevel.dll` into the suspended process [D2, D3]; `core/low` detours `LdrInitializeThunk` so `SbieDll.dll` loads **before** the process initializes [C13–C15].
- The driver replaces the primary token: `Token_ReplacePrimary` → `Token_Restrict(SANDBOX_INERT | DISABLE_MAX_PRIVILEGE)`, integrity dropped to Untrusted (Low if a window station is opened), `DropAdminRights` strips Admin/Power Users, anonymous LUID patched [B16]. Construction uses `SepFilterToken`/`SeFilterToken` or modern `Token_CreateToken` reconstruction; the unexported-symbol dependencies and `PrimaryTokenFrozen` EPROCESS bit are documented in the official internals page [A3, B16].
- The earlier (fuller) token is **retained** per-process; for a mediated syscall the driver impersonates it, executes the call, de-impersonates [A3, B18]. So the sandboxed process can never itself wield the original token – even after unhooking ntdll [A1].

### 2.2 Kernel enforcement (SbieDrv)

Init order in DriverEntry: Process → Thread → File → Key → Ipc → Gui → Api → WFP [B1].

- **Files**: FltMgr minifilter (`FltRegisterFilter`) since Vista; XP used a parse-procedure hook [B3, B4].
- **Registry**: `CmRegisterCallbackEx` registry callbacks [B5]; sandboxed hive `RegHive` mounted at `\REGISTRY\USER\Sandbox_<user>_<box>` [B20, A13].
- **Objects**: `ObRegisterCallbacks` on resolved object types (ALPC Port, Section, Mutant, JobObject, SymbolicLink…) mapping to check handlers [B6, B7].
- **Syscalls**: a per-service `SYSCALL_ENTRY` table (index, param count, ntdll offset, ntos func, handlers) resolved from `KeServiceDescriptorTable`/shadow table [B8–B10]; Set1 handlers rewrite behavior (token syscalls), Set2 handlers post-check handles (OpenProcess/OpenThread/AlpcOpenSender*) [B11, B17, B18].
- **GUI**: driver-level win32k interception – documented externally as SSDT + shadow-SSDT hooks on `NtUserSendInput`, `NtUserBlockInput`, `NtUserPostMessage`, `NtUserPostThreadMessage`, `NtUserSetWindowsHookEx`, `NtUserMessageCall`, `NtUserDestroyWindow`… plus `OpenProcedure` hooks on ObjectTypes [E1]. Config flags `EnableWin32kHooks`/`ApproveWinNtSysCall`/`SysCallLockDown` tune it [B8, A18].
- **Network**: WFP callout "SbieFilter" + per-box `NetworkAccess=` rules; user-mode WSA fallback [B21, A20].
- **Config/auth**: driver parses Sandboxie.ini itself [B22]; supporter features gated by RSA-verified Certificate.dat [B23]; kernel-build adaptation via signed DynData offsets [B24].

### 2.3 User-mode virtualization (SbieDll)

- **Injection**: `SbieDll_InjectLow` writes SBIELOW_DATA + detour code; `LdrInitializeThunk` detour loads SbieDll before init [C13–C15, D3].
- **Hook engine**: custom trampoline layer (`SbieDll_Hook`/`SBIEDLL_HOOK`, `MODULE_HOOK` trampolines) on vendored Microsoft Detours – not EasyHook [C2, C3, A24].
- **Namespace rewrite**: hooks on NtCreate/Open for Event, EventPair, KeyedEvent, Timer, Mutant, Semaphore, Section(+Ex), MapView, SymLink, DirectoryObject redirect into `\Sandbox\<user>\<box>\Session_N` [C4, C5, A4, B20]. Unnamed jobs get `Sbie_DummyJob_*` names; jobs can't ASSIGN/TERMINATE [C5, B19].
- **File virtualization**: `File_GetCopyPath` maps TruePath→CopyPath; `File_MigrateFile` copies host file into the box on first write (copy-on-write); tombstones in `FilePaths.dat` mark deleted/relocated host files [C6–C9, A27]. OpenFilePath/ReadFilePath punch holes [A15, A16, A6].
- **Registry virtualization**: `Key_GetTruePath` translation + merged view of real+sandboxed keys; writes go to the box's mounted hive [C11, C12, A13].
- **IPC/RPC**: named pipes/mailslots re-prefixed per-box (AppContainerNamedObjects SID-aware) [C10]; sandboxed epmapper [D7]; sandboxed RpcSs runs real rpcss inside the box when COM is closed [D9]; rpcrt hooks inject real ports only for whitelisted cases [C24].

### 2.4 GUI separation – the closest thing to "input separation"

This is the part that answers the question most directly. Sandboxie's GUI isolation is **message blocking + renaming + proxying**, all enforcement – no second input channel:

- **Window class renaming**: classes get a `Sandbox:<box>:` prefix so sandboxed windows can't collide with or impersonate outside windows [C17, A9]. `[#]` marker injected into window titles [C20].
- **Message interception**: hooks on SendMessage/SendMessageTimeout/SendNotifyMessage/PostMessage/PostThreadMessage/DispatchMessage [C19]; driver-side shadow-SSDT checks on NtUserPostMessage/PostThreadMessage/MessageCall [E1]. Default: sandboxed programs cannot access, communicate, close, or destroy windows outside the sandbox [A9]. `OpenWinClass=*` relaxes this explicitly at the cost of isolation.
- **Input-function blocking**: hooks on SendInput, BlockInput, ClipCursor, SetForegroundWindow; `Gui_SendInput` **aborts if the foreground window isn't in the same box** – direct anti-shatter enforcement [C18, E1]. Screen capture (GetDC/PrintWindow) also gated [C18].
- **Separate window station**: GuiServer creates `Sandboxie_WinSta_<tick>` + desktop with NULL DACL and an untrusted-integrity SACL; GUI proxy slaves in the service perform window ops on the real desktop on behalf (EnumWindows, FindWindow, SendPostMessage, clipboard get/set) [D6, C20, C22].
- **The OS-level basis**: window messages can only be sent between processes on the **same desktop** [I2]; only Winsta0 is interactive [I1]; job UI restrictions (UILIMIT_HANDLES, clipboard, global atoms, hooks) are the documented containment knobs [G8]; Chromium uses the same alternate-desktop/winstation + job + DisallowWin32kSystemCalls mitigation [J1, J5, J14, I4, I5].

### 2.5 The broker (SbieSvc)

Privileged operations the sandboxed process cannot do are executed by the unsandboxed service: driver loading (NtLoadDriver), injection, process control (RunSandboxed/KillAll), per-user helpers (CreateProcessAsUser, EFS proxy opens), GUI proxy, epmapper, COM proxy, net proxy [D1–D8]. Same broker/target split as Chromium (SpawnTargetAsync/LowerToken, shared-memory CrossCall IPC) [J3, J7, J13].

## 3. What this means for the computer-use question

| Goal | Sandboxie's mechanism | Relevance to a virtual input device |
|------|----------------------|-------------------------------------|
| Stop program A's writes from reaching real FS/registry | Minifilter + CmCallback + SbieDll CoW into box paths | None – resource isolation, not input |
| Stop A from seeing/impersonating outside objects | `\Sandbox\…\Session_N` private namespace + name rewriting | Analogue: Raw Input device identity is the "namespace" for input |
| Stop A from messaging/injecting input into outside windows | Message hooks + `Sandbox:` class prefix + `Gui_SendInput` same-box check + UIPI + job UILIMIT | **This is the only input-related isolation that exists – it blocks, it doesn't channel** |
| Let A still work | Brokered syscalls (impersonate retained token) + SbieSvc proxies | Analogue: our daemon mediates virtual-device reports |
| Contain A's network | WFP callout per box | None |
| Hard isolation of untrusted code | Token + IL + (optionally) AppContainer/compartment mode | Orthogonal |

**Conclusion:** "separação a nível de programas" is achieved by *denying* cross-boundary operations, not by giving each side its own input path. The two relevant facts for our design:

1. If the goal is **agent-vs-app attribution**, virtual devices solve it (own VID/PID/hDevice/senderID) – nothing in Sandboxie's model is needed.
2. If the goal is **agent input must not reach the user's apps** (containment), the documented tools are the same ones Sandboxie/Chromium use: run the agent's targets on a **separate desktop/window station** (messages can't cross desktops [I2], but note only Winsta0 is interactive [I1]), job UI restrictions [G8], UIPI integrity gap [F4–F6], an AppContainer, or a VM (Hyper-V/MDAG/Windows Sandbox = separate kernel [K6–K9]). A virtual input device alone does **not** provide that containment – its events merge into the shared desktop, exactly like hardware.

## 4. Gaps and caveats

- `core/drv/gui.c` internals and `guimsg.c` message-filter logic not read line-by-line; GUI enforcement split between driver and DLL is partially verified (comments + proxy + hooked prototypes) – marked accordingly.
- Minifilter altitude value and Ronen Tzur's original internals articles (tzuk.net) not retrieved.
- Whether raw direct syscalls on x64 hit a driver-level hook beyond the SbieDll-mediated table is only partially verified; the code comments state the restricted token/UIPI is the backstop [B19, A1].
- Sandboxie internals rely on undocumented kernel details (SepFilterToken, EPROCESS bits, DynData offsets) – fragile across Windows builds, which is why it needs signing + DynData [A3, B24].

## 5. Source register

166 deduplicated sources in `sandboxie-isolation-sources.md`, sections A–K: Sandboxie official docs + driver/DLL/service source files + Windows primitive docs (tokens, IL/UIPI, jobs, namespaces, win32k, WFP, desktops) + Chromium/Firefox sandbox sources + container/silo/Drawbridge references + one verified third-party driver analysis.
