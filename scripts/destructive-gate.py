#!/usr/bin/env python3
"""PreToolUse hook: blocks destructive commands that are irreversible or high-risk.

Fires on exec and write_to_process (C90-C91). write_to_process is a
laundered exec channel: its text reaches a live shell's stdin, so only
CR/LF-terminated lines (actually submitted) are scanned. _hookrun
normalizes wtp payloads - injects the submitted lines as
tool_input.command so every runner child sees real commands; the local
extraction below is the direct-invocation fallback. Pending input-line
text is buffered per shell (state/wtp-*.txt) so text and its CR arriving
in separate calls still gate (split-write bypass).

Stdin payload (per Devin CLI docs /cli/extensibility/hooks/lifecycle-hooks):
  {"hook_event_name": "PreToolUse", "tool_name": "exec",
   "tool_input": {"command": "..."}, "session_id": "...", "prompt_id": "..."}

Exit codes (per Devin CLI docs /cli/extensibility/hooks/overview#exit-codes):
  0 = success, hook continues normally
  2 = block, action is denied
  other = error, logged but doesn't block

Gates (deterministic, read-only, fail-open):
  1. rm -rf (and Windows Remove-Item -Recurse -Force / rd /s) with dangerous
     paths (/, ~, *, . alone, parent, system dirs, drive roots)
  2. git push --force / -f without --dry-run
  3. git reset --hard (warn only, sometimes legitimate)
  4. DROP TABLE / DROP DATABASE / TRUNCATE in SQL
  5. chmod -R 777 on root or home
  6. git clean -fdx (removes untracked + ignored files, irreversible)
  7. git branch -D (force delete branch; allowed when `git cherry` proves
     every commit patch-equivalent in HEAD - squash/rebase-merge safe)
  8. mkfs / wipefs / blkdiscard / dd to disk devices (filesystem wipe)
  9. Windows reserved device basename (nul/con/aux/prn/com1-9/lpt1-9, any
     ext) used as redirect target or tee/touch/mkdir/cp/mv/ln/install arg,
     outside a cmd/powershell/pwsh wrapper - bash has no device mapping:
     creates literal ghost artifacts or silently discards output
 10. NTFS ADS: ':' in a redirect/verb target basename (Windows-scoped)

Warn-path advisories (stderr, never block):
  - bulk worktree discard: git checkout/restore '.' , stash drop/clear,
    forced switch/remove (checkout|switch -f, --force, --discard-changes,
    worktree remove --force, reset --merge)
  - recovery-net destroyers + Gate-7 bypass: reflog expire --expire now,
    gc --prune=now, update-ref -d, vssadmin delete shadows, wbadmin
    delete, bcdedit /delete, netsh * reset, reg delete HKLM
  - secure-erase tools: shred, sdelete, cipher /w, Clear-RecycleBin
  - session killers: shutdown/reboot/halt/poweroff/logoff/
    Restart-Computer/init 0|6/systemctl poweroff/killall/kill -9 -1
  - protection/evidence destroyers: Defender disable|exclusion,
    advfirewall state off, Set-ExecutionPolicy Unrestricted|Bypass,
    event-log/audit-policy/USN-journal clears
  - permission wipe: icacls/cacls recursive Everyone:F (chmod -R 777)
  - infra destroyers: docker prune -v/compose down -v, terraform destroy,
    kubectl delete ns/pvc/pv/workload/secret, helm uninstall,
    vagrant destroy, cloud deletes (aws s3 rm -r/ec2 terminate/cfn
    stack/rds/ecs, az vm/aks/storage/webapp, gcloud instances/
    clusters/sql/storage/functions, doctl * delete), rclone
    delete|purge, gsutil rm, git push --delete/':ref', gh repo
    delete, gh api -X DELETE
  - publish/deploy: package pushes (npm|pnpm|yarn, twine, cargo, gem,
    nuget, poetry), docker/helm push, --prod deploys (vercel/netlify/
    firebase/fly/serverless/sam/cdk/wrangler)
  - remote-code fetch-pipe: curl|wget|iwr|irm piped/chained into a shell
    or interpreter, iex (iwr ...) cradle
  - SQL data wipes: WHERE-less DELETE, ALTER TABLE ... DROP (Gate 4 also
    blocks DROP USER|ROLE|INDEX|VIEW|... + FLUSHALL/FLUSHDB/
    dropDatabase/db.x.drop on psql/mysql/sqlite/mongo/redis clients)

Source: "Reason Less, Verify More" (arXiv:2607.07405, KDD 2026 Workshop)
  4-gate suite raised success 29.6%->42.0% (+12.4pp, P=0.0012, replicated P=0.0008)
  78% of failures are silent wrong-state with no tool error.
  Gates are deterministic, read-only, pre-execution predicates.
  Fail-open: if a gate raises an exception, log and allow.
"""
import sys, json, os, re, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _hookrun

# Whitelisted path prefixes for rm -rf (build/cache dirs safe to remove)
RM_RF_WHITELIST = (
    "build", "dist", "node_modules", "__pycache__", ".pytest_cache",
    "target", "bin", "obj", ".gradle", ".m2", "coverage",
    ".next", ".nuxt", ".cache", "tmp", "temp", ".venv", "venv",
)

# rm with recursive+force flags, capturing the target list
RM_RF_RE = re.compile(r"\brm\s+(?:-[a-zA-Z]*\s+)*(?:-[a-zA-Z]*r[a-zA-Z]*f[a-zA-Z]*|-[a-zA-Z]*f[a-zA-Z]*r[a-zA-Z]*|--recursive\s+--force|--force\s+--recursive)\s+(.+)")

# Explicitly dangerous rm targets (POSIX + Windows drive roots)
RM_DANGEROUS_TARGETS = {
    "/", "~", "$HOME", "*", ".", "..", "/*", "~/*", "./*",
    "C:", "C:\\", "C:/", "D:", "D:\\", "D:/", "*.*",
}

# git global flags interposed between `git` and the verb (-C dir, -c k=v,
# -P, --no-pager, --git-dir[= ]x, --work-tree[= ]x, --exec-path[= ]x) —
# without this, `git -C repo push -f` bypasses every git gate.
_GIT_FLAGS = (r"(?:\s+(?:-[a-zA-Z](?:\s+\S+)??|--[\w-]+(?:=\S+|\s+\S+)??))*")
# Windows resolves git.exe/git.cmd/git.bat too - without the suffix arm
# `git.exe push --force` bypasses every git gate below (probe 2026-11-24).
_GIT = r"\bgit(?:\.(?:exe|cmd|bat|com))?\b" + _GIT_FLAGS

# git push --force without --dry-run.
# Negative lookahead on -f avoids matching --follow-tags.
# --force-with-lease is intentionally EXCLUDED: it is the recommended safe
# alternative to --force (fails if remote has new commits). Blocking it would
# encourage users to use the more dangerous --force instead.
GIT_FORCE_PUSH = re.compile(_GIT + r"\s+push\b[^|;&]*?(?:\s-f\b|\s-[a-zA-Z]*f[a-zA-Z]*\b|\s--force\b(?!-with-lease))")
GIT_DRY_RUN = re.compile(r"(?:\s--dry-run(?![\w-])|\s-n(?![\w-]))")

GIT_RESET_HARD = re.compile(_GIT + r"\s+reset\s+--hard\b")

# Bulk worktree discard: checkout/restore of "." discards EVERY uncommitted
# change in one shot (2026-11-24 incident: `git checkout -- .` reverted a
# full session of uncommitted gate fixes - recovery needed live copies).
# Warn-path like reset --hard; file-level `checkout -- f` stays silent.
GIT_BULK_DISCARD = re.compile(
    _GIT + r"\s+(?:checkout|restore)\b[^|;&]*?(?:\s--\s*\.|\s\.(?:[/\\]|\s|$))"
)
# Force-switch discards uncommitted changes silently: checkout/switch -f,
# --force, --discard-changes; worktree remove --force kills a worktree with
# its changes; reset --merge drops local modifications.
GIT_FORCE_SWITCH = re.compile(
    _GIT + r"\s+(?:(?:checkout|switch)\b[^|;&]*?(?:\s-f\b|"
    r"\s--force\b|\s--discard-changes\b)|worktree\s+remove\b[^|;&]*"
    r"(?:\s-f\b|\s--force\b)|reset\s+--merge\b)"
)
GIT_STASH_DROP = re.compile(_GIT + r"\s+stash\s+(?:drop|clear)\b")
# Recovery-net destroyers + Gate-7 bypasses: reflog expire erases the only
# rollback for orphaned commits; gc --prune=now drops unreachable objects
# immediately; update-ref -d deletes refs without the branch -D gate.
GIT_RECOVERY_KILL = re.compile(
    _GIT + r"\s+(?:reflog\s+expire\b[^|;&]*--expire(?:=|\s)now|"
    r"gc\b[^|;&]*--prune(?:=|\s)now|update-ref\s+-d\b)|"
    r"\b(?:vssadmin\s+delete\s+shadows|wbadmin\s+delete|"
    r"bcdedit\b[^|;&]*/delete|netsh\b[^|;&]*\breset\b|"
    r"reg\s+delete\s+(?:\\\\[^ |;&]+\\)?HKLM|"
    r"crontab\s+-r\b|schtasks\s+/delete\b[^|;&]*/tn\s+\*|"
    r"Unregister-ScheduledTask\b|certutil\s+-delstore\b|"
    r"net\s+user\s+(?:[^\s|;&`'\"$(\n]|'[^'\n]*'|\"[^\"\n]*\")+\s+"
    r"/delete\b|Remove-LocalUser\b)")

SQL_DESTRUCTIVE = re.compile(
    r"\b(?:DROP\s+(?:TABLE|DATABASE|SCHEMA|USER|ROLE|INDEX|VIEW|"
    r"PROCEDURE|FUNCTION|TRIGGER|SEQUENCE|EXTENSION)\b|"
    r"TRUNCATE\s+TABLE\b|FLUSHALL|FLUSHDB|dropDatabase\s*\(|"
    r"db\.\w+\.drop\s*\()",
    re.IGNORECASE,
)

# Lower-tier data destruction (warn): WHERE-less DELETE wipes every row;
# ALTER ... DROP destroys schema+data but is routine in migrations.
SQL_WARN = re.compile(
    r"\bDELETE\s+FROM\s+[\"'`\w.]+\s*[\"'`;]?\s*(?:$|[|;&])|"
    r"\bALTER\s+TABLE\s+(?:[^\s|;&`'\"$(\n]|'[^'\n]*'|\"[^\"\n]*\")+\s+DROP\b",
    re.IGNORECASE,
)

# SQL client binaries — the destructive SQL gate only fires when one of these
# is in the command, so that echo/grep/cat/git-commit text mentioning the
# keywords is not falsely blocked.
SQL_CLIENTS = re.compile(
    r"\b(?:psql|mysql|sqlite3?|sqlcmd|cockroach(?:-sql)?|db2|sqlplus|"
    r"pgcli|mycli|litecli|usql|sqlshell|mongo(?:sh)?|redis-cli|"
    r"valkey-cli)\b",
    re.IGNORECASE,
)

