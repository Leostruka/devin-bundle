# Source Index – Independent Virtual Keyboard & Mouse

Deduplicated registry for `virtual-input-devices.md`. Each entry: title – URL – type – the concrete fact it supports. Categories: `spec` (primary standard/protocol), `osdoc` (official platform documentation), `kernel` (kernel doc/source), `source` (project source code), `project` (project docs/readme), `forum` (vendor forum/Q&A), `secondary` (articles, SO, blogs), `paper` (academic/standards-track research).

## A. HID theory and device identity

| # | Source | Type | Fact supported |
|---|--------|------|----------------|
| A1 | Device Class Definition for HID 1.11 (USB-IF) – https://www.usb.org/sites/default/files/hid1_11.pdf | spec | HID devices self-describe via report descriptors; descriptor defines report structure, usages, collections. A virtual device must emit a valid descriptor to exist as a "real" keyboard/mouse. |
| A2 | HID Usage Tables 1.5 (USB-IF) – https://www.usb.org/sites/default/files/hut1_5.pdf | spec | Usage pages + usage IDs assign semantics to report fields (Generic Desktop X/Y; Keyboard/Keypad page 0x07). |
| A3 | USB-IF HID page / HUT 1.7 – https://www.usb.org/hid | spec | HUT is the single source of truth for usages ("purpose and meaning of a data field in a HID report"). |
| A4 | USB-IF member agreement (VID clause) – https://usb.org/sites/default/files/usb-if_member_agreement_080618_1.pdf | spec | "Each Vendor ID Number is assigned to one company for its sole and exclusive use"; unauthorized VID use is prohibited – VID is a claimed identity. |
| A5 | HID Collections Overview (MS) – https://learn.microsoft.com/en-us/windows-hardware/drivers/hid/hid-collections | osdoc | Report descriptors define top-level collections (TLCs); Windows opens TLCs for system use. |
| A6 | Touchscreen sample report descriptors (MS) – https://learn.microsoft.com/en-us/windows-hardware/design/component-guidelines/touchscreen-sample-report-descriptors | osdoc | Concrete descriptor: `0x85 REPORT_ID`, nested Application/Logical collections, INPUT(Data,Var,Abs) – report-ID multiplexing pattern. |
| A7 | Develop Windows Device Drivers for HID (MS) – https://learn.microsoft.com/en-us/windows-hardware/drivers/hid/ | osdoc | "HID consists of two fundamental concepts, a report descriptor, and reports"; Input/Output/Feature report types. |
| A8 | HID Usages (MS) – https://learn.microsoft.com/en-us/windows-hardware/drivers/hid/hid-usages | osdoc | Usage page is a 16-bit value; Generic Desktop = 0x01 (Mouse 0x02, Keyboard 0x06). |
| A9 | HID API (HidD_*/HidP_*) (MS) – https://learn.microsoft.com/en-us/windows-hardware/drivers/hid/hid-api | osdoc | HidD_GetAttributes/HidP_GetCaps enumerate per-TLC identity (VID/PID/usage). |
| A10 | Interpreting HID Reports (MS) – https://learn.microsoft.com/en-us/windows-hardware/drivers/hid/interpreting-hid-reports | osdoc | HidP_GetUsages/GetValue extract per-usage data from a report. |
| A11 | HID Transports Overview (MS) – https://learn.microsoft.com/en-us/windows-hardware/drivers/hid/hid-transports | osdoc | In-box minidrivers per transport (USB/BT/BLE/I2C/GPIO/SPI); Hidclass/Hidparse report limits (8KB-1bit reports). |
| A12 | Transport Minidrivers (MS) – https://learn.microsoft.com/en-us/windows-hardware/drivers/hid/transport-minidrivers | osdoc | Custom transports need a minidriver; KMDF required for keyboard/mouse filter drivers. |

## B. Windows – why SendInput/injection is not a second device

| # | Source | Type | Fact supported |
|---|--------|------|----------------|
| B1 | SendInput (winuser.h) – https://learn.microsoft.com/en-us/windows/win32/api/winuser/nf-winuser-sendinput | osdoc | "Inserts events serially into the keyboard or mouse input stream"; subject to UIPI; returns 0 if blocked (BlockInput). No device identity. |
| B2 | INPUT structure – https://learn.microsoft.com/en-us/windows/win32/api/winuser/ns-winuser-input | osdoc | INPUT is a MOUSEINPUT/KEYBDINPUT/HARDWAREINPUT union – one synthesized event, no device handle. |
| B3 | KEYBDINPUT – https://learn.microsoft.com/en-us/windows/win32/api/winuser/ns-winuser-keybdinput | osdoc | `dwExtraInfo` is the only app-defined tag on a synthesized keystroke. |
| B4 | MOUSEINPUT – https://learn.microsoft.com/en-us/windows/win32/api/winuser/ns-winuser-mouseinput | osdoc | Same `dwExtraInfo` limitation for mouse. |
| B5 | LowLevelKeyboardProc – https://learn.microsoft.com/en-us/windows/win32/winmsg/lowlevelkeyboardproc | osdoc | "If the input comes from a call to keybd_event, the input was 'injected'" – OS labels injection at hook level. |
| B6 | KBDLLHOOKSTRUCT – https://learn.microsoft.com/en-us/windows/win32/api/winuser/ns-winuser-kbdllhookstruct | osdoc | `LLKHF_INJECTED` (bit 4) marks injected keys; `LLKHF_LOWER_IL_INJECTED` marks lower-IL injectors. |
| B7 | MSLLHOOKSTRUCT – https://learn.microsoft.com/en-us/windows/win32/api/winuser/ns-winuser-msllhookstruct | osdoc | `LLMHF_INJECTED`/`LLMHF_LOWER_IL_INJECTED` for mouse; struct carries `time` + `dwExtraInfo`. |
| B8 | GetMessageExtraInfo – https://learn.microsoft.com/en-us/windows/win32/api/winuser/nf-winuser-getmessageextrainfo | osdoc | Per-queue extra-info value is "application- or driver-defined" – a tag, not device identity. |
| B9 | System Events and Mouse Messages (MI_WP_SIGNATURE) – https://learn.microsoft.com/en-us/windows/win32/tablet/system-events-and-mouse-messages | osdoc | Windows itself stamps pen/touch origin via `0xFF515700` signature in extra info – the tag space is OS-shared. |
| B10 | mouse_event / keybd_event – https://learn.microsoft.com/en-us/windows/win32/api/winuser/nf-winuser-mouse_event | osdoc | Legacy injection APIs superseded by SendInput; their output is "injected" by definition. |
| B11 | BlockInput – https://learn.microsoft.com/en-us/windows/win32/api/winuser/nf-winuser-blockinput | osdoc | Blocks all kbd/mouse input; system unblocks on Ctrl+Alt+Del; only blocking thread may SendInput. |
| B12 | INPUT_MESSAGE_ORIGIN_ID – https://learn.microsoft.com/en-us/windows/win32/api/winuser/ne-winuser-input_message_origin_id | osdoc | `IMO_HARDWARE` vs `IMO_INJECTED`; UIAccess-manifested app's injected input reports as `IMO_HARDWARE` – sanctioned "looks-like-hardware" path. |
| B13 | GetCurrentInputMessageSource – https://learn.microsoft.com/en-us/windows/win32/api/winuser/nf-winuser-getcurrentinputmessagesource | osdoc | Receiver-side query returns deviceType + originId per message. |
| B14 | InSendMessageEx – https://learn.microsoft.com/en-us/windows/win32/api/winuser/nf-winuser-insendmessageex | osdoc | Distinguishes sent vs posted messages; posted WM_* injection invisible to input flags. |
| B15 | AttachThreadInput – https://learn.microsoft.com/en-us/windows/win32/api/winuser/nf-winuser-attachthreadinput | osdoc | Merges two threads' input queues; fails if journal-record hook installed; cannot cross desktops. |
| B16 | JournalPlaybackProc – https://learn.microsoft.com/en-us/windows/win32/winmsg/journalplaybackproc | osdoc | While WH_JOURNALPLAYBACK is installed, regular mouse/keyboard input is disabled; hook supplies timed EVENTMSGs. |
| B17 | JournalRecordProc – https://learn.microsoft.com/en-us/windows/win32/winmsg/journalrecordproc | osdoc | Ctrl+Alt+Del cannot be recorded – stops journaling, removes hooks; journaling unsupported on Win11. |
| B18 | MS Q&A: identify injecting process – https://learn.microsoft.com/en-us/answers/questions/2122732/how-do-i-know-which-process-trigger-the-injected-k | forum | Windows provides no API linking a synthesized event to the injecting process – injection is anonymous. |

## C. Windows – integrity, secure desktop, gated capabilities

| # | Source | Type | Fact supported |
|---|--------|------|----------------|
| C1 | Mandatory Integrity Control – https://learn.microsoft.com/en-us/windows/win32/secauthz/mandatory-integrity-control | osdoc | Integrity SIDs in SACLs; low IL cannot write to medium+ objects regardless of DACL – underpins UIPI. |
| C2 | What is UIPI (MS blog) – https://learn.microsoft.com/en-us/archive/blogs/vishalsi/what-is-user-interface-privilege-isolation-uipi-on-vista | osdoc | Lower-privilege process cannot SendMessage/PostMessage to higher-IL windows (silently dropped), attach hooks, or use journal hooks on higher IL. |
| C3 | Security Considerations for Assistive Technologies – https://learn.microsoft.com/en-us/windows/win32/winauto/uiauto-securityoverview | osdoc | uiAccess requires Authenticode signature + secure location + admin launch; secure desktop/logon UI unreachable even then. |
| C4 | UAC: only elevate UIAccess in secure locations – https://learn.microsoft.com/en-us/previous-versions/windows/it-pro/windows-10/security/threat-protection/security-policy-settings/user-account-control-only-elevate-uiaccess-applications-that-are-installed-in-secure-locations | osdoc | Windows enforces PKI signature check on any interactive app requesting UIAccess. |
| C5 | App capability declarations (uiAccess) – https://learn.microsoft.com/en-us/windows/apps/package-and-deploy/app-capability-declarations | osdoc | `uiAccess` is a restricted capability for packaged apps. |
| C6 | UAC: switch to secure desktop – https://learn.microsoft.com/en-us/previous-versions/windows/it-pro/windows-10/security/threat-protection/security-policy-settings/user-account-control-switch-to-the-secure-desktop-when-prompting-for-elevation | osdoc | Secure desktop: only trusted SYSTEM processes run there; protects against input/output spoofing. |
| C7 | How UAC works – https://learn.microsoft.com/en-us/windows/security/application-security/application-control/user-account-control/how-it-works | osdoc | Only Windows processes can access the secure desktop. |
| C8 | Initializing Winlogon – https://learn.microsoft.com/en-us/windows/win32/secauthn/initializing-winlogon | osdoc | Winlogon registers SAS (Ctrl+Alt+Del) first so no other app can hook it; creates separate Winlogon/application desktops. |
| C9 | InputInjector.InjectKeyboardInput (inputInjectionBrokered) – https://learn.microsoft.com/en-us/uwp/api/windows.ui.input.preview.injection.inputinjector.injectkeyboardinput | osdoc | `InputInjector` is "the virtual input device" but requires the restricted `inputInjectionBrokered` capability. |
| C10 | Simulate user input through input injection (UWP) – https://learn.microsoft.com/en-us/windows/uwp/ui-input/input-injection | osdoc | Brokered injection requires MSIX packaging + restricted capability; still not an enumerable device. |
| C11 | winrt-api: Windows.UI.Input.Preview.Injection – https://github.com/MicrosoftDocs/winrt-api/blob/docs/windows.ui.input.preview.injection/windows_ui_input_preview_injection.md | osdoc | Namespace reference reiterates the restricted-capability requirement. |
| C12 | InjectSyntheticPointerInput / CreateSyntheticPointerDevice – https://learn.microsoft.com/en-us/windows/win32/api/winuser/nf-winuser-injectsyntheticpointerinput | osdoc | User-mode synthetic device handle exists but only for PT_TOUCH/PT_PEN – keyboard/mouse excluded. |
| C13 | humaninterfacedevice DeviceCapability – https://learn.microsoft.com/en-us/uwp/schemas/appxpackage/how-to-specify-device-capabilities-for-hid | osdoc | UWP HID access requires manifest capability scoped to VID/PID + usage page. |
| C14 | HidDevice.FromIdAsync – https://learn.microsoft.com/en-us/uwp/api/windows.devices.humaninterfacedevice.hiddevice.fromidasync | osdoc | First open from UI thread shows consent prompt; ReadWrite needed for output reports. |

## D. Windows – Raw Input device identity and the single cursor

| # | Source | Type | Fact supported |
|---|--------|------|----------------|
| D1 | Raw Input Overview – https://learn.microsoft.com/en-us/windows/win32/inputdev/about-raw-input | osdoc | Apps register per TLC; can "distinguish the source of the input even if it is from the same type of device. For example, two mouse devices." |
| D2 | RAWINPUTHEADER – https://learn.microsoft.com/en-us/windows/win32/api/winuser/ns-winuser-rawinputheader | osdoc | `hDevice` = "handle to the device generating the raw input data" – per-device attribution key. |
| D3 | GetRawInputDeviceInfo – https://learn.microsoft.com/en-us/windows/win32/api/winuser/nf-winuser-getrawinputdeviceinfow | osdoc | RIDI_DEVICENAME/RIDI_DEVICEINFO/RIDI_PREPARSEDDATA queries expose identity per handle. |
| D4 | RID_DEVICE_INFO – https://learn.microsoft.com/en-us/windows/win32/api/winuser/ns-winuser-rid_device_info | osdoc | `dwType` discriminates RIM_TYPEMOUSE/KEYBOARD/HID; HID variant carries dwVendorId/dwProductId/usUsagePage/usUsage. |
| D5 | RAWINPUTDEVICE / RegisterRawInputDevices – https://learn.microsoft.com/en-us/windows/win32/api/winuser/ns-winuser-rawinputdevice | osdoc | Registration by UsagePage/Usage; `RIDEV_INPUTSINK` enables background receipt; `RIDEV_NOLEGACY` suppresses legacy messages. |
| D6 | Using Raw Input (official sample) – https://learn.microsoft.com/en-us/windows/win32/inputdev/using-raw-input | osdoc | Registers keyboard 0x01/0x06 + mouse 0x01/0x02; each WM_INPUT read via GetRawInputData carries the source device handle. |
| D7 | Mouse Input Overview – https://learn.microsoft.com/en-us/windows/win32/inputdev/about-mouse-input | osdoc | The system maintains a single mouse cursor hot spot that all mouse input drives – a second mouse cannot have its own pointer. |
| D8 | SO: distinguishing secondary mouse via Raw Input – https://stackoverflow.com/questions/22605538/raw-input-handling-distinguishing-secondary-mouse | secondary | Practitioners filter WM_INPUT by RAWINPUTHEADER.hDevice; GetRawInputDeviceList enumerates handles. |
| D9 | Windows MultiPoint Mouse SDK – https://learn.microsoft.com/en-us/previous-versions/msdn10/ee906605(v=msdn.10) | osdoc | Framework supporting up to 25 mice concurrently with per-device events/permissions – app-level multiple cursors, not OS cursors. |

