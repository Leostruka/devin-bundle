# Privileged broker templates (opt-in, admin-provisioned)

These templates expose exactly one privileged operation —
restart of an allowlisted system service (`service.restart`) — through
an OS-authorized broker. There is no generic command execution, no
wildcard capability, and no credential forwarding.

The bundle installer **only copies these template files**. Nothing is
registered, loaded, or activated automatically. Every provisioning
step below requires an administrator account and includes a dry-run or
check command so the change can be verified before it takes effect.

## Windows — JEA endpoint (`windows-jea.pssc`)

Prerequisite: elevated PowerShell (Run as Administrator).

### Install

```powershell
# Dry-run / check: validate the session configuration file first.
Test-PSSessionConfigurationFile -Path .\windows-jea.pssc -Verbose

# Copy to a stable location and register the endpoint.
Copy-Item .\windows-jea.pssc "$env:ProgramData\system-control\windows-jea.pssc"
Register-PSSessionConfiguration `
    -Name SystemControlBroker `
    -Path "$env:ProgramData\system-control\windows-jea.pssc" `
    -Force
```

### Status

```powershell
Get-PSSessionConfiguration -Name SystemControlBroker
```

The `.pssc` ships no `RoleDefinitions`, so only local administrators
can connect initially. To bind a non-admin subject, grant access
explicitly after registration:

```powershell
Set-PSSessionConfiguration -Name SystemControlBroker `
    -ShowSecurityDescriptorUI   # grant Execute on the SDDL dialog
```

### Disable

```powershell
Disable-PSSessionConfiguration -Name SystemControlBroker
# Verify: the endpoint shows Enabled = False.
Get-PSSessionConfiguration -Name SystemControlBroker |
    Select-Object Name, Enabled
```

### Uninstall

```powershell
Unregister-PSSessionConfiguration -Name SystemControlBroker -Force
Remove-Item "$env:ProgramData\system-control\windows-jea.pssc"
# Verify: no output means the endpoint is gone.
Get-PSSessionConfiguration -Name SystemControlBroker
```

## Linux — polkit action (`linux-polkit.policy`)

Prerequisite: root (or sudo).

### Install

```sh
# Dry-run / check: validate the XML before installing.
pkaction --action-id dev.system-control.restart-allowed-service 2>/dev/null \
    || xmllint --noout linux-polkit.policy

install -o root -g root -m 0644 linux-polkit.policy \
    /usr/share/polkit-1/actions/dev.system-control.policy
systemctl restart polkit   # or: pkcheck to verify on next call
```

### Status

```sh
pkaction --action-id dev.system-control.restart-allowed-service --verbose
```

### Disable

```sh
# Polkit has no disable verb; remove the file and reload.
rm /usr/share/polkit-1/actions/dev.system-control.policy
systemctl restart polkit
# Verify: "no action" means the action is gone.
pkaction --action-id dev.system-control.restart-allowed-service
```

### Uninstall

Identical to disable: remove the installed policy file and reload
polkit. Verify with the same `pkaction` lookup — the broker then
reports unprovisioned and all dispatches are rejected before any
OS call.
