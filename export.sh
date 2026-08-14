#!/usr/bin/env bash
# Devin bundle exporter (Linux / WSL / macOS).
# Exports FULL Devin CLI setup: AGENTS.md, agents/, skills/, config.json, hooks.v1.json, scripts/, mcp_config.json, credentials.toml
set -euo pipefail

BUNDLE_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BUNDLE_DIR="$BUNDLE_ROOT"

DRY_RUN=0
COMMIT=0
PUSH=0
NO_MASK=0

usage() {
  cat <<EOF
Devin bundle exporter (Linux / WSL / macOS)

Exports the full Devin CLI configuration to the bundle.

Usage: ./export.sh [--dry-run] [--commit] [--push] [--no-mask] [--help]

  --dry-run   Show what would be copied without writing.
  --commit    After export, git add + commit with a generated message.
  --push      After commit, git push. Implies --commit.
  --no-mask   Do not mask sensitive values in config.json, mcp_config.json, credentials.toml.
  --help      Show this message.
EOF
}

for arg in "$@"; do
  case "$arg" in
    --dry-run) DRY_RUN=1 ;;
    --commit)  COMMIT=1 ;;
    --push)    COMMIT=1; PUSH=1 ;;
    --no-mask) NO_MASK=1 ;;
    --help|-h) usage; exit 0 ;;
    *) echo "Unknown option: $arg"; usage; exit 1 ;;
  esac
done

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

convert_to_lf() {
  local file="$1"
  if [[ $DRY_RUN -eq 1 ]]; then
    echo "$file (would convert to LF)"
  else
    # Remove carriage returns (macOS-compatible)
    if [[ "$(uname)" == "Darwin" ]]; then
      sed -i '' 's/\r$//' "$file"
    else
      sed -i 's/\r$//' "$file"
    fi
  fi
}

# --- Detect Devin config home ---
if [[ -n "${DEVIN_HOME:-}" ]]; then
  DEVIN_HOME="$DEVIN_HOME"
else
  DEVIN_HOME="${XDG_CONFIG_HOME:-$HOME/.config}/devin"
fi

echo "================================================"
echo "  Devin Bundle Exporter"
echo "  Source : $DEVIN_HOME"
echo "  Bundle : $BUNDLE_DIR"
[[ $DRY_RUN -eq 1 ]] && echo "  Mode   : DRY-RUN"
[[ $NO_MASK -eq 1 ]] && echo "  Masking: DISABLED"
echo "================================================"

# --- Ensure bundle dir ---
if [[ ! -d "$BUNDLE_DIR" ]]; then
  if [[ $DRY_RUN -eq 1 ]]; then skip "would create $BUNDLE_DIR"; else mkdir -p "$BUNDLE_DIR"; ok "created $BUNDLE_DIR"; fi
fi

# --- 1. Export AGENTS.md ---
step "Export AGENTS.md"
agents_md_src="$DEVIN_HOME/AGENTS.md"
agents_md_dst="$BUNDLE_DIR/AGENTS.md"
if [[ -f "$agents_md_src" ]]; then
  src_h="$(file_hash "$agents_md_src")"
  dst_h=""
  if [[ -f "$agents_md_dst" ]]; then dst_h="$(file_hash "$agents_md_dst")"; fi
  if [[ "$src_h" == "$dst_h" ]]; then
    ok "AGENTS.md (unchanged)"
  else
    if [[ $DRY_RUN -eq 1 ]]; then skip "would copy AGENTS.md"
    else cp "$agents_md_src" "$agents_md_dst"; convert_to_lf "$agents_md_dst"; ok "AGENTS.md exported"; fi
  fi
else
  warn "AGENTS.md not found at $agents_md_src"
fi

