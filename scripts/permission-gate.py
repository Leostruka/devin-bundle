#!/usr/bin/env python3
"""permission-gate — PermissionRequest hook: auto-approve provably read-only
commands, stay silent on everything else.

Design: approve-only, never deny; deny-by-default shapes. A command is
approved only when its full argument list matches an explicit safe shape —
unknown verbs, write-capable flags, positional args outside the verb's
read-only grammar, and any shell composition all fall through to silence so
the human prompt proceeds. `block` is never emitted: an unexpected payload
is a bug in the gate, not a reason to hide a decision from the user.
"""
import json
import re
import sys

# Shell composition: an approved command is ONE invocation.
UNSAFE_CHARS = re.compile(r"[;&|`$<>\\\r\n]|\(|\)")

# Binaries that can only read/print — every arg form is safe.
SAFE_BINARIES = {
    "ls", "dir", "pwd", "cat", "head", "tail", "wc", "file", "which",
    "whereis", "uname", "whoami", "printenv", "echo",
}

# git verbs that cannot mutate (given the arg rules below). Positionals are
# allowed unless flagged as creating refs.
GIT_READONLY = {
    "status", "diff", "log", "show", "blame", "grep", "shortlog",
    "whatchanged", "describe", "rev-parse", "rev-list", "check-ignore",
    "cat-file", "count-objects", "for-each-ref", "ls-files", "verify-commit",
    "verify-tag", "name-rev", "ls-remote",
}
# git verbs that mutate when given a positional ref name — list forms only.
GIT_LIST_ONLY = {
    "branch": re.compile(r"^-(a|v|l|r|f|q|u\d*|vv|list|show-current)"
                         r"|^--(list|all|show-current|remotes|contains|"
                         r"merged|no-merged|sort=|points-at|format=|column|"
                         r"no-column|omit-empty|ignore-case)"),
    "tag": re.compile(r"^-(l|n\d*|v|sort=|points-at|contains|merged|"
                      r"no-merged|list|ignore-case|column|no-column)|"
                      r"^--(list|sort=|points-at|contains|merged|no-merged|"
                      r"format=|ignore-case|column|no-column)"),
}
# git verbs with mixed read/write subcommands.
GIT_SUBVERBS = {
    "remote": {"show", "get-url"},
    "stash": {"list", "show"},
    "reflog": {"show"},
}
# git arg shapes that turn a read verb into a side effect.
GIT_DANGEROUS_ARG = re.compile(
    r"^ext::|"                       # ext:: transport executes the payload
    r"^--output(=|$)|"               # arbitrary file write
    r"^(--exec(ute)?|--receive-pack|--upload-pack)(=|$)|"  # protocol exec
    r"^(--open-files-in-pager|--ext-diff|--textconv)(=|$)",  # exec helpers
    re.I)
# git grep -O<pager> executes the pager; case-sensitive (-o is --others).
GIT_GREP_PAGER = re.compile(r"^-O")
# -p/--prune only mutates under `git remote`; -u is --upload-pack on ls-remote.
GIT_REMOTE_DANGEROUS = re.compile(r"^(-p|--prune)$", re.I)
GIT_LSREMOTE_DANGEROUS = re.compile(r"^-u$")

# gh: commands are `gh <noun> <verb>`.
GH_NOUN_READS = {
    "pr": {"view", "list", "diff", "checks", "status"},
    "issue": {"view", "list", "status"},
    "repo": {"view", "list"},
    "run": {"view", "list"},
    "workflow": {"view", "list"},
    "release": {"view", "list"},
    "gist": {"view", "list"},
    "search": {"prs", "issues", "repos", "commits", "code"},
    "auth": {"status"},
    "label": {"list"},
}
# gh api is read-only only without a body/method/header-override.
GH_API_SAFE_FLAG = re.compile(
    r"^(-q|--jq|--paginate|--slurp|--template=|--cache|--include$|-i$|"
    r"--verbose$)")
GH_API_WRITE = re.compile(
    r"^(-X|--method|-f|--field|-F|--raw-field|--input|-H|--header)=?|"
    r"method-override", re.I)

FD_DANGEROUS = re.compile(r"^(-x|--exec|--exec-batch)", re.I)
RG_DANGEROUS = re.compile(r"^--pre(=|$)|^--hostname-bin", re.I)
DATE_DANGEROUS = re.compile(r"^(-s|--set)")


