#!/usr/bin/env python3
"""Fix broken template links in Obsidian wiki Media/ templates."""

import argparse
import os
import sys

TEMPLATE_FIXES = {
    '[[...]]': '[[09-Decisions]]',
    '[[00-SRS]]': '[[01-SRS]]',
    '[[01-Architecture]]': '[[02-Architecture]]',
    '[[Diagrams/Context]]': '[[Diagrams/01-Context]]',
    '[[Diagrams/Container]]': '[[Diagrams/02-Container]]',
    '[[Diagrams/Component]]': '[[Diagrams/03-Component]]',
    '[[Diagrams/Domain]]': '[[Diagrams/04-Domain]]',
    '[[Diagrams/DataModel]]': '[[Diagrams/05-DataModel]]',
    '[[Diagrams/Flow]]': '[[Diagrams/06-Flow]]',
    '[[Diagrams/Sequence]]': '[[Diagrams/07-Sequence]]',
    '[[Diagrams/Class]]': '[[Diagrams/08-Class]]',
    '[[Diagrams/State]]': '[[Diagrams/09-State]]',
    '[[Diagrams/C4Dynamic]]': '[[Diagrams/10-C4Dynamic]]',
    '[[Diagrams/C4Deployment]]': '[[Diagrams/11-C4Deployment]]',
    '[[Diagrams/GitGraph]]': '[[Diagrams/12-GitGraph]]',
    '[[Diagrams/Mindmap]]': '[[Diagrams/13-Mindmap]]',
}


def fix_wiki(wiki_dir):
    if not os.path.isdir(wiki_dir):
        print(f"MISSING: {wiki_dir}")
        return 0

    # Check if Modules/Auth.md exists
    auth_exists = os.path.isfile(os.path.join(wiki_dir, 'Modules', 'Auth.md'))
    fixes = dict(TEMPLATE_FIXES)
    if not auth_exists:
        fixes['[[Modules/Auth]]'] = '_ExampleModule_'
        fixes['[[Modules/{{MODULE_NAME}}]]'] = '_ExampleModule_'

    md_files = []
    for root, dirs, files in os.walk(wiki_dir):
        for f in files:
            if f.endswith('.md'):
                md_files.append(os.path.join(root, f))

    changed = []
    for fp in md_files:
        with open(fp, 'r', encoding='utf-8') as fh:
            content = fh.read()
        original = content
        for old_link, new_link in fixes.items():
            content = content.replace(old_link, new_link)
        if content != original:
            with open(fp, 'w', encoding='utf-8') as fh:
                fh.write(content)
            changed.append(os.path.relpath(fp, wiki_dir))

    name = os.path.basename(os.path.dirname(wiki_dir))
    if changed:
        print(f"{name}: fixed {len(changed)} files")
        for c in changed:
            print(f"  - {c}")
    else:
        print(f"{name}: no template fixes needed")
    return len(changed)


def find_wikis(base_dir):
    wikis = []
    for root, dirs, files in os.walk(base_dir):
        if '_wiki' in dirs:
            wikis.append(os.path.join(root, '_wiki'))
    return wikis


def main():
    parser = argparse.ArgumentParser(description='Fix broken template links in wiki Media/ templates')
    parser.add_argument('--wiki', help='Path to a single _wiki directory')
    parser.add_argument('--base', help='Base directory to search for _wiki directories')
    args = parser.parse_args()

    total = 0
    if args.wiki:
        total = fix_wiki(args.wiki)
    elif args.base:
        for w in sorted(find_wikis(args.base)):
            total += fix_wiki(w)
    else:
        parser.print_help()
        sys.exit(1)

    print(f"\nTotal files changed: {total}")


if __name__ == '__main__':
    main()
