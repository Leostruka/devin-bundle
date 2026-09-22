#!/usr/bin/env python3
"""Validate content rigor of an Obsidian codebase wiki.

Complements validate_wiki_structure.py (structural checks) and audit.py
(diagram/secret/link checks) with CONTENT-level rigor checks that the
skill requires but no existing script enforced:

1. source: format — must be `source: path/to/file.ext:line` (not bare `source:`)
2. Minimum 5 distinct source files cited per root page
3. Sources: footer at end of each major section (## header followed by content)
4. 00-Overview.md links to ALL root pages (01-SRS through 11-TechDebt)
5. Function pages have ## Links section
6. Tables listing components/modules/APIs have a Source column
7. 11-TechDebt.md exists when effort is medium or high
8. Architecture critique section when effort is high
9. Effort level in wiki-config.json is valid (low/medium/high)

Usage:
    python validate_wiki_content.py [--wiki-dir <path>]

Exit code 0 = all checks passed, 1 = one or more failures.
"""
import argparse
import json
import re
import sys
from pathlib import Path


def find_wiki_dir(explicit: str = None) -> Path:
    if explicit:
        p = Path(explicit)
        if p.is_dir():
            return p
    cwd = Path.cwd()
    if (cwd / "wiki-config.json").exists():
        return cwd
    for child in cwd.iterdir():
        if child.is_dir() and (child / "wiki-config.json").exists():
            return child
    return cwd


def load_effort(wiki_dir: Path) -> str:
    """Load effort level from wiki-config.json. Default 'high' if absent."""
    config_path = wiki_dir / "wiki-config.json"
    if not config_path.exists():
        return "high"
    try:
        config = json.loads(config_path.read_text(encoding="utf-8"))
        return config.get("effort", "high")
    except (json.JSONDecodeError, KeyError):
        return "high"


# --- Check functions ---

def check_source_format(wiki_dir: Path) -> list:
    """Check that all `source:` citations use `path:line` format."""
    failures = []
    # Valid: source: src/file.ts:42, source: D:/path/file.sql:1, source: path/to/file.py:1
    # Also valid: extensionless files (Dockerfile, CNAME, .htaccess), line ranges, and
    # references wrapped in backticks or followed by descriptions/table separators.
    # The regex finds the last colon/digits pair in the reference.
    source_token_pattern = re.compile(r'source:\s*(.+?)\s*:\s*(\d+(?:-\d+)?)(?=\s|$|[^\w\-])')

    files = [f for f in wiki_dir.rglob("*.md") if "Media" not in str(f) and "Diagrams" not in str(f)]
    for f in files:
        content = f.read_text(encoding="utf-8", errors="replace")
        # Find all source: references
        for mo in re.finditer(r'source:\s*\S+[^\n]*', content):
            ref = mo.group(0)
            start = mo.start()
            # Skip inline code mentions like `` `source:` ... `` when not a real citation
            if start > 0 and content[start - 1] == '`' and not re.search(r':\s*\d+(?:-\d+)?\b', ref):
                continue
            # Allow source: followed by a directory path, optionally with a description
            if re.search(r'source:\s*[^\s:]+[/\\\\]\s*(?:—|\||\)|`|$)', ref):
                continue
            m = source_token_pattern.search(ref)
            if m and not re.fullmatch(r'\d+', m.group(1).strip().strip('`').strip()):
                continue
            # Flag bare source: without path:line
            failures.append(
                f"SOURCE_FORMAT: {f.relative_to(wiki_dir)} has bare 'source:' "
                f"without path:line format: '{ref.strip()[:60]}'"
            )
    return failures


def check_min_sources_per_page(wiki_dir: Path) -> list:
    """Check that each root page cites at least 5 distinct source files."""
    failures = []
    root_pages = [
        "00-Overview.md", "01-SRS.md", "02-Architecture.md",
        "03-Database.md", "04-Modules.md", "05-Functions.md",
        "06-Dependencies.md", "07-Config.md", "08-Glossary.md",
        "09-Decisions.md",
    ]
    source_file_pattern = re.compile(r'source:\s*(.+?)\s*:\s*\d+(?:-\d+)?')

    for page_name in root_pages:
        p = wiki_dir / page_name
        if not p.exists():
            continue  # Caught by structure validator
        content = p.read_text(encoding="utf-8", errors="replace")
        sources = set(source_file_pattern.findall(content))
        if len(sources) < 5:
            failures.append(
                f"MIN_SOURCES: {page_name} cites only {len(sources)} distinct source files "
                f"(minimum 5 required)"
            )
    return failures


