#!/usr/bin/env bash
# Devin bundle exporter (Linux / WSL / macOS).
# Exports global Devin CLI setup: AGENTS.md, agents/, skills/, config.json, scripts/, data/, mcp_config.json, credentials.toml
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
  ( cd "$1" 2>/dev/null && find . -type f -print0 | xargs -0 sha256sum 2>/dev/null | sort | sha256sum | cut -d' ' -f1 )
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

# --- Normalize Devin home paths back to bundle placeholder ---
# When config.json is exported, the absolute DEVIN_HOME path that install.sh
# expanded from {{APPDATA}}/devin must be collapsed back to the portable
# placeholder so the bundle remains shareable across machines/users.
normalize_config_paths() {
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
    return
  fi
  DEVIN_HOME="$DEVIN_HOME" "$py" -c 'import os,sys; h=os.environ["DEVIN_HOME"]; sys.stdout.write(sys.stdin.read().replace(h, "{{APPDATA}}/devin"))' < "$file" > "${file}.tmp" && mv "${file}.tmp" "$file"
}

# --- Strip hooks from exported config.json ---
# hooks.v1.json is the single authored source of hook bindings; the live
# config.json hooks are a rendered artifact and must not round-trip back.
strip_config_hooks() {
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
    return
  fi
  "$py" -c 'import json,sys,os; p=sys.argv[1]; d=json.load(open(p,encoding="utf-8-sig")); d["hooks"]={}; mp=os.path.join(os.path.dirname(p),"data","bundle-models.json")
try:
    dp=json.load(open(mp,encoding="utf-8-sig")).get("default_parent_model")
    if dp and isinstance(d.get("agent"),dict): d["agent"]["model"]=dp
except OSError: pass
open(p,"w",encoding="utf-8",newline="\n").write(json.dumps(d,indent=2)+"\n")' "$file"
}

