#!/usr/bin/env python3
"""Prompt Compiler — interactive pre-flight prompt optimizer.

Compiles a rough task description into an optimized "super prompt" tuned to a
target model's prompt-engineering best practices, loaded from local JSON
knowledge bases in `knowledge_bases/` (populated by the knowledge-modeling
skill). On approval, writes `.devin/scratch/optimized_ready.md` for a fresh
local session to consume.

Modes (auto-detected; never blocks in CI):

  prompt_compiler.py --self-test              # offline asserts + JSON
  prompt_compiler.py --list-models            # models with a KB
  prompt_compiler.py                          # interactive REPL (TTY only)
  prompt_compiler.py --task "..." --model swe-2
  prompt_compiler.py --task "..." --model swe-2 --dry-run   # no write
"""
import argparse
import hashlib
import json
import sys
from pathlib import Path

EXT_DIR = Path(__file__).resolve().parent
KB_DIR = EXT_DIR / "knowledge_bases"
OUT_NAME = "optimized_ready.md"


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


def compile_prompt(task, kb, notes=None):
    """Render the optimized prompt: template + task + injected rules + user notes."""
    lines = [
        "# Optimized Prompt",
        "",
        "## Task",
        task.strip(),
        "",
    ]
    if kb.get("template"):
        lines += ["## Structure", kb["template"].strip(), ""]
    for key, title in (("rules", "Rules"), ("do", "Do"), ("dont", "Don't")):
        items = kb.get(key) or []
        if items:
            lines.append(f"## {title}")
            lines += [f"- {i}" for i in items]
            lines.append("")
    if notes:
        lines += ["## User Adjustments", notes.strip(), ""]
    return "\n".join(lines)


def save(text, root):
    out = root / ".devin" / "scratch" / OUT_NAME
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(text, encoding="utf-8")
    return out


def interactive(model_arg):
    model = (model_arg or input("Target model (e.g. swe-2, claude, kimi): ")).strip()
    kb, used = load_kb(model)
    if kb is None:
        emit({"ok": False, "error": f"knowledge base unreadable for '{model}'"}, 1)
    print(f"[compiler] model={used} kb={'loaded' if used != 'generic' else 'generic fallback'}")
    task = input("Task description: ").strip()
    notes = None
    while True:
        draft = compile_prompt(task, kb, notes)
        print("\n" + draft + "\n")
        fb = input("Feedback, or 'APPROVE' to save: ").strip()
        if fb.upper() == "APPROVE":
            out = save(draft, find_repo_root())
            emit({"ok": True, "model": used, "path": str(out),
                  "sha256": hashlib.sha256(draft.encode()).hexdigest()})
        notes = fb if notes is None else f"{notes}\n{fb}"


def main():
    p = argparse.ArgumentParser(description="Interactive pre-flight prompt optimizer.")
    p.add_argument("--task", help="Task description (required in non-interactive mode)")
    p.add_argument("--model", help="Target model key (knowledge_bases/<model>.json)")
    p.add_argument("--list-models", action="store_true")
    p.add_argument("--dry-run", action="store_true", help="Compile only; do not write file")
    p.add_argument("--self-test", action="store_true")
    args = p.parse_args()

    if args.self_test:
        kb, used = load_kb("definitely-not-a-model")
        assert kb is not None and used == "generic", "generic fallback failed"
        draft = compile_prompt("do X", kb, "also Y")
        assert "## Task" in draft and "do X" in draft and "also Y" in draft
        emit({"ok": True, "self_test": "passed", "models": list_models()})

    if args.list_models:
        emit({"ok": True, "models": list_models()})

    if sys.stdin.isatty() and sys.stdout.isatty():
        interactive(args.model)

    # Non-interactive: never call input() — require explicit flags.
    if not args.task:
        emit({"ok": False, "error": "non-interactive mode requires --task (and optionally --model, --dry-run)"}, 2)
    kb, used = load_kb(args.model or "")
    if kb is None:
        emit({"ok": False, "error": f"knowledge base unreadable for '{args.model}'"}, 1)
    draft = compile_prompt(args.task, kb)
    result = {"ok": True, "model": used, "sha256": hashlib.sha256(draft.encode()).hexdigest()}
    if args.dry_run:
        result["dry_run"] = True
        result["prompt"] = draft
    else:
        result["path"] = str(save(draft, find_repo_root()))
    emit(result)


if __name__ == "__main__":
    main()
