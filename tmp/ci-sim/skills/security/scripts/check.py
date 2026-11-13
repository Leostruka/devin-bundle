#!/usr/bin/env python3
"""Check a project for secure defaults."""
import os
import re
import sys


def check_project(repo='.'):
    """Run a lightweight secure-defaults checklist and return findings."""
    findings = []
    gitignore = os.path.join(repo, '.gitignore')
    if os.path.exists(gitignore):
        content = open(gitignore, encoding='utf-8').read()
        if '.env' not in content:
            findings.append('.env is not in .gitignore')
    else:
        findings.append('no .gitignore found')

    if not os.path.exists(os.path.join(repo, '.env.example')):
        findings.append('.env.example is missing')

    secret_patterns = [
        re.compile(r'(?:api[_-]?key|password|token|secret)\s*=\s*["\']\S+["\']', re.I),
    ]
    for root, _, files in os.walk(repo):
        if '.git' in root or '__pycache__' in root:
            continue
        for name in files:
            if not name.endswith(('.py', '.js', '.ts', '.json', '.yaml', '.yml', '.sh', '.ps1')):
                continue
            path = os.path.join(root, name)
            try:
                with open(path, encoding='utf-8') as f:
                    text = f.read()
            except Exception:
                continue
            for pat in secret_patterns:
                if pat.search(text):
                    findings.append(f'possible hardcoded secret in {path}')
                    break

    return findings


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description='Check secure defaults')
    parser.add_argument('--repo', default='.')
    args = parser.parse_args()
    findings = check_project(args.repo)
    if findings:
        for f in findings:
            print(f)
        sys.exit(1)
    print('OK')