CHMOD_DANGEROUS = re.compile(r"\bchmod\s+(?:(?:-[a-zA-Z]*R[a-zA-Z]*|--recursive)\s+)777\s+(?:/|~|\$HOME)(?:\s|$)")

# Windows recursive-delete equivalents: Remove-Item -Recurse -Force, rd /s /q,
# del /s /q, rmdir /s. These are the Windows counterparts to rm -rf.
# Pattern 1: flags before target (Remove-Item -Recurse -Force C:\)
WIN_RM_RE = re.compile(
    r"\b(?:Remove-Item|del|erase|rmdir|rd|ri|rm)\b"
    r"(?:\s+-[a-zA-Z]+)*\s+"
    r"(?:(?:-[a-zA-Z]*[rR][a-zA-Z]*[fF][a-zA-Z]*|-[a-zA-Z]*[fF][a-zA-Z]*[rR][a-zA-Z]*|--Recurse\s+--Force|--Force\s+--Recurse|-Recurse\s+-Force|-Force\s+-Recurse|/s\s*/q|/s)\s+)"
    r"(.+)",
    re.IGNORECASE,
)
# Pattern 2: target before flags (Remove-Item C:\ -Recurse -Force) — PowerShell
# allows parameters in any order. The path must NOT start with '-' (a flag).
WIN_RM_RE_PATH_FIRST = re.compile(
    r"\b(?:Remove-Item|del|erase|rmdir|rd|ri|rm)\b"
    r"(?:\s+(?:-[a-zA-Z]+))*\s+"  # optional leading flags
    r"([^-]\S*)"  # the target path (must not start with '-')
    r"(?:\s+(?:-[a-zA-Z]*[rR][a-zA-Z]*[fF][a-zA-Z]*|-[a-zA-Z]*[fF][a-zA-Z]*[rR][a-zA-Z]*|--Recurse\s+--Force|--Force\s+--Recurse|-Recurse\s+-Force|-Force\s+-Recurse|/s\s*/q|/s)\b)",
    re.IGNORECASE,
)
# Pattern 3: recursive-force flags with NO target (malformed, like POSIX rm -rf
# with no target — treated as dangerous by check_rm_rf).
WIN_RM_RE_NOTARGET = re.compile(
    r"\b(?:Remove-Item|del|erase|rmdir|rd|ri|rm)\b"
    r"(?:\s+-[a-zA-Z]+)*\s+"
    r"(?:-[a-zA-Z]*[rR][a-zA-Z]*[fF][a-zA-Z]*|-[a-zA-Z]*[fF][a-zA-Z]*[rR][a-zA-Z]*|--Recurse\s+--Force|--Force\s+--Recurse|-Recurse\s+-Force|-Force\s+-Recurse|/s\s*/q|/s)"
    r"(?:\s+(?:-[a-zA-Z]+))*\s*$",
    re.IGNORECASE,
)

# Deleting or corrupting subagent enforcement state (profile records,
# dispatch ledger, budget policy) resets the session's own limits -
# self-unlimiting class. Anchored on the state/ path component (matches
# <devin-home>/state/subagent-*; bare "subagent-x.json" elsewhere is fine)
# or the whole state dir itself (devin/state -> rm -rf state-dir).
# A state-file target: exact names AND glob forms (rm state/wtp-*.txt
# wipes every pending-line buffer; wtp-* without an extension is the
# same wipe). Glob metachars live in the name class; the terminator
# lookahead replaces \b (a trailing * is not a word char).
_STATE_FILE_NAME = (r"(?:subagent-[\w.*?{}\[\],-]*(?:\.jsonl?)?|"
                    r"wtp-[\w.*?{}\[\],-]*(?:\.txt)?|"
                    # Any name carrying glob metachars under state/ can
                    # resolve to an enforcement file (?tp-*, [s]ubagent,
                    # {a,b}, bare *). state/ contents are all gated
                    # files - no glob in there is innocent.
                    r"[\w.*?{}\[\],+~-]*[*?{\[][\w.*?{}\[\],+~.-]*)")
# Left boundary is a lookbehind (not consumed): `>`/`=`/`:` stay with the
# operator (`>state/x`, `of=state/x`, `h:state/x`) while still bounding
# the state component. `[^\s\\/>=:]` = "no non-boundary char before".
# File-level targets keep the broad boundary: `x/state/subagent-*.json`
# carries an enforcement-specific basename wherever `state` sits - a
# DEVIN_STATE_DIR may point anywhere.
_STATE_PATH = (r"(?<![^\s\\/>=:])state[\\/]+" + _STATE_FILE_NAME +
               r"(?=[\s|;&'\"\n]|$)")
# Bare-dir targets anchor tighter: a `state` segment counts at path root
# (`./`/`../`/`seg/../` prefixes resolve to it) or under a `devin`
# segment (the enforcement dir lives under the devin home wherever that
# is). `src/state`/`dist/state` are project dirs (Redux-style) - a
# mid-path `state` after an ordinary segment does not anchor.
_STATE_PRE = (
    r"(?:(?<![^\s>=:'\"])(?:(?:\.{1,2}|[^\s\\/>=:]+[\\/]+\.\.)[\\/]+)*"
    r"|(?:(?<![^\s>=:'\"])|(?<=[\\/]))"
    r"(?:[^\s|;&>=:\\/]+[\\/])*(?<![\w-])devin[\\/]+)")
_STATE_DIR = (_STATE_PRE + r"state"
              # Win32 strips trailing dots: `rm -rf state.` deletes `state`.
              r"\.{0,3}(?=[/\\'\"\s|;&\n]|$)")
# `cd ...state && rm wtp-x.txt` - a bare state-basename target after a
# cd/pushd into a state dir carries no `state/` component in the operand.
# Self-contained arm: the separator class includes newlines (wtp joins
# submitted lines with \n), the dir tolerates quotes/trailing slash and
# a redirect after it, and a shell -c/-Command wrapper may precede the
# verb. `cd state\nrm wtp-x` is the natural two-line wtp flow.
# Wrappers that may precede cd or the verb: env/nice/sudo/xargs exec the
# following verb directly (`cd state && env rm x`); bash/sh/cmd need a
# -c//c flag, powershell/pwsh take a bare command (Remove-Item ...).
_STATE_WRAP = (r"(?:[({!`]+\s*|\$\(\s*)*"
               # Env-assignment (`A=1 rm`) and redirect (`> f rm`)
               # prefixes precede the verb without executing it.
               r"(?:[\w.]+=(?:[^\s|;&`'\"$(\n]|'[^'\n]*'|\"[^\"\n]*\")*\s+|"
               r">>?\s*(?:[^\s|;&`'\"$(\n]|'[^'\n]*'|\"[^\"\n]*\")+\s+)*"
               r"(?:(?:env|nice|nohup|sudo|doas|runas|timeout|xargs|"
               r"watch|stdbuf|ionice|taskset|chrt|command|builtin|exec|"
               r"noglob|time|busybox|eval|strace|ltrace|setsid|pkexec|"
               r"detach|flock|unshare|nsenter|chroot|while|until|for|"
               r"do|then|elif|else|if|case)\s+"
               r"(?:(?:[^\s|;&`'\"$(\n]|'[^'\n]*'|\"[^\"\n]*\")+\s+)*)?"
               r"(?:(?:powershell|pwsh)\s+|"
               r"(?:bash|sh|dash|zsh|cmd)\b[^|;&\n]*?"
               r"(?:-c|/c|-Command)\s+[\"']?)?")
_STATE_CD = (r"(?:^|[|;&`$(\n]|\s)" + _STATE_WRAP +
             r"(?:cd|chdir|pushd|Set-Location|sl)\s+"
             r"[\"']?[^|;&\n\"']*?(?<![\w.-])state\.{0,3}"
             r"(?=[/\\'\"\s|;&\n]|$)[/\\]?[\"']?"
             r"(?:\s*>>?\s*[^\s|;&\n]+)?\s*[|;&\n]+\s*" + _STATE_WRAP)
# Two-hop form: `cd devin && rm -rf state` - cd into the devin home then
# hit the bare state dir. Same quoting/separator tolerances as _STATE_CD.
_DEVIN_CD = (r"(?:^|[|;&`$(\n]|\s)" + _STATE_WRAP +
             r"(?:cd|chdir|pushd|Set-Location|sl)\s+"
             r"[\"']?[^|;&\n\"']*?(?<![\w.-])devin"
             r"(?=[/\\'\"\s|;&\n]|$)[/\\]?[\"']?"
             r"(?:\s*>>?\s*[^\s|;&\n]+)?\s*[|;&\n]+\s*" + _STATE_WRAP +
             r"(?:(?:rm|del|erase|ri|rd|rmdir|Remove-Item|Rename-Item|"
             r"ren\b|unlink|shred|srm|wipe|mv|move|Move-Item|"
             r"find\b[^|;&\n]*?-delete)\b[^|;&\n]*?(?<![\w.-])state"
             r"(?=[/\\'\"\s|;&\n]|$)"
             # `cd devin && find . -delete` / `... | xargs rm` - the
             # whole-dir wipe needs no `state` operand to hit it.
             r"|find\b[^|;&\n]*-delete\b|[^|;&\n]*\|\s*(?:xargs\s+)*"
             r"(?:rm|del|erase|ri|rd|rmdir|Remove-Item|unlink|shred|srm|"
             r"wipe)\b)")
_STATE_NAME = (r"[\"']?(?:\.[/\\])?" + _STATE_FILE_NAME +
               r"(?=[\s|;&'\"\n)`]|$)")
# After `cd state`, extra segments may precede the verb
# (`cd state && sl . && rm x`, `cd state && for f in y; do rm $f`) -
# each tolerates any single-segment command then re-anchors the verb.
_CD_SEGS = r"(?:[^|;&\n]*?[|;&\n]+\s*" + _STATE_WRAP + r")*"
# A command substitution inside a delete-verb's operand resolves at
# run time - `rm -rf sta$(echo te)` targets `state` while the scan sees
# only `sta$(`. Same uninspectable-transport class as ENCODED_EXEC: the
# operand text the gate needs is produced by code it cannot read.
_STATE_SUBST_TARGET = re.compile(
    r"(?:^|[|;&\n])\s*(?:rm|del|erase|ri|rd|rmdir|Remove-Item|"
    r"Rename-Item|ren|unlink|shred|srm|wipe|mv|move|Move-Item|"
    r"find|xargs)\b[^|;&\n]*?(?:\$\(|`)",
    re.IGNORECASE)
_STATE_TARGET = _STATE_PATH + "|" + _STATE_DIR
# Command-position anchor: a verb only runs at command start, after a
# separator/command-substitution, under a privilege wrapper, or inside a
# shell -c/-Command quote - mid-string occurrences are prose
# (`echo "rm state/x"` stays silent; `bash -c 'rm state/x'` still hits).
_CMD_POS = (r"(?:^|[|;&`$(]|\b(?:sudo|doas|runas|xargs|env|nice|nohup|"
            r"timeout|ionice|watch|stdbuf|strace|ltrace|taskset|chrt)\s+"
            r"(?:(?:[^\s|;&`'\"$(\n]|'[^'\n]*'|\"[^\"\n]*\")+\s+)*|"
            r"(?:-[ckCK]|-Command|/[ckCK]|eval)\s*[\"'`])\s*")
