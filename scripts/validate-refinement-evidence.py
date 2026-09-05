#!/usr/bin/env python3
"""Validates refinement evidence from refinements.log.jsonl.

Checks each refinement entry to see if the cited evidence includes a
reproducible command or tool call. Flags entries with vague evidence
as "phantom guardrail suspects."

Usage:
  python validate-refinement-evidence.py [path/to/refinements.log.jsonl]

If no path given, checks:
  1. .devin/refinements.log.jsonl (project)
  2. ~/.config/devin/refinements.log.jsonl (global)

Source: "Phantom Guardrails" (Wang et al., arXiv:2607.13083)
  15/60 runs (25%) of self-improving agents invent failures.
  Phantom guardrails persist in add-only accept loops.
  Evidence without reproduction is a phantom, not a pattern.

Also: "Reward Hacking in Self-Improving Code Agents" (ICLR 2026 Workshop)
  73.8% Kernel-Bench, 46.8% ALE-Bench optimizations show proxy gains
  without real gains. Always validate with held-out tests.
"""
import sys, json, os, re


def devin_home():
    """Return the Devin user config home.

    Windows: %APPDATA%\\devin
    Unix: $XDG_CONFIG_HOME/devin or ~/.config/devin
    """
    appdata = os.environ.get("APPDATA", "")
    if appdata:
        return os.path.join(appdata, "devin")
    xdg = os.environ.get("XDG_CONFIG_HOME", "")
    if xdg:
        return os.path.join(xdg, "devin")
    return os.path.join(os.path.expanduser("~"), ".config", "devin")


# Patterns that indicate reproducible evidence
REPRODUCIBLE_PATTERNS = [
    re.compile(r"(exec|run|command|cmd)\s*[:=]\s*", re.IGNORECASE),
    re.compile(r"(python|pytest|npm|cargo|go|git|gh)\s+\S+", re.IGNORECASE),
    re.compile(r"(test|spec|check|lint|build)\s+", re.IGNORECASE),
    re.compile(r"(error|traceback|fail|exception)\s*[:=]?\s*\S+", re.IGNORECASE),
    re.compile(r"(exit\s+code|return\s+code)\s*[:=]?\s*\d+", re.IGNORECASE),
    re.compile(r"(file|path|line)\s*[:=]\s*\S+", re.IGNORECASE),
    re.compile(r"(arxiv|doi|http|url)\s*[:=]?\s*\S+", re.IGNORECASE),
    # PowerShell cmdlets (Windows runtime) — Select-String, Get-ChildItem, etc.
    re.compile(r"(Select-String|Get-ChildItem|Get-Content|Add-Content|Set-Content|Invoke-WebRequest|Measure-Object)\s+", re.IGNORECASE),
    # Matched results / returned N matches / lines N, M
    re.compile(r"returned\s+\d+\s+match", re.IGNORECASE),
    # Devin CLI tool calls (read, grep, glob, find_file_by_name, run_subagent, etc.)
    re.compile(r"\b(?:read|grep|glob|find_file_by_name|run_subagent|web_search|webfetch|mcp_call_tool|write|edit|exec)\b.*[:\s]", re.IGNORECASE),
]

# Vague evidence patterns (likely phantom)
VAGUE_PATTERNS = [
    re.compile(r"\bI think\b", re.IGNORECASE),
    re.compile(r"\bseems like\b", re.IGNORECASE),
    re.compile(r"\bprobably\b", re.IGNORECASE),
    re.compile(r"\bmight have\b", re.IGNORECASE),
    re.compile(r"\bappears to\b", re.IGNORECASE),
    re.compile(r"\bI noticed\b", re.IGNORECASE),
]


def find_log_path():
    """Find the refinements log file."""
    # Check command line arg
    if len(sys.argv) > 1 and os.path.exists(sys.argv[1]):
        return sys.argv[1]

    # Check project-local
    project = os.path.join(os.getcwd(), ".devin", "refinements.log.jsonl")
    if os.path.exists(project):
        return project

    # Check Devin user home
    global_path = os.path.join(devin_home(), "refinements.log.jsonl")
    if os.path.exists(global_path):
        return global_path

    return None