## E. Windows – VHF and HID driver stack (the real second-device path)

| # | Source | Type | Fact supported |
|---|--------|------|----------------|
| E1 | Write a HID Source Driver Using VHF – https://learn.microsoft.com/en-us/windows-hardware/drivers/hid/virtual-hid-framework--vhf- | osdoc | Since Win10, VHF eliminates writing a transport minidriver; KMDF/WDM source driver links vhfkm.lib; in-box Vhf.sys enumerates child PDOs. Kernel-mode only. |
| E2 | VhfCreate – https://learn.microsoft.com/en-us/windows-hardware/drivers/ddi/vhf/nf-vhf-vhfcreate | osdoc | `VhfCreate(VHF_CONFIG, &handle)` after WdfDeviceCreate creates one enumerable virtual HID device. |
| E3 | VHF_CONFIG – https://learn.microsoft.com/en-us/windows-hardware/drivers/ddi/vhf/ns-vhf-%5Fvhf%5Fconfig | osdoc | Config exposes VendorID, ProductID, VersionNumber, ContainerID, HardwareIDs, report descriptor pointer – direct control of device identity. |
| E4 | VhfReadReportSubmit – https://learn.microsoft.com/en-us/windows-hardware/drivers/ddi/vhf/nf-vhf-vhfreadreportsubmit | osdoc | Submits HID Input Reports upstream; reports flow through hidclass/kbdhid/mouhid like physical hardware. |
| E5 | VhfStart – https://learn.microsoft.com/en-us/windows-hardware/drivers/ddi/vhf/nf-vhf-vhfstart | osdoc | Starts the virtual device; callbacks begin only after VhfStart. |
| E6 | vhf.h DDI index – https://learn.microsoft.com/en-us/windows-hardware/drivers/ddi/vhf/ | osdoc | Full VHF surface: VHF_CONFIG_INIT, VhfDelete, async op callbacks, HID_XFER_PACKET. |
| E7 | Dmf_VirtualHidKeyboard.c (Microsoft DMF) – https://github.com/microsoft/DMF/blob/master/Dmf/Modules.Library/Dmf_VirtualHidKeyboard.c | source | Microsoft's DMF ships a module building a virtual HID keyboard on VHF with full keyboard+consumer-control descriptor. |
| E8 | hulirou/Virtual-keyboard-and-mouse – https://github.com/hulirou/Virtual-keyboard-and-mouse/ | source | KMDF+VHF driver creating composite virtual keyboard+mouse; user-mode IOCTL queue feeds reports. |
| E9 | VHF gamepad example – https://github.com/SenuthLikesCrak/Virtual-HID-Framework-gamepad-example | source | Minimal VHF sample: descriptor, INF, driver end-to-end. |
| E10 | HID Architecture – https://learn.microsoft.com/en-us/windows-hardware/drivers/hid/hid-architecture | osdoc | hidclass.sys is the WDM function+bus driver for HIDClass; glue between clients and transports. |
| E11 | HID Client Drivers – https://learn.microsoft.com/en-us/windows-hardware/drivers/hid/hid-client-drivers | osdoc | Transport stack creates a PDO per HID device; hidclass creates a PDO per TLC – one composite device exposes separate keyboard and mouse TLCs. |
| E12 | Creating UMDF HID Minidrivers – https://learn.microsoft.com/en-us/windows-hardware/drivers/wdf/creating-umdf-hid-minidrivers | osdoc | MsHidKmdf.sys/MsHidUmdf.sys pass-through under hidclass; minidriver is a lower filter – needs a bus PDO, so VHF is simpler for pure-virtual devices. |
| E13 | Minidriver Operations – https://learn.microsoft.com/en-us/windows-hardware/drivers/hid/minidriver-operations | osdoc | Minidriver registers via HidRegisterMinidriver; must handle fixed IOCTL set (IRP_MJ_INTERNAL_DEVICE_CONTROL, PNP). |
| E14 | HIDClass DDI reference – https://learn.microsoft.com/en-us/windows-hardware/drivers/ddi/_hid/ | osdoc | IOCTLs a minidriver must support; only hidclass.sys sends them. |
| E15 | vhidmini2 sample – https://github.com/microsoft/Windows-driver-samples/tree/main/hid/vhidmini2 | source | UMDF2/KMDF virtual HID minidriver, root-enumerated via `devcon install … root\vhidmini`; official descriptor-testing vehicle. |
| E16 | Keyboard and mouse HID client drivers – https://learn.microsoft.com/en-us/windows-hardware/drivers/hid/keyboard-and-mouse-hid-client-drivers | osdoc | kbdhid.sys/mouhid.sys map HID usages→scan codes/mouse data into kbdclass/mouclass – any HID device with kb/mouse TLCs is bound by inbox mappers. |
| E17 | IOCTL_INTERNAL_KEYBOARD_CONNECT – https://learn.microsoft.com/en-us/windows-hardware/drivers/ddi/kbdmou/ni-kbdmou-ioctl_internal_keyboard_connect | osdoc | A filter substitutes its own CONNECT_DATA service callback – injection rides the *existing* keyboard's identity, not a new device. |
| E18 | IOCTL_INTERNAL_MOUSE_CONNECT – https://learn.microsoft.com/en-us/windows-hardware/drivers/ddi/kbdmou/ni-kbdmou-ioctl_internal_mouse_connect | osdoc | Same contract for mouclass/mouse devices. |
| E19 | kbfiltr sample – https://github.com/microsoft/Windows-driver-samples/tree/main/input/kbfiltr | source | WDF upper filter between KbdClass and i8042prt; "could conceivably add, remove, or modify input." |
| E20 | moufiltr sample – https://github.com/microsoft/Windows-driver-samples/blob/main/input/moufiltr/README.md | source | WDF mouse upper-filter equivalent. |
| E21 | 3rd Party Filter Drivers – https://learn.microsoft.com/en-us/windows-hardware/drivers/hid/3rd-party-filter-drivers | osdoc | Documents Kbfiltr/Moufiltr service-callback templates – official description of filter-level injection. |
| E22 | IOCTL_HID_READ_REPORT – https://learn.microsoft.com/en-us/windows-hardware/drivers/ddi/hidport/ni-hidport-ioctl_hid_read_report | osdoc | hidclass ping-pongs read-report IOCTLs to the minidriver for continuous input – the queue a virtual device fills. |
| E23 | Finding and opening a HID collection – https://learn.microsoft.com/en-us/windows-hardware/drivers/hid/finding-and-opening-a-hid-collection | osdoc | SetupDi* enumeration → device interface path → CreateFile per TLC. |
| E24 | HIDP_CAPS – https://learn.microsoft.com/en-us/windows-hardware/drivers/ddi/hidpi/ns-hidpi-_hidp_caps | osdoc | Per-TLC caps: Usage, UsagePage, report lengths, button/value caps. |
| E25 | Windows-IoT HIDInjector sample – https://github.com/microsoft/Windows-IoT-Samples/tree/master/samples/HIDInjector | source | Microsoft's VHF-based injector for touch/keyboard/mouse with a console app feeding HID blocks via device interface. |
| E26 | gaojs/vhid-keyboard-mouse – https://github.com/gaojs/vhid-keyboard-mouse | source | Community VHF keyboard+mouse driver; verified on Win11 under testsigning. |

## F. Windows – third-party drivers, virtual USB bus, hardware path

| # | Source | Type | Fact supported |
|---|--------|------|----------------|
| F1 | Interception (oblitum) – https://github.com/oblitum/interception | source | Signed kbdclass/mouclass upper filters + user-mode API; admin install; 10 keyboard + 10 mouse slots you can read/steer – but strokes carry the *existing* device's identity. |
| F2 | interception.c IOCTL surface – https://github.com/oblitum/Interception/blob/master/library/interception.c | source | IOCTL_WRITE/READ/GET_HARDWARE_ID implement per-device stroke send/receive. |
| F3 | ViGEmBus – https://github.com/ViGEm/ViGEmBus/ | source | KMDF bus driver creating PDO-backed virtual Xbox 360/DS4 pads; "games require no additional modification" – proven bus+PDO pattern (archived/EOL). |
| F4 | ViGEmClient SDK – https://github.com/nefarius/ViGEmClient/tree/master | source | `vigem_target_*_alloc` + `vigem_target_add` performs virtual plug-in, then feeds reports – client/driver split model. |
| F5 | ViGEm docs – https://docs.nefarius.at/projects/ViGEm/ | project | Operational documentation for the bus driver and SDK. |
| F6 | vmulti (djpnewton) – https://github.com/djpnewton/vmulti | source | Root-enumerated KMDF virtual HID exposing multitouch/mouse/digitizer/keyboard/joystick collections; `testvmulti.exe /mouse` moves the cursor. |
| F7 | vmulticommon.h – https://github.com/djpnewton/vmulti/blob/master/inc/vmulticommon.h | source | One device, VID 0x00FF/PID 0xBACC, distinct REPORT_ID per function (keyboard 0x07, mouse 0x03). |
| F8 | UDECX overview – https://learn.microsoft.com/en-us/windows-hardware/drivers/usbcon/developing-windows-drivers-for-emulated-usb-host-controllers-and-devices | osdoc | KMDF + in-box UdeCx.sys host an emulated USB controller + virtual USB devices with real descriptors/endpoints. |
| F9 | Writing a UDE client driver – https://learn.microsoft.com/en-us/windows-hardware/drivers/usbcon/writing-a-ude-client-driver | osdoc | UdecxUsbDeviceCreate/UdecxUsbDevicePlugIn plug a virtual device into the emulated controller. |
| F10 | usbip-win (cezanne) – https://github.com/cezanne/usbip-win | source | vhci(wdm)/vhci(ude) virtual host controllers; attach remote/virtual USB devices which enumerate normally. |
| F11 | HidHide – https://github.com/nefarius/HidHide/ | source | KMDF filter hiding selected HID devices per-process. |
| F12 | HidHide FAQ – https://docs.nefarius.at/projects/HidHide/FAQ/ | project | Cannot cloak mice/keyboards/touchpads; cannot block Raw Input – per-process filtering does not apply to kb/mouse. |
| F13 | TinyUSB hid_composite – https://docs.tinyusb.org/en/latest/examples/device/hid%5Fcomposite.html | project | Single HID interface multiplexing keyboard/mouse/consumer/gamepad by report ID on a real USB device. |
| F14 | TinyUSB hid_multiple_interface – https://docs.tinyusb.org/en/latest/examples/device/hid_multiple_interface.html | project | Two independent HID interfaces (keyboard + mouse) in one composite USB device. |
| F15 | pico-examples dev_hid_composite – https://github.com/raspberrypi/pico-examples/blob/master/usb/device/dev_hid_composite/main.c | source | Official RP2040 example sending keyboard/mouse/consumer/gamepad reports. |
| F16 | Adafruit TinyUSB hid_composite – https://github.com/adafruit/Adafruit_TinyUSB_Arduino/blob/master/examples/HID/hid_composite/hid_composite.ino | source | Arduino variant with custom VID/PID string descriptors + TUD_HID_REPORT_DESC_KEYBOARD/MOUSE. |

## G. Windows – driver signing and install gates

| # | Source | Type | Fact supported |
|---|--------|------|----------------|
| G1 | Kernel-Mode Code Signing Requirements – https://learn.microsoft.com/en-us/windows-hardware/drivers/install/kernel-mode-code-signing-requirements--windows-vista-and-later- | osdoc | Since Win10 1607 new kernel drivers must be signed by Microsoft via Hardware Dev Center (attestation or WHQL). |
| G2 | Driver Signing Policy – https://learn.microsoft.com/en-us/windows-hardware/drivers/install/kernel-mode-code-signing-policy--windows-vista-and-later- | osdoc | Cross-signed drivers grandfathered only; EV cert required for Dev Center account. |
| G3 | Attestation signing – https://learn.microsoft.com/en-us/windows-hardware/drivers/dashboard/code-signing-attestation | osdoc | Attestation (no HLK) produces drivers valid on Win10 Desktop+; CAB signed with EV cert – fastest legitimate route. |
| G4 | Driver signing offerings matrix – https://learn.microsoft.com/en-us/windows-hardware/drivers/dashboard/driver-signing-offerings | osdoc | Per-version attestation vs HLK vs cross-signed acceptance incl. Device Guard caveats. |
| G5 | TESTSIGNING boot option – https://learn.microsoft.com/en-us/windows-hardware/drivers/install/the-testsigning-boot-configuration-option | osdoc | `bcdedit -set TESTSIGNING ON` + reboot loads test-signed drivers; Secure Boot must be disabled – dev-only. |
| G6 | Installing an unsigned driver during development – https://learn.microsoft.com/en-us/windows-hardware/drivers/install/installing-an-unsigned-driver-during-development-and-test | osdoc | Kernel debugging (`bcdedit -debug on`) disables load-time signature enforcement for dev machines only. |
| G7 | PnPUtil – https://learn.microsoft.com/en-us/windows-hardware/drivers/devtest/pnputil | osdoc | Driver-store add/install requires elevation – no kernel path self-installs unelevated. |
| G8 | Microsoft recommended driver block rules – https://learn.microsoft.com/en-us/windows/security/application-security/application-control/app-control-for-business/design/microsoft-recommended-driver-block-rules | osdoc | Blocklist targets vulnerable/malicious drivers and those that "circumvent the Windows Security Model"; on-by-default with HVCI/Smart App Control/S mode. |