_STATE_FILE_DELETE_PATTERN = (
    r"(?:" + _CMD_POS +
    r"(?:rm|del|erase|ri|rd|rmdir|Remove-Item|Rename-Item|ren\b|"
    r"unlink|shred|srm|wipe|mv|move|Move-Item)\b[^|;&]*?)"
    r"(?:" + _STATE_TARGET + ")"
    r"|\bFile\]::(?:Delete|Move|Replace)\w*\s*\([^)]*?"
    r"(?:['\"]?state[\\/]+" + _STATE_FILE_NAME + "|" + _STATE_DIR + ")"
    r"|" + _CMD_POS + r"find\b[^|;&]*?(?:" + _STATE_TARGET + ")"
    r"[^|;&]*?(?:-delete\b|-exec(?:dir)?\s+\S)"
    # Any producer mentioning a state path piped into a delete verb:
    # `find state | xargs rm`, `echo state/x | xargs rm` - the operands
    # ride the pipe, invisible to the verb's arg list.
    r"|" + _CMD_POS + r"[^|;&]*?(?:" + _STATE_TARGET + ")"
    r"[^|;&]*\|\s*(?:xargs\s+)*(?:rm|del|erase|ri|rd|rmdir|Remove-Item|"
    r"Rename-Item|ren|unlink|shred|srm|wipe|mv|move|Move-Item)\b"
    r"|" + _STATE_CD + _CD_SEGS +
    r"(?:rm|del|erase|ri|rd|rmdir|Remove-Item|Rename-Item|ren\b|"
    r"unlink|shred|srm|wipe|mv|move|Move-Item)\b[^|;&\n]*?" + _STATE_NAME +
    r"|" + _STATE_CD + _CD_SEGS + r"find\b[^|;&\n]*?-delete\b"
    # `cd state && ls | xargs rm` - piped operands hit state files with
    # no literal name in the rm arg list at all.
    r"|" + _STATE_CD + _CD_SEGS + r"[^|;&\n]*\|\s*(?:xargs\s+)*"
    r"(?:rm|del|erase|ri|rd|rmdir|Remove-Item|Rename-Item|ren|unlink|"
    r"shred|srm|wipe|mv|move|Move-Item)\b"
    # `cd state && for f in wtp-x; do rm $f; done` - loop-var/subst
    # operands resolve at run time, invisible to the name scan.
    r"|" + _STATE_CD + _CD_SEGS +
    r"(?:rm|del|erase|ri|rd|rmdir|Remove-Item|Rename-Item|ren\b|"
    r"unlink|shred|srm|wipe|mv|move|Move-Item)\b[^|;&\n]*?[$`]"
    r"|" + _DEVIN_CD
)
# Writes are as dangerous as deletes: `>` truncates (json.load fails ->
# uncapped fail-open), `>>`/append poisons ts fields, tee/truncate/sed -i/
# dd of=/rsync --delete replace content. cp/install write the state path
# only when it is the DESTINATION (last operand) - `cp state/x /tmp/bak`
# reads state and stays allowed.
_STATE_FILE_WRITE_PATTERN = (
    r"(?:>>?\s*[\"']?[^|;&]*?|" + _CMD_POS +
    r"(?:tee|truncate|Out-File|Set-Content|Add-Content|Clear-Content|"
    r"sc\b|Set-ItemProperty|sed\b[^|;&]*-i|"
    r"dd\b[^|;&]*of=)(?:\b|(?<==))[^|;&]*?)(?:" + _STATE_TARGET + ")"
    r"|\bFile\]::(?:Write|Append|Create|Copy|Move|Replace)\w*\s*\([^)]*?"
    r"(?:['\"]?state[\\/]+" + _STATE_FILE_NAME + "|" + _STATE_DIR + ")"
    r"|" + _CMD_POS + r"(?:cp|copy|Copy-Item|rsync|install)\b[^|;&]*?"
    r"(?:" + _STATE_TARGET + r")[\\/'\"]*\s*(?:$|[|;&])"
    r"|" + _STATE_CD + _CD_SEGS +
    r"(?:tee|truncate|Out-File|Set-Content|Add-Content|Clear-Content|sc\b|"
    r"sed\b[^|;&]*-i|dd\b[^|;&]*of=|cp|copy|Copy-Item)\b[^|;&]*?" +
    _STATE_NAME +
    r"|" + _STATE_CD + _CD_SEGS + r"[^|;&]*?>>?\s*" + _STATE_NAME +
    # Tools whose path operand is flag-shaped: curl -o, wget -O,
    # iwr -OutFile, gcc/javac/rustc -o/-d, tar -cf/-C, unzip -d,
    # pandoc -o, certutil -encode/-decode <out>, ffmpeg output.
    r"|" + _CMD_POS +
    r"(?:curl|wget|iwr|Invoke-WebRequest|Invoke-RestMethod|"
    r"gcc|g\+\+|clang|cc|ld|objcopy|javac|rustc|go|pandoc|"
    r"pg_dump|certutil|msbuild|cl\b|link|lib|fsutil|tar|unzip)"
    r"\b[^|;&]*?"
    r"(?:-o\b|-O\b|-d\b|-c\w*|-C\s|--output(?:-document|-file)?[\s=]|"
    r"-OutFile\b|--directory\b|--destdir[\s=]|--prefix[\s=]|"
    r"-Path\b|seteof\b)[^|;&]*?(?:" + _STATE_TARGET + r")" +
    # Positional last-arg destinations: scp/rsync/install/gzip-family/
    # New-Item/bitsadmin/ffmpeg - the state path must sit at the END
    # (source-position reads stay allowed). tar/unzip/zip/7z keep out:
    # their state-named operand is the SOURCE archive, not a write.
    r"|" + _CMD_POS +
    r"(?:scp|install|rsync|gzip|gunzip|bzip2|bunzip2|xz|unxz|"
    r"New-Item|bitsadmin|ffmpeg)\b"
    r"[^|;&]*?(?:" + _STATE_TARGET + r")"
    r"(?:[\\/][^\s\\/|;&]*)*(?:\s+-[\w:]+)*\s*(?:$|[|;&])" +
    # robocopy /MIR wipes extras in the DEST dir - a state dir named
    # anywhere in the args with /mir present is a mirror into it.
    r"|\brobocopy\b(?=[^|;&]*/mir\b)[^|;&]*?(?:" + _STATE_TARGET + r")"
    # zip's output archive is the FIRST operand: `zip state/x files`.
    r"|\bzip\b\s*(?:-\S+\s+)*(?:" + _STATE_TARGET + r")"
)

_STATE_FILE_DELETE_RE = None
_STATE_FILE_WRITE_RE = None


def _state_file_patterns():
    global _STATE_FILE_DELETE_RE, _STATE_FILE_WRITE_RE
    if _STATE_FILE_DELETE_RE is None:
        _STATE_FILE_DELETE_RE = re.compile(
            _STATE_FILE_DELETE_PATTERN, re.IGNORECASE)
    if _STATE_FILE_WRITE_RE is None:
        _STATE_FILE_WRITE_RE = re.compile(
            _STATE_FILE_WRITE_PATTERN, re.IGNORECASE)
    return _STATE_FILE_DELETE_RE, _STATE_FILE_WRITE_RE


def _state_file_targeted(command):
    lowered = command.lower()
    if "state" not in lowered and "devin" not in lowered:
        return False
    delete_re, write_re = _state_file_patterns()
    return bool(delete_re.search(command) or write_re.search(command))


# git clean -fdx: removes untracked AND ignored files (irreversible, no reflog)
# Excludes -n (dry-run) — if -n is present, it's a preview, not a destructive op.
# Matches combined flags (-fdx, -xfd) and --force with separate -d/-x flags.
GIT_CLEAN_FORCE = re.compile(_GIT + r"\s+clean\s+(?:-[a-zA-Z]*[fF][a-zA-Z]*[dDxX][a-zA-Z]*|-[a-zA-Z]*[dDxX][a-zA-Z]*[fF][a-zA-Z]*|--force\b(?:\s+-[a-zA-Z]+)*\s+-[a-zA-Z]*[dDxX]|-f\b(?:\s+-[a-zA-Z]+)*\s+-[a-zA-Z]*[dDxX])")
GIT_CLEAN_DRY_RUN = re.compile(
    _GIT + r"\s+clean\b[^|;&]*?(?:-[a-zA-Z]*n[a-zA-Z]*\b|--dry-run\b)")

# git branch -D: force-delete branch (loses unmerged commits). Other flags
# may sit between `branch` and the delete flag (`branch -d -D x`,
# `branch --list -D x`), so the prefix allows flag tokens; [^|;&] capture
# stops at command separators so finditer sees each -D in a chain.
GIT_BRANCH_FORCE_DELETE = re.compile(
    _GIT + r"\s+branch\s+(?:(?:-[a-zA-Z][\w-]*|--[\w-]+(?:=\S*)?)"
    r"(?:\s+\S+)?\s+)*"
    r"(?:-[a-zA-Z]*D[a-zA-Z]*\b|--delete\s+--force\b)\s*([^|;&]*)")

# git branch flags that consume the following token as a value (rename
# target, sort key, upstream, filter ref) - their operand is not a branch
# to delete.
_BRANCH_VALUE_FLAGS = frozenset({
    "-m", "-M", "-c", "-C", "-u", "-t",
    "--set-upstream-to", "--sort", "--format", "--points-at",
    "--merged", "--no-merged", "--contains", "--no-contains",
    "--column", "--color", "--abbrev", "--edit-description",
})

# git config writes and `git -c k=v`/`--config-env` inline config:
# exec-capable keys turn a benign git op into code execution - the
# command text still reads `git status` while core.hooksPath / alias.* /
# credential.helper / filter.*.clean / mergetool.*.cmd etc. exec on the
# op itself or every later git call. Reads/removals (`config key`,
# `--get`, `--unset`, `--list`, `-e`) stay allowed - only a WRITE of a
# denied key blocks.
_GIT_SEG = re.compile(
    # `git` must sit at command position - `echo "git config x y"` /
    # `man git-config` are prose, not invocations. Wrappers that exec
    # the next word keep it reachable (xargs feeds config operands via
    # stdin; loops/env-assign do the same).
    r"(?:^|[|;&`$(\n])\s*"
    r"(?:[\w.]+=(?:[^\s|;&`'\"$(\n]|'[^'\n]*'|\"[^\"\n]*\")*\s+)*"
    r"(?:(?:sudo|doas|env|nice|nohup|xargs|command|builtin|exec|eval|"
    r"time|noglob|strace|ltrace|setsid|pkexec|watch|stdbuf|ionice|"
    r"taskset|chrt|while|until|for|if|then|do|elif|else)\s+"
    r"(?:(?:[^\s|;&`'\"$(\n]|'[^'\n]*'|\"[^\"\n]*\")+\s+)*)*"
    # Path-qualified binary: `/usr/bin/git`, `C:\tools\git.exe`,
    # `./git` - any dir prefix ending in a separator before `git`.
    r"(?:[^\s|;&`'\"$(\n]*[\\/])*"
    r"git(?:\.(?:exe|cmd|bat|com))?(?=\s)[^|;&\n]*")
