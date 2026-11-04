#!/usr/bin/env bash
# Devin bundle installer (Linux / WSL / macOS).
# Installs global Devin CLI setup: AGENTS.md, agents/, skills/, config.json, scripts/, extensions/, mcp_config.json, credentials.toml
set -euo pipefail

BUNDLE_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BUNDLE_DIR="$BUNDLE_ROOT"

DRY_RUN=0
FORCE=0
BACKUP=0
RESTORE_SECRETS=0

usage() {
  cat <<EOF
Devin bundle installer (Linux / WSL / macOS)

Installs the full Devin CLI configuration from the bundle.

Usage: ./install.sh [--dry-run] [--force] [--backup] [--restore-secrets] [--help]

  --dry-run         Show what would happen without writing anything.
  --force           Overwrite existing files without prompting.
  --backup          Backup existing files before overwriting.
  --restore-secrets Opt in to installing credentials.toml and mcp_config.json
                    when they contain real (unmasked) values. MASKED values
                    cannot be restored automatically; restore them manually
                    from a backup.
  --help            Show this message.
EOF
}

for arg in "$@"; do
  case "$arg" in
    --dry-run)         DRY_RUN=1 ;;
    --force)           FORCE=1 ;;
    --backup)          BACKUP=1 ;;
    --restore-secrets) RESTORE_SECRETS=1 ;;
    --help|-h)         usage; exit 0 ;;
    *) echo "Unknown option: $arg"; usage; exit 1 ;;
  esac
done

if [[ ! -d "$BUNDLE_DIR" ]]; then echo "ERROR: bundle dir not found at $BUNDLE_ROOT" >&2; exit 1; fi

# --- Helpers ---
step() { printf "\n\033[36m[*] %s\033[0m\n" "$1"; }
ok()   { printf "    \033[32m[+] %s\033[0m\n" "$1"; }
skip() { printf "    \033[33m[~] %s\033[0m\n" "$1"; }
warn() { printf "    \033[33m[!] %s\033[0m\n" "$1"; }
err()  { printf "    \033[31m[x] %s\033[0m\n" "$1"; }

# --- sha256 tool detection ---
# Stock macOS ships shasum, not sha256sum. Without a hasher every hash
# comparison silently returns "" == "" and reports everything unchanged.
if command -v sha256sum &>/dev/null; then
  SHA256_CMD="sha256sum"
elif command -v shasum &>/dev/null; then
  SHA256_CMD="shasum -a 256"
elif command -v openssl &>/dev/null; then
  SHA256_CMD="openssl dgst -sha256 -r"
else
  echo "ERROR: no sha256 tool found (need sha256sum, shasum, or openssl)" >&2
  exit 1
fi

file_hash() {
  $SHA256_CMD "$1" 2>/dev/null | awk '{print $1}'
}

# dir_hash ignores __pycache__/ and *.pyc: bytecode caches are runtime
# artifacts, not payload, and are stripped from installed copies anyway.
dir_hash() {
  ( cd "$1" 2>/dev/null && find . -type f -not -path '*/__pycache__/*' -not -name '*.pyc' -print0 | xargs -0 $SHA256_CMD 2>/dev/null | sort | $SHA256_CMD | awk '{print $1}' )
}

# Same as dir_hash but skips .venv/ trees, cargo target/ dirs, and staged
# compiled artifacts (extensions derive these at install time).
dir_hash_ext() {
  ( cd "$1" 2>/dev/null && find . -type f -not -path '*/.venv/*' -not -path '*/target/*' -not -name '*.pyd' -not -name '*.so' -not -name '*.dylib' -not -path '*/__pycache__/*' -not -name '*.pyc' -print0 | xargs -0 $SHA256_CMD 2>/dev/null | sort | $SHA256_CMD | awk '{print $1}' )
}

# --- Single python interpreter resolution ---
# One detection point; every inline/child python call goes through `python`
# so python3-only and python-only hosts behave identically.
PY=""
if command -v python3 &>/dev/null; then
  PY="python3"
elif command -v python &>/dev/null; then
  PY="python"
fi
python() {
  if [[ -z "$PY" ]]; then
    echo "python: interpreter not found" >&2
    return 127
  fi
  "$PY" "$@"
}

# --- Skipped-step tracking (install receipt + end summary) ---
# warn-and-continue leaves degraded installs invisible; record each skip so
# the run ends with a durable receipt and a printed list of what did not happen.
INSTALL_SKIPS=()
record_skip() { INSTALL_SKIPS+=("$1"); }

