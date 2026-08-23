#!/usr/bin/env python3
"""PreToolUse hook: blocks destructive commands that are irreversible or high-risk.

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
  7. git branch -D (force delete branch, loses unmerged work)
  8. mkfs / dd to disk devices (filesystem wipe)

Source: "Reason Less, Verify More" (arXiv:2607.07405, KDD 2026 Workshop)
  4-gate suite raised success 29.6%->42.0% (+12.4pp, P=0.0012, replicated P=0.0008)
  78% of failures are silent wrong-state with no tool error.
  Gates are deterministic, read-only, pre-execution predicates.
  Fail-open: if a gate raises an exception, log and allow.
"""
import sys, json, re

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

# git push --force without --dry-run.
# Negative lookahead on -f avoids matching --follow-tags.
# --force-with-lease is intentionally EXCLUDED: it is the recommended safe
# alternative to --force (fails if remote has new commits). Blocking it would
# encourage users to use the more dangerous --force instead.
GIT_FORCE_PUSH = re.compile(r"\bgit\s+push\b[^|;&]*?(?:\s-f\b|\s-[a-zA-Z]*f[a-zA-Z]*\b|\s--force\b(?!-with-lease))")
GIT_DRY_RUN = re.compile(r"(?:\s--dry-run(?![\w-])|\s-n(?![\w-]))")

GIT_RESET_HARD = re.compile(r"\bgit\s+reset\s+--hard\b")

SQL_DESTRUCTIVE = re.compile(
    r"\b(?:DROP\s+(?:TABLE|DATABASE|SCHEMA)|TRUNCATE\s+TABLE)\b",
    re.IGNORECASE,
)

# SQL client binaries — the destructive SQL gate only fires when one of these
# is in the command, so that echo/grep/cat/git-commit text mentioning the
# keywords is not falsely blocked.
SQL_CLIENTS = re.compile(
    r"\b(?:psql|mysql|sqlite3?|sqlcmd|cockroach(?:-sql)?|db2|sqlplus|"
    r"pgcli|mycli|litecli|usql|sqlshell|psql)\b",
    re.IGNORECASE,
)

CHMOD_DANGEROUS = re.compile(r"\bchmod\s+(?:-[a-zA-Z]*R[a-zA-Z]*\s+)777\s+(?:/|~|\$HOME)(?:\s|$)")

# Windows recursive-delete equivalents: Remove-Item -Recurse -Force, rd /s /q,
# del /s /q, rmdir /s. These are the Windows counterparts to rm -rf.
# Pattern 1: flags before target (Remove-Item -Recurse -Force C:\)
WIN_RM_RE = re.compile(
    r"\b(?:Remove-Item|del|rmdir|rd)\b"
    r"(?:\s+-[a-zA-Z]+)*\s+"
    r"(?:(?:-[a-zA-Z]*[rR][a-zA-Z]*[fF][a-zA-Z]*|-[a-zA-Z]*[fF][a-zA-Z]*[rR][a-zA-Z]*|--Recurse\s+--Force|--Force\s+--Recurse|-Recurse\s+-Force|-Force\s+-Recurse|/s\s*/q|/s)\s+)"
    r"(.+)",
    re.IGNORECASE,
)
# Pattern 2: target before flags (Remove-Item C:\ -Recurse -Force) — PowerShell
# allows parameters in any order. The path must NOT start with '-' (a flag).
WIN_RM_RE_PATH_FIRST = re.compile(
    r"\b(?:Remove-Item|del|rmdir|rd)\b"
    r"(?:\s+(?:-[a-zA-Z]+))*\s+"  # optional leading flags
    r"([^-]\S*)"  # the target path (must not start with '-')
    r"(?:\s+(?:-[a-zA-Z]*[rR][a-zA-Z]*[fF][a-zA-Z]*|-[a-zA-Z]*[fF][a-zA-Z]*[rR][a-zA-Z]*|--Recurse\s+--Force|--Force\s+--Recurse|-Recurse\s+-Force|-Force\s+-Recurse|/s\s*/q|/s)\b)",
    re.IGNORECASE,
)
# Pattern 3: recursive-force flags with NO target (malformed, like POSIX rm -rf
# with no target — treated as dangerous by check_rm_rf).
WIN_RM_RE_NOTARGET = re.compile(
    r"\b(?:Remove-Item|del|rmdir|rd)\b"
    r"(?:\s+-[a-zA-Z]+)*\s+"
    r"(?:-[a-zA-Z]*[rR][a-zA-Z]*[fF][a-zA-Z]*|-[a-zA-Z]*[fF][a-zA-Z]*[rR][a-zA-Z]*|--Recurse\s+--Force|--Force\s+--Recurse|-Recurse\s+-Force|-Force\s+-Recurse|/s\s*/q|/s)"
    r"(?:\s+(?:-[a-zA-Z]+))*\s*$",
    re.IGNORECASE,
)