_GIT_CFG_INLINE = re.compile(
    r"(?:^|\s)(?:-c|--config-env)(?:\s+|=)[\"']?([\w.+-]+)\s*=")
_GIT_CFG_DENY_EXACT = frozenset({
    "core.hookspath", "core.fsmonitor", "core.sshcommand",
    "core.pager", "core.editor", "core.gitproxy", "core.askpass",
    "diff.external", "init.templatedir", "safe.directory",
    "man.viewer", "interactive.difffilter", "sendemail.sendmailcmd",
    "http.sslverify", "http.sslcainfo", "http.sslcapath",
    "http.proxy", "https.proxy", "ssh.variant", "web.browser",
    "instaweb.httpd", "instaweb.modulepath",
})
_GIT_CFG_DENY_PREFIX = (
    "alias.", "include.", "includeif.", "pager.",
    "browser.", "web.", "gpg.ssh.", "extcmd.")
# Program/exec suffixes across tool namespaces (mergetool.*.cmd,
# filter.*.clean/smudge/process, gpg.*.program, tar.*.command,
# protocol.*.allow, merge.*.driver, remote-free .url kept out -
# remote.*.url writes are benign and common).
_GIT_CFG_DENIED_KEY = re.compile(
    r"\.(?:driver|cmd|program|helper|insteadof|pushinsteadof|command|"
    r"clean|smudge|process|required|variant|fsmonitor|askpass|pager|"
    r"editor|hookspath|difffilter|sendmailcmd|viewer|external|allow)$|"
    r"^submodule\..*\.(?:update|url|path)$")
# Mode flags that make `git config` a read - not a write.
# rename-section/remove-section WRITE config (remove can strip protective
# keys like core.hooksPath), so they are handled as writes below.
_GIT_CFG_NONWRITE = re.compile(
    r"^--?(?:get.*|list|l$|unset.*|"
    r"edit|e$|show-origin|show-scope|name-only|fixed-value|z$)$")
# Section rewrite ops - every operand is a section/key name.
_GIT_CFG_SECTION_OP = re.compile(r"--?(?:rename-section|remove-section)")
# config flags that consume the following token (never a key/value).
_GIT_CFG_VALFLAGS = frozenset({
    "-f", "--file", "--blob", "--type", "--default", "--value",
    "--get-urlmatch"})


def _git_cfg_denied(key):
    k = key.lower()
    return (k in _GIT_CFG_DENY_EXACT
            or k.startswith(_GIT_CFG_DENY_PREFIX)
            or bool(_GIT_CFG_DENIED_KEY.search(k)))


# git global flags that redirect execution: --exec-path replaces every
# sub-command lookup, and -C/--git-dir/--work-tree aim git at a foreign
# repo whose hooks run on the subcommand (post-checkout, commit-msg...).
_GIT_EXEC_FLAGS = re.compile(
    r"--exec-path(?:\s|=)|(?:-C|--git-dir|--work-tree)(?:\s|=)[^|;&\n]*\b"
    r"(?:commit|checkout|switch|restore|merge|rebase|pull|am\b|"
    r"cherry-pick|revert|worktree\s+add|submodule|stash\b.*\bpop)")


def _git_cfg_danger(command):
    """Return a denied git-config key being SET in the command, or None.
    Covers `git -c k=v`/`--config-env` inline sets and `git config k v`
    writes; reads/removals pass."""
    if _GIT_EXEC_FLAGS.search(command):
        return "<git exec-path/foreign-repo flag>"
    for m in _GIT_SEG.finditer(command):
        seg = m.group(0)
        for im in _GIT_CFG_INLINE.finditer(seg):
            if _git_cfg_denied(im.group(1)):
                return im.group(1)
        cm = re.search(r"\bconfig\b", seg)
        if cm and not _GIT_CFG_NONWRITE.search(seg):
            toks = seg[cm.end():].split()
            pos = []
            skip = False
            for t in toks:
                t = t.strip("'\"")
                if skip:
                    skip = False
                    continue
                if t.startswith("-"):
                    skip = t in _GIT_CFG_VALFLAGS
                    continue
                pos.append(t)
            # Operands assembled at run time are uninspectable: xargs
            # pipes key+value in, read-loops/vars/$()/backtick build the
            # key itself - a denied key can't be matched when the key is
            # dynamic, so the whole write form blocks.
            if pos and re.search(r"[$`]", pos[0]):
                return "<dynamic git-config operand>"
            if not pos and re.search(r"\bxargs\b|\bread\b", seg):
                return "<stdin-fed git config>"
            # rename/remove-section: every operand is a section name, and
            # removing a section can strip protective keys - all checked.
            if _GIT_CFG_SECTION_OP.search(seg):
                if any(_git_cfg_denied(p) for p in pos):
                    return "<git config section op>"
                continue
            if len(pos) >= 2 and _git_cfg_denied(pos[0]):
                return pos[0]
    return None


# mkfs / dd to disk devices (filesystem wipe / raw disk write).
# Device prefixes: sd/hd/vd (virt), xvd (AWS EBS), nvme, mmcblk (SD/eMMC),
# loop, nbd, dm-/mapper (LVM/device-mapper), disk (macOS), plus the Windows
# raw-device path \\.\PhysicalDriveN - all verified real targets 2026-11-24.
DISK_WIPE = re.compile(
    r"\b(?:(?:mkfs(?:\.\w+)?|mke2fs|wipefs|blkdiscard)\s[^|;&]*?"
    r"(?:/dev/|[\\/]+[.][\\/]+PhysicalDrive)"
    r"|dd\s+.*\bof="
    r"(?:/dev/(?:sd|nvme|hd|vd|xvd|mmcblk|loop|nbd|dm-|mapper|disk)"
    r"|[\\/]+[.][\\/]+PhysicalDrive)"
    # Volume/partition destroyers - the target IS the volume, no /dev
    # needed. (lv|vg|pv)remove requires a non-flag operand so `man lvremove`
    # / `lvremove --help` stay silent; `lvremove -f vg/lv` still blocks.
    r"|\b(?:zpool\s+destroy|(?:lv|vg|pv)remove\b[^|;&]*?\s(?![-|;&])\S|"
    r"mdadm\b[^|;&]*--zero-superblock|newfs(?:_\w+)?\b[^|;&]*?\s(?![-|;&])\S|"
    r"diskutil\s+eraseDisk|parted\s+"
    r"(?:[^\s|;&`'\"$(\n]|'[^'\n]*'|\"[^\"\n]*\")+\s+mklabel|"
    r"sgdisk\b[^|;&]*-Z|wsl(?:\.exe)?\s+--unregister))",
    re.IGNORECASE)

# Encoded execution: the gate scans command text, so a payload smuggled
# through a decoder is uninspectable - powershell -e/-ec/-enc/
# -EncodedCommand (PS accepts parameter prefixes), any base64/certutil/
# openssl/xxd decode piped or substituted into a shell/eval, decode-
# wrapping command substitutions inside a sh/eval argument. Canonical
# malware pattern; never legitimate agent work.
ENCODED_EXEC = re.compile(
    r"\b(?:powershell|pwsh)(?:\.exe)?\b[^|;&]*?"
    # PS resolves any unambiguous parameter prefix - every prefix of
    # EncodedCommand (-e/-en/-enc/-enco/-encod/-encode/-encoded/
    # -encodedc/-encodedco/-encodedcom/-encodedcomm/-encodedcomman/
    # -encodedcommand) plus the -ec alias.
    r"\s-(?:e|ec|en|enc|enco|encod|encode|encoded|encodedc|encodedco|"
    r"encodedcom|encodedcomm|encodedcomman|encodedcommand)\b|"
    r"\b(?:base64|certutil|openssl\s+enc|xxd)\b[^|;&]*?"
    r"(?:-d\b|--decode\b|-D\b|-decode\b|-r\b)[^|;&]*?"
    r"\|\s*(?:bash|sh|zsh|dash|ash|ksh|eval|source|python|perl|ruby|node|"
    r"powershell|pwsh|cmd)\b|"
    # `bash -c "$(printf '\x41..')"` - a transform producer inside a
    # command substitution that feeds an interpreter decodes payload
    # bytes the scan never sees as shell words.
    r"\b(?:bash|sh|zsh|dash|ash|ksh|eval|source|cmd)\b[^|;&]*?"
    r"\$\([^)]*?(?:base64\b|certutil\b|openssl\b|xxd\b|printf\b|"
    r"uudecode\b|uudeview\b|echo\s+-[a-zA-Z]*e|rev\b|tr\s)[^)]*?\)|"
    r"\b(?:eval|source)\b\s*[\"'`]?[$<]\([^)]*?"
    r"(?:base64|certutil|openssl|xxd|printf\b[^)]*?\\x)[^)]*?\)|"
    # A transform producer piped into a shell/interpreter launders the
    # payload: printf/echo -e escape bytes, rev/tr rearrange them, the
    # decoders unencode them - the executed text never appears as a
    # shell word. Direct producers (cat/curl/find) pass output through
    # untouched - same exposure class as `sh file`, which the gate
    # already accepts (file contents are outside the scan model).
    r"\b(?:printf|echo\s+-[a-zA-Z]*e|rev|tac|tr\s|fold|dd\b[^|;&]*conv|"
    r"sed\b|awk\b|perl\b|python\d*|php\b|node\b|ruby\b|xxd\b|base64\b|"
    r"openssl\b|certutil\b|uudecode\b|uudeview\b|hexdump\b|od\b|"
    r"(?<![\w.])(?:cmd|bash|sh|zsh|dash|ksh|pwsh|powershell)\b)"
    r"[^|;&]*\|\s*(?:(?:sudo|doas|xargs)\s+)?"
    r"(?:bash|sh|zsh|dash|ash|ksh|csh|tcsh|ssh|cmd|pwsh|powershell)\b|"
    r"\b(?:printf|echo\s+-[a-zA-Z]*e|rev|tr\s|xxd\b|base64\b|openssl\b|"
    r"certutil\b|uudecode\b|uudeview\b)[^|;&]*\|\s*"
    r"(?:python\d*|perl|ruby|php|node|deno)\b"
    r"(?:\s+-[ce]\b|\s+-(?:\s|$)|\s*$|\s*(?=[|;&]))|"
    # `bash <(...)`, `sh <(...)`, `source <(...)` - process substitution
    # feeds produced bytes to the interpreter.
    r"\b(?:bash|sh|zsh|dash|ash|ksh|eval|source)\b[^|;&]*?<[<(]|"
    # `eval $'\x41..'` - ANSI-C $'..' escapes decode inside eval; quote
    # unwrapping may leave the bare backslash form `eval \x41..`.
    r"\b(?:eval|source)\b\s*[\"'`]?(?:\$'|\\x)|"
    # `python -c 'import base64;exec(..)'` etc - inline interpreter decode
    # or exec verbs in the -c/-e payload.
    r"\b(?:python\d*|perl|ruby|node|php|lua|deno)\b[^|;&]*?-[ce]\s*"
    r"(?:\"(?:[^\"\\]|\\.)*?(?:base64|b64|fromhex|unhex|decode|eval\b|"
    r"exec\b|system\(|popen|subprocess|os\.system)(?:[^\"\\]|\\.)*?\"|"
    r"'(?:[^'\\]|\\.)*?(?:base64|b64|fromhex|unhex|decode|eval\b|"
    r"exec\b|system\(|popen|subprocess|os\.system)(?:[^'\\]|\\.)*?'|"
    r"`(?:[^`\\]|\\.)*?(?:base64|b64|fromhex|unhex|decode|eval\b|"
    r"exec\b|system\(|popen|subprocess|os\.system)(?:[^`\\]|\\.)*?`|"
    r"[^\s|;&\"'`]*?(?:base64|b64|fromhex|unhex|decode|eval\b|exec\b|"
    r"system\(|popen|subprocess|os\.system)[^\s|;&\"'`]*)",
    re.IGNORECASE)