# --- 2. Export agents/ profiles ---
step "Export agents/ profiles"
agents_src="$DEVIN_HOME/agents"
agents_dst="$BUNDLE_DIR/agents"
if [[ -d "$agents_src" ]]; then
  if [[ ! -d "$agents_dst" ]]; then
    if [[ $DRY_RUN -eq 1 ]]; then skip "would create $agents_dst"; else mkdir -p "$agents_dst"; fi
  fi
  for agent_file in "$agents_src"/*.md; do
    [[ -f "$agent_file" ]] || continue
    name="$(basename "$agent_file")"
    dst_file="$agents_dst/$name"
    src_h="$(file_hash "$agent_file")"
    dst_h=""
    if [[ -f "$dst_file" ]]; then dst_h="$(file_hash "$dst_file")"; fi
    if [[ "$src_h" == "$dst_h" ]]; then
      ok "agents/$name (unchanged)"
    else
      if [[ $DRY_RUN -eq 1 ]]; then skip "would copy agents/$name"
      else cp "$agent_file" "$dst_file"; convert_to_lf "$dst_file"; ok "agents/$name exported"; fi
    fi
  done
else
  warn "agents/ directory not found at $agents_src"
fi

# --- 3. Export skills/ (auto-discover all) ---
step "Export skills/"
skills_src="$DEVIN_HOME/skills"
skills_dst="$BUNDLE_DIR/skills"
exported_skills=0; unchanged_skills=0
if [[ -d "$skills_src" ]]; then
  if [[ ! -d "$skills_dst" ]]; then
    if [[ $DRY_RUN -eq 1 ]]; then skip "would create $skills_dst"; else mkdir -p "$skills_dst"; fi
  fi
  for skill_dir in "$skills_src"/*/; do
    [[ -d "$skill_dir" ]] || continue
    name="$(basename "$skill_dir")"
    dst_dir="$skills_dst/$name"
    src_h="$(dir_hash "$skill_dir")"
    dst_h=""
    if [[ -d "$dst_dir" ]]; then dst_h="$(dir_hash "$dst_dir")"; fi
    if [[ "$src_h" == "$dst_h" ]]; then
      ok "skills/$name (unchanged)"
      unchanged_skills=$((unchanged_skills+1))
    else
      if [[ $DRY_RUN -eq 1 ]]; then skip "would export skills/$name"
      else rm -rf "$dst_dir"; cp -r "$skill_dir" "$dst_dir"; ok "skills/$name exported"; fi
      exported_skills=$((exported_skills+1))
    fi
  done
else
  warn "skills/ directory not found at $skills_src"
fi

# --- 4. Export config.json (mask org_id) ---
step "Export config.json"
config_src="$DEVIN_HOME/config.json"
config_dst="$BUNDLE_DIR/config.json"
if [[ -f "$config_src" ]]; then
  if [[ $NO_MASK -eq 1 ]]; then
    if [[ $DRY_RUN -eq 1 ]]; then skip "would copy config.json (no mask)"
    else cp "$config_src" "$config_dst"; convert_to_lf "$config_dst"; ok "config.json exported (no mask)"; fi
  else
    if command -v python3 &>/dev/null; then
      if [[ $DRY_RUN -eq 1 ]]; then skip "would copy config.json (masked)"
      else
        python3 -c "
import json
with open('$config_src', 'r') as f:
    data = json.load(f)
if 'org_id' in data:
    data['org_id'] = 'MASKED'
if 'devin' in data and 'org_id' in data['devin']:
    data['devin']['org_id'] = 'MASKED'
with open('$config_dst', 'w') as f:
    json.dump(data, f, indent=2)
"
        convert_to_lf "$config_dst"
        ok "config.json exported (masked)"
      fi
    else
      warn "python3 not found, copying config.json without masking"
      if [[ $DRY_RUN -eq 1 ]]; then skip "would copy config.json (unmasked - no python3)"
      else cp "$config_src" "$config_dst"; convert_to_lf "$config_dst"; ok "config.json exported (unmasked)"; fi
    fi
  fi
else
  warn "config.json not found at $config_src"
fi

