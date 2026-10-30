---
name: shell-safe
description: Use whenever running shell commands or writing .sh/.bash scripts. Prevents blanked files, wrong-directory deletes, and silent failures: same-file redirect truncation, empty-variable rm -rf, unquoted expansion, pipe exit-code swallowing, cd-then-delete traps, sed -i portability, tarbombs, verify-after-write discipline.
triggers: [user, model]
allowed-tools: [read, exec, write, edit, grep]
---

# Shell Safe

Sibling of `powershell-safe`: same class of disaster, other shell. The exec tool runs bash (Git Bash on Windows), so most commands pass through here.

## Rule zero: file content does not go through the shell

Use `write`/`edit` tools for real files. Never:

- `cat << EOF > file.py` for project files.
- `echo "..." > config.json`.
- `sed -i` / `awk > file` for edits the `edit` tool does better.

Redirect only for disposable output (logs, dumps).

## Same file, read and written

```bash
cat config.txt | sed 's/a/b/' > config.txt   # config.txt BLANKED
grep foo app.log > app.log                    # app.log BLANKED
```

The shell opens `config.txt` for write (truncating) before `cat` runs. Safe patterns:

```bash
# 1. Temp + move
sed 's/a/b/' config.txt > config.txt.tmp && mv config.txt.tmp config.txt

# 2. Read first (small files)
c=$(cat config.txt); printf '%s' "${c//a/b}" > config.txt

# 3. sponge (moreutils) if available
sed 's/a/b/' config.txt | sponge config.txt
```

Note the `&&`: if `sed` fails, `mv` does not run and the original survives. With `;` it would overwrite with nothing.

## rm -rf with empty variable

```bash
rm -rf "$DIR/"      # DIR empty -> rm -rf /
rm -rf $DIR/*       # DIR empty -> rm -rf /*
```

Mandatory defenses:

```bash
: "${DIR:?DIR empty, aborting}" && rm -rf "$DIR"
# or
[ -n "$DIR" ] && [ -d "$DIR" ] || exit 1
```

- Always `"$VAR"` double-quoted (unquoted, spaces split into args and empties vanish silently).
- In scripts: `set -u` makes undefined variables an error, not "".

## cd then delete: order matters

```bash
cd build; rm -rf *        # if cd fails, rm runs in CURRENT dir
cd build && rm -rf *      # correct: rm only runs if cd worked
```

Better: do not depend on cwd. `rm -rf build/*` or `find build -mindepth 1 -delete`.

## Pipe swallows exit codes

```bash
failing_cmd | tee log.txt ; echo $?   # 0 (exit of tee!)
```

- `$?` in a pipe is the LAST command's exit.
- `set -o pipefail` makes the pipe return the first error.
- `cmd1 | cmd2 && next` without pipefail continues even with cmd1 dead.

## Scripts: minimum boilerplate

```bash
#!/usr/bin/env bash
set -euo pipefail    # -e stop on first error, -u undefined var = error,
                     # pipefail = pipes propagate failures
```

Without it, a script continues after errors and later steps run on broken state.

## Treacherous globbing

```bash
for f in *.txt; do ...    # no match: iterates the literal string "*.txt"
```

In delete/process loops, a literal `*.txt` reaches later steps as a nonexistent file. Defense: `shopt -s nullglob` or `[ -e "$f" ] || continue`.

## Silent overwrite

- `mv a b` overwrites `b` without asking; `cp` too. Use `-n` (no-clobber) or `-i`.
- `>` truncates; `>>` appends. Wrong operator = blanked file or duplicated log.
- `>` follows symlinks: redirecting to a symlink overwrites its target.

## find -delete / xargs rm: look before destroying

```bash
find . -name "*.tmp" -delete          # blind
find . -name "*.tmp" -print -delete   # delete showing what matched
```

`xargs` without `-0` breaks on names with spaces: `find . -print0 | xargs -0 rm`.

## chmod/chown and sudo

- `chmod -R 777` never: it masks the real problem (usually ownership or umask).
- `sudo` does not work in the exec tool (no TTY for password). If root is needed, ask the user to run it.
- `kill -9` first kills without cleanup. `kill` (TERM) first, `-9` only if it survives.

## Extraction and copy

- `tar -xzf pkg.tar.gz` may be a tarbomb (files into cwd root). `tar -tzf pkg.tar.gz | head` first.
- `rsync a/ b/` != `rsync a b/`: trailing slash changes semantics. `--dry-run` before destructive rsync (`--delete`).
- `scp`/`ssh host cmd`: quoting passes through TWO shells (local and remote). Print destructive ssh commands before running.

## Portability

- `sed -i` differs: GNU `sed -i 's/a/b/' f` vs BSD/macOS `sed -i '' 's/a/b/' f`. Portable: `sed -i.bak 's/a/b/' f` (works on both, creates .bak).
- `date`, `stat`, `readlink -f` also differ GNU vs BSD.
- CRLF/LF: Windows-originated `\r\n` breaks shebang (`bad interpreter`). `file script.sh` shows it; `sed -i 's/\r$//'` fixes it.

## Post-operation verification

- After redirect writes: `wc -l file` + `head`.
- After delete/move: `ls` the directory.
- After a script: check real exit code (`echo $?` immediately, before another command overwrites it).

## Checklist

1. Real file content? -> `write`/`edit` tool, not shell.
2. Same file on both ends of the pipe? -> temp+move.
3. Variable in rm/mv/cd checked non-empty? Double quotes?
4. `cd` followed by destructive op uses `&&`?
5. Script has `set -euo pipefail`?
6. Blind delete? `-print`/dry-run first.
7. Wrote? Read it back (`wc -l`, `head`)?

## Cascade

- `powershell-safe`: sibling skill, same concepts, other syntax.
- `edge-cases` before operations on real data/state.