# Windows disk wipe: `format X:` quick/full format, `diskpart` interactive,
# PowerShell Format-Volume/Clear-Disk erase a volume/disk without the
# `format X:` shape.
WIN_DISK_WIPE = re.compile(
    r"\bformat\s+[a-zA-Z]:(?=[\s/]|$)|\bdiskpart\b|"
    r"\bFormat-Volume\b|\bClear-Disk\b[^|;&]*?(?:-RemoveData|"
    r"-RemoveOEM|-Force\b)",
    re.IGNORECASE)

# Recoverability killers (warn): cipher /w erases free-space data, sdelete
# and shred bypass every recovery path by design, Clear-RecycleBin destroys
# the bin safety net.
SECURE_ERASE = re.compile(
    r"\b(?:cipher\s+/w\b|sdelete\b|shred\b|(?:srm|wipe)\s+\S|"
    r"Clear-RecycleBin\b)",
    re.IGNORECASE)

# Infra destroyers (warn): these destroy live resources/state - the blast
# radius exceeds a local worktree. Advisory only (often intentional).
INFRA_DESTROY = re.compile(
    r"\b(?:docker\s+(?:system\s+prune\b[^|;&]*-[af]|volume\s+prune)|"
    r"docker(?:\s+compose|-compose)\s+down\b[^|;&]*-v|"
    r"terraform\s+(?:destroy|apply\b[^|;&]*-destroy)|"
    r"kubectl\s+delete\s+(?:namespace|ns|pvc|pv|deployment|statefulset|"
    r"daemonset|ingress|secret|configmap|pods?|cronjobs?|jobs?|"
    r"services?|svc|nodes?)\b|"
    r"kubectl\s+delete\b[^|;&]*(?:--all\b|-f\b)|"
    r"helm\s+(?:uninstall|delete)\b|"
    r"vagrant\s+destroy\b|"
    r"aws\s+(?:s3\s+(?:rb|rm\b[^|;&]*(?:--recursive|-r\b))|"
    r"ec2\s+terminate-instances|cloudformation\s+delete-stack|"
    r"ecs\s+delete-service|rds\s+delete-db)\b|"
    r"az\s+(?:group\s+delete|vm\s+delete|vmss\s+delete|aks\s+delete|"
    r"storage\s+(?:account\s+delete|blob\s+delete-batch)|"
    r"webapp\s+delete|functionapp\s+delete)\b|"
    r"gcloud\s+(?:projects\s+delete|compute\s+instances\s+delete|"
    r"container\s+clusters\s+delete|sql\s+instances\s+delete|"
    r"storage\s+(?:rm|buckets\s+delete)|functions\s+delete)\b|"
    r"doctl\s+(?:[\w-]+\s+)*delete\b|"
    r"rclone\s+(?:delete|purge|deletefile)\b|"
    r"gsutil\s+(?:-[\w-]+(?:\s+\S+)?\s+)*rm\b|"
    r"git\S*\s+push\b[^|;&]*(?:\s--delete\b|\s:[\w./-]+)|"
    r"gh\S*\s+(?:repo\s+delete\b|api\b[^|;&]*(?:-X|--method)[=\s]*"
    r"DELETE))",
    re.IGNORECASE)

# Publish/deploy (warn): pushes public/production state - packages become
# visible (npm unpublish is 72h-limited), images overwrite shared tags,
# --prod deploys mutate live systems.
PUBLISH_DEPLOY = re.compile(
    r"\b(?:(?:npm|pnpm)\s+publish|yarn\s+npm\s+publish|"
    r"twine\s+upload|cargo\s+publish|gem\s+push|"
    r"(?:dotnet\s+)?nuget\s+push|poetry\s+publish|"
    r"docker\s+push|helm\s+push|"
    r"vercel\b[^|;&]*(?:--prod|deploy\b[^|;&]*--prod)|"
    r"netlify\s+deploy\b[^|;&]*--prod|"
    r"firebase\s+deploy|(?:flyctl|fly)\s+deploy|"
    r"serverless\s+deploy|sam\s+deploy|cdk\s+deploy|"
    r"wrangler\s+(?:deploy|publish))\b",
    re.IGNORECASE)

# Remote-code fetch-pipe (warn): a download verb feeding an interpreter runs
# unvetted remote code. Advisory only (installers legitimately use it, but the
# blast radius is the whole machine). Covers pipe form (curl|sh, iwr|iex),
# chained form (wget x && sh x) and the PS cradle (iex (iwr ...)).
_FETCH_VERBS = r"(?:curl|wget|iwr|irm|Invoke-WebRequest|Invoke-RestMethod)"
_INTERPRETERS = (
    r"(?:(?:sudo|env)\s+)?(?:(?:ba|z|da|k|c|fi|a)?sh|iex|Invoke-Expression|powershell(?:\.exe)?|"
    r"pwsh|cmd|python[0-9.]*|node|ruby|perl)\b|"
    r"/(?:usr/)?bin/(?:ba|z|da|k|c|fi|a)?sh\b")
FETCH_PIPE_EXEC = re.compile(
    r"\b" + _FETCH_VERBS + r"\b[^|;]*\|\s*" + _INTERPRETERS + r"|"
    r"\b" + _FETCH_VERBS + r"\b[^|;]*&&\s*" + _INTERPRETERS + r"|"
    r"\b" + _FETCH_VERBS + r"\b[^|;]*;\s*" + _INTERPRETERS + r"|"
    r"\b(?:iex|Invoke-Expression)\s*\([^)]*\b(?:iwr|irm|Invoke-WebRequest|"
    r"Invoke-RestMethod|DownloadString|WebClient)\b",
    re.IGNORECASE)

# Windows chmod-777 equivalent (warn): recursive Everyone:F grants destroy the
# ACL model on whatever path they hit - same class as CHMOD_DANGEROUS.
ACL_WIPE = re.compile(
    r"\b(?:icacls|cacls|xcacls)\b(?=[^|;&]*/t\b)[^|;&]*"
    r"/(?:grant|g)\b[^|;&]*(?:Everyone|\*?S-1-1-0)[^|;&]*:F\b",
    re.IGNORECASE)

# Session/state killers (warn): shutdown/reboot/logoff kill every running
# process and all in-flight work. Command-position anchored (^, &&, ;, |) so
# `cd shutdown` or `cat reboot.log` stay silent. kill -9 -1 / killall5 hit
# every owned process at once.
SESSION_KILL = re.compile(
    r"(?:^|&&|\|\||[|;])\s*(?:sudo\s+)?(?:shutdown|reboot|halt|poweroff|"
    r"logoff|Restart-Computer|Stop-Computer|init\s+[06]|telinit\s+[06]|"
    r"systemctl\s+(?:poweroff|reboot|halt)|killall5?|loginctl\s+"
    r"(?:poweroff|reboot|halt|terminate-user))\b|"
    r"\bkill\s+(?:-[a-zA-Z]*9|-KILL)\s+-1\b|"
    r"\bpkill\b[^|;&]*\s-u\b",
    re.IGNORECASE)

# PowerShell pipe-delete (warn): source piped into a delete verb deletes
# every piped object - only possible under PS semantics. Covers the bare
# `| ri` form, pipeline-variable targets (`| ri $_.FullName`), and
# ForEach-Object delete blocks (`| % { ri $_ }`).
PS_PIPE_DELETE = re.compile(
    r"\|\s*(?:Remove-Item|ri)\s*(?:-[a-zA-Z]+)*\s*['\"`]?\s*"
    r"(?:$|[|;&])|"
    r"\|\s*(?:Remove-Item|ri)\b[^|;&]*\$_\.\w+|"
    r"\|\s*(?:%|foreach(?:-Object)?)\s*\{[^}]*\b(?:Remove-Item|ri)\b",
    re.IGNORECASE)

# File-destroyers outside the rm family (warn): interpreter tree-deletes,
# find -delete on broad roots, rsync --delete mirroring, dd zero-fills.
# Literal dangerous targets only (root/home/drive/dot) - rmtree('build')
# stays silent like the whitelisted rm -rf.
FILE_DESTROY = re.compile(
    r"\b(?:shutil\.rmtree|FileUtils\.rm_rf|remove_tree)\s*\(\s*"
    r"['\"]?(?:/|~|\.\.?|[A-Za-z]:[\\/])|"
    r"\bfind\s+(?:/|~|\.\.?|[A-Za-z]:[\\/])[^|;&]*"
    r"(?:-delete\b|-exec(?:dir)?\s+(?:rm|shred|srm)\b)|"
    r"\brsync\b[^|;&]*--delete\b|"
    r"\bdd\b[^|;&]*\bif=/dev/(?:zero|random|urandom)\b[^|;&]*\bof=",
    re.IGNORECASE)

# Protection/evidence destroyers (warn): disarm defenses or wipe the forensic
# trail - Defender disables/exclusions, firewall off, execution-policy bypass,
# event-log/audit-policy/USN-journal clears.
PROTECTION_KILL = re.compile(
    r"\b(?:Set-MpPreference\b[^|;&]*(?:-Disable\w+\s+\$?[tT]rue|"
    r"Exclusion\w*)|"
    r"Add-MpPreference\b[^|;&]*Exclusion\w*|"
    r"netsh\s+advfirewall\b[^|;&]*\bstate\s+off\b|"
    r"Set-ExecutionPolicy\b[^|;&]*\b(?:Unrestricted|Bypass)\b|"
    r"wevtutil\s+cl\b|(?:Clear|Remove)-EventLog\b|"
    r"auditpol\b[^|;&]*/(?:clear|remove)\b|"
    r"fsutil\s+usn\s+deletejournal|"
    r"ip6?tables\s+-F\b|nft\s+flush\b|ufw\s+(?:disable|reset)\b|"
    r"ip\s+route\s+flush\b|firewall-cmd\b[^|;&]*--panic-on|"
    r"Set-NetFirewallProfile\b[^|;&]*-Enabled\s+(?:\$?[fF]alse|0))\b",
    re.IGNORECASE)

