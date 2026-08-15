---
name: heartbeat
description: Use when a task needs periodic monitoring or scheduled re-entry, when the user wants the agent to check on something at intervals, or when emulating PrimeAgent's heartbeat and schedule features within Devin CLI's lifecycle-event-driven runtime.
---

# Heartbeat (Scheduled Re-Entry)

## When to Use

- Monitoring a long-running build, deployment, or CI pipeline
- Polling for a PR review, merge, or external event
- Periodic health checks (test suite, lint, dependency status)
- Scheduled tasks (run checks every N minutes, daily reports)
- Emulating PrimeAgent's `/heartbeat` and `prime-agent schedule`

## When NOT to Use

- One-shot check — just run the command
- Task completes in seconds — no need for periodic monitoring
- Real-time alerting is needed — use external monitoring (Sentry, PagerDuty)

## Source

Adapts PrimeAgent's heartbeat and schedule features (PrimeIntellect blog,
2026-08-05). PrimeAgent supports `/heartbeat`, `rlm_heartbeat`, and
`prime-agent schedule` for periodic session re-entry. Devin CLI hooks fire on
lifecycle events (PreToolUse, PostToolUse, Stop), not on time schedules. This
skill emulates scheduled re-entry using OS-level schedulers + a heartbeat
script that launches a new Devin CLI session with a prompt.

## Core Concept

**Three layers:**
1. **OS scheduler** (Task Scheduler on Windows, cron on Linux/macOS) triggers at intervals
2. **Heartbeat script** writes a prompt file and launches Devin CLI
3. **Devin CLI session** reads the prompt, runs the check, writes results

```
┌─────────────────┐     ┌──────────────────┐     ┌─────────────────┐
│  OS Scheduler   │────▶│  Heartbeat Script │────▶│  Devin CLI      │
│  (every 5 min)  │     │  (writes prompt)  │     │  (runs check)   │
└─────────────────┘     └──────────────────┘     └─────────────────┘
                                                         │
                                                         ▼
                                                ┌─────────────────┐
                                                │  Results file   │
                                                │  (JSON log)     │
                                                └─────────────────┘
```

## Heartbeat Script

A Python script that:
1. Writes a prompt file with the check to run
2. Launches Devin CLI with that prompt (non-interactive mode if available)
3. Logs the result

### Cross-platform script

```python
#!/usr/bin/env python3
"""Heartbeat: launches a Devin CLI session with a scheduled prompt."""
import subprocess, json, os, datetime, sys

HEARTBEAT_DIR = os.path.join(os.getcwd(), ".devin", "heartbeats")
os.makedirs(HEARTBEAT_DIR, exist_ok=True)

# Read heartbeat config
config_path = os.path.join(HEARTBEAT_DIR, "config.json")
if not os.path.exists(config_path):
    print("No heartbeat config found. Create .devin/heartbeats/config.json")
    sys.exit(1)

with open(config_path) as f:
    config = json.load(f)

prompt = config.get("prompt", "Run health check.")
log_path = os.path.join(HEARTBEAT_DIR, "log.jsonl")

# Write prompt file for Devin CLI
prompt_file = os.path.join(HEARTBEAT_DIR, "prompt.txt")
with open(prompt_file, "w") as f:
    f.write(prompt)

# Launch Devin CLI (adjust command for your setup)
# On Windows: devin.exe --prompt-file <file>
# On Linux: devin --prompt-file <file>
# Adjust the binary name and flags per your installation
devin_cmd = config.get("devin_command", "devin")
result = subprocess.run(
    [devin_cmd, "--prompt-file", prompt_file],
    capture_output=True, text=True, timeout=300
)

# Log result
entry = {
    "timestamp": datetime.datetime.now().isoformat(),
    "prompt": prompt,
    "exit_code": result.returncode,
    "stdout": result.stdout[:1000],  # bounded
    "stderr": result.stderr[:500],   # bounded
}
with open(log_path, "a") as f:
    f.write(json.dumps(entry) + "\n")

print(f"Heartbeat logged to {log_path}")
```

## Setup Workflow

### Step 1: Create heartbeat config

