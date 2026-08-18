#!/usr/bin/env python3
"""Audit one or more Obsidian project wikis against established standards."""

import argparse
import os
import re
import sys

# Wikilink pattern — handles escaped pipes in markdown tables
LINK_PATTERN = re.compile(r'\[\[([^\]]+?)\]\]')

# Sensitive info patterns
SECRET_PATTERNS = [
    re.compile(r'(password|passwd|secret|api_key|apikey|private_key|token|credential)\s*[=:]\s*[\'"][^\'"]{8,}[\'"]', re.IGNORECASE),
    re.compile(r'(DB_PASSWORD|DB_PASS|MAIL_PASSWORD|MAIL_PASS|SMTP_PASS|REDIS_PASSWORD|AWS_SECRET|CLIENT_SECRET|NOTIFY_SIGNING_SECRET)\s*[=:]\s*[\'\"]?[^\s\'\"#]{6,}', re.IGNORECASE),
]

# False positive patterns (already redacted or public tokens)
SECRET_FALSE_POSITIVES = ['(REDACTED', 'SECURITY FINDING', 'publicKeyToken', '-----BEGIN', 'Token="31bf3856']

# Scaffold placeholder markers
SCAFFOLD_MARKERS = ['_1-2 paragraph', '_What it does', '_Summary of', '_Brief description', '_Short summary']


def parse_target(raw):
    """Parse wikilink target, handling escaped pipes."""
    parts = []
    current = ''
    i = 0
    while i < len(raw):
        if i < len(raw) - 1 and raw[i] == '\\' and raw[i + 1] == '|':
            parts.append(current)
            current = ''
            i += 2
        elif raw[i] == '|':
            parts.append(current)
            current = ''
            i += 1
        else:
            current += raw[i]
            i += 1
    parts.append(current)
    return parts[0].strip()


def is_false_positive(tgt):
    """Check if a wikilink target is a known false positive."""
    if tgt.startswith('#'):
        return True
    if tgt.startswith('...'):
        return True
    if tgt.startswith(':'):
        return True
    if tgt.startswith('byte,'):
        return True
    return False