# Windows reserved device basenames in bash have no device mapping:
# `> nul`, `> con`, `> com1`, `> "nul"`, `> ./nul`, `>nul` (no space),
# `tee nul`, `touch nul`, `mkdir nul`, `cp/mv x nul`, `ln x nul` all create
# literal ghost files/dirs (or silently discard for `nul.txt`-style stems).
# Observed live 2026-11-24 (adversarial probe after Gate 9 shipped).
# Only safe inside cmd/powershell/pwsh wrappers, which resolve the names
# to real devices themselves.
_RESERVED_STEM = r"(?:nul|con|aux|prn|com[1-9]|lpt[1-9])"
# Win32 also strips trailing dots/spaces: `> nul.` and `> "nul "` hit the
# device path (verified 2026-11-24) - the ext group allows zero chars.
_RESERVED_TARGET = (r"[\"']?\.{0,2}[\\/]?" + _RESERVED_STEM +
                    r"(?:\.[\w-]*)?[\"']?(?=[\s;|&]|$)")
RESERVED_REDIRECT = re.compile(
    r">{1,2}\s*" + _RESERVED_TARGET, re.IGNORECASE)
RESERVED_VERB = re.compile(
    r"\b(?:tee|touch|mkdir|cp|mv|ln|install)\b(?:\s+-[\w-]+)*\s+[^|;&]*?"
    + _RESERVED_TARGET, re.IGNORECASE)
SHELL_WRAPPER = re.compile(
    r"\b(?:cmd(?:\.exe)?|powershell(?:\.exe)?|pwsh(?:\.exe)?)\b",
    re.IGNORECASE)

# NTFS alternate data streams: a ':' in the basename of a redirect/verb
# target silently diverts content into a hidden stream while the named file
# is created 0-byte (verified 2026-11-24 - same wrong-state class as the
# reserved names above). The pattern requires the ':' AFTER the last path
# separator so 'C:\dir\file.txt' drive prefixes do not match. Windows-only:
# ':' is a legal POSIX filename char. Remote/URI forms are not ADS: ':' not
# followed by a path separator (ctr:/x, s3://b) and '@' tokens (user@host:)
# are excluded - docker cp/scp/rsync destinations stay allowed.
_ADS_BASENAME = (r"(?:[^\s|;&>\"']*[\\/])*"
                 r"(?![A-Za-z](?::[\\/]|:\s|:$))"
                 r"(?<![^\s|;&>\"'\\/])[^\s|;&>\"'/\\@]+:(?![\\/])")
ADS_REDIRECT = re.compile(r">{1,2}\s*[\"']?" + _ADS_BASENAME)
ADS_VERB = re.compile(
    r"\b(?:tee|touch|mkdir|cp|mv|ln|install)\b(?:\s+-[\w-]+)*\s+[^|;&]*?"
    + _ADS_BASENAME)

# Trailing-dot/space collapse: Win32 strips them, so '> f.' writes 'f' -
# several "different" names land on one path (verified 2026-11-24, same
# silent wrong-state class as ADS). Windows-only (POSIX keeps 'f.').
_DOT_TARGET = r"[^\s|;&>\"']*[.]\s*[\"'`]?\s*(?:$|[|;&])"
DOT_REDIRECT = re.compile(r">{1,2}\s*[\"']?" + _DOT_TARGET)
DOT_VERB = re.compile(
    r"\b(?:tee|touch|mkdir|cp|mv|ln|install|rmdir)\b(?:\s+-[\w-]+)*\s+"
    r"[^|;&]*?" + _DOT_TARGET)


def _branch_d_targets(command):
    """Branch operands of every `git branch -D` in the command."""
    out = []
    for m in GIT_BRANCH_FORCE_DELETE.finditer(command):
        skip_next = False
        for tok in (m.group(1) or "").split():
            tok = tok.strip().strip("'\"")
            if not tok:
                continue
            if tok in ("&&", "||", ";", "|", ">", ">>"):
                break
            if skip_next:
                skip_next = False
                continue
            # Flags (-D, --force, --delete) are modifiers; `--` is the
            # POSIX end-of-options marker; value-taking flags consume
            # the next token (a rename/sort target, not a branch).
            if tok in _BRANCH_VALUE_FLAGS:
                skip_next = True
            elif tok.startswith("-"):
                continue
            else:
                out.append(tok)
    return out


def _cherry_merged(branch):
    """True when every commit on <branch> is patch-equivalent in HEAD.

    `git cherry HEAD <branch>` marks commits `+` when they have no
    patch-equivalent upstream - squash/rebase merges rewrite SHAs but keep
    patch-ids, so a fully merged branch reports zero `+` lines even though
    `git branch -d` still refuses the delete (observed 2026-11-24:
    post-squash lane cleanup needed `update-ref -d` to bypass this gate).
    Unresolvable refs or git failures count as NOT merged (fail-safe).
    """
    try:
        import subprocess as _sp
        p = _sp.run(["git", "cherry", "HEAD", branch],
                    capture_output=True, text=True, encoding="utf-8",
                    errors="replace", timeout=15)
    except Exception:
        return False
    if p.returncode != 0:
        return False
    return all(not line.startswith("+") for line in p.stdout.splitlines())


# Stashed by main() so block() can re-pend a denied wtp line - the
# keystrokes stay on the real input line after a deny (blocked-call
# desync), and direct invocation does not pass through _hookrun.run().
_WTP_PAYLOAD = None


def _log_block(reason):
    """Append-only machine-local telemetry: one JSONL line per block.

    Proportionate observability for an internal tool (observability-quality
    skill): a structured log, no backend, negligible cost. Motivation: FP
    frequency was estimated from memory for months ('~2 blocks/day') with
    no data; friction claims in self-improvement loops need numbers. The
    log lives beside the live config (machine-local, never committed).
    Fail-safe: telemetry failure must never affect the security decision.
    """
    try:
        cfg = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        metrics = os.path.join(cfg, "metrics")
        os.makedirs(metrics, exist_ok=True)
        entry = {
            "ts": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "kind": reason[:80],
            "cwd": os.path.basename(os.getcwd()),
        }
        with open(os.path.join(metrics, "gate-blocks.jsonl"), "a",
                  encoding="utf-8") as fh:
            fh.write(json.dumps(entry, ensure_ascii=False) + "\n")
    except Exception:
        pass


def block(reason):
    """Emit a block decision and exit with code 2 (deny)."""
    if _WTP_PAYLOAD is not None:
        _hookrun.wtp_reject(_WTP_PAYLOAD)
    _log_block(reason)
    print(json.dumps({"decision": "block", "reason": reason}))
    sys.exit(2)


def split_targets(target_str):
    """Split an rm target list into individual paths, stripping quotes."""
    targets = []
    for raw in target_str.split():
        t = raw.strip().strip("'\"")
        # Stop at shell operators / redirections
        if t in ("&&", "||", ";", "|", ">", ">>"):
            break
        if t.startswith("-"):
            continue  # trailing flag
        if t:
            targets.append(t)
    return targets


def is_whitelisted(target):
    """True when the target is a known-safe build/cache directory (relative)."""
    t = target.rstrip("/").lstrip("./")
    if not t:
        return False
    first = t.split("/")[0]
    return first in RM_RF_WHITELIST


def check_rm_rf(command):
    """Return True when rm -rf (POSIX) or Remove-Item -Recurse -Force (Windows)
    targets a dangerous path."""
    # Check no-target case first (malformed recursive-force delete)
    if WIN_RM_RE_NOTARGET.search(command):
        return True
    for regex in (RM_RF_RE, WIN_RM_RE, WIN_RM_RE_PATH_FIRST):
        m = regex.search(command)
        if not m:
            continue
        targets = split_targets(m.group(1))
        if not targets:
            return True  # recursive-force delete with no target is malformed
        for target in targets:
            # Trailing slashes don't change the target: `rm -rf ./` is `.`.
            # Dot components collapse too: `dir/..`, `x/../../y`,
            # `node_modules/..` and `./.` all land on cwd or a parent -
            # normpath resolves them where rstrip cannot.
            norm = target.rstrip("/\\") or target
            try:
                collapsed = os.path.normpath(norm).rstrip("/\\")
            except (ValueError, OSError):
                collapsed = norm
            if norm in RM_DANGEROUS_TARGETS or \
                    collapsed in RM_DANGEROUS_TARGETS or collapsed == ".":
                return True
            # Absolute or home-relative paths are dangerous unless whitelisted
            if target.startswith(("/", "~", "$HOME")):
                return True
            # Windows drive roots (C:\, D:/, etc.)
            if re.match(r"^[A-Za-z]:[\\/]", target):
                return True
            # `..` only as a path component - `..foo`/`...` are legit names.
            def _is_parent(p):
                return p == ".." or p.startswith(("../", "..\\"))
            if _is_parent(target) or _is_parent(collapsed):
                return True
            # Globs widen the target set - `?` matches one char like `*`.
            if ("*" in target or "?" in target) and \
                    not is_whitelisted(target):
                return True
            if not is_whitelisted(target):
                # Relative non-whitelisted path: allow, but only if it is a
                # subdirectory (contains no traversal) — already checked above.
                continue
    return False


# Quoted single tokens hide verbs and flag values from every gate below:
# `git "push" --force`, `git "branch" -D`, `dd of="/dev/x"` all scanned
# clean pre-fix (probe 2026-11-24). Only single-token quotes unwrap -
# multi-word quoted text is prose/paths, not command syntax, and stays
# untouched so echo "text" shapes keep today's behavior.
_QUOTED_TOKEN = re.compile(r"\$?(['\"])([A-Za-z0-9_./\\:~=+*-]+)\1")
_EMPTY_QUOTES = re.compile(r"(''|\"\")")


def _unwrap_quoted_tokens(text):
    # Empty quote pairs concatenate away in shell (st''ate == state);
    # $'...' is ANSI-C quoting ($'state' == state) - both must collapse
    # before the single-token unwrap or they defeat name anchoring.
    text = _EMPTY_QUOTES.sub("", text)
    return _QUOTED_TOKEN.sub(r"\2", text)


def _deescape_shell(text):
    # Bash resolves \x -> x in unquoted words: r\m -> rm, st\ate -> state,
    # conf\ig -> config - the escaped spelling launders gated verbs and
    # targets. Brace expansion ({state}, state{,}) and $IFS (expands to a
    # separator) resolve the same way. The scan runs on raw AND de-escaped
    # forms (union - over-detect is the safe direction): raw keeps the
    # Windows-path view `devin\state`, the variant keeps the bash view
    # `devinstate` plus every escape-collapsed word.
    # Exception: `X:\` drive prefixes keep their backslash - collapsing
    # `C:\dir` to `C:dir` destroys the separator the ADS/drive lookahead
    # needs, turning every `X:\` target into a fake basename-colon match.
    t = re.sub(r"(?<![A-Za-z]:)\\(.)", r"\1", text)
    t = t.replace("{,}", "")
    t = re.sub(r"\$IFS\b", " ", t)
    return t.replace("{", "").replace("}", "")