# git clean -fdx: removes untracked AND ignored files (irreversible, no reflog)
# Excludes -n (dry-run) — if -n is present, it's a preview, not a destructive op.
# Matches combined flags (-fdx, -xfd) and --force with separate -d/-x flags.
GIT_CLEAN_FORCE = re.compile(r"\bgit\s+clean\s+(?:-[a-zA-Z]*[fF][a-zA-Z]*[dDxX][a-zA-Z]*|-[a-zA-Z]*[dDxX][a-zA-Z]*[fF][a-zA-Z]*|--force\b(?:\s+-[a-zA-Z]+)*\s+-[a-zA-Z]*[dDxX]|-f\b(?:\s+-[a-zA-Z]+)*\s+-[a-zA-Z]*[dDxX])")
GIT_CLEAN_DRY_RUN = re.compile(r"\bgit\s+clean\s+(?:-[a-zA-Z]*n[a-zA-Z]*|-[a-zA-Z]*\s+--dry-run\b)")

# git branch -D: force-delete branch (loses unmerged commits)
GIT_BRANCH_FORCE_DELETE = re.compile(r"\bgit\s+branch\s+(?:-[a-zA-Z]*D[a-zA-Z]*\b|--delete\s+--force\b)")

# mkfs / dd to disk devices (filesystem wipe / raw disk write)
DISK_WIPE = re.compile(r"\b(?:mkfs(?:\.\w+)?|dd\s+.*\bof=/dev/(?:sd|nvme|hd|vd|disk))", re.IGNORECASE)


def block(reason):
    """Emit a block decision and exit with code 2 (deny)."""
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
            if target in RM_DANGEROUS_TARGETS:
                return True
            # Absolute or home-relative paths are dangerous unless whitelisted
            if target.startswith(("/", "~", "$HOME")):
                return True
            # Windows drive roots (C:\, D:/, etc.)
            if re.match(r"^[A-Za-z]:[\\/]", target):
                return True
            if target.startswith(".."):
                return True
            if "*" in target and not is_whitelisted(target):
                return True
            if not is_whitelisted(target):
                # Relative non-whitelisted path: allow, but only if it is a
                # subdirectory (contains no traversal) — already checked above.
                continue
    return False


def strip_commit_message(command):
    """Remove commit message text from git commit commands so gates don't
    match descriptive text inside -m '...' or -F file references.

    Gates must scan the actual command, not prose in a commit message that
    happens to mention 'git clean -fdx' or 'mkfs' as a description of what
    was done. This extracts only the command portion before -m/--message/-F.

    For non-commit commands, returns the original string unchanged.
    """
    if "git commit" not in command.lower():
        return command
    # Strip everything after -m / --message= / --message / -F
    stripped = re.split(
        r"\s+(?:-m\b|--message(?:=|\s)|-F\b|--file(?:=|\s))",
        command,
        maxsplit=1,
    )
    return stripped[0] if stripped else command


def main():
    try:
        data = json.load(sys.stdin)
    except (json.JSONDecodeError, EOFError, ValueError):
        sys.exit(0)  # fail-open: cannot parse, allow

    if data.get("tool_name", "") != "exec":
        sys.exit(0)

    tool_input = data.get("tool_input") or {}
    command = tool_input.get("command", "") or ""
    if not command.strip():
        sys.exit(0)

    # Scan only the actual command, not commit message text.
    # A commit message that describes "added git clean -fdx gate" is not
    # a destructive command — it's prose. Gates must match real commands.
    scan_command = strip_commit_message(command)

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

    # Gate 4: SQL destructive operations (only when a SQL client is invoked)
    try:
        if SQL_DESTRUCTIVE.search(scan_command) and SQL_CLIENTS.search(scan_command):
            block(
                "SQL destructive operation (DROP TABLE/DATABASE/SCHEMA or TRUNCATE) detected. "
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
    try:
        if GIT_BRANCH_FORCE_DELETE.search(scan_command):
            block(
                "git branch -D force-deletes a branch, losing unmerged commits. "
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

    # Gate 3: git reset --hard — warn only (legitimate after rebase)
    try:
        if GIT_RESET_HARD.search(scan_command):
            print(
                "WARNING: git reset --hard discards all uncommitted changes.",
                file=sys.stderr,
            )
    except Exception:
        pass

    sys.exit(0)


if __name__ == "__main__":
    main()
