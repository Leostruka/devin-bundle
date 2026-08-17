#!/usr/bin/env python3
"""Scan Obsidian wiki files for sensitive information (passwords, API keys, tokens)."""

import argparse
import os
import re
import sys

# Patterns for real credential values (not just mentions of the word "password")
SECRET_PATTERNS = [
    (re.compile(r'(password|passwd)\s*[=:]\s*[\'"][^\'"]{6,}[\'"]', re.IGNORECASE), 'Hardcoded password'),
    (re.compile(r'(DB_PASSWORD|DB_PASS|MAIL_PASSWORD|MAIL_PASS|SMTP_PASS|REDIS_PASSWORD)\s*[=:]\s*[\'\"]?[^\s\'\"#]{6,}', re.IGNORECASE), 'Environment credential'),
    (re.compile(r'(api_key|apikey|API_KEY)\s*[=:]\s*[\'"][^\'"]{10,}[\'"]', re.IGNORECASE), 'API key'),
    (re.compile(r'(secret|SECRET)\s*[=:]\s*[\'"][^\'"]{10,}[\'"]', re.IGNORECASE), 'Secret key'),
    (re.compile(r'(private_key|PRIVATE_KEY)\s*[=:]\s*-{5}BEGIN', re.IGNORECASE), 'Private key'),
    (re.compile(r'(token|TOKEN)\s*[=:]\s*[\'"][^\'"]{20,}[\'"]', re.IGNORECASE), 'Auth token'),
    (re.compile(r'password="[^"]{6,}"', re.IGNORECASE), 'XML attribute password'),
]

# False positive patterns (public tokens, not secrets)
FALSE_POSITIVES = [
    'publicKeyToken',  # .NET assembly tokens (public)
    '(REDACTED',       # Already redacted
    'SECURITY FINDING', # Already flagged
]


def scan_file(fp):
    """Scan a single file for secrets. Returns list of (line_num, match, pattern_name)."""
    findings = []
    with open(fp, 'r', encoding='utf-8') as fh:
        for i, line in enumerate(fh, 1):
            for pattern, name in SECRET_PATTERNS:
                for m in pattern.finditer(line):
                    match_text = m.group(0)
                    # Check false positives
                    if any(fp_text in match_text for fp_text in FALSE_POSITIVES):
                        continue
                    findings.append((i, match_text[:100], name))
    return findings


def scan_wiki(wiki_dir):
    """Scan a wiki directory for secrets."""
    if not os.path.isdir(wiki_dir):
        print(f"MISSING: {wiki_dir}")
        return []

    md_files = []
    for root, dirs, files in os.walk(wiki_dir):
        for f in files:
            if f.endswith('.md'):
                md_files.append(os.path.join(root, f))

    all_findings = []
    for fp in md_files:
        findings = scan_file(fp)
        for line_num, match, name in findings:
            all_findings.append((os.path.relpath(fp, wiki_dir), line_num, match, name))

    return all_findings


def find_wikis(base_dir):
    wikis = []
    for root, dirs, files in os.walk(base_dir):
        if '_wiki' in dirs:
            wikis.append(os.path.join(root, '_wiki'))
    return wikis


def main():
    parser = argparse.ArgumentParser(description='Scan wiki files for sensitive information')
    parser.add_argument('--wiki', help='Path to a single _wiki directory')
    parser.add_argument('--base', help='Base directory to search for _wiki directories')
    parser.add_argument('--vault', help='Vault root to search for all _wiki directories')
    args = parser.parse_args()

    all_results = []

    if args.wiki:
        findings = scan_wiki(args.wiki)
        if findings:
            all_results.append((args.wiki, findings))
    elif args.base:
        for w in sorted(find_wikis(args.base)):
            findings = scan_wiki(w)
            if findings:
                all_results.append((w, findings))
    elif args.vault:
        for w in sorted(find_wikis(args.vault)):
            findings = scan_wiki(w)
            if findings:
                all_results.append((w, findings))
    else:
        parser.print_help()
        sys.exit(1)

    if not all_results:
        print("No secrets found.")
        sys.exit(0)

    total = 0
    for wiki_path, findings in all_results:
        name = os.path.basename(os.path.dirname(wiki_path))
        print(f"\n{name} — {len(findings)} finding(s):")
        for fp, line, match, ptype in findings:
            print(f"  {fp}:{line} [{ptype}]")
            print(f"    {match}")
            total += 1

    print(f"\nTotal: {total} secret(s) found across {len(all_results)} wiki(s)")
    sys.exit(1 if total > 0 else 0)


if __name__ == '__main__':
    main()
