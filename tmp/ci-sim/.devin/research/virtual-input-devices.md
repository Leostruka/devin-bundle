# Independent Virtual Keyboard & Mouse – Deep Research Report

Date: 2026-09-22. Scope: replace the current `extensions/computer-use` physical/global input model (pynput `mouse.Controller`/`keyboard.Controller`) with **one additional virtual keyboard + one additional virtual mouse whose inputs are independent and identifiable**. 386 deduplicated sources in `virtual-input-devices-sources.md` (IDs referenced below, e.g. [E1]).

## 1. Current state (what is being replaced)

`computer-use` sends input through pynput, which on every platform uses **stream injection**, not a device:

- Windows → `SendInput` via ctypes [V1–V3]: events are inserted serially into the shared system input stream [B1], flagged `LL*HF_INJECTED` to any low-level hook observer [B5–B7], subject to UIPI (cannot reach equal/higher-integrity windows) [C2, C3], and carry no device identity [B18].
- macOS → `CGEventPost(kCGHIDEventTap)` [V4, V5]: requires Accessibility (PostEvent) TCC grant [N10–N15]; events carry posting-PID provenance [N5]; blocked by secure input contexts [N20].
- Linux/X11 → `Xlib.ext.xtest.fake_input` [V6]: XTEST is X11-only [L8]; under Wayland it only reaches XWayland clients [L10] and on modern desktops is itself routed through the RemoteDesktop portal (consent dialog) [L11, L12].

Pain points to fix: injected-flag detection, UIPI/TCC boundaries, no per-device identity, single merged input state (stuck modifiers shared with the physical user), no layout-independent scancode path.

## 2. Theory of operation – the four strata

The research converges on a strict layering model. "Independent input" means different things at each layer:

| Layer | Mechanism | Produces a real device? | Detectable as synthetic? | Privilege gate |
|---|---|---|---|---|
| **DOM/app** | JS `dispatchEvent`, `XSendEvent` | No | Yes – `isTrusted=false` [S17], `send_event` flag [L9] | None, but often rejected |
| **Stream injection** | SendInput, CGEventPost, XTEST, journal hooks | No | Yes – `LL*HF_INJECTED` [B6/B7], provenance PID fields [N5], dedicated XTEST slave devices [L5, L7] | UIPI / TCC / compositor policy |
| **Virtual device** | VHF (Win), uinput/uhid (Linux), HIDDriverKit/CoreHID (macOS), virtio-input (VM) | Yes – enumerable PDO/evdev node/IOHIDDevice with own VID/PID/name | No at consumer level – indistinguishable from hardware [E1, H1, O26]; identifiable at device level by design | Kernel trust: signed driver / device-node write access / Apple entitlement / portal consent |
| **Wire/hypervisor** | RDP input PDUs, RFB, SPICE, QMP, USB/IP, HID gadget | Yes, on the remote side | No – enters the target as hardware | Channel/session authentication |

The decisive fact: **only layer 3 (and wire→device layer 4) creates an independently identifiable device**. Every layer-2 API inserts into the shared stream and is marked or attributable to a process.

## 3. What "independent" can and cannot mean

Two different goals were separable only through the sources:

1. **Independent identity/state** – a second keyboard+mouse that are enumerable, nameable (VID/PID/device node/`HIDVirtualDevice` property/EIS device name), carry their own modifier/button state, and whose events can be attributed (Raw Input `hDevice` [D2–D4], evdev node + `EVIOCGID` [H10–H12], IOHID `senderID` [O16–O18], EIS device names [K10], XTEST slave IDs [L5]). **Achievable on all three desktop OSes.**

2. **Independent effect** – a second *cursor* and a second *keyboard focus* operating simultaneously with the user's. **Not achievable as a general OS capability:**
   - Windows: single system cursor hot spot for all mice [D7]; `WM_MOUSEMOVE` carries no source [D8]. Multiple cursors exist only inside apps that draw their own (MultiPoint SDK model [D9]) or via Raw-Input-driven custom UI.
   - macOS: same – all mouse APIs assume one cursor [P9, P10].
   - X11: genuinely possible via MPX master-device pairs (cursor + focus per pair) [L13–L16] – but X11-only, and XI1.x clients see only the first pair [L14].
   - Wayland: possible only via multi-seat, which is compositor- and toolkit-dependent (Sway/wlroots yes; KWin/Mutter effectively no for arbitrary clients) [J5, J17–J20]. SDL only recently learned multi-seat [J18].