# The exec tool's `env` dict is an injection channel the command scan
# cannot see: the command text stays benign while an env var smuggles the
# payload. Blocked keys (case-insensitive match, POSIX+Windows):
# - startup files: BASH_ENV/ENV/ZDOTDIR/PROMPT_COMMAND source attacker
#   files before the command runs
# - loader/runtime injection: LD_*/DYLD_*, NODE_OPTIONS, PYTHONSTARTUP/
#   PYTHONPATH/PYTHONHOME, RUBYOPT, PERL5OPT/PERL5LIB, JAVA_*_OPTIONS,
#   MAKEFILES/MAKEFLAGS
# - spawned helpers (themselves programs git/shell exec):
#   GIT_SSH_COMMAND/GIT_SSH, *ASKPASS, EDITOR/VISUAL/GIT_*_EDITOR, PAGER/
#   GIT_PAGER/MANPAGER, GIT_EXTERNAL_DIFF
# - git state/config redirect: GIT_DIR, GIT_WORK_TREE, GIT_CONFIG_COUNT +
#   GIT_CONFIG_KEY_*/GIT_CONFIG_VALUE_* (core.hooksPath -> RCE on any git
#   op), GIT_CONFIG_GLOBAL/SYSTEM, XDG_CONFIG_HOME, HOME/USERPROFILE
#   (relocates ~/.gitconfig lookup)
# - prefixes: BASH_FUNC_* (exported function bodies), GIT_CONFIG_KEY_*,
#   GIT_CONFIG_VALUE_*, DYLD_*
_ENV_DENY = {
    "bash_env", "env", "zdotdir", "prompt_command", "shelldir",
    "ld_preload", "ld_audit", "ld_library_path", "ld_debug",
    "dyld_insert_libraries", "dyld_library_path",
    "dyld_fallback_library_path", "dyld_print_libraries",
    "node_options", "pythonstartup", "pythonpath", "pythonhome",
    "rubyopt", "perl5opt", "perl5lib", "perl5db",
    "java_tool_options", "jdk_java_options", "_java_options",
    "makefiles", "makeflags", "mflags",
    "git_ssh_command", "git_ssh", "git_askpass", "ssh_askpass",
    "sudo_askpass", "git_editor", "editor", "visual",
    "git_sequence_editor", "git_pager", "pager", "manpager",
    "git_external_diff", "git_dir", "git_work_tree",
    "git_config_count", "git_config_global", "git_config_system",
    "git_config_nosystem", "git_config_parameters", "git_exec_path",
    "git_template_dir", "xdg_config_home", "home", "userprofile",
    "histfile", "inputrc", "bash_history", "psmodulepath",
    "browser", "cvs_rsh", "rsync_rsh", "svn_ssh", "hg_ssh",
    "darcs_ssh", "git_ssh_variant", "ssh_command", "ansible_ask_pass",
}
_ENV_DENY_PREFIX = ("bash_func_", "git_config_key_", "git_config_value_",
                    "dyld_")
# PATH is the strongest env vector: custom dirs shadow EVERY binary the
# command names (`{"PATH": "/tmp/x"}` + `ls` runs /tmp/x/ls). Allowed only
# when the inherited-path reference comes first - appended dirs can add
# binaries but cannot shadow ones that already resolve.
_PATH_SELF = re.compile(r"\$env:path|\$path|%path%", re.IGNORECASE)


# exec `workdir` relocates relative targets the scan sees as bare names:
# `rm -rf x` + workdir=/ removes /x. Recursive/wipe-class verbs with a
# sensitive root (fs root, home, system dirs) can't be verified -> block.
_WORKDIR_SENSITIVE = re.compile(
    r"^(?:~|%USERPROFILE%|%SystemRoot%|%WINDIR%|[\\/]|"
    r"[A-Za-z]:[\\/]*|[A-Za-z]:[\\/]+(?:Windows|Users|Program\s*Files|"
    r"ProgramData)[\\/]*|/(?:home|etc|usr|var|bin|sbin|lib|boot|opt|"
    r"root|srv)[\\/]*)$",
    re.IGNORECASE)
_WORKDIR_WIPE = re.compile(
    r"\brm\b[^|;&]*-[a-zA-Z]*[rR][a-zA-Z]*|\brm\b[^|;&]*[*?]|"
    r"\b(?:del|rd|rmdir|Remove-Item)\b[^|;&]*(?:/s\b|-r\b|-Recurse\b)|"
    r"\brobocopy\b[^|;&]*/mir\b|\b(?:format|mkfs|shred|srm|wipe)\b|"
    r"\bdd\b[^|;&]*\bof=",
    re.IGNORECASE)


def _env_violations(env):
    """Dangerous keys / shadowing PATH in an exec env dict (key names are
    the attack surface; values are program-parsed, not shell-expanded)."""
    bad = []
    for k, v in env.items():
        key = str(k).lower()
        if key in _ENV_DENY or key.startswith(_ENV_DENY_PREFIX):
            bad.append(str(k))
        elif key == "path":
            val = "" if v is None else str(v)
            m = _PATH_SELF.search(val)
            # Leading separator = empty first segment = the CURRENT dir
            # shadows every inherited binary (`":$PATH"` / `";%PATH%"`).
            if (not m or val[: m.start()].strip(";:")
                    or val.startswith((":", ";"))):
                bad.append("PATH")
    return bad


def strip_commit_message(command):
    """Remove commit message text from git commit commands so gates don't
    match descriptive text inside -m '...' or -F file references.

    Gates must scan the actual command, not prose in a commit message that
    happens to mention 'git clean -fdx' or 'mkfs' as a description of what
    was done. This extracts only the command portion before -m/--message/-F.

    For non-commit commands, returns the original string unchanged.
    """
    if not re.search(_GIT + r"\s+commit\b", command, re.IGNORECASE):
        return command
    # Strip everything after -m (incl. clustered -am/-sm and attached
    # -m"msg") / --message / -F / --file so message prose is never gated.
    stripped = re.split(
        r"\s+(?:-[a-zA-Z]*m\b|--message(?:=|\s)|-F\b|--file(?:=|\s))",
        command,
        maxsplit=1,
    )
    return stripped[0] if stripped else command