```
write .devin/heartbeats/config.json {"prompt": "Run npm test and report any failures. If all pass, report 'green'.", "devin_command": "devin", "interval_minutes": 5}
```

### Step 2: Install the heartbeat script

Copy the script above to:
- Windows: `%APPDATA%\devin\scripts\heartbeat.py`
- Linux/macOS: `~/.config/devin/scripts/heartbeat.py`

### Step 3: Register with OS scheduler

**Windows (Task Scheduler):**
```powershell
$action = New-ScheduledTaskAction -Execute "python" -Argument "%APPDATA%\devin\scripts\heartbeat.py" -WorkingDirectory "<project dir>"
$trigger = New-ScheduledTaskTrigger -Once -At (Get-Date) -RepetitionInterval (New-TimeSpan -Minutes 5)
Register-ScheduledTask -TaskName "devin-heartbeat" -Action $action -Trigger $trigger
```

**Linux/macOS (cron):**
```bash
echo "*/5 * * * * cd /path/to/project && python ~/.config/devin/scripts/heartbeat.py" | crontab -
```

### Step 4: Monitor results

Read the heartbeat log:
```
read .devin/heartbeats/log.jsonl
```

Or tail it:
```
exec: tail -20 .devin/heartbeats/log.jsonl
```

### Step 5: Stop the heartbeat

**Windows:**
```powershell
Unregister-ScheduledTask -TaskName "devin-heartbeat" -Confirm:$false
```

**Linux/macOS:**
```bash
crontab -l | grep -v heartbeat | crontab -
```

## Heartbeat via PostToolUse Hook (In-Session)

For periodic checks **within a running session** (not across sessions), use a
PostToolUse hook that checks elapsed time since last heartbeat:

```json
{
  "PostToolUse": [
    {
      "matcher": "exec",
      "hooks": [
        {
          "type": "command",
          "command": "python \"%APPDATA%\\devin\\scripts\\in-session-heartbeat.py\"",
          "timeout": 10
        }
      ]
    }
  ]
}
```

The `in-session-heartbeat.py` script checks if N minutes have passed since
the last heartbeat and, if so, injects a reminder to run the check. This is
not true scheduled re-entry, but it provides periodic nudges within a session.

## Limitations vs PrimeAgent Heartbeats

| Feature | PrimeAgent | Heartbeat (this skill) |
|---|---|---|
| Re-enters existing session | Yes | No (launches new session) |
| `/heartbeat` command | Yes (built-in) | No (OS scheduler + script) |
| `rlm_heartbeat` API | Yes | No |
| `prime-agent schedule` | Yes (cron-like) | Emulated via OS scheduler |
| In-session periodic check | Yes | Via PostToolUse hook (nudge, not re-entry) |
| Cross-session persistence | Yes (daemon) | No (each session is fresh) |

## Anti-Patterns

- **Don't use heartbeats for one-shot checks.** Run the command directly.
- **Don't forget to unregister the scheduler.** Stale cron entries waste resources.
- **Don't make heartbeats too frequent.** Each launch is a new Devin CLI session — costly. 5+ minutes minimum.
- **Don't ignore the log.** Read `log.jsonl` periodically to catch issues.
- **Don't use in-session heartbeats for critical monitoring.** They only fire on tool use, not on idle time.

## Security Considerations (Rule 13)

- The heartbeat script runs with the user's permissions — not sandboxed
- The prompt file is writable by the user — a malicious actor could inject commands
- The OS scheduler entry persists across reboots — review and clean up regularly
- Don't put secrets in the heartbeat config — use env vars or `.devin/config.local.json`

## Evidence Summary

| Claim | Source | Status |
|---|---|---|
| PrimeAgent `/heartbeat` re-enters session periodically | PrimeAgent blog | Verified |
| `rlm_heartbeat` API for programmatic heartbeats | PrimeAgent blog | Verified |
| `prime-agent schedule` for scheduled re-entry | PrimeAgent blog | Verified |
| Devin CLI hooks fire on lifecycle events, not time | Devin CLI docs (self-extend skill) | Verified |
| OS schedulers can launch CLI sessions | Standard OS feature | N/A (adaptation) |