backup_file() {
  local file="$1"
  local backup
  backup="${file}.backup.$(date +%Y%m%d_%H%M%S)"
  if [[ -f "$file" ]]; then
    if [[ $DRY_RUN -eq 1 ]]; then
      echo "$file (would backup to $backup)"
    else
      cp "$file" "$backup"
      ok "backed up $file"
    fi
  elif [[ -d "$file" ]]; then
    # Directories (skills, docs, extensions) need a recursive backup or
    # --backup silently does nothing before a destructive rm -rf.
    if [[ $DRY_RUN -eq 1 ]]; then
      echo "$file (would backup dir to $backup)"
    else
      cp -r "$file" "$backup"
      ok "backed up $file"
    fi
  fi
}

# Copy a directory tree into place minus runtime bytecode caches
# (__pycache__/, *.pyc) so stale .pyc files are never shipped to targets.
copy_tree_clean() {
  local src="$1" dst="$2"
  rm -rf "$dst"
  cp -r "$src" "$dst"
  find "$dst" -type d -name '__pycache__' -prune -exec rm -rf {} + 2>/dev/null || true
  find "$dst" -type f -name '*.pyc' -delete 2>/dev/null || true
}

# Restrict a secrets-bearing file to owner-read/write (0600).
restrict_secret_mode() {
  local file="$1"
  [[ -f "$file" ]] || return
  if [[ $DRY_RUN -eq 1 ]]; then
    skip "would chmod 600 $file"
  else
    chmod 600 "$file" 2>/dev/null || warn "could not chmod 600 $file"
  fi
}

contains_masked() {
  local file="$1"
  grep -q "MASKED" "$file" 2>/dev/null
}

# --- Expand {{APPDATA}}/devin placeholder in config.json ---
# The bundle's config.json uses a portable placeholder for the Devin home.
# At install time, replace the literal "{{APPDATA}}/devin" with the actual
# $DEVIN_HOME so hook commands resolve to the installed scripts directory.
# This works for both the default ~/.config/devin and custom DEVIN_HOME values.
expand_devin_home_in_config() {
  local file="$1"
  if [[ $DRY_RUN -eq 1 ]] || [[ ! -f "$file" ]]; then
    return
  fi
  if [[ -z "$PY" ]]; then
    warn "python not found; config.json may keep {{APPDATA}}/devin placeholder"
    record_skip "config.json {{APPDATA}}/devin placeholder expansion (python missing)"
    return
  fi
  DEVIN_HOME="$DEVIN_HOME" python -c 'import os,sys; h=os.environ["DEVIN_HOME"]; sys.stdout.write(sys.stdin.read().replace("{{APPDATA}}/devin", h))' < "$file" > "${file}.tmp" && mv "${file}.tmp" "$file"
}

# --- Strip BOM from file (if present) ---
# BOM (EF BB BF) in YAML frontmatter can prevent parsers from recognizing
# the `---` delimiter, causing model/name/allowed-tools fields to be ignored.
strip_bom() {
  local file="$1"
  if [[ ! -f "$file" ]]; then return; fi
  # Check if first 3 bytes are BOM (EF BB BF)
  if head -c 3 "$file" | od -A n -t x1 | grep -q "ef bb bf"; then
    if [[ $DRY_RUN -eq 1 ]]; then
      skip "would strip BOM from $(basename "$file")"
    else
      # Portable BOM strip: GNU `sed -i` syntax fails under BSD sed (macOS)
      # and BSD sed does not interpret \xEF escapes; tail -c +4 works on both.
      tail -c +4 "$file" > "${file}.bomtmp" && mv "${file}.bomtmp" "$file"
      ok "stripped BOM from $(basename "$file")"
    fi
  fi
}

# --- Case sensitivity detection ---
# Returns 0 (true) if case-sensitive, 1 (false) if case-insensitive.
is_case_sensitive() {
  local dir="$1"
  local tmp_lower="$dir/.casetest_$$"
  touch "$tmp_lower" 2>/dev/null || return 0  # assume sensitive on error
  if [[ -f "$dir/.CASETEST_$$" ]]; then
    rm -f "$tmp_lower"
    return 1  # case-insensitive
  else
    rm -f "$tmp_lower"
    return 0  # case-sensitive
  fi
}

