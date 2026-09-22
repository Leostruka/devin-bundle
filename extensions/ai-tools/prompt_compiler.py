#!/usr/bin/env python3
"""Prompt Compiler — Golden Template assembler.

The AGENT does the thinking: it reads the user's request, decides the effort
level (medium/high/max) semantically, picks a senior operational persona, and
drafts the five template blocks. This script only validates and assembles —
no heuristics, no language-specific guessing. Works in any language because
all judgment lives upstream in the model.

Spec input is JSON with keys:

  effort      "medium" | "high" | "max"          (required — decided by agent)
  persona     "Staff Engineer", "SecOps", ...    (required)
  model       "swe-2", "claude", ...             (optional; resolves variant id
                                                from bundle-models.json)
  goal        1-2 paragraph goal statement       (required)
  context     architecture/tool/current state    (required)
  acceptance  [measurable criterion, ...]        (required, >=1)
  in_scope    [item, ...]                        (required, >=1)
  out_scope   [forbidden item, ...]              (required, >=1)
  phases      ["checkpoint step", ...]           (required, >=1)

Modes:

  prompt_compiler.py --self-test                  # offline asserts + JSON
  prompt_compiler.py --list-models                # models with a KB
  prompt_compiler.py --draft spec.json            # validate + write
  prompt_compiler.py --draft -                    # spec JSON from stdin
  prompt_compiler.py --spec '{"effort":"high",...}'
  prompt_compiler.py                              # interactive REPL (TTY only)

On approval, writes `.devin/scratch/optimized_ready.md` for a fresh local
session to consume.
"""
import argparse
import hashlib
import json
import os
import re
import sys
from pathlib import Path

EXT_DIR = Path(__file__).resolve().parent
KB_DIR = EXT_DIR / "knowledge_bases"
OUT_NAME = "optimized_ready.md"

EFFORTS = ("medium", "high", "max")


def emit(obj, code=0):
    print(json.dumps(obj, indent=2, ensure_ascii=False))
    sys.exit(code)


def find_repo_root():
    for d in [Path.cwd(), *Path.cwd().parents]:
        if (d / ".devin").is_dir() or (d / ".git").exists():
            return d
    return Path.cwd()


def load_kb(model):
    path = KB_DIR / f"{model.lower().strip()}.json"
    if not path.exists():
        path = KB_DIR / "generic.json"
    try:
        kb = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None, None
    return kb, path.stem


def list_models():
    return sorted(p.stem for p in KB_DIR.glob("*.json") if p.stem != "generic")


def load_variant_map():
    """Family -> {effort: model_id} from bundle-models.json; embedded fallback."""
    candidates = [find_repo_root() / "data" / "bundle-models.json"]
    appdata = os.environ.get("APPDATA")
    if appdata:
        candidates.append(Path(appdata) / "devin" / "data" / "bundle-models.json")
    candidates.append(Path.home() / ".config" / "devin" / "data" / "bundle-models.json")
    for path in candidates:
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        variants = {}
        for m in data.get("models", []):
            mid, effort = m.get("id", ""), m.get("effort")
            if effort and "-" in mid:
                variants.setdefault(mid.rsplit("-", 1)[0], {})[effort] = mid
        for alias, fam in data.get("aliases", {}).items():
            if fam in variants:
                variants[alias] = variants[fam]
        if variants:
            return variants
    return {"swe-2": {"medium": "swe-2-medium", "high": "swe-2-high", "max": "swe-2-max"}}


def variant_for(model, effort, variants=None):
    """Deterministic family+effort -> variant id. No guessing: effort is
    supplied by the agent. Returns None when the model has no variants."""
    if not model or not effort:
        return None
    variants = variants if variants is not None else load_variant_map()
    family = variants.get(model.lower().strip())
    return family.get(effort) if family else None


# --- Golden Template -------------------------------------------------------

LIST_FIELDS = ("acceptance", "in_scope", "out_scope", "phases")
STR_FIELDS = ("effort", "persona", "goal", "context")


def _as_list(v):
    if isinstance(v, str):
        return [v] if v.strip() else []
    return [str(i) for i in v] if isinstance(v, list) else []


def validate_spec(spec):
    """Return list of problems; empty = valid."""
    problems = []
    if not isinstance(spec, dict):
        return ["spec must be a JSON object"]
    effort = str(spec.get("effort", "")).lower().strip()
    if effort not in EFFORTS:
        problems.append(f"effort must be one of {EFFORTS} (got '{spec.get('effort')}')")
    for f in ("persona", "goal", "context"):
        if not str(spec.get(f, "")).strip():
            problems.append(f"'{f}' is required and non-empty")
    for f in LIST_FIELDS:
        if not _as_list(spec.get(f)):
            problems.append(f"'{f}' requires >= 1 item")
    return problems


def _strip_num(s):
    """Drop leading '1.' / '1)' / '**Fase N:**' so numbering stays canonical."""
    s = s.strip()
    s = re.sub(r"^\d+[.)]\s*", "", s)
    s = re.sub(r"^\*\*Fase\s+\d+[:.]?\*\*\s*", "", s, flags=re.I)
    return s.strip()


def render(spec):
    """Assemble the Golden Template. Exact structure — nothing added."""
    effort = spec["effort"].lower().strip()
    lines = [
        f"# Nível de Esforço Obrigatório: {effort.upper()}",
        f"# Perfil Operacional: {spec['persona'].strip()}",
        "",
        "# Goal",
        spec["goal"].strip(),
        "",
        "# Context",
        spec["context"].strip(),
        "",
        "# Acceptance Criteria",
    ]
    lines += [f"{i}. {_strip_num(c)}" for i, c in enumerate(_as_list(spec["acceptance"]), 1)]
    lines += ["", "# Scope & Non-Goals"]
    lines += [f"- **IN SCOPE:** {s.strip()}" for s in _as_list(spec["in_scope"])]
    lines += [f"- **OUT OF SCOPE:** {s.strip()}" for s in _as_list(spec["out_scope"])]
    lines += ["", "# Execution Hints & Checkpoints"]
    lines += [f"{i}. **Fase {i}:** {_strip_num(p)}" for i, p in enumerate(_as_list(spec["phases"]), 1)]
    return "\n".join(lines) + "\n"