## H. Linux – kernel input subsystem, uinput, uhid, evdev

| # | Source | Type | Fact supported |
|---|--------|------|----------------|
| H1 | uinput module – https://docs.kernel.org/input/uinput.html | kernel | Writing /dev/uinput creates a virtual input device with declared capabilities; events delivered "to userspace and in-kernel consumers" identically to real devices; libevdev recommended. |
| H2 | Input event codes – https://docs.kernel.org/input/event-codes.html | kernel | Stateful protocol: EV_KEY/EV_REL/EV_ABS + EV_SYN/SYN_REPORT framing; SYN_DROPPED on queue overrun. |
| H3 | Input Subsystem driver API – https://docs.kernel.org/driver-api/input.html | kernel | input_register_device() produces devices consumed by evdev handlers at /dev/input/eventX; input_grab_device exclusive grab semantics. |
| H4 | include/uapi/linux/uinput.h – https://github.com/torvalds/linux/blob/master/include/uapi/linux/uinput.h | kernel | uinput_setup{name[80], id.bustype/vendor/product}; UI_SET_PHYS; identity fields are free-form. |
| H5 | Commit 052876f8 (UI_DEV_SETUP/UI_ABS_SETUP) – https://github.com/torvalds/linux/commit/052876f8e5aec887d22c4d06e54aa5531ffcec75 | kernel | uinput v5 ioctls are the supported creation path. |
| H6 | input-event-codes.h – https://github.com/torvalds/linux/blob/master/include/uapi/linux/input-event-codes.h | kernel | Full KEY_*/BTN_*/REL_*/ABS_* code space; BUS_VIRTUAL/BUS_USB bustype values. |
| H7 | drivers/input/evdev.c – https://github.com/torvalds/linux/blob/master/drivers/input/evdev.c | kernel | EVIOCGRAB → evdev_grab(): all device events go to that client exclusively. |
| H8 | input.rst – https://kernel.org/doc/Documentation/input/input.rst | kernel | struct input_event{time,type,code,value}; /dev/input/eventX ABI; evtest for testing. |
| H9 | UHID – user-space HID drivers – https://kernel.org/doc/html/latest/hid/uhid.html | kernel | /dev/uhid registers real kernel hid_devices via UHID_CREATE2; input as raw HID reports – appears like USB/BT hardware. |
| H10 | include/uapi/linux/input.h – https://github.com/torvalds/linux/blob/master/include/uapi/linux/input.h | kernel | EVIOCGRAB (0x90) grab/release, EVIOCREVOKE (0x91), EVIOCGID returns input_id{bustype,vendor,product,version}. |
| H11 | input-programming – https://docs.kernel.org/6.9/input/input-programming.html | kernel | Driver sets dev->name + id.bustype/vendor/product before input_register_device – uinput ids are caller-chosen. |
| H12 | drivers/input/input.c – https://github.com/torvalds/linux/blob/master/drivers/input/input.c | kernel | /proc/bus/input/devices prints Bus/Vendor/Product/Version + Handlers per device – identity observable in userspace. |
| H13 | Input subsystem intro (evdev timestamps) – https://www.kernel.org/doc/html/latest/input/input.html | kernel | Kernel assigns timestamps; reads always return whole events; per-client evdev buffer. |
| H14 | evdev.c annotated (codebrowser) – https://codebrowser.dev/linux/linux/drivers/input/evdev.c.html | kernel | evdev_set_clk_type per-client clock selection; grab exclusivity detail. |
| H15 | kernel_lockdown(7) – https://man7.org/linux/man-pages/man7/kernel_lockdown.7.html | kernel | Lockdown restricts unsigned module loading, /dev/mem, BPF – blocks kernel-level virtual devices under Secure Boot lockdown. |
| H16 | Kernel module signing – https://docs.kernel.org/7.0/admin-guide/module-signing.html | kernel | CONFIG_MODULE_SIG_FORCE rejects unsigned/unknown-key modules. |
| H17 | evtest – http://cgit.freedesktop.org/evtest/plain/evtest.txt | project | Prints device name/phys/capabilities and monitors events; --grab for EVIOCGRAB – verification tool for the second device. |

## I. Linux – udev permissions, seat assignment, libinput

| # | Source | Type | Fact supported |
|---|--------|------|----------------|
| I1 | udev – ArchWiki – https://wiki.archlinux.org/title/Udev | secondary | TAG+="uaccess" grants seat-user ACL via logind; warning: do not uaccess input devices (keylogger risk); MODE 0660 + group is the alternative. |
| I2 | xremap: running without sudo – https://github.com/xremap/xremap/blob/master/doc/running_without_sudo.md | project | Working rule: KERNEL=="uinput", GROUP="input", TAG+="uaccess", MODE:="0660", OPTIONS+="static_node=uinput". |
| I3 | steam-for-linux #4794 – https://github.com/ValveSoftware/steam-for-linux/issues/4794 | forum | uaccess ACL on /dev/uinput fails without OPTIONS+="static_node=uinput" – udev must create the node to tag it. |
| I4 | ydotool PR #315 – https://github.com/ReimuNotMoe/ydotool/pull/315 | source | Minimal deployed rule: KERNEL=="uinput", GROUP="input", MODE="0660", OPTIONS+="static_node=uinput". |
| I5 | systemd 60-input-id.rules – https://github.com/systemd/systemd/blob/master/rules.d/60-input-id.rules | source | IMPORT{builtin}="input_id" sets ID_INPUT* from capability bitmasks; hwdb keyed on bustype/vendor/product/name. |
| I6 | udev-builtin-input_id.c – https://github.com/systemd/systemd/blob/main/src/udev/udev-builtin-input_id.c | source | ID_INPUT_KEYBOARD=1 requires the full alphanumeric block (mask 0xFFFFFFFE on first 32 key bits) – a "keyboard" must advertise real key coverage. |
| I7 | systemd 60-persistent-input.rules – https://github.com/systemd/systemd/blob/master/rules.d/60-persistent-input.rules | source | Maps ID_INPUT_KEYBOARD/MOUSE → /dev/input/by-id/ persistent symlinks – named device gets stable addressable path. |
| I8 | libinput: device configuration via udev – https://wayland.freedesktop.org/libinput/doc/latest/device-configuration-via-udev.html | osdoc | ID_SEAT (default seat0), WL_SEAT (default "default"), LIBINPUT_DEVICE_GROUP; device ignored without ID_INPUT + one type prop. |
| I9 | libinput: Seats – https://wayland.freedesktop.org/libinput/doc/latest/seats.html | osdoc | Each device assigned to exactly one seat; logical seat groups devices for one user; compositor may create additional seats as independent device sets. |
| I10 | libinput device API – https://wayland.freedesktop.org/libinput/doc/latest/api/group__device.html | osdoc | libinput_device_get_udev_device/get_device_group/set_seat_logical_name – compositor-side hooks to identify/reassign the virtual device. |
| I11 | libevdev uinput API – https://freedesktop.org/software/libevdev/doc/latest/group__uinput.html | osdoc | libevdev_uinput_create_from_device(); one fd = one device (second fails EINVAL); device lifetime tied to fd – daemon must hold it open. |
| I12 | libevdev-uinput.c – https://github.com/whot/libevdev/blob/master/libevdev/libevdev-uinput.c | source | UI_DEV_SETUP copies name/vendor/product/bustype verbatim – reference for setting identity. |
| I13 | python-evdev UInput API – https://python-evdev.readthedocs.io/en/latest/apidoc.html | project | UInput(events, name, vendor, product, version, bustype, phys) – all identity fields explicit in Python. |
| I14 | python-evdev tutorial – https://python-evdev.readthedocs.io/en/stable/tutorial.html | project | UInput(cap, name='example-device'); InputDevice.name/.phys readable back – round-trip identifiability. |
| I15 | org.freedesktop.login1 – https://www.freedesktop.org/software/systemd/man/latest/org.freedesktop.login1.html | osdoc | TakeDevice(major,minor) returns fd to session controller only; muted when session inactive – seat-scoped exclusive input access. |
| I16 | seatd/libseat – https://github.com/kennylevinsen/seatd | project | Minimal seat daemon mediating display/input access without root. |
| I17 | sd-login(3) – https://man.archlinux.org/man/core/systemd-libs/sd-login.3.en | osdoc | "seat" tag = seat assignment; "uaccess" = ACL tied to active session. |

## J. Wayland – protocols, seats, compositor reality

| # | Source | Type | Fact supported |
|---|--------|------|----------------|
| J1 | virtual-keyboard-unstable-v1 – https://wayland.app/protocols/virtual-keyboard-unstable-v1 | spec | create_virtual_keyboard(wl_seat); client supplies mmap'd xkb keymap before key/modifiers; compositor "should present an error when an untrusted client requests a new keyboard"; support matrix: wlroots family/COSMIC/Mir yes; KWin/Mutter/Weston no. |
| J2 | wlr-virtual-pointer-unstable-v1 – https://wayland.app/protocols/wlr-virtual-pointer-unstable-v1 | spec | zwlr_virtual_pointer_v1 motion/motion_absolute/button/axis mirroring wl_pointer; optional seat+output binding; wlroots-only. |
| J3 | wlroots virtual-pointer example – https://github.com/swaywm/wlroots/blob/master/examples/virtual-pointer.c | source | Minimal client: bind zwlr_virtual_pointer_manager_v1, create pointer on wl_seat, send motion/button. |
| J4 | wlr_virtual_keyboard_v1.h – https://wlroots.pages.freedesktop.org/wlroots/wlr/types/wlr_virtual_keyboard_v1.h.html | osdoc | Virtual keyboard is a wlr_keyboard bound to a wlr_seat; wlr_input_device_get_virtual_keyboard() distinguishes it from physical – identifiable compositor-side. |
| J5 | wayland-book: Seats – https://wayland-book.com/seat.html | osdoc | A seat has up to one keyboard + one pointer; a second keyboard joins the same seat; multi-seat rare – clients see merged wl_keyboard regardless of device count. |
| J6 | wayland-book: Keyboard – https://wayland-book.com/seat/keyboard.html | osdoc | wl_keyboard.enter/leave carry focus; key events carry serial + scancode – client-visible events carry no device identity. |
| J7 | kde-fake-input protocol – https://wayland.app/protocols/kde-fake-input | spec | org_kde_kwin_fake_input: keyboard_key(evdev)/pointer/touch; header warns "desktop environment implementation detail. Regular clients must not use." |
| J8 | KWin FakeInputBackend – https://invent.kde.org/plasma/kwin/-/blob/master/src/backends/fakeinput/fakeinputbackend.cpp | source | Implements authenticate(application, reason) + key/button/motion/touch per bound resource – KDE-native but private. |
| J9 | wayvnc – https://github.com/any1/wayvnc/ | project | VNC server for wlroots creating virtual input devices via wlr-virtual-pointer + virtual-keyboard; GNOME/KDE/Weston unsupported – production precedent. |
| J10 | wl-kbptr – https://github.com/moverest/wl-kbptr | project | Tested matrix: Sway/Hyprland/niri/dwl/labwc/Wayfire work; KWin lacks wlr-virtual-pointer (ydotool suggested); Mutter lacks all. |
| J11 | wl-uinput-proxy – https://github.com/pgaskin/wl-uinput-proxy | project | Proxies Wayland connection, implementing virtual-keyboard/wlr-virtual-pointer via uinput – protocol surface over kernel backend. |
| J12 | Hyprland Permissions – https://wiki.hypr.land/Configuring/Advanced-and-Cool/Permissions/ | project | keyboard permission is a regex on device name, default ALLOW; can deny "malicious virtual / usb keyboards" – virtual devices are name-identifiable to compositor policy. |
| J13 | Hyprland IKeyboard.hpp – https://github.com/hyprwm/Hyprland/blob/main/src/devices/IKeyboard.hpp | source | `virtual bool isVirtual() = 0;` – virtual keyboards are a distinct device class internally. |
| J14 | sway-input(5) – https://manpages.debian.org/trixie/sway/sway-input.5.en.html | osdoc | swaymsg -t get_inputs lists per-device identifiers; input <identifier> configures exactly one device. |
| J15 | python-wayland wl_seat – https://python-wayland.org/wayland/wl_seat/ | osdoc | Seat capabilities bitmask (pointer/keyboard/touch); get_keyboard errors with missing_capability. |
| J16 | LWN: Wayland security model – https://lwn.net/Articles/589727/ | secondary | Wayland input stack doesn't allow apps to snoop input, generate events appearing as user input, or grab all input – vs X11 which permits all. |
| J17 | Weston multi-seat udev patch – https://lore.freedesktop.org/wayland-devel/1370020199-1132-10-git-send-email-robert.bradford@intel.com/ | source | ENV{WL_SEAT} udev labels pull devices into multiple weston seats – independent seats via device tagging. |
| J18 | SDL Wayland multi-seat PR – https://github.com/libsdl-org/SDL/pull/12626 | source | Wayland can expose multiple seats with "multiple, simultaneously active, desktop pointers and keyboards with independent layouts"; tested on Sway with two kb/mouse sets. |
| J19 | wlroots multi-seat PR – https://github.com/swaywm/wlroots/pull/2417 | source | Wayland-backend multi-seat: tracks multiple seats, multiple pointers, keyboard focus following pointer per seat. |
| J20 | State of multi-player Wayland – https://wps.hkprog.org/posts/state-of-multi-player-wayland-wf9hs3 | secondary | Support matrix: core wayland protocol deep multi-seat; Weston no dynamic reconfigure; sway can't detach devices; niri none; clients must be per-seat aware. |

## K. Wayland – portals and libei (the sanctioned path on GNOME/KDE)

