#!/usr/bin/env bash
# Devin bundle installer (Linux / WSL / macOS / macOS).
# Restores skills + consolidated AGENTS.md to the correct Devin config locations.
set -euo pipefail

BUNDLE_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SKILLS_SRC="$BUNDLE_ROOT/skills"
RULES_SRC="$BUNDLE_ROOT/AGENTS.md"

DRY_RUN=0
FORCE=0

usage() {
  cat <<EOF
Devin bundle installer (Linux / WSL / macOS)

Usage: ./install.sh [--dry-run] [--force]

  --dry-run   Show what would happen without writing anything.
  --force     Overwrite existing skills/rules without prompting.
  --help      Show this message.
EOF
}

for arg in "$@"; do
  case "$arg" in
    --dry-run) DRY_RUN=1 ;;
    --force)   FORCE=1 ;;
    --help|-h) usage; exit 0 ;;
    *) echo "Unknown option: $arg"; usage; exit 1 ;;
  esac
done

if [[ ! -d "$SKILLS_SRC" ]]; then echo "ERROR: skills/ not found in $BUNDLE_ROOT" >&2; exit 1; fi
if [[ ! -f "$RULES_SRC" ]];  then echo "ERROR: AGENTS.md not found in $BUNDLE_ROOT" >&2; exit 1; fi

# --- Resolve target dirs ---
DEVIN_HOME="${XDG_CONFIG_HOME:-$HOME/.config}/devin"
SKILLS_DST="$DEVIN_HOME/skills"
RULES_DST="$DEVIN_HOME/AGENTS.md"

step() { printf "\n\033[36m[*] %s\033[0m\n" "$1"; }
ok()   { printf "    \033[32m[+] %s\033[0m\n" "$1"; }
skip() { printf "    \033[33m[~] %s (dry-run)\033[0m\n" "$1"; }
warn() { printf "    \033[33m[!] %s\033[0m\n" "$1"; }

echo "================================================"
echo "  Devin Bundle Installer"
echo "  Target : $DEVIN_HOME"
[[ $DRY_RUN -eq 1 ]] && echo "  Mode   : DRY-RUN"
echo "================================================"

# --- 1. Ensure dirs ---
step "Ensure target directories"
if [[ $DRY_RUN -eq 1 ]]; then
  skip "would create $DEVIN_HOME (if missing)"
  skip "would create $SKILLS_DST (if missing)"
else
  mkdir -p "$DEVIN_HOME" "$SKILLS_DST"
  ok "$DEVIN_HOME"
  ok "$SKILLS_DST"
fi

# --- 2. Install rules ---
step "Install consolidated rules"
install_file() {
  local src="$1" dst="$2" label="$3"
  if [[ -f "$dst" ]]; then
    if diff -q "$src" "$dst" >/dev/null 2>&1; then
      ok "$label already up-to-date"
    elif [[ $FORCE -eq 1 ]]; then
      if [[ $DRY_RUN -eq 1 ]]; then skip "would overwrite $dst"; else cp "$src" "$dst"; ok "overwrote $dst"; fi
    else
      warn "$dst exists and differs. Use --force to overwrite."
    fi
  else
    if [[ $DRY_RUN -eq 1 ]]; then skip "would write $dst"; else cp "$src" "$dst"; ok "wrote $dst"; fi
  fi
}
install_file "$RULES_SRC" "$RULES_DST" "AGENTS.md"

# --- 3. Install skills ---
step "Install skills"
installed=0; updated=0; skipped=0

dir_hash() {
  ( cd "$1" && find . -type f | sort | xargs sha256sum 2>/dev/null | sha256sum | cut -d' ' -f1 )
}

for skill_dir in "$SKILLS_SRC"/*/; do
  [[ -d "$skill_dir" ]] || continue
  name="$(basename "$skill_dir")"
  dst="$SKILLS_DST/$name"

  if [[ -d "$dst" ]]; then
    src_h="$(dir_hash "$skill_dir")"
    dst_h="$(dir_hash "$dst")"
    if [[ "$src_h" == "$dst_h" ]]; then
      ok "$name (unchanged)"
      skipped=$((skipped+1))
    elif [[ $FORCE -eq 1 ]]; then
      if [[ $DRY_RUN -eq 1 ]]; then skip "would update $name"; else rm -rf "$dst"; cp -r "$skill_dir" "$dst"; ok "updated $name"; fi
      updated=$((updated+1))
    else
      warn "$name exists and differs. Use --force to update."
    fi
  else
    if [[ $DRY_RUN -eq 1 ]]; then skip "would install $name"; else cp -r "$skill_dir" "$dst"; ok "installed $name"; fi
    installed=$((installed+1))
  fi
done

# --- 4. Summary ---
step "Summary"
echo "    Skills installed : $installed"
echo "    Skills updated   : $updated"
echo "    Skills unchanged : $skipped"
if [[ $DRY_RUN -eq 1 ]]; then
  printf "\n\033[33mDry-run complete. Re-run without --dry-run to apply.\033[0m\n"
else
  printf "\n\033[32mDone. Restart Devin CLI to pick up new skills/rules.\033[0m\n"
fi