def has_reproducible_evidence(evidence):
    """Check if evidence string contains reproducible commands or references."""
    if not evidence:
        return False
    return any(pattern.search(evidence) for pattern in REPRODUCIBLE_PATTERNS)


def has_vague_evidence(evidence):
    """Check if evidence string uses vague language."""
    if not evidence:
        return True
    return any(pattern.search(evidence) for pattern in VAGUE_PATTERNS)


def validate_entry(entry):
    """Validate one refinement entry.

    Returns (category, issues) where category is "valid", "phantom" or "suspect".
    "phantom" means the evidence may describe a failure that never happened
    (missing/vague/non-reproducible). "suspect" means the evidence is concrete
    but the claimed outcome is not backed by held-out validation.
    """
    issues = []
    phantom = False
    evidence = entry.get("evidence", "") or ""

    if not evidence.strip():
        issues.append("no evidence field")
        phantom = True
    else:
        if not has_reproducible_evidence(evidence):
            issues.append("evidence lacks a reproducible command or source reference")
            phantom = True
        if has_vague_evidence(evidence):
            issues.append("evidence uses vague language (I think / seems like / probably)")
            phantom = True

    if entry.get("outcome", "") == "helped":
        if not any(
            kw in evidence.lower()
            for kw in ("held-out", "holdout", "held out", "validation", "test")
        ):
            issues.append(
                "outcome='helped' without held-out validation - may be an illusory "
                "gain (47-74% of self-improvement gains are illusory)"
            )

    if not issues:
        return "valid", issues
    return ("phantom" if phantom else "suspect"), issues


def main():
    log_path = find_log_path()
    if not log_path:
        print("No refinements.log.jsonl found. Nothing to validate.", file=sys.stderr)
        print("\nRefinement Evidence Validation Summary:", file=sys.stderr)
        print("  Total: 0  Valid: 0  Phantom suspects: 0  Other suspects: 0", file=sys.stderr)
        sys.exit(0)

    total = 0
    phantoms = 0
    suspect = 0
    valid = 0

    try:
        with open(log_path, "r", encoding="utf-8") as f:
            for line_num, line in enumerate(f, 1):
                line = line.strip()
                if not line:
                    continue
                try:
                    entry = json.loads(line)
                except json.JSONDecodeError:
                    print(f"Line {line_num}: invalid JSON, skipping", file=sys.stderr)
                    continue

                total += 1

                # Skip rolled-back entries — they are no longer active
                if entry.get("status") == "rolled-back":
                    continue

                category, issues = validate_entry(entry)
                ref_id = entry.get("id", "?")

                if category == "valid":
                    valid += 1
                elif category == "phantom":
                    phantoms += 1
                    print(
                        f"PHANTOM SUSPECT (line {line_num}, id={ref_id}): "
                        + "; ".join(issues),
                        file=sys.stderr,
                    )
                else:
                    suspect += 1
                    print(
                        f"SUSPECT (line {line_num}, id={ref_id}): " + "; ".join(issues),
                        file=sys.stderr,
                    )

    except (OSError, IOError) as e:
        print(f"Error reading log: {e}", file=sys.stderr)
        sys.exit(0)

    print(f"\nRefinement Evidence Validation Summary:", file=sys.stderr)
    print(f"  Total: {total}  Valid: {valid}  Phantom suspects: {phantoms}  Other suspects: {suspect}", file=sys.stderr)

    if phantoms > 0:
        print(f"\n  WARNING: {phantoms} refinement(s) may be phantom guardrails.", file=sys.stderr)
        print(f"  25% of self-improvement runs invent failures (arXiv:2607.13083).", file=sys.stderr)
        print(f"  Review evidence before trusting these refinements.", file=sys.stderr)

    if suspect > 0:
        print(f"\n  WARNING: {suspect} refinement(s) lack held-out validation.", file=sys.stderr)
        print(f"  47-74% of self-improvement gains are illusory (ICLR 2026 Workshop).", file=sys.stderr)

    sys.exit(0)

if __name__ == "__main__":
    main()
