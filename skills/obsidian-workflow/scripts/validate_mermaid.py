#!/usr/bin/env python3
"""Validate Mermaid syntax in Obsidian wiki diagram files.

Two-layer validation:
1. Regex checks for common structural errors (fence, sources inside, etc.)
2. Node-based mermaid.parse() for real syntax validation (no Chromium needed)

Usage:
    python validate_mermaid.py --wiki <wiki-dir>
    python validate_mermaid.py --base <projects-dir>
    python validate_mermaid.py --vault <vault-dir>
"""

import argparse
import os
import re
import subprocess
import sys

# Path to the Node-based mermaid parser
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PARSE_CHECK_JS = os.path.join(
    os.path.dirname(os.path.dirname(SCRIPT_DIR)), "scripts", "mermaid-parse-check.js"
)
# Fallback: global scripts dir
if not os.path.isfile(PARSE_CHECK_JS):
    PARSE_CHECK_JS = os.path.join(
        os.environ.get("APPDATA", ""), "devin", "scripts", "mermaid-parse-check.js"
    )


def check_mermaid_regex(content, filename):
    """Check a file's content for Mermaid structural issues. Returns list of (issue_type, description)."""
    issues = []

    mermaid_blocks = list(re.finditer(r'(`{2,3})mermaid\n(.*?)\1', content, re.DOTALL))

    if not mermaid_blocks:
        if re.search(r'`mermaid', content):
            issues.append(('MALFORMED_FENCE', 'Found `mermaid but not properly fenced with triple backticks'))
        else:
            issues.append(('NO_MERMAID', 'No ```mermaid block found'))
        return issues

    for block_match in mermaid_blocks:
        fence = block_match.group(1)
        mermaid = block_match.group(2)

        if fence != '```':
            issues.append(('WRONG_FENCE', f'Uses {fence}mermaid instead of ```mermaid'))

        if re.search(r'<!-- Sources:', mermaid):
            issues.append(('SOURCES_INSIDE_MERMAID', '<!-- Sources: --> is inside ```mermaid block (should be outside)'))

        if '<br///' in mermaid:
            issues.append(('BR_TRIPLE_SLASH', '<br/// found (should be <br/>)'))

        for i, line in enumerate(mermaid.split('\n'), 1):
            stripped = line.strip()
            if re.match(r'^\w+\s+fill:', stripped) and not stripped.startswith('style'):
                issues.append(('MISSING_STYLE_KEYWORD', f'L{i}: {stripped[:60]}'))

        subgraph_count = sum(1 for l in mermaid.split('\n') if l.strip().startswith('subgraph'))
        end_count = sum(1 for l in mermaid.split('\n') if l.strip() == 'end')
        if subgraph_count != end_count:
            issues.append(('SUBGRAPH_END_MISMATCH', f'{subgraph_count} subgraph(s) but {end_count} end(s)'))

    return issues


def check_mermaid_parse(diagram_code):
    """Validate diagram with mermaid.parse() via Node. Returns (ok, error_msg)."""
    if not os.path.isfile(PARSE_CHECK_JS):
        return None, "mermaid-parse-check.js not found"
    try:
        result = subprocess.run(
            ["node", PARSE_CHECK_JS, diagram_code.strip()],
            capture_output=True,
            text=True,
            timeout=15,
        )
        if result.returncode == 0:
            return True, ""
        err = result.stderr.strip() or result.stdout.strip()
        return False, err[:200]
    except (subprocess.TimeoutExpired, FileNotFoundError) as e:
        return None, f"node unavailable: {e}"


def check_wiki_diagrams(wiki_dir):
    """Check all diagram files in a wiki directory."""
    diag_dir = os.path.join(wiki_dir, 'Diagrams')
    if not os.path.isdir(diag_dir):
        return {}

    results = {}
    for f in sorted(os.listdir(diag_dir)):
        if not f.endswith('.md'):
            continue
        fp = os.path.join(diag_dir, f)
        with open(fp, 'r', encoding='utf-8') as fh:
            content = fh.read()

        issues = check_mermaid_regex(content, f)

        # Node-based parse validation
        mermaid_match = re.search(r'```mermaid\n(.*?)```', content, re.DOTALL)
        if mermaid_match:
            ok, err = check_mermaid_parse(mermaid_match.group(1))
            if ok is False:
                issues.append(('PARSE_ERROR', err))

        if issues:
            results[f] = issues

    return results


def find_wikis(base_dir):
    """Find all _wiki/ directories under base_dir."""
    wikis = []
    for root, dirs, files in os.walk(base_dir):
        if '_wiki' in dirs:
            wikis.append(os.path.join(root, '_wiki'))
    return wikis


def main():
    parser = argparse.ArgumentParser(description='Validate Mermaid syntax in wiki diagram files')
    parser.add_argument('--wiki', help='Path to a single _wiki directory')
    parser.add_argument('--base', help='Base directory to search for _wiki directories')
    parser.add_argument('--vault', help='Vault root to search for all _wiki directories')
    args = parser.parse_args()

    all_results = {}

    if args.wiki:
        results = check_wiki_diagrams(args.wiki)
        if results:
            all_results[args.wiki] = results
    elif args.base:
        for w in sorted(find_wikis(args.base)):
            results = check_wiki_diagrams(w)
            if results:
                all_results[w] = results
    elif args.vault:
        for w in sorted(find_wikis(args.vault)):
            results = check_wiki_diagrams(w)
            if results:
                all_results[w] = results
    else:
        parser.print_help()
        sys.exit(1)

    if not all_results:
        print("All Mermaid diagrams pass syntax validation. 0 issues.")
        sys.exit(0)

    total = 0
    for wiki_path, file_issues in all_results.items():
        name = os.path.basename(os.path.dirname(wiki_path))
        print(f"\n{name}:")
        for filename, issues in file_issues.items():
            print(f"  {filename}:")
            for issue_type, desc in issues:
                print(f"    [{issue_type}] {desc}")
                total += 1

    print(f"\nTotal: {total} issue(s) across {len(all_results)} wiki(s)")
    sys.exit(1 if total > 0 else 0)


if __name__ == '__main__':
    main()