# --- 5. Export hooks.v1.json ---
step "Export hooks.v1.json"
hooks_src="$DEVIN_HOME/hooks.v1.json"
hooks_dst="$BUNDLE_DIR/hooks.v1.json"
if [[ -f "$hooks_src" ]]; then
  src_h="$(file_hash "$hooks_src")"
  dst_h=""
  if [[ -f "$hooks_dst" ]]; then dst_h="$(file_hash "$hooks_dst")"; fi
  if [[ "$src_h" == "$dst_h" ]]; then
    ok "hooks.v1.json (unchanged)"
  else
    if [[ $DRY_RUN -eq 1 ]]; then skip "would copy hooks.v1.json"
    else cp "$hooks_src" "$hooks_dst"; convert_to_lf "$hooks_dst"; ok "hooks.v1.json exported"; fi
  fi
else
  warn "hooks.v1.json not found at $hooks_src"
fi

# --- 6. Export scripts/ ---
step "Export scripts/"
scripts_src="$DEVIN_HOME/scripts"
scripts_dst="$BUNDLE_DIR/scripts"
if [[ -d "$scripts_src" ]]; then
  if [[ ! -d "$scripts_dst" ]]; then
    if [[ $DRY_RUN -eq 1 ]]; then skip "would create $scripts_dst"; else mkdir -p "$scripts_dst"; fi
  fi
  for script_file in "$scripts_src"/*; do
    [[ -f "$script_file" ]] || continue
    name="$(basename "$script_file")"
    dst_file="$scripts_dst/$name"
    src_h="$(file_hash "$script_file")"
    dst_h=""
    if [[ -f "$dst_file" ]]; then dst_h="$(file_hash "$dst_file")"; fi
    if [[ "$src_h" == "$dst_h" ]]; then
      ok "scripts/$name (unchanged)"
    else
      if [[ $DRY_RUN -eq 1 ]]; then skip "would copy scripts/$name"
      else cp "$script_file" "$dst_file"; ok "scripts/$name exported"; fi
    fi
  done
else
  warn "scripts/ directory not found at $scripts_src"
fi

# --- 7. Export mcp_config.json (mask secrets) ---
step "Export mcp_config.json"
mcp_src="$DEVIN_HOME/mcp_config.json"
mcp_dst="$BUNDLE_DIR/mcp_config.json"
if [[ -f "$mcp_src" ]]; then
  if [[ $NO_MASK -eq 1 ]]; then
    if [[ $DRY_RUN -eq 1 ]]; then skip "would copy mcp_config.json (no mask)"
    else cp "$mcp_src" "$mcp_dst"; convert_to_lf "$mcp_dst"; ok "mcp_config.json exported (no mask)"; fi
  else
    if command -v python3 &>/dev/null; then
      if [[ $DRY_RUN -eq 1 ]]; then skip "would copy mcp_config.json (masked)"
      else
        python3 -c "
import json
import re

with open('$mcp_src', 'r') as f:
    data = json.load(f)

def mask_value(v):
    if isinstance(v, str):
        # Mask URLs containing tokens
        if 'token' in v.lower() or 'api_key' in v.lower():
            return 'MASKED'
        return v
    elif isinstance(v, dict):
        return {k: mask_value(val) for k, val in v.items()}
    elif isinstance(v, list):
        return [mask_value(item) for item in v]
    return v

# Mask env values with API_KEY, TOKEN, etc.
if isinstance(data, dict):
    for key, val in data.items():
        if key.upper() in ['API_KEY', 'TOKEN', 'SECRET', 'PASSWORD', 'AUTH']:
            data[key] = 'MASKED'
        else:
            data[key] = mask_value(val)

with open('$mcp_dst', 'w') as f:
    json.dump(data, f, indent=2)
"
        convert_to_lf "$mcp_dst"
        ok "mcp_config.json exported (masked)"
      fi
    else
      warn "python3 not found, copying mcp_config.json without masking"
      if [[ $DRY_RUN -eq 1 ]]; then skip "would copy mcp_config.json (unmasked - no python3)"
      else cp "$mcp_src" "$mcp_dst"; convert_to_lf "$mcp_dst"; ok "mcp_config.json exported (unmasked)"; fi
    fi
  fi
else
  warn "mcp_config.json not found at $mcp_src"
fi

# --- 8. Export credentials.toml (mask all values) ---
step "Export credentials.toml"
creds_src="$DEVIN_HOME/credentials.toml"
creds_dst="$BUNDLE_DIR/credentials.toml"
if [[ -f "$creds_src" ]]; then
  if [[ $NO_MASK -eq 1 ]]; then
    if [[ $DRY_RUN -eq 1 ]]; then skip "would copy credentials.toml (no mask)"
    else cp "$creds_src" "$creds_dst"; convert_to_lf "$creds_dst"; ok "credentials.toml exported (no mask)"; fi
  else
    if [[ $DRY_RUN -eq 1 ]]; then skip "would copy credentials.toml (masked)"
    else
      # Mask all values in TOML (simple sed approach)
      sed 's/=.*/= "MASKED"/g' "$creds_src" > "$creds_dst"
      convert_to_lf "$creds_dst"
      ok "credentials.toml exported (masked)"
    fi
  fi
