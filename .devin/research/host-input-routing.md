# Windows Scoped Synthetic Input - Research Report

**Verdict:** Windows has no user-mode API that routes *real* input events to a chosen HWND. Every "background input" path either (a) fakes messages and depends on the target's gullibility, (b) hijacks the shared foreground input stream, or (c) puts the target in a different input universe (VM, RDP session, browser renderer, console buffer).

## 1. MESSAGE-LEVEL INPUT (PostMessage/SendMessage)

`PostMessage`/`SendMessage` with WM_KEYDOWN/UP, WM_CHAR, WM_SYSKEY*, WM_LBUTTON*, WM_MOUSEMOVE, WM_MOUSEWHEEL, WM_SETCURSOR delivers to an HWND without focus *to deliver*.

**Documented unreliability** (Raymond Chen x2): posted messages bypass the input queue - no WH_KEYBOARD hook firing, no shift-state updates (GetKeyState/GetAsyncKeyState see real state), no dead-key/IME processing. Works only as far as "the program allows itself to be fooled" [S1][S2].

| Target class | Result |
|---|---|
| Win32 standard controls (Edit, Button, VB6/VCL/MFC) | works for WM_CHAR/WM_KEYDOWN into the *child* control HWND (Notepad: target Edit child, not frame) [S3][S16]. VB6 windowless: works minimized if WM_ACTIVATE WA_ACTIVE precedes WM_LBUTTON* [S5] |
| Qt | works same-IL; UIPI blocks otherwise (ERROR_ACCESS_DENIED, needs uiAccess=true) [S108][S109] |
| Chromium/Electron | FAILS. Field code blacklists all Chrome_* classes for WM_CHAR [S8]. Chromium filters WM_KEYDOWN it didn't initiate [S10]. WH_KEYBOARD_LL delivery flaky when Chromium foreground [S11] |
| UWP/WinUI | PostMessage returns success, input swallowed; XAML ignores WM_CHAR [S8][S9][S106][S107] |
| Windows Terminal | WM_CHAR swallowed by XAML pipeline - explicitly unsupported [S8][S9]; conhost proper works via WriteConsoleInput (sec.6) |
| Games (DX/DirectInput/raw) | fails when game reads below message level (DirectInput GetDeviceState, WM_INPUT raw, GetAsyncKeyState) [S85][S87][S25] |
| Menus/toolbars | WM_LBUTTON* reaches client area only; menus need WM_COMMAND w/ command ID [S6] |

**Mouse:** WM_LBUTTONDOWN/UP posts with client coords in lParam - bypasses hit-testing, cursor position, WM_MOUSEACTIVATE. Works on gullible apps [S5][S112]; games may require real SetCursorPos [S7][S111]. WM_SETCURSOR only fires on real cursor movement - posting is cosmetic [S75]. WM_MOUSEWHEEL follows keyboard focus - posting to background HWND inconsistent [S24].

**Tooling precedent:** AutoHotkey ControlSend/ControlClick works background; docs warn interference, recommend SetControlDelay -1 + NA (no-activate) [S12][S13][S15].

## 2. SENDINPUT - VERIFIED: NO PER-WINDOW SCOPING

- SendInput inserts "serially into the keyboard or mouse input stream" - same stream as hardware; **no destination parameter** [S16]. "SendInput doesn't know what will happen to the input" [S63].
- Keyboard->focus window; mouse->under-cursor (or capture); wheel->focus [S24].
- keybd_event/mouse_event superseded, same semantics [S17][S18].
- AttachThreadInput+SetFocus moves *which* focus, never scopes *to HWND* - target still steals activation [S23][S64].
- UIPI: injection only into equal/lower IL, fails silently [S16][S108].
- **Detectability:** LLKHF_INJECTED/LLKHF_LOWER_IL_INJECTED (KBDLLHOOKSTRUCT); LLMHF_INJECTED/LLMHF_LOWER_IL_INJECTED (MSLLHOOKSTRUCT) - kernel-set, unavoidable user-mode [S20][S21][S22]. Raw Input hDevice NULL for injected [S22]. Driver-level injection evades [S19][S51].
- InputInjector (WinRT): same global stream; needs inputInjectionBrokered capability; can hit elevated apps; still no HWND targeting [S26][S27][S28][S29].

## 3. UI AUTOMATION - THE SANCTIONED BACKGROUND PATH

- Control patterns act on provider semantics, not input pipeline - **work on background/occluded/non-foreground windows** for most framework controls [S30][S38].
- InvokePattern.Invoke - activation without click [S31][S32]. ExpandCollapse, Toggle, SelectionItem likewise.
- ValuePattern.SetValue - set edit text w/o keystrokes. TextPattern is READ-ONLY ("does not insert text") [S37][S115].
- ScrollPattern - scroll by % = mouse-wheel substitute w/o cursor [S30]. TransformPattern - move/resize.
- Coverage: WinForms/WPF/UIA-native good; Qt5 partial; **Chromium needs --force-renderer-accessibility** [S97]. Custom/DX/game UIs: dead end.
- **UIAccess** (uiAccess=true manifest): bypasses UIPI; requires Authenticode signature + secure location + admin for high IL [S34][S35][S36]. Only user-mode privilege expanding UIA reach.