# --- Dedup AGENTS.md case variants ---
# On case-sensitive FSs: removes agents.md (lowercase) if it exists as a
# separate file. On case-insensitive FSs (Windows/WSL /mnt/c, macOS default):
# AGENTS.md and agents.md are the same file -- warns about Devin CLI duplicate
# listing (known bug, not fixable from filesystem level).
dedup_agents_md() {
  local dir="$1"
  local label="$2"
  local canonical="$dir/AGENTS.md"
  local lower="$dir/agents.md"

  if [[ ! -f "$canonical" ]]; then return; fi

  if is_case_sensitive "$dir"; then
    if [[ -f "$lower" ]]; then
      warn "$label: found agents.md (lowercase) duplicate -- removing"
      if [[ $DRY_RUN -eq 1 ]]; then
        skip "would remove agents.md duplicate"
      else
        rm -f "$lower"
        ok "$label: removed agents.md duplicate (kept AGENTS.md)"
      fi
    fi
  else
    skip "$label: case-insensitive FS -- Devin CLI may list AGENTS.md twice (known bug, not fixable here)"
  fi
}

# --- Detect Devin config home ---
if [[ -z "${DEVIN_HOME:-}" ]]; then
  case "$(uname -s)" in
    MINGW*|MSYS*|CYGWIN*)
      # Git Bash on Windows: the Devin CLI reads %APPDATA%\devin, NOT
      # ~/.config/devin. Resolve via APPDATA (cygpath preferred; fall back
      # to backslash + drive-letter conversion so bash paths work).
      if [[ -n "${APPDATA:-}" ]]; then
        if command -v cygpath &>/dev/null; then
          DEVIN_HOME="$(cygpath -u "$APPDATA")/devin"
        else
          DEVIN_HOME="$(printf '%s' "$APPDATA" | sed 's|\\|/|g; s|^\([A-Za-z]\):|/\L\1|')/devin"
        fi
      else
        DEVIN_HOME="${XDG_CONFIG_HOME:-$HOME/.config}/devin"
      fi
      ;;
    *)
      DEVIN_HOME="${XDG_CONFIG_HOME:-$HOME/.config}/devin"
      ;;
  esac
fi

echo "================================================"
echo "  Devin Bundle Installer"
echo "  Target : $DEVIN_HOME"
echo "  Bundle : $BUNDLE_DIR"
[[ $DRY_RUN -eq 1 ]] && echo "  Mode   : DRY-RUN"
[[ $FORCE -eq 1 ]] && echo "  Force  : ENABLED"
[[ $BACKUP -eq 1 ]] && echo "  Backup : ENABLED"
[[ $RESTORE_SECRETS -eq 1 ]] && echo "  Secrets: RESTORE"
echo "================================================"

# --- Ensure target dirs ---
step "Ensure target directories"
if [[ $DRY_RUN -eq 1 ]]; then
  skip "would create $DEVIN_HOME (if missing)"
  skip "would create $DEVIN_HOME/agents (if missing)"
  skip "would create $DEVIN_HOME/skills (if missing)"
  skip "would create $DEVIN_HOME/scripts (if missing)"
else
  mkdir -p "$DEVIN_HOME" "$DEVIN_HOME/agents" "$DEVIN_HOME/skills" "$DEVIN_HOME/scripts"
  ok "created target directories"
fi

# --- 1. Install AGENTS.md ---
step "Install AGENTS.md"
agents_md_src="$BUNDLE_DIR/AGENTS.md"
agents_md_dst="$DEVIN_HOME/AGENTS.md"
if [[ -f "$agents_md_src" ]]; then
  if [[ -f "$agents_md_dst" ]]; then
    if diff -q "$agents_md_src" "$agents_md_dst" >/dev/null 2>&1; then
      ok "AGENTS.md already up-to-date"
    elif [[ $FORCE -eq 1 ]]; then
      if [[ $BACKUP -eq 1 ]]; then backup_file "$agents_md_dst"; fi
      if [[ $DRY_RUN -eq 1 ]]; then skip "would overwrite AGENTS.md"
      else cp "$agents_md_src" "$agents_md_dst"; ok "AGENTS.md installed"; fi
    else
      warn "AGENTS.md exists and differs. Use --force to overwrite."
    fi
  else
    if [[ $DRY_RUN -eq 1 ]]; then skip "would install AGENTS.md"
    else cp "$agents_md_src" "$agents_md_dst"; ok "AGENTS.md installed"; fi
  fi
else
  warn "AGENTS.md not found in bundle"
fi

# --- 1b. Dedup AGENTS.md case variants (Windows/WSL bug workaround) ---
step "Dedup AGENTS.md case variants"
dedup_agents_md "$DEVIN_HOME" "target"
dedup_agents_md "$BUNDLE_DIR" "bundle"

