---
name: red-team
description: Use when running an authorized offensive-security engagement against a declared target (binary, web app, network, wireless, firmware, mobile). Routes to domain skills (re-binary, web-probe, net-probe, wireless-probe, firmware-probe, mobile-probe) and enforces the engagement contract (target/window/ROE) plus evidence discipline.
triggers: [user, model]
---

# Red Team

Orchestrator for authorized offensive work. Sibling of `security`
(defensive, audits our own code); this tree operates on declared targets
under an explicit engagement contract.

## Engagement contract (mandatory)

Every offensive action requires, before any command runs:

- `target`: declared scope (host, URL, artifact path, device)
- `window`: engagement window
- `roe`: rules of engagement reference (allowed techniques, limits)

Missing contract = refuse and ask. Destructive or irreversible actions
require explicit per-action confirmation. No credential harvesting.
Missing tool = `unknown`, never fabricated; unsupported platform =
`unsupported_platform`.

## Domain routing

| Target type | Skill | Engine |
|---|---|---|
| Binary / APK / firmware RE | `re-binary` | `extensions/rea-ops/wrapper.py` |
| Web app / API / injection | `web-probe` | `offsec-tools` (zap, sqlmap, nuclei, ffuf) |
| Host / network / SMB / TLS | `net-probe` | `offsec-tools` (nmap, netexec, testssl.sh) |
| Wi-Fi / RF / SDR / RFID | `wireless-probe` | `offsec-tools` (aircrack, hcxtools, kismet) |
| Firmware image / embedded | `firmware-probe` | `offsec-tools` (binwalk, unblob, emba) |
| Android/iOS app | `mobile-probe` | `offsec-tools` (jadx, apktool, mobsf, frida) |

## Environment check (always first)

```bash
python extensions/rea-ops/wrapper.py doctor        # REA CLI + engines
python extensions/offsec-tools/wrapper.py doctor   # tools x backends
python extensions/offsec-tools/wrapper.py capabilities
```

Backend order for `offsec-tools run`: `--backend native|wsl|docker`,
else auto (native -> wsl -> docker). WSL2 covers most Linux-only tools;
RF capture needs usbipd-win + hardware; native-linux-only tiers report
`unsupported_platform`.

## Evidence discipline

Every finding records: command argv, backend, tool version,
target sha256 (for artifacts), confidence (`confirmed|likely|unknown`),
and limitations. `unknown` is a valid answer; absence of evidence is not
evidence of absence. Store engagement artifacts under `.devin/scratch/`
or the engagement workdir, never in target scope.

## Boundaries

- Defensive audits of our own code/config go to `security` skill.
- No novel payload authoring; use documented tool capabilities.
- No credential harvesting, exfiltration of real secrets, or persistence.
- Active/destructive tool modes are gated by the wrapper (`--confirm`);
  confirm per action with the user, not per session.