# --- Strip BOM from file (if present) ---
# BOM (EF BB BF) in YAML frontmatter can prevent parsers from recognizing
# the `---` delimiter, causing model/name/allowed-tools fields to be ignored.
strip_bom() {
  local file="$1"
  if [[ ! -f "$file" ]]; then return; fi
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

# --- Report dst entries absent from src ---
# Export is one-way (live -> bundle); items deleted upstream would
# persist silently. Auto-delete is unsafe in both directions (bundle may
# hold authored work not yet installed), so we only report.
report_stale() {
  local src_dir="$1" dst_dir="$2" label="$3"
  [[ -d "$src_dir" && -d "$dst_dir" ]] || return
  for dst_entry in "$dst_dir"/*; do
    [[ -e "$dst_entry" ]] || continue
    local name
    name="$(basename "$dst_entry")"
    if [[ ! -e "$src_dir/$name" ]]; then
      warn "$label: $name is bundle-only (not in live config) -- kept; remove manually if unintended"
    fi
  done
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
if [[ -z "${DEVIN_HOME:-}" ]]; then
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

# --- 1b. Dedup AGENTS.md case variants (Windows/WSL bug workaround) ---
step "Dedup AGENTS.md case variants"
dedup_agents_md "$DEVIN_HOME" "source"
dedup_agents_md "$BUNDLE_DIR" "bundle"

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
  report_stale "$agents_src" "$agents_dst" "agents"
else
  warn "agents/ directory not found at $agents_src"
fi

# --- 2b. Strip BOM from agent files (YAML frontmatter safety) ---
step "Strip BOM from agent files"
for agent_file in "$BUNDLE_DIR"/agents/*.md; do
  [[ -f "$agent_file" ]] || continue
  strip_bom "$agent_file"
done

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
  report_stale "$skills_src" "$skills_dst" "skills"
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
    else cp "$config_src" "$config_dst"; convert_to_lf "$config_dst"; normalize_config_paths "$config_dst"; strip_config_hooks "$config_dst"; ok "config.json exported (no mask)"; fi
  else
    if command -v python3 &>/dev/null; then
      if [[ $DRY_RUN -eq 1 ]]; then skip "would copy config.json (masked)"
      else
        python3 -c "
import json, sys
src, dst = sys.argv[1], sys.argv[2]
with open(src, 'r', encoding='utf-8-sig') as f:
    data = json.load(f)
if 'org_id' in data:
    data['org_id'] = 'MASKED'
if 'devin' in data and 'org_id' in data['devin']:
    data['devin']['org_id'] = 'MASKED'
data['hooks'] = {}
with open(dst, 'w', encoding='utf-8', newline='\n') as f:
    json.dump(data, f, indent=2)
" "$config_src" "$config_dst"
        convert_to_lf "$config_dst"
        normalize_config_paths "$config_dst"
        strip_config_hooks "$config_dst"
        ok "config.json exported (masked)"
      fi
    else
      warn "python3 not found, copying config.json without masking"
      if [[ $DRY_RUN -eq 1 ]]; then skip "would copy config.json (unmasked - no python3)"
      else cp "$config_src" "$config_dst"; convert_to_lf "$config_dst"; normalize_config_paths "$config_dst"; strip_config_hooks "$config_dst"; ok "config.json exported (unmasked)"; fi
    fi
  fi
else
  warn "config.json not found at $config_src"
fi

# --- 5. Project hooks template ---
step "Project hooks template"
skip "hooks.v1.json is project-level and is maintained in the repository"

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
  report_stale "$scripts_src" "$scripts_dst" "scripts"
else
  warn "scripts/ directory not found at $scripts_src"
fi

# --- 6a. Export data/ (model context windows and thresholds) ---
step "Export data/ (model context windows)"
data_src="$DEVIN_HOME/data"
data_dst="$BUNDLE_DIR/data"
if [[ -d "$data_src" ]]; then
  if [[ ! -d "$data_dst" ]]; then
    if [[ $DRY_RUN -eq 1 ]]; then skip "would create $data_dst"; else mkdir -p "$data_dst"; fi
  fi
  for data_file in "$data_src"/*; do
    [[ -f "$data_file" ]] || continue
    name="$(basename "$data_file")"
    dst_file="$data_dst/$name"
    src_h="$(file_hash "$data_file")"
    dst_h=""
    if [[ -f "$dst_file" ]]; then dst_h="$(file_hash "$dst_file")"; fi
    if [[ "$src_h" == "$dst_h" ]]; then
      ok "data/$name (unchanged)"
    else
      if [[ $DRY_RUN -eq 1 ]]; then skip "would copy data/$name"
      else cp "$data_file" "$dst_file"; ok "data/$name exported"; fi
    fi
  done
  report_stale "$data_src" "$data_dst" "data"
else
  warn "data/ directory not found at $data_src"
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
import json, sys, re
src, dst = sys.argv[1], sys.argv[2]
with open(src, 'r', encoding='utf-8-sig') as f:
    data = json.load(f)

SECRET_KEY = re.compile(r'token|secret|api[_-]?key|password|passwd|auth|bearer|credential|private|pat\b|client_secret', re.I)

def mask_value(v, key=''):
    if SECRET_KEY.search(key):
        return 'MASKED'
    if isinstance(v, str):
        # Mask URLs with embedded credentials or token-looking strings
        if re.search(r'://[^/\s:]+:[^@/\s]+@', v):
            return re.sub(r'://[^/\s:]+:[^@/\s]+@', '://MASKED@', v)
        if 'token' in v.lower() or 'api_key' in v.lower() or 'apikey' in v.lower():
            return 'MASKED'
        return v
    if isinstance(v, dict):
        return {k: mask_value(val, k) for k, val in v.items()}
    if isinstance(v, list):
        return [mask_value(item, key) for item in v]
    return v

# Mask env values with API_KEY, TOKEN, etc.
if isinstance(data, dict):
    data = {k: ('MASKED' if SECRET_KEY.search(k) else mask_value(v, k)) for k, v in data.items()}

with open(dst, 'w', encoding='utf-8', newline='\n') as f:
    json.dump(data, f, indent=2)
" "$mcp_src" "$mcp_dst"
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
      # Mask all values in TOML, including multiline arrays/strings:
      # `key = [` masks the key line, then continuation lines are dropped
      # until the opening `[`/`"""`/`'''` closes (they would leak raw).
      python3 -c "
import sys, re
src, dst = sys.argv[1], sys.argv[2]
out, skip_until = [], None
for line in open(src, encoding='utf-8', errors='replace'):
    if skip_until is not None:
        if skip_until in line:
            skip_until = None
        continue
    m = re.match(r'^(\s*[^=\s]+\s*)=(.*)$', line)
    if not m:
        out.append(line.rstrip('\n'))
        continue
    key, rhs = m.group(1), m.group(2).strip()
    out.append(key + '= \"MASKED\"')
    if rhs.startswith('[') and ']' not in rhs:
        skip_until = ']'
    elif rhs.startswith('\"\"\"') and rhs.count('\"\"\"') == 1:
        skip_until = '\"\"\"'
    elif rhs.startswith(chr(39)*3) and rhs.count(chr(39)*3) == 1:
        skip_until = chr(39)*3
open(dst, 'w', encoding='utf-8', newline='\n').write('\n'.join(out) + '\n')
" "$creds_src" "$creds_dst"
      convert_to_lf "$creds_dst"
      ok "credentials.toml exported (masked)"
    fi
  fi
else
  warn "credentials.toml not found at $creds_src"
fi

# --- 9. Pre-push validation ---
if [[ $PUSH -eq 1 && $NO_MASK -eq 1 && $DRY_RUN -eq 0 ]]; then
  err "FATAL: --push with --no-mask would export real secrets and push them to the repository."
  err "       This is a security risk. Aborting."
  err "       If you must back up unmasked credentials, use --no-mask --commit (no push) and review the diff manually."
  exit 1
fi

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

  # Run full repo audit and test suite before push (Rule 5: no push without green)
  # audit.py walks "." and reads manifest.json/AGENTS.md relative to cwd --
  # it must run inside BUNDLE_DIR or it audits the caller's directory.
  step "Running audit.py"
  if ( cd "$BUNDLE_DIR" && python audit.py ); then
    ok "audit.py passed"
  else
    err "audit.py failed"
    validation_failed=1
  fi

  step "Running pytest"
  # no path arg: pytest.ini testpaths=tests is the CI suite; "." would
  # sweep extensions/ integration tests that hard-fail without a live env
  if ( cd "$BUNDLE_DIR" && python -m pytest -q ); then
    ok "pytest passed"
  else
    err "pytest failed"
    validation_failed=1
  fi

  if [[ $validation_failed -eq 1 ]]; then
    err "Pre-push validation failed, aborting push"
    exit 1
  fi
fi

# --- 10. Summary ---
step "Summary"
echo "    Skills exported  : $exported_skills"
echo "    Skills unchanged : $unchanged_skills"
echo "    Config: AGENTS.md, agents/, config.json, scripts/, data/, mcp_config.json, credentials.toml"

# --- 11. Optional git commit + push ---
if [[ $COMMIT -eq 1 && $DRY_RUN -eq 0 ]]; then
  step "Git commit"
  cd "$BUNDLE_ROOT"
  # Stage only the paths export.sh can write -- staging the whole tree
  # would sweep unrelated working-tree changes into the generated commit.
  # NOTE: docs land dissolved under .devin/{docs,plans,templates}, not docs/.
  export_paths=(AGENTS.md agents skills config.json hooks.v1.json scripts data mcp_config.json credentials.toml .devin/docs .devin/plans .devin/templates export.sh export.ps1)
  existing_paths=()
  for p in "${export_paths[@]}"; do [[ -e "$BUNDLE_ROOT/$p" ]] && existing_paths+=("$p"); done
  if ! git add -- "${existing_paths[@]}"; then
    err "git add failed"
  fi
  if [[ -n "$(git status --porcelain -- "${existing_paths[@]}")" ]]; then
    date_str="$(date +%Y-%m-%d)"
    if git commit -m "export: refresh devin bundle ($date_str)

Skills: $exported_skills exported, $unchanged_skills unchanged
Config: AGENTS.md, config.json, mcp_config.json, credentials.toml, scripts/, data/, agents/"; then
      ok "committed"
      if [[ $PUSH -eq 1 ]]; then
        if git push 2>&1 | sed 's/^/    /'; then
          ok "pushed"
        else
          err "push failed"
        fi
      fi
    else
      err "git commit failed"
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