# --- 2. Install agents/ profiles ---
step "Install agents/ profiles"
agents_src="$BUNDLE_DIR/agents"
agents_dst="$DEVIN_HOME/agents"
if [[ -d "$agents_src" ]]; then
  for agent_file in "$agents_src"/*.md; do
    [[ -f "$agent_file" ]] || continue
    name="$(basename "$agent_file")"
    dst_file="$agents_dst/$name"
    if [[ -f "$dst_file" ]]; then
      if diff -q "$agent_file" "$dst_file" >/dev/null 2>&1; then
        ok "agents/$name already up-to-date"
      elif [[ $FORCE -eq 1 ]]; then
        if [[ $BACKUP -eq 1 ]]; then backup_file "$dst_file"; fi
        if [[ $DRY_RUN -eq 1 ]]; then skip "would overwrite agents/$name"
        else cp "$agent_file" "$dst_file"; ok "agents/$name installed"; fi
      else
        warn "agents/$name exists and differs. Use --force to overwrite."
      fi
    else
      if [[ $DRY_RUN -eq 1 ]]; then skip "would install agents/$name"
      else cp "$agent_file" "$dst_file"; ok "agents/$name installed"; fi
    fi
  done
else
  warn "agents/ not found in bundle"
fi

# --- 2b. Strip BOM from agent files (YAML frontmatter safety) ---
step "Strip BOM from agent files"
for agent_file in "$DEVIN_HOME"/agents/*.md; do
  [[ -f "$agent_file" ]] || continue
  strip_bom "$agent_file"
done

# --- 3. Install skills/ ---
step "Install skills/"
skills_src="$BUNDLE_DIR/skills"
skills_dst="$DEVIN_HOME/skills"
installed_skills=0; updated_skills=0; skipped_skills=0
if [[ -d "$skills_src" ]]; then
  for skill_dir in "$skills_src"/*/; do
    [[ -d "$skill_dir" ]] || continue
    name="$(basename "$skill_dir")"
    dst_dir="$skills_dst/$name"
    if [[ -d "$dst_dir" ]]; then
      src_h="$(dir_hash "$skill_dir")"
      dst_h="$(dir_hash "$dst_dir")"
      if [[ "$src_h" == "$dst_h" ]]; then
        ok "skills/$name (unchanged)"
        skipped_skills=$((skipped_skills+1))
      elif [[ $FORCE -eq 1 ]]; then
        if [[ $BACKUP -eq 1 ]]; then backup_file "$dst_dir"; fi
        if [[ $DRY_RUN -eq 1 ]]; then skip "would update skills/$name"
        else copy_tree_clean "$skill_dir" "$dst_dir"; ok "skills/$name updated"; fi
        updated_skills=$((updated_skills+1))
      else
        warn "skills/$name exists and differs. Use --force to update."
      fi
    else
      if [[ $DRY_RUN -eq 1 ]]; then skip "would install skills/$name"
      else copy_tree_clean "$skill_dir" "$dst_dir"; ok "skills/$name installed"; fi
      installed_skills=$((installed_skills+1))
    fi
  done
else
  warn "skills/ not found in bundle"
fi

# --- 4. Install config.json (merge, preserve org_id) ---
step "Install config.json"
config_src="$BUNDLE_DIR/config.json"
config_dst="$DEVIN_HOME/config.json"
if [[ -f "$config_src" ]]; then
  if [[ -f "$config_dst" ]]; then
    if [[ $FORCE -eq 1 ]]; then
      if [[ $BACKUP -eq 1 ]]; then backup_file "$config_dst"; fi
      if [[ $DRY_RUN -eq 1 ]]; then skip "would overwrite config.json"
      else cp "$config_src" "$config_dst"; expand_devin_home_in_config "$config_dst"; ok "config.json installed (force)"; fi
    else
      # Merge: recursive deep-merge, local settings win (matches
      # install.ps1 Merge-Hashtables semantics). jq `*` recurses objects,
      # so local-only keys (theme, shell prefs, devin.org_id) survive and
      # bundle values fill the gaps.
      if command -v jq &>/dev/null; then
        if [[ $DRY_RUN -eq 1 ]]; then skip "would merge config.json (deep-merge, local wins)"
        else
          if jq -s '.[0] * .[1]' "$config_src" "$config_dst" > "${config_dst}.tmp" 2>/dev/null; then
            mv "${config_dst}.tmp" "$config_dst"
            expand_devin_home_in_config "$config_dst"
            ok "config.json merged (deep-merge, local settings preserved)"
          else
            rm -f "${config_dst}.tmp"
            warn "config.json merge failed (invalid JSON?) - keeping existing file"
            record_skip "config.json merge (jq merge failed)"
          fi
        fi
      else
        # No lossy sed fallback: regex-merging JSON silently corrupts
        # nested values (e.g. devin.org_id). Skip loudly instead.
        warn "jq not found; skipping config.json merge (install jq, or re-run with --force to overwrite)"
        record_skip "config.json merge (jq missing)"
      fi
    fi
  else
    if [[ $DRY_RUN -eq 1 ]]; then skip "would install config.json"
    else cp "$config_src" "$config_dst"; expand_devin_home_in_config "$config_dst"; ok "config.json installed"; fi
  fi
