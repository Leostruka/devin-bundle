# Feasibility – "Docker-like" Mini Virtual Environments with Dedicated/Virtualized Input

Date: 2026-09-22. Question: can we build lightweight virtual environments (container/VM) where one physical mouse+keyboard pair is dedicated to the environment – and computer-use/ Devin drives it – while the user's own devices stay untouched? Sources: `virtual-input-devices-sources.md` sections Q, R, X, Y (IDs referenced).

## 1. Verdict

**Feasible – and already built, twice.** Two production precedents implement almost exactly this:

- **Wolf (games-on-whales)**: apps run in Docker containers on Linux; `inputtino` creates **virtual uinput/uhid devices on the host per app**; udev rules tag them to a dedicated group and **move them to a different seat** so the host desktop ignores them; `fake-udev` forwards hotplug events into the app container; each app gets a headless Wayland compositor (Smithay-based `gst-wayland-display`) whose framebuffer feeds a stream encoder [Y9–Y12]. This is "Docker for virtual desktops with virtual input" – minus game streaming, it's the reference architecture.
- **vuinputd**: a CUSE proxy that gives each container a fake `/dev/uinput`; a host daemon creates the real uinput devices and udev rules scope them per-container; works with Docker/Podman/LXC/systemd-nspawn [Y8]. This is the generic "mediated virtual input" component.

Two independent input paths exist at once – the physical pair dedicated to the env AND a virtual pair Devin writes – because Linux input is device-per-node and compositor-attachable.

## 2. The mechanism, decomposed

A "mini environment with virtualized input" needs four separable pieces:

| Piece | Linux host | Windows host |
|---|---|---|
| **Container/VM boundary** | Docker/Podman/systemd-nspawn (namespace isolation, shared kernel) or QEMU/KVM VM | WSL2 (lightweight VM), Hyper-V VM, or QEMU/VirtualBox |
| **Dedicate physical kb+mouse to env** | `--device /dev/input/by-id/<dev>` into container + **EVIOCGRAB** so the host desktop stops seeing them [Y7, H7/H10]; or udev `ID_SEAT`/`WL_SEAT` to a non-`seat0` seat [I8, I9, J17] | `usbipd bind` + `attach` → device detaches from Windows entirely and appears in WSL2/Hyper-V Linux guest [Y1–Y4] (Hyper-V has no native USB passthrough [Y5, Y6]) |
| **Devin's input channel into env** | dedicated **uinput** device created on host, forwarded into the container (vuinputd/fake-udev), or wire protocol: WayVNC/RFB, SPICE, QMP `input-send-event` for VMs [Y8, Y13, Q15–Q17, R3] | inside WSL2/VM: uinput device or RFB/QMP; for Hyper-V guests also `Msvm_Keyboard.TypeScancodes` [R11] |
| **Display/observation** | headless compositor (labwc/weston headless, sway headless, Xvfb) + WayVNC/x11vnc/Sunshine stream [Y13, Y14, Y7] | WSLg/Weston or RDP/VNC into the guest; VM console stream |

## 3. Reference design (closest to "Docker for computer-use")

Per environment (say `env-1`):

```
physical mouse B + keyboard B
    │  EVIOCGRAB on host (or ID_SEAT=agent / usbipd attach)
    ▼
/dev/input/by-id/*-B  ──--device──►  container env-1
                                        ├─ headless Wayland/X compositor
                                        ├─ app under test
                                        └─ wayvnc/x11vnc → framebuffer → Devin vision

Devin input path:
    host: uinput device "devin-kb-1"/"devin-mouse-1"  (created by daemon)
        │  udev tag → forwarded into env-1 (vuinputd / fake-udev / mknod)
        ▼
    compositor in env-1 sees them as normal seat devices
```

