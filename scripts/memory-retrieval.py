#!/usr/bin/env python3
"""UserPromptSubmit hook: cue-anchored retrieval from .devin/memory/.

Scans .devin/memory/ notes, matches the user's prompt against cues
(keyword, path, symbol) in frontmatter, and injects the top-k relevant
notes as additionalContext.

Evidence:
- arXiv:2607.20972: voluntary memory use ≈ 0; deterministic injection works.
- arXiv:2608.15008: excessive retrieval hurts sequential tasks; keep top-k small.
"""
import json, os, re, sys, glob

BASE = '.devin/memory'
TOP_K = 3


def load_note(path):
    with open(path, encoding='utf-8') as f:
        content = f.read()
    cues = []
    title = ''
    category = ''
    status = ''
    if content.startswith('---'):
        m = re.search(r'^---\n(.*?)\n---', content, re.S)
        if m:
            fm = m.group(1)
            for line in fm.splitlines():
                if line.startswith('title:'):
                    title = line.split(':', 1)[1].strip().strip('"')
                elif line.startswith('category:'):
                    category = line.split(':', 1)[1].strip()
                elif line.startswith('status:'):
                    status = line.split(':', 1)[1].strip()
                elif line.strip().startswith('- '):
                    kv = line.strip()[2:]
                    if ':' in kv:
                        k, v = kv.split(':', 1)
                        cues.append((k.strip(), v.strip().strip('"').lower()))
    body = re.sub(r'^---\n.*?\n---', '', content, flags=re.S, count=1).strip()
    return {
        'path': path,
        'rel': path.replace(BASE + os.sep, '').replace('.md', '').replace(os.sep, '/'),
        'title': title,
        'category': category,
        'status': status,
        'cues': cues,
        'body': body,
    }


def score(note, prompt):
    prompt_l = prompt.lower()
    sc = 0
    for kind, val in note['cues']:
        if val in prompt_l:
            if kind == 'keyword':
                sc += 3
            elif kind == 'symbol':
                sc += 4
            elif kind == 'path':
                sc += 2
    for tag in re.findall(r'- (\S+)', note['body'][:1000]):
        if tag.lower() in prompt_l:
            sc += 1
    if note['status'] != 'active':
        sc = sc // 2
    return sc


def main():
    try:
        data = json.load(sys.stdin)
    except (json.JSONDecodeError, EOFError, ValueError):
        sys.exit(0)

    if data.get('hookEventName') != 'UserPromptSubmit' and data.get('hook_event_name') != 'UserPromptSubmit':
        sys.exit(0)

    prompt = data.get('prompt', '')
    if not prompt or not os.path.isdir(BASE):
        sys.exit(0)

    notes = []
    for p in glob.glob(os.path.join(BASE, '**', '*.md'), recursive=True):
        if p.endswith('MOC.md'):
            continue
        notes.append(load_note(p))

    scored = [(score(n, prompt), n) for n in notes]
    scored = [(s, n) for s, n in scored if s > 0]
    scored.sort(key=lambda x: x[0], reverse=True)

    if not scored:
        sys.exit(0)

    top = scored[:TOP_K]
    print(f"memory-retrieval: {len(top)} memory note(s) matched user prompt", file=sys.stderr)
    lines = [f"> [!note] Project memory ({len(top)} match{'es' if len(top) > 1 else ''})\n"]
    for s, n in top:
        lines.append(f"> **[[{n['rel']}|{n['title']}]]** ({n['category']})\n")
        # first non-empty body line
        for bline in n['body'].splitlines():
            bline = bline.strip()
            if bline:
                lines.append(f"> {bline}\n")
                break
        lines.append(f"> Source: `{n['path']}`\n")
        lines.append(">\n")

    print(json.dumps({
        "hookSpecificOutput": {
            "hookEventName": "UserPromptSubmit",
            "additionalContext": ''.join(lines).rstrip()
        }
    }))
    sys.exit(0)


if __name__ == "__main__":
    main()
