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
# Negative lookahead on -f avoids matching --follow-tags, --force-with-lease is
# still a force push so it is intentionally included.
GIT_FORCE_PUSH = re.compile(r"\bgit\s+push\b[^|;&]*?(?:\s-f\b|\s-[a-zA-Z]*f[a-zA-Z]*\b|\s--force\b|\s--force-with-lease\b)")
GIT_DRY_RUN = re.compile(r"(?:\s--dry-run(?![\w-])|\s-n(?![\w-]))")

GIT_RESET_HARD = re.compile(r"\bgit\s+reset\s+--hard\b")

SQL_DESTRUCTIVE = re.compile(
    r"\b(?:DROP\s+(?:TABLE|DATABASE|SCHEMA)|TRUNCATE\s+TABLE)\b",
    re.IGNORECASE,
)

CHMOD_DANGEROUS = re.compile(r"\bchmod\s+(?:-[a-zA-Z]*R[a-zA-Z]*\s+)777\s+(?:/|~|\$HOME)(?:\s|$)")

# Windows recursive-delete equivalents: Remove-Item -Recurse -Force, rd /s /q,
# del /s /q, rmdir /s. These are the Windows counterparts to rm -rf.
WIN_RM_RE = re.compile(
    r"\b(?:Remove-Item|del|rmdir|rd)\b"
    r"(?:\s+-[a-zA-Z]+)*\s+"
    r"(?:(?:-[a-zA-Z]*[rR][a-zA-Z]*[fF][a-zA-Z]*|-[a-zA-Z]*[fF][a-zA-Z]*[rR][a-zA-Z]*|--Recurse\s+--Force|--Force\s+--Recurse|/s\s*/q|/s)\s+)"
    r"(.+)",
    re.IGNORECASE,
)

# git clean -fdx: removes untracked AND ignored files (irreversible, no reflog)
# Excludes -n (dry-run) — if -n is present, it's a preview, not a destructive op.
GIT_CLEAN_FORCE = re.compile(r"\bgit\s+clean\s+(?:-[a-zA-Z]*[fF][a-zA-Z]*[dDxX][a-zA-Z]*|-[a-zA-Z]*[dDxX][a-zA-Z]*[fF][a-zA-Z]*|--force\b)")
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
    for regex in (RM_RF_RE, WIN_RM_RE):
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

    # Gate 1: rm -rf dangerous paths
    try:
        if check_rm_rf(command):
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
        if GIT_FORCE_PUSH.search(command) and not GIT_DRY_RUN.search(command):
            block(
                "git push --force without --dry-run. Run with --dry-run first to "
                "verify what will be pushed, then repeat without it."
            )
    except SystemExit:
        raise
    except Exception:
        pass

    # Gate 4: SQL destructive operations
    try:
        if SQL_DESTRUCTIVE.search(command):
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
        if CHMOD_DANGEROUS.search(command):
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
        if GIT_CLEAN_FORCE.search(command) and not GIT_CLEAN_DRY_RUN.search(command):
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
        if GIT_BRANCH_FORCE_DELETE.search(command):
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
        if DISK_WIPE.search(command):
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
        if GIT_RESET_HARD.search(command):
            print(
                "WARNING: git reset --hard discards all uncommitted changes.",
                file=sys.stderr,
            )
    except Exception:
        pass

    sys.exit(0)


if __name__ == "__main__":
    main()