| # | Source | Type | Fact supported |
|---|--------|------|----------------|
| K1 | org.freedesktop.portal.RemoteDesktop – https://flatpak.github.io/xdg-desktop-portal/docs/doc-org.freedesktop.portal.RemoteDesktop.html | spec | CreateSession→SelectDevices(KEYBOARD/POINTER/TOUCHSCREEN)→Start (user dialog); ConnectToEIS() fd (recommended) or Notify* D-Bus (mutually exclusive); persist_mode/restore_token for consent persistence. |
| K2 | impl.portal.RemoteDesktop – https://flatpak.github.io/xdg-desktop-portal/docs/doc-org.freedesktop.impl.portal.RemoteDesktop.html | spec | ConnectToEIS returns fd "to an EIS implementation" for a sender libei context. |
| K3 | xdg-desktop-portal PR #762 – https://github.com/flatpak/xdg-desktop-portal/pull/762 | source | EIS socket supersedes NotifyFoo; after handover app↔compositor talk directly; portal retains kill power; libei has no keysym event. |
| K4 | remote-desktop.c (portal source) – https://github.com/flatpak/xdg-desktop-portal/blob/main/desktop-portal/remote-desktop.c | source | check_position() validates absolute pointer coords against screencast stream bounds; uses_eis blocks mixing paths. |
| K5 | org.freedesktop.portal.ScreenCast – https://flatpak.github.io/xdg-desktop-portal/docs/doc-org.freedesktop.portal.ScreenCast.html | spec | OpenPipeWireRemote() returns fd for pw_context_connect_fd; needed only when screen content requested. |
| K6 | xdg-desktop-portal-gnome commit – https://mail.gnome.org/archives/commits-list/2022-March/msg06564.html | source | GNOME dialog asks for streams only when SelectSources was called – input-only RemoteDesktop sessions are supported. |
| K7 | libei docs – https://libinput.pages.freedesktop.org/libei/index.html | osdoc | libei=client, libeis=compositor, liboeffis=portal helper; emulated events feed "the same way as physical devices… indistinguishable" to Wayland clients; distinguishable inside the compositor for access control. |
| K8 | libei API index – https://libinput.pages.freedesktop.org/libei/api/index.html | osdoc | EI client ≈ physical input device; ei_device_keyboard_key uses evdev scancodes. |
| K9 | libeis server API – https://libinput.pages.freedesktop.org/libei/api/group__libeis.html | osdoc | EIS impl creates seats (eis_client_new_seat) and devices (eis_seat_new_device); impl may disconnect unwanted clients – compositor owns device creation. |
| K10 | libeis device API – https://libinput.pages.freedesktop.org/libei/api/group__libeis-device.html | osdoc | eis_device_configure_name()/get_name() – EIS devices carry names = independently identifiable injected devices. |
| K11 | liboeffis API – https://libinput.pages.freedesktop.org/libei/api/group__liboeffis.html | osdoc | Helper does the portal dance → OEFFIS_EVENT_CONNECTED_TO_EIS → oeffis_get_eis_fd(). |
| K12 | libportal Session.connect_to_eis – https://libportal.org/method.Session.connect_to_eis.html | osdoc | fd usable with ei_setup_backend_fd(); must be called before xdp_session_start(); Notify* ignored afterwards. |
| K13 | xdg-desktop-portal-kde MR !279 – https://invent.kde.org/plasma/xdg-desktop-portal-kde/-/merge_requests/279 | source | KDE ConnectToEIS fetches fd from KWin (org.kde.KWin.EIS.RemoteDesktop) – real EIS endpoint on Plasma Wayland. |
| K14 | xdg-desktop-portal-gnome MR !133 – https://gitlab.gnome.org/GNOME/xdg-desktop-portal-gnome/-/merge_requests/133 | source | GNOME backend implements handle_connect_to_eis() → mutter's EIS. |
| K15 | who-t: libei opening the portal doors – http://who-t.blogspot.com/2022/12/libei-opening-portal-doors.html | secondary | RemoteDesktop hands an EIS socket to the app; portal can still close the session (P. Hutterer, libei author). |
| K16 | who-t: libei integrations – http://who-t.blogspot.com/2026/07/libei-integrations-in-xdg-remotedesktop.html | secondary | "EIS implementation is in control of virtually everything… decides which devices are available, when they can send events." |
| K17 | libei RFC (wayland-devel 2020-07) – https://lists.freedesktop.org/archives/wayland-devel/2020-July/041568.html | spec | "Emulated input comes via a separate channel. The server a) knows it's emulated, b) knows who it is coming from, c) has complete control." |
| K18 | libei RFC (wayland-devel 2020-08) – https://lists.freedesktop.org/archives/wayland-devel/2020-August/041589.html | spec | Portal sets EIS client name to app-id; libreis for capability restrictions; XWayland portal switch = one-line change. |
| K19 | InputLeap PR #1594 – https://github.com/input-leap/input-leap/pull/1594 | source | Working portal→EIS injection: barrierc sender context via ConnectToEIS; --use-ei flag. |
| K20 | impl.portal.InputCapture – https://flatpak.github.io/xdg-desktop-portal/docs/doc-org.freedesktop.impl.portal.InputCapture.html | spec | Complement portal capturing local input via EIS receiver fd – the read-side leg if the extension also captures physical input. |
| K21 | wayland-devel: extension protocols (2023-07) – https://lists.freedesktop.org/archives/wayland-devel/2023-July/042893.html | spec | "Portals negotiate consent and set up sessions; libei transmits events" (jadahl, mutter dev) – endorsed sandboxed injection. |

## L. X11 – XTEST, XI2/MPX, per-device identity

| # | Source | Type | Fact supported |
|---|--------|------|----------------|
| L1 | XTEST Extension Protocol – https://xorg.freedesktop.org/releases/X11R7.7/doc/xextproto/xtest.html | spec | XTestFakeInput simulates KeyPress/Release, ButtonPress/Release, MotionNotify; detail = physical keycode; server "may withdraw such facilities arbitrarily." |
| L2 | XTestFakeKeyEvent(3) – https://man.archlinux.org/man/extra/libxtst/XTestFakeKeyEvent.3.en | osdoc | libXtst API: XTestFakeKeyEvent/FakeButtonEvent/FakeMotionEvent; ignored if extension absent. |
| L3 | xtestlib.html (X11R7.5 archive) – https://x.org/archive/X11R7.5/doc/Xext/xtestlib.html | spec | Same API documented with delay semantics; motion is WarpPointer-like. |
| L4 | XTEST library spec PDF – https://x.org/docs/Xext/xtest.pdf | spec | XTestFakeKeyEvent(display,keycode,press,delay) C signature. |
| L5 | xinput – ArchWiki – https://wiki.archlinux.org/title/Xinput | secondary | xinput list shows "Virtual core XTEST pointer/keyboard" as dedicated slave devices – XTEST input is device-attributed. |
| L6 | xinput(1) man – https://man.archlinux.org/man/extra/xorg-xinput/xinput.1.en | osdoc | create-master prefix creates a master pointer+keyboard pair; reattach moves slave devices; set-cp assigns ClientPointer. |
| L7 | xorg-devel: XTEST device test – https://lists.freedesktop.org/archives/xorg-devel/2012-July/032200.html | source | XIQueryDevice asserts "Virtual core XTEST pointer/keyboard" names (ids 4/5); each new master gets its own XTEST pair. |
| L8 | xdotool README – https://github.com/jordansissel/xdotool/blob/master/README.md | project | "Uses X11's XTEST extension… will not work correctly [on Wayland]"; XWayland only reaches X clients. |
| L9 | xdotool xdo.h – https://github.com/jordansissel/xdotool/blob/main/xdo.h | source | CURRENTWINDOW → XTEST; targeting a specific window → XSendEvent, which sets send_event flag that "many programs observe and reject" – trusted vs synthetic distinction in X11. |
| L10 | pynput limitations – https://pynput.readthedocs.io/en/latest/limitations.html | project | Under Wayland only XWayland-client events seen; PYNPUT_BACKEND_KEYBOARD=uinput requires root – incumbent's failure mode. |
| L11 | Ubuntu bug 2075962 (XWayland XTest→portal) – https://bugs.launchpad.net/bugs/2075962 | forum | XWayland needs libei+liboeffis at build time; then XTEST requests route through the RemoteDesktop portal (user-authorized). |
| L12 | KWin: xwayland enable-ei-portal – https://invent.kde.org/plasma/kwin/-/commit/805435d1572d48beb9499f9b27a0c9d405f05ebb | source | KWin passes -enable-ei-portal to Xwayland when supported – XTEST→portal/EIS wiring on KDE. |
| L13 | MPX (freedesktop wiki) – https://wiki.freedesktop.org/xorg/Development/Documentation/MPX/ | spec | Two-layer hierarchy: slave devices (no cursor) attach to master devices (cursor+keyboard focus); MDs come in pointer/keyboard pairs – true multiple independent cursors+focus on X11. |
| L14 | XI2 protocol (inputproto XI2proto.txt) – https://xorg.freedesktop.org/archive/X11R7.5/doc/inputproto/XI2proto.txt | spec | XI2 introduces master/slave hierarchy, multiple independent master devices (MPX), raw device events; XI1.x clients see only the first master pair. |
| L15 | Multi-pointer X – ArchWiki – https://wiki.archlinux.org/title/Multi-pointer_X | secondary | Xorg ≥1.7 multi-pointer: multiple cursors each with own keyboard focus; xinput create-master/reattach workflow. |
| L16 | RFC: device hierarchy for MPX – https://lists.x.org/archives/xorg/2007-September/028154.html | spec | "Each pointer device a separate cursor and each keyboard device a separate keyboard focus"; MD = merged state of attached SDs. |

## M. Linux – deployed virtual-input tools (patterns)

| # | Source | Type | Fact supported |
|---|--------|------|----------------|
| M1 | ydotool – https://github.com/ReimuNotMoe/ydotool | project | uinput-based, works on X11/Wayland/TTY; ydotoold "requires access to /dev/uinput. This usually requires root"; persistent daemon because udev takes time to recognize a new device. |
| M2 | ydotool(1) man – https://manpages.debian.org/experimental/ydotool/ydotool.1.en.html | osdoc | CLI surface: click/mousemove --absolute/type/key; YDOTOOL_SOCKET. |
| M3 | dotool – https://sr.ht/~geb/dotool/ | project | uinput keyboard/mouse, systemwide incl. TTY, keyboard-layout aware. |
| M4 | dotool(1) – https://git.sr.ht/~geb/dotool/tree/master/doc/dotool.1.scd | project | Requires write to /dev/uinput (input group udev rule); DOTOOL_KEYBOARD_NAME names the virtual keyboard "useful making rules." |
| M5 | wtype – https://github.com/atx/wtype | project | zwp_virtual_keyboard_v1 client; fails if compositor lacks the protocol; keys released when the object is destroyed. |
| M6 | keyd – https://github.com/rvaiya/keyd/blob/master/src/keyd.h | source | Creates uinput device "keyd virtual keyboard" (BUS_USB, Logitech ids); skips managing devices matching that name – self-identification pattern. |
| M7 | kmonad tutorial – https://github.com/kmonad/kmonad/blob/master/keymap/tutorial.kbd | project | output (uinput-sink "name") creates a named virtual keyboard; input grabs a specific /dev/input/by-id device. |
| M8 | Sunshine inputtino_common.h – https://github.com/LizardByte/Sunshine/blob/master/src/platform/linux/input/inputtino_common.h | source | Separate uinput devices "Mouse passthrough"/"Keyboard passthrough", vendor 0xBEEF/product 0xDEAD, seat-suffixed names – the exact two-device architecture. |
| M9 | Sunshine PR #1127 – https://github.com/LizardByte/Sunshine/pull/1127 | source | TAG+="uaccess" grants seat-user ACL on /dev/uinput without input-group membership. |
| M10 | Sunshine PR #2606 – https://github.com/LizardByte/Sunshine/pull/2606 | source | DualSense via /dev/uhid + udev KERNEL=="uhid" GROUP="input" MODE="0660" + modules-load entry – uhid deployment recipe. |
| M11 | Sunshine usage docs – https://docs.lizardbyte.dev/projects/sunshine/v0.17.0/about/usage.html | project | "Sunshine needs access to uinput to create mouse and gamepad events" – confirms uinput as the production injection substrate. |
| M12 | input-remapper reader_service – https://github.com/sezanzeb/input-remapper/blob/main/inputremapper/gui/reader_service.py | source | Root daemon + polkit gate; unprivileged GUI; reader timeouts limit exposure – privilege-separation pattern. |
| M13 | wev – https://git.sr.ht/~sircmpwn/wev | project | Wayland xev: prints wl_keyboard/wl_pointer events, -g lists globals – verification tooling. |
| M14 | NixOS keyd wiki – https://wiki.nixos.org/wiki/Keyd | secondary | libinput quirk MatchName=keyd virtual keyboard → AttrKeyboardIntegration=internal – name-based policy targeting the virtual device. |

## N. macOS – Quartz provenance, TCC, secure input