## 4. HOOKS & JOURNAL

- WH_JOURNALRECORD/PLAYBACK: **unsupported since Win11, slated removal** [S39][S40][S41]; playback DISABLES all real mouse/kbd input - the exact hijack we avoid [S39][S40]; crippled since Vista [S42].
- LL hooks (WH_KEYBOARD_LL/WH_MOUSE_LL): observe-and-veto only; can suppress real input; **cannot inject or redirect to background window** [S19][S20].
- WH_KEYBOARD (in-proc): posted messages never trigger it - how apps detect PostMessage input [S2].

## 5. VIRTUAL HID / DRIVER PATHS

| Solution | Mechanism | Scoped to one app? |
|---|---|---|
| ViGEmBus | KMDF bus driver, virtual X360/DS4 PDOs; reports as real hardware; per-*session* ownership only [S43][S44][S45] | NO (gamepads have no focus routing anyway) |
| vmulti | virtual HID mouse+kbd+touch; "moves THE cursor" - global stream [S46][S47] | NO |
| Interception | kernel filter on real devices; re-inject indistinguishable from hardware (no *_INJECTED) - still shared stream [S48-51] | NO |
| HidHide | inverse: hides devices from non-whitelisted processes - scopes VISIBILITY not delivery [S54-56] | n/a |
| Parsec PVUD | proprietary virtual USB host controller; Riot-whitelisted [S84] | NO |

Drivers raise fidelity to hardware-level and beat *_INJECTED - **cannot create a second input stream per window. Windows has exactly one interactive input stream per input desktop** [S63][S64].

## 6. RDP / SESSION / VM - TRUE INPUT INDEPENDENCE

| Environment | Independence |
|---|---|
| RDP session (incl RemoteApp) | own RdpDD.sys/RdpWD.sys kbd/mouse drivers over protocol channels [S77][S78]; SendInput inside targets THAT session's foreground; console untouched. RemoteApp shares session per disableconnectionsharing [S79]; multi-session needs Server SKU |
| Windows Sandbox | full VM; wsb connect = RDP in [S80]; no single-app passthrough [S81] |
| Hyper-V/VirtualBox VM | IKeyboard.putScancode injects at virtual hardware, guest-only [S100][S101][S102] |
| WSA/AppContainer | WSA EOL Mar 2025 [S82][S83]; AppContainer = same desktop, no separation |
| CreateDesktop (non-interactive) | SendInput fails: "input only goes to interactive desktop"; SetThreadDesktop+SwitchDesktop steals screen - dead end; PostMessage still works for gullible apps [S62-65] |

**RDP is the only mainstream mechanism giving a second independent focused-input universe on one machine** - Vanguard incident proves RDPWD.sys input trusted while session-local SendInput dropped [S84].

## 7. MOUSE-VIA-KEYBOARD COVERAGE MATRIX

| Method | Move | Click | R-click | Drag | Wheel | Background? |
|---|---|---|---|---|---|---|
| WM_LBUTTON*/RBUTTON*/MOUSEWHEEL posted | pseudo (lParam) | gullible | gullible | partial | posted | delivery yes; effect app-dependent |
| UIA Invoke/Toggle/Scroll | n/a | semantic | n/a | no | ScrollPattern | YES |
| UIA Value/TextEdit | n/a | n/a | n/a | n/a | n/a | YES (typing substitute) |
| MouseKeys | yes | yes | yes | yes | no | NO - shared cursor [S66-68] |
| Steam Input legacy | yes | yes | yes | partial | yes + click-at-pos | NO - global input, game focused [S69-71] |
| WriteConsoleInput (conhost) | MOUSE_EVENT | yes | yes | yes | yes | YES console buffer; needs AttachConsole+CONIN$ [S57][S58][S61] |
| CDP Input.dispatchMouseEvent | yes | yes | yes | yes | yes | YES tab/renderer-scoped, headless or headed [S92][S95] |
| RDP session | yes | yes | yes | yes | yes | YES session-scoped |
| Virtual HID mouse | shared cursor | yes | yes | yes | yes | NO - hijacks cursor |
| MA_NOACTIVATE/WS_EX_NOACTIVATE (self-side) | - | - | - | - | - | own window takes clicks unfocused - overlay tool, not driving others [S72-74] |

## 8. BROWSER - CDP AS THE SCOPED-INPUT PRECEDENT

`Input.dispatchMouseEvent/dispatchKeyEvent/dispatchTouchEvent/insertText` synthesize input INSIDE the target renderer through Blink's real pipeline (trusted-ish events, hit-testing, pointer events) - scoped by WebSocket/targetId, works headless AND headed, no OS focus [S92-95]. chromium input_handler.cc maps protocol to blink::WebInputEvent via widget_host_ [S95]; DevTools uses same dispatch for desktop UI automation [S96]. **Proof that scoped input requires in-process injection - the renderer owns scoping, not the OS.**