def _git_ok(parts):
    if len(parts) < 2:
        return True  # bare `git` prints help
    verb = parts[1].lower()
    args = parts[2:]
    if verb in GIT_LIST_ONLY:
        pat = GIT_LIST_ONLY[verb]
        return all(pat.match(a) for a in args)
    if verb == "remote":
        if not args or args[0] in ("-v", "--verbose"):
            return len(args) <= 1  # `git remote` / `remote -v` list only
        return args[0].lower() in GIT_SUBVERBS["remote"] and \
            all(not GIT_REMOTE_DANGEROUS.match(a)
                and not GIT_DANGEROUS_ARG.match(a) for a in args[1:])
    if verb in GIT_SUBVERBS:
        subs = GIT_SUBVERBS[verb]
        # `git reflog` bare defaults to `show`; `git stash` bare mutates.
        if verb == "reflog" and not args:
            return True
        return bool(args) and args[0].lower() in subs and \
            all(not GIT_DANGEROUS_ARG.match(a) for a in args[1:])
    if verb not in GIT_READONLY:
        return False
    extra = GIT_LSREMOTE_DANGEROUS if verb == "ls-remote" else None
    return all(not GIT_DANGEROUS_ARG.match(a)
               and not GIT_GREP_PAGER.match(a)
               and not (extra and extra.match(a)) for a in args)


def _gh_ok(parts):
    if len(parts) < 2:
        return True  # bare `gh` prints help
    noun = parts[1].lower()
    args = parts[2:]
    if noun == "api":
        return bool(args) and all(
            (not a.startswith("-")) or GH_API_SAFE_FLAG.match(a)
            for a in args
        ) and not any(GH_API_WRITE.match(a) for a in args)
    verbs = GH_NOUN_READS.get(noun)
    if verbs is None:
        return False
    return bool(args) and args[0].lower() in verbs and \
        all(not a.startswith("-X")
            and not re.match(r"^(-w|--web)", a) for a in args)


def _exec_verdict(command):
    cmd = command.strip()
    if not cmd or UNSAFE_CHARS.search(cmd):
        return False
    # Quote removal: the shell strips ALL quotes after tokenization, so
    # `--out""put` runs as `--output`. Normalize the same way per token.
    parts = [p.replace("'", "").replace('"', "") for p in cmd.split()]
    exe = parts[0].rsplit("/", 1)[-1].rsplit("\\", 1)[-1].lower()
    exe = re.sub(r"\.(exe|bat|cmd|ps1)$", "", exe)
    if exe in SAFE_BINARIES:
        return True
    if exe == "git":
        return _git_ok(parts)
    if exe == "gh":
        return _gh_ok(parts)
    if exe == "fd":
        return not any(FD_DANGEROUS.match(a) for a in parts[1:])
    if exe == "rg":
        return not any(RG_DANGEROUS.match(a) for a in parts[1:])
    if exe == "date":
        # args must be flags or +format; a bare MMDDhhmm positional sets time.
        return all(a.startswith("-") or a.startswith("+") for a in parts[1:]) \
            and not any(DATE_DANGEROUS.match(a) for a in parts[1:])
    if exe == "hostname":
        # positional or -F/--file sets the name; flag-only forms are reads.
        return all(a.startswith("-") and a not in ("-F", "--file")
                   for a in parts[1:])
    return False


def main():
    reconfigure = getattr(sys.stdin, "reconfigure", None)
    if reconfigure:
        try:
            reconfigure(encoding="utf-8", errors="replace")
        except (OSError, ValueError):
            pass
    try:
        data = json.load(sys.stdin)
    except (json.JSONDecodeError, EOFError, ValueError):
        return  # fail-open: no opinion
    if not isinstance(data, dict):
        return
    tool = data.get("tool_name", "")
    inp = data.get("tool_input") or {}
    if tool == "exec":
        cmd = inp.get("command", "") if isinstance(inp, dict) else ""
        if cmd and _exec_verdict(cmd):
            print(json.dumps({"decision": "approve",
                              "reason": "permission-gate: read-only command"}))
    # every other tool: no opinion -> user prompt proceeds


if __name__ == "__main__":
    try:
        main()
    except Exception:
        pass  # fail-open always
    sys.exit(0)