| # | Source | Type | Fact supported |
|---|--------|------|----------------|
| N1 | CGEventSourceStateID – https://developer.apple.com/documentation/coregraphics/cgeventsourcestateid | osdoc | kCGEventSourceStatePrivate allocates an independent state table + unique source-state ID; HID state reflects hardware. |
| N2 | CGEventSource – https://developer.apple.com/documentation/coregraphics/cgeventsource | osdoc | Source accumulates generation/posting state; deriving a source from a tapped event "marks events as related." |
| N3 | CGEventSource.h (10.9 SDK) – https://github.com/phracker/MacOSX-SDKs/blob/master/MacOSX10.9.sdk/System/Library/Frameworks/CoreGraphics.framework/Versions/A/Headers/CGEventSource.h | source | CGEventSourceCreate(stateID); private-state sources get unique IDs – sanctioned for "remote control programs." |
| N4 | Quartz Event Services Reference – https://leopard-adc.pepas.com/documentation/Carbon/Reference/QuartzEventServicesRef/Reference/reference.html | osdoc | CGEventSourceGetSourceStateID; same ID can back separate mouse/keyboard sources – paired virtual devices sharing one private state. |
| N5 | CGEventTypes.h (10.8 SDK) – https://github.com/phracker/MacOSX-SDKs/blob/master/MacOSX10.8.sdk/System/Library/Frameworks/CoreGraphics.framework/Versions/A/Headers/CGEventTypes.h | source | kCGEventSourceUnixProcessID=41, UserData=42, UserID=43, GroupID=44, SourceStateID=45 – taps can read PID+stateID+64-bit tag per event. |
| N6 | CGEvent.h (10.8 SDK) – https://jenkins.heirloomcomputing.com/downloads/MacOSX10.8.sdk/System/Library/Frameworks/ApplicationServices.framework/Versions/A/Frameworks/CoreGraphics.framework/Versions/A/Headers/CGEvent.h | source | CGEventCreateMouseEvent/KeyboardEvent take a CGEventSourceRef – the stamping point. |
| N7 | CGPostKeyboardEvent – https://developer.apple.com/documentation/coregraphics/cgpostkeyboardevent(_:_:) | osdoc | Deprecated; replacement init(keyboardEventSource:virtualKey:keyDown:) – Apple steers to source-carrying API. |
| N8 | CGEvent.tapCreate – https://developer.apple.com/documentation/coregraphics/cgevent/tapcreate(tap:place:options:eventsofinterest:callback:userinfo:) | osdoc | Only root may create kCGHIDEventTap (where HID events enter WindowServer); non-root → NULL. |
| N9 | CGEvent.tapPostEvent – https://developer.apple.com/documentation/coregraphics/cgevent/tappostevent(_:) | osdoc | Re-posts at the tap's stream position; seen by later taps – tap-originated events inherit tap provenance. |
| N10 | CGPreflightPostEventAccess – https://developer.apple.com/documentation/coregraphics/cgpreflightposteventaccess() | osdoc | Boolean check for post-event authorization – posting requires a TCC grant, not just creation. |
| N11 | CoreGraphics 11.0b3 API diff – http://codeworkshop.net/objc-diff/sdkdiffs/macos/11.0b3/CoreGraphics.html | secondary | CGPreflight/RequestListenEventAccess + PostEventAccess added in Big Sur – TCC split listen vs post. |
| N12 | IOHIDRequestType – https://developer.apple.com/documentation/iokit/iohidrequesttype | osdoc | kIOHIDRequestTypeListenEvent (Input Monitoring) vs PostEvent (Accessibility) – separate TCC gates. |
| N13 | IOHIDRequestAccess – https://developer.apple.com/documentation/iokit/3181574-iohidrequestaccess | osdoc | Triggers the TCC prompt for listen/post. |
| N14 | SO: Input Monitoring status mapping – https://stackoverflow.com/questions/79010369 | secondary | IOHIDCheckAccess(PostEvent) maps to the Accessibility pane; ListenEvent → Input Monitoring; PostEvent implies Listen. |
| N15 | AXUIElement.h – https://developer.apple.com/documentation/applicationservices/axuielement_h | osdoc | AXIsProcessTrusted/AXIsProcessTrustedWithOptions(kAXTrustedCheckOptionPrompt) – the Accessibility trust gate. |
| N16 | Apple: control input monitoring – https://support.apple.com/guide/mac-help/control-access-to-input-monitoring-on-mac-mchl4cedafb6/mac | osdoc | User-level UI for Input Monitoring grants. |
| N17 | Apple Platform Security: protecting app access – https://support.apple.com/guide/security/protecting-app-access-to-user-data-secc01781f46/web | osdoc | TCC enforces Input Monitoring, Screen Recording, Accessibility. |
| N18 | PPPC payload (deployment) – https://support.apple.com/guide/deployment/privacy-preferences-policy-control-payload-dep38df53c2a/1/web/1.0 | osdoc | PostEvent = "use CoreGraphics APIs to send CGEvents to the system event stream"; MDM can pre-grant. |
| N19 | com.apple.TCC configuration profile – https://github.com/apple/device-management/blob/release/mdm/profiles/com.apple.TCC.configuration-profile-policy.yaml | source | ListenEvent grantable only as deny; Accessibility grant deprecated macOS 26.2 – deployment constraints. |
| N20 | TN2150: Using Secure Event Input Fairly – https://developer.apple.com/library/archive/technotes/tn2150/_index.html | osdoc | EnableSecureEventInput (10.3+) blocks keyboard-intercept processes from receiving events; persists when app backgrounds – observation is cut during secure input. |
| N21 | SecureKeyboardEntry (CocoaDev) – https://cocoadev.github.io/SecureKeyboardEntry/ | secondary | Enable/Disable/IsSecureEventInputEnabled API surface. |
| N22 | Chromium secure_password_input.mm – https://github.com/chromium/chromium/blob/main/ui/base/cocoa/secure_password_input.mm | source | Scoped counter around EnableSecureEventInput – production usage. |

## O. macOS – real virtual HID devices (IOHIDUserDevice, DriverKit, CoreHID)

| # | Source | Type | Fact supported |
|---|--------|------|----------------|
| O1 | IOHIDUserDevice.h – https://github.com/opensource-apple/IOKitUser/blob/master/hid.subproj/IOHIDUserDevice.h | source | IOHIDUserDeviceCreate "creates a virtual IOHIDDevice in the kernel"; IOHIDUserDeviceHandleReport dispatches a report to the HID stack. |
| O2 | IOHIDUserDevice.c – https://github.com/opensource-apple/IOKitUser/blob/master/hid.subproj/IOHIDUserDevice.c | source | CFType wrapping io_service_t+io_connect_t; get/setReport callbacks – full client mechanics. |
| O3 | IOHIDUserDevice.cpp (kernel) – https://github.com/apple-oss-distributions/IOHIDFamily/blob/02b1f53c/IOHIDFamily/IOHIDUserDevice.cpp | source | Kernel sets kIOHIDVirtualHIDevice=true unless privileged entitlement; newReportDescriptor reads kIOHIDReportDescriptorKey – virtual flag forcibly stamped. |
| O4 | IOHIDResourceUserClient.cpp – https://github.com/apple-oss-distributions/IOHIDFamily/blob/02b1f53c/IOHIDFamily/IOHIDResourceUserClient.cpp | source | Creation requires com.apple.hid.manager.user-access-device (Apple-private) or com.apple.developer.hid.virtual.device; else "not entitled" – kernel-enforced gate. |
| O5 | IOHIDKeys.h (10.6 SDK) – https://github.com/phracker/MacOSX-SDKs/blob/master/MacOSX10.6.sdk/System/Library/Frameworks/IOKit.framework/Versions/A/Headers/hid/IOHIDKeys.h | source | Property keys (VendorID, ProductID, HIDVirtualDevice, usage pairs) for matching dictionaries. |
| O6 | kIOHIDVirtualHIDevice binding – https://docs.rs/objc2-io-kit/latest/src/objc2_io_kit/generated/hidsystem.rs.html | source | kIOHIDVirtualHIDevice = "HIDVirtualDevice" – the property to query via IOHIDDeviceGetProperty/ioreg. |
| O7 | IOHIDDevice (user-space) – https://developer.apple.com/documentation/iokit/iohiddevice_h_user-space | osdoc | Per-device property/report access – how clients enumerate/verify the virtual device. |
| O8 | IOHIDDevice.h (Darwin) – https://github.com/apple-oss-distributions/IOHIDFamily/blob/02b1f53c/IOHIDFamily/IOHIDDevice.h | source | IOHIDDevice publishes registry properties + reports events through shared memory; "no mandate that the transport layer must be restricted to USB." |
| O9 | IOHIDDevice.cpp (Darwin) – https://github.com/apple-oss-distributions/IOHIDFamily/blob/19666c840a6d896468416ff0007040a10b7b46b8/IOHIDFamily/IOHIDDevice.cpp | source | IOHIDAsyncReportQueue → handleReportWithTime – the async report path a virtual device feeds. |
| O10 | IOHIDLib.c (IOHIDPostEvent) – https://raw.githubusercontent.com/aosm/IOKitUser/master/hidsystem.subproj/IOHIDLib.c | source | Posts evioLLEvent via IOConnectCallMethod to IOHIDSystem; embeds getpid() – injects below WindowServer carrying poster PID; deprecated. |
| O11 | IOHIDPostEvent binding + deprecation – https://docs.rs/objc2-io-kit/latest/objc2_io_kit/fn.IOHIDPostEvent.html | osdoc | Apple deprecation note: "Use CGSEventTap for posting HID events, IOHIDUserDevice for simulating HID device." |
| O12 | ckb input_mac.c – https://github.com/ccMSC/ckb/blob/master/src/ckb-daemon/input_mac.c | source | IOHIDPostEvent returns kIOReturnNotPrivileged unless EUID == /dev/console owner; root alone insufficient. |
| O13 | IOHIDSystem.cpp::postEvent – https://github.com/apple-oss-distributions/IOHIDFamily/blob/main/IOHIDSystem/IOHIDSystem.cpp | source | nxEvent.payload.service_id = sender->getRegistryEntryID(); ext_pid recorded – every queued event tagged with the sending service's registry ID. |
| O14 | IOHIDSystem.h – https://github.com/apple-oss-distributions/IOHIDFamily/blob/02b1f53c/IOHIDSystem/IOKit/hidsystem/IOHIDSystem.h | source | extPostEvent/extSetMouseLocation user-client entry points. |
| O15 | IOHIDShared.h – https://opensource.apple.com/source/IOHIDFamily/IOHIDFamily-1035.1.4/IOHIDSystem/IOKit/hidsystem/IOHIDShared.h.auto.html | source | evioLLEvent/NXEventData wire format for HID injection. |
| O16 | IOHIDEvent.cpp – https://github.com/apple-oss-distributions/IOHIDFamily/blob/02b1f53c/IOHIDFamily/IOHIDEvent.cpp | source | IOHIDEvent carries _senderID + set/getSenderID. |
| O17 | IOHIDEventData.h – https://github.com/apple-oss-distributions/IOHIDFamily/blob/02b1f53c/IOHIDFamily/IOHIDEventData.h | source | IOHIDSystemQueueElement.senderID = "RegistryID of sending service" – queue consumers distinguish devices per event. |
| O18 | IOHIDEventTypes.h – https://opensource.apple.com/source/IOHIDFamily/IOHIDFamily-421.6/IOHIDFamily/IOHIDEventTypes.h.auto.html | source | IOHIDEventSenderID sized to IORegistryEntry::getRegistryEntryID; undefined = 0 – identity = registry entry ID of the device. |
| O19 | IOHIDEventService.cpp – https://github.com/apple-open-source/macos/blob/master/IOHIDFamily/IOHIDFamily/IOHIDEventService.cpp | source | dispatchKeyboardEvent/dispatchRelativePointerEvent/dispatchAbsolutePointerEvent convert reports → IOHIDEvent → dispatchEvent – the translation pipeline. |
| O20 | deskflow OSXKeyState.cpp – https://github.com/deskflow/deskflow/blob/42b824a8/src/lib/platform/OSXKeyState.cpp | source | IOHIDPostEvent for virtual keys – real-world deprecated-API usage (Synergy/Deskflow). |
| O21 | WWDC19-702 System Extensions & DriverKit – https://developer.apple.com/videos/play/wwdc2019/702/ | osdoc | DriverKit = userspace drivers outside the kernel (Catalina+); HID is a DriverKit family – official kext replacement. |
| O22 | Creating a Driver Using DriverKit – https://developer.apple.com/documentation/driverkit/creating-a-driver-using-the-driverkit-sdk | osdoc | IOUserHIDEventService personality needs VendorID/ProductID/PrimaryUsagePage/PrimaryUsage; IOUserHIDDevice = device service class. |
| O23 | Requesting Entitlements for DriverKit – https://developer.apple.com/documentation/DriverKit/requesting-entitlements-for-driverkit-development | osdoc | Request via developer.apple.com/system-extensions; "the system loads only drivers that have a valid set of entitlements." |
| O24 | com.apple.developer.driverkit – https://developer.apple.com/documentation/bundleresources/entitlements/com.apple.developer.driverkit | osdoc | Required on every dext; must be requested. |
| O25 | family.hid.virtual.device entitlement – https://developer.apple.com/documentation/bundleresources/entitlements/com.apple.developer.driverkit.family.hid.virtual.device | osdoc | Doc: lets an app "create and manage virtual HID devices" – conflicts with forum note below (defunct). |
| O26 | HIDDriverKit tag (Apple engineer) – https://developer.apple.com/forums/tags/hiddriverkit | forum | Entitlement map: AppleUserHIDDevice→family.hid.device, AppleUserHIDEventService→family.hid.eventservice, IOHIDInterface→transport.hid; family.hid.virtual.device is defunct; com.apple.developer.hid.virtual.device = CoreHID API; system "makes no strong attempt to identify transport bus." |
| O27 | Karabiner-DriverKit-VirtualHIDDevice – https://github.com/pqrs-org/Karabiner-DriverKit-VirtualHIDDevice | source | Virtual keyboard+mouse dext "recognized by macOS same as physical hardware"; header-only client lib; commands only accepted from root processes – the complete working template. |
| O28 | Karabiner-Elements security docs – https://karabiner-elements.pqrs.org/docs/help/advanced-topics/security/ | project | Core-Service seizes devices and reposts via the virtual driver; VirtualHIDDevice-Daemon only accepts root clients – production privilege model. |
| O29 | Karabiner DEVELOPMENT.md – https://github.com/pqrs-org/karabiner-elements/blob/main/DEVELOPMENT.md | source | Root required for kIOHIDOptionsTypeSeizeDevice and to feed the virtual driver; DriverKit signing needs a paid developer account. |
| O30 | VendorSpecificUSBDriverKitSample – https://github.com/Drewbadour/VendorSpecificUSBDriverKitSample | source | IOUserHIDDevice subclass: override newDeviceDescription/newReportDescriptor, inject via handleReport – the three-method recipe. |
| O31 | HIDDriverKitAccelerationDisableSample – https://github.com/Drewbadour/HIDDriverKitAccelerationDisableSample | source | IOUserHIDEventService subclass; dispatchRelativePointerEvent/dispatchRelativeScrollWheelEvent – the event-service half. |
| O32 | dispatchDigitizerTouchEvent – https://developer.apple.com/documentation/hiddriverkit/iouserhideventservice/dispatchdigitizertouchevent | osdoc | Event services dispatch typed events to the system after parsing reports. |
| O33 | Deprecated kernel extensions – https://developer.apple.com/support/kernel-extensions | osdoc | IOHIDFamily KPIs unsupported since Big Sur; "clients should use HIDDriverKit" – the kext path is dead. |
| O34 | SO: userclient-access entitlement – https://stackoverflow.com/questions/63664458 | secondary | com.apple.developer.driverkit.userclient-access needed for app↔dext IPC; granted per-dext-bundleID. |
| O35 | Core HID framework – https://developer.apple.com/documentation/CoreHID | osdoc | macOS 15+; "emulate a device connected to the system… send input to other apps without physical hardware." |
| O36 | HIDVirtualDevice – https://developer.apple.com/documentation/corehid/hidvirtualdevice | osdoc | "Virtual service to emulate a HID device connected to the system"; dispatchInputReport, activate(delegate:). |
| O37 | Creating virtual devices (CoreHID) – https://developer.apple.com/documentation/corehid/creatingvirtualdevices | osdoc | "System treats the device as any other external peripheral"; HIDVirtualDevice.Properties(descriptor:vendorID:) + delegate for get/setReport. |
| O38 | Forums 822647: HIDVirtualDevice + Accessibility – https://origin-devforums.apple.com/forums/thread/822647 | forum | HIDVirtualDevice for keyboard/mouse/touchpad triggers the Accessibility TCC prompt – tied to device type, not API. |
| O39 | Forums 820676: App Review rejection – https://origin-devforums.apple.com/forums/thread/820676 | forum | App using HIDVirtualDevice rejected under guideline 2.4.5 (Accessibility for non-accessibility purpose) – MAS distribution risk. |
| O40 | SO 79839945: HIDVirtualDevice requirements – https://stackoverflow.com/questions/79839945 | secondary | Signing with com.apple.developer.hid.virtual.device alone → AMFI kill (err -413); entitlement requires Apple-issued profile via request form. |
| O41 | Forums 820066: seize + virtual HID – https://origin-devforums.apple.com/forums/thread/820066 | forum | Apple-endorsed pattern: CoreHID seizeDevice() on the real device → re-emit via virtual HID device. |
| O42 | PassKeeZ #26 (uhid port) – https://github.com/Zig-Sec/PassKeeZ/issues/26 | forum | Linux uhid → HIDVirtualDevice port plan incl. dispatchInputReport sample – the uinput analogue. |
| O43 | foohid – https://github.com/unbit/foohid | source | Legacy IOKit driver for userspace virtual HID (keyboard/mouse/joypad) – pre-DriverKit approach, obsolete on modern macOS. |
| O44 | Karabiner device_if conditions – https://karabiner-elements.pqrs.org/docs/json/complex-modifications-manipulator-definition/conditions/device/ | project | Conditions match vendor_id, product_id, is_built_in_keyboard, is_karabiner_virtual_hid_device – downstream tools can distinguish the virtual device. |
| O45 | Karabiner #3083 device JSON – https://github.com/pqrs-org/Karabiner-Elements/issues/3083 | forum | Device records expose device_id (registry ID), location_id, transport, is_karabiner_virtual_hid_device. |
| O46 | Karabiner discussion #3980 – https://github.com/pqrs-org/Karabiner-Elements/discussions/3980 | forum | device_id = registry entry ID, changes per connect; stable identity = vendor/product, not registry ID. |