else
  warn "config.json not found in bundle"
fi

# --- 4a. User hooks rendered from hooks.v1.json (single source) ---
# hooks.v1.json is authored with project-relative `python scripts/...` commands;
# user-level hooks need absolute paths -- render and inject into config.json.hooks.
step "Render config.json hooks from hooks.v1.json"
if [[ -f "$BUNDLE_DIR/hooks.v1.json" && -f "$config_dst" ]]; then
  if [[ $DRY_RUN -eq 1 ]]; then
    skip "would render config.json hooks from hooks.v1.json"
  elif [[ -n "$PY" ]]; then
    # The Devin CLI is a native process; on Git Bash/MSYS a POSIX /c/...
    # DEVIN_HOME renders hook commands Windows python cannot open. Pass a
    # Windows-style home so rendered paths are spawnable.
    render_home="$DEVIN_HOME"
    case "$(uname -s)" in
      MINGW*|MSYS*|CYGWIN*)
        if command -v cygpath &>/dev/null; then
          render_home="$(cygpath -w "$DEVIN_HOME")"
        fi
        ;;
    esac
    if python "$BUNDLE_DIR/scripts/render-user-hooks.py" "$render_home" --merge "$config_dst"; then
      ok "config.json hooks rendered from hooks.v1.json"
      # Sanity: rendered commands point at $DEVIN_HOME/scripts; a missing
      # payload there means fail_closed guards would block tool calls.
      if [[ ! -f "$DEVIN_HOME/scripts/pre-exec-guard.py" ]]; then
        warn "scripts/pre-exec-guard.py missing at $DEVIN_HOME -- rendered hook commands may not resolve"
        record_skip "hook command payload check (scripts/pre-exec-guard.py missing)"
      fi
    else
      warn "render-user-hooks.py failed -- hooks not updated"
      record_skip "config.json hooks render (render-user-hooks.py failed)"
    fi
  else
    warn "python not found -- config.json hooks not rendered"
    record_skip "config.json hooks render (python missing)"
  fi
fi

# --- 5. Project hooks template ---
step "Project hooks template"
skip "hooks.v1.json is project-level; copy it into .devin/ when needed"