else
  warn "credentials.toml not found at $creds_src"
fi

# --- 9. Pre-push validation ---
if [[ $PUSH -eq 1 && $DRY_RUN -eq 0 ]]; then
  step "Pre-push validation"
  validation_failed=0

  # Validate JSON files
  for json_file in "$BUNDLE_DIR"/*.json; do
    [[ -f "$json_file" ]] || continue
    name="$(basename "$json_file")"
    if command -v python3 &>/dev/null; then
      if ! python3 -m json.tool "$json_file" >/dev/null 2>&1; then
        err "$name: invalid JSON"
        validation_failed=1
      else
        ok "$name: valid JSON"
      fi
    elif command -v jq &>/dev/null; then
      if ! jq empty "$json_file" >/dev/null 2>&1; then
        err "$name: invalid JSON"
        validation_failed=1
      else
        ok "$name: valid JSON"
      fi
    fi
  done

  # Validate Python scripts
  if [[ -d "$scripts_dst" ]]; then
    for py_file in "$scripts_dst"/*.py; do
      [[ -f "$py_file" ]] || continue
      name="$(basename "$py_file")"
      if command -v python3 &>/dev/null; then
        if ! python3 -m py_compile "$py_file" >/dev/null 2>&1; then
          err "$name: syntax error"
          validation_failed=1
        else
          ok "$name: valid Python"
        fi
      fi
    done
  fi

  if [[ $validation_failed -eq 1 ]]; then
    err "Validation failed, aborting push"
    exit 1
  fi
fi

# --- 10. Summary ---
step "Summary"
echo "    Skills exported  : $exported_skills"
echo "    Skills unchanged : $unchanged_skills"
echo "    Config: AGENTS.md, agents/, config.json, hooks.v1.json, scripts/, mcp_config.json, credentials.toml"

# --- 11. Optional git commit + push ---
if [[ $COMMIT -eq 1 && $DRY_RUN -eq 0 ]]; then
  step "Git commit"
  cd "$BUNDLE_ROOT"
  git add -A 2>/dev/null
  if [[ -n "$(git status --porcelain)" ]]; then
    date_str="$(date +%Y-%m-%d)"
    git commit -m "export: refresh devin bundle ($date_str)

Skills: $exported_skills exported, $unchanged_skills unchanged
Config: AGENTS.md, config.json, hooks.v1.json, mcp_config.json, credentials.toml, scripts/, agents/" 2>/dev/null
    ok "committed"
    if [[ $PUSH -eq 1 ]]; then
      git push 2>&1 | sed 's/^/    /'
      ok "pushed"
    fi
  else
    ok "nothing to commit (bundle already up to date)"
  fi
fi

if [[ $DRY_RUN -eq 1 ]]; then
  printf "\n\033[33mDry-run complete. Re-run without --dry-run to apply.\033[0m\n"
else
  printf "\n\033[32mExport complete.\033[0m\n"
fi