## P. macOS – event taps, test stacks, single-cursor limit

| # | Source | Type | Fact supported |
|---|--------|------|----------------|
| P1 | CGEventTapLocation – https://developer.apple.com/documentation/coregraphics/cgeventtaplocation | osdoc | kCGHIDEventTap only for root processes; session/annotated taps per login session – injection position ladder. |
| P2 | XCUICoordinate – https://developer.apple.com/documentation/xcuiautomation/xcuicoordinate | osdoc | click()/click(forDuration:thenDragTo:) – element-relative synthesis inside test bundles only. |
| P3 | XCUIElement (Xcode 7.2 docs mirror) – https://bootstraponline.github.io/xcuitest/Xcode_7.2_(7C68)/public_docs/html/Classes/XCUIElement.html | osdoc | typeText:/click/typeKey:modifierFlags: synthesized relative to resolved element – test-runner context only. |
| P4 | Appium XCUITest input-events guide – https://appium.github.io/appium-xcuitest-driver/latest/guides/input-events/ | project | XCPointerEventPath/XCSynthesizedEventRecord are private, undocumented; "supplied to the system kernel for execution" – private SPI reaches HID-level synthesis. |
| P5 | WebDriverAgent XCEventGenerator.h – https://github.com/facebook/WebDriverAgent/blob/master/PrivateHeaders/XCTest/XCEventGenerator.h | source | -_postCGEvent:, clickAtPoint:, hoverAtPoint: – even Apple's macOS test stack bottoms out at CGEvent. |
| P6 | Hammerspoon libeventtap_event.m – https://github.com/Hammerspoon/hammerspoon/blob/master/extensions/eventtap/libeventtap_event.m | source | CGEventPost(kCGSessionEventTap)/CGEventPostToPSN; kCGHIDEventTap "doesn't seem to be any different" – posting location doesn't hide process provenance. |
| P7 | cliclick – https://github.com/BlueM/cliclick/ | source | CLI mouse/keyboard emulation entirely on CGEventCreate*/CGEventPost – the status-quo approach being replaced. |
| P8 | SO: simulating mouse input – https://stackoverflow.com/questions/2734117 | secondary | Canonical CGEventCreateMouseEvent+CGEventPost(kCGHIDEventTap) snippet. |
| P9 | Dynamouse – https://github.com/projectstorm/dynamouse/ | source | "Mac allows multiple mice plugged-in… it doesn't allow multiple cursors"; assigns pointer devices to displays via Accessibility – single-cursor constraint. |
| P10 | Superuser: two mice, two pointers – https://superuser.com/questions/649325/two-mice-two-pointers-one-mac | secondary | No good way to a secondary mouse cursor – all mouse APIs assume one cursor. |
| P11 | FS-UAE mouse docs (ManyMouse) – https://fs-uae.net/docs/mouse/ | project | Multiple mice disabled on macOS due to security prompts; Input Monitoring grant needed to see individual devices – per-device reading is permission-gated. |

## Q. Remote desktop protocols (wire→device)

| # | Source | Type | Fact supported |
|---|--------|------|----------------|
| Q1 | MS-RDPBCGR: Keyboard and Mouse Input – https://learn.microsoft.com/en-us/openspecs/windows_protocols/ms-rdpbcgr/f0ea088b-1398-43f0-af42-f4e027ab2009 | spec | Client→server input PDUs in slow-path (T.128-like) and fast-path forms convey keyboard/mouse data the server injects. |
| Q2 | MS-RDPBCGR: Slow-Path Input Event – https://learn.microsoft.com/en-us/openspecs/windows_protocols/ms-rdpbcgr/a9a26b3d-84a2-495f-83fc-9edd6601f33b | spec | TS_INPUT_EVENT messageTypes: SCANCODE 0x0004, UNICODE 0x0005, MOUSE 0x8001, MOUSEX 0x8002, MOUSEREL 0x8004. |
| Q3 | MS-RDPBCGR: Fast-Path Input Event PDU – https://learn.microsoft.com/en-us/openspecs/windows_protocols/ms-rdpbcgr/37879f07-d502-4426-b218-c6119f58349c | spec | Fast-path container of keyboard/unicode/mouse/mousex/sync/QoE/relative-mouse events. |
| Q4 | MS-RDPBCGR: TS_FP_INPUT_EVENT – https://learn.microsoft.com/en-us/openspecs/windows_protocols/ms-rdpbcgr/76c4dd59-7ba0-445d-a03c-885212ab80f6 | spec | eventHeader packs eventCode (scancode/mouse/mousex/sync/unicode/mouserel) + flags. |
| Q5 | MS-RDPBCGR: Processing Fast-Path Input PDU – https://learn.microsoft.com/en-us/openspecs/windows_protocols/ms-rdpbcgr/178aef78-2606-4e44-a94a-6ee6f6dc5cc6 | spec | Server MUST drop the connection on unknown event types. |
| Q6 | MS-RDPBCGR: Fast-Path Keyboard Event – https://learn.microsoft.com/en-us/openspecs/windows_protocols/ms-rdpbcgr/089d362b-31eb-4a1a-b6fa-92fe61bb5dbf | spec | keyCode = 1-byte scancode; RELEASE/EXTENDED flags; Pause = Ctrl+NumLock sequence – layout-independent. |
| Q7 | MS-RDPBCGR: Unicode Keyboard Event – https://learn.microsoft.com/en-us/openspecs/windows_protocols/ms-rdpbcgr/551b9903-8fb9-4d00-b3ac-a187431efb86 | spec | unicodeCode sends a codepoint instead of scancode; requires INPUT_FLAG_UNICODE. |
| Q8 | MS-RDPBCGR: TS_INPUT_CAPABILITYSET – https://learn.microsoft.com/en-us/openspecs/windows_protocols/ms-rdpbcgr/b3bc76ae-9ee5-454f-b197-ede845ca69cc | spec | INPUT_FLAG_SCANCODES/MOUSEX/FASTPATH_INPUT/UNICODE/MOUSE_RELATIVE negotiated at connect. |
| Q9 | MS-RDPEI: Input Virtual Channel – https://learn.microsoft.com/en-us/openspecs/windows_protocols/ms-rdpei/72a8cb65-7f6c-407c-a21a-3d970721fed0 | spec | Touch/pen frames over DVC Microsoft::Windows::RDS::Input "injected into the session." |
| Q10 | FreeRDP libfreerdp/core/input.c – https://github.com/FreeRDP/FreeRDP/blob/master/libfreerdp/core/input.c | source | input_send_keyboard_event serializes flags+keyCode into INPUT_EVENT_SCANCODE PDUs; freerdp_input_send_keyboard_event public API. |
| Q11 | FreeRDP rdpei.h – https://github.com/FreeRDP/FreeRDP/blob/master/include/freerdp/channels/rdpei.h | source | RDPEI_CHANNEL_NAME + RDPINPUT_CONTACT_FLAG_*/CONTACT_DATA – touch injection reference. |
| Q12 | xorgxrdp rdpKeyboard.c – https://github.com/neutrinolabs/xorgxrdp/blob/devel/xrdpkeyb/rdpKeyboard.c | source | xrdpkeyb_drv.so is a real Xorg input driver; RDP key msgs → KbdAddEvent → core keyboard events – server-side input IS a registered device. |
| Q13 | xorgxrdp rdpMouse.c – https://github.com/neutrinolabs/xorgxrdp/blob/devel/xrdpmouse/rdpMouse.c | source | rdpInputMouse → QueuePointerEvents(POINTER_ABSOLUTE); 9-button mask diffing – absolute pointer injection into X. |
| Q14 | MS-RDPEUSB: USB Devices Virtual Channel – https://learn.microsoft.com/en-us/openspecs/windows_protocols/ms-rdpeusb/a1004d0e-99e9-4968-894b-0b924ef2f125 | spec | URBDRC relays USB packets; server creates a matching device – device redirection makes a client-side emulated USB device appear local. |
| Q15 | RFC 6143 §7.5.4 KeyEvent – https://datatracker.ietf.org/doc/html/rfc6143#section-7.5.4 | spec | RFB msg 4: down-flag + 32-bit X11 keysym "even if the client or server is not running X." |
| Q16 | RFC 6143 §7.5.5 PointerEvent – https://datatracker.ietf.org/doc/html/rfc6143#section-7.5.5 | spec | RFB msg 5: button-mask bits 0–7 + absolute x/y – absolute pointer injection. |
| Q17 | rfbproto.rst (QEMU Extended Key Event) – https://github.com/rfbproto/rfbproto/blob/master/rfbproto.rst | spec | Msg 255/subtype 0 carries keysym + XT keycode – keymap-independent VNC input for VMs emulating PS/2. |
| Q18 | TigerVNC VNCServerST.cxx – https://github.com/TigerVNC/tigervnc/blob/master/common/rfb/VNCServerST.cxx | source | keyEvent(keysym,keycode,down) gated by acceptKeyEvents → desktop->keyEvent – server-side dispatch point. |
| Q19 | TigerVNC vncInput.c – https://github.com/TigerVNC/tigervnc/blob/master/unix/xserver/hw/vnc/vncInput.c | source | codeMap[xtcode] when raw code present else keysym mapping; QueuePointerEvents for motion/buttons. |
| Q20 | TigerVNC XDesktop.cxx (x0vncserver) – https://github.com/TigerVNC/tigervnc/blob/master/unix/x0vncserver/XDesktop.cxx | source | Injects into an existing X session via XTestFakeKeyEvent/ButtonEvent/MotionEvent – wire→XTEST bridge. |
| Q21 | noVNC API.md (RFB.sendKey) – https://github.com/novnc/noVNC/blob/master/docs/API.md | project | sendKey(keysym, code, down); code accepts DOM KeyboardEvent.code – JS API emitting device-level RFB events. |
| Q22 | noVNC API-internal.md – https://github.com/novnc/noVNC/blob/master/docs/API-internal.md | project | core/input/keyboard.js translates DOM keyDown/keyUp to X11 keysyms. |
| Q23 | LibVNCClient rfbclient.c – https://github.com/LibVNC/libvncserver/blob/master/src/libvncclient/rfbclient.c | source | SendPointerEvent/SendKeyEvent write rfbPointerEventMsg/rfbKeyEventMsg to the socket – minimal C client input. |
| Q24 | spice.proto InputsChannel – https://gitlab.freedesktop.org/spice/spice-protocol/-/blob/master/spice.proto | spec | key_down/key_up(uint32 code), mouse_motion(dx/dy), mouse_position(x,y,display_id), mouse_press/release; server mouse_motion_ack flow control. |
| Q25 | SPICE protocol documentation – https://spice-space.org/spice-protocol.html | spec | Dedicated inputs channel; "Key value is expressed using PC AT scan code"; server mode = relative MOUSE_MOTION, client mode = absolute MOUSE_POSITION. |
| Q26 | SPICE protocol PDF v1.0 – https://www.spice-space.org/static/docs/spice_protocol.pdf | spec | Channel-split session model; inputs channel "controls the server mouse and the keyboard." |
| Q27 | SpiceInputsChannel API – https://www.spice-space.org/api/spice-gtk/SpiceInputsChannel.html | osdoc | spice_inputs_key_press uses PC XT scancodes (0xe0 prefix → OR 0x100); set_key_locks syncs guest LEDs. |
| Q28 | SPICE user manual (mouse modes) – https://spice.pages.freedesktop.org/spice-space/spice-user-manual.html | osdoc | Client mouse mode needs an absolute pointing device (USB tablet in QEMU); cursor may desync – absolute vs relative tradeoff. |
| Q29 | usbredir protocol v0.7 – https://github.com/SPICEorg/usbredir/blob/master/usb-redirection-protocol.txt | spec | Tunnels USB transfers for a single device over TCP/VMC; usb_redir_header{type,length,id} + control/data packets. |
| Q30 | SPICE usbredir overview – https://www.spice-space.org/usbredir.html | osdoc | usbredir independent of SPICE transport; QEMU side hw/usb/redirect.c; the server doesn't care if the device is physical or emulated. |
| Q31 | Guacamole protocol reference – https://guacamole.apache.org/doc/gug/protocol-reference.html | spec | key instruction (keysym, pressed) using X11 keysym; mouse instruction (x, y, button-mask). |
| Q32 | Guacamole protocol overview – https://guacamole.apache.org/doc/gug/guacamole-protocol.html | osdoc | Client→server instructions are "control instructions and events (mouse and keyboard)" – input is a separate instruction stream. |
| Q33 | libguac protocol.h – https://guacamole.apache.org/doc/1.5.5/libguac/protocol_8h.html | osdoc | guac_protocol_send_key(socket, keysym, pressed, timestamp) / send_mouse(x, y, mask, timestamp). |