# --- 6. Install scripts/ ---
step "Install scripts/"
scripts_src="$BUNDLE_DIR/scripts"
scripts_dst="$DEVIN_HOME/scripts"
if [[ -d "$scripts_src" ]]; then
  for script_file in "$scripts_src"/*; do
    [[ -f "$script_file" ]] || continue
    name="$(basename "$script_file")"
    dst_file="$scripts_dst/$name"
    if [[ -f "$dst_file" ]]; then
      if diff -q "$script_file" "$dst_file" >/dev/null 2>&1; then
        ok "scripts/$name already up-to-date"
      elif [[ $FORCE -eq 1 ]]; then
        if [[ $BACKUP -eq 1 ]]; then backup_file "$dst_file"; fi
        if [[ $DRY_RUN -eq 1 ]]; then skip "would overwrite scripts/$name"
        else cp "$script_file" "$dst_file"; ok "scripts/$name installed"; fi
      else
        warn "scripts/$name exists and differs. Use --force to overwrite."
      fi
    else
      if [[ $DRY_RUN -eq 1 ]]; then skip "would install scripts/$name"
      else cp "$script_file" "$dst_file"; ok "scripts/$name installed"; fi
    fi
  done
else
  warn "scripts/ not found in bundle"
fi

# --- 6a. Install data/ (model context windows, thresholds) ---
step "Install data/ (model context windows)"
data_src="$BUNDLE_DIR/data"
data_dst="$DEVIN_HOME/data"
if [[ -d "$data_src" ]]; then
  [[ $DRY_RUN -eq 1 ]] || mkdir -p "$data_dst"
  for data_file in "$data_src"/*; do
    [[ -f "$data_file" ]] || continue
    name="$(basename "$data_file")"
    dst_file="$data_dst/$name"
    if [[ -f "$dst_file" ]]; then
      if diff -q "$data_file" "$dst_file" >/dev/null 2>&1; then
        ok "data/$name already up-to-date"
      elif [[ $FORCE -eq 1 ]]; then
        if [[ $BACKUP -eq 1 ]]; then backup_file "$dst_file"; fi
        if [[ $DRY_RUN -eq 1 ]]; then skip "would overwrite data/$name"
        else cp "$data_file" "$dst_file"; ok "data/$name installed"; fi
      else
        warn "data/$name exists and differs. Use --force to overwrite."
      fi
    else
      if [[ $DRY_RUN -eq 1 ]]; then skip "would install data/$name"
      else cp "$data_file" "$dst_file"; ok "data/$name installed"; fi
    fi
  done
else
  warn "data/ not found in bundle"
fi

# --- 7. Install mcp_config.json (skip if masked) ---
step "Install mcp_config.json"
mcp_src="$BUNDLE_DIR/mcp_config.json"
mcp_dst="$DEVIN_HOME/mcp_config.json"
if [[ -f "$mcp_src" ]]; then
  if contains_masked "$mcp_src"; then
    if [[ $FORCE -eq 1 ]]; then
      # ps1 parity: -Force installs the masked file so server entries/URLs
      # land; tokens are MASKED placeholders to fill in manually.
      if [[ -f "$mcp_dst" && $BACKUP -eq 1 ]]; then backup_file "$mcp_dst"; fi
      if [[ $DRY_RUN -eq 1 ]]; then skip "would install mcp_config.json (MASKED placeholders)"
      else
        cp "$mcp_src" "$mcp_dst"
        restrict_secret_mode "$mcp_dst"
        ok "mcp_config.json installed with MASKED placeholders -- fill tokens manually"
      fi
    else
      warn "mcp_config.json contains MASKED values, skipping (use --force to install placeholders)"
      record_skip "mcp_config.json install (MASKED values; needs --force)"
    fi
  else
    if [[ -f "$mcp_dst" ]]; then
      if diff -q "$mcp_src" "$mcp_dst" >/dev/null 2>&1; then
        ok "mcp_config.json already up-to-date"
      elif [[ $FORCE -eq 1 ]]; then
        if [[ $BACKUP -eq 1 ]]; then backup_file "$mcp_dst"; fi
        if [[ $DRY_RUN -eq 1 ]]; then skip "would overwrite mcp_config.json"
        else cp "$mcp_src" "$mcp_dst"; restrict_secret_mode "$mcp_dst"; ok "mcp_config.json installed"; fi
      else
        warn "mcp_config.json exists and differs. Use --force to overwrite."
      fi
    else
      if [[ $DRY_RUN -eq 1 ]]; then skip "would install mcp_config.json"
      else cp "$mcp_src" "$mcp_dst"; restrict_secret_mode "$mcp_dst"; ok "mcp_config.json installed"; fi
    fi
  fi
else
  warn "mcp_config.json not found in bundle"
fi

# --- 8. Install credentials.toml (only with --restore-secrets) ---
step "Install credentials.toml"
creds_src="$BUNDLE_DIR/credentials.toml"
creds_dst="$DEVIN_HOME/credentials.toml"
if [[ -f "$creds_src" ]]; then
  if contains_masked "$creds_src"; then
    if [[ $RESTORE_SECRETS -eq 1 ]]; then
      warn "credentials.toml contains MASKED values, cannot restore automatically"
      warn "You must manually restore credentials.toml from your backup"
    else
      warn "credentials.toml contains MASKED values, skipping (use --restore-secrets to attempt restore)"
    fi
    record_skip "credentials.toml install (MASKED values)"
  elif [[ $RESTORE_SECRETS -eq 0 ]]; then
    # Never plant real secrets without explicit opt-in (ps1 parity).
    warn "credentials.toml contains real values; skipping (use --restore-secrets to install)"
    record_skip "credentials.toml install (real values; needs --restore-secrets)"
  else
    if [[ -f "$creds_dst" ]]; then
      if diff -q "$creds_src" "$creds_dst" >/dev/null 2>&1; then
        ok "credentials.toml already up-to-date"
      elif [[ $FORCE -eq 1 ]]; then
        if [[ $BACKUP -eq 1 ]]; then backup_file "$creds_dst"; fi
        if [[ $DRY_RUN -eq 1 ]]; then skip "would overwrite credentials.toml"
        else cp "$creds_src" "$creds_dst"; restrict_secret_mode "$creds_dst"; ok "credentials.toml installed"; fi
      else
        warn "credentials.toml exists and differs. Use --force to overwrite."
      fi
    else
      if [[ $DRY_RUN -eq 1 ]]; then skip "would install credentials.toml"
      else cp "$creds_src" "$creds_dst"; restrict_secret_mode "$creds_dst"; ok "credentials.toml installed"; fi
    fi
  fi
else
  warn "credentials.toml not found in bundle"
fi

# --- 8b. Install extensions/ (local tools, e.g. computer-use) ---
step "Install extensions/ (local tools)"
ext_src="$BUNDLE_DIR/extensions"
ext_dst="$DEVIN_HOME/extensions"
if [[ -d "$ext_src" ]]; then
  for ext_dir in "$ext_src"/*/; do
    [[ -d "$ext_dir" ]] || continue
    name="$(basename "$ext_dir")"
    if [[ -z "$(find "$ext_dir" -mindepth 1 -type f -print -quit 2>/dev/null)" ]]; then
      skip "extensions/$name is empty"
      continue
    fi
    dst_dir="$ext_dst/$name"
    if [[ -d "$dst_dir" ]]; then
      src_h="$(dir_hash_ext "$ext_dir")"
      dst_h="$(dir_hash_ext "$dst_dir")"
      if [[ "$src_h" == "$dst_h" ]]; then
        ok "extensions/$name (unchanged)"
      elif [[ $FORCE -eq 1 ]]; then
        if [[ $BACKUP -eq 1 ]]; then backup_file "$dst_dir"; fi
        if [[ $DRY_RUN -eq 1 ]]; then skip "would update extensions/$name"
        else rm -rf "$dst_dir"; mkdir -p "$dst_dir"; tar -C "$ext_dir" --exclude='./.venv' --exclude='./target' -cf - . | tar -C "$dst_dir" -xf -; ok "extensions/$name updated"; fi
      else
        warn "extensions/$name exists and differs. Use --force to update."
      fi
    else
      if [[ $DRY_RUN -eq 1 ]]; then skip "would install extensions/$name"
      else mkdir -p "$dst_dir"; tar -C "$ext_dir" --exclude='./.venv' --exclude='./target' -cf - . | tar -C "$dst_dir" -xf -; ok "extensions/$name installed"; fi
    fi
  done

  # --- 8c. extension Python deps (isolated venv, no system/user-site) ---
  for ext_name in computer-use scrape-tools; do
    ext_dir="$ext_dst/$ext_name"
    [[ -f "$ext_dir/requirements.txt" ]] || continue
    if [[ -z "$PY" ]]; then
      warn "python not found - skipping $ext_name venv (scripts need pip deps)"
      record_skip "$ext_name venv creation (python missing)"
    elif [[ $DRY_RUN -eq 1 ]]; then
      skip "would create venv at $ext_dir/.venv and pip install -r requirements.txt"
    else
      venv_py="$ext_dir/.venv/bin/python"
      [[ -x "$venv_py" ]] || venv_py="$ext_dir/.venv/Scripts/python.exe"
      if [[ ! -x "$venv_py" ]]; then
        "$PY" -m venv "$ext_dir/.venv"
        venv_py="$ext_dir/.venv/bin/python"
        [[ -x "$venv_py" ]] || venv_py="$ext_dir/.venv/Scripts/python.exe"
      fi
      if "$venv_py" -m pip install --quiet --disable-pip-version-check -r "$ext_dir/requirements.txt"; then
        ok "$ext_name deps installed in $ext_dir/.venv"
      else
        warn "$ext_name pip install failed"
      fi
    fi
  done

  # --- 8d. rust-core compiled extensions (optional toolchain, non-blocking) ---
  rc_src="$ext_src/rust-core"
  rc_dir="$ext_dst/rust-core"
  if [[ -f "$rc_src/Cargo.toml" ]]; then
    if ! command -v cargo &>/dev/null; then
      warn "cargo/rustc not found -- skipping rust-core build (install Rust toolchain to enable hybrid extensions)"
      record_skip "rust-core build (cargo missing)"
    elif [[ $DRY_RUN -eq 1 ]]; then
      skip "would run: cargo build --release in $rc_dir and stage .so artifacts"
    else
      if cargo build --release --quiet --manifest-path "$rc_dir/Cargo.toml"; then
        staged=0
        for lib in "$rc_dir"/target/release/*.so "$rc_dir"/target/release/*.dylib "$rc_dir"/target/release/*.dll; do
          [[ -f "$lib" ]] || continue
          base="$(basename "$lib")"            # libfast_math.so / libfast_math.dylib / fast_math.dll
          mod="${base#lib}"                    # fast_math.so / fast_math.dylib / fast_math.dll
          case "$mod" in
            *.dylib) mod="${mod%.dylib}.so" ;; # fast_math.so
            *.dll)   mod="${mod%.dll}.pyd" ;;  # fast_math.pyd (Python ext suffix on Windows)
          esac
          cp "$lib" "$rc_dir/$mod"
          staged=$((staged+1))
          ok "rust extension staged: $mod"
        done
        [[ $staged -eq 0 ]] && warn "cargo build ok but no cdylib artifacts found in target/release"
      else
        warn "rust-core cargo build failed -- continuing without compiled extensions"
      fi
    fi
  fi
else
  warn "extensions/ not found in bundle"
fi

# --- 8e. Install docs/ (bundle docs; sources dissolved under .devin/) ---
step "Install docs/"
docs_dst="$DEVIN_HOME/docs"
docs_seen=0
for part in docs plans templates; do
  docs_src="$BUNDLE_DIR/.devin/$part"
  part_dst="$docs_dst"
  [[ "$part" != "docs" ]] && part_dst="$docs_dst/$part"
  [[ -d "$docs_src" ]] || continue
  docs_seen=1
  if [[ -d "$part_dst" ]]; then
    src_h="$(dir_hash "$docs_src")"
    dst_h="$(dir_hash "$part_dst")"
    if [[ "$src_h" == "$dst_h" ]]; then
      ok "docs/$part (unchanged)"
    elif [[ $FORCE -eq 1 ]]; then
      if [[ $BACKUP -eq 1 ]]; then backup_file "$part_dst"; fi
      if [[ $DRY_RUN -eq 1 ]]; then skip "would update docs/$part"
      else copy_tree_clean "$docs_src" "$part_dst"; ok "docs/$part updated"; fi
    else
      warn "docs/$part exists and differs. Use --force to update."
    fi
  else
    if [[ $DRY_RUN -eq 1 ]]; then skip "would install docs/$part"
    else mkdir -p "$(dirname "$part_dst")"; copy_tree_clean "$docs_src" "$part_dst"; ok "docs/$part installed"; fi
  fi
done
[[ $docs_seen -eq 0 ]] && warn ".devin/{docs,plans,templates} not found in bundle"

# --- 9. Summary ---
step "Summary"
echo "    Skills installed : $installed_skills"
echo "    Skills updated   : $updated_skills"
echo "    Skills unchanged : $skipped_skills"
echo "    Config: AGENTS.md, agents/, config.json, scripts/, data/, docs/, extensions/, mcp_config.json, credentials.toml"

# --- Skipped-step report + install receipt ---
# warn-and-continue is invisible after scrollback; list every degraded step
# and persist a receipt so a partial install is auditable later.
if [[ ${#INSTALL_SKIPS[@]} -gt 0 ]]; then
  step "Skipped steps"
  for s in "${INSTALL_SKIPS[@]}"; do
    echo "    - $s"
  done
fi
if [[ $DRY_RUN -eq 0 ]]; then
  receipt="$DEVIN_HOME/.install-receipt.json"
  {
    printf '{\n  "timestamp": "%s",\n  "bundle": "%s",\n  "skipped": [\n' "$(date -u +%Y-%m-%dT%H:%M:%SZ 2>/dev/null || date +%Y-%m-%dT%H:%M:%S)" "$BUNDLE_DIR"
    for i in "${!INSTALL_SKIPS[@]}"; do
      sep=","; [[ $i -eq $((${#INSTALL_SKIPS[@]} - 1)) ]] && sep=""
      printf '    "%s"%s\n' "${INSTALL_SKIPS[$i]//\"/}" "$sep"
    done
    printf '  ]\n}\n'
  } > "$receipt" 2>/dev/null || warn "could not write install receipt to $receipt"
fi

if [[ $DRY_RUN -eq 1 ]]; then
  printf "\n\033[33mDry-run complete. Re-run without --dry-run to apply.\033[0m\n"
else
  printf "\n\033[32mDone. Restart Devin CLI to pick up new configuration.\033[0m\n"
  if command -v devin >/dev/null 2>&1; then
    step "devin doctor"
    devin doctor
    # CLI version drift notice: adequacao plans pin a validated version;
    # warn (non-blocking) when the installed CLI has moved past it.
    ident="$BUNDLE_DIR/data/bundle-identity.json"
    if [[ -f "$ident" && -n "$PY" ]]; then
      want="$(python -c 'import json,sys; print(json.load(open(sys.argv[1],encoding="utf-8-sig")).get("validated_cli_version",""))' "$ident" 2>/dev/null || true)"
      have="$(devin --version 2>/dev/null | grep -oE '[0-9]+\.[0-9]+\.[0-9]+' | head -1 || true)"
      if [[ -n "$want" && -n "$have" && "$want" != "$have" ]]; then
        warn "devin CLI $have differs from bundle-validated $want -- check the latest .devin/plans adequacao doc"
      fi
    fi
  fi
fi