## 9. GAME / FOREIGN-PROCESS REALITY

- Message-level dies vs any game reading below WM_*: DirectInput GetDeviceState (wrapper over WM_INPUT thread since XP), raw input, GetAsyncKeyState [S85-89].
- RIDEV_INPUTSINK = receive-side background raw input; no symmetric inject-sink for senders [S88].
- Exclusive fullscreen = illusion post-Vista; focus-loss forces windowed anyway [S91].
- Detection: *_INJECTED flags [S20-22]; hDevice==NULL [S22]; missing WH_KEYBOARD correlation [S2].
- Anti-cheat: EAC checks Interception's mouse.sys/keyboard.sys and refuses launch; Vanguard silently drops SendInput mouse events; only whitelisted virtual-HID (Parsec PVUD) or bespoke drivers pass [S52][S53][S51][S84].
- Community consensus "SendInput to background game": impossible; workarounds = driver-injection (still global) or Arduino-as-keyboard [S25][S87][S112].

| App type | Keyboard (background) | Mouse (background) |
|---|---|---|
| Win32 native | PostMessage to child control | app-dependent |
| Qt | needs equal IL | partial |
| Electron/Chromium | no (CDP if debug port) | no (CDP) |
| UWP/WinUI | no (UIA partial) | no (UIA Invoke) |
| conhost console | WriteConsoleInput | MOUSE_EVENT records |
| Windows Terminal | no; UIA partial | no |
| Games | no; in-proc hooks or driver; anti-cheat risk high | same |

## 10. SYNTHESIS MATRIX

| Mechanism | Background-safe | Mouse | Detection risk | Privilege | Per-HWND scoped |
|---|---|---|---|---|---|
| PostMessage | delivery yes | partial | medium (missing hook/shift) | same IL | YES |
| SendInput/mouse_event | NO steals focus/cursor | yes | high (_INJECTED, NULL hDevice) | same/lower IL | NO |
| InputInjector (WinRT) | NO same stream | yes | high | brokered cap | NO |
| UI Automation | YES | semantic only | none (sanctioned) | uiAccess elevated | control-level |
| Journal hooks | NO blocks input | yes | high; dead on Win11 | admin-ish | NO |
| LL hooks | observe only | no | n/a | same IL | NO |
| WriteConsoleInput | YES | console only | none | AttachConsole | console |
| Virtual HID/Interception | NO shared stream | yes | low hw-level; AC blacklists | admin+driver | NO |
| HidHide | n/a (visibility) | n/a | n/a | driver | per-process hide |
| CDP Input.dispatch* | YES | yes | none (first-party) | debug port | per-target |
| RDP session | YES | yes | low (RDPWD.sys trusted) | session rights | per-session |
| VM putScancode | YES | yes | low | hypervisor API | per-VM |
| CreateDesktop | NO must switch | - | - | - | NO |
| MouseKeys/Steam Input | NO | yes | none | user | NO |

## RECOMMENDATION FOR THE BUNDLE

Default channel ladder (host-side, scoped where possible):
1. **Win32/conhost**: PostMessage WM_CHAR + mouse msgs; WriteConsoleInput for console apps.
2. **UIA-backed controls**: Invoke/Value/Scroll patterns - sanctioned, zero detection.
3. **Chromium**: CDP dispatch* when agent launches/attaches the browser.
4. **Fallback for hostile targets (games, UWP, Chromium w/o CDP)**: RDP session or VM - the only guaranteed full-mouse universes. VM path already exists (C00-C17 QMP).
5. **Never:** SendInput/InputInjector to "background" (steals user focus), journal hooks (blocks input + dead on Win11), CreateDesktop tricks (dead end).

## SOURCES (115)

Index S1-S115 as captured in the research log: MSDN/Microsoft Learn (S16-18, S20-21, S26-41, S57-68, S72-83, S97-99, S115), Old New Thing/Raymond Chen (S1,S2,S73,S74), Stack Overflow/MS Q&A (S3-S7,S14,S19,S22-S25,S61,S63,S85-91,S103,S106-S112), GitHub repos+issues (S8-S11,S43-S56,S80-84,S94-96,S102,S104,S113), vendor docs (AutoHotkey S12-15, Steam S69-71, VirtualBox S100-101, pywinauto S97-99), field blogs (S65,S89,S114,ph3at,keyman), Wikipedia S78, DeepWiki S45. Full annotated list preserved in the F3 research log; every claim in sections 1-10 carries its [Sn] reference.

**Gaps:** No single MS doc states baldly "SendInput cannot be scoped to a window" - conclusion is structural (no destination param; input goes to focus/hit-test) corroborated by S16/S24/S25/S63. Steam Input's exact injection layer UNDOCUMENTED. Whether WriteConsoleInput MOUSE_EVENT records bypass the documented console-mouse focus gating is UNVERIFIED.