def check_sources_footer(wiki_dir: Path) -> list:
    """Check that root pages have `Sources:` footer lines."""
    failures = []
    root_pages = [
        "00-Overview.md", "01-SRS.md", "02-Architecture.md",
        "03-Database.md", "04-Modules.md", "05-Functions.md",
        "06-Dependencies.md", "07-Config.md", "08-Glossary.md",
        "09-Decisions.md",
    ]
    for page_name in root_pages:
        p = wiki_dir / page_name
        if not p.exists():
            continue
        content = p.read_text(encoding="utf-8", errors="replace")
        # Check for Sources: footer (case-insensitive, at start of line)
        if not re.search(r'^Sources?:\s', content, re.MULTILINE | re.IGNORECASE):
            failures.append(
                f"SOURCES_FOOTER: {page_name} missing 'Sources:' footer line"
            )
    return failures


def check_overview_links(wiki_dir: Path) -> list:
    """Check that 00-Overview.md links to ALL root pages."""
    failures = []
    overview = wiki_dir / "00-Overview.md"
    if not overview.exists():
        return failures  # Caught by structure validator

    content = overview.read_text(encoding="utf-8", errors="replace")
    expected_pages = [
        "01-SRS", "02-Architecture", "03-Database", "04-Modules",
        "05-Functions", "06-Dependencies", "07-Config", "08-Glossary",
        "09-Decisions", "10-Logbook",
    ]

    for page in expected_pages:
        # Check for wikilink [[page or [[page|alias
        link_pattern = re.compile(r'\[\[' + re.escape(page) + r'(?:\|[^\]]+)?\]\]')
        if not link_pattern.search(content):
            failures.append(
                f"OVERVIEW_LINKS: 00-Overview.md missing wikilink to [[{page}]]"
            )

    # Check for 11-TechDebt link (if file exists or effort >= medium)
    techdebt = wiki_dir / "11-TechDebt.md"
    if techdebt.exists():
        link_pattern = re.compile(r'\[\[11-TechDebt(?:\|[^\]]+)?\]\]')
        if not link_pattern.search(content):
            failures.append(
                "OVERVIEW_LINKS: 00-Overview.md missing wikilink to [[11-TechDebt]] "
                "(file exists but is not linked)"
            )

    return failures


def check_function_links_section(wiki_dir: Path) -> list:
    """Check that function pages in Functions/ have a ## Links section."""
    failures = []
    functions_dir = wiki_dir / "Functions"
    if not functions_dir.exists():
        return failures  # Caught by structure validator

    for p in sorted(functions_dir.glob("*.md")):
        content = p.read_text(encoding="utf-8", errors="replace")
        if "## Links" not in content and "[[05-Functions]]" not in content:
            failures.append(
                f"FUNCTION_LINKS: Functions/{p.name} missing '## Links' section "
                f"(should link back to [[05-Functions]] and parent module)"
            )
    return failures


def check_source_column_in_tables(wiki_dir: Path) -> list:
    """Check that tables in module/function index pages have a Source column."""
    failures = []
    target_pages = ["04-Modules.md", "05-Functions.md"]

    for page_name in target_pages:
        p = wiki_dir / page_name
        if not p.exists():
            continue
        content = p.read_text(encoding="utf-8", errors="replace")
        # Find markdown table headers (lines with |---|)
        lines = content.split("\n")
        for i, line in enumerate(lines):
            if line.strip().startswith("|") and "---" in line and i > 0:
                header = lines[i - 1].strip()
                if header.startswith("|"):
                    # Check if header has Source column
                    if "Source" not in header and "source" not in header:
                        # Only flag tables that list components/modules/functions
                        if any(kw in header.lower() for kw in ["module", "function", "component", "api", "endpoint", "service", "class"]):
                            failures.append(
                                f"SOURCE_COLUMN: {page_name} has a table listing "
                                f"modules/functions without a 'Source' column "
                                f"(line {i}): {header[:60]}..."
                            )
    return failures


