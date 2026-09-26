# Source Index – Sandboxie Program-Level Isolation

Deduplicated registry for `sandboxie-isolation-mechanism.md`. Format: title – URL – type – concrete fact. Types: `source` (repository file), `osdoc` (Microsoft/official platform docs), `sbdocs` (official Sandboxie docs), `spec`/`paper`, `secondary`.

## A. Sandboxie – architecture and official docs

| # | Source | Type | Fact |
|---|--------|------|------|
| A1 | Isolation Mechanism – https://sandboxie-plus.github.io/sandboxie-docs/Content/IsolationMechanism.html | sbdocs | Sandboxed processes get a heavily restricted token; SbieDll hooks ntdll syscall stubs → SbieDrv mediates; bypassing hooks hits the restricted token → access denied. FS/registry virtualization lives in SbieDll. |
| A2 | Architecture of Sandboxie (discussion #3882) – https://github.com/sandboxie-plus/Sandboxie/discussions/3882 | sbdocs | Three components: SbieDll (user-mode hooks → broker), SbieSvc (broker validating policy), SbieDrv (transparent FS/registry redirection, process tracking). Two-choice model: comply with hook → broker validates; bypass → access denied via restricted token. Similar to Chrome renderer sandbox. |
| A3 | Token and Syscall Internals (TokenMagic) – https://sandboxie-plus.github.io/sandboxie-docs/Content/TokenMagic.html | sbdocs | Driver process callbacks → LowLevel/SbieDll injection → primary token filtered/reconstructed; SepFilterToken (legacy) / Token_CreateToken (modern) paths; retained source token impersonated per mediated call (PsImpersonateClient + ETHREAD DynData fix); PrimaryTokenFrozen bit cleared in EPROCESS. |
| A4 | Sandbox Hierarchy – https://sandboxie-plus.github.io/sandboxie-docs/Content/SandboxHierarchy.html | sbdocs | IpcRootPath `\Sandbox\<user>\<box>\Session_N` with per-sandbox object dirs mirroring \BaseNamedObjects, \RPC Control; sandboxed objects live inside it; "sandboxed programs are never permitted to access IPC objects outside the sandbox namespace, not even for read-only." |
| A5 | Resource Access Settings – https://sandboxie-plus.github.io/sandboxie-docs/Content/ResourceAccessSettings.html | sbdocs | IPC Access category manages NT IPC object exclusions; Blocked overrides Direct; `\RPC Control\AudioSrv` block mutes a sandbox. |
| A6 | Resource Access matrix – https://sandboxie-plus.github.io/sandboxie-docs/Content/ResourceAccess.html | sbdocs | Full Open/Closed/Read/Write/Normal × File/Key/Ipc/Clsid/WinClass directive matrix; OpenFilePath/OpenKeyPath don't apply to programs residing inside the sandbox. |
| A7 | ClosedIpcPath – https://sandboxie-plus.github.io/sandboxie-docs/Content/ClosedIpcPath.html | sbdocs | Denies all access incl. read; used to block default-allowed resources. |
| A8 | SandboxieTrace – https://sandboxie-plus.github.io/sandboxie-docs/Content/SandboxieTrace.html | sbdocs | Resource classes F/K/I/G map to OpenFilePath/OpenKeyPath/OpenIpcPath/OpenWinClass; ClsidTrace → OpenClsid. |
| A9 | OpenWinClass – https://sandboxie-plus.github.io/sandboxie-docs/Content/OpenWinClass/ | sbdocs | Normally a sandboxed program cannot access, communicate, close or destroy a window outside the sandbox; OpenWinClass grants exceptions; `*` opens all windows + disables renaming; class names are translated to `Sandbox:<box>:<class>`. |
| A10 | How it Works – https://sandboxie-plus.github.io/sandboxie-docs/Content/HowitWorks.html | sbdocs | Interception model: program changes redirected into the sandbox container, disposable as a unit. |
| A11 | TechnicalAspects – https://sandboxie-plus.github.io/sandboxie-docs/Content/TechnicalAspects/ | sbdocs | "In-depth discussions of employed mechanisms and security guaranties" – official internals index. |
| A12 | Access Token Isolation – https://sandboxie-plus.github.io/sandboxie-docs/Content/AccessTokenIsolation.html | sbdocs | User-facing config of token-construction paths (referenced by TokenMagic as the current path doc). |
| A13 | KeyRootPath – https://sandboxie-plus.github.io/sandboxie-docs/Content/KeyRootPath/ | sbdocs | Sandboxed hive mounted at `\REGISTRY\USER\Sandbox_<user>_<box>`; RegHive/RegHive.LOG files in the box folder. |
| A14 | OpenIpcPath – https://sandboxie-plus.com/sandboxie/openipcpath/ | sbdocs | OpenIpcPath exposes specific IPC objects; `<prog.exe>,*` grants full access into the outside process's address space; default allows only read access. |
| A15 | OpenFilePath – https://sandboxie-plus.com/sandboxie/openfilepath/ | sbdocs | Punches a direct-access hole in FS virtualization; supports wildcards and program prefixes. |
| A16 | ReadFilePath – https://sandboxie-plus.com/sandboxie/readfilepath/ | sbdocs | Read-only variant of OpenFilePath. |
| A17 | DropAdminRights – https://sandboxie-plus.com/sandboxie/dropadminrights/ | sbdocs | Strips Administrators/Power Users membership from sandboxed process tokens. |
| A18 | Security-mode – https://sandboxie-plus.com/security-mode/ | sbdocs | UseSecurityMode = DropAdminRights + RestrictDevices + SysCallLockDown + UseRuleSpecificity (hardened box). |
| A19 | FakeAdminRights – https://sandboxie-plus.com/sandboxie/fakeadminrights/ | sbdocs | Simulates elevation so installers run under dropped rights. |
| A20 | WFP Support – https://sandboxie-plus.com/wfpsupport/ | sbdocs | NetworkEnableWFP; `NetworkAccess=<prog>,Allow/Block;Port=;Address=;Protocol=` per-box rules; user-mode fallback filter since v0.9.3. |
| A21 | BlockPort – https://sandboxie-plus.com/sandboxie/blockport/ | sbdocs | BlockPort removed → replaced by NetworkAccess rules (Template_BlockPorts). |
| A22 | SandboxieIni – https://sandboxie-plus.com/sandboxie/sandboxieini/ | sbdocs | Config: GlobalSettings + per-box sections, ≤32-char box names. |
| A23 | Feature Comparison – https://sandboxie-plus.com/feature-comparison/ | sbdocs | Plus & Classic share the same core components; supporter-cert features (encryption, proxy injection, DNS filtering, ARM64). |
| A24 | HookTrace – https://sandboxie-plus.github.io/sandboxie-docs/Content/HookTrace/ | sbdocs | Confirms SbieDll_HookInit() hook engine; HOOK_STAT_* statuses; ARM64 syscall-hook handling. |
| A25 | DefaultFolder – https://sandboxie-plus.github.io/sandboxie-docs/Content/DefaultFolder/ | sbdocs | Privacy-mode box pre-creates folders; cites file_dir.c File_CreateBaseFolders. |
| A26 | EnableEFS – https://sandboxie-plus.github.io/sandboxie-docs/Content/EnableEFS.html | sbdocs | EFS blocked by default; proxy open via UserServer + handle duplication. |
| A27 | Delete-V2 – https://github.com/sandboxie-plus/sandboxie-docs/blob/main/docs/Content/Delete-V2.md | sbdocs | FS/registry virtualization copy-on-write semantics: deleted host files marked via FilePaths.dat/KeyPaths.dat; rename creates redirection entry. |
| A28 | SBIE_DLL_API (archived) – https://sandboxie-website-archive.github.io/www.sandboxie.com/SBIE_DLL_API.html | sbdocs | SbieDll exports incl. programmatic "Hook a User-Mode Entrypoint." |
| A29 | sandboxie-docs repo – https://github.com/sandboxie-plus/sandboxie-docs | sbdocs | Community-maintained docs source rendered at sandboxie-plus.github.io and sandboxie-plus.com. |
| A30 | Downloads – https://sandboxie-plus.com/downloads/ | sbdocs | Current v1.18.2; Plus & Classic same core components/security. |

## B. Sandboxie – kernel driver (SbieDrv) source

| # | Source | Type | Fact |
|---|--------|------|------|
| B1 | core/drv/driver.c – https://github.com/sandboxie-plus/Sandboxie/blob/master/Sandboxie/core/drv/driver.c | source | DriverEntry init order: Process → Thread → File → Key → Ipc → Gui hooks → Api device → WFP_Init. |
| B2 | core/drv/api_defs.h – https://github.com/sandboxie-plus/Sandboxie/blob/master/Sandboxie/core/drv/api_defs.h | source | `\Device\SandboxieDriverApi`; CTL codes incl. 0x802/0x803 calling SeFilterToken/SepFilterToken; API_* enum. |
| B3 | core/drv/file.c – https://github.com/sandboxie-plus/Sandboxie/blob/master/Sandboxie/core/drv/file.c | source | File_Init: XP parse-procedure hook vs Vista+ minifilter registration. |
| B4 | core/drv/file_flt.c – https://github.com/sandboxie-plus/Sandboxie/blob/master/Sandboxie/core/drv/file_flt.c | source | FltRegisterFilter minifilter; comment: minifilter only filters real files – path interception also needed. |
| B5 | core/drv/key.c – https://github.com/sandboxie-plus/Sandboxie/blob/master/Sandboxie/core/drv/key.c | source | Registry filter via CmRegisterCallbackEx (key_flt.c); API_OPEN_KEY, unmount-hive API. |
| B6 | core/drv/obj.c – https://github.com/sandboxie-plus/Sandboxie/blob/master/Sandboxie/core/drv/obj.c | source | Kernel object-type table resolved by name (ALPC Port, Section, Mutant, JobObject, SymbolicLink…). |
| B7 | core/drv/obj_flt.c – https://github.com/sandboxie-plus/Sandboxie/blob/master/Sandboxie/core/drv/obj_flt.c | source | ObRegisterCallbacks object filter; maps types→handlers (Ipc_CheckGenericObject/CheckPortObject/CheckJobObject). |
| B8 | core/drv/syscall.c – https://github.com/sandboxie-plus/Sandboxie/blob/master/Sandboxie/core/drv/syscall.c | source | Syscall_Set1/Set2 handlers on SYSCALL_ENTRY; ApproveWinNtSysCall/DisableWinNtHook config; EnableWin32kHooks. |
| B9 | core/drv/syscall.h – https://github.com/sandboxie-plus/Sandboxie/blob/master/Sandboxie/core/drv/syscall.h | source | SYSCALL_ENTRY fields: syscall_index, param_count, ntdll_offset, ntos_func, handler funcs. |
| B10 | core/drv/syscall_64.c – https://github.com/sandboxie-plus/Sandboxie/blob/master/Sandboxie/core/drv/syscall_64.c | source | Locates KeServiceDescriptorTable, shadow/win32k filter table, kernel base. |
| B11 | core/drv/syscall_open.c – https://github.com/sandboxie-plus/Sandboxie/blob/master/Sandboxie/core/drv/syscall_open.c | source | Syscall_OpenHandle post-open access checks; NtGetNextProcess writable-handle risk note (ICD-11903). |
| B12 | core/drv/process.c – https://github.com/sandboxie-plus/Sandboxie/blob/master/Sandboxie/core/drv/process.c | source | Process_Create: File_CreateBoxPath → Ipc_CreateBoxPath → Key_MountHive → WFP_InitProcess → init hooks → Token_ReplacePrimary; process notify; forced programs. |
| B13 | core/drv/process.h – https://github.com/sandboxie-plus/Sandboxie/blob/master/Sandboxie/core/drv/process.h | source | PROCESS flags: drop_rights, bAppCompartment, can_use_jobs, primary_token, sbiedll_loaded. |
| B14 | core/drv/process_api.c – https://github.com/sandboxie-plus/Sandboxie/blob/master/Sandboxie/core/drv/process_api.c | source | SbieApi_QueryProcess returns flags incl. SBIE_FLAG_APP_COMPARTMENT, WIN32K_HOOKABLE, HOST_INJECT. |
| B15 | core/drv/process_util.c – https://github.com/sandboxie-plus/Sandboxie/blob/master/Sandboxie/core/drv/process_util.c | source | Process_IsInPcaJob detects `\BaseNamedObjects\PCA_*` job objects. |
| B16 | core/drv/token.c – https://github.com/sandboxie-plus/Sandboxie/blob/master/Sandboxie/core/drv/token.c | source | Token_ReplacePrimary → Token_Restrict(SANDBOX_INERT|DISABLE_MAX_PRIVILEGE); Untrusted integrity (Low if OpenWndStation); DropAdminRights; anonymous LUID; OriginalToken/UnfilteredToken escapes. |
| B17 | core/drv/thread.c – https://github.com/sandboxie-plus/Sandboxie/blob/master/Sandboxie/core/drv/thread.c | source | PsSetCreateThreadNotifyRoutine; Set1 handlers for token syscalls; Set2 checks on OpenProcess/OpenThread/AlpcOpenSender*. |
| B18 | core/drv/thread_token.c – https://github.com/sandboxie-plus/Sandboxie/blob/master/Sandboxie/core/drv/thread_token.c | source | Impersonation tokens re-filtered; non-matching → STATUS_ACCESS_DENIED. |
| B19 | core/drv/ipc.c – https://github.com/sandboxie-plus/Sandboxie/blob/master/Sandboxie/core/drv/ipc.c | source | Port syscall handlers (RequestPort, AlpcSendWaitReceivePort, ImpersonateClientOfPort); jobs must be named + ASSIGN/TERMINATE denied; comment: direct syscalls bypass the interface but restricted token/UIPI still applies. |
| B20 | core/drv/box.c – https://github.com/sandboxie-plus/Sandboxie/blob/master/Sandboxie/core/drv/box.c | source | Defaults: FileRootPath `\??\%SystemDrive%\Sandbox\%USER%\%SANDBOX%`, KeyRootPath `\REGISTRY\USER\Sandbox_%USER%_%SANDBOX%`, IpcRootPath `\Sandbox\%USER%_%SANDBOX%\Session_%SESSION%`. |
| B21 | core/drv/wfp.c – https://github.com/sandboxie-plus/Sandboxie/blob/master/Sandboxie/core/drv/wfp.c | source | WFP callout "SbieFilter" implementing per-box internet restrictions. |
| B22 | core/drv/conf.c – https://github.com/sandboxie-plus/Sandboxie/blob/master/Sandboxie/core/drv/conf.c | source | Driver parses Sandboxie.ini; runtime toggles NetworkEnableWFP, EnableObjectFiltering, Syscall_Update_Config. |
| B23 | core/drv/verify.c – https://github.com/sandboxie-plus/Sandboxie/blob/master/Sandboxie/core/drv/verify.c | source | RSA verify of Certificate.dat vs embedded trusted public key (BCryptVerifySignature). |
| B24 | core/drv/dyn_data.c – https://github.com/sandboxie-plus/Sandboxie/blob/master/Sandboxie/core/drv/dyn_data.c | source | Signed DynData offsets adapt the driver to kernel builds. |
| B25 | core/drv/util.c – https://github.com/sandboxie-plus/Sandboxie/blob/master/Sandboxie/core/drv/util.c | source | MyIsCallerSigned → KphVerifyCurrentProcess gates API callers. |
| B26 | core/drv/hook_32.c – https://github.com/sandboxie-plus/Sandboxie/blob/master/Sandboxie/core/drv/hook_32.c | source | Kernel function hooking; finds Zw routines by disassembling Zw stubs (32-bit). |

## C. Sandboxie – SbieDll user-mode hooks + low-level injector

| # | Source | Type | Fact |
|---|--------|------|------|
| C1 | core/dll/dllmain.c – https://github.com/sandboxie-plus/Sandboxie/blob/master/Sandboxie/core/dll/dllmain.c | source | DllMain → SbieDll_HookInit; queries box paths via SbieApi_QueryBoxPath; Gui_ConnectToWindowStationAndDesktop per thread; CompartmentMode flag. |
| C2 | core/dll/dllhook.c – https://github.com/sandboxie-plus/Sandboxie/blob/master/Sandboxie/core/dll/dllhook.c | source | SbieDll_Hook trampoline engine + common/hook_util.c; vendored common/Detours/detours.h – custom Detours-based hooks, not EasyHook. |
| C3 | core/dll/sbiedll.h – https://github.com/sandboxie-plus/Sandboxie/blob/master/Sandboxie/core/dll/sbiedll.h | source | SBIEDLL_HOOK macro wraps SbieDll_Hook; exported SbieDll_InjectLow. |
| C4 | core/dll/ipc.c – https://github.com/sandboxie-plus/Sandboxie/blob/master/Sandboxie/core/dll/ipc.c | source | Hooks NtCreate/Open for Event, EventPair, KeyedEvent, Timer, Mutant, Semaphore, Section(+Ex), MapView, SymLink, DirectoryObject → sandbox namespace. |
| C5 | core/dll/sysinfo.c – https://github.com/sandboxie-plus/Sandboxie/blob/master/Sandboxie/core/dll/sysinfo.c | source | Global\/Local\ normalization; unnamed jobs get Sbie_DummyJob_* names; objects prefixed with Dll_BoxIpcPath; AppContainerNamedObjects handling. |
| C6 | core/dll/file.c – https://github.com/sandboxie-plus/Sandboxie/blob/master/Sandboxie/core/dll/file.c | source | File_GetCopyPath = BoxFilePath + TruePath; composes file_link/pipe/del/snapshots/dir/recovery/copy modules. |
| C7 | core/dll/file_copy.c – https://github.com/sandboxie-plus/Sandboxie/blob/master/Sandboxie/core/dll/file_copy.c | source | File_MigrateFile copy-on-write: opens TruePath (driver fallback SbieApi_OpenFile on sharing violation), copies into CopyPath. |
| C8 | core/dll/file_del.c – https://github.com/sandboxie-plus/Sandboxie/blob/master/Sandboxie/core/dll/file_del.c | source | Tombstones: FILE_DELETED_FLAG/RELOCATION flags; v2 marks in FilePaths.dat/RegPaths.dat. |
| C9 | core/dll/file_recovery.c – https://github.com/sandboxie-plus/Sandboxie/blob/master/Sandboxie/core/dll/file_recovery.c | source | Immediate Recovery file lists (RecoverFolder, AutoRecoverIgnore). |
| C10 | core/dll/file_pipe.c – https://github.com/sandboxie-plus/Sandboxie/blob/master/Sandboxie/core/dll/file_pipe.c | source | Named-pipe/mailslot creation redirected to box pipe path; preserves AppContainerNamedObjects\<SID>\ structure. |
| C11 | core/dll/key.c – https://github.com/sandboxie-plus/Sandboxie/blob/master/Sandboxie/core/dll/key.c | source | Key_GetTruePath translates handles/names to \registry paths for redirection. |
| C12 | core/dll/key_merge.c – https://github.com/sandboxie-plus/Sandboxie/blob/master/Sandboxie/core/dll/key_merge.c | source | Merged view of sandboxed + real keys. |
| C13 | core/dll/lowlevel_inject.c – https://github.com/sandboxie-plus/Sandboxie/blob/master/Sandboxie/core/dll/lowlevel_inject.c | source | SbieDll_InjectLow fills SBIELOW_DATA; resolves LdrInitializeThunk (+EC variant on ARM64). |
| C14 | core/low/init.c – https://github.com/sandboxie-plus/Sandboxie/blob/master/Sandboxie/core/low/init.c | source | EntrypointC synchronizes threads via Init_Lock, runs low-level init, jumps to LdrInitializeThunk; DetourCode loads SbieDll before process init. |
| C15 | core/low/entry_arm.asm – https://github.com/sandboxie-plus/Sandboxie/blob/master/Sandboxie/core/low/entry_arm.asm | source | ARM64 entry: calls EntrypointC, br x8 to LdrInitializeThunk trampoline. |
| C16 | core/dll/gui.c – https://github.com/sandboxie-plus/Sandboxie/blob/master/Sandboxie/core/dll/gui.c | source | Hooks CreateWindowExA/W, UserHandleGrantAccess, IsWindow*, MessageBox; Gui_ConnectToWindowStationAndDesktop. |
| C17 | core/dll/guiclass.c – https://github.com/sandboxie-plus/Sandboxie/blob/master/Sandboxie/core/dll/guiclass.c | source | Window classes renamed with `Sandbox:<box>:` prefix; OpenWinClass `*` disables; NoRenameWinClass patterns; hooks GetClassName. |
| C18 | core/dll/guimisc.c – https://github.com/sandboxie-plus/Sandboxie/blob/master/Sandboxie/core/dll/guimisc.c | source | Hooks SetParent, SetForegroundWindow, ClipCursor, BlockInput, SendInput; Gui_SendInput aborts if foreground window not in same box (shatter protection); GetDC/PrintWindow capture blocking. |
| C19 | core/dll/gui_p.h – https://github.com/sandboxie-plus/Sandboxie/blob/master/Sandboxie/core/dll/gui_p.h | source | Hooked prototypes: SendMessage, SendMessageTimeout, SendNotifyMessage, PostMessage, PostThreadMessage, DispatchMessage. |
| C20 | core/dll/sh.c – https://github.com/sandboxie-plus/Sandboxie/blob/994ef2cc/Sandboxie/core/dll/sh.c | source | `[#]` title-marker injection + Shell_NotifyIconW proxy via GuiServer when OpenWinClass=* (FindWindowW/SendMessageW hooks not installed). |
| C21 | core/dll/proc.c – https://github.com/sandboxie-plus/Sandboxie/blob/master/Sandboxie/core/dll/proc.c | source | Hooks NtCreateUserProcess, CreateProcessInternalW, RtlCreateProcessParametersEx, SetProcessMitigationPolicy; fake CreateAppContainerToken outside compartment mode. |
| C22 | core/dll/advapi.c – https://github.com/sandboxie-plus/Sandboxie/blob/master/Sandboxie/core/dll/advapi.c | source | UseSbieDeskHack hooks SetSecurityInfo/GetSecurityInfo so Chrome passes DACL checks via dummy window station. |
| C23 | core/dll/sxs.c – https://github.com/sandboxie-plus/Sandboxie/blob/master/Sandboxie/core/dll/sxs.c | source | Mounts real HKLM\COMPONENTS for compatibility; hooks CheckTokenMembership. |
| C24 | core/dll/rpcrt.c – https://github.com/sandboxie-plus/Sandboxie/blob/master/Sandboxie/core/dll/rpcrt.c | source | Injects real spooler port into binding string; sandboxed epmapper bypass; port treated as built-in OpenIpcPath. |
| C25 | core/dll/net.c – https://github.com/sandboxie-plus/Sandboxie/blob/master/Sandboxie/core/dll/net.c | source | WSA socket hooks; SbieApi_CheckInternetAccess; PromptForInternetAccess; DNS-filter hooks. |
| C26 | core/dll/ldr_init.c – https://github.com/sandboxie-plus/Sandboxie/blob/master/Sandboxie/core/dll/ldr_init.c | source | Ldr_LoadInjectDlls loads user InjectDll/InjectDll64 DLLs. |

## D. Sandboxie – SbieSvc broker and helpers

| # | Source | Type | Fact |
|---|--------|------|------|
| D1 | core/svc/main.cpp – https://github.com/sandboxie-plus/Sandboxie/blob/master/Sandboxie/core/svc/main.cpp | source | SbieSvc service; spawns _ComProxy, _UacProxy, _NetProxy, _GuiProxy, _UserProxy slave processes. |
| D2 | core/svc/DriverAssist.cpp – https://github.com/sandboxie-plus/Sandboxie/blob/master/Sandboxie/core/svc/DriverAssist.cpp | source | LPC worker: driver messages SVC_INJECT_PROCESS→InjectLow, SVC_MOUNTED_HIVE, SVC_CONFIG_UPDATED, SVC_LOG_MESSAGE. |
| D3 | core/svc/DriverAssistInject.cpp – https://github.com/sandboxie-plus/Sandboxie/blob/master/Sandboxie/core/svc/DriverAssistInject.cpp | source | InjectLow: verifies process create time, queries box paths/flags, injects SbieLow into the target. |
| D4 | core/svc/DriverAssistStart.cpp – https://github.com/sandboxie-plus/Sandboxie/blob/master/Sandboxie/core/svc/DriverAssistStart.cpp | source | Starts SbieDrv via NtLoadDriver; ABI version check. |
| D5 | core/svc/ProcessServer.cpp – https://github.com/sandboxie-plus/Sandboxie/blob/master/Sandboxie/core/svc/ProcessServer.cpp | source | PipeServer MSGID_PROCESS: RunSandboxed, KillOne/KillAll, Suspend/Resume handlers. |
| D6 | core/svc/GuiServer.cpp – https://github.com/sandboxie-plus/Sandboxie/blob/master/Sandboxie/core/svc/GuiServer.cpp | source | Creates `Sandboxie_WinSta_<tick>` window station + desktop with NULL DACL and untrusted-integrity SACL; GUI proxy slaves (EnumWindows, FindWindow, SendPostMessage, clipboard). |
| D7 | core/svc/EpMapperServer.cpp – https://github.com/sandboxie-plus/Sandboxie/blob/master/Sandboxie/core/svc/EpMapperServer.cpp | source | Sandboxed RPC endpoint mapper; port-ID→interface UUID; OpenSmartCard/ClosePrintSpooler gates. |
| D8 | core/svc/UserServer.cpp – https://github.com/sandboxie-plus/Sandboxie/blob/master/Sandboxie/core/svc/UserServer.cpp | source | Per-user worker via CreateProcessAsUser; EFS/proxy file open helpers. |
| D9 | apps/com/RpcSs/rpcss.c – https://github.com/sandboxie-plus/Sandboxie/blob/master/Sandboxie/apps/com/RpcSs/rpcss.c | source | Runs real rpcss.dll/RpcEptMapper ServiceMain inside the box when COM isn't opened – sandboxed COM universe. |
| D10 | Sandboxie/ReadMe.md – https://github.com/sandboxie-plus/Sandboxie/blob/master/Sandboxie/ReadMe.md | source | Core = SbieDrv + SbieSvc + SbieDll; core/low builds LowLevel.dll embedded in SbieSvc.exe as a resource. |
| D11 | xanasoft/Sandboxie history – https://github.com/xanasoft/Sandboxie | source | Timeline: 2004–2013 Ronen Tzur; 2013–2017 Invincea; 2017–2020 Sophos; GPL open-source 8 Apr 2020; Xanatos fork 9 Apr 2020. |
| D12 | Sophos open-source announcement – https://www.sophos.com/en-us/blog/sandboxie-is-now-an-open-source-tool | sbdocs | Sophos released Sandboxie open source; "integrates with Windows at a very low level." |
| D13 | BleepingComputer coverage – https://www.bleepingcomputer.com/news/software/the-sandboxie-windows-sandbox-isolation-tool-is-now-open-source/ | secondary | Dates: original 26 Jun 2004; Invincea Dec 2013; Sophos Feb 2017; free license Sept 2019. |

## E. Third-party analysis of Sandboxie internals

| # | Source | Type | Fact |
|---|--------|------|------|
| E1 | vallejo.cc: Sandboxie process isolation with kernel hooks – https://web.archive.org/web/20130429072246/http:/vallejo.cc/48 | secondary | SbieDrv hooks kernel objects' OpenProcedure (token, process, thread, event, section, port, semaphore) + SSDT and shadow-SSDT entries: win32k NtUserSendInput, NtUserBlockInput, NtUserPostMessage, NtUserPostThreadMessage, NtUserSetWindowsHookEx, NtUserMessageCall… – the window-message interception layer. |

## F. Windows primitives – tokens, integrity, UIPI

| # | Source | Type | Fact |
|---|--------|------|------|
| F1 | CreateRestrictedToken – https://learn.microsoft.com/en-us/windows/win32/api/securitybaseapi/nf-securitybaseapi-createrestrictedtoken | osdoc | Restricted token via deny-only SIDs, deleted privileges, restricting SIDs. |
| F2 | Restricted Tokens – https://learn.microsoft.com/en-us/windows/win32/secauthz/restricted-tokens | osdoc | Access requires both token SIDs AND restricting-SID checks to pass. |
| F3 | SID Attributes in an Access Token – https://learn.microsoft.com/en-us/windows/win32/secauthz/sid-attributes-in-an-access-token | osdoc | Deny-only SID: deny ACEs apply, allow ACEs ignored; cannot be re-enabled. |
| F4 | Mandatory Integrity Control – https://learn.microsoft.com/en-us/windows/win32/secauthz/mandatory-integrity-control | osdoc | MIC evaluated before DACL; integrity SID in SACL; low-IL cannot write medium objects even if DACL allows. |
| F5 | ChangeWindowMessageFilterEx – https://learn.microsoft.com/en-us/windows/win32/api/winuser/nf-winuser-changewindowmessagefilterex | osdoc | UIPI blocks messages from lower-IL senders; per-window allow-list; low-IL processes can't change the filter. |
| F6 | ChangeWindowMessageFilter – https://learn.microsoft.com/en-us/windows/win32/api/winuser/nf-winuser-changewindowmessagefilter | osdoc | Process-wide UIPI filter; messages >WM_USER blocked by default. |
| F7 | Designing Applications to Run at Low IL – https://learn.microsoft.com/en-us/previous-versions/dotnet/articles/bb625960(v=msdn.10) | osdoc | Low-IL blocks most window messages + hooks (UIPI), CreateRemoteThread, shared sections, higher-IL named objects; allowed: clipboard, RPC, sockets. |
| F8 | IE Protected Mode (IE blog) – https://learn.microsoft.com/en-us/archive/blogs/ie/protected-mode-in-vista-ie7 | osdoc | IE7 PM = UAC + MIC + UIPI; UIPI "protects against shatter attacks." |
| F9 | MIC in Windows Vista (compat blog) – https://learn.microsoft.com/en-us/archive/blogs/steriley/mandatory-integrity-control-in-windows-vista | osdoc | IEPM writes only to low-IL locations; compat mode virtualizes writes (Virtualized dirs + InternetRegistry). |

## G. Windows primitives – AppContainer, jobs, namespaces

| # | Source | Type | Fact |
|---|--------|------|------|
| G1 | Implementing an AppContainer – https://learn.microsoft.com/en-us/windows/win32/secauthz/implementing-an-appcontainer | osdoc | AC access = intersection of user/group SIDs AND AppContainer/capability SIDs; runs at Low IL. |
| G2 | AppContainer Isolation – https://learn.microsoft.com/en-us/windows/win32/secauthz/appcontainer-isolation | osdoc | AC isolates files, registry, network, devices, credentials; **"keyboard and mouse are always available"** – input is not the isolation boundary. |
| G3 | GetAppContainerNamedObjectPath – https://learn.microsoft.com/en-us/windows/win32/api/securityappcontainer/nf-securityappcontainer-getappcontainernamedobjectpath | osdoc | Each app container has its own named object path; global/session objects inaccessible by default. |
| G4 | CreateAppContainerProfile – https://learn.microsoft.com/en-us/windows/win32/api/userenv/nf-userenv-createappcontainerprofile | osdoc | Per-user, per-app profile folders + registry ACL'd to package + capability SIDs. |
| G5 | AppContainer SID constants – https://learn.microsoft.com/en-us/windows/win32/secauthz/app-container-sid-constants | osdoc | SECURITY_APP_PACKAGE_AUTHORITY + capability RID structure – per-package SIDs. |
| G6 | Edge RendererAppContainerEnabled – https://learn.microsoft.com/en-us/DeployEdge/microsoft-edge-policies/rendererappcontainerenabled | osdoc | Edge ≥96 launches renderers into AppContainer (Win10 RS5+). |
| G7 | WebView2 sandboxing – https://learn.microsoft.com/en-us/microsoft-edge/webview2/concepts/measures | osdoc | WebView2 renderers run LowIL or AppContainer; DLL injection "breaks Chromium's sandboxing model." |
| G8 | JOBOBJECT_BASIC_UI_RESTRICTIONS – https://learn.microsoft.com/en-us/windows/win32/api/winnt/ns-winnt-jobobject_basic_ui_restrictions | osdoc | UILIMIT_HANDLES blocks USER handles owned by non-job processes; READCLIPBOARD/WRITECLIPBOARD, DESKTOP, GLOBALATOMS, EXITWINDOWS restrictions. |
| G9 | Job Objects – https://learn.microsoft.com/en-us/windows/win32/procthread/job-objects | osdoc | Children auto-join job unless breakaway; KILL_ON_JOB_CLOSE; nested jobs since Win8. |
| G10 | AssignProcessToJobObject – https://learn.microsoft.com/en-us/windows/win32/api/jobapi2/nf-jobapi2-assignprocesstojobobject | osdoc | Association cannot be broken; UI-limit jobs cannot nest; breakaway rules. |
| G11 | JOBOBJECT_SECURITY_LIMIT_INFORMATION – https://learn.microsoft.com/en-us/windows/win32/api/winnt/ns-winnt-jobobject_security_limit_information | osdoc | Pre-Vista job token limits: NO_ADMIN, ONLY_TOKEN, RESTRICTED_TOKEN, FILTER_TOKENS. |
| G12 | Object Namespaces – https://learn.microsoft.com/en-us/windows/win32/sync/object-namespaces | osdoc | Private namespace via CreatePrivateNamespace + boundary descriptor; same-named namespaces coexist with different boundaries. |
| G13 | CreatePrivateNamespace – https://learn.microsoft.com/en-us/windows/win32/api/winbase/nf-winbase-createprivatenamespacea | osdoc | Boundary descriptor defines isolation; APPCONTAINER_SID flag needed in AC context. |
| G14 | Kernel Object Namespaces – https://learn.microsoft.com/en-us/windows/win32/termserv/kernel-object-namespaces | osdoc | Global\ + per-session Local\ namespaces; Global\ needs SeCreateGlobalPrivilege for sections/symlinks. |
| G15 | IoCreateNotificationEvent – https://learn.microsoft.com/en-us/windows-hardware/drivers/ddi/wdm/nf-wdm-iocreatenotificationevent | osdoc | Kernel objects in \BaseNamedObjects; user-mode reaches via Global\ prefix. |

## H. Windows primitives – FS/registry virtualization + interception

| # | Source | Type | Fact |
|---|--------|------|------|
| H1 | Registry Virtualization – https://learn.microsoft.com/en-us/windows/win32/sysinfo/registry-virtualization | osdoc | UAC redirects HKLM\Software writes to per-user VirtualStore transparently since Vista. |
| H2 | UAC Virtualization (TechNet Mag) – https://learn.microsoft.com/en-us/previous-versions/technet-magazine/cc138019(v=msdn.10) | osdoc | Protected writes redirect to %LOCALAPPDATA%\VirtualStore; virtualization flag in the process token; driver = Luafv. |
| H3 | Minifilter altitudes/load order – https://learn.microsoft.com/en-us/windows-hardware/drivers/ifs/load-order-groups-and-altitudes-for-minifilter-drivers | osdoc | Unique altitude sets filter position in the I/O stack; Microsoft assigns altitudes. |
| H4 | Filter Manager concepts – https://learn.microsoft.com/en-us/windows-hardware/drivers/ifs/filter-manager-concepts | osdoc | FltMgr.sys in-box; minifilters register pre/post-operation callbacks per I/O op. |
| H5 | ProjFS – https://learn.microsoft.com/en-us/windows/win32/projfs/projected-file-system | osdoc | User-mode provider projects backing store under a virtualization root; files materialized via provider callbacks (VFS for Git). |
| H6 | Detours (USENIX NT'99) – https://usenix.org/legacy/events/usenix-nt99/full_papers/hunt/hunt.pdf | paper | Intercepts Win32 functions by rewriting target function images in-memory; trampoline preserves the original as a callable subroutine – the technique class behind SbieDll/Chromium hooks. |

## I. Windows primitives – GUI isolation, win32k, IPC

| # | Source | Type | Fact |
|---|--------|------|------|
| I1 | Window Stations – https://learn.microsoft.com/en-us/windows/win32/winstation/window-stations | osdoc | Window station = securable object containing clipboard + atom table + desktops; only Winsta0 is interactive – can display UI AND receive user input. |
| I2 | Desktops – https://learn.microsoft.com/en-us/windows/win32/winstation/desktops | osdoc | "Window messages can be sent only between processes on the same desktop"; hooks only see same-desktop windows – the desktop is the shatter boundary. |
| I3 | Window Station/Desktop Creation – https://learn.microsoft.com/en-us/windows/win32/winstation/window-station-and-desktop-creation | osdoc | DACL rights: WINSTA_ACCESSCLIPBOARD, WINSTA_ACCESSGLOBALATOMS, WINSTA_CREATEDESKTOP; noninteractive services get own winstation. |
| I4 | PROCESS_MITIGATION_SYSTEM_CALL_DISABLE_POLICY – https://learn.microsoft.com/en-us/windows/win32/api/winnt/ns-winnt-process_mitigation_system_call_disable_policy | osdoc | DisallowWin32kSystemCalls=1 → process cannot perform GUI (win32k) syscalls at all – kernel-level GUI lockout used by sandboxed renderers. |
| I5 | SetProcessMitigationPolicy – https://learn.microsoft.com/en-us/windows/win32/api/processthreadsapi/nf-processthreadsapi-setprocessmitigationpolicy | osdoc | ProcessSystemCallDisablePolicy "disables ability to use NTUser/GDI functions at the lowest layer." |
| I6 | RPC_BINDING_HANDLE_SECURITY_V1 – https://learn.microsoft.com/en-us/windows/win32/api/rpcdce/ns-rpcdce-rpc_binding_handle_security_v1_a | osdoc | ncalrpc (local RPC over ALPC) uses kernel-provided transport security; dynamic identity tracking + impersonation QoS. |
| I7 | RPC Interface Restriction – https://learn.microsoft.com/en-us/windows-server/security/rpc-interface-restrict | osdoc | RestrictRemoteClients forces auth checks; RpcServerRegisterIf security callback = server-side access control for local IPC. |
| I8 | LPC architecture (ntdebugging) – https://learn.microsoft.com/en-us/archive/blogs/ntdebugging/lpc-local-procedure-calls-part-1-architecture | osdoc | LPCP_PORT_OBJECT holds SECURITY_QUALITY_OF_SERVICE + SECURITY_CLIENT_CONTEXT – impersonation context per connection. |
| I9 | CWE-422 Shatter – https://cwe.mitre.org/data/definitions/422.html | spec | Unprotected Windows messaging lets a lower-privilege sender reach an elevated process; cites Paget 2002. |
| I10 | Paget Shatter paper (archive) – https://web.archive.org/web/20060115174629/http://security.tombom.co.uk/shatter.html | paper | Any process on a desktop can SendMessage any window on the same desktop; no message-source authentication. |

## J. Chromium sandbox (the same model, documented)

| # | Source | Type | Fact |
|---|--------|------|------|
| J1 | sandbox.md design doc – https://chromium.googlesource.com/chromium/src/+/HEAD/docs/design/sandbox.md | osdoc | "Sandbox operates at process-level granularity." Core = 4 mechanisms: restricted token, job object, desktop object, integrity levels. Job blocks SystemParametersInfo, desktop switch, clipboard R/W, broadcasts, SetWindowsHookEx, global atoms, external USER handles. |
| J2 | sandbox_faq.md – https://chromium.googlesource.com/chromium/src/+/HEAD/docs/design/sandbox_faq.md | osdoc | "The only resources sandboxed processes can freely use are CPU cycles and memory"; relies on the Windows security model so access checks fail. |
| J3 | sandbox.h – https://chromium.googlesource.com/chromium/src/+/refs/heads/main/sandbox/win/src/sandbox.h | source | BrokerServices::SpawnTargetAsync (suspended child + policy) / TargetServices::LowerToken (privilege drop in target). |
| J4 | sandbox README – https://chromium.googlesource.com/chromium/src.git/+/refs/heads/lkgr/sandbox/README.md | source | "win/ uses a combination of restricted tokens, distinct job objects, alternate desktops, and integrity levels." |
| J5 | sandbox_win.cc – https://chromium.googlesource.com/chromium/src/+/lkgr/sandbox/policy/win/sandbox_win.cc | source | Default: delayed IL UNTRUSTED, initial LOW, token USER_LOCKDOWN, lockdown DACL, Desktop::kAlternateWinstation, JobLevel::kLockdown, closes DeviceApi handles. |
| J6 | BUILD.gn sandbox/win – https://chromium.googlesource.com/chromium/src/+/141.0.7390.122/sandbox/win/BUILD.gn | source | File inventory: alternate_desktop.cc, app_container_base.cc, filesystem_interception, handle_closer, interception, policy_engine, sharedmem_ipc, target_process. |
| J7 | target_process.cc – https://chromium.googlesource.com/chromium/src/sandbox/+/refs/heads/main/win/src/target_process.cc | source | Broker maps a shared-memory IPC section into the suspended target before main()/CRT; CrossCall dispatcher services target IPC. |
| J8 | restricted_token.cc – https://chromium.googlesource.com/chromium/src/+/48.0.2556.0/sandbox/win/src/restricted_token.cc | source | Calls ::CreateRestrictedToken with SANDBOX_INERT; falls back to DuplicateTokenEx. |
| J9 | restricted_token_utils.cc – https://chromium.googlesource.com/chromium/src/sandbox/+/refs/heads/main/win/src/restricted_token_utils.cc | source | Token levels USER_UNPROTECTED → USER_LOCKDOWN; per-target restricted SID + lockdown default DACL. |
| J10 | interception.cc – https://chromium.googlesource.com/chromium/src/+/01c8afd0dc14a1acef383c5f231258d0cfac95e5/sandbox/win/src/interception.cc | source | InterceptionManager::InitializeInterceptions → PatchNtdll; always intercepts NtMapViewOfSection/NtUnmapViewOfSection to track module loads. |
| J11 | interceptors_64.cc – https://chromium.googlesource.com/chromium/src/+/refs/heads/main/sandbox/win/src/interceptors_64.cc | source | TargetNtCreateFile64 etc. forward Nt* calls through the interception layer. |
| J12 | target_interceptions.h – https://chromium.googlesource.com/chromium/src/+/430d8ebfe6d4033d47bbebec5ecc117e97b21688/sandbox/win/src/target_interceptions.h | source | In-target section-map hooks detect DLL loads to patch/clean interceptions. |
| J13 | signed_interception.cc – https://chromium.googlesource.com/chromium/src/+/430d8ebfe6d4033d47bbebec5ecc117e97b21688/sandbox/win/src/signed_interception.cc | source | TargetNtCreateSection → QueryBroker via CrossCall shared-memory IPC; denies with STATUS_INVALID_IMAGE_HASH. |
| J14 | Firefox Security/Sandbox – https://wiki.mozilla.org/Security/Sandbox | sbdocs | Firefox Windows content sandbox Level 6+: JOB_LOCKDOWN, USER_RESTRICTED token, alternate desktop AND alternate window station, IL low→untrusted, mitigation set incl. Win32k restrictions. |
| J15 | Firefox Security/Sandbox/Specifics – https://wiki.mozilla.org/Security/Sandbox/Specifics | sbdocs | Firefox uses the Chromium sandbox library (security/sandbox/chromium/sandbox/win) via broker/target shims. |

## K. Network isolation + containers + research models

| # | Source | Type | Fact |
|---|--------|------|------|
| K1 | WFP start page – https://learn.microsoft.com/en-us/windows/win32/fwp/windows-filtering-platform-start-page | osdoc | WFP = user + kernel APIs for packet filtering; replaces TDI/NDIS-filter/LSP. |
| K2 | WFP architecture – https://learn.microsoft.com/en-us/windows/win32/fwp/windows-filtering-platform-architecture-overview | osdoc | ~50 kernel filtering layers; callout drivers add classification/inspection. |
| K3 | WFP basic operation – https://learn.microsoft.com/en-us/windows/win32/fwp/basic-operation | osdoc | Shims classify packets, filter engine evaluates, shims enforce; ALE Connect/Receive-Accept layers for per-app policy. |
| K4 | UWP Firewall troubleshooting – https://learn.microsoft.com/en-us/windows/security/operating-system-security/network-security/windows-firewall/troubleshooting-uwp-firewall | osdoc | Default block filters enforce AppContainer network isolation; loopback blocked by default. |
| K5 | WFP filtering condition flags – https://learn.microsoft.com/en-us/windows/win32/fwp/filtering-condition-flags- | osdoc | FWP_CONDITION_FLAG_IS_APPCONTAINER_LOOPBACK distinguishes AC loopback traffic. |
| K6 | MDAG overview – https://learn.microsoft.com/en-us/windows/security/application-security/application-isolation/microsoft-defender-application-guard/md-app-guard-overview | osdoc | Untrusted content in an isolated Hyper-V container with a separate kernel (deprecated Win11 24H2). |
| K7 | Windows Sandbox architecture – https://learn.microsoft.com/en-us/windows/security/application-security/application-isolation/windows-sandbox/windows-sandbox-architecture | osdoc | Dynamic Base Image: immutable host files shared + pristine mutable copies; 30-MB compressed package. |
| K8 | Windows Sandbox overview – https://learn.microsoft.com/en-us/windows/security/application-security/application-isolation/windows-sandbox/ | osdoc | Hardware-based virtualization, separate kernel, disposable VM. |
| K9 | Container isolation modes – https://learn.microsoft.com/en-us/virtualization/windowscontainers/manage-containers/hyperv-container | osdoc | Process isolation: shared kernel, per-container virtualized namespaces – FS, registry, network ports, PID space, Object Manager namespace. |
| K10 | MSDN Mag: Windows Server Containers – https://learn.microsoft.com/en-us/archive/msdn-magazine/2017/april/containers-bringing-docker-to-windows-developers-with-windows-server-containers | osdoc | Server silos = job objects + isolated FS/registry/object namespaces – like Linux namespaces; basis of Windows containers. |
| K11 | Container resource controls – https://learn.microsoft.com/en-us/virtualization/windowscontainers/manage-containers/resource-controls | osdoc | Containers tracked via parent job object; Hyper-V isolation bounds even job-escaped processes. |
| K12 | PsGetJobServerSilo – https://learn.microsoft.com/en-us/windows-hardware/drivers/ddi/ntddk/nf-ntddk-psgetjobserversilo | osdoc | Kernel API returns a job's ServerSilo – silos are job-object attributes. |
| K13 | Drawbridge project – https://microsoft.com/en-us/research/project/drawbridge/ | paper | Picoprocess = process-based isolation; ABI = 45 fixed downcalls serviced by a security monitor that virtualizes host OS resources. |
| K14 | Drawbridge ASPLOS'11 paper – https://microsoft.com/en-us/research/wp-content/uploads/2016/02/asplos2011-drawbridge.pdf | paper | "The security monitor virtualizes host OS resources through its ABI with the library OS." |
| K15 | Pico Process Overview (WSL blog) – https://learn.microsoft.com/en-us/archive/blogs/wsl/pico-process-overview | osdoc | Kernel driver brokers between host kernel and user-mode library OS; pico processes became production (LXSS/WSL). |
