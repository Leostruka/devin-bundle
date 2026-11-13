# Hook event flow

Stdin JSON payload to merged stdout decision, per lifecycle event. Entry
points are the 10 commands wired in `hooks.v1.json`; inner scripts run
in-process through `scripts/_hookrun.py`. Merge rules: first `block`
wins (exit 2), `additionalContext` concatenates, `updatedInput`
shallow-merges, an inner-script crash is fail-open. `fail_closed` on the
entry covers failure of the entry point itself (PreToolUse only).

```mermaid
flowchart TD
    CLI[Devin CLI lifecycle event] --> PAY[stdin JSON payload<br/>session_id, prompt_id, tool_name, tool_input]

    subgraph PRE[PreToolUse - fail_closed]
        PAY --> M1{matcher}
        M1 -->|exec| PEG[pre-exec-guard.py<br/>timeout 300s]
        M1 -->|write edit notebook_edit| PWG[pre-write-guard.py<br/>timeout 90s]
        PEG --> HR1[_hookrun fan-out]
        PWG --> HR2[_hookrun fan-out<br/>+TEXT_ONLY when write or edit]
    end

    subgraph POST[PostToolUse]
        PAY --> M2{matcher}
        M2 -->|exec mcp_call_tool| PX[post-exec.py 30s]
        M2 -->|write edit| MPE[memory-post-edit.py 10s]
        M2 -->|write edit| CG[compact-gate.py 15s]
    end

    subgraph LIFE[Session lifecycle]
        PAY --> UPS[user-prompt.py 20s<br/>UserPromptSubmit]
        PAY --> SS[session-start.py 10s<br/>SessionStart]
        PAY --> ST[stop-guard.py 25s<br/>Stop]
        PAY --> SE[memory-stop.py 5s<br/>SessionEnd]
        PAY --> CP[constraint-pinning.py 5s<br/>PostCompaction]
    end

    HR1 --> MRG{decision merge}
    HR2 --> MRG
    PX --> MRG
    MPE --> MRG
    UPS --> MRG
    SS --> MRG
    ST --> MRG

    MRG -->|any block| BLK[stdout decision block<br/>exit 2]
    MRG -->|context only| CTX[stdout hookSpecificOutput<br/>additionalContext, updatedInput<br/>exit 0]
    MRG -->|no output| OK[exit 0]

    CRASH[inner script exception] -.->|fail-open, stderr log| MRG
    FAIL[entry point failure] -.->|fail_closed: block| BLK
```

Inner-script lists per entry point live in `.devin/docs/TOOLS-MAP.md`
(hook table) and `.devin/docs/HOOKS-PIPELINE.md` (merge contract).