## R. Hypervisors and virtual machines

| # | Source | Type | Fact supported |
|---|--------|------|----------------|
| R1 | Virtio spec 1.4 – Input Device (ID 18) – https://docs.oasis-open.org/virtio/virtio/v1.4/cs01/virtio-v1.4-cs01.pdf | spec | virtio_input_event{type,code,value} mirrors Linux evdev; eventq device→driver input, statusq LED feedback – paravirt HID spec. |
| R2 | QEMU virtio-input-pci.c – https://gitlab.com/qemu-project/qemu/-/blob/master/hw/virtio/virtio-input-pci.c | source | virtio-keyboard-pci/-mouse-pci/-tablet-pci/-multitouch-pci device types; tablet = absolute pointer. |
| R3 | QEMU QMP input-send-event – https://www.qemu.org/docs/master/interop/qemu-qmp-ref.html | osdoc | input-send-event takes InputEvent union (key/btn/rel/abs/mtu) + optional device/head routing; send-key + QKeyCode for convenience – management-plane injection. |
| R4 | QEMU ui/input-linux.c – https://gitlab.com/qemu-project/qemu/-/blob/master/ui/input-linux.c | source | -object input-linux,evdev=/dev/input/eventN reads evdev → qcode → qemu_input_event_send_key_qcode; grab via Ctrl+Ctrl – replaying a uinput device is a viable path. |
| R5 | QEMU vhost-user-input docs – https://www.qemu.org/docs/master/system/devices/virtio/vhost-user-contrib.html | osdoc | External daemon (contrib/vhost-user-input --evdev-path=…) feeds the guest over virtqueue+shared memory – out-of-process input injection. |
| R6 | QEMU USB emulation docs – https://www.qemu.org/docs/master/system/devices/usb.html | osdoc | usb-tablet = absolute-coordinate pointer overriding PS/2; usb-host passthrough by hostbus/hostaddr or vendorid+productid. |
| R7 | libvirt domain XML <input> – https://libvirt.org/formatdomain.html#elementsInput | osdoc | <input type='tablet' bus='usb|virtio'/>; type='passthrough' maps host evdev into the guest via virtio-input-host. |
| R8 | libvirt virDomainSendKey – https://libvirt.org/html/libvirt-libvirt-domain.html#virDomainSendKey | osdoc | virDomainSendKey(dom, codeset, holdtime, keycodes, flags); codesets LINUX/XT/ATSET1-3 – hypervisor-agnostic key injection. |
| R9 | VirtualBox SDK IKeyboard – https://www.virtualbox.org/sdkref/interface_i_keyboard.html | osdoc | putScancode(s), putUsageCode (USB HID usage ID), putCAD – scancode + HID-usage injection via console object. |
| R10 | VirtualBox SDK IMouse – https://www.virtualbox.org/sdkref/interface_i_mouse.html | osdoc | putMouseEvent relative; putMouseEventAbsolute(x,y,…) in pixels from [1,1]; putEventMultiTouch. |
| R11 | Hyper-V Msvm_Keyboard.TypeScancodes – https://learn.microsoft.com/en-us/windows/win32/hyperv_v2/msvm-keyboard-typescancodes | osdoc | WMI TypeScancodes(uint8[]) simulates key sequences in the VM – host→guest injection without RDP. |
| R12 | Hyper-V input classes – https://learn.microsoft.com/en-us/windows/win32/hyperv_v2/input-classes | osdoc | Every VM has Msvm_Keyboard, Msvm_Ps2Mouse, Msvm_SyntheticMouse (synthetic requires VMBus). |
| R13 | USB/IP protocol – https://docs.kernel.org/usb/usbip_protocol.html | kernel | OP_REQ_IMPORT binds a device; USBIP_CMD_SUBMIT ships URBs over TCP; RET_SUBMIT returns results – whole USB device (incl. HID) over network. |
| R14 | usbip stub_rx.c – https://github.com/torvalds/linux/blob/master/drivers/usb/usbip/stub_rx.c | kernel | stub_recv_cmd_submit builds a real urb from the network PDU and submits it to the local USB device – the wire→physical-USB boundary. |
| R15 | Linux USB HID gadget – https://docs.kernel.org/usb/gadget_hid.html | kernel | g_hid/configfs emulates USB HID; write HID reports to /dev/hidgX; sample keyboard report descriptor – the target host sees a genuine USB keyboard. |
| R16 | PiKVM USB configuration – https://docs.pikvm.org/usb/ | project | OTG gadget exposes hid.usb0 keyboard + hid.usb1 absolute and hid.usb2 relative mice; 9-endpoint budget – production KVM-over-IP proving gadget input at scale. |

## S. Browser-level input (trusted vs untrusted)

| # | Source | Type | Fact supported |
|---|--------|------|----------------|
| S1 | CDP Input domain – https://chromedevtools.github.io/devtools-protocol/tot/Input/ | spec | dispatchKeyEvent (windowsVirtualKeyCode/nativeVirtualKeyCode/code/key/commands), dispatchMouseEvent, dispatchTouchEvent, insertText – input enters the real pipeline. |
| S2 | Chromium input_handler.cc – https://chromium.googlesource.com/chromium/src/+/main/content/browser/devtools/protocol/input_handler.cc | source | DispatchMouseEvent builds blink::WebMouseEvent → host_->ForwardMouseEvent on RenderWidgetHostView – same path as real input → isTrusted=true DOM events. |
| S3 | chromium-dev: dispatchEvent vs DevTools input – https://groups.google.com/a/chromium.org/g/chromium-dev/c/q7EAxeILS9Q | forum | DevTools-injected events "appear from the browser", create user gestures and default actions; JS dispatchEvent is untrusted – authoritative app-vs-device distinction. |
| S4 | W3C WebDriver Actions – https://www.w3.org/TR/webdriver1/ | spec | POST /session/{id}/actions; input sources none|key|pointer|wheel; session input state table persists pressed state; actions dispatch through the UA input pipeline (trusted). |
| S5 | WebDriver WD (actions endpoints) – https://www.w3.org/TR/2026/WD-webdriver2-20260528/ | spec | Perform Actions / Release Actions endpoints; session input source list. |
| S6 | WebDriver BiDi input module – https://w3c.github.io/webdriver-bidi/#module-input | spec | input.performActions/releaseActions/setFiles; reuses the Actions processing model over bidirectional transport. |
| S7 | MDN: BiDi input.performActions – https://developer.mozilla.org/en-US/docs/Web/WebDriver/Reference/BiDi/Modules/input/performActions | osdoc | Actions array of typed sources (key/pointer/wheel) with per-source ids – multiple named logical devices per context. |
| S8 | MDN: BiDi input module – https://developer.mozilla.org/en-US/docs/Web/WebDriver/Reference/BiDi/Modules/input | osdoc | Commands "simulate user input actions such as key presses, mouse clicks, scrolling, file selection" per browsing context. |
| S9 | Selenium Actions API – https://www.selenium.dev/documentation/webdriver/actions_api/ | osdoc | "Low-level interface for providing virtualized device input"; key/pointer/wheel sources; depressed state persists across ActionBuilder instances; add_key_input/add_pointer_input create named extra devices. |
| S10 | Selenium action_builder source – https://www.selenium.dev/selenium/docs/api/py/_modules/selenium/webdriver/common/actions/action_builder.html | source | ActionBuilder devices list; add_key_input(name="keyboard2")/add_pointer_input(kind, name) – multiple named input sources per session. |
| S11 | Playwright Keyboard API – https://playwright.dev/docs/api/class-keyboard | osdoc | keyboard.type generates keydown/keypress/input/keyup; insertText "dispatches only input event, does not emit keydown/keyup/keypress." |
| S12 | Playwright server/input.ts – https://github.com/microsoft/playwright/blob/main/packages/playwright-core/src/server/input.ts | source | Keyboard/Mouse wrap per-browser RawKeyboard/RawMouse; track _pressedModifiers/_pressedKeys – framework→protocol dispatch architecture. |
| S13 | Playwright webViewInput.ts – https://github.com/microsoft/playwright/blob/main/packages/injected/src/webview/webViewInput.ts | source | WebView path constructs new KeyboardEvent/InputEvent + dispatchEvent – the untrusted fallback, contrasted with the CDP path. |
| S14 | Puppeteer cdp/Input.ts – https://github.com/puppeteer/puppeteer/blob/main/packages/puppeteer-core/src/cdp/Input.ts | source | CdpKeyboard.down → Input.dispatchKeyEvent{type:'keyDown'|'rawKeyDown', windowsVirtualKeyCode, code, key} – Puppeteer input = CDP Input domain. |
| S15 | Firefox bug 1848958 (widget-level input) – https://bugzilla.mozilla.org/show_bug.cgi?id=1848958 | forum | Marionette/BiDi moved to sending mouse events "at the widget level instead of synthesized DOM events" – closer to real user input. |
| S16 | MarionetteCommandsChild.sys.mjs – https://searchfox.org/firefox-main/source/remote/marionette/actors/MarionetteCommandsChild.sys.mjs | source | #dispatchEvent → lazy.event.synthesizeMouseAtPoint/sendKeyDown on windowUtils – synthesis via nsIDOMWindowUtils, not DOM dispatchEvent. |
| S17 | Event.isTrusted – https://developer.mozilla.org/en-US/docs/Web/API/Event/isTrusted | osdoc | true only for UA-generated events; dispatchEvent()/click() yield isTrusted=false – the web-layer injected-detection analog. |

## T. Streaming and game-streaming input

| # | Source | Type | Fact supported |
|---|--------|------|----------------|
| T1 | moonlight-common-c Limelight.h – https://github.com/moonlight-stream/moonlight-common-c/blob/master/src/Limelight.h | source | LiSendMouseMoveEvent/MousePositionEvent/MouseButtonEvent/KeyboardEvent2(keyCode, keyAction, modifiers)/Utf8TextEvent – full input API over ENet. |
| T2 | moonlight-common-c Input.h – https://github.com/moonlight-stream/moonlight-common-c/blob/master/src/Input.h | source | NV_KEYBOARD_PACKET (DOWN 0x03/UP 0x04, keyCode+modifiers), ABS/REL_MOUSE_MOVE, UTF8_TEXT_EVENT; ENet channels KEYBOARD 0x02 / MOUSE 0x03 – device-level wire packets. |
| T3 | Sunshine src/input.cpp – https://github.com/LizardByte/Sunshine/blob/master/src/input.cpp | source | Parses NV_* packet magics and dispatches passthrough() to platform backends – host-side decode of streaming input. |
| T4 | FreeRDP xf_event.c – https://github.com/FreeRDP/FreeRDP/blob/6562b6f8/client/X11/xf_event.c | source | X11 client event handling + pointer/keyboard grabs – local capture side of RDP input. |
| T5 | FreeRDP xf_input.c – https://github.com/FreeRDP/FreeRDP/blob/75abb988/client/X11/xf_input.c | source | XI2 registration (XIQueryVersion ≥2.2), raw/device event registration – XInput2-based capture. |

## U. Android contrast (same theory, different gate)

| # | Source | Type | Fact supported |
|---|--------|------|----------------|
| U1 | IInputManager.aidl – https://android.googlesource.com/platform/frameworks/base/+/refs/heads/main/core/java/android/hardware/input/IInputManager.aidl | source | injectInputEvent/injectInputEventToTarget require INJECT_EVENTS; targeted-UID injection supported. |
| U2 | AOSP commit (INJECT_EVENTS model) – https://android.googlesource.com/platform/frameworks/base/+/edff3851325467a3f56ebe87af67df326b00a318 | source | Signature-level permission granted to system + shell – app-level injection impossible without platform signature. |
| U3 | scrcpy keyboard.md – https://github.com/Genymobile/scrcpy/blob/master/doc/keyboard.md | project | --keyboard=uhid "simulates a physical HID keyboard using the UHID kernel module" – appears as physical keyboard; same device-node strategy as desktop uinput/uhid. |
| U4 | scrcpy(1) – https://manpages.debian.org/testing/scrcpy/scrcpy.1.en.html | osdoc | --otg simulates physical kbd+mouse "as if plugged directly via OTG"; sdk mode uses system API (text-limited) – device emulation beats API injection for fidelity. |

