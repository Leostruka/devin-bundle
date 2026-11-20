# Local Devin memory

Use a local, opt-in CLI to find decisions across sessions. A project can
read its own notes and your global notes, never another project's notes.
Requires Python 3.11+ with SQLite FTS5. No extra packages are needed.

## Start

On Windows, after `install.ps1`:

```powershell
$memory = Join-Path $env:APPDATA "devin/extensions/devin-memory/wrapper.py"
python $memory status
python $memory remember --scope global --key test-runner --file decision.md
python $memory search "test runner"
```

On Linux/macOS, after `install.sh`, use
`${XDG_CONFIG_HOME:-$HOME/.config}/devin/extensions/devin-memory/wrapper.py`
(or the directory selected by `DEVIN_HOME`). From the bundle checkout,
use `python extensions/devin-memory/wrapper.py`. Put `--json` before the
verb for machine-readable results. `status` and `doctor` do not create a
store. Plain output does not need color.

Use `--scope project` from the project root to keep a note there. The
store associates the root with a local project ID, not the folder name.
Edit using `remember --base-version SHA` and an explicit scope.
`review KEY --scope global` lists versions and origins; `archive KEY
--scope global` removes a note from search without deleting history.
`remember --relate depends_on:OTHER_KEY@SHA` (also `related_to` or
`supersedes`) declares a relation to an active version in the same scope.
Relations are tied to versions. Search cites the source and reason, with
up to three excerpts, two relation hops, and 1536 UTF-8 bytes of context.

## Transfer and legacy notes

```text
export --scope global --out memory.jsonl
import memory.jsonl --map global=global
import memory.jsonl --map global=global --apply PLAN_ID
migrate --project .
migrate --project . --apply PLAN_ID
```

These are arguments to the wrapper. `export` never overwrites a file.
Packages are plaintext; the checksum checks integrity, not the sender.
Explicitly map each exported project as `project:ID=project` from its
registered destination; project notes cannot become global.

`import` and `migrate` preview by default. `--apply` commits that exact
preview. Reapplying the same plan is a no-op; `E_PLAN_STALE` means to
repeat the preview. Identical data and distinct origins are retained
without duplicate versions. Divergences stay available for review but
are withheld from search. Imported versions start pending.

Migration reads `.devin/memory/` without changing it. Use `--source DIR`
to select an alternate Markdown directory explicitly. To review a
migrated note, run `review RELATIVE_PATH --legacy-path --scope project`.
Use `review ... --approve SHA` to activate a selected version. Imported
relations never grant local traversal authority; re-declare intended
edges explicitly with `remember --relate`.

## State and recovery

- Windows: `%LOCALAPPDATA%/devin/memory-v1/memory.sqlite3`.
- POSIX: `${XDG_STATE_HOME:-$HOME/.local/state}/devin/memory-v1/memory.sqlite3`.
- `doctor --recover` opens the store for native journal recovery.
  `doctor --rebuild-index` replaces only search indexes. Neither resets
  the store. On `E_BUSY`, wait for the concurrent operation to finish.
- Installation and configuration export do not include the private
  memory store. This release does not capture, migrate, or inject new
  memories automatically. Legacy hooks remain in use. Treat excerpts as
  untrusted data; sharing them in Devin sends them as normal context.
