#!/usr/bin/env python3
"""Create or update a project memory note.

Reads a note file or stdin, validates frontmatter, and writes it to
.devin/memory/notes/YYYY/MM/<topic>.md (or logbook/... for daily notes).
Updates MOC and logbook index on request.

Usage:
  python capture-memory.py --file note.md --category question
  python capture-memory.py --title "Fiscal quarters" --body note.md
  cat note.md | python capture-memory.py --title "Fiscal quarters" --category convention
"""
import argparse, os, re, sys, shutil
from datetime import datetime

BASE = '.devin/memory'


def slugify(text):
    return re.sub(r'[^a-z0-9]+', '-', text.lower()).strip('-')


def parse_frontmatter(path):
    with open(path, encoding='utf-8') as f:
        content = f.read()
    if content.startswith('---'):
        parts = content.split('---', 2)
        if len(parts) >= 3:
            return parts[2].lstrip('\n')
    return content


def today():
    return datetime.now().strftime('%Y-%m-%d')


def ensure_dirs():
    now = datetime.now()
    for sub in ['notes', 'logbook', 'decisions', 'scripts', 'templates']:
        os.makedirs(os.path.join(BASE, sub, now.strftime('%Y'), now.strftime('%m')), exist_ok=True)


def write_note(title, body, category, session=''):
    ensure_dirs()
    now = datetime.now()
    date = today()
    slug = slugify(title)
    if category == 'logbook':
        path = os.path.join(BASE, 'logbook', now.strftime('%Y'), now.strftime('%m'), f'{date}.md')
    elif category == 'decision':
        path = os.path.join(BASE, 'decisions', f'ADR-{slug}.md')
    else:
        path = os.path.join(BASE, 'notes', now.strftime('%Y'), now.strftime('%m'), f'{slug}.md')

    if os.path.exists(path):
        print(f'Note exists: {path}')
        return path

    frontmatter = f"""---
title: "{title}"
date: "{date}"
session: "{session}"
category: {category}
tags:
  - {category}
status: active
cues: []
---

{body}
"""
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'w', encoding='utf-8') as f:
        f.write(frontmatter)
    print(f'Wrote: {path}')
    return path


def update_moc(title, rel, category):
    moc = os.path.join(BASE, 'MOC.md')
    entry = f"- [[{rel}|{title}]] — {category} ({today()})"
    if os.path.exists(moc):
        with open(moc, encoding='utf-8') as f:
            content = f.read()
    else:
        content = "# Project Memory MOC\n\n## Notes\n\n## Logbook\n\n## Decisions\n"
    section = '## Notes' if category == 'question' or category == 'convention' or category == 'solution' else f'## {category.capitalize()}s'
    if section not in content:
        content += f"\n{section}\n"
    lines = content.splitlines()
    out = []
    inserted = False
    for i, line in enumerate(lines):
        out.append(line)
        if line.strip() == section.strip() and not inserted:
            out.append(entry)
            inserted = True
    if not inserted:
        out.append(entry)
    with open(moc, 'w', encoding='utf-8') as f:
        f.write('\n'.join(out) + '\n')
    print(f'Updated: {moc}')


def install_helpers():
    src = os.path.dirname(__file__)
    dst = os.path.join(BASE, 'scripts')
    for name in ['capture-memory.py', 'query-memory.py', 'audit-memory.py']:
        s = os.path.join(src, name)
        d = os.path.join(dst, name)
        if os.path.exists(s) and not os.path.exists(d):
            os.makedirs(dst, exist_ok=True)
            shutil.copy2(s, d)
            print(f'Installed helper: {d}')


def main():
    p = argparse.ArgumentParser(description='Capture a project memory note')
    p.add_argument('--file', help='Path to note body file')
    p.add_argument('--title', required=True, help='Note title')
    p.add_argument('--category', default='question', choices=['question', 'convention', 'decision', 'failure', 'solution', 'logbook'])
    p.add_argument('--session', default='', help='Session id or trace')
    p.add_argument('--update-moc', action='store_true', help='Update MOC.md')
    p.add_argument('--install', action='store_true', help='Install helper scripts into .devin/memory/scripts/')
    args = p.parse_args()

    if args.install:
        install_helpers()
        return

    if args.file:
        body = parse_frontmatter(args.file)
    else:
        body = sys.stdin.read()

    if not body.strip():
        print('No note body provided')
        sys.exit(1)

    path = write_note(args.title, body, args.category, args.session)
    if args.update_moc:
        rel = path.replace(BASE + os.sep, '').replace('.md', '').replace(os.sep, '/')
        update_moc(args.title, rel, args.category)


if __name__ == '__main__':
    main()