## V. Incumbent libraries (what computer-use currently does)

| # | Source | Type | Fact supported |
|---|--------|------|----------------|
| V1 | pynput keyboard/_win32.py – https://github.com/moses-palmer/pynput/blob/master/lib/pynput/keyboard/_win32.py | source | KeyCode._parameters → SendInput(1, INPUT(KEYBOARD, KEYBDINPUT)) – current Windows keyboard path is SendInput. |
| V2 | pynput mouse/_win32.py – https://github.com/moses-palmer/pynput/blob/c3af9c8132e73/lib/pynput/mouse/_win32.py | source | _press/_release/_scroll → SendInput with MOUSEINPUT; position via SetCursorPos. |
| V3 | pynput _util/win32.py – https://github.com/moses-palmer/pynput/blob/master/lib/pynput/_util/win32.py | source | INPUT/MOUSEINPUT/KEYBDINPUT ctypes structures; SendInput = windll.user32.SendInput. |
| V4 | pynput keyboard/_darwin.py – https://github.com/moses-palmer/pynput/blob/master/lib/pynput/keyboard/_darwin.py | source | _handle → CGEventPost(kCGHIDEventTap, …) – current macOS path is Quartz injection. |
| V5 | pynput mouse/_darwin.py – https://github.com/moses-palmer/pynput/blob/master/lib/pynput/mouse/_darwin.py | source | _position_set/_press/_scroll → CGEventPost(kCGHIDEventTap) with CGEventCreateMouseEvent/ScrollWheelEvent. |
| V6 | pynput keyboard/_xorg.py – https://github.com/moses-palmer/pynput/blob/master/lib/pynput/keyboard/_xorg.py | source | _handle → Xlib.ext.xtest.fake_input – current Linux/X11 path is XTEST. |
| V7 | pynput docs index (backends) – https://github.com/moses-palmer/pynput/blob/master/docs/index.rst | project | Backends: darwin (macOS), win32 (Windows), uinput (optional Linux keyboard-only, root), xorg (default elsewhere), dummy. |
| V8 | PyAutoGUI _pyautogui_win.py – https://github.com/asweigart/pyautogui/blob/master/pyautogui/_pyautogui_win.py | source | WinAPI ctypes INPUT/MOUSEINPUT/KEYBDINPUT; "All keyboard presses are sent to the window that currently has focus." |

## W. Security research and trusted-path theory

| # | Source | Type | Fact supported |
|---|--------|------|----------------|
| W1 | CWE-422 / Paget Shatter attack – https://cwe.mitre.org/data/definitions/422 | paper | 2002: unprivileged app sends window messages to higher-privilege app → arbitrary code exec – the flaw class UIPI exists to close. |
| W2 | Shatter attacks (Wikipedia) – https://en.wikipedia.org/wiki/Shatter_attacks | secondary | Windows message system let messages be injected into any same-session app with a message loop. |
| W3 | NCSC-TG-005 (Trusted Network Interpretation) – https://irp.fas.org/nsa/rainbow/tg005.htm | paper | Extends TCSEC trusted-path concept to networks. |
| W4 | TCSEC trusted path (TG-017) – https://irp.fas.org/nsa/rainbow/tg017.htm | paper | B2+: "TCB shall support a trusted communication path… initiated exclusively by a user"; B3: "logically isolated and unmistakably distinguishable" – definitional basis for SAS/secure desktop. |
| W5 | Common Criteria FTP_TRP.1 – https://commoncriteriaportal.org/files/ccfiles/CC2022PART2R1.pdf | paper | Trusted path: logically distinct channel, assured endpoint identification, protection from modification/disclosure. |
| W6 | NIST SP 800-53 SC-11 Trusted Path – https://nist-sp-800-53-r5.bsafes.com/docs/3-18-system-and-communications-protection/sc-11-trusted-path/ | paper | Trusted paths let "users communicate (using input devices such as keyboards) directly with security functions"; Ctrl+Alt+Del cited as non-spoofable. |
| W7 | SGXIO (CODASPY 2017) – https://doi.org/10.48550/arxiv.1701.01061 | paper | Generic trusted I/O path for SGX protecting against "kernel-level keyloggers." |
| W8 | VIPER (CCS 2011) – https://netsec.ethz.ch/publications/papers/li_mccune_perrig_viper_ccs2011.pdf | paper | Timed challenge-response attestation of peripheral firmware – provenance of the device itself ("is the keyboard really a keyboard"). |
| W9 | Flicker (EuroSys 2008) – https://www.andrew.cmu.edu/user/bparno/papers/flicker.pdf | paper | Isolated execution with ~250-line TCB even against hostile BIOS/OS/DMA. |
| W10 | LPM whole-system provenance (USENIX Sec 2015) – https://www.usenix.org/system/files/conference/usenixsecurity15/sec15-paper-bates.pdf | paper | Kernel-layer provenance framework; provenance itself is "a ripe attack vector." |
| W11 | CamFlow (SoCC 2017) – https://dl.acm.org/doi/10.1145/3127479.3129249 | paper | Whole-system provenance via LSM+Netfilter – captures how objects (incl. input events) reached their state. |
| W12 | BadUSB (BH USA 2014) – https://infocondb.org/con/black-hat/black-hat-usa-2014/badusb-on-accessories-that-turn-evil | paper | Reprogrammed USB controller spoofs device class – storage converts itself to "keyboard"; host trust in HID is exploitable. |
| W13 | USB Rubber Ducky docs – https://documentation.hak5.org/hak5-usb-rubber-ducky | project | ATTACKMODE HID [VID pid] emulates a keyboard typing DuckyScript; Keystroke Reflection abuses HID OUT (LED) endpoint – HID identity spoof + trust model. |
| W14 | Wardle: Synthetic Reality (OBTS v2) – https://objectivebythesea.org/v2/talks/OBTS_v2_Wardle.pdf | paper | WindowServer checks CGXSenderCanSynthesizeEvents (sandbox_check "hid-control"); synthetic clicks with pid==0 bypassed the filter (CVE-2017-7150) – macOS provenance-check internals. |
| W15 | Objective-See blog (synthetic click filtering) – https://objective-see.org/blog/blog_0x36.html | secondary | TCC prompts protected: "Sender is prohibited from synthesizing events" when the poster lacks assistive access. |
| W16 | Objective-See: TCC events in Endpoint Security – https://objective-see.org/blog/blog_0x7F.html | secondary | ES_EVENT_TYPE_NOTIFY_TCC_MODIFY (macOS 15.4) exposes permission grants to ES clients – provenance observability for TCC state. |

## X. Multiseat gaming stack (multiple humans, one machine, dedicated devices)

| # | Source | Type | Fact |
|---|--------|------|------|
| X1 | Nucleus Co-op README (SplitScreen-Me) – https://github.com/SplitScreen-Me/splitscreenme-nucleus/blob/master/README.md | project | Symlinks and opens multiple game instances (mutex killing sometimes required); each instance "will only answer to one specific gamepad" via custom xinput libraries; instances connected via LAN/online emulation (Goldberg, Nemirtingas); windows resized/repositioned for synthetic split-screen. |
| X2 | Nucleus Co-op repo – https://github.com/SplitScreen-Me/splitscreenme-nucleus | source | Current maintained fork of the split-screen launcher. |
| X3 | lucasassislar/nucleuscoop README (original) – https://github.com/lucasassislar/nucleuscoop/blob/master/README.md | project | Original design: symlinked game folder per instance, "customized version of xinput libraries that will only answer to one specific gamepad instance"; xinput1 passthroughs gamepad 1, xinput2 passes to slot 2, etc.; generic per-game JS handler. |
| X4 | Nucleus Co-op v2.4.0 release – https://github.com/SplitScreen-Me/splitscreenme-nucleus/releases/tag/v2.4.0 | project | SDL2 gamepad restriction DLL; multiple-players-per-instance assignment (XInput/Proto XInput, SDL2); hook DLLs can trigger AV false positives – deployment caveat. |
| X5 | Nucleus handler docs – https://distrohelena.github.io/nucleuscoop/ | project | Handler options incl. KillMutex (single-instance mutex names to close), ForceFinishOnPlay, per-game OnPlay callbacks. |
| X6 | Universal Split Screen repo – https://github.com/UniversalSplitScreen/UniversalSplitScreen | source | "Split screen multiplayer for any game with multiple keyboards, mice and controllers" – the input-routing layer (superseded by ProtoInput). |
| X7 | USS HooksCPP.cpp – https://github.com/UniversalSplitScreen/UniversalSplitScreen/blob/develop/HooksCPP/HooksCPP.cpp | source | In-process hooks: `RegisterRawInputDevices_Hook` returns TRUE without registering (game thinks it registered); `WM_INPUT` filter compares `raw->header.hDevice` to `allowed_mouse_handle`/`allowedCtrler` – ALLOW or BLOCK per message; legacy message filters; DirectInput device enumeration hooks. |
| X8 | ProtoInput – https://github.com/Ilyaki/ProtoInput | source | Successor: performs "all input redirection from within the target process using hooks"; modular C API (protoloader.h) lets a host install hooks (RegisterRawInputHookID etc.) per instance; in-process redirection = smoother input + better game compatibility. |
| X9 | USS releases – https://github.com/UniversalSplitScreen/UniversalSplitScreen/releases | source | Hook list incl. DirectInput→XInput translation (DInput has no 4-controller cap); FindWindow hook so a game can't detect another instance's window; "faking window focus within the input" for the Raw Input filter. |
| X10 | USS quickstart – https://universalsplitscreen.github.io/docs/quickstart/ | project | Workflow: launch multiple instances, assign mouse/keyboard/controller per window; single-instance blocks worked around via steam_api.dll rename or Goldberg emulator. |

## Y. Containerized/VM mini-environments with virtualized input

| # | Source | Type | Fact |
|---|--------|------|------|
| Y1 | usbipd-win – https://github.com/dorssel/usbipd-win | source | Windows service+CLI sharing locally attached USB devices to WSL 2 **and Hyper-V guests** (and any remote usbip client); `bind` persists, `attach` doesn't; while attached the device is unavailable to Windows. |
| Y2 | MS: Connect USB devices to WSL – https://learn.microsoft.com/en-gb/windows/wsl/connect-usb | osdoc | Official WSL2 USB guide via usbipd-win; requires WSL kernel ≥5.10.60.1; bind needs admin, attach does not. |
| Y3 | usbipd-win WSL support wiki – https://github.com/dorssel/usbipd-win/wiki/WSL-support | project | `usbipd attach --wsl` flow; udev rules inside WSL needed for non-root device access. |
| Y4 | woshub: USB to WSL/Hyper-V – https://woshub.com/share-host-usb-devices-windows-wsl-hyper-v/ | secondary | usbipd-win passes devices to Linux guests on Hyper-V; previously only USB drives/Enhanced Session Mode redirection existed. |
| Y5 | MS Q&A: USB passthrough in Hyper-V – https://learn.microsoft.com/en-us/answers/questions/2193986/usb-passthrough-in-hyper-v-and-networking-with-hyp | forum | Hyper-V has **no native USB passthrough** (unlike VMware/VirtualBox); workarounds = RDP/Enhanced Session redirection or USB-over-IP. |
| Y6 | MS Q&A: USB passthrough Hyper-V ARM – https://learn.microsoft.com/en-us/answers/questions/2280146/usb-pass-through-on-hyper-v-windows-pro-arm-system | forum | On ARM hosts no shipped usbipd; third-party USB-over-Ethernet (VirtualHere, FlexiHub) is the workaround. |
| Y7 | joonas.fi: Attach a keyboard to a Docker container – https://joonas.fi/2020/12/attach-a-keyboard-to-a-docker-container/ | secondary | Practical recipe: forward a specific `/dev/input/by-id/*` node into the container + `EVIOCGRAB` for exclusive access (host desktop stops seeing the device); Xvfb+x11vnc as the virtual display. |
| Y8 | vuinputd – https://github.com/joleuger/vuinputd | source | CUSE-based proxy for `/dev/uinput`: fake uinput inside each container, host daemon creates the real uinput devices, udev rules tag/isolate them per container – host ignores them, container sees them natively; works with Docker/Podman/LXC/systemd-nspawn. |
| Y9 | Wolf: how it works – https://games-on-whales.github.io/wolf/stable/dev/how-it-works.html | project | inputtino creates virtual input devices via uinput/uhid on the host; recommended udev rules restrict them to a group and **move mouse+keyboard to a different seat**; fake-udev forwards hotplug into app containers; per-app headless Wayland compositor (gst-wayland-display, Smithay/Rust) feeds the encode pipeline. |
| Y10 | Wolf repo – https://github.com/games-on-whales/wolf | source | Moonlight streaming server: multiple users stream different content on one host; on-demand virtual desktops, any resolution/FPS, no monitor; apps run in Docker containers. |
| Y11 | Wolf quickstart – https://games-on-whales.github.io/wolf/stable/user/quickstart.html | project | Reference container flags: `--device /dev/dri /dev/uinput /dev/uhid`, `-v /dev:/dev`, `-v /run/udev`, `--device-cgroup-rule "c 13:* rmw"`. |
| Y12 | Wolf configuration – https://games-on-whales.github.io/wolf/stable/user/configuration.html | project | Per-app runner (docker/process), `GOW_REQUIRED_DEVICES=/dev/input/event*`, `WOLF_RENDER_NODE` gives each app its own GPU render node. |
| Y13 | labwc-headless-docker – https://github.com/XT-Martinez/labwc-headless-docker | source | Headless labwc (wlroots) Wayland session in Docker + Sunshine/WayVNC; `start-fake-udev.sh` monitors host udev events and mknods matching `/dev/input/eventN` inside the container – per-container input isolation. |
| Y14 | Incus forum: headless wayland container – https://discuss.linuxcontainers.org/t/headless-wayland-container-streaming-via-sunshine-sway-libinput-not-finding-input-devices/18852 | forum | unix-char device passthrough of `/dev/input/eventN` + `/dev/uinput` into a container; sway runs on libinput or headless backend; uinput-created devices don't hotplug via unix-hotplug – fake-udev/mknod needed. |