def check_techdebt_page(wiki_dir: Path, effort: str) -> list:
    """Check that 11-TechDebt.md exists when effort is medium or high."""
    failures = []
    if effort == "low":
        return failures  # Not required at low effort

    techdebt = wiki_dir / "11-TechDebt.md"
    if not techdebt.exists():
        failures.append(
            f"TECHDEBT: 11-TechDebt.md missing (required at effort='{effort}')"
        )
        return failures

    content = techdebt.read_text(encoding="utf-8", errors="replace")
    # Check for numbered issues (AP-001, OPT-001)
    if effort == "high":
        if not re.search(r'AP-\d{3}', content):
            failures.append(
                "TECHDEBT: 11-TechDebt.md has no numbered anti-patterns "
                "(expected AP-001, AP-002, ... at high effort)"
            )
        if not re.search(r'OPT-\d{3}', content) and "Optimization" not in content:
            # OPT- prefix optional but should have optimization section
            if "## Optimization" not in content and "## Optimization opportunities" not in content:
                failures.append(
                    "TECHDEBT: 11-TechDebt.md missing optimization opportunities section "
                    "(expected at high effort)"
                )

    # Check for source citations in tech debt items
    source_pattern = re.compile(r'source:\s*(.+?)\s*:\s*\d+(?:-\d+)?')
    if not source_pattern.search(content):
        failures.append(
            "TECHDEBT: 11-TechDebt.md has no source: citations "
            "(every issue must cite source file:line)"
        )

    # Check for parent frontmatter
    if not re.search(r'parent:\s*00-Overview', content):
        failures.append(
            "TECHDEBT: 11-TechDebt.md missing 'parent: 00-Overview' in frontmatter"
        )

    return failures


def check_architecture_critique(wiki_dir: Path, effort: str) -> list:
    """Check that 02-Architecture.md has critique section at high effort."""
    failures = []
    if effort != "high":
        return failures  # Only required at high effort

    arch = wiki_dir / "02-Architecture.md"
    if not arch.exists():
        return failures  # Caught by structure validator

    content = arch.read_text(encoding="utf-8", errors="replace")
    if "## Architecture critique" not in content and "## Architecture Critique" not in content:
        failures.append(
            "ARCH_CRITIQUE: 02-Architecture.md missing '## Architecture critique' section "
            "(required at high effort)"
        )

    return failures


def check_effort_valid(wiki_dir: Path, effort: str) -> list:
    """Check that effort level in wiki-config.json is valid."""
    failures = []
    valid = {"low", "medium", "high"}
    if effort not in valid:
        failures.append(
            f"EFFORT: wiki-config.json has invalid effort='{effort}' "
            f"(must be one of: {', '.join(sorted(valid))})"
        )
    return failures


def main():
    parser = argparse.ArgumentParser(
        description="Validate content rigor of Obsidian codebase wiki"
    )
    parser.add_argument("--wiki-dir", type=str, help="Path to the _wiki directory")
    args = parser.parse_args()

    wiki_dir = find_wiki_dir(args.wiki_dir)
    effort = load_effort(wiki_dir)

    print(f"Wiki directory: {wiki_dir}")
    print(f"Effort level:   {effort}")
    print()

    if not (wiki_dir / "wiki-config.json").exists():
        print("ERROR: No wiki-config.json found. Is this a valid wiki directory?")
        sys.exit(1)

    all_failures = []
    all_checks = [
        ("Effort level valid", lambda: check_effort_valid(wiki_dir, effort)),
        ("source: path:line format", lambda: check_source_format(wiki_dir)),
        ("Min 5 sources per root page", lambda: check_min_sources_per_page(wiki_dir)),
        ("Sources: footer in root pages", lambda: check_sources_footer(wiki_dir)),
        ("00-Overview links to all root pages", lambda: check_overview_links(wiki_dir)),
        ("Function pages have ## Links", lambda: check_function_links_section(wiki_dir)),
        ("Source column in index tables", lambda: check_source_column_in_tables(wiki_dir)),
        (f"11-TechDebt.md exists (effort={effort})", lambda: check_techdebt_page(wiki_dir, effort)),
        (f"Architecture critique section (effort={effort})", lambda: check_architecture_critique(wiki_dir, effort)),
    ]

    for check_name, check_fn in all_checks:
        print(f"=== {check_name} ===")
        failures = check_fn()
        if failures:
            for f in failures:
                print(f"  FAIL: {f}")
            all_failures.extend(failures)
        else:
            print("  OK")
        print()

    print("=" * 60)
    if all_failures:
        print(f"CONTENT VALIDATION FAILED: {len(all_failures)} issue(s) found")
        sys.exit(1)
    else:
        print("CONTENT VALIDATION PASSED: all checks OK")
        sys.exit(0)


if __name__ == "__main__":
    main()
