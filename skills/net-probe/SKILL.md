---
name: net-probe
description: Use when probing declared hosts or networks under an engagement contract (port/service scan, SMB/AD enumeration, TLS audit, vulnerability scan). Routes to extensions/offsec-tools/wrapper.py tools: nmap, masscan, netexec, enum4linux-ng, testssl.sh, openvas. Verify-not-exploit by default.
triggers: [user, model]
---

# Net Probe

Network/infrastructure offensive testing under contract, via
`extensions/offsec-tools/wrapper.py` (domain `net`).

## Contract (mandatory)

`--target` (host/CIDR), `--window`, `--roe`. ROE states scan rate,
excluded hosts, and whether credentialed checks are in scope.

## Tools

| Tool | Mode | Use |
|---|---|---|
| `nmap` | active | port/service/version scan, NSE scripts |
| `masscan` | active | high-rate discovery; raw-socket (WSL preferred) |
| `netexec` | active | SMB/WinRM/LDAP enumeration and checks |
| `enum4linux-ng` | active | SMB/RPC user/share enumeration |
| `testssl.sh` | passive | TLS config/cipher audit |
| `openvas` | active | full vuln scan (Docker GVM stack) |

## Commands

```bash
W=extensions/offsec-tools/wrapper.py

python $W run --tool nmap --target 10.0.0.5 --window "..." --roe "..." \
  --confirm -- -sV -Pn --top-ports 1000 10.0.0.5
python $W run --tool netexec --target 10.0.0.0/24 --window "..." \
  --roe "..." --confirm --backend wsl -- smb 10.0.0.0/24
python $W run --tool testssl.sh --target t.example:443 --window "..." \
  --roe "..." --backend wsl
```

Backend: native first; `masscan`/`testssl.sh`/`netexec` are usually
healthier on `wsl`. `openvas` is docker-only and heavy -- confirm the
engagement actually needs it.

## Evidence

Per finding: probe argv, backend, raw output excerpt, confidence.
Scanner output is a lead, not a finding -- verify with a targeted probe
before reporting `confirmed`.

## Boundaries

- Verify-not-exploit default: prove exposure, do not pivot or persist.
- No credential harvesting (no dumping LSASS/NTDS, no relay-to-auth).
- Excluded hosts/rates in ROE are hard stops.