**Consequence for computer-use:** a virtual kbd+mouse gives the agent its own *device*, but its events still drive the *same* desktop cursor and focus as the user's physical devices. If the actual requirement is "agent input must not collide with the human's session," the correct targets are browser-level input (CDP/BiDi – per-context sources, unaffected by desktop state [S1–S10]) or a VM/remote target (QMP, RDP, RFB – separate machine session entirely [Q, R]).

## 4. Platform findings

### Windows

- **VHF (Virtual HID Framework)** is the sanctioned route: a KMDF/WDM "HID source driver" links `vhfkm.lib`; in-box `Vhf.sys` enumerates child PDOs; `VHF_CONFIG` sets VendorID/ProductID/HardwareIDs/report descriptor; `VhfReadReportSubmit` feeds input reports that flow through hidclass→kbdhid/mouhid→kbdclass/mouclass exactly like hardware [E1–E6, E10, E16]. Microsoft ships a virtual keyboard module in DMF [E7] and an IoT HID-injector sample for touch/kb/mouse [E25]; community composite kb+mouse implementations exist [E8, E9, E26, F6–F7].
- **Identity/attribution:** Raw Input registration (TLC 0x01/0x02 mouse, 0x01/0x06 keyboard) + `RAWINPUTHEADER.hDevice` + `GetRawInputDeviceInfo` give per-device filtering and VID/PID readback [D1–D6]. A dedicated udev-style "only this device" grab does not exist on Windows; `RIDEV_NOLEGACY`/`RIDEV_INPUTSINK` are the levers [D5].
- **Independence limit:** one system cursor [D7]; virtual-mouse events merge into it.
- **Privilege limits:** every kernel path needs an elevated install (PnPUtil [G7]) and, since Win10 1607, a Microsoft-signed driver (attestation or HLK; EV cert for the Dev Center account) [G1–G4]. TESTSIGNING requires Secure Boot off – dev-only [G5, G6]. WDAC recommended block rules may flag known-abused drivers [G8]. VHF input is not IL-bounded the way SendInput is – a virtual HID can type into elevated windows where SendInput cannot [B1, C2].
- **Alternatives evaluated:** Interception (upper filters on kbdclass/mouclass – injects *as* the existing device, so no new identity [F1, F2, E17–E21]); ViGEmBus (bus-driver PDO pattern, proven, but gamepads only + archived [F3–F5]); UDECX/usbip-win (full virtual USB enumeration – heavier but real [F8–F10]); InputInjector (brokered, restricted capability, not an enumerable device [C9–C11]); synthetic pointer API (pen/touch only [C12]); TinyUSB/RP2040 hardware dongle – a real second USB kbd+mouse with zero signing/admin burden [F13–F16].

### Linux / Wayland

- **uinput is the canonical path**: `/dev/uinput` + `UI_DEV_SETUP`/`UI_DEV_CREATE` creates a device with caller-chosen name/bustype/vendor/product/phys [H1, H4, H5, H11]; events are delivered to userspace and in-kernel consumers identically to hardware [H1]. Two fds = two independent devices (one fd per device – libevdev enforces this [I11]), exactly the requested "one extra keyboard + one extra mouse," as already done in production by Sunshine (separate "Keyboard/Mouse passthrough" devices, vendor 0xBEEF [M8]).
- **Permissions:** write access to `/dev/uinput` – root, `input` group via udev `MODE="0660" GROUP="input" OPTIONS+="static_node=uinput"` [I2–I4], or seat-scoped `TAG+="uaccess"` (with the static_node caveat [I3] and the keylogger-risk warning [I1]). A persistent daemon holding the fd is required both for lifetime (fd close destroys the device [I11]) and for the udev-recognition delay [M1]. To be classified as a real keyboard the device must advertise the full alphanumeric key block [I6].
- **Wayland coverage:** uinput works on every session type (X11/Wayland/TTY) [M1, M3]. The Wayland-native protocols (`zwp_virtual_keyboard_v1`, `zwlr_virtual_pointer_v1`) exist but are **compositor-gated and absent on KWin and Mutter** [J1, J2, J10] – usable only on wlroots-family compositors, where the devices are separately identifiable internals (`isVirtual`, per-seat objects) [J4, J12, J13].
- **The sanctioned cross-desktop Wayland path is RemoteDesktop portal → libei/EIS**: CreateSession→SelectDevices(KEYBOARD|POINTER)→Start (user consent, persistable via restore_token), then `ConnectToEIS()` hands an fd for a libei sender context; events are indistinguishable to clients but provenance-tagged inside the compositor (app-id labeling, revocable) [K1–K3, K7–K18, K21]. Both GNOME and KDE backends serve ConnectToEIS [K13, K14]. D-Bus `Notify*` absolute-motion calls require an accompanying screencast stream – EIS does not [K4].
- **Seats:** devices can be assigned to non-default logical/physical seats via udev (`WL_SEAT`/`ID_SEAT`) [I8, I9, J17] – real independent seat only where the compositor implements multi-seat (sway/wlroots [J19, J20]); otherwise events merge into seat0's single focus [J5].
- **Contrast baseline:** XTEST under X11 creates dedicated "Virtual core XTEST" slave devices – identifiable, but X11-only [L1–L7]. XWayland on Wayland compositors is being rewired to the same portal/EIS path [L11, L12]. Android shows the same theory with different gates (INJECT_EVENTS signature permission vs `/dev/uhid` on the device [U1–U4]).

