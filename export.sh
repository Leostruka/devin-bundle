#!/usr/bin/env bash
# Devin bundle exporter (Linux / WSL / macOS).
# Regenerates skills/ and AGENTS.md in the bundle from the live Devin config on this machine.
set -euo pipefail

BUNDLE_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
MANIFEST_PATH="$BUNDLE_ROOT/manifest.json"
SKILLS_DST="$BUNDLE_ROOT/skills"
RULES_DST="$BUNDLE_ROOT/AGENTS.md"

DRY_RUN=0
COMMIT=0
PUSH=0

usage() {
  cat <<EOF
Devin bundle exporter (Linux / WSL / macOS)

Regenerates the bundle from the live Devin config on this machine.

Usage: ./export.sh [--dry-run] [--commit] [--push]

  --dry-run   Show what would be copied without writing.
  --commit    After export, git add + commit with a generated message.
  --push      After commit, git push. Implies --commit.
  --help      Show this message.
EOF
}

for arg in "$@"; do
  case "$arg" in
    --dry-run) DRY_RUN=1 ;;
    --commit)  COMMIT=1 ;;
    --push)    COMMIT=1; PUSH=1 ;;
    --help|-h) usage; exit 0 ;;
    *) echo "Unknown option: $arg"; usage; exit 1 ;;
  esac
done

if [[ ! -f "$MANIFEST_PATH" ]]; then echo "ERROR: manifest.json not found at $MANIFEST_PATH" >&2; exit 1; fi

# --- Helpers ---
step() { printf "\n\033[36m[*] %s\033[0m\n" "$1"; }
ok()   { printf "    \033[32m[+] %s\033[0m\n" "$1"; }
skip() { printf "    \033[33m[~] %s (dry-run)\033[0m\n" "$1"; }
warn() { printf "    \033[33m[!] %s\033[0m\n" "$1"; }
err()  { printf "    \033[31m[x] %s\033[0m\n" "$1"; }

resolve_path() {
  local raw="$1"
  # Expand ~ and env vars
  raw="${raw//\~/$HOME}"
  raw="${raw//\$HOME/$HOME}"
  raw="${raw//\$APPDATA/$HOME/.config}"
  raw="${raw//%APPDATA%/$HOME/.config}"
  raw="${raw//%USERPROFILE%/$HOME}"
  echo "$raw"
}

dir_hash() {
  ( cd "$1" 2>/dev/null && find . -type f | sort | xargs sha256sum 2>/dev/null | sha256sum | cut -d' ' -f1 )
}

# --- Detect Devin config home ---
DEVIN_HOME="${XDG_CONFIG_HOME:-$HOME/.config}/devin"

echo "================================================"
echo "  Devin Bundle Exporter"
echo "  Source : $DEVIN_HOME"
echo "  Bundle : $BUNDLE_ROOT"
[[ $DRY_RUN -eq 1 ]] && echo "  Mode   : DRY-RUN"
echo "================================================"

# --- 1. Ensure skills/ dir ---
if [[ ! -d "$SKILLS_DST" ]]; then
  if [[ $DRY_RUN -eq 1 ]]; then skip "would create $SKILLS_DST"; else mkdir -p "$SKILLS_DST"; ok "created $SKILLS_DST"; fi
fi

# --- 2. Export rules ---
step "Export consolidated rules"
RULES_FOUND=""
for r in "$DEVIN_HOME/AGENTS.md" "$DEVIN_HOME/rules.md" "$HOME/.claude/CLAUDE.md"; do
  if [[ -f "$r" ]]; then RULES_FOUND="$r"; break; fi
done
if [[ -n "$RULES_FOUND" ]]; then
  if [[ $DRY_RUN -eq 1 ]]; then skip "would copy $RULES_FOUND -> $RULES_DST"
  else cp "$RULES_FOUND" "$RULES_DST"; ok "rules exported from $RULES_FOUND"; fi
else
  warn "no AGENTS.md/rules.md/CLAUDE.md found; keeping existing bundle/AGENTS.md"
fi

# --- 3. Export skills (parse manifest with python3 or jq) ---
step "Export skills"
exported=0; unchanged=0; failed=0

# Use python3 if available, else jq
if command -v python3 &>/dev/null; then
  PARSER="python3"
elif command -v jq &>/dev/null; then
  PARSER="jq"
else
  echo "ERROR: need python3 or jq to parse manifest.json" >&2; exit 1
fi

get_skill_list() {
  if [[ "$PARSER" == "python3" ]]; then
    python3 -c "
import json, sys
with open('$MANIFEST_PATH') as f:
    m = json.load(f)
for s in m.get('skills', []):
    print(s['name'] + '|' + s.get('original_path', ''))
"
  else
    jq -r '.skills[] | .name + "|" + (.original_path // "")' "$MANIFEST_PATH"
  fi
}

while IFS='|' read -r name src_raw; do
  [[ -z "$name" ]] && continue
  src="$(resolve_path "$src_raw")"
  dst="$SKILLS_DST/$name"

  if [[ ! -d "$src" ]]; then
    err "$name : source not found at $src"
    failed=$((failed+1))
    continue
  fi

  src_h="$(dir_hash "$src")"
  dst_h=""
  if [[ -d "$dst" ]]; then dst_h="$(dir_hash "$dst")"; fi

  if [[ "$src_h" == "$dst_h" ]]; then
    ok "$name (unchanged)"
    unchanged=$((unchanged+1))
  else
    if [[ $DRY_RUN -eq 1 ]]; then skip "would export $name from $src"
    else rm -rf "$dst"; cp -r "$src" "$dst"; ok "exported $name"; fi
    exported=$((exported+1))
  fi
done < <(get_skill_list)

# --- 4. Summary ---
step "Summary"
echo "    Skills exported  : $exported"
echo "    Skills unchanged : $unchanged"
echo "    Skills failed    : $failed"

# --- 5. Optional git commit + push ---
if [[ $COMMIT -eq 1 && $DRY_RUN -eq 0 && $failed -eq 0 ]]; then
  step "Git commit"
  cd "$BUNDLE_ROOT"
  git add -A 2>/dev/null
  if [[ -n "$(git status --porcelain)" ]]; then
    date_str="$(date +%Y-%m-%d)"
    git commit -m "export: refresh skills + rules ($date_str)" 2>/dev/null
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