def audit_wiki(wiki_dir):
    """Audit a single wiki directory. Returns dict of results."""
    result = {
        'path': wiki_dir,
        'exists': os.path.isdir(wiki_dir),
        'md_count': 0,
        'diagram_count': 0,
        'has_14_architecture': False,
        'mermaid_issues': [],
        'frontmatter_issues': [],
        'broken_links': 0,
        'broken_details': [],
        'source_count': 0,
        'source_pct': 0,
        'language': 'unknown',
        'secrets_found': 0,
        'secret_details': [],
        'overview_status': 'missing',
        'status': 'MISSING',
    }

    if not result['exists']:
        return result

    # Collect all .md files
    md_files = []
    for root, dirs, files in os.walk(wiki_dir):
        for f in files:
            if f.endswith('.md'):
                md_files.append(os.path.join(root, f))
    result['md_count'] = len(md_files)

    if not md_files:
        result['status'] = 'MISSING'
        return result

    # Diagrams
    diag_dir = os.path.join(wiki_dir, 'Diagrams')
    if os.path.isdir(diag_dir):
        diags = [f for f in os.listdir(diag_dir) if f.endswith('.md')]
        result['diagram_count'] = len(diags)
        result['has_14_architecture'] = '14-Architecture.md' in diags

        # Check Mermaid syntax in each diagram
        mermaid_issues = []
        for diag_file in sorted(diags):
            diag_path = os.path.join(diag_dir, diag_file)
            with open(diag_path, 'r', encoding='utf-8') as fh:
                diag_content = fh.read()
            # Check for mermaid block
            mermaid_match = re.search(r'(`{2,3})mermaid\n(.*?)\1', diag_content, re.DOTALL)
            if not mermaid_match:
                if '`mermaid' in diag_content:
                    mermaid_issues.append((diag_file, 'MALFORMED_FENCE'))
                else:
                    mermaid_issues.append((diag_file, 'NO_MERMAID'))
                continue
            mermaid = mermaid_match.group(2)
            fence = mermaid_match.group(1)
            if fence != '```':
                mermaid_issues.append((diag_file, 'WRONG_FENCE'))
            if '<!-- Sources:' in mermaid:
                mermaid_issues.append((diag_file, 'SOURCES_INSIDE'))
            if '<br///' in mermaid:
                mermaid_issues.append((diag_file, 'BR_TRIPLE_SLASH'))
            for line in mermaid.split('\n'):
                stripped = line.strip()
                if re.match(r'^\w+\s+fill:', stripped) and not stripped.startswith('style'):
                    mermaid_issues.append((diag_file, 'MISSING_STYLE'))
                    break
        result['mermaid_issues'] = mermaid_issues

    # Wikilinks + source format
    all_basenames = set()
    all_links = {}
    files_with_source = 0
    secrets_found = []

    for fp in md_files:
        with open(fp, 'r', encoding='utf-8') as fh:
            content = fh.read()

        # Frontmatter checks
        rel_path = os.path.relpath(fp, wiki_dir)
        if content.startswith('---'):
            fm_end = content.find('\n---', 3)
            if fm_end == -1:
                result['frontmatter_issues'].append((rel_path, 'MISSING_CLOSING', 'frontmatter not closed with ---'))
            else:
                fm = content[3:fm_end]
                if '\\' in fm and ('title:' in fm or 'project:' in fm):
                    # Check for backslash-escaped quotes (common error: title: \ ... \)
                    if re.search(r'(title|project):\s*\\', fm):
                        result['frontmatter_issues'].append((rel_path, 'BACKSLASH_QUOTE', 'frontmatter uses backslashes instead of quotes'))

        # Source format
        if 'source:' in content:
            files_with_source += 1

        # Wikilinks
        for i, line in enumerate(content.split('\n'), 1):
            for m in LINK_PATTERN.finditer(line):
                tgt = parse_target(m.group(1))
                all_links.setdefault(tgt, []).append((os.path.relpath(fp, wiki_dir), i))

        # Secrets
        for pattern in SECRET_PATTERNS:
            for m in pattern.finditer(content):
                match_text = m.group(0)
                if any(fp_text in match_text for fp_text in SECRET_FALSE_POSITIVES):
                    continue
                secrets_found.append((os.path.relpath(fp, wiki_dir), match_text[:80]))

        all_basenames.add(os.path.splitext(os.path.basename(fp))[0])

    # Broken links
    broken = []
    for tgt, refs in sorted(all_links.items()):
        if is_false_positive(tgt):
            continue
        tgt_clean = tgt.replace('\\', '/')
        tgt_base = tgt_clean.split('/')[-1]
        found = tgt_base in all_basenames
        if not found:
            for b in all_basenames:
                if tgt_clean == b or tgt_clean.endswith('/' + b):
                    found = True
                    break
        if not found:
            broken.append((tgt, refs))

    result['broken_links'] = len(broken)
    result['broken_details'] = broken[:10]
    result['source_count'] = files_with_source
    result['source_pct'] = (files_with_source * 100) // len(md_files) if md_files else 0
    result['secrets_found'] = len(secrets_found)
    result['secret_details'] = secrets_found[:5]

    # Language check (from 00-Overview)
    ov_path = os.path.join(wiki_dir, '00-Overview.md')
    if os.path.isfile(ov_path):
        with open(ov_path, 'r', encoding='utf-8') as fh:
            ov_content = fh.read()
        is_scaffold = any(m in ov_content for m in SCAFFOLD_MARKERS)
        result['overview_status'] = 'scaffold' if is_scaffold else 'populated'

        pt_words = len(re.findall(r'\b(?:de|que|para|com|uma|não|sim|este|esta|como|mais|apenas)\b', ov_content, re.IGNORECASE))
        en_words = len(re.findall(r'\b(?:the|and|for|with|this|that|from|which|provides|handles)\b', ov_content, re.IGNORECASE))
        result['language'] = 'PT' if pt_words > en_words else 'EN'

    # Status
    has_mermaid_issues = len(result.get('mermaid_issues', [])) > 0
    has_frontmatter_issues = len(result.get('frontmatter_issues', [])) > 0
    if result['source_pct'] >= 96 and result['broken_links'] == 0 and result['diagram_count'] == 14 and result['secrets_found'] == 0 and not has_mermaid_issues and not has_frontmatter_issues:
        result['status'] = 'GOOD'
    elif result['source_pct'] >= 96 and result['broken_links'] <= 2 and result['diagram_count'] == 14 and not has_mermaid_issues and not has_frontmatter_issues:
        result['status'] = 'GOOD'
    elif result['source_pct'] < 50 or result['broken_links'] >= 10:
        result['status'] = 'CRITICAL'
    elif result['source_pct'] < 80 or result['broken_links'] >= 1 or has_mermaid_issues or has_frontmatter_issues:
        result['status'] = 'POOR'
    else:
        result['status'] = 'FIXED'

    return result


