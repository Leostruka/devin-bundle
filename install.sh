#!/usr/bin/env bash
# Devin bundle installer (Linux / WSL / macOS).
# Installs global Devin CLI setup: AGENTS.md, agents/, skills/, config.json, scripts/, mcp_config.json, credentials.toml
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
  --restore-secrets Restore masked values in credentials.toml and mcp_config.json.
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

file_hash() {
  sha256sum "$1" 2>/dev/null | cut -d' ' -f1
}

dir_hash() {
  ( cd "$1" 2>/dev/null && find . -type f | sort | xargs sha256sum 2>/dev/null | sha256sum | cut -d' ' -f1 )
}

backup_file() {
  local file="$1"
  if [[ -f "$file" ]]; then
    local backup="${file}.backup.$(date +%Y%m%d_%H%M%S)"
    if [[ $DRY_RUN -eq 1 ]]; then
      echo "$file (would backup to $backup)"
    else
      cp "$file" "$backup"
      ok "backed up $file"
    fi
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
  local py
  if command -v python3 &>/dev/null; then
    py=python3
  elif command -v python &>/dev/null; then
    py=python
  else
    warn "python not found; config.json may keep {{APPDATA}}/devin placeholder"
    return
  fi
  DEVIN_HOME="$DEVIN_HOME" "$py" -c 'import os,sys; h=os.environ["DEVIN_HOME"]; sys.stdout.write(sys.stdin.read().replace("{{APPDATA}}/devin", h))' < "$file" > "${file}.tmp" && mv "${file}.tmp" "$file"
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
      sed -i '1s/^\xEF\xBB\xBF//' "$file"
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
# AGENTS.md and agents.md are the same file — warns about Devin CLI duplicate
# listing (known bug, not fixable from filesystem level).
dedup_agents_md() {
  local dir="$1"
  local label="$2"
  local canonical="$dir/AGENTS.md"
  local lower="$dir/agents.md"

  if [[ ! -f "$canonical" ]]; then return; fi

  if is_case_sensitive "$dir"; then
    if [[ -f "$lower" ]]; then
      warn "$label: found agents.md (lowercase) duplicate — removing"
      if [[ $DRY_RUN -eq 1 ]]; then
        skip "would remove agents.md duplicate"
      else
        rm -f "$lower"
        ok "$label: removed agents.md duplicate (kept AGENTS.md)"
      fi
    fi
  else
    skip "$label: case-insensitive FS — Devin CLI may list AGENTS.md twice (known bug, not fixable here)"
  fi
}

# --- Detect Devin config home ---
if [[ -n "${DEVIN_HOME:-}" ]]; then
  DEVIN_HOME="$DEVIN_HOME"
else
  DEVIN_HOME="${XDG_CONFIG_HOME:-$HOME/.config}/devin"
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
        else rm -rf "$dst_dir"; cp -r "$skill_dir" "$dst_dir"; ok "skills/$name updated"; fi
        updated_skills=$((updated_skills+1))
      else
        warn "skills/$name exists and differs. Use --force to update."
      fi
    else
      if [[ $DRY_RUN -eq 1 ]]; then skip "would install skills/$name"
      else cp -r "$skill_dir" "$dst_dir"; ok "skills/$name installed"; fi
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
      # Merge: preserve local org_id and devin.org_id
      if command -v jq &>/dev/null; then
        if [[ $DRY_RUN -eq 1 ]]; then skip "would merge config.json (preserve org_id)"
        else
          # Extract local org_id values
          local_org_id=$(jq -r '.org_id // empty' "$config_dst" 2>/dev/null || echo "")
          local_devin_org_id=$(jq -r '.devin.org_id // empty' "$config_dst" 2>/dev/null || echo "")
          # Copy bundle config
          cp "$config_src" "$config_dst"
          # Force org_id to MASKED (never inherit bundle's), then override with local if real
          jq '.org_id = "MASKED" | .devin.org_id = "MASKED"' "$config_dst" > "${config_dst}.tmp" && mv "${config_dst}.tmp" "$config_dst"
          if [[ -n "$local_org_id" && "$local_org_id" != "MASKED" ]]; then
            jq --arg org "$local_org_id" '.org_id = $org' "$config_dst" > "${config_dst}.tmp" && mv "${config_dst}.tmp" "$config_dst"
          fi
          if [[ -n "$local_devin_org_id" && "$local_devin_org_id" != "MASKED" ]]; then
            jq --arg org "$local_devin_org_id" '.devin.org_id = $org' "$config_dst" > "${config_dst}.tmp" && mv "${config_dst}.tmp" "$config_dst"
          fi
          expand_devin_home_in_config "$config_dst"
          ok "config.json merged (preserved org_id, forced MASKED default)"
        fi
      else
        # Fallback: simple sed-based merge
        if [[ $DRY_RUN -eq 1 ]]; then skip "would merge config.json (sed fallback)"
        else
          # Extract org_id using sed
          local_org_id=$(grep -o '"org_id"[[:space:]]*:[[:space:]]*"[^"]*"' "$config_dst" 2>/dev/null | head -1 | cut -d'"' -f4 || echo "")
          cp "$config_src" "$config_dst"
          # Force org_id to MASKED (never inherit bundle's)
          if [[ "$(uname)" == "Darwin" ]]; then
            sed -i '' 's/"org_id"[[:space:]]*:[[:space:]]*"[^"]*"/"org_id": "MASKED"/g' "$config_dst"
          else
            sed -i 's/"org_id"[[:space:]]*:[[:space:]]*"[^"]*"/"org_id": "MASKED"/g' "$config_dst"
          fi
          # Override with local if real
          if [[ -n "$local_org_id" && "$local_org_id" != "MASKED" ]]; then
            if [[ "$(uname)" == "Darwin" ]]; then
              sed -i '' 's/"org_id"[[:space:]]*:[[:space:]]*"[^"]*"/"org_id": "'"$local_org_id"'"/g' "$config_dst"
            else
              sed -i 's/"org_id"[[:space:]]*:[[:space:]]*"[^"]*"/"org_id": "'"$local_org_id"'"/g' "$config_dst"
            fi
          fi
          expand_devin_home_in_config "$config_dst"
          ok "config.json merged (sed fallback, forced MASKED default)"
        fi
      fi
    fi
  else
    if [[ $DRY_RUN -eq 1 ]]; then skip "would install config.json"
    else cp "$config_src" "$config_dst"; expand_devin_home_in_config "$config_dst"; ok "config.json installed"; fi
  fi
else
  warn "config.json not found in bundle"
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

# --- 7. Install mcp_config.json (skip if masked) ---
step "Install mcp_config.json"
mcp_src="$BUNDLE_DIR/mcp_config.json"
mcp_dst="$DEVIN_HOME/mcp_config.json"
if [[ -f "$mcp_src" ]]; then
  if contains_masked "$mcp_src"; then
    warn "mcp_config.json contains MASKED values, skipping (cannot restore)"
    if [[ $RESTORE_SECRETS -eq 1 ]]; then
      warn "Use --restore-secrets to restore from local file (not implemented yet)"
    fi
  else
    if [[ -f "$mcp_dst" ]]; then
      if diff -q "$mcp_src" "$mcp_dst" >/dev/null 2>&1; then
        ok "mcp_config.json already up-to-date"
      elif [[ $FORCE -eq 1 ]]; then
        if [[ $BACKUP -eq 1 ]]; then backup_file "$mcp_dst"; fi
        if [[ $DRY_RUN -eq 1 ]]; then skip "would overwrite mcp_config.json"
        else cp "$mcp_src" "$mcp_dst"; ok "mcp_config.json installed"; fi
      else
        warn "mcp_config.json exists and differs. Use --force to overwrite."
      fi
    else
      if [[ $DRY_RUN -eq 1 ]]; then skip "would install mcp_config.json"
      else cp "$mcp_src" "$mcp_dst"; ok "mcp_config.json installed"; fi
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
  else
    if [[ -f "$creds_dst" ]]; then
      if diff -q "$creds_src" "$creds_dst" >/dev/null 2>&1; then
        ok "credentials.toml already up-to-date"
      elif [[ $FORCE -eq 1 ]]; then
        if [[ $BACKUP -eq 1 ]]; then backup_file "$creds_dst"; fi
        if [[ $DRY_RUN -eq 1 ]]; then skip "would overwrite credentials.toml"
        else cp "$creds_src" "$creds_dst"; ok "credentials.toml installed"; fi
      else
        warn "credentials.toml exists and differs. Use --force to overwrite."
      fi
    else
      if [[ $DRY_RUN -eq 1 ]]; then skip "would install credentials.toml"
      else cp "$creds_src" "$creds_dst"; ok "credentials.toml installed"; fi
    fi
  fi
else
  warn "credentials.toml not found in bundle"
fi

# --- 9. Summary ---
step "Summary"
echo "    Skills installed : $installed_skills"
echo "    Skills updated   : $updated_skills"
echo "    Skills unchanged : $skipped_skills"
echo "    Config: AGENTS.md, agents/, config.json, scripts/, mcp_config.json, credentials.toml"

if [[ $DRY_RUN -eq 1 ]]; then
  printf "\n\033[33mDry-run complete. Re-run without --dry-run to apply.\033[0m\n"
else
  printf "\n\033[32mDone. Restart Devin CLI to pick up new configuration.\033[0m\n"
fi