def main():
    try:
        _hookrun.pin_stdio_utf8(sys.stdin)
        data = json.load(sys.stdin)
    except (json.JSONDecodeError, EOFError, ValueError):
        sys.exit(0)  # fail-open: cannot parse, allow

    if not isinstance(data, dict):
        sys.exit(0)
    tool_name = data.get("tool_name", "")
    if tool_name not in ("exec", "write_to_process"):
        sys.exit(0)

    tool_input = data.get("tool_input")
    if not isinstance(tool_input, dict):
        sys.exit(0)
    env = tool_input.get("env")
    if isinstance(env, dict):
        bad = _env_violations(env)
        if bad:
            block(
                "env override " + ", ".join(sorted(bad)) +
                " injects executable state invisible to the command "
                "scan (startup files, loader/runtime hooks, git config, "
                "spawned helpers, or binary shadowing). Set it inside "
                "the command text where the gate can see it - e.g. "
                "`export PATH=\"$PATH:dir\"; cmd`.")
    command = tool_input.get("command", "") or ""
    workdir = tool_input.get("workdir")
    if (tool_name == "exec" and isinstance(workdir, str)
            and _WORKDIR_SENSITIVE.search(workdir.strip())
            and isinstance(command, str)
            and _WORKDIR_WIPE.search(command)):
        block(
            "wipe-class verb with a sensitive `workdir` root (" +
            workdir.strip() + ") - relative targets land somewhere "
            "dangerous and the command scan cannot resolve them. "
            "cd into the directory inside the command text instead.")
    if tool_name == "write_to_process":
        # The 'command' key on a wtp payload is never trusted - it is not
        # part of the tool schema and could be injected by the caller.
        # Extraction is idempotent (dedup record in the gated buffer
        # file), so always extract the submitted lines ourselves.
        global _WTP_PAYLOAD
        _WTP_PAYLOAD = data
        command = _hookrun.wtp_submitted_text(data)
        if "\x1e" in command:
            # Line-edit sentinel: history recall, cursor moves, edits and
            # completion all produce a submitted line the append-model
            # cannot reproduce - the gate cannot inspect what executes.
            # Same block whether the control and submit share one call or
            # are split across calls (sentinel lives in the pending
            # buffer).
            block(
                "line-editing control (arrows/C-a/C-e/<TAB>/<C-r>/etc.) "
                "before a submit makes the executed text uninspectable - "
                "history entries and mid-line edits are invisible to the "
                "gate. Re-type the command as one contiguous string - "
                "typed input is gated normally.")
    if not isinstance(command, str) or not command.strip():
        sys.exit(0)

    # Scan only the actual command, not commit message text.
    # A commit message that describes "added git clean -fdx gate" is not
    # a destructive command — it's prose. Gates must match real commands.
    scan_command = _unwrap_quoted_tokens(strip_commit_message(command))
    # Union with the bash-resolved form: every gate below searches the
    # combined text, so an escaped spelling hits the same arm as its
    # resolved word. `;` joins the variants - a hard boundary every
    # operand span ([^|;&...]) stops at, so a line-1 tail cannot read a
    # line-2 head as its operand (the \n joiner made `lvremove\nman`
    # look like `lvremove man`).
    scan_command += ";" + _deescape_shell(scan_command)
    # Variant with non-shell heredoc bodies removed: gates 9/10 guard
    # Windows filesystem artifacts created by the SHELL's own redirect/
    # verb machinery - inside a python/node heredoc body the same text is
    # inert string data, so scanning it there is pure false positive.

    # Gate 1: rm -rf dangerous paths
    try:
        if check_rm_rf(scan_command):
            block(
                "rm -rf targets a dangerous path (/, ~, *, ., parent, or absolute path). "
                "Use a specific relative subdirectory. Whitelisted prefixes: "
                + ", ".join(sorted(RM_RF_WHITELIST))
            )
    except SystemExit:
        raise
    except Exception:
        pass  # fail-open

    # Gate 2: git push --force without --dry-run
    try:
        if GIT_FORCE_PUSH.search(scan_command) and not GIT_DRY_RUN.search(scan_command):
            block(
                "git push --force without --dry-run. Run with --dry-run first to "
                "verify what will be pushed, then repeat without it."
            )
    except SystemExit:
        raise
    except Exception:
        pass

    # Gate 3c: git config writes / -c inline config with exec-capable
    # keys - a benign `git status` becomes RCE via core.hooksPath,
    # alias.*, credential.helper, filter.*.clean, includeIf.*.path etc.
    try:
        bad_key = _git_cfg_danger(scan_command)
        if bad_key:
            block(
                f"git config key '{bad_key}' executes code (hooks, "
                "alias expansion, credential/pager/filter programs, or "
                "config inclusion). Setting it would run arbitrary "
                "commands on this or a later git operation.")
    except SystemExit:
        raise
    except Exception:
        pass

    # Gate 4: SQL destructive operations (only when a SQL client is invoked)
    try:
        if SQL_DESTRUCTIVE.search(scan_command) and SQL_CLIENTS.search(scan_command):
            block(
                "SQL destructive operation (DROP/TRUNCATE/FLUSHALL/"
                "dropDatabase) detected. "
                "Use a reversible migration instead, or run it directly in a DB shell if intentional."
            )
    except SystemExit:
        raise
    except Exception:
        pass

    # Gate 5: chmod -R 777 on root or home
    try:
        if CHMOD_DANGEROUS.search(scan_command):
            block(
                "chmod -R 777 on root or home directory breaks system security. "
                "Use a specific path and the minimum required permissions."
            )
    except SystemExit:
        raise
    except Exception:
        pass

    # Gate 6: git clean -fdx (removes untracked + ignored files, irreversible)
    try:
        if GIT_CLEAN_FORCE.search(scan_command) and not GIT_CLEAN_DRY_RUN.search(scan_command):
            block(
                "git clean -fdx removes untracked AND ignored files with no "
                "reflog recovery. Use -n (dry-run) first to review what would "
                "be removed, or remove specific files explicitly."
            )
    except SystemExit:
        raise
    except Exception:
        pass

    # Gate 7: git branch -D (force delete branch, loses unmerged work)
    # Allows the delete when `git cherry` proves every commit on the branch
    # is already patch-equivalent in HEAD (covers squash/rebase merges that
    # `git branch -d` cannot see). Unknown/unresolved refs stay blocked.
    try:
        targets = _branch_d_targets(scan_command)
        # -C <dir>/--git-dir/--work-tree and GIT_DIR=/GIT_WORK_TREE= env
        # prefixes point at another repo: the cherry check cannot verify
        # it, so treat as unverifiable and keep the block.
        foreign_repo = targets and (re.search(
            r"\bgit(?:\.(?:exe|cmd|bat|com))?\b\s+"
            r"(?:-c\s+(?:[^\s|;&`'\"$(\n]|'[^'\n]*'|\"[^\"\n]*\")+\s+)*"
            r"(-C|--git-dir\b|--work-tree\b)",
            scan_command) or re.search(r"\bGIT_(?:DIR|WORK_TREE)=",
                                       scan_command))
        if foreign_repo or (targets and not all(_cherry_merged(b) for b in targets)):
            block(
                "git branch -D force-deletes a branch with unmerged commits. "
                "Use -d (safe delete, blocks if unmerged) or merge first."
            )
    except SystemExit:
        raise
    except Exception:
        pass

    # Gate 8: mkfs / dd to disk devices (filesystem wipe / raw disk write)
    try:
        if DISK_WIPE.search(scan_command):
            block(
                "mkfs or dd to a disk device wipes the filesystem / writes raw "
                "data to the device. This is irreversible. Confirm the device "
                "path explicitly if this is intentional."
            )
    except SystemExit:
        raise
    except Exception:
        pass

    # Gate 8b: Windows format / diskpart / PowerShell disk wipe
    try:
        if WIN_DISK_WIPE.search(scan_command):
            block(
                "format/diskpart wipes or repartitions a disk. This is "
                "irreversible. Confirm the target explicitly if intentional."
            )
    except SystemExit:
        raise
    except Exception:
        pass

    # Gate 8c: encoded execution - a decoded payload is uninspectable to
    # the command scan, so the transport itself is blocked.
    try:
        if ENCODED_EXEC.search(scan_command):
            block(
                "encoded/obfuscated execution (powershell -enc, base64/"
                "certutil/openssl/xxd decode piped or substituted into a "
                "shell/eval) hides the real command from the gate. "
                "Run the decoded command as plain text instead.")
    except SystemExit:
        raise
    except Exception:
        pass

    # Gate 8d: deleting subagent enforcement state (profile records,
    # dispatch ledger, budget policy) - self-unlimiting class; the
    # file-tool side is guarded in validate-tool-args.
    try:
        if _state_file_targeted(scan_command):
            block(
                "delete/write targeting hook enforcement state "
                "(subagent-*.json* / wtp-*.txt / the devin/state dir) - "
                "removing or corrupting it resets the session's own "
                "profile/budget limits or the stdin-channel line buffers. "
                "Ask the user to change policy instead.")
    except SystemExit:
        raise
    except Exception:
        pass

    # Gate 8e: command substitution inside a delete-verb's operand -
    # the target resolves at run time and the gate cannot read it.
    try:
        if _STATE_SUBST_TARGET.search(scan_command):
            block(
                "delete/move verb takes a command substitution or "
                "backtick operand - the real target resolves inside the "
                "substitution and is invisible to the gate (e.g. a "
                "state-file path built at run time). Expand the target "
                "list first, then run the delete on literal names.")
    except SystemExit:
        raise
    except Exception:
        pass

    # SECURITY NOTE (2026-11-26 review, verdict UNSAFE on narrowing):
    # heredoc bodies are deliberately NOT stripped before scanning. A
    # regex-based stripper was tried and an independent adversarial
    # review verified 7 working bypasses (fake operators in comments/
    # quotes, delimiter truncation, multiple heredocs, indirect shell
    # recipients, cmd recipient, deescape-union synthesis). Heredoc
    # stdin for interpreters is executable code (os.system et al), so
    # the 'inert data' premise is false. False-positive cost accepted;
    # workaround: write the payload with the write tool to a file and
    # execute the file. Do NOT re-narrow without a real shell parser.
    # Gate 9: Windows reserved device name outside a cmd/powershell wrapper
    # (literal ghost artifact or silent discard in bash). Windows-only: on
    # POSIX, `nul`/`con`/`aux` are ordinary legal filenames.
    try:
        if os.name == "nt" \
                and (RESERVED_REDIRECT.search(scan_command)
                     or RESERVED_VERB.search(scan_command)) \
                and not SHELL_WRAPPER.search(scan_command):
            block(
                "bash has no NUL/CON/AUX/PRN/COM1-9/LPT1-9 device: that "
                "name creates a literal ghost file/dir (or silently "
                "discards for stem.ext forms). Use '/dev/null' for "
                "discard, a different filename, or wrap in "
                "cmd /c / powershell where the name resolves to a device."
            )
    except SystemExit:
        raise
    except Exception:
        pass

    # Gate 10: NTFS alternate-data-stream target ('name:stream') - the named
    # file is created 0-byte and content diverts into a hidden stream.
    # Windows-only; ':' is a legal POSIX filename char.
    try:
        ads_match = ADS_REDIRECT.search(scan_command) \
            or ADS_VERB.search(scan_command)
        if os.name == "nt" and ads_match:
            block(
                "redirect/verb target basename contains ':' - on Windows "
                "this is an NTFS alternate data stream, so the named file "
                "is created empty and content is silently diverted. Use a "
                "filename without ':'. Matched "
                f"{ads_match.group(0)[:80]!r} - if you are writing a file "
                "whose literal content mentions such a pattern, use the "
                "write tool to create the file instead of a shell heredoc "
                "or redirect (the body is scanned because interpreter "
                "stdin is executable code). If this is a false positive, "
                "report it - but note the gate fails closed by design.")
        if os.name == "nt" \
                and (DOT_REDIRECT.search(scan_command)
                     or DOT_VERB.search(scan_command)):
            block(
                "redirect/verb target ends in a dot or space - Win32 "
                "strips it, so the write silently lands on the stripped "
                "name. Remove the trailing '.'/' '.")
    except SystemExit:
        raise
    except Exception:
        pass

    # Gate 3: advisory warn-paths (stderr, never block) - reset --hard is
    # legitimate after rebase, the rest need operator awareness only.
    warn_checks = [
        (GIT_RESET_HARD.search,
         "WARNING: git reset --hard discards all uncommitted changes."),
        (GIT_BULK_DISCARD.search,
         "WARNING: git checkout/restore of '.' discards ALL "
         "uncommitted changes - prefer file-scoped checkout or "
         "'git stash' first."),
        (GIT_FORCE_SWITCH.search,
         "WARNING: forced switch/remove/reset discards uncommitted "
         "changes - 'git stash' first."),
        (GIT_STASH_DROP.search,
         "WARNING: git stash drop/clear deletes stashed work "
         "irreversibly."),
        (GIT_RECOVERY_KILL.search,
         "WARNING: destroys the recovery net (reflog expire, "
         "gc --prune=now, shadow copies, backups, bcdedit, "
         "HKLM registry) or deletes refs directly (update-ref -d)."),
        (SECURE_ERASE.search,
         "WARNING: secure-erase tool (shred/sdelete/srm/wipe/cipher /w/"
         "Clear-RecycleBin) - deleted content is unrecoverable "
         "by design."),
        (INFRA_DESTROY.search,
         "WARNING: destroys live infra/resources (docker prune -v, "
         "terraform destroy, kubectl delete, helm uninstall, "
         "vagrant destroy, cloud deletes, remote ref delete)."),
        (FETCH_PIPE_EXEC.search,
         "WARNING: downloads and executes remote code in one step "
         "(curl|sh, iwr|iex) - unvetted content runs with full "
         "user privileges."),
        (ACL_WIPE.search,
         "WARNING: recursive Everyone:F ACL grant (icacls/cacls "
         "/t) destroys the permission model - Windows chmod -R 777."),
        (SESSION_KILL.search,
         "WARNING: shuts down/reboots the session or kills all "
         "processes - all in-flight work is lost."),
        (PROTECTION_KILL.search,
         "WARNING: disarms a defense or wipes the forensic trail "
         "(Defender disable/exclusion, firewall off, exec-policy "
         "bypass, event-log/audit clear)."),
        (lambda c: SQL_WARN.search(c) and SQL_CLIENTS.search(c),
         "WARNING: data-destroying SQL (WHERE-less DELETE wipes "
         "every row; ALTER TABLE ... DROP loses column data)."),
        (PUBLISH_DEPLOY.search,
         "WARNING: publishes or deploys to public/production "
         "state (package registry push, image push, --prod "
         "deploy) - externally visible and hard to undo."),
        (PS_PIPE_DELETE.search,
         "WARNING: pipes objects into a delete verb (x | "
         "Remove-Item) - deletes every piped item."),
        (FILE_DESTROY.search,
         "WARNING: destroys files outside the rm gate "
         "(rmtree/remove_tree on a root target, find -delete, "
         "rsync --delete, dd zero-fill)."),
    ]
    try:
        warnings = [msg for check, msg in warn_checks if check(scan_command)]
        if warnings:
            # stderr for direct invocation; additionalContext is the channel
            # that actually surfaces under _hookrun (child stderr is dropped
            # because fail_closed treats hook stderr as rejection).
            for msg in warnings:
                print(msg, file=sys.stderr)
            print(json.dumps({"hookSpecificOutput": {
                "hookEventName": "PreToolUse",
                "additionalContext": "\n".join(warnings)}}))
    except Exception:
        pass  # fail-soft: cleanup; preserve primary error

    sys.exit(0)


if __name__ == "__main__":
    main()
