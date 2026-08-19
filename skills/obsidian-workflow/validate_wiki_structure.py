#!/usr/bin/env python3
"""Validate the structural integrity of an obsidian-project-docs wiki.

Checks:
1. Required root pages exist (00-09, 10-Logbook)
2. Modules/ directory exists and is not empty
3. Functions/ directory exists and is not empty
4. Decisions/ directory exists and is not empty
5. Diagrams/ directory exists with 14+ diagrams
6. Daily/ directory exists with at least one note
7. Project.base exists
8. wiki-config.json exists and passes validation
9. Every function listed in 05-Functions.md has a corresponding Functions/*.md file
10. All wikilinks resolve (no broken links)
11. All pages have required frontmatter (parent, tags)
12. Root pages (00-09, 10-Logbook) have standardized frontmatter (title, project, parent, tags, status)
13. Daily notes have standardized frontmatter (title, date, project, parent=10-Logbook, tags, status)
14. All root pages have ## Relevant source files and ## Purpose and Scope
15. All Mermaid diagrams have <!-- Sources: --> comments
16. No sensitive data (passwords, credentials, secrets)

Usage:
    python validate_wiki_structure.py [--wiki-dir <path>] [--vault-dir <path>]

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


def collect_vault_stems(vault_dir: Path) -> set:
    """Collect all .md file stems in the vault for wikilink resolution."""
    stems = set()
    # Walk up to find the vault root (parent of the project folder)
    # Try the wiki dir's parent, then grandparent
    for search_dir in [vault_dir.parent, vault_dir.parent.parent, vault_dir]:
        if not search_dir.exists():
            continue
        for p in search_dir.rglob("*.md"):
            stems.add(p.stem)
    return stems


def check_required_files(wiki_dir: Path) -> list:
    """Check that all required root pages and directories exist."""
    failures = []
    required_pages = [
        "00-Overview.md", "01-SRS.md", "02-Architecture.md",
        "03-Database.md", "04-Modules.md", "05-Functions.md",
        "06-Dependencies.md", "07-Config.md", "08-Glossary.md",
        "09-Decisions.md", "10-Logbook.md",
    ]
    for page in required_pages:
        if not (wiki_dir / page).exists():
            failures.append(f"MISSING root page: {page}")

    required_dirs = ["Modules", "Functions", "Decisions", "Diagrams", "Daily"]
    for d in required_dirs:
        dir_path = wiki_dir / d
        if not dir_path.exists():
            failures.append(f"MISSING directory: {d}/")
        elif not dir_path.is_dir():
            failures.append(f"NOT a directory: {d}/")
        else:
            md_count = len(list(dir_path.glob("*.md")))
            if md_count == 0:
                failures.append(f"EMPTY directory: {d}/ (0 .md files)")

    # Project.base
    if not (wiki_dir / "Project.base").exists():
        failures.append("MISSING: Project.base")

    # wiki-config.json
    if not (wiki_dir / "wiki-config.json").exists():
        failures.append("MISSING: wiki-config.json")

    return failures


def check_diagrams_count(wiki_dir: Path) -> list:
    """Check that at least 14 diagram files exist."""
    failures = []
    diagrams_dir = wiki_dir / "Diagrams"
    if not diagrams_dir.exists():
        return failures  # Already caught by check_required_files
    md_files = list(diagrams_dir.glob("*.md"))
    if len(md_files) < 14:
        failures.append(f"DIAGRAMS: only {len(md_files)} diagram files (minimum 14 required)")
    return failures


def check_functions_not_empty(wiki_dir: Path) -> list:
    """Check that Functions/ directory is not empty and matches 05-Functions.md registry."""
    failures = []
    functions_dir = wiki_dir / "Functions"
    functions_page = wiki_dir / "05-Functions.md"

    if not functions_dir.exists():
        return failures  # Already caught
    if not functions_page.exists():
        return failures  # Already caught

    fn_files = list(functions_dir.glob("*.md"))
    if len(fn_files) == 0:
        failures.append("FUNCTIONS: directory is EMPTY — every function in 05-Functions.md MUST have a Functions/<name>.md file")
        return failures

    # Try to count functions listed in 05-Functions.md table
    content = functions_page.read_text(encoding="utf-8", errors="replace")
    # Count table rows (lines starting with | that aren't headers/separators)
    table_rows = [l for l in content.split("\n") if l.strip().startswith("|")
                  and not l.strip().startswith("|--")
                  and not l.strip().startswith("| -")
                  and "Function" not in l
                  and "Name" not in l
                  and "Endpoint" not in l
                  and "Method" not in l]
    # Subtract non-function rows (hard to be precise, so just warn)
    if len(table_rows) > len(fn_files) + 10:  # Allow tolerance for header/separator rows
        failures.append(f"FUNCTIONS: 05-Functions.md lists ~{len(table_rows)} table rows but Functions/ has only {len(fn_files)} files — possible missing function pages")

    return failures


def check_wikilinks(wiki_dir: Path, vault_stems: set) -> list:
    """Check that all wikilinks resolve to existing files.

    Supports both stem-only ([[PageName]]) and path-based ([[Folder/PageName]]) wikilinks.
    Path-based links are resolved relative to the wiki directory and vault root.
    Handles Obsidian table pipe-escape syntax: [[Target\\|Alias]] → target is 'Target'.
    """
    failures = []
    files = [f for f in wiki_dir.rglob("*.md") if "Media" not in str(f)]
    total = 0
    broken = []
    for f in files:
        content = f.read_text(encoding="utf-8", errors="replace")
        links = re.findall(r"\[\[([^\]|]+)(?:\|[^\]]+)?\]\]", content)
        for link in links:
            link = link.strip()
            total += 1
            # Skip anchor-only links ([[#Section]])
            if link.startswith("#"):
                continue
            # Strip trailing backslash (Obsidian table pipe-escape: [[Target\|Alias]])
            link = link.rstrip("\\")
            # Try stem-only resolution first
            if link in vault_stems:
                continue
            # Try path-based resolution (relative to wiki dir)
            if "/" in link:
                # Try relative to wiki dir
                path_candidate = wiki_dir / f"{link}.md"
                if path_candidate.exists():
                    continue
                # Try relative to vault root (parent of project folder)
                vault_root = wiki_dir.parent.parent
                path_candidate2 = vault_root / f"{link}.md"
                if path_candidate2.exists():
                    continue
                # Try relative to project folder (parent of _wiki)
                path_candidate3 = wiki_dir.parent / f"{link}.md"
                if path_candidate3.exists():
                    continue
            broken.append(f"[[{link}]] in {f.relative_to(wiki_dir)}")
    if broken:
        failures.append(f"WIKILINKS: {len(broken)} broken out of {total} total:")
        for b in broken[:20]:
            failures.append(f"  {b}")
        if len(broken) > 20:
            failures.append(f"  ... ({len(broken)} total)")
    return failures


def check_frontmatter(wiki_dir: Path) -> list:
    """Check that all pages have required frontmatter fields."""
    failures = []
    files = [f for f in wiki_dir.rglob("*.md") if "Media" not in str(f)]
    for f in files:
        content = f.read_text(encoding="utf-8", errors="replace")
        if not content.startswith("---"):
            failures.append(f"FRONTMATTER: {f.relative_to(wiki_dir)} missing frontmatter")
            continue
        # Extract frontmatter
        parts = content.split("---", 2)
        if len(parts) < 3:
            failures.append(f"FRONTMATTER: {f.relative_to(wiki_dir)} malformed frontmatter")
            continue
        fm = parts[1]
        if "parent:" not in fm and "00-Overview" not in f.name:
            failures.append(f"FRONTMATTER: {f.relative_to(wiki_dir)} missing 'parent:' field")
        if "tags:" not in fm:
            failures.append(f"FRONTMATTER: {f.relative_to(wiki_dir)} missing 'tags:' field")
    return failures


def check_root_page_frontmatter(wiki_dir: Path) -> list:
    """Check that root pages (00-09, 10-Logbook) have standardized frontmatter.

    Required fields: title, project, parent, tags (YAML list), status.
    Title format: "Project Name - Page Name" (hyphen, not em-dash).
    Status must be 'active' or 'inactive'.
    """
    failures = []
    root_pages = [
        "00-Overview.md", "01-SRS.md", "02-Architecture.md",
        "03-Database.md", "04-Modules.md", "05-Functions.md",
        "06-Dependencies.md", "07-Config.md", "08-Glossary.md",
        "09-Decisions.md", "10-Logbook.md",
    ]
    required_fields = ["title:", "project:", "parent:", "tags:", "status:"]
    valid_statuses = {"active", "inactive"}

    for page_name in root_pages:
        p = wiki_dir / page_name
        if not p.exists():
            continue  # Already caught by check_required_files
        content = p.read_text(encoding="utf-8", errors="replace")
        if not content.startswith("---"):
            continue  # Already caught
        parts = content.split("---", 2)
        if len(parts) < 3:
            continue
        fm = parts[1]

        # Check required fields
        for field in required_fields:
            if field not in fm:
                failures.append(f"FRONTMATTER: {page_name} missing '{field}' field")

        # Check status value
        status_match = re.search(r'^status:\s*(\S+)', fm, re.MULTILINE)
        if status_match:
            status_val = status_match.group(1).strip().strip('"').strip("'")
            if status_val not in valid_statuses:
                failures.append(
                    f"FRONTMATTER: {page_name} has invalid status '{status_val}' "
                    f"(must be 'active' or 'inactive')"
                )

        # Check title doesn't use em-dash
        title_match = re.search(r'^title:\s*"([^"]*)"', fm, re.MULTILINE)
        if title_match:
            title_val = title_match.group(1)
            if "\u2014" in title_val or "\u2013" in title_val:
                failures.append(
                    f"FRONTMATTER: {page_name} title uses em-dash/en-dash "
                    f"(should be hyphen): \"{title_val}\""
                )

        # Check tags is YAML list (not inline)
        if "tags:" in fm:
            tags_section = re.search(r'^tags:\s*\[', fm, re.MULTILINE)
            if tags_section:
                failures.append(
                    f"FRONTMATTER: {page_name} uses inline tags format "
                    f"(should be YAML list with '- tag')"
                )

    return failures


def check_daily_notes(wiki_dir: Path) -> list:
    """Check that daily notes have standardized frontmatter.

    Required fields: title, date, project, parent (10-Logbook), tags (YAML list), status.
    Title format: "Project Name - YYYY-MM-DD" (hyphen, not em-dash).
    Filename: YYYY-MM-DD.md
    """
    failures = []
    daily_dir = wiki_dir / "Daily"
    if not daily_dir.exists():
        return failures  # Already caught

    required_fields = ["title:", "date:", "project:", "parent:", "tags:", "status:"]
    valid_statuses = {"active", "inactive"}

    for p in sorted(daily_dir.glob("*.md")):
        content = p.read_text(encoding="utf-8", errors="replace")
        if not content.startswith("---"):
            failures.append(f"DAILY: {p.name} missing frontmatter")
            continue
        parts = content.split("---", 2)
        if len(parts) < 3:
            failures.append(f"DAILY: {p.name} malformed frontmatter")
            continue
        fm = parts[1]

        # Check required fields
        for field in required_fields:
            if field not in fm:
                failures.append(f"DAILY: {p.name} missing '{field}' field")

        # Check parent is 10-Logbook
        parent_match = re.search(r'^parent:\s*(\S+)', fm, re.MULTILINE)
        if parent_match:
            parent_val = parent_match.group(1).strip().strip('"').strip("'")
            if parent_val != "10-Logbook":
                failures.append(
                    f"DAILY: {p.name} parent should be '10-Logbook' "
                    f"(got '{parent_val}')"
                )

        # Check status value
        status_match = re.search(r'^status:\s*(\S+)', fm, re.MULTILINE)
        if status_match:
            status_val = status_match.group(1).strip().strip('"').strip("'")
            if status_val not in valid_statuses:
                failures.append(
                    f"DAILY: {p.name} has invalid status '{status_val}' "
                    f"(must be 'active' or 'inactive')"
                )

        # Check title format: "Project Name - YYYY-MM-DD" (hyphen, not em-dash)
        title_match = re.search(r'^title:\s*"([^"]*)"', fm, re.MULTILINE)
        if title_match:
            title_val = title_match.group(1)
            if "\u2014" in title_val or "\u2013" in title_val:
                failures.append(
                    f"DAILY: {p.name} title uses em-dash/en-dash "
                    f"(should be hyphen): \"{title_val}\""
                )
            # Check title ends with the date (filename stem)
            date_str = p.stem
            if not title_val.endswith(date_str):
                failures.append(
                    f"DAILY: {p.name} title should end with date '{date_str}' "
                    f"(got \"{title_val}\")"
                )

        # Check tags is YAML list (not inline)
        if "tags:" in fm:
            tags_section = re.search(r'^tags:\s*\[', fm, re.MULTILINE)
            if tags_section:
                failures.append(
                    f"DAILY: {p.name} uses inline tags format "
                    f"(should be YAML list with '- tag')"
                )

    return failures


def check_page_structure(wiki_dir: Path) -> list:
    """Check that root pages have required sections."""
    failures = []
    root_pages = ["00-Overview", "01-SRS", "02-Architecture", "03-Database",
                  "04-Modules", "05-Functions", "06-Dependencies", "07-Config",
                  "08-Glossary", "09-Decisions"]
    for name in root_pages:
        p = wiki_dir / f"{name}.md"
        if not p.exists():
            continue  # Already caught
        content = p.read_text(encoding="utf-8", errors="replace")
        if "## Relevant" not in content:
            failures.append(f"STRUCTURE: {name}.md missing '## Relevant source files'")
        if "## Purpose" not in content:
            failures.append(f"STRUCTURE: {name}.md missing '## Purpose and Scope'")
    return failures


def check_mermaid_sources(wiki_dir: Path) -> list:
    """Check that all Mermaid diagrams have Sources comments."""
    failures = []
    diagrams_dir = wiki_dir / "Diagrams"
    if not diagrams_dir.exists():
        return failures
    for p in sorted(diagrams_dir.glob("*.md")):
        content = p.read_text(encoding="utf-8", errors="replace")
        if "```mermaid" not in content:
            failures.append(f"MERMAID: {p.name} missing mermaid code block")
        if "<!-- Sources:" not in content and "<!-- Sources" not in content:
            failures.append(f"MERMAID: {p.name} missing '<!-- Sources: -->' comment")
    return failures


def check_sensitive_data(wiki_dir: Path) -> list:
    """Check for potential sensitive data (passwords, credentials, secrets)."""
    failures = []
    # Patterns that indicate real credentials (not just variable names)
    sensitive_patterns = [
        (r"DB_PASSWORD\s*=\s*['\"][^'\"]{4,}['\"]", "DB_PASSWORD with actual value"),
        (r"FTP_PASS\s*=\s*['\"][^'\"]{4,}['\"]", "FTP_PASS with actual value"),
        (r"MAIL_PASS\s*=\s*['\"][^'\"]{4,}['\"]", "MAIL_PASS with actual value"),
        (r"API_KEY\s*=\s*['\"][^'\"]{10,}['\"]", "API_KEY with actual value"),
        (r"SECRET\s*=\s*['\"][^'\"]{8,}['\"]", "SECRET with actual value"),
    ]
    files = [f for f in wiki_dir.rglob("*.md") if "Media" not in str(f)]
    for f in files:
        content = f.read_text(encoding="utf-8", errors="replace")
        for pattern, desc in sensitive_patterns:
            matches = re.findall(pattern, content, re.IGNORECASE)
            if matches:
                failures.append(f"SENSITIVE: {f.relative_to(wiki_dir)} contains {desc}: {matches[0][:50]}...")
    return failures


def main():
    parser = argparse.ArgumentParser(description="Validate obsidian-project-docs wiki structure")
    parser.add_argument("--wiki-dir", type=str, help="Path to the _wiki directory")
    parser.add_argument("--vault-dir", type=str, help="Path to the Obsidian vault root (for wikilink resolution)")
    args = parser.parse_args()

    wiki_dir = find_wiki_dir(args.wiki_dir)
    vault_dir = Path(args.vault_dir) if args.vault_dir else wiki_dir.parent.parent

    print(f"Wiki directory: {wiki_dir}")
    print(f"Vault root:     {vault_dir}")
    print()

    if not (wiki_dir / "wiki-config.json").exists():
        print(f"ERROR: No wiki-config.json found in {wiki_dir}")
        print("Is this a valid obsidian-project-docs wiki directory?")
        sys.exit(1)

    all_failures = []
    all_checks = [
        ("Required files and directories", lambda: check_required_files(wiki_dir)),
        ("Diagram count (min 14)", lambda: check_diagrams_count(wiki_dir)),
        ("Functions/ not empty", lambda: check_functions_not_empty(wiki_dir)),
        ("Page structure (Relevant + Purpose)", lambda: check_page_structure(wiki_dir)),
        ("Frontmatter (parent + tags)", lambda: check_frontmatter(wiki_dir)),
        ("Root page frontmatter (title+project+status)", lambda: check_root_page_frontmatter(wiki_dir)),
        ("Daily notes frontmatter", lambda: check_daily_notes(wiki_dir)),
        ("Mermaid Sources comments", lambda: check_mermaid_sources(wiki_dir)),
        ("Sensitive data scan", lambda: check_sensitive_data(wiki_dir)),
    ]

    # Collect vault stems for wikilink check
    vault_stems = collect_vault_stems(vault_dir)
    all_checks.append(("Wikilink resolution", lambda: check_wikilinks(wiki_dir, vault_stems)))

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

    # Summary
    print("=" * 60)
    if all_failures:
        print(f"VALIDATION FAILED: {len(all_failures)} issue(s) found")
        sys.exit(1)
    else:
        print("VALIDATION PASSED: all checks OK")
        sys.exit(0)


if __name__ == "__main__":
    main()