def find_wikis(base_dir):
    """Find all _wiki/ directories under base_dir."""
    wikis = []
    for root, dirs, files in os.walk(base_dir):
        if '_wiki' in dirs:
            wikis.append(os.path.join(root, '_wiki'))
    return wikis


def print_table(results):
    """Print results as a table."""
    print()
    print(f"| Wiki | Files | Diagrams | 14-Arch | Mermaid | Frontmatter | Broken | Source % | Lang | Secrets | Status |")
    print(f"|------|-------|----------|---------|---------|-------------|--------|----------|------|---------|--------|")
    for r in results:
        name = os.path.basename(os.path.dirname(r['path']))
        arch = 'yes' if r['has_14_architecture'] else 'NO'
        mermaid = f"{len(r.get('mermaid_issues', []))} issues" if r.get('mermaid_issues') else 'OK'
        fm = f"{len(r.get('frontmatter_issues', []))} issues" if r.get('frontmatter_issues') else 'OK'
        print(f"| {name} | {r['md_count']} | {r['diagram_count']} | {arch} | {mermaid} | {fm} | {r['broken_links']} | {r['source_pct']}% | {r['language']} | {r['secrets_found']} | {r['status']} |")

    # Details
    for r in results:
        name = os.path.basename(os.path.dirname(r['path']))
        if r.get('mermaid_issues'):
            print(f"\n{name} — {len(r['mermaid_issues'])} Mermaid issues:")
            for diag, issue_type in r['mermaid_issues']:
                print(f"  {diag}: [{issue_type}]")
        if r.get('frontmatter_issues'):
            print(f"\n{name} — {len(r['frontmatter_issues'])} Frontmatter issues:")
            for fp, issue_type, desc in r['frontmatter_issues']:
                print(f"  {fp}: [{issue_type}] {desc}")
        if r['broken_links'] > 0:
            print(f"\n{name} — {r['broken_links']} broken links:")
            for tgt, refs in r['broken_details']:
                print(f"  [[{tgt}]] from {refs[0][0]}:{refs[0][1]}")
        if r['secrets_found'] > 0:
            print(f"\n{name} — {r['secrets_found']} secrets found:")
            for fp, match in r['secret_details']:
                print(f"  {fp}: {match}...")


def main():
    parser = argparse.ArgumentParser(description='Audit Obsidian project wikis')
    parser.add_argument('--wiki', help='Path to a single _wiki directory')
    parser.add_argument('--base', help='Base directory to search for _wiki directories')
    parser.add_argument('--vault', help='Vault root to search for all _wiki directories')
    args = parser.parse_args()

    if args.wiki:
        results = [audit_wiki(args.wiki)]
    elif args.base:
        wikis = find_wikis(args.base)
        results = [audit_wiki(w) for w in sorted(wikis)]
    elif args.vault:
        wikis = find_wikis(args.vault)
        results = [audit_wiki(w) for w in sorted(wikis)]
    else:
        parser.print_help()
        sys.exit(1)

    print_table(results)

    # Exit code
    critical = sum(1 for r in results if r['status'] == 'CRITICAL')
    if critical > 0:
        sys.exit(1)


if __name__ == '__main__':
    main()