- **Devin's devices never touch the host session**: udev rules scope them to the env's seat/group (Wolf's documented practice [Y9]) – the host compositor ignores them, so agent input can't reach user apps, and vice versa the user's physical devices can't reach env-1 (grabbed or seat-assigned).
- **Two cursors for real**: inside env-1's compositor there's a pointer; the host has its own. This is the only way to get true cursor/focus independence – separate compositors/seats, which is precisely what sections J17–J20 (multi-seat) and Y9 (per-app compositor) document.
- **Hotplug**: uinput-created devices don't appear inside containers automatically – solved pattern = fake-udev/mknod forwarding [Y8, Y13, Y14].

## 4. Windows-specific path (this machine)

- **WSL2 route (lightest real VM)**: plug 2nd kb+mouse → `usbipd bind` (admin, persistent) + `usbipd attach --wsl` (no admin) → the devices vanish from Windows and appear as evdev nodes inside WSL2 [Y1–Y3]. Run the containerized env inside WSL2 (Docker Desktop or plain dockerd): `--device` the event nodes in, plus a uinput pair for Devin. Bonus property: **while attached, Windows physically cannot use those devices** – perfect dedication, automatic release on detach.
- **Hyper-V route**: same usbipd share → `usbip attach` inside a Linux guest (usbipd-win explicitly supports Hyper-V guests [Y1, Y4]). Heavier; needs manual guest setup.
- **VirtualBox/QEMU route**: USB filter by VID/PID or port → guest. Works; heavier than WSL2.
- **No-VM alternative on Windows**: there is no seat/container equivalent for GUI input isolation – Windows containers can't host independent interactive input stacks (no per-container desktop). The mini-env on Windows realistically = WSL2 or a VM.
- **Important shortcut**: if the target is already a VM/container, Devin doesn't need a physical second pair at all – hypervisor/wire injection (QMP `input-send-event`, virtio-input, RFB `KeyEvent/PointerEvent`, Msvm TypeScancodes) IS the independent virtual input channel [R3, R1, Q15–Q17, R11]. Physical dedication is only needed if a *second human* will also drive that env locally.

## 5. What already exists vs what to build

| Component | Existing | Build needed? |
|---|---|---|
| Mediated virtual input for containers | vuinputd [Y8]; inputtino+udev-seat pattern [Y9] | No – reuse/fork |
| Headless compositor per env | labwc-headless-docker, Wolf gst-wayland-display, weston/sway headless, Xvfb | No – pick one |
| Input forwarding host→env | fake-udev/mknod pattern [Y13, Y14]; EVIOCGRAB [Y7] | Thin wrapper |
| Windows device dedication | usbipd-win (WSL2, Hyper-V) [Y1] | No – CLI orchestration only |
| Devin input backend inside env | uinput writer (Linux), RFB/SPICE client, QMP client | Small – computer-use needs a "virtual-env" backend adapter |
| Lifecycle orchestration | none off-the-shelf for this exact purpose | The actual new work: create env, bind devices, spawn compositor+agent input device, teardown with all-keys-up |

## 6. Risks and limits

- **Container ≠ security boundary**: `/dev/input`, `/dev/dri`, device-cgroup `c 13:* rmw` grants pierce isolation (the Hyperland gist and Wolf flags make this explicit) – fine for trusted Devin workloads, not for hostile code.
- **udev race**: devices created via uinput take time to be recognized; persistent daemon or fake-udev forwarding required [M1, Y14].
- **Windows host adds a hop**: no native Hyper-V USB passthrough → usbipd is the only general path; attach is non-persistent across reboots/unplugs [Y1].
- **Display is separate work**: input is the easy half; the env needs a framebuffer (headless compositor) + stream (VNC/SPICE/WayVNC/Sunshine) for the agent's vision loop.
- **VM injection supersedes hardware**: inside any VM, prefer QMP/virtio-input/RFB over passing physical devices – simpler and fully independent [R1–R3].

## 7. Recommendation

Build it as a `virtual-env` backend on top of existing pieces:

1. **Linux**: container + dedicated seat – `--device` second kb+mouse (EVIOCGRAB or `ID_SEAT=agent`), vuinputd/fake-udev for Devin's uinput pair, headless labwc/weston + WayVNC for vision. Wolf's udev/seat rules are the template.
2. **Windows**: WSL2 + usbipd attach for physical dedication; the Linux container stack runs inside WSL2 unchanged. For stronger isolation, Hyper-V guest + usbipd.
3. **Any VM target**: skip physical devices; expose `input-send-event`/virtio-input/RFB as the Devin channel – this is the simplest fully-independent path and needs zero extra hardware.
4. Reuse, don't reinvent: vuinputd (input mediation), inputtino/Wolf udev rules (seat isolation), labwc/weston headless (compositor), WayVNC/RFB (I/O channel).