### macOS

- **Three strata verified:** (1) Quartz `CGEventSource` – a `kCGEventSourceStatePrivate` source gets a unique source-state ID, and events carry posting PID/UID/state-ID/user-tag readable by event taps [N1–N6]: independently *marked* but not a device, and still TCC-gated (PostEvent = Accessibility) [N10–N14]. (2) **Real virtual HID devices** – `IOHIDUserDeviceCreate` (legacy userspace; kernel stamps `HIDVirtualDevice=true` and enforces entitlement [O1–O4]), **DriverKit `IOUserHIDDevice` dext** (Karabiner's shipped model: virtual kb+mouse "recognized same as physical hardware," root-gated control channel [O27–O31]), and **CoreHID `HIDVirtualDevice`** (macOS 15+, userspace, no dext: `Properties(descriptor:vendorID:)` + `dispatchInputReport`; "system treats the device as any other external peripheral" [O35–O37]). (3) `IOHIDPostEvent` – deprecated IOHIDSystem injection requiring console-owner EUID even as root [O10–O12].
- **Every virtual-HID path is entitlement-gated:** `com.apple.developer.hid.virtual.device` (CoreHID, Apple request form – self-signing gets AMFI-killed [O40]) or the DriverKit entitlement set (`driverkit` + `family.hid.device`/`eventservice` + `transport.hid` + `userclient-access` for app↔dext IPC) [O22–O26, O34]. Keyboard/mouse-class virtual devices additionally trigger the Accessibility TCC prompt [O38], and Mac App Store distribution was rejected for non-accessibility use [O39].
- **Independence:** virtual devices get real registry identity (VendorID/ProductID/`HIDVirtualDevice`/transport) [O5–O7, O44–O46]; every queued IOHIDEvent carries `senderID` = publishing service's registry ID [O13, O16–O18]. Still **one global cursor** [P9, P10]; `EnableSecureEventInput` blocks observation during secure input [N20].

### Remote / virtualization (already "virtual devices")

- Wire protocols carry input as device-level events: RDP fast/slow-path input PDUs (scancode, unicode, mouse, mousex, mouserel; capability-negotiated) [Q1–Q9]; RFB `KeyEvent`/`PointerEvent` (keysym + absolute pointer; QEMU extended key event adds raw keycode) [Q15–Q17]; SPICE inputs channel (AT scancodes; relative server mode vs absolute client mode requiring a usb-tablet) [Q24–Q28]; Guacamole `key`/`mouse` instructions [Q31–Q33]; Moonlight NV_* packets over ENet [T1–T3].
- Hypervisor plane: virtio-input mirrors evdev into the guest [R1, R2]; QMP `input-send-event`/`send-key` injects without any display protocol [R3]; libvirt `virDomainSendKey` and `<input type='tablet|passthrough'>` [R7, R8]; VirtualBox `IKeyboard.putScancode`/`IMouse.putMouseEventAbsolute` [R9, R10]; Hyper-V `Msvm_Keyboard.TypeScancodes` [R11, R12]. USB transport: USB/IP exports real URBs [R13, R14]; Linux HID gadget (`/dev/hidgX`) and PiKVM OTG present a genuine USB kbd+mouse to any host [R15, R16].
- **Absolute vs relative:** coordinate-driven automation needs absolute-capable channels (tablet/PointerEvent/putMouseEventAbsolute/`mouse_position`); relative-only modes desync [Q28, R6].

### Browser targets

- CDP `Input.dispatchKeyEvent/dispatchMouseEvent` enter Chromium's real input path (WebMouseEvent→RenderWidgetHostView) → `isTrusted=true` DOM events, user gestures, default actions [S1–S3]. WebDriver classic `/actions` and BiDi `input.performActions` standardize **named input sources** (`key`/`pointer`/`wheel` with per-source ids and persistent pressed-state) – i.e., independent logical keyboard+mouse inside a browsing context, with zero OS footprint [S4–S10]. Playwright/Puppeteer map onto these [S11–S14]; Firefox routes Marionette/BiDi through widget-level synthesis, not DOM events [S15, S16]. JS `dispatchEvent` remains untrusted [S13, S17].

## 5. Comparison for the stated goal

| Path | Extra identifiable kbd+mouse? | Independent cursor/focus? | Privilege | Fits computer-use? |
|---|---|---|---|---|
| SendInput / CGEventPost / XTEST (current) | No | No (shared) | Low (TCC/UIPI-limited) | Status quo |
| Windows VHF driver | Yes – own PDO, VID/PID, Raw-Input-visible | No – shared cursor/focus | Admin install + MS-signed driver | Yes for desktop control + attribution; heavy rollout |
| Linux uinput ×2 | Yes – distinct event nodes, name/ids | No (unless compositor multi-seat) | uinput write access or portal consent | Yes – best Linux fit; daemon required |
| Wayland virt-kb/ptr protocols | Yes (compositor-visible) | Per-seat only | Compositor-dependent; absent on KWin/Mutter | Partial – wlroots only |
| Portal/libei (Wayland) | Yes – named EIS devices, consent-scoped | No | User consent dialog | Yes on GNOME/KDE without root |
| macOS CoreHID / DriverKit dext | Yes – registry device + senderID | No – one cursor | Apple entitlement + TCC Accessibility | Yes but entitlement latency/distribution limits |
| Browser CDP/BiDi | Yes – named logical sources | N/A (per-context) | DevTools/WebDriver session | Best for web targets |
| QMP/virtio-input, RDP/RFB/SPICE | Yes – on the remote/guest | Yes – separate machine | Channel auth | Best isolation overall |
| USB gadget / TinyUSB dongle | Yes – real hardware | No | None on host (needs the gadget host) | Viable zero-driver fallback |

## 6. Recommendation

**Adopt a layered input backend; do not bet on a single mechanism.**

1. **Keep virtual-device injection as the desktop path.** Per OS:
   - **Linux (primary dev target):** two persistent uinput devices – one keyboard (full alphanumeric block [I6]), one pointer (REL_X/Y + BTN_* or ABS_* for absolute mode) – held by a small daemon or owned process (fd lifetime = device lifetime [I11]); ship the documented udev rule [I2–I4]; expose `/dev/input/by-id` naming for verification [I7]. On GNOME/KDE Wayland without privileges, use RemoteDesktop portal→libei with `restore_token` persistence [K1, K11, K12]. On wlroots, optionally prefer virtual-keyboard/wlr-virtual-pointer [J1, J2].
   - **Windows:** VHF HID-source driver exposing keyboard + mouse TLCs (composite descriptor with distinct report IDs, à la vmulti [F7]) with a private IOCTL feed; read attribution via Raw Input `hDevice` [D2–D4]. Budget EV cert + attestation signing + elevated installer [G1–G4, G7]. This removes the injected flag and the UIPI ceiling – real device input reaches elevated windows.
   - **macOS:** CoreHID `HIDVirtualDevice` on macOS 15+ (request `com.apple.developer.hid.virtual.device` early) [O35–O37, O40]; Karabiner-model DriverKit dext if older-macOS support or a root daemon is acceptable [O27–O31]. Interim: private `CGEventSource` for marked events [N1–N4].
2. **Use browser-level input for browser targets** (CDP `Input.*` or BiDi `input.performActions` with separate `keyboard`/`pointer` source ids) – true logical independence inside the page, no OS risk [S1–S10]. Already aligned with `cu_browser`/`browser.py` direction.
3. **Use hypervisor/wire paths for isolation-sensitive targets** – QMP `input-send-event`, virtio-input, RDP/RFB where the agent acts on a VM or remote session [Q, R].
4. **Keep the physical fallback** for pre-boot/secure-desktop-less edge cases, and keep `OwnedInputs` semantics: on device teardown send all-keys-up/all-buttons-up before `UI_DEV_DESTROY`/`VhfDelete`/`HIDVirtualDevice` deactivation to prevent stuck modifiers [B16, M5].
5. **Explicitly out of scope / impossible claim:** a second independent *system cursor* and *keyboard focus* on Windows/macOS/mainline Wayland does not exist as an OS feature; MPX (X11) and multi-seat (select Wayland compositors) are the only documented exceptions [D7, P9, L13–L16, J5, J17–J20]. Marketing the virtual devices as "non-interfering" would be a false claim.

## 7. Limitations and caveats (verified)

- **Windows kernel rollout cost:** MS signing (EV cert, Dev Center), elevated install, possible WDAC blocklisting of input drivers [G1–G8]. TESTSIGNING is dev-only [G5].
- **Linux permission surface:** `/dev/uinput` is root/input-group/uaccess-gated by design (keylogger risk) [I1]; udev rule + daemon required; device recognized asynchronously after creation [M1].
- **Wayland fragmentation:** virtual-keyboard/pointer protocols unsupported on KWin/Mutter [J1, J2, J10]; portal/libei is the only desktop-agnostic route and is consent-based [K1, K15–K17].
- **macOS distribution:** entitlement requires Apple approval; Accessibility TCC prompt; MAS rejection risk for non-accessibility use [O38–O40].
- **Attribution vs invisibility:** virtual devices are *identifiable* (that's the point) – Hyprland can policy-match them by name [J12], Karabiner flags `is_karabiner_virtual_hid_device` [O44], Windows Raw Input exposes VID/PID [D4]. They are not stealth, and HID-spoofing abuse potential (BadUSB-class) is documented [W12, W13].
- **Verified gaps:** no MS doc states explicitly that VHF input lacks `LLKHF_INJECTED` (inferred from the injected-vs-driver-source definitions [B5] and VHF's HID-stack path [E1, E4]); anti-cheat/EDR treatment of virtual-HID drivers is undocumented; Portal `persist_mode` acceptance varies by backend; GNOME EIS device-naming detail unverified.

## 8. Multiseat gaming – the "dedicated input per program" case

The user's real target (multiple people playing on one machine, each with their own devices) is a solved problem in production – but **not via virtual devices and not via Sandboxie alone**. The deployed stack (Nucleus Co-op + ProtoInput / Universal Split Screen) separates concerns [X1–X10]:

| Concern | How it's done today | Source |
|---|---|---|
| Multi-instance (game refuses to run twice) | Symlinked game folder + KillMutex (named-mutex isolation) or a sandbox (Sandboxie/private namespace) | X1, X5, X10 |
| Input dedication per instance | **In-process hooks**, not OS routing: hook `RegisterRawInputDevices` (game thinks it registered), filter every `WM_INPUT` by `RAWINPUTHEADER.hDevice` against the assigned device handle – ALLOW/BLOCK per message; legacy message filters; DirectInput enumeration hooks | X7, X8 |
| Gamepad dedication | Custom xinput DLL per instance mapping physical pad N → XInput slot 0; SDL2 restriction DLL; DInput→XInput hook bypasses the 4-controller cap | X1, X3, X4, X9 |
| Cursor/focus illusion | Hooks on GetCursorPos/SetCursorPos/foreground; "faking window focus within the input" – required because **all mice still share one system cursor** | X9, D7 |
| Multiplayer link | LAN/online emulation between instances (Goldberg, Nemirtingas) | X1 |

Two facts worth noting for our design:

1. **The illusion lives inside the target process.** Dedication is achieved by lying to each instance about which devices exist and which window has focus – Raw Input's `hDevice` provides the attribution, in-process hooks provide the enforcement. Zero drivers, zero virtual devices needed on Windows.
2. **Virtual devices improve, don't replace, this stack.** A per-instance VHF/uinput device gives clean attribution (the instance's input is born separate, not filtered), but the shared-cursor and fake-focus problems remain – the ProtoInput-style message/focus hooks are still required regardless.

For an agent equivalent (agent inputs must not collide with the human's session), the analogous minimal path is: dedicated virtual device for attribution + window/message filtering for containment – or simply run the target inside a browser context/VM where independence is native.

## 9. Source register

396 deduplicated sources, categorized by type (spec / osdoc / kernel / source / project / forum / secondary / paper) and platform, with the concrete fact each supports: **`virtual-input-devices-sources.md`** (sections A–X). Primary-spec and official-doc sources dominate; secondary/forum sources are used only where no primary documentation exists (marked as such in the fact column).
