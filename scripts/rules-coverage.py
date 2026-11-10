#!/usr/bin/env python3
"""rules-coverage — map natural-language rules to deterministic controls.

For each enforceable clause in rule files (modal markers: never/must/
don't/always/refuse/require/deny), reports which concrete control backs
it (hook script, audit check, permission rule) or flags it unenforced.

Inspired by arXiv 2608.23550: only ~4-16% of CLAUDE.md security rules
map to a built-in control - this audit makes the coverage explicit.

Usage: rules-coverage.py [RULE_FILE ...]     (JSON to stdout)
"""
import json
import os
import re
import sys

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

MODAL = re.compile(
    r"\b(never|must|always|don't|do not|refuse|required|require|"
    r"deny|block|no \w+ without|only|forbidden|prohibit)\b", re.I)
# Section headers / pure-prose lines are not enforceable clauses
NON_RULE = re.compile(r"^\s*(#|\*|>|```|rule |source|\||\[)")

# keyword -> deterministic control(s) backing the clause
CONTROL_REGISTRY = [
    (r"secret|api key|password|token|private key|credential",
     ["scripts/destructive-gate.py", "config permissions.deny"]),
    (r"co-?authored|signature", ["scripts/check-ai-signature.py"]),
    (r"push.*(green|without)|green.*push|failing.*test|test.*fail",
     ["scripts/check-push-green.py", "CI pytest matrix"]),
    (r"delet|disabl|skip|remov.*test|test.*remov",
     ["scripts/check-push-green.py", "audit.py"]),
    (r"em[- ]?dash", ["scripts/no-em-dash.py"]),
    (r"architecture|manifest", ["scripts/architecture-gate.py",
                                ".devin/ARCHITECTURE_MANIFEST.md"]),
    (r"utf-?8|encoding|text=true|stdin|codepage|cp1252",
     ["audit.py [37]", "audit.py [38]", "audit.py [39]"]),
    (r"ok.*false|exit.*(non-?zero|code)|envelope",
     ["audit.py [36]"]),
    (r"overwrit|refuse.*exist|truncate",
     ["scripts/pre-write-guard.py"]),
    (r"file.*size|800.*(line|loc)|line.*limit",
     ["scripts/file-size-guard.py"]),
    (r"design|contrast|a11y|accessib", ["scripts/design-lint-gate.py"]),
    (r"mermaid", ["scripts/validate-mermaid.py"]),
    (r"skill.*format|skill\.md", ["scripts/validate-skill-format.py"]),
    (r"dependen|dep-|vulnerab|package", ["scripts/dep-audit-gate.py",
                                         "scripts/dep-audit.py"]),
    (r"spec.*consist|consist.*spec", ["scripts/spec-consistency.py"]),
    (r"tool.*arg|arg.*valid", ["scripts/validate-tool-args.py"]),
    (r"write.*(outside|guard)|edit.*guard", ["scripts/pre-write-guard.py"]),
    (r"destruct|rm -rf|force.*push|dangerous",
     ["scripts/destructive-gate.py", "scripts/pre-exec-guard.py"]),
    (r"exec|command.*guard|shell", ["scripts/pre-exec-guard.py"]),
    (r"compact|context.*(budget|pressure)|token.*budget",
     ["scripts/compact-gate.py", "scripts/context-budget.py",
      "scripts/context-pressure.py"]),
    (r"refine|evidence|held-?out|validation",
     ["scripts/validate-refinement-evidence.py", "tests/held-out/"]),
    (r"hook", ["scripts/_hookrun.py", "scripts/render-user-hooks.py",
               "hooks.v1.json"]),
    (r"laya|decision.*(model|gate)", ["scripts/laya-guard.py",
                                      "extensions/laya-tools/"]),
    (r"memory|memories", ["scripts/memory-retrieval.py",
                          "scripts/memory-post-edit.py",
                          "scripts/memory-post-exec.py",
                          "scripts/memory-stop.py"]),
    (r"status.*vocab|vocab|triage", ["scripts/status_vocab.py",
                                     ".devin/agents/triage-labels.md"]),
    (r"stuck|loop.*detect", ["scripts/stuck-detect.py"]),
    (r"constraint.*pin|pin.*constraint|pinned",
     ["scripts/constraint-pinning.py"]),
    (r"silent.*error|error.*swallow", ["scripts/silent-error-review.py"]),
    (r"install|ledger|export", ["scripts/install-ledger.py",
                                "scripts/check-tools.py", "export.ps1"]),
    (r"audit", ["audit.py"]),
    (r"sandbox|permission|trust", ["devin --sandbox", "--permission-mode",
                                   "permissions.deny"]),
    (r"model|tier|cost", ["data/bundle-models.json"]),
    (r"issue|tracker|status", ["scripts/roadmap-board.py",
                               ".devin/agents/issue-tracker.md"]),
    (r"commit|message|trailer", ["scripts/check-ai-signature.py"]),
    (r"roadmap|dag|capacity|wip", ["scripts/roadmap-board.py"]),
    (r"calendar|gcal|schedule", ["extensions/gcal/wrapper.py"]),
    (r"subagent|dispatch", ["skills/dispatching-parallel-agents/"]),
    (r"goal|objective", ["scripts/focus.py"]),
]

DEFAULT_RULE_FILES = [".devin/global_rules.md"]


def clause_lines(path):
    out = []
    try:
        with open(path, encoding="utf-8", errors="replace") as f:
            for n, line in enumerate(f, 1):
                s = line.strip()
                if not s or NON_RULE.match(line):
                    continue
                if MODAL.search(s):
                    out.append((n, s[:300]))
    except OSError as e:
        print(json.dumps({"ok": False, "error": f"{path}: {e}"}))
        sys.exit(2)
    return out


def controls_for(text):
    hits = []
    for pat, controls in CONTROL_REGISTRY:
        if re.search(pat, text, re.I):
            hits.extend(controls)
    return sorted(set(hits))


def main(argv):
    files = argv[1:]
    if not files:
        files = list(DEFAULT_RULE_FILES)
        # user-level AGENTS.md is merged in sessions; include if present
        user_rules = os.path.join(os.environ.get("APPDATA", ""), "devin",
                                  "AGENTS.md")
        if os.path.exists(user_rules):
            files.append(user_rules)
    rules, uncovered = [], 0
    for path in files:
        for n, text in clause_lines(path):
            controls = controls_for(text)
            if not controls:
                uncovered += 1
            rules.append({"file": path, "line": n, "text": text,
                          "controls": controls, "covered": bool(controls)})
    print(json.dumps({"ok": True,
                      "scanned_files": files,
                      "enforceable_clauses": len(rules),
                      "covered": len(rules) - uncovered,
                      "uncovered": uncovered,
                      "coverage": round(
                          (len(rules) - uncovered) / max(len(rules), 1), 4),
                      "rules": rules}, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