def save(text, root):
    out = root / ".devin" / "scratch" / OUT_NAME
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(text, encoding="utf-8")
    return out


def load_draft(arg):
    """Load spec JSON from a path, '-' (stdin), or an inline JSON string."""
    if arg == "-":
        raw = sys.stdin.read()
    elif arg.lstrip().startswith("{"):
        raw = arg
    else:
        raw = Path(arg).read_text(encoding="utf-8")
    return json.loads(raw)


def finalize(spec, dry_run):
    problems = validate_spec(spec)
    if problems:
        emit({"ok": False, "errors": problems}, 1)
    prompt = render(spec)
    result = {"ok": True,
              "effort": spec["effort"].lower().strip(),
              "persona": spec["persona"].strip(),
              "sha256": hashlib.sha256(prompt.encode()).hexdigest()}
    model = str(spec.get("model", "")).lower().strip()
    variant = variant_for(model, result["effort"])
    if variant:
        result["recommended_model"] = variant
    if dry_run:
        result["dry_run"] = True
        result["prompt"] = prompt
    else:
        result["path"] = str(save(prompt, find_repo_root()))
    emit(result)


FIELD_PROMPTS = {
    "effort": "Effort level (medium/high/max)",
    "persona": "Operational persona (e.g. Staff Engineer, SecOps Lead)",
    "model": "Target model family (optional, e.g. swe-2)",
    "goal": "Goal (1-2 paragraphs)",
    "context": "Context (architecture, tools, current state)",
}


def input_list(label):
    print(f"{label} — one per line, blank to finish:")
    items = []
    while True:
        line = input("  > ").strip()
        if not line:
            break
        items.append(line)
    return items


def interactive(draft_arg=None):
    spec = load_draft(draft_arg) if draft_arg else {}
    while True:
        missing = [f for f in STR_FIELDS if not str(spec.get(f, "")).strip()] \
                + [f for f in LIST_FIELDS if not _as_list(spec.get(f))]
        for f in missing:
            spec[f] = input_list(f) if f in LIST_FIELDS else input(f"{FIELD_PROMPTS.get(f, f)}: ").strip()
        problems = validate_spec(spec)
        if problems:
            print("[compiler] invalid spec:", "; ".join(problems))
            continue
        print("\n" + render(spec) + "\n")
        fb = input("Section to edit (effort/persona/goal/context/acceptance/"
                   "in_scope/out_scope/phases) or 'APPROVE' to save: ").strip()
        if fb.upper() == "APPROVE":
            finalize(spec, dry_run=False)
        key = fb.lower().replace("-", "_").replace(" ", "_")
        if key in LIST_FIELDS:
            spec[key] = input_list(key)
        elif key in FIELD_PROMPTS or key == "model":
            spec[key] = input(f"{key}: ").strip()
        else:
            print(f"[compiler] unknown section '{fb}'")


def main():
    p = argparse.ArgumentParser(description="Golden Template prompt assembler.")
    p.add_argument("--draft", help="Spec JSON file path, or '-' for stdin")
    p.add_argument("--spec", help="Inline spec JSON string")
    p.add_argument("--list-models", action="store_true")
    p.add_argument("--dry-run", action="store_true", help="Render only; do not write file")
    p.add_argument("--self-test", action="store_true")
    args = p.parse_args()

    if args.self_test:
        kb, used = load_kb("definitely-not-a-model")
        assert kb is not None and used == "generic", "generic fallback failed"
        spec = {"effort": "high", "persona": "Staff Engineer", "model": "swe-2",
                "goal": "Ship X.", "context": "Repo Y, tool Z.",
                "acceptance": ["pytest green"], "in_scope": ["src/"],
                "out_scope": ["deploy"], "phases": ["do it. **PARE e aguarde aprovação.**"]}
        assert validate_spec(spec) == []
        out = render(spec)
        for h in ("# Nível de Esforço Obrigatório: HIGH", "# Perfil Operacional: Staff Engineer",
                  "# Goal", "# Context", "# Acceptance Criteria", "1. pytest green",
                  "- **IN SCOPE:** src/", "- **OUT OF SCOPE:** deploy",
                  "# Execution Hints & Checkpoints", "1. **Fase 1:**"):
            assert h in out, f"missing: {h}"
        assert validate_spec({"effort": "huge"}) and validate_spec({"effort": "high"})
        fam = {"swe-2": {"medium": "m", "high": "h", "max": "x"}}
        assert variant_for("swe-2", "max", fam) == "x"
        assert variant_for("claude", "max", fam) is None
        emit({"ok": True, "self_test": "passed", "models": list_models()})

    if args.list_models:
        emit({"ok": True, "models": list_models()})

    draft_arg = args.draft or args.spec
    if sys.stdin.isatty() and sys.stdout.isatty() and not draft_arg:
        interactive()

    # Non-interactive: a spec is required — the agent fills the blocks.
    if not draft_arg:
        emit({"ok": False,
              "error": "non-interactive mode requires --draft <file|-> or --spec '<json>'"}, 2)
    try:
        spec = load_draft(draft_arg)
    except (OSError, json.JSONDecodeError) as e:
        emit({"ok": False, "error": f"draft unreadable: {e}"}, 1)
    finalize(spec, args.dry_run)


if __name__ == "__main__":
    main()
